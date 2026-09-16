"""Tests for the central session-backed CSRF protection (issue #8)."""

import pytest
from unittest.mock import patch

from zotero_client.web.csrf import (
    CSRF_FORM_FIELD,
    CSRF_HEADER,
    get_csrf_token,
    validate_csrf,
)
from zotero_client.web.security import check_credentials

from .conftest import CSRF_INPUT_RE, make_item


def token_from_page(client):
    """Fetch a detail page and return the CSRF token a browser would submit."""
    with patch('zotero_client.web.routes.items.get_client') as mock_gc:
        mock_gc.return_value.get_item.return_value = make_item()
        mock_gc.return_value.get_tags.return_value = []
        mock_gc.return_value.get_attachments.return_value = []
        resp = client.get('/items/ABC123')

    assert resp.status_code == 200, resp.status_code
    match = CSRF_INPUT_RE.search(resp.data)
    assert match, 'no csrf_token hidden input in the rendered detail page'
    return match.group(1).decode()


class TestTokenExposure:
    def test_detail_page_embeds_the_token(self, client, csrf_token):
        with patch('zotero_client.web.routes.items.get_client') as mock_gc:
            mock_gc.return_value.get_item.return_value = make_item()
            mock_gc.return_value.get_tags.return_value = []
            mock_gc.return_value.get_attachments.return_value = []
            resp = client.get('/items/ABC123')

        assert resp.status_code == 200
        assert b'name="csrf_token"' in resp.data
        assert csrf_token.encode() in resp.data

    def test_token_is_stable_within_a_session(self, client):
        assert token_from_page(client) == token_from_page(client)

    def test_token_survives_requests_that_never_render_it(self, client):
        first = token_from_page(client)
        with patch('zotero_client.web.routes.tags.get_client') as mock_gc:
            mock_gc.return_value.get_tags.return_value = []
            assert client.get('/tags').status_code == 200
        assert token_from_page(client) == first

    def test_tokens_differ_between_sessions(self, app):
        assert token_from_page(app.test_client()) != token_from_page(app.test_client())

    def test_get_csrf_token_creates_on_demand(self, app):
        with app.test_request_context('/items'):
            token = get_csrf_token()
            assert token
            assert get_csrf_token() == token


class TestUnsafeMethodsRequireAToken:
    @pytest.mark.parametrize('method', ['POST', 'PUT', 'PATCH', 'DELETE'])
    def test_every_unsafe_method_is_checked(self, app, method):
        with app.test_request_context('/items', method=method):
            result = validate_csrf()
        assert result is not None, f'{method} must not bypass CSRF validation'
        assert result[1] == 400

    @pytest.mark.parametrize('method', ['GET', 'HEAD', 'OPTIONS'])
    def test_safe_methods_pass(self, app, method):
        with app.test_request_context('/items', method=method):
            assert validate_csrf() is None

    def test_mismatched_token_is_rejected(self, app):
        with app.test_request_context('/items', method='POST', data={CSRF_FORM_FIELD: 'nope'}):
            result = validate_csrf()
        assert result[1] == 400


class TestDeleteRoute:
    def test_delete_without_token_does_not_call_the_api(self, client):
        with patch('zotero_client.web.routes.items.get_client') as mock_gc:
            resp = client.post('/items/ABC123/delete')
        assert resp.status_code == 400
        assert b'CSRF' in resp.data
        mock_gc.return_value.delete_item.assert_not_called()

    def test_delete_with_another_sessions_token_is_rejected(self, app, client):
        other_token = token_from_page(app.test_client())

        with patch('zotero_client.web.routes.items.get_client') as mock_gc:
            resp = client.post('/items/ABC123/delete', data={CSRF_FORM_FIELD: other_token})

        assert resp.status_code == 400
        mock_gc.return_value.delete_item.assert_not_called()

    def test_delete_with_valid_token_hits_the_success_path(self, client, csrf_token):
        with patch('zotero_client.web.routes.items.get_client') as mock_gc:
            mock_gc.return_value.delete_item.return_value = None
            resp = client.post('/items/ABC123/delete', data={CSRF_FORM_FIELD: csrf_token})
            mock_gc.return_value.delete_item.assert_called_once_with('ABC123')

        assert resp.status_code == 302
        assert '/items' in resp.headers['Location']

    def test_delete_accepts_the_header_carrier(self, client, csrf_token):
        with patch('zotero_client.web.routes.items.get_client') as mock_gc:
            mock_gc.return_value.delete_item.return_value = None
            resp = client.post('/items/ABC123/delete', headers={CSRF_HEADER: csrf_token})
            mock_gc.return_value.delete_item.assert_called_once_with('ABC123')

        assert resp.status_code == 302

    def test_credential_guard_runs_first(self, client_no_creds):
        """No creds + no token reports the actionable 503, not a CSRF 400."""
        resp = client_no_creds.post('/items/ABC123/delete')
        assert resp.status_code == 503


class TestCentralWiring:
    def test_validation_is_installed_on_the_app(self, app):
        assert validate_csrf in app.before_request_funcs.get(None, [])

    def test_token_helper_is_available_to_templates(self, app):
        assert app.jinja_env.globals['csrf_token'] is get_csrf_token

    def test_credential_guard_is_registered_before_csrf(self, app):
        hooks = app.before_request_funcs.get(None, [])
        assert hooks.index(check_credentials) < hooks.index(validate_csrf)
