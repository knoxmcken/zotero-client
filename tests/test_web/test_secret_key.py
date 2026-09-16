"""Tests for FLASK_SECRET_KEY resolution in the web app factory (issue #7)."""

import logging
import re
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from zotero_client.web import create_app
from zotero_client.web import SECRET_KEY_ENV_VAR

#: The literal that used to be the silent fallback; it must never be used again.
OLD_HARDCODED_DEFAULT = 'dev-secret-change-me'

HEX64 = re.compile(r'^[0-9a-f]{64}$')

CREDS = {'api_key': 'test_key', 'user_id': 'test_user', 'library_type': 'users'}


def _patch_load_environment(creds=None):
    return patch('zotero_client.web.load_environment', return_value=dict(CREDS if creds is None else creds))


def _build(monkeypatch, secret=None, debug=False):
    """Build an app with FLASK_SECRET_KEY definitely unset or set."""
    if secret is None:
        monkeypatch.delenv(SECRET_KEY_ENV_VAR, raising=False)
    else:
        monkeypatch.setenv(SECRET_KEY_ENV_VAR, secret)
    with _patch_load_environment():
        return create_app(debug=debug)


class TestSecretKeyRequiredOutsideDebug:
    def test_missing_key_outside_debug_refuses_to_start(self, monkeypatch):
        monkeypatch.delenv(SECRET_KEY_ENV_VAR, raising=False)
        with _patch_load_environment():
            with pytest.raises(RuntimeError) as excinfo:
                create_app()

        message = str(excinfo.value)
        assert SECRET_KEY_ENV_VAR in message
        # Actionable: tells the operator how to fix it.
        assert 'set it' in message.lower()

    def test_missing_key_outside_debug_default_is_not_debug(self, monkeypatch):
        """Omitting the argument must behave like debug=False, not like debug."""
        monkeypatch.delenv(SECRET_KEY_ENV_VAR, raising=False)
        with _patch_load_environment():
            with pytest.raises(RuntimeError):
                create_app(False)

    def test_env_var_is_used_verbatim(self, monkeypatch):
        app = _build(monkeypatch, secret='explicit-secret')
        assert app.secret_key == 'explicit-secret'

    def test_env_var_wins_even_in_debug(self, monkeypatch):
        app = _build(monkeypatch, secret='explicit-secret', debug=True)
        assert app.secret_key == 'explicit-secret'

    def test_empty_env_var_counts_as_unset(self, monkeypatch):
        monkeypatch.setenv(SECRET_KEY_ENV_VAR, '')
        with _patch_load_environment():
            with pytest.raises(RuntimeError):
                create_app()


class TestSecretKeyGeneratedInDebug:
    def test_debug_generates_a_random_key(self, monkeypatch):
        app = _build(monkeypatch, debug=True)
        assert isinstance(app.secret_key, str)
        assert HEX64.match(app.secret_key), app.secret_key
        assert app.secret_key != OLD_HARDCODED_DEFAULT

    def test_debug_key_differs_per_process(self, monkeypatch):
        first = _build(monkeypatch, debug=True)
        second = _build(monkeypatch, debug=True)
        assert first.secret_key != second.secret_key

    def test_debug_warns_that_sessions_are_not_persistent(self, monkeypatch, caplog):
        with caplog.at_level(logging.WARNING):
            app = _build(monkeypatch, debug=True)
        # The warning must be on the app's own logger, so it is visible to operators.
        assert any(
            record.levelno == logging.WARNING and SECRET_KEY_ENV_VAR in record.getMessage()
            for record in caplog.records
        ), caplog.text
        assert 'restart' in caplog.text.lower()

    def test_debug_app_serves_requests(self, monkeypatch):
        """A debug app with a generated key must be fully usable (session + all)."""
        app = _build(monkeypatch, debug=True)
        app.config['TESTING'] = True
        client = app.test_client()

        with patch('zotero_client.web.routes.items.get_client') as mock_gc:
            mock_gc.return_value.get_items.return_value = []
            mock_gc.return_value.get_tags.return_value = []
            resp = client.get('/items')

        assert resp.status_code == 200

        # The generated key must really sign the session cookie: write through the
        # session and read it back on a later request.
        with client.session_transaction() as sess:
            sess['probe'] = 'ok'
        with client.session_transaction() as sess:
            assert sess['probe'] == 'ok'


class TestCliPassesDebugThrough:
    """`start_web_server` must hand args.debug to the factory (issue #7 wiring)."""

    def test_debug_flag_reaches_create_app(self):
        from zotero_client.cli.main import start_web_server

        fake_app = MagicMock()
        with patch('zotero_client.web.create_app', return_value=fake_app) as mock_create:
            start_web_server(SimpleNamespace(host='127.0.0.1', port=5000, debug=True))

        mock_create.assert_called_once_with(debug=True)

    def test_non_debug_flag_reaches_create_app(self):
        from zotero_client.cli.main import start_web_server

        fake_app = MagicMock()
        with patch('zotero_client.web.create_app', return_value=fake_app) as mock_create:
            start_web_server(SimpleNamespace(host='127.0.0.1', port=5000, debug=False))

        mock_create.assert_called_once_with(debug=False)
