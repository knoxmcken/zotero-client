import pytest
from unittest.mock import Mock, patch
from zotero_client.models.tag import Tag

@patch('requests.get')
def test_get_tags_all(mock_get, mock_client):
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = [
        {"tag": "tag1", "type": 1},
        {"tag": "tag2", "type": 0}
    ]
    mock_get.return_value = mock_response

    tags = mock_client.get_tags()

    mock_get.assert_called_once_with(
        f'{mock_client.BASE_URL}/{mock_client.library_type}/{mock_client.user_id}/tags',
        headers=mock_client.headers,
        params={'limit': 100, 'start': 0},
        timeout=mock_client.TIMEOUT,
    )
    assert len(tags) == 2
    assert isinstance(tags[0], Tag)
    assert tags[0].tag == "tag1"
    assert tags[1].type == 0

@patch('requests.get')
def test_get_tags_for_item(mock_get, mock_client):
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = [
        {"tag": "item-tag", "type": 1}
    ]
    mock_get.return_value = mock_response

    item_id = "ITEM123"
    tags = mock_client.get_tags(item_id=item_id)

    mock_get.assert_called_once_with(
        f'{mock_client.BASE_URL}/{mock_client.library_type}/{mock_client.user_id}/items/{item_id}/tags',
        headers=mock_client.headers,
        params={'limit': 100, 'start': 0},
        timeout=mock_client.TIMEOUT,
    )
    assert len(tags) == 1
    assert tags[0].tag == "item-tag"

@patch('requests.patch')
@patch('requests.get')
def test_add_tags_to_item_merges_existing_tags(mock_get, mock_patch, mock_client):
    """Tags are an item field: the API answers 405 to POST and PUT on /items/<k>/tags.

    So the client reads the item, merges, and PATCHes the whole list. Array
    properties are complete lists, so sending only the new tags would silently
    drop every existing one -- which is what this asserts against.
    """
    item_url = f'{mock_client.BASE_URL}/{mock_client.library_type}/{mock_client.user_id}/items/ITEM123'

    get_response = Mock()
    get_response.status_code = 200
    get_response.json.return_value = {
        "key": "ITEM123",
        "version": 7,
        "data": {"key": "ITEM123", "tags": [{"tag": "existing", "type": 1}]},
    }
    get_response.raise_for_status.return_value = None
    mock_get.return_value = get_response

    patch_response = Mock()
    patch_response.status_code = 204
    patch_response.raise_for_status.return_value = None
    mock_patch.return_value = patch_response

    # 'existing' is repeated deliberately: it must not be added twice.
    mock_client.add_tags_to_item("ITEM123", ["existing", "new-tag"])

    mock_get.assert_called_once_with(
        item_url,
        headers=mock_client.headers,
        timeout=mock_client.TIMEOUT,
    )
    mock_patch.assert_called_once_with(
        item_url,
        headers={
            **mock_client.headers,
            'Content-Type': 'application/json',
            'If-Unmodified-Since-Version': '7',
        },
        json={'tags': [{'tag': 'existing', 'type': 1}, {'tag': 'new-tag'}]},
        timeout=mock_client.TIMEOUT,
    )


@patch('requests.patch')
@patch('requests.get')
def test_add_tags_honours_a_supplied_version(mock_get, mock_patch, mock_client):
    """A caller-supplied version is used as the precondition instead of the read one."""
    get_response = Mock()
    get_response.json.return_value = {
        "key": "ITEM123", "version": 7, "data": {"key": "ITEM123", "tags": []},
    }
    get_response.raise_for_status.return_value = None
    mock_get.return_value = get_response

    patch_response = Mock()
    patch_response.status_code = 204
    patch_response.raise_for_status.return_value = None
    mock_patch.return_value = patch_response

    mock_client.add_tags_to_item("ITEM123", ["new-tag"], 3)

    assert mock_patch.call_args.kwargs['headers']['If-Unmodified-Since-Version'] == '3'
    assert mock_patch.call_args.kwargs['json'] == {'tags': [{'tag': 'new-tag'}]}


@patch('requests.patch')
@patch('requests.get')
def test_remove_tags_from_item(mock_get, mock_patch, mock_client):
    """Removal re-sends the item's remaining tags, in a single write."""
    item_url = f'{mock_client.BASE_URL}/{mock_client.library_type}/{mock_client.user_id}/items/ITEM123'

    get_response = Mock()
    get_response.json.return_value = {
        "key": "ITEM123",
        "version": 5,
        "data": {
            "key": "ITEM123",
            "tags": [
                {"tag": "keep", "type": 1},
                {"tag": "old-tag1"},
                {"tag": "old-tag2"},
            ],
        },
    }
    get_response.raise_for_status.return_value = None
    mock_get.return_value = get_response

    patch_response = Mock()
    patch_response.status_code = 204
    patch_response.raise_for_status.return_value = None
    mock_patch.return_value = patch_response

    mock_client.remove_tags_from_item("ITEM123", ["old-tag1", "old-tag2"])

    mock_patch.assert_called_once_with(
        item_url,
        headers={
            **mock_client.headers,
            'Content-Type': 'application/json',
            'If-Unmodified-Since-Version': '5',
        },
        json={'tags': [{'tag': 'keep', 'type': 1}]},
        timeout=mock_client.TIMEOUT,
    )


@patch('requests.patch')
@patch('requests.get')
def test_tag_names_with_special_characters_survive(mock_get, mock_patch, mock_client):
    """Tag names travel as JSON values now, so no URL escaping is involved."""
    get_response = Mock()
    get_response.json.return_value = {
        "key": "ITEM123", "version": 1, "data": {"key": "ITEM123", "tags": []},
    }
    get_response.raise_for_status.return_value = None
    mock_get.return_value = get_response

    patch_response = Mock()
    patch_response.status_code = 204
    patch_response.raise_for_status.return_value = None
    mock_patch.return_value = patch_response

    mock_client.add_tags_to_item("ITEM123", ["with space", "a/b", "c#d", "100%"])

    assert mock_patch.call_args.kwargs['json'] == {
        'tags': [
            {'tag': 'with space'},
            {'tag': 'a/b'},
            {'tag': 'c#d'},
            {'tag': '100%'},
        ]
    }
