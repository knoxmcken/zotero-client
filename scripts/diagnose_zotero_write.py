#!/usr/bin/env python3
"""Diagnose the create -> read 404 seen in the integration workflow.

Prints the HTTP status and response body for each call in the write path.
Credentials are never printed (the Zotero key and user id are also masked by
GitHub Actions).

Established so far (see docs/NOTE_PERSISTENCE_INVESTIGATION.md), against the
live API with library version advancing, polling at t+0/1/2/4/8s and a 30s tail:

  note (standalone)      POST 200 + key + version bump, never readable --
                         404 with and without includeTrashed, absent from every
                         listing, no deletion-log record.
  note with parentItem   same, but the object *does* exist server-side: deleting
                         the parent cascades a delete onto the note's key.
  book                   readable on the first attempt, every round.
  journalArticle         readable on the first attempt, every round.

So item type is the deciding variable, and there is no propagation window to
wait out -- neither for the types that work (attempt 1, always) nor for notes
(waiting never helps). This script varies the item type so the contrast stays
visible in CI logs.

Each run performs up to 5 creates and deletes everything it can. Note that a
standalone note, and any note, cannot be deleted through the API (DELETE also
returns 404), so a note created here is only reclaimed by deleting its parent.

Exit code is 0 by default -- diagnostic only, must not fail the build, because
CI runs this on every push. Pass --strict to assert the write contract instead:
a 2xx create that returns a key must become readable, so --strict exits non-zero
for as long as notes behave this way. Do not wire --strict into the per-push
step until the note behaviour is resolved (see the findings document).
"""

import argparse
import os
import sys
import time

import requests

BASE_URL = "https://api.zotero.org"
BODY_LIMIT = 300
DEFAULT_TYPES = ("note", "book", "journalArticle", "note+parent")
POLL_DELAYS = (0, 1, 2, 4, 8)

# Which arm each created item belongs to, so cleanup can order the deletes.
RESULTS = []


def _credential_summary(value):
    return "<unset>" if not value else f"<set len={len(value)}>"


def show(label, response):
    body = " ".join(response.text.split())[:BODY_LIMIT]
    print(f"{label}: HTTP {response.status_code} {body}")
    return response


def build_payload(item_type, round_number, parent_key=None):
    """Return an item payload for one arm of the matrix."""
    if item_type == "note":
        return {"itemType": "note", "note": f"<p>write-path diagnostic (note r{round_number})</p>"}
    if item_type == "note+parent":
        return {
            "itemType": "note",
            "note": f"<p>write-path diagnostic (child note r{round_number})</p>",
            "parentItem": parent_key,
        }
    if item_type == "journalArticle":
        return {
            "itemType": "journalArticle",
            "title": f"write-path diagnostic (journalArticle r{round_number}) - please delete",
        }
    return {
        "itemType": item_type,
        "title": f"write-path diagnostic ({item_type} r{round_number}) - please delete",
    }


def extract_key(response):
    try:
        entry = response.json().get("successful", {}).get("0", {})
    except ValueError:
        return None
    return entry.get("key") or entry.get("data", {}).get("key")


def library_version(items_url, headers):
    response = requests.get(items_url, headers=headers, params={"limit": 1}, timeout=30)
    return response.headers.get("Last-Modified-Version")


def listing_keys(items_url, headers, limit=10):
    response = requests.get(
        items_url,
        headers=headers,
        params={"sort": "dateAdded", "direction": "desc", "limit": limit},
        timeout=30,
    )
    if response.status_code != 200:
        return None
    return [item.get("key") for item in response.json()]


def key_access_summary(api_key):
    """Report what the key is actually allowed to do (never prints the key)."""
    response = requests.get(f"{BASE_URL}/keys/{api_key}", timeout=30)
    if response.status_code != 200:
        return f"HTTP {response.status_code}"
    access = response.json().get("access", {})
    return access.get("user", {})


