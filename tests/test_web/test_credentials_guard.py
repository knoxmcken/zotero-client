"""Tests for the single application-wide credential guard (issue #9)."""

import pytest
from unittest.mock import MagicMock, patch
from flask import Blueprint

from zotero_client.web.security import PUBLIC_ENDPOINTS, check_credentials
from zotero_client.web.routes.items import items_bp
from zotero_client.web.routes.collections import collections_bp
from zotero_client.web.routes.tags import tags_bp


def _probe_blueprint():
    """A brand new blueprint, as a future contributor would add it."""
    bp = Blueprint('probe', __name__)

    @bp.route('/probe')
    def probe():
        return 'probe ok'

    return bp


class TestExistingRoutesStillGated:
    """The three pre-existing 503 cases, now served by the shared guard."""

    @pytest.mark.parametrize('path', ['/items', '/items/ABC123', '/collections', '/tags'])
    def test_503_when_no_creds(self, client_no_creds, path):
        resp = client_no_creds.get(path)
        assert resp.status_code == 503
        assert b'credentials' in resp.data.lower()

    def test_guard_renders_the_same_message(self, client_no_creds):
        resp = client_no_creds.get('/items')
        assert b'ZOTERO_API_KEY' in resp.data
        assert b'ZOTERO_USER_ID' in resp.data

    def test_creds_present_passes_through(self, client):
        with patch('zotero_client.web.routes.items.get_client') as mock_gc:
            mock_gc.return_value.get_items.return_value = []
            mock_gc.return_value.get_tags.return_value = []
            resp = client.get('/items')
        assert resp.status_code == 200


class TestNotSkippable:
    """A new blueprint must be gated without doing anything special."""

    def test_new_blueprint_is_gated(self, app_no_creds):
        app_no_creds.register_blueprint(_probe_blueprint())
        resp = app_no_creds.test_client().get('/probe')
        assert resp.status_code == 503
        assert b'credentials' in resp.data.lower()

    def test_new_blueprint_works_when_creds_present(self, app):
        app.register_blueprint(_probe_blueprint())
        resp = app.test_client().get('/probe')
        assert resp.status_code == 200
        assert b'probe ok' in resp.data

    def test_route_registered_directly_on_app_is_gated(self, app_no_creds):
        @app_no_creds.route('/direct')
        def direct():
            return 'direct ok'

        resp = app_no_creds.test_client().get('/direct')
        assert resp.status_code == 503

    def test_unknown_url_still_404s_without_creds(self, client_no_creds):
        """No endpoint matched, so Flask's own 404 wins over the guard."""
        assert client_no_creds.get('/definitely-not-a-route').status_code == 404

    def test_static_endpoint_stays_public(self, client_no_creds):
        """The allowlist keeps asset serving reachable without credentials."""
        assert PUBLIC_ENDPOINTS == frozenset({'static'})
        resp = client_no_creds.get('/static/nonexistent.css')
        assert resp.status_code != 503


class TestSingleDefinition:
    def test_no_per_blueprint_copies_remain(self):
        """The guard must exist once, not once per route module."""
        for bp in (items_bp, collections_bp, tags_bp):
            assert not bp.before_request_funcs, (
                f'{bp.name} still registers its own before_request hook'
            )

    def test_guard_is_installed_on_the_app(self, app, app_no_creds):
        for application in (app, app_no_creds):
            hooks = application.before_request_funcs.get(None, [])
            assert check_credentials in hooks
