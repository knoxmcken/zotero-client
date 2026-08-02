"""Items blueprint for the web UI."""

from flask import Blueprint, render_template, request, redirect, url_for, flash, abort, current_app
from zotero_client.web import get_client

items_bp = Blueprint('items', __name__)


@items_bp.before_request
def check_credentials():
    if current_app.config.get('CREDENTIALS_MISSING'):
        return render_template(
            'error.html',
            code=503,
            message='Zotero credentials are not configured. Set ZOTERO_API_KEY and ZOTERO_USER_ID in your .env file.',
        ), 503


@items_bp.route('/')
def index():
    return redirect(url_for('items.list_items'))


@items_bp.route('/items')
def list_items():
    q = request.args.get('q', '').strip() or None
    item_type = request.args.get('type', '').strip() or None
    tag = request.args.get('tag', '').strip() or None
    limit = request.args.get('limit', type=int) or None

    client = get_client(current_app)
    try:
        items = client.get_items(q=q, item_type=item_type, tag=tag, limit=limit)
    except Exception as e:
        flash(f'Error fetching items: {e}', 'danger')
        items = []

    return render_template('items/list.html', items=items, q=q or '', item_type=item_type or '', tag=tag or '', limit=limit or '')


@items_bp.route('/items/<item_id>')
def item_detail(item_id):
    client = get_client(current_app)
    try:
        item = client.get_item(item_id)
    except Exception as e:
        abort(404)

    try:
        tags = client.get_tags(item_id=item_id)
    except Exception:
        tags = []

    try:
        attachments = client.get_attachments(item_id=item_id)
    except Exception:
        attachments = []

    return render_template('items/detail.html', item=item, tags=tags, attachments=attachments)


@items_bp.route('/items/<item_id>/delete', methods=['POST'])
def delete_item(item_id):
    client = get_client(current_app)
    try:
        client.delete_item(item_id)
        flash(f'Item {item_id} deleted.', 'success')
    except Exception as e:
        flash(f'Error deleting item: {e}', 'danger')
    return redirect(url_for('items.list_items'))
