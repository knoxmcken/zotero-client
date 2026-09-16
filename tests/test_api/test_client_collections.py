import pytest
from unittest.mock import Mock, patch
from zotero_client.models.collection import Collection

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
        headers=mock_client.headers,
        params={'limit': 100, 'start': 0},
        timeout=mock_client.TIMEOUT,
    )
    assert len(collections) == 1
    assert isinstance(collections[0], Collection)
    assert collections[0].name == "Collection One"

@patch('requests.post')
def test_create_collection(mock_post, mock_client):
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "successful": {
            "0": {
                "key": "NEWCOLLECTION123",
                "version": 1,
                "data": {
                    "key": "NEWCOLLECTION123",
                    "name": "New Test Collection",
                    "parentCollection": False
                }
            }
        },
        "failed": {}
    }
    mock_post.return_value = mock_response

    collection_data = {"name": "New Test Collection"}
    created_collection = mock_client.create_collection(collection_data)

    mock_post.assert_called_once_with(
        f'{mock_client.BASE_URL}/{mock_client.library_type}/{mock_client.user_id}/collections',
        headers=mock_client.headers,
        json=[collection_data],
        timeout=mock_client.TIMEOUT,
    )
    assert isinstance(created_collection, Collection)
    assert created_collection.key == "NEWCOLLECTION123"
    assert created_collection.name == "New Test Collection"

@patch('requests.get')
@patch('requests.put')
def test_update_collection(mock_put, mock_get, mock_client):
    """A successful PUT answers 204 No Content, so the collection is re-read."""
    put_response = Mock()
    put_response.status_code = 204
    put_response.content = b''  # no body on success
    put_response.raise_for_status.return_value = None
    mock_put.return_value = put_response

    get_response = Mock()
    get_response.json.return_value = {
        "key": "UPDATECOLLECTION456",
        "version": 2,
        "data": {
            "key": "UPDATECOLLECTION456",
            "name": "Updated Collection Name",
            "parentCollection": False
        }
    }
    get_response.raise_for_status.return_value = None
    mock_get.return_value = get_response

    collection_id = "UPDATECOLLECTION456"
    updated_data = {"name": "Updated Collection Name"}
    version = 1
    updated_collection = mock_client.update_collection(collection_id, updated_data, version)

    expected_headers = mock_client.headers.copy()
    expected_headers['If-Unmodified-Since-Version'] = str(version)
    mock_put.assert_called_once_with(
        f'{mock_client.BASE_URL}/{mock_client.library_type}/{mock_client.user_id}/collections/{collection_id}',
        headers=expected_headers,
        json=updated_data,
        timeout=mock_client.TIMEOUT,
    )
    mock_get.assert_called_once_with(
        f'{mock_client.BASE_URL}/{mock_client.library_type}/{mock_client.user_id}/collections/{collection_id}',
        headers=mock_client.headers,
        timeout=mock_client.TIMEOUT,
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
        headers=expected_headers,
        timeout=mock_client.TIMEOUT,
    )

@patch('requests.delete')
@patch('requests.get')
def test_delete_collection_without_a_version_reads_the_precondition(mock_get, mock_delete, mock_client):
    """Omitting the version must still work: the API requires a precondition."""
    collection_id = "DELETECOLLECTION789"

    get_response = Mock()
    get_response.json.return_value = {
        "key": collection_id,
        "version": 4,
        "data": {"key": collection_id, "name": "x", "parentCollection": False},
    }
    get_response.raise_for_status.return_value = None
    mock_get.return_value = get_response

    delete_response = Mock()
    delete_response.status_code = 204
    delete_response.raise_for_status.return_value = None
    mock_delete.return_value = delete_response

    mock_client.delete_collection(collection_id)

    mock_get.assert_called_once_with(
        f'{mock_client.BASE_URL}/{mock_client.library_type}/{mock_client.user_id}/collections/{collection_id}',
        headers=mock_client.headers,
        timeout=mock_client.TIMEOUT,
    )
    mock_delete.assert_called_once_with(
        f'{mock_client.BASE_URL}/{mock_client.library_type}/{mock_client.user_id}/collections/{collection_id}',
        headers={**mock_client.headers, 'If-Unmodified-Since-Version': '4'},
        timeout=mock_client.TIMEOUT,
    )
