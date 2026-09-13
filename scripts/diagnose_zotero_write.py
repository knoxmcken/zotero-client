#!/usr/bin/env python3
"""Diagnose the create -> delete 404 seen in the integration workflow.

Prints the HTTP status and response body for each call in the write
path. Credentials are never printed (the Zotero key and user id are
also masked by GitHub Actions).

Earlier runs established that POST returns 200 with a created object
(and the library version advances), but the returned key is never
readable and never appears in listings. This version tests the two
remaining explanations:

  H1  the object is committed but hidden -- e.g. it lands in the trash,
      so probe with includeTrashed=1
  H2  the write contract matters -- compare the client's unversioned
      write with the two documented contracts (Zotero-Write-Token, or
      If-Unmodified-Since-Version)

Exit code is always 0 -- diagnostic only, must not fail the build.
"""

import os
import sys
import time
import uuid

import requests

BASE_URL = "https://api.zotero.org"
BODY_LIMIT = 300
POLL_ATTEMPTS = 4
POLL_DELAY = 3.0


def _credential_summary(value):
    return "<unset>" if not value else f"<set len={len(value)}>"


def show(label, response):
    body = " ".join(response.text.split())[:BODY_LIMIT]
    print(f"{label}: HTTP {response.status_code} {body}")
    return response


def extract_key(response):
    try:
        entry = response.json().get("successful", {}).get("0", {})
    except ValueError:
        return None
    return entry.get("key") or entry.get("data", {}).get("key")


def library_version(items_url, headers):
    response = requests.get(items_url, headers=headers, params={"limit": 1}, timeout=30)
    return response.headers.get("Last-Modified-Version")


def listing_keys(items_url, headers, include_trashed=False, limit=10):
    params = {"sort": "dateAdded", "direction": "desc", "limit": limit}
    if include_trashed:
        params["includeTrashed"] = 1
    response = requests.get(items_url, headers=headers, params=params, timeout=30)
    if response.status_code != 200:
        return None
    return [item.get("key") for item in response.json()]


def probe(key, items_url, headers, label):
    """Report visibility of one created key; return attempts-to-readable or None."""
    item_url = f"{items_url}/{key}"
    show(
        f"[{label}] GET    /items/{key}?includeTrashed=1",
        requests.get(item_url, headers=headers, params={"includeTrashed": 1}, timeout=30),
    )
    readable_after = None
    for attempt in range(1, POLL_ATTEMPTS + 1):
        status = requests.get(item_url, headers=headers, timeout=30).status_code
        print(f"[{label}] poll {attempt}: HTTP {status}")
        if status == 200:
            readable_after = attempt
            break
        time.sleep(POLL_DELAY)
    listed = listing_keys(items_url, headers)
    listed_trashed = listing_keys(items_url, headers, include_trashed=True)
    print(f"[{label}] in listing: {key in (listed or [])}")
    print(f"[{label}] in listing (includeTrashed): {key in (listed_trashed or [])}")
    return readable_after


def main():
    api_key = os.getenv("ZOTERO_API_KEY")
    user_id = os.getenv("ZOTERO_USER_ID")
    library_type = os.getenv("ZOTERO_LIBRARY_TYPE", "users")
    print(
        "diagnose write path: "
        f"library_type={library_type} "
        f"user_id={_credential_summary(user_id)} "
        f"api_key={_credential_summary(api_key)}"
    )
    if not api_key or not user_id:
        print("SKIP: ZOTERO_API_KEY / ZOTERO_USER_ID not set")
        return 0

    headers = {"Zotero-API-Key": api_key}
    items_url = f"{BASE_URL}/{library_type}/{user_id}/items"
    baseline = library_version(items_url, headers)
    print(f"library Last-Modified-Version={baseline!r}")

    note = "<p>CI write-path diagnostic</p>"
    created = {}

    # Variant A: exactly what the client does today.
    key_a = extract_key(
        show(
            "A POST /items (unversioned, no token)",
            requests.post(items_url, headers=headers, json=[{"itemType": "note", "note": note}], timeout=30),
        )
    )
    print(f"A parsed key={key_a!r}")

    # Variant B: unversioned with the documented Zotero-Write-Token.
    token_headers = dict(headers)
    token_headers["Zotero-Write-Token"] = uuid.uuid4().hex
    key_b = extract_key(
        show(
            "B POST /items (unversioned + Zotero-Write-Token)",
            requests.post(
                items_url,
                headers=token_headers,
                json=[{"itemType": "note", "note": note}],
                timeout=30,
            ),
        )
    )
    print(f"B parsed key={key_b!r}")

    # Variant C: versioned write against a freshly read library version.
    key_c = None
    for attempt in (1, 2):
        current = library_version(items_url, headers)
        versioned_headers = dict(headers)
        versioned_headers["If-Unmodified-Since-Version"] = str(current)
        response = show(
            f"C POST /items (versioned {current}, attempt {attempt})",
            requests.post(
                items_url,
                headers=versioned_headers,
                json=[{"itemType": "note", "note": note}],
                timeout=30,
            ),
        )
        if response.status_code == 200:
            key_c = extract_key(response)
            break
    print(f"C parsed key={key_c!r}")

    for label, key in (("A", key_a), ("B", key_b), ("C", key_c)):
        if not key:
            continue
        created[label] = key
        probe(key, items_url, headers, label)

    print("RESULT summary:")
    for label, key in created.items():
        print(f"RESULT   variant {label}: key={key}")

    # Clean up anything that did become readable.
    for label, key in created.items():
        item_url = f"{items_url}/{key}"
        current = requests.get(item_url, headers=headers, timeout=30)
        if current.status_code == 200:
            version = current.json().get("version")
            delete_headers = dict(headers)
            if version:
                delete_headers["If-Unmodified-Since-Version"] = str(version)
            show(
                f"cleanup DELETE /items/{key}",
                requests.delete(item_url, headers=delete_headers, timeout=30),
            )
    return 0


if __name__ == "__main__":
    sys.exit(main())
