"""Unit tests for the export functionality of the Zotero API client."""

import unittest
from unittest.mock import patch, MagicMock
from zotero_client.api.client import ZoteroClient

class TestZoteroClientExport(unittest.TestCase):
    """Test cases for the ZoteroClient export methods."""

    def setUp(self):
        """Set up the test client."""
        self.client = ZoteroClient(api_key='test_api_key', user_id='test_user_id')

    @patch('requests.get')
    def test_export_items_bibtex(self, mock_get):
        """Test exporting items to BibTeX format."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = '@book{key1, title="Test Book"}'
        mock_get.return_value = mock_response

        bibtex_data = self.client.export_items(format='bibtex')

        self.assertEqual(bibtex_data, '@book{key1, title="Test Book"}')
        mock_get.assert_called_once_with(
            f'{self.client.BASE_URL}/{self.client.library_type}/{self.client.user_id}/items',
            headers=self.client.headers,
            params={'format': 'bibtex'}
        )

    @patch('requests.get')
    def test_export_items_csv(self, mock_get):
        """Test exporting items to CSV format."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = 'key,title\nkey1,"Test Book"'
        mock_get.return_value = mock_response

        csv_data = self.client.export_items(format='csv')

        self.assertEqual(csv_data, 'key,title\nkey1,"Test Book"')
        mock_get.assert_called_once_with(
            f'{self.client.BASE_URL}/{self.client.library_type}/{self.client.user_id}/items',
            headers=self.client.headers,
            params={'format': 'csv'}
        )

if __name__ == '__main__':
    unittest.main()
