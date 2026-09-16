"""Tags blueprint for the web UI."""

from flask import Blueprint, render_template, current_app, flash
from zotero_client.web import get_client

tags_bp = Blueprint('tags', __name__)


@tags_bp.route('/tags')
def list_tags():
    client = get_client(current_app)
    try:
        tags = client.get_tags()
    except Exception as e:
        flash(f'Error fetching tags: {e}', 'danger')
        tags = []
    return render_template('tags/list.html', tags=tags)
