"""Flask web UI for zotero-client."""

import os
from flask import Flask, render_template
from zotero_client.utils.config import load_environment
from zotero_client.api.client import ZoteroClient


def get_client(app):
    """Instantiate ZoteroClient from app config. Called per request."""
    return ZoteroClient(
        api_key=app.config['ZOTERO_API_KEY'],
        user_id=app.config['ZOTERO_USER_ID'],
        openai_api_key=app.config.get('OPENAI_API_KEY'),
        library_type=app.config['ZOTERO_LIB_TYPE'],
    )


def create_app():
    """Flask application factory."""
    app = Flask(__name__, template_folder='templates', static_folder='static')
    app.secret_key = os.getenv('FLASK_SECRET_KEY', 'dev-secret-change-me')

    cfg = load_environment()
    app.config['ZOTERO_API_KEY'] = cfg.get('api_key') or ''
    app.config['ZOTERO_USER_ID'] = cfg.get('user_id') or ''
    app.config['ZOTERO_LIB_TYPE'] = cfg.get('library_type', 'users')
    app.config['OPENAI_API_KEY'] = os.getenv('OPENAI_API_KEY')
    app.config['CREDENTIALS_MISSING'] = not (
        app.config['ZOTERO_API_KEY'] and app.config['ZOTERO_USER_ID']
    )

    from .routes.items import items_bp
    from .routes.collections import collections_bp
    from .routes.tags import tags_bp

    app.register_blueprint(items_bp)
    app.register_blueprint(collections_bp)
    app.register_blueprint(tags_bp)

    @app.errorhandler(404)
    def not_found(e):
        return render_template('error.html', message='Page not found.'), 404

    @app.errorhandler(500)
    def server_error(e):
        return render_template('error.html', message='An unexpected error occurred.'), 500

    return app
