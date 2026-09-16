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
def test_app_can_load_template(template):
    """Jinja resolves the template through the app, not just on disk."""
    app = create_app()
    assert app.jinja_env.get_template(template).name == template
