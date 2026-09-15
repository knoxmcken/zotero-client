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

@patch('requests.post')
def test_add_tags_to_item(mock_post, mock_client):
    mock_response = Mock()
    mock_response.status_code = 200 # Zotero API returns 200 on success for adding tags
    mock_post.return_value = mock_response

    item_id = "ITEM123"
    tags_to_add = ["new-tag", "another-tag"]
    version = 1
    mock_client.add_tags_to_item(item_id, tags_to_add, version)

    expected_headers = mock_client.headers.copy()
    expected_headers['If-Unmodified-Since-Version'] = str(version)
    expected_json = [{'tag': 'new-tag'}, {'tag': 'another-tag'}]
    mock_post.assert_called_once_with(
        f'{mock_client.BASE_URL}/{mock_client.library_type}/{mock_client.user_id}/items/{item_id}/tags',
        headers=expected_headers,
        json=expected_json,
        timeout=mock_client.TIMEOUT,
    )

@patch('requests.delete')
def test_remove_tags_from_item(mock_delete, mock_client):
    """Each removal advances the item version, so the precondition is refreshed."""
    first_response = Mock()
    first_response.status_code = 204
    first_response.headers = {'Last-Modified-Version': '2'}
    second_response = Mock()
    second_response.status_code = 204
    second_response.headers = {'Last-Modified-Version': '3'}
    mock_delete.side_effect = [first_response, second_response]

    item_id = "ITEM123"
    tags_to_remove = ["old-tag1", "old-tag2"]
    version = 1
    mock_client.remove_tags_from_item(item_id, tags_to_remove, version)

    first_headers = mock_client.headers.copy()
    first_headers['If-Unmodified-Since-Version'] = '1'
    second_headers = mock_client.headers.copy()
    second_headers['If-Unmodified-Since-Version'] = '2'

    mock_delete.assert_any_call(
        f'{mock_client.BASE_URL}/{mock_client.library_type}/{mock_client.user_id}/items/{item_id}/tags/old-tag1',
        headers=first_headers,
        timeout=mock_client.TIMEOUT,
    )
    mock_delete.assert_any_call(
        f'{mock_client.BASE_URL}/{mock_client.library_type}/{mock_client.user_id}/items/{item_id}/tags/old-tag2',
        headers=second_headers,
        timeout=mock_client.TIMEOUT,
    )
    assert mock_delete.call_count == len(tags_to_remove)


@patch('requests.delete')
def test_remove_tags_encodes_tag_names(mock_delete, mock_client):
    """Tag names go into the URL path, so they must be percent-encoded."""
    response = Mock()
    response.status_code = 204
    response.headers = {}
    mock_delete.return_value = response

    item_id = "ITEM123"
    mock_client.remove_tags_from_item(item_id, ["with space", "a/b", "c#d"], None)

    base = f'{mock_client.BASE_URL}/{mock_client.library_type}/{mock_client.user_id}/items/{item_id}/tags'
    assert [call.args[0] for call in mock_delete.call_args_list] == [
        f'{base}/with%20space',
        f'{base}/a%2Fb',
        f'{base}/c%23d',
    ]