def create_and_probe(item_type, payload, items_url, headers, attempts, delay):
    """Create one item and report everything we can learn about it."""
    version_before = library_version(items_url, headers)
    response = show(
        f"[{item_type}] POST /items",
        requests.post(items_url, headers=headers, json=[payload], timeout=30),
    )
    version_after = library_version(items_url, headers)
    key = extract_key(response)
    print(f"[{item_type}] parsed key={key!r} library version {version_before} -> {version_after}")
    result = {
        "item_type": item_type,
        "key": key,
        "version": None,
        "readable": False,
        "attempts": None,
        "elapsed": None,
        "listed": None,
        "delete_status": None,
    }
    RESULTS.append(result)
    if not key:
        return result

    item_url = f"{items_url}/{key}"
    started = time.time()
    for attempt in range(1, attempts + 1):
        while time.time() - started < POLL_DELAYS[min(attempt - 1, len(POLL_DELAYS) - 1)]:
            time.sleep(0.05)
        current = requests.get(item_url, headers=headers, timeout=30)
        print(f"[{item_type}] poll {attempt}: HTTP {current.status_code}")
        if current.status_code == 200:
            result.update(
                readable=True,
                attempts=attempt,
                elapsed=time.time() - started,
                version=current.json().get("version"),
            )
            break
        time.sleep(delay)

    if result["readable"]:
        print(f"[{item_type}] RESULT: readable after {result['attempts']} attempt(s) "
              f"(~{result['elapsed']:.1f}s)")
    else:
        result["attempts"] = attempts
        result["elapsed"] = time.time() - started
        trashed = requests.get(item_url, headers=headers, params={"includeTrashed": 1}, timeout=30)
        print(f"[{item_type}] RESULT: never readable after {attempts} poll(s) "
              f"(~{result['elapsed']:.1f}s); includeTrashed=HTTP {trashed.status_code}")

    listed = listing_keys(items_url, headers)
    if listed is not None:
        result["listed"] = key in listed
        print(f"[{item_type}] in newest-10 listing: {result['listed']}")
    return result


def verify_deletion(items_url, headers, result):
    """Delete a readable item and confirm it is gone; never fail by default."""
    key = result["key"]
    item_url = f"{items_url}/{key}"
    delete_headers = dict(headers)
    if result["version"]:
        delete_headers["If-Unmodified-Since-Version"] = str(result["version"])
    response = show(f"cleanup DELETE /items/{key}", requests.delete(item_url, headers=delete_headers, timeout=30))
    result["delete_status"] = response.status_code
    read_back = requests.get(item_url, headers=headers, params={"includeTrashed": 1}, timeout=30)
    print(f"cleanup read-back /items/{key} (includeTrashed): HTTP {read_back.status_code}")
    result["delete_verified"] = read_back.status_code == 404


