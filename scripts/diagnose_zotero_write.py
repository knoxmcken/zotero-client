#!/usr/bin/env python3
"""Diagnose the create -> delete 404 seen in the integration workflow.

Prints the HTTP status and response body for each call in the write
path. Credentials are never printed (the Zotero key and user id are
also masked by GitHub Actions).

Established so far: POST returns 200 with a created object and the
library version advances, but the created key is never readable (404,
with or without includeTrashed) and never appears in any listing -- for
every documented write contract, over 12s+.

Every successful create so far used itemType="note". This run varies
the item type to check whether notes specifically fail to persist:

  control  note   (what the client assigns in create_item today)
  probe    book   (an ordinary bibliographic item)

Exit code is always 0 -- diagnostic only, must not fail the build.
"""

import os
import sys
import time

import requests

BASE_URL = "https://api.zotero.org"
BODY_LIMIT = 300
POLL_ATTEMPTS = 3
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


def create_and_probe(label, payload, items_url, headers):
    """Create one item and report everything we can learn about it."""
    response = show(f"[{label}] POST /items", requests.post(items_url, headers=headers, json=[payload], timeout=30))
    key = extract_key(response)
    print(f"[{label}] parsed key={key!r}")
    if not key:
        return None

    item_url = f"{items_url}/{key}"
    for attempt in range(1, POLL_ATTEMPTS + 1):
        status = requests.get(item_url, headers=headers, timeout=30).status_code
        print(f"[{label}] poll {attempt}: HTTP {status}")
        if status == 200:
            print(f"[{label}] RESULT: readable after {attempt} attempt(s)")
            return key
        time.sleep(POLL_DELAY)

    print(f"[{label}] RESULT: never readable")
    listed = listing_keys(items_url, headers) or []
    print(f"[{label}] in newest-10 listing: {key in listed}")
    return key


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
    print(f"library Last-Modified-Version={library_version(items_url, headers)!r}")

    keys = {}
    keys["note"] = create_and_probe(
        "note", {"itemType": "note", "note": "<p>CI write-path diagnostic (note)</p>"}, items_url, headers
    )
    keys["book"] = create_and_probe(
        "book", {"itemType": "book", "title": "CI write-path diagnostic (book)"}, items_url, headers
    )

    print("RESULT summary:")
    for item_type, key in keys.items():
        print(f"RESULT   {item_type}: key={key}")

    # Clean up anything that did become readable.
    for item_type, key in keys.items():
        if not key:
            continue
        item_url = f"{items_url}/{key}"
        current = requests.get(item_url, headers=headers, timeout=30)
        if current.status_code == 200:
            version = current.json().get("version")
            delete_headers = dict(headers)
            if version:
                delete_headers["If-Unmodified-Since-Version"] = str(version)
            show(f"cleanup DELETE /items/{key}", requests.delete(item_url, headers=delete_headers, timeout=30))
    return 0


if __name__ == "__main__":
    sys.exit(main())
