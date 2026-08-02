"""Tests for the items web UI routes."""

import pytest
from unittest.mock import patch, MagicMock
from zotero_client.models.item import Item
from zotero_client.models.tag import Tag


def make_item(key='ABC123', title='Test Item', item_type='journalArticle', date='2024'):
    return Item(
        key=key, title=title, item_type=item_type,
        creators=[{'firstName': 'Jane', 'lastName': 'Doe'}],
        date=date, url='', version=1,
    )


class TestItemsList:
    def test_root_redirects_to_items(self, client):
        resp = client.get('/')
        assert resp.status_code == 302
        assert '/items' in resp.headers['Location']

    def test_items_list_renders_table(self, client):
        item = make_item()
        with patch('zotero_client.web.routes.items.get_client') as mock_gc:
            mock_gc.return_value.get_items.return_value = [item]
            resp = client.get('/items')
        assert resp.status_code == 200
        assert b'Test Item' in resp.data

    def test_items_list_passes_search_params(self, client):
        with patch('zotero_client.web.routes.items.get_client') as mock_gc:
            mock_gc.return_value.get_items.return_value = []
            client.get('/items?q=python&type=book&tag=ml&limit=5')
            mock_gc.return_value.get_items.assert_called_once_with(
                q='python', item_type='book', tag='ml', limit=5
            )

    def test_items_list_empty_state(self, client):
        with patch('zotero_client.web.routes.items.get_client') as mock_gc:
            mock_gc.return_value.get_items.return_value = []
            resp = client.get('/items')
        assert b'No items found' in resp.data

    def test_items_list_api_error_flashes(self, client):
        with patch('zotero_client.web.routes.items.get_client') as mock_gc:
            mock_gc.return_value.get_items.side_effect = Exception('API down')
            resp = client.get('/items')
        assert b'Error fetching items' in resp.data

    def test_items_list_503_when_no_creds(self, client_no_creds):
        resp = client_no_creds.get('/items')
        assert resp.status_code == 503
        assert b'credentials' in resp.data.lower()


class TestItemDetail:
    def test_detail_renders_fields(self, client):
        item = make_item()
        with patch('zotero_client.web.routes.items.get_client') as mock_gc:
            mock_gc.return_value.get_item.return_value = item
            mock_gc.return_value.get_tags.return_value = []
            mock_gc.return_value.get_attachments.return_value = []
            resp = client.get('/items/ABC123')
        assert resp.status_code == 200
        assert b'Test Item' in resp.data
        assert b'ABC123' in resp.data

    def test_detail_renders_tags(self, client):
        item = make_item()
        tag = Tag(tag='science', type=0)
        with patch('zotero_client.web.routes.items.get_client') as mock_gc:
            mock_gc.return_value.get_item.return_value = item
            mock_gc.return_value.get_tags.return_value = [tag]
            mock_gc.return_value.get_attachments.return_value = []
            resp = client.get('/items/ABC123')
        assert b'science' in resp.data

    def test_detail_404_on_missing_item(self, client):
        with patch('zotero_client.web.routes.items.get_client') as mock_gc:
            mock_gc.return_value.get_item.side_effect = Exception('Not found')
            resp = client.get('/items/MISSING')
        assert resp.status_code == 404

    def test_detail_503_when_no_creds(self, client_no_creds):
        resp = client_no_creds.get('/items/ABC123')
        assert resp.status_code == 503


class TestDeleteItem:
    def test_delete_redirects_to_list(self, client):
        with patch('zotero_client.web.routes.items.get_client') as mock_gc:
            mock_gc.return_value.delete_item.return_value = None
            resp = client.post('/items/ABC123/delete')
        assert resp.status_code == 302
        assert '/items' in resp.headers['Location']

    def test_delete_calls_api(self, client):
        with patch('zotero_client.web.routes.items.get_client') as mock_gc:
            mock_gc.return_value.delete_item.return_value = None
            client.post('/items/ABC123/delete')
            mock_gc.return_value.delete_item.assert_called_once_with('ABC123')

    def test_delete_503_when_no_creds(self, client_no_creds):
        resp = client_no_creds.post('/items/ABC123/delete')
        assert resp.status_code == 503
