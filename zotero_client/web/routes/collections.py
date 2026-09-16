"""Collections blueprint for the web UI."""

from flask import Blueprint, render_template, current_app, flash
from zotero_client.web import get_client

collections_bp = Blueprint('collections', __name__)


@collections_bp.route('/collections')
def list_collections():
    client = get_client(current_app)
    try:
        collections = client.get_collections()
    except Exception as e:
        flash(f'Error fetching collections: {e}', 'danger')
        collections = []
    return render_template('collections/list.html', collections=collections)