def deletion_log_contains(api_key, library, user_id, since, key):
    """Was `key` recorded as deleted at or after `since`? (evidence it existed)"""
    url = f"{BASE_URL}/{library}/{user_id}/deleted"
    response = requests.get(url, headers={"Zotero-API-Key": api_key}, params={"since": since}, timeout=60)
    if response.status_code != 200:
        return None
    return key in response.json().get("items", [])


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--types",
        default=",".join(DEFAULT_TYPES),
        help=f"comma-separated item types to try, in order (default: {','.join(DEFAULT_TYPES)}); "
             "'note+parent' creates a parent book plus a child note",
    )
    parser.add_argument("--rounds", type=int, default=1, help="rounds per item type (default: 1)")
    parser.add_argument("--poll-attempts", type=int, default=len(POLL_DELAYS),
                        help=f"read attempts per create (default: {len(POLL_DELAYS)})")
    parser.add_argument("--poll-delay", type=float, default=1.0,
                        help="seconds between read attempts (default: 1.0)")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="exit non-zero when a create returned a key but never became readable, "
             "or unreadable leftovers could not be deleted (off by default: CI runs this on every push)",
    )
    args = parser.parse_args(argv)

    item_types = [t.strip() for t in args.types.split(",") if t.strip()]
    unknown = [t for t in item_types if t not in DEFAULT_TYPES]
    if unknown:
        print(f"unknown item type(s): {', '.join(unknown)}; known: {', '.join(DEFAULT_TYPES)}")
        return 0

    api_key = os.getenv("ZOTERO_API_KEY")
    user_id = os.getenv("ZOTERO_USER_ID")
    library_type = os.getenv("ZOTERO_LIBRARY_TYPE", "users")
    print(
        "diagnose write path: "
        f"library_type={library_type} "
        f"user_id={_credential_summary(user_id)} "
        f"api_key={_credential_summary(api_key)} "
        f"types={item_types} rounds={args.rounds} strict={args.strict}"
    )
    if not api_key or not user_id:
        print("SKIP: ZOTERO_API_KEY / ZOTERO_USER_ID not set")
        return 0

    headers = {"Zotero-API-Key": api_key}
    items_url = f"{BASE_URL}/{library_type}/{user_id}/items"
    print(f"key access (user library): {key_access_summary(api_key)}")
    print(f"library Last-Modified-Version={library_version(items_url, headers)!r}")

    # A note+parent arm needs a readable-ish parent; one per round.
    for round_number in range(1, args.rounds + 1):
        parent_result = None
        if "note+parent" in item_types:
            print(f"\n-- round {round_number}: creating parent for the note+parent arm --")
            parent_result = create_and_probe(
                "parent book",
                {"itemType": "book",
                 "title": f"write-path diagnostic (parent book r{round_number}) - please delete"},
                items_url, headers, args.poll_attempts, args.poll_delay,
            )
        for item_type in item_types:
            print(f"\n-- round {round_number}: {item_type} --")
            if item_type == "note+parent":
                if not parent_result or not parent_result["key"]:
                    print("SKIP note+parent: no parent key was returned")
                    continue
                payload = build_payload(item_type, round_number, parent_result["key"])
            else:
                payload = build_payload(item_type, round_number)
            create_and_probe(item_type, payload, items_url, headers, args.poll_attempts, args.poll_delay)

        # Cleanup per round: addressable items first, the parent last so that
        # its deletion reclaims any child note the API refuses to address.
        print("\n-- cleanup --")
        leftovers = []
        for result in [r for r in RESULTS if r["key"]]:
            if result.get("delete_status") is not None:
                continue
            if result is parent_result:
                continue
            if result["readable"]:
                verify_deletion(items_url, headers, result)
            else:
                print(f"cleanup SKIP /items/{result['key']}: never readable, so DELETE also 404s")
                leftovers.append(result)
        if parent_result:
            parent_key = parent_result["key"]
            if parent_result["readable"]:
                version_before_delete = library_version(items_url, headers)
                verify_deletion(items_url, headers, parent_result)
                for leftover in leftovers:
                    if leftover["item_type"] == "note+parent":
                        recorded = deletion_log_contains(
                            api_key, library_type, user_id, int(version_before_delete), leftover["key"]
                        )
                        print(
                            f"evidence: child note {leftover['key']} recorded in /deleted at the "
                            f"parent's deletion (since={version_before_delete}): {recorded} "
                            "-- True means the note existed server-side despite never being readable"
                        )
            else:
                print(f"cleanup SKIP /items/{parent_key}: parent never readable")
                leftovers.append(parent_result)

    print("\nRESULT summary:")
    for result in RESULTS:
        if not result["key"]:
            continue
        if result["readable"]:
            outcome = f"readable after {result['attempts']} attempt(s) (~{result['elapsed']:.1f}s)"
        else:
            outcome = f"NEVER readable after {result['attempts']} attempt(s) (~{result['elapsed']:.1f}s)"
        print(f"RESULT   {result['item_type']:16s} key={result['key']} {outcome} "
              f"listed={result['listed']} delete={result['delete_status']}")

    unexpected = [r for r in RESULTS if r["key"] and not r["readable"]]
    undeleted = [r for r in RESULTS if r.get("delete_verified") is False]
    if not unexpected and not undeleted:
        print("RESULT contract: every create that returned a key became readable")
        return 0
    print(f"RESULT contract: {len(unexpected)} create(s) returned a key but never became readable "
          f"({', '.join(sorted({r['item_type'] for r in unexpected}))})")
    if undeleted:
        print(f"RESULT contract: {len(undeleted)} deletion(s) could not be verified: "
              f"{', '.join(r['key'] for r in undeleted)}")
    if args.strict:
        print("RESULT strict: failing -- see docs/NOTE_PERSISTENCE_INVESTIGATION.md")
        return 1
    print("RESULT diagnostic-only: exiting 0 (pass --strict to fail on this)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
