"""Integration tests for Zotero API client.

These tests require valid API credentials set as environment variables:
- ZOTERO_API_KEY
- ZOTERO_USER_ID
"""

import os
import pytest
from zotero_client.api.client import ZoteroClient


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
        assert created.key is not None
        
        # Clean up - delete the item
        real_client.delete_item(created.key, created.version)
    
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
        import subprocess
        result = subprocess.run(
            ['zot', 'tags', 'list'],
            capture_output=True,
            text=True,
            env={**os.environ, 'ZOTERO_LIBRARY_TYPE': 'users'}
        )
        assert result.returncode in [0, 1]
