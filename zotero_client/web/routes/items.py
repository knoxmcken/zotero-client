"""Items Blueprint — list, detail, delete."""

import requests as http_requests
from flask import (
    Blueprint, abort, current_app, flash,
    redirect, render_template, request, url_for,
)
from zotero_client.web import get_client

items_bp = Blueprint('items', __name__)


@items_bp.before_request
def require_credentials():
    if current_app.config.get('CREDENTIALS_MISSING'):
        return render_template(
            'error.html',
            message='Zotero credentials are not configured. '
                    'Set ZOTERO_API_KEY and ZOTERO_USER_ID in your .env file.',
        ), 503


@items_bp.route('/')
def index():
    return redirect(url_for('items.list_items'))


@items_bp.route('/items')
def list_items():
    q = request.args.get('q') or None
    item_type = request.args.get('type') or None
    tag = request.args.get('tag') or None
    limit = request.args.get('limit', type=int) or None

    client = get_client(current_app)
    try:
        items = client.get_items(limit=limit, q=q, item_type=item_type, tag=tag)
    except http_requests.HTTPError as e:
        status = e.response.status_code if e.response is not None else 0
        if status in (401, 403):
            flash('Invalid API key or insufficient permissions.', 'danger')
        else:
            flash(f'Zotero API error: {e}', 'danger')
        items = []
    except Exception as e:
        flash(f'Error fetching items: {e}', 'danger')
        items = []

    return render_template(
        'items/list.html',
        items=items,
        q=q or '',
        item_type=item_type or '',
        tag=tag or '',
        limit=limit or '',
    )


@items_bp.route('/items/<item_id>')
def item_detail(item_id):
    client = get_client(current_app)
    try:
        item = client.get_item(item_id)
    except http_requests.HTTPError as e:
        status = e.response.status_code if e.response is not None else 0
        if status == 404:
            abort(404)
        flash(f'Error fetching item: {e}', 'danger')
        return redirect(url_for('items.list_items'))
    except Exception as e:
        flash(f'Error fetching item: {e}', 'danger')
        return redirect(url_for('items.list_items'))

    try:
        tags = client.get_tags(item_id=item_id)
    except Exception:
        tags = []

    try:
        attachments = client.get_attachments(item_id=item_id)
    except Exception:
        attachments = []

    return render_template(
        'items/detail.html',
        item=item,
        tags=tags,
        attachments=attachments,
    )


@items_bp.route('/items/<item_id>/delete', methods=['POST'])
def delete_item(item_id):
    client = get_client(current_app)
    try:
        item = client.get_item(item_id)
        client.delete_item(item_id, item.version)
        flash(f'Item "{item.title}" deleted successfully.', 'success')
    except Exception as e:
        flash(f'Error deleting item: {e}', 'danger')
    return redirect(url_for('items.list_items'))
