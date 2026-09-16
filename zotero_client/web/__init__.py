"""Flask web application for the Zotero client."""

import os
import secrets
from flask import Flask, render_template
from zotero_client.api.client import ZoteroClient
from zotero_client.utils.config import load_environment

#: Environment variable holding the session-cookie signing key.
SECRET_KEY_ENV_VAR = 'FLASK_SECRET_KEY'

_MISSING_SECRET_KEY_MESSAGE = (
    "{var} is not set. The Flask session cookie is signed with this value, so the web UI "
    "refuses to start without it. Set it in your environment or .env file, for example:\n"
    "  {var}=$(python -c 'import secrets; print(secrets.token_hex(32))')\n"
    "For a throwaway local run use `zot web --debug`, which generates a random per-process "
    "key instead."
).format(var=SECRET_KEY_ENV_VAR)


def _configure_secret_key(app, debug):
    """Resolve the session signing key, refusing to invent one in production.

    A silent fallback would leave a deployment that forgot to set the environment
    variable looking healthy while signing cookies with a value published in the
    source tree, so anyone who can reach the app could forge a session.
    """
    key = os.getenv(SECRET_KEY_ENV_VAR)
    if key:
        app.secret_key = key
        return

    if debug:
        app.secret_key = secrets.token_hex(32)
        app.logger.warning(
            "%s is not set; generated a random per-process session key because debug mode "
            "is on. Sessions (flash messages, CSRF tokens) will not survive a restart.",
            SECRET_KEY_ENV_VAR,
        )
        return

    raise RuntimeError(_MISSING_SECRET_KEY_MESSAGE)


def get_client(app):
    """Create a ZoteroClient from the current app config."""
    return ZoteroClient(
        api_key=app.config['ZOTERO_API_KEY'],
        user_id=app.config['ZOTERO_USER_ID'],
        openai_api_key=app.config.get('OPENAI_API_KEY'),
        library_type=app.config['ZOTERO_LIB_TYPE'],
    )


def create_app(debug=False):
    """Application factory.

    Args:
        debug: Development mode. Only in this mode may a random session key be
            generated when ``FLASK_SECRET_KEY`` is unset.
    """
    app = Flask(__name__, template_folder='templates', static_folder='static')
    _configure_secret_key(app, debug)

    cfg = load_environment()
    app.config['ZOTERO_API_KEY'] = cfg.get('api_key') or ''
    app.config['ZOTERO_USER_ID'] = cfg.get('user_id') or ''
    app.config['ZOTERO_LIB_TYPE'] = cfg.get('library_type', 'users')
    app.config['OPENAI_API_KEY'] = os.getenv('OPENAI_API_KEY')
    app.config['CREDENTIALS_MISSING'] = not (
        app.config['ZOTERO_API_KEY'] and app.config['ZOTERO_USER_ID']
    )

    from zotero_client.web.routes.items import items_bp
    from zotero_client.web.routes.collections import collections_bp
    from zotero_client.web.routes.tags import tags_bp

    app.register_blueprint(items_bp)
    app.register_blueprint(collections_bp)
    app.register_blueprint(tags_bp)

    @app.errorhandler(404)
    def not_found(e):
        return render_template('error.html', code=404, message='Page not found.'), 404

    @app.errorhandler(500)
    def server_error(e):
        return render_template('error.html', code=500, message='Internal server error.'), 500

    return app
