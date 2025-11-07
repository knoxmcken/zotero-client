import pytest
from unittest.mock import Mock, patch
from zotero_client.api.client import ZoteroClient
from zotero_client.models.tag import Tag

@pytest.fixture
def mock_client():
    return ZoteroClient(api_key="test_key", user_id="test_user")

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
        headers=mock_client.headers
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
        headers=mock_client.headers
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
        json=expected_json
    )

@patch('requests.delete')
def test_remove_tags_from_item(mock_delete, mock_client):
    mock_response = Mock()
    mock_response.status_code = 204 # No Content for successful delete
    mock_delete.return_value = mock_response

    item_id = "ITEM123"
    tags_to_remove = ["old-tag1", "old-tag2"]
    version = 1
    mock_client.remove_tags_from_item(item_id, tags_to_remove, version)

    expected_headers = mock_client.headers.copy()
    expected_headers['If-Unmodified-Since-Version'] = str(version)

    # Assert that delete was called for each tag
    mock_delete.assert_any_call(
        f'{mock_client.BASE_URL}/{mock_client.library_type}/{mock_client.user_id}/items/{item_id}/tags/old-tag1',
        headers=expected_headers
    )
    mock_delete.assert_any_call(
        f'{mock_client.BASE_URL}/{mock_client.library_type}/{mock_client.user_id}/items/{item_id}/tags/old-tag2',
        headers=expected_headers
    )
    assert mock_delete.call_count == len(tags_to_remove)
