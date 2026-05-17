"""Tests for tags Blueprint."""

from unittest.mock import MagicMock, patch
from zotero_client.models.tag import Tag


class TestTagsList:

    @patch('zotero_client.web.routes.tags.get_client')
    def test_tags_list_renders_names(self, mock_get_client, client):
        mock_zot = MagicMock()
        mock_zot.get_tags.return_value = [
            Tag(tag='machine-learning', type=1),
            Tag(tag='python', type=0),
        ]
        mock_get_client.return_value = mock_zot

        response = client.get('/tags')
        assert response.status_code == 200
        body = response.data.decode()
        assert 'machine-learning' in body
        assert 'python' in body
        assert 'Manual' in body
        assert 'Automatic' in body

    @patch('zotero_client.web.routes.tags.get_client')
    def test_tags_list_empty_state(self, mock_get_client, client):
        mock_zot = MagicMock()
        mock_zot.get_tags.return_value = []
        mock_get_client.return_value = mock_zot

        response = client.get('/tags')
        assert response.status_code == 200
        assert b'No tags found' in response.data

    def test_tags_missing_credentials_returns_503(self, client_no_creds):
        response = client_no_creds.get('/tags')
        assert response.status_code == 503
