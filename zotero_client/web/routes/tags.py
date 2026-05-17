"""Tags Blueprint."""

import requests as http_requests
from flask import (
    Blueprint, current_app, flash, render_template,
)
from zotero_client.web import get_client

tags_bp = Blueprint('tags', __name__)


@tags_bp.before_request
def require_credentials():
    if current_app.config.get('CREDENTIALS_MISSING'):
        return render_template(
            'error.html',
            message='Zotero credentials are not configured. '
                    'Set ZOTERO_API_KEY and ZOTERO_USER_ID in your .env file.',
        ), 503


@tags_bp.route('/tags')
def list_tags():
    client = get_client(current_app)
    try:
        tags = client.get_tags()
    except http_requests.HTTPError as e:
        status = e.response.status_code if e.response is not None else 0
        if status in (401, 403):
            flash('Invalid API key or insufficient permissions.', 'danger')
        else:
            flash(f'Zotero API error: {e}', 'danger')
        tags = []
    except Exception as e:
        flash(f'Error fetching tags: {e}', 'danger')
        tags = []

    return render_template('tags/list.html', tags=tags)
