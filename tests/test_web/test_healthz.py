"""Tests for the /healthz platform healthcheck endpoint."""

from unittest.mock import patch


def test_healthz_ok_without_calling_zotero(client):
    with patch('zotero_client.web.get_client') as mock_gc:
        resp = client.get('/healthz')

    assert resp.status_code == 200
    assert resp.get_json() == {'status': 'ok'}
    mock_gc.assert_not_called()


def test_healthz_fails_when_credentials_missing(client_no_creds):
    resp = client_no_creds.get('/healthz')

    assert resp.status_code == 503
