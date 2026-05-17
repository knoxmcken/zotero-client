"""Collections Blueprint."""

import requests as http_requests
from flask import (
    Blueprint, current_app, flash, render_template,
)
from zotero_client.web import get_client

collections_bp = Blueprint('collections', __name__)


@collections_bp.before_request
def require_credentials():
    if current_app.config.get('CREDENTIALS_MISSING'):
        return render_template(
            'error.html',
            message='Zotero credentials are not configured. '
                    'Set ZOTERO_API_KEY and ZOTERO_USER_ID in your .env file.',
        ), 503


@collections_bp.route('/collections')
def list_collections():
    client = get_client(current_app)
    try:
        collections = client.get_collections()
    except http_requests.HTTPError as e:
        status = e.response.status_code if e.response is not None else 0
        if status in (401, 403):
            flash('Invalid API key or insufficient permissions.', 'danger')
        else:
            flash(f'Zotero API error: {e}', 'danger')
        collections = []
    except Exception as e:
        flash(f'Error fetching collections: {e}', 'danger')
        collections = []

    return render_template('collections/list.html', collections=collections)
