"""Tests for collections Blueprint."""

from unittest.mock import MagicMock, patch
from zotero_client.models.collection import Collection


def make_collection(**kwargs):
    defaults = dict(key='COL1', name='My Collection', version=1, parent_collection=None)
    defaults.update(kwargs)
    return Collection(**defaults)


class TestCollectionsList:

    @patch('zotero_client.web.routes.collections.get_client')
    def test_collections_list_renders_names(self, mock_get_client, client):
        mock_zot = MagicMock()
        mock_zot.get_collections.return_value = [
            make_collection(name='Research'),
            make_collection(key='COL2', name='Papers'),
        ]
        mock_get_client.return_value = mock_zot

        response = client.get('/collections')
        assert response.status_code == 200
        body = response.data.decode()
        assert 'Research' in body
        assert 'Papers' in body

    @patch('zotero_client.web.routes.collections.get_client')
    def test_collections_list_empty_state(self, mock_get_client, client):
        mock_zot = MagicMock()
        mock_zot.get_collections.return_value = []
        mock_get_client.return_value = mock_zot

        response = client.get('/collections')
        assert response.status_code == 200
        assert b'No collections found' in response.data

    def test_collections_missing_credentials_returns_503(self, client_no_creds):
        response = client_no_creds.get('/collections')
        assert response.status_code == 503
