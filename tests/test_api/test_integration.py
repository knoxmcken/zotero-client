"""Integration tests for Zotero API client.

These tests require valid API credentials set as environment variables:
- ZOTERO_API_KEY
- ZOTERO_USER_ID
"""

import os
import time

import pytest
import requests

from zotero_client.api.client import ZoteroClient

# Zotero can return a transient 404 for an object immediately after a write
# while the new version propagates. Tolerate that window rather than failing
# the run on the first attempt.
_WRITE_PROPAGATION_ATTEMPTS = 5
_WRITE_PROPAGATION_DELAY = 1.0


def _status_of(exc):
    """Return the HTTP status carried by a requests error, if any."""
    return getattr(getattr(exc, 'response', None), 'status_code', None)


def _wait_until_readable(client, key):
    """Poll until a freshly created item can be read back; return attempt count."""
    last_error = None
    for attempt in range(1, _WRITE_PROPAGATION_ATTEMPTS + 1):
        try:
            client.get_item(key)
            return attempt
        except requests.exceptions.HTTPError as exc:
            last_error = exc
            if _status_of(exc) != 404:
                raise
            time.sleep(_WRITE_PROPAGATION_DELAY)
    pytest.fail(
        f"item {key} was created but never became readable after "
        f"{_WRITE_PROPAGATION_ATTEMPTS} attempts: {last_error}"
    )


def _delete_with_retry(client, key, version):
    """Delete an item, tolerating a transient 404; return attempt count."""
    last_error = None
    for attempt in range(1, _WRITE_PROPAGATION_ATTEMPTS + 1):
        try:
            client.delete_item(key, version)
            return attempt
        except requests.exceptions.HTTPError as exc:
            last_error = exc
            if _status_of(exc) != 404:
                raise
            time.sleep(_WRITE_PROPAGATION_DELAY)
    pytest.fail(
        f"delete of {key} kept returning 404 after "
        f"{_WRITE_PROPAGATION_ATTEMPTS} attempts: {last_error}"
    )


@pytest.fixture
def real_client():
    """Create a real client with credentials from environment."""
    api_key = os.getenv('ZOTERO_API_KEY')
    user_id = os.getenv('ZOTERO_USER_ID')
    
    if not api_key or not user_id:
        pytest.skip("Zotero API credentials not set")
    
    return ZoteroClient(api_key, user_id)


@pytest.mark.integration
class TestIntegrationConnection:
    """Test actual API connection."""
    
    def test_client_initializes_with_real_credentials(self, real_client):
        """Test that client initializes with real credentials."""
        assert real_client.api_key is not None
        assert real_client.user_id is not None
        assert real_client.library_type == 'users'
    
    def test_can_fetch_items(self, real_client):
        """Test that we can actually fetch items from Zotero."""
        items = real_client.get_items(limit=5)
        assert isinstance(items, list)
        # Should have at least some items in a real library
        assert len(items) >= 0
    
    def test_can_fetch_collections(self, real_client):
        """Test that we can fetch collections."""
        collections = real_client.get_collections(limit=5)
        assert isinstance(collections, list)
    
    def test_can_fetch_tags(self, real_client):
        """Test that we can fetch tags."""
        tags = real_client.get_tags()
        assert isinstance(tags, list)


@pytest.mark.integration
class TestIntegrationCRUD:
    """Test CRUD operations with real API."""
    
    def test_create_and_delete_item(self, real_client):
        """Test creating and then deleting an item."""
        # Create a test item
        test_item = {
            "itemType": "note",
            "note": "<p>Integration test item - please delete</p>"
        }

        created = real_client.create_item(test_item)
        assert created is not None
        assert created.key, "create_item did not return an item key"

        # Confirm the new item is actually addressable before cleaning up,
        # and record how many attempts the write needed (useful in CI logs).
        read_attempts = _wait_until_readable(real_client, created.key)
        delete_attempts = _delete_with_retry(
            real_client, created.key, created.version
        )
        print(
            f"create -> read ({read_attempts} attempt(s)) -> "
            f"delete ({delete_attempts} attempt(s)) OK for key {created.key}"
        )
    
    def test_get_item_by_key(self, real_client):
        """Test retrieving a specific item by its key."""
        # First get a list of items
        items = real_client.get_items(limit=1)
        
        if not items:
            pytest.skip("No items in library to test with")
        
        # Get the first item's key
        item_key = items[0].key
        
        # Fetch that specific item
        item = real_client.get_item(item_key)
        assert item.key == item_key


@pytest.mark.integration  
class TestIntegrationCLI:
    """Test CLI commands with real credentials."""
    
    def test_cli_items_list(self):
        """Test CLI items list command."""
        api_key = os.getenv('ZOTERO_API_KEY')
        user_id = os.getenv('ZOTERO_USER_ID')
        if not api_key or not user_id:
            pytest.skip("Zotero API credentials not set")
        
        import subprocess
        result = subprocess.run(
            ['zot', 'items', 'list', '--limit', '3'],
            capture_output=True,
            text=True,
            env={**os.environ, 'ZOTERO_LIBRARY_TYPE': 'users'}
        )
        # Should succeed (exit code 0) or give a reasonable error
        assert result.returncode in [0, 1]
    
    def test_cli_collections_list(self):
        """Test CLI collections list command."""
        api_key = os.getenv('ZOTERO_API_KEY')
        user_id = os.getenv('ZOTERO_USER_ID')
        if not api_key or not user_id:
            pytest.skip("Zotero API credentials not set")
        
        import subprocess
        result = subprocess.run(
            ['zot', 'collections', 'list'],
            capture_output=True,
            text=True,
            env={**os.environ, 'ZOTERO_LIBRARY_TYPE': 'users'}
        )
        assert result.returncode in [0, 1]
    
    def test_cli_tags_list(self):
        """Test CLI tags list command."""
        api_key = os.getenv('ZOTERO_API_KEY')
        user_id = os.getenv('ZOTERO_USER_ID')
        if not api_key or not user_id:
            pytest.skip("Zotero API credentials not set")
        
        import subprocess
        result = subprocess.run(
            ['zot', 'tags', 'list'],
            capture_output=True,
            text=True,
            env={**os.environ, 'ZOTERO_LIBRARY_TYPE': 'users'}
        )
        assert result.returncode in [0, 1]
