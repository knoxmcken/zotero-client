"""Tests for Zotero API client."""

import unittest
from unittest.mock import Mock, patch
from zotero_client.api.client import ZoteroClient


class TestZoteroClient(unittest.TestCase):
    """Test cases for ZoteroClient."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.api_key = 'test_api_key'
        self.user_id = 'test_user_id'
        self.client = ZoteroClient(self.api_key, self.user_id)
    
    def test_client_initialization(self):
        """Test client initialization."""
        self.assertEqual(self.client.api_key, self.api_key)
        self.assertEqual(self.client.user_id, self.user_id)
        self.assertEqual(self.client.library_type, 'users')
    
    @patch('zotero_client.api.client.requests.get')
    def test_get_items(self, mock_get):
        """Test getting items."""
        mock_response = Mock()
        mock_response.json.return_value = [{'data': {'title': 'Test Item'}}]
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        items = self.client.get_items()
        
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]['data']['title'], 'Test Item')


if __name__ == '__main__':
    unittest.main()
