"""Tests for the collections web UI routes."""

import pytest
from unittest.mock import patch
from zotero_client.models.collection import Collection


def make_collection(key='COL1', name='My Collection', parent=None):
    return Collection(key=key, name=name, parent_collection=parent, version=1)


class TestCollectionsList:
    def test_collections_renders_table(self, client):
        col = make_collection()
        with patch('zotero_client.web.routes.collections.get_client') as mock_gc:
            mock_gc.return_value.get_collections.return_value = [col]
            resp = client.get('/collections')
        assert resp.status_code == 200
        assert b'My Collection' in resp.data

    def test_collections_empty_state(self, client):
        with patch('zotero_client.web.routes.collections.get_client') as mock_gc:
            mock_gc.return_value.get_collections.return_value = []
            resp = client.get('/collections')
        assert b'No collections found' in resp.data

    def test_collections_503_when_no_creds(self, client_no_creds):
        resp = client_no_creds.get('/collections')
        assert resp.status_code == 503
