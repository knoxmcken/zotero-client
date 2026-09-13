#!/usr/bin/env python3
"""Diagnose the create -> delete 404 seen in the integration workflow.

Runs the write path one step at a time and prints the HTTP status and
response body for each call, so CI logs show exactly where the write
breaks. Credentials are never printed; the Zotero API key and user id
are also masked by GitHub Actions in workflow logs.

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
BODY_LIMIT = 600


def _credential_summary(value):
    """Describe a credential without revealing it."""
    return "<unset>" if not value else f"<set len={len(value)}>"


def show(label, response):
    """Print one response line, with the body flattened and truncated."""
    body = " ".join(response.text.split())[:BODY_LIMIT]
    print(f"{label}: HTTP {response.status_code} {body}")
    return response


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

    show(
        "GET    /items?limit=1",
        requests.get(items_url, headers=headers, params={"limit": 1}, timeout=30),
    )

    payload = [{"itemType": "note", "note": "<p>CI write-path diagnostic</p>"}]
    created = show(
        "POST   /items",
        requests.post(items_url, headers=headers, json=payload, timeout=30),
    )

    key = version = None
    try:
        entry = created.json().get("successful", {}).get("0", {})
        key = entry.get("key") or entry.get("data", {}).get("key")
        version = entry.get("version")
    except ValueError:
        print("POST   /items returned a non-JSON body")

    print(f"parsed key={key!r} version={version!r}")
    if not key:
        print("RESULT: POST returned no key -- cannot continue")
        return 0

    item_url = f"{items_url}/{key}"
    show(f"GET    /items/{key}", requests.get(item_url, headers=headers, timeout=30))

    delete_headers = {"Zotero-API-Key": api_key}
    if version is not None:
        delete_headers["If-Unmodified-Since-Version"] = str(version)
    deleted = show(
        f"DELETE /items/{key}",
        requests.delete(item_url, headers=delete_headers, timeout=30),
    )

    if deleted.status_code == 404:
        print("DELETE returned 404 -- retrying once after 3s to test propagation delay")
        time.sleep(3)
        deleted = show(
            f"DELETE /items/{key} (retry)",
            requests.delete(item_url, headers=delete_headers, timeout=30),
        )

    print(f"RESULT: final DELETE status={deleted.status_code}")
    if deleted.status_code == 404:
        print("RESULT: the created item never became deletable at this key")
    return 0


if __name__ == "__main__":
    sys.exit(main())
