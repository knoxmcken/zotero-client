#!/usr/bin/env python3
"""Diagnose the create -> delete 404 seen in the integration workflow.

Runs the write path one step at a time and prints the HTTP status and
response body for each call, so CI logs show exactly where the write
breaks. Credentials are never printed; the Zotero API key and user id
are also masked by GitHub Actions in workflow logs.

Questions this answers:
  1. Does POST return a key, and is that key immediately readable?
  2. Does the created key show up in a recent-items listing at all?
  3. Does a versioned write (If-Unmodified-Since-Version) behave
     differently from an unversioned one?

Exit code is always 0 -- this is diagnostic only and must not fail the
build.

Usage:
    python scripts/diagnose_zotero_write.py
"""

import os
import sys
import time

import requests

BASE_URL = "https://api.zotero.org"
BODY_LIMIT = 400
READ_ATTEMPTS = 3
READ_DELAY = 2.0


def _credential_summary(value):
    """Describe a credential without revealing it."""
    return "<unset>" if not value else f"<set len={len(value)}>"


def show(label, response):
    """Print one response line, with the body flattened and truncated."""
    body = " ".join(response.text.split())[:BODY_LIMIT]
    print(f"{label}: HTTP {response.status_code} {body}")
    return response


def extract_key(response):
    """Pull the created item key out of a Zotero write response."""
    try:
        entry = response.json().get("successful", {}).get("0", {})
    except ValueError:
        return None
    return entry.get("key") or entry.get("data", {}).get("key")


def poll_readable(items_url, key, headers, attempts=READ_ATTEMPTS, delay=READ_DELAY):
    """Poll GET /items/<key> and return the attempts needed, or None."""
    for attempt in range(1, attempts + 1):
        status = requests.get(f"{items_url}/{key}", headers=headers, timeout=30).status_code
        print(f"poll   /items/{key} attempt {attempt}: HTTP {status}")
        if status == 200:
            return attempt
        time.sleep(delay)
    return None


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

    baseline = show(
        "GET    /items?limit=1",
        requests.get(items_url, headers=headers, params={"limit": 1}, timeout=30),
    )
    library_version = baseline.headers.get("Last-Modified-Version")
    print(f"library Last-Modified-Version={library_version!r}")

    # 1. Unversioned write (what the client does today).
    payload = [{"itemType": "note", "note": "<p>CI write-path diagnostic</p>"}]
    created = show(
        "POST   /items (unversioned)",
        requests.post(items_url, headers=headers, json=payload, timeout=30),
    )
    key = extract_key(created)
    print(f"parsed key={key!r}")

    readable_after = None
    if key:
        show(f"GET    /items/{key} (immediate)", requests.get(f"{items_url}/{key}", headers=headers, timeout=30))
        readable_after = poll_readable(items_url, key, headers)

        # 2. Does the key appear in a recent-items listing at all?
        recent = requests.get(
            items_url,
            headers=headers,
            params={"sort": "dateAdded", "direction": "desc", "limit": 10},
            timeout=30,
        )
        if recent.status_code == 200:
            keys = [item.get("key") for item in recent.json()]
            print(f"recent items (newest 10): {keys}")
            print(f"created key present in listing: {key in keys}")
        else:
            show("GET    /items?sort=dateAdded", recent)

    # 3. Versioned write, which is the other documented write contract.
    if library_version:
        versioned_headers = dict(headers)
        versioned_headers["If-Unmodified-Since-Version"] = str(library_version)
        created_v = show(
            "POST   /items (versioned)",
            requests.post(
                items_url,
                headers=versioned_headers,
                json=[{"itemType": "book", "title": "CI versioned write probe"}],
                timeout=30,
            ),
        )
        key_v = extract_key(created_v)
        print(f"parsed versioned key={key_v!r}")
        if key_v:
            time.sleep(READ_DELAY)
            show(f"GET    /items/{key_v}", requests.get(f"{items_url}/{key_v}", headers=headers, timeout=30))

    print("RESULT summary:")
    print(f"RESULT   unversioned key={key!r} readable_after_attempt={readable_after!r}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
