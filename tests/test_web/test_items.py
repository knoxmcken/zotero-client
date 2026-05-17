"""Tests for items Blueprint."""

import pytest
from unittest.mock import MagicMock, patch
from zotero_client.models.item import Item


def make_item(**kwargs):
    defaults = dict(
        key='ITEM1', version=1, item_type='book', title='Test Book',
        creators=[], date='2023', url='', abstract_note=None,
        parent_item=None, links={},
    )
    defaults.update(kwargs)
    return Item(**defaults)


class TestItemsList:

    def test_redirects_root_to_items(self, client):
        response = client.get('/')
        assert response.status_code == 302
        assert '/items' in response.headers['Location']

    @patch('zotero_client.web.routes.items.get_client')
    def test_items_list_renders_table(self, mock_get_client, client):
        mock_zot = MagicMock()
        mock_zot.get_items.return_value = [
            make_item(key='A1', title='Alpha'),
            make_item(key='B2', title='Beta'),
        ]
        mock_get_client.return_value = mock_zot

        response = client.get('/items')
        assert response.status_code == 200
        body = response.data.decode()
        assert 'Alpha' in body
        assert 'Beta' in body

    @patch('zotero_client.web.routes.items.get_client')
    def test_items_list_passes_search_params(self, mock_get_client, client):
        mock_zot = MagicMock()
        mock_zot.get_items.return_value = []
        mock_get_client.return_value = mock_zot

        client.get('/items?q=python&type=book&tag=ml&limit=5')

        mock_zot.get_items.assert_called_once_with(
            limit=5, q='python', item_type='book', tag='ml'
        )

    @patch('zotero_client.web.routes.items.get_client')
    def test_items_list_empty_state(self, mock_get_client, client):
        mock_zot = MagicMock()
        mock_zot.get_items.return_value = []
        mock_get_client.return_value = mock_zot

        response = client.get('/items')
        assert response.status_code == 200
        assert b'No items found' in response.data

    @patch('zotero_client.web.routes.items.get_client')
    def test_items_list_api_error_shows_flash(self, mock_get_client, client):
        import requests as req
        mock_zot = MagicMock()
        err = req.HTTPError(response=MagicMock(status_code=403))
        mock_zot.get_items.side_effect = err
        mock_get_client.return_value = mock_zot

        response = client.get('/items')
        assert response.status_code == 200
        assert b'Invalid API key' in response.data

    def test_items_list_missing_credentials_returns_503(self, client_no_creds):
        response = client_no_creds.get('/items')
        assert response.status_code == 503
        assert b'credentials' in response.data.lower()


class TestItemDetail:

    @patch('zotero_client.web.routes.items.get_client')
    def test_detail_renders_item_fields(self, mock_get_client, client):
        mock_zot = MagicMock()
        mock_zot.get_item.return_value = make_item(
            key='ITEM1', title='My Book', abstract_note='Great abstract',
            creators=[{'firstName': 'Jane', 'lastName': 'Doe'}],
        )
        mock_zot.get_tags.return_value = []
        mock_zot.get_attachments.return_value = []
        mock_get_client.return_value = mock_zot

        response = client.get('/items/ITEM1')
        assert response.status_code == 200
        body = response.data.decode()
        assert 'My Book' in body
        assert 'Great abstract' in body
        assert 'Jane' in body

    @patch('zotero_client.web.routes.items.get_client')
    def test_detail_shows_tags(self, mock_get_client, client):
        from zotero_client.models.tag import Tag
        mock_zot = MagicMock()
        mock_zot.get_item.return_value = make_item()
        mock_zot.get_tags.return_value = [Tag(tag='python', type=1)]
        mock_zot.get_attachments.return_value = []
        mock_get_client.return_value = mock_zot

        response = client.get('/items/ITEM1')
        assert b'python' in response.data

    @patch('zotero_client.web.routes.items.get_client')
    def test_detail_404_on_missing_item(self, mock_get_client, client):
        import requests as req
        mock_zot = MagicMock()
        err = req.HTTPError(response=MagicMock(status_code=404))
        mock_zot.get_item.side_effect = err
        mock_get_client.return_value = mock_zot

        response = client.get('/items/MISSING')
        assert response.status_code == 404

    def test_detail_missing_credentials_returns_503(self, client_no_creds):
        response = client_no_creds.get('/items/X')
        assert response.status_code == 503


class TestDeleteItem:

    @patch('zotero_client.web.routes.items.get_client')
    def test_delete_redirects_to_list(self, mock_get_client, client):
        mock_zot = MagicMock()
        mock_zot.get_item.return_value = make_item(key='ITEM1', version=3)
        mock_get_client.return_value = mock_zot

        response = client.post('/items/ITEM1/delete')
        assert response.status_code == 302
        assert '/items' in response.headers['Location']

    @patch('zotero_client.web.routes.items.get_client')
    def test_delete_calls_delete_item(self, mock_get_client, client):
        mock_zot = MagicMock()
        mock_zot.get_item.return_value = make_item(key='ITEM1', version=3)
        mock_get_client.return_value = mock_zot

        client.post('/items/ITEM1/delete')
        mock_zot.delete_item.assert_called_once_with('ITEM1', 3)

    def test_delete_missing_credentials_returns_503(self, client_no_creds):
        response = client_no_creds.post('/items/X/delete')
        assert response.status_code == 503
