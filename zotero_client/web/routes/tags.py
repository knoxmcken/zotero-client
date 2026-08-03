"""Tags blueprint for the web UI."""

from flask import Blueprint, render_template, current_app, flash
from zotero_client.web import get_client

tags_bp = Blueprint('tags', __name__)


@tags_bp.before_request
def check_credentials():
    if current_app.config.get('CREDENTIALS_MISSING'):
        return render_template(
            'error.html',
            code=503,
            message='Zotero credentials are not configured. Set ZOTERO_API_KEY and ZOTERO_USER_ID in your .env file.',
        ), 503


@tags_bp.route('/tags')
def list_tags():
    client = get_client(current_app)
    try:
        tags = client.get_tags()
    except Exception as e:
        flash(f'Error fetching tags: {e}', 'danger')
        tags = []
    return render_template('tags/list.html', tags=tags)
