"""Tests for the tags web UI routes."""

import pytest
from unittest.mock import patch
from zotero_client.models.tag import Tag


class TestTagsList:
    def test_tags_renders_table(self, client):
        tag = Tag(tag='python', type=0)
        with patch('zotero_client.web.routes.tags.get_client') as mock_gc:
            mock_gc.return_value.get_tags.return_value = [tag]
            resp = client.get('/tags')
        assert resp.status_code == 200
        assert b'python' in resp.data

    def test_tags_empty_state(self, client):
        with patch('zotero_client.web.routes.tags.get_client') as mock_gc:
            mock_gc.return_value.get_tags.return_value = []
            resp = client.get('/tags')
        assert b'No tags found' in resp.data

    def test_tags_503_when_no_creds(self, client_no_creds):
        resp = client_no_creds.get('/tags')
        assert resp.status_code == 503
