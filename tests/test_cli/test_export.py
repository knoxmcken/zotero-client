"""Unit tests for the export CLI command."""

import unittest
from unittest.mock import patch, MagicMock
import os
import io
from zotero_client.cli.main import main

class TestExportCLI(unittest.TestCase):
    """Test cases for the `cl export` command."""

    @patch('zotero_client.cli.main.ZoteroClient')
    def test_export_bibtex_stdout(self, MockZoteroClient):
        """Test exporting to BibTeX format and printing to stdout."""
        mock_client = MockZoteroClient.return_value
        mock_client.export_items.return_value = '@book{key1, title="Test Book"}'

        with patch('sys.stdout', new_callable=io.StringIO) as mock_stdout:
            with patch('sys.argv', ['cl', 'export', '--format', 'bibtex']):
                main()
                self.assertEqual(mock_stdout.getvalue().strip(), '@book{key1, title="Test Book"}')

    @patch('zotero_client.cli.main.ZoteroClient')
    def test_export_csv_to_file(self, MockZoteroClient):
        """Test exporting to CSV format and saving to a file."""
        mock_client = MockZoteroClient.return_value
        mock_client.export_items.return_value = 'key,title\nkey1,"Test Book"'
        output_file = 'test_export.csv'

        with patch('sys.argv', ['cl', 'export', '--format', 'csv', '--output', output_file]):
            main()

        self.assertTrue(os.path.exists(output_file))
        with open(output_file, 'r', encoding='utf-8') as f:
            content = f.read()
            self.assertEqual(content, 'key,title\nkey1,"Test Book"')
        os.remove(output_file)

if __name__ == '__main__':
    unittest.main()

