"""Shared fixtures for web UI tests."""

import os
import pytest
from unittest.mock import patch
from zotero_client.web import create_app

#: The app refuses to start without FLASK_SECRET_KEY outside debug mode, so the
#: fixtures below supply one explicitly rather than relying on a default.
TEST_SECRET_KEY = 'test-secret-key'


def _env_with_secret_key():
    """Patch os.environ so create_app sees a signing key."""
    return patch.dict(os.environ, {'FLASK_SECRET_KEY': TEST_SECRET_KEY})


@pytest.fixture
def app():
    with _env_with_secret_key(), patch('zotero_client.web.load_environment') as mock_env:
        mock_env.return_value = {
            'api_key': 'test_key',
            'user_id': 'test_user',
            'library_type': 'users',
        }
        application = create_app()
        application.config['TESTING'] = True
    return application


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def app_no_creds():
    with _env_with_secret_key(), patch('zotero_client.web.load_environment') as mock_env:
        mock_env.return_value = {
            'api_key': '',
            'user_id': '',
            'library_type': 'users',
        }
        application = create_app()
        application.config['TESTING'] = True
    return application


@pytest.fixture
def client_no_creds(app_no_creds):
    return app_no_creds.test_client()
