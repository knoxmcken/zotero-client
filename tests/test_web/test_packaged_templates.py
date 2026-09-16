"""Guard that the web templates actually ship with the distribution.

The templates live in ``zotero_client/web/templates`` and reach an installed
wheel only through ``[tool.setuptools.package-data]``. A wheel built without
that entry still imports and still starts, but every page 500s on a missing
template -- which is exactly how the bug reached main.

This file is deliberately credentials-free and network-free so it can run in
the ordinary unit suite, and it is also the check the ``packaged-wheel`` CI job
runs from a clean environment where only the built wheel is importable.
"""

import importlib.resources

import pytest

from zotero_client.web import create_app

#: create_app() refuses to start without a signing key outside debug mode, so
#: this file supplies one rather than relying on a default. Kept local (rather
#: than imported from conftest) because the packaged-wheel CI job runs this file
#: from a clean environment where only the built wheel is importable.
TEST_SECRET_KEY = 'packaged-templates-test-key'

# Every template the app can render. Keep in sync with
# zotero_client/web/templates/.
TEMPLATES = (
    'base.html',
    'error.html',
    'items/list.html',
    'items/detail.html',
    'collections/list.html',
    'tags/list.html',
)


@pytest.fixture
def secret_key(monkeypatch):
    """Give create_app() a signing key (see #7)."""
    monkeypatch.setenv('FLASK_SECRET_KEY', TEST_SECRET_KEY)
    return TEST_SECRET_KEY


def _templates_root():
    return importlib.resources.files('zotero_client.web') / 'templates'


@pytest.mark.parametrize('template', TEMPLATES)
def test_template_is_packaged(template):
    """The template file is present inside the installed package data."""
    packaged = _templates_root() / template
    assert packaged.is_file(), (
        f"{template} is missing from the packaged templates at {packaged}; "
        "check [tool.setuptools.package-data] in pyproject.toml"
    )


@pytest.mark.parametrize('template', TEMPLATES)
def test_app_can_load_template(secret_key, template):
    """Jinja resolves the template through the app, not just on disk."""
    app = create_app()
    assert app.jinja_env.get_template(template).name == template
