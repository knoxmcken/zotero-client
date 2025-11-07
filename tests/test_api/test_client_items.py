import pytest
from unittest.mock import Mock, patch
from zotero_client.api.client import ZoteroClient
from zotero_client.models.item import Item

@pytest.fixture
def mock_client():
    return ZoteroClient(api_key="test_key", user_id="test_user")

@patch('requests.post')
def test_create_item(mock_post, mock_client):
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = [{
        "key": "NEWITEM123",
        "version": 1,
        "data": {
            "key": "NEWITEM123",
            "itemType": "book",
            "title": "New Test Book",
            "creators": [],
            "date": "2024",
            "url": ""
        }
    }]
    mock_post.return_value = mock_response

    item_data = {"itemType": "book", "title": "New Test Book"}
    created_item = mock_client.create_item(item_data)

    mock_post.assert_called_once_with(
        f'{mock_client.BASE_URL}/{mock_client.library_type}/{mock_client.user_id}/items',
        headers=mock_client.headers,
        json=[item_data]
    )
    assert isinstance(created_item, Item)
    assert created_item.key == "NEWITEM123"
    assert created_item.title == "New Test Book"

@patch('requests.put')
def test_update_item(mock_put, mock_client):
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = [{
        "key": "UPDATEITEM456",
        "version": 2,
        "data": {
            "key": "UPDATEITEM456",
            "itemType": "journalArticle",
            "title": "Updated Article Title",
            "creators": [],
            "date": "2023",
            "url": ""
        }
    }]
    mock_put.return_value = mock_response

    item_id = "UPDATEITEM456"
    updated_data = {"title": "Updated Article Title"}
    version = 1
    updated_item = mock_client.update_item(item_id, updated_data, version)

    expected_headers = mock_client.headers.copy()
    expected_headers['If-Unmodified-Since-Version'] = str(version)
    mock_put.assert_called_once_with(
        f'{mock_client.BASE_URL}/{mock_client.library_type}/{mock_client.user_id}/items/{item_id}',
        headers=expected_headers,
        json=updated_data
    )
    assert isinstance(updated_item, Item)
    assert updated_item.title == "Updated Article Title"
    assert updated_item.version == 2

@patch('requests.delete')
def test_delete_item(mock_delete, mock_client):
    mock_response = Mock()
    mock_response.status_code = 204 # No Content for successful delete
    mock_delete.return_value = mock_response

    item_id = "DELETEITEM789"
    version = 1
    mock_client.delete_item(item_id, version)

    expected_headers = mock_client.headers.copy()
    expected_headers['If-Unmodified-Since-Version'] = str(version)
    mock_delete.assert_called_once_with(
        f'{mock_client.BASE_URL}/{mock_client.library_type}/{mock_client.user_id}/items/{item_id}',
        headers=expected_headers
    )

@patch('requests.get')
def test_get_items_advanced_search(mock_get, mock_client):
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = [{
        "key": "SEARCHITEM1",
        "version": 1,
        "data": {
            "key": "SEARCHITEM1",
            "itemType": "journalArticle",
            "title": "Search Result Article",
            "creators": [],
            "date": "2020",
            "url": ""
        }
    }]
    mock_get.return_value = mock_response

    # Test with various search parameters
    items = mock_client.get_items(
        limit=5,
        q="search term",
        qmode="everything",
        item_type="journalArticle",
        tag="biology",
        include_trashed=True
    )

    expected_params = {
        'limit': 5,
        'q': "search term",
        'qmode': "everything",
        'itemType': "journalArticle",
        'tag': "biology",
        'includeTrashed': 1
    }

    mock_get.assert_called_once_with(
        f'{mock_client.BASE_URL}/{mock_client.library_type}/{mock_client.user_id}/items',
        headers=mock_client.headers,
        params=expected_params
    )
    assert len(items) == 1
    assert items[0].title == "Search Result Article"
    assert items[0].item_type == "journalArticle"

@patch('requests.get')
def test_get_attachments(mock_get, mock_client):
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = [{
        "key": "ATTACHMENT1",
        "version": 1,
        "data": {
            "key": "ATTACHMENT1",
            "itemType": "attachment",
            "title": "Test Attachment",
            "parentItem": "PARENTITEM123",
            "creators": [],
            "date": "2024",
            "url": ""
        }
    }]
    mock_get.return_value = mock_response

    # Test getting all attachments
    attachments = mock_client.get_attachments(limit=1)

    expected_params_all = {'itemType': 'attachment', 'limit': 1}
    mock_get.assert_called_with(
        f'{mock_client.BASE_URL}/{mock_client.library_type}/{mock_client.user_id}/items',
        headers=mock_client.headers,
        params=expected_params_all
    )
    assert len(attachments) == 1
    assert attachments[0].title == "Test Attachment"
    assert attachments[0].item_type == "attachment"

    # Test getting attachments for a specific parent item
    mock_get.reset_mock()
    attachments_for_item = mock_client.get_attachments(item_id="PARENTITEM123")

    expected_params_item = {'itemType': 'attachment', 'parentItem': 'PARENTITEM123'}
    mock_get.assert_called_with(
        f'{mock_client.BASE_URL}/{mock_client.library_type}/{mock_client.user_id}/items',
        headers=mock_client.headers,
        params=expected_params_item
    )
    assert len(attachments_for_item) == 1
    assert attachments_for_item[0].parent_item == "PARENTITEM123"
