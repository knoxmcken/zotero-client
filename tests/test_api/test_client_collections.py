import pytest
from unittest.mock import Mock, patch
from zotero_client.api.client import ZoteroClient
from zotero_client.models.collection import Collection

@pytest.fixture
def mock_client():
    return ZoteroClient(api_key="test_key", user_id="test_user")

@patch('requests.get')
def test_get_collections(mock_get, mock_client):
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = [{
        "key": "COLLECTION1",
        "version": 1,
        "data": {
            "key": "COLLECTION1",
            "name": "Collection One",
            "parentCollection": False
        }
    }]
    mock_get.return_value = mock_response

    collections = mock_client.get_collections()

    mock_get.assert_called_once_with(
        f'{mock_client.BASE_URL}/{mock_client.library_type}/{mock_client.user_id}/collections',
        headers=mock_client.headers
    )
    assert len(collections) == 1
    assert isinstance(collections[0], Collection)
    assert collections[0].name == "Collection One"

@patch('requests.post')
def test_create_collection(mock_post, mock_client):
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = [{
        "key": "NEWCOLLECTION123",
        "version": 1,
        "data": {
            "key": "NEWCOLLECTION123",
            "name": "New Test Collection",
            "parentCollection": False
        }
    }]
    mock_post.return_value = mock_response

    collection_data = {"name": "New Test Collection"}
    created_collection = mock_client.create_collection(collection_data)

    mock_post.assert_called_once_with(
        f'{mock_client.BASE_URL}/{mock_client.library_type}/{mock_client.user_id}/collections',
        headers=mock_client.headers,
        json=[collection_data]
    )
    assert isinstance(created_collection, Collection)
    assert created_collection.key == "NEWCOLLECTION123"
    assert created_collection.name == "New Test Collection"

@patch('requests.put')
def test_update_collection(mock_put, mock_client):
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = [{
        "key": "UPDATECOLLECTION456",
        "version": 2,
        "data": {
            "key": "UPDATECOLLECTION456",
            "name": "Updated Collection Name",
            "parentCollection": False
        }
    }]
    mock_put.return_value = mock_response

    collection_id = "UPDATECOLLECTION456"
    updated_data = {"name": "Updated Collection Name"}
    version = 1
    updated_collection = mock_client.update_collection(collection_id, updated_data, version)

    expected_headers = mock_client.headers.copy()
    expected_headers['If-Unmodified-Since-Version'] = str(version)
    mock_put.assert_called_once_with(
        f'{mock_client.BASE_URL}/{mock_client.library_type}/{mock_client.user_id}/collections/{collection_id}',
        headers=expected_headers,
        json=updated_data
    )
    assert isinstance(updated_collection, Collection)
    assert updated_collection.name == "Updated Collection Name"
    assert updated_collection.version == 2

@patch('requests.delete')
def test_delete_collection(mock_delete, mock_client):
    mock_response = Mock()
    mock_response.status_code = 204 # No Content for successful delete
    mock_delete.return_value = mock_response

    collection_id = "DELETECOLLECTION789"
    version = 1
    mock_client.delete_collection(collection_id, version)

    expected_headers = mock_client.headers.copy()
    expected_headers['If-Unmodified-Since-Version'] = str(version)
    mock_delete.assert_called_once_with(
        f'{mock_client.BASE_URL}/{mock_client.library_type}/{mock_client.user_id}/collections/{collection_id}',
        headers=expected_headers
    )
