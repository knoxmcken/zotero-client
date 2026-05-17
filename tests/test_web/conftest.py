"""Shared fixtures for web UI tests."""

import pytest
from unittest.mock import patch
from zotero_client.web import create_app


@pytest.fixture
def app():
    with patch('zotero_client.web.load_environment') as mock_env:
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
    """App with missing credentials."""
    with patch('zotero_client.web.load_environment') as mock_env:
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
