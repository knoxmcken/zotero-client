"""Shared fixtures for web UI tests."""

import os
import re
import pytest
from unittest.mock import patch
from zotero_client.models.item import Item
from zotero_client.web import create_app

#: The app refuses to start without FLASK_SECRET_KEY outside debug mode, so the
#: fixtures below supply one explicitly rather than relying on a default.
TEST_SECRET_KEY = 'test-secret-key'

#: Pulls the token out of the rendered form, the way a browser would.
CSRF_INPUT_RE = re.compile(rb'name="csrf_token"[^>]*value="([^"]+)"')


def make_item(key='ABC123', title='Test Item', item_type='journalArticle', date='2024'):
    """A minimal item, shared by the web tests."""
    return Item(
        key=key, title=title, item_type=item_type,
        creators=[{'firstName': 'Jane', 'lastName': 'Doe'}],
        date=date, url='', version=1,
    )


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


@pytest.fixture
def csrf_token(client):
    """A real CSRF token, harvested from the rendered detail page.

    Going through the page (rather than the session directly) means these tests
    also fail if the hidden input disappears from the template.
    """
    with patch('zotero_client.web.routes.items.get_client') as mock_gc:
        mock_gc.return_value.get_item.return_value = make_item()
        mock_gc.return_value.get_tags.return_value = []
        mock_gc.return_value.get_attachments.return_value = []
        resp = client.get('/items/ABC123')

    assert resp.status_code == 200, resp.status_code
    match = CSRF_INPUT_RE.search(resp.data)
    assert match, 'no csrf_token hidden input in the rendered detail page'
    return match.group(1).decode()
