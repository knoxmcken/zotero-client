import hashlib
import os

import pytest
from unittest.mock import Mock, patch, MagicMock
import builtins
from zotero_client.models.item import Item

@patch('requests.post')
def test_create_item(mock_post, mock_client):
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "successful": {
            "0": {
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
            }
        },
        "failed": {}
    }
    mock_post.return_value = mock_response

    item_data = {"itemType": "book", "title": "New Test Book"}
    created_item = mock_client.create_item(item_data)

    mock_post.assert_called_once_with(
        f'{mock_client.BASE_URL}/{mock_client.library_type}/{mock_client.user_id}/items',
        headers=mock_client.headers,
        json=[item_data],
        timeout=mock_client.TIMEOUT,
    )
    assert isinstance(created_item, Item)
    assert created_item.key == "NEWITEM123"
    assert created_item.title == "New Test Book"

@patch('requests.get')
@patch('requests.put')
def test_update_item(mock_put, mock_get, mock_client):
    """A successful PUT answers 204 No Content, so the item is re-read."""
    put_response = Mock()
    put_response.status_code = 204
    put_response.content = b''  # no body on success
    put_response.raise_for_status.return_value = None
    mock_put.return_value = put_response

    get_response = Mock()
    get_response.json.return_value = {
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
    }
    get_response.raise_for_status.return_value = None
    mock_get.return_value = get_response

    item_id = "UPDATEITEM456"
    updated_data = {"title": "Updated Article Title"}
    version = 1
    updated_item = mock_client.update_item(item_id, updated_data, version)

    expected_headers = mock_client.headers.copy()
    expected_headers['If-Unmodified-Since-Version'] = str(version)
    mock_put.assert_called_once_with(
        f'{mock_client.BASE_URL}/{mock_client.library_type}/{mock_client.user_id}/items/{item_id}',
        headers=expected_headers,
        json=updated_data,
        timeout=mock_client.TIMEOUT,
    )
    mock_get.assert_called_once_with(
        f'{mock_client.BASE_URL}/{mock_client.library_type}/{mock_client.user_id}/items/{item_id}',
        headers=mock_client.headers,
        timeout=mock_client.TIMEOUT,
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
        headers=expected_headers,
        timeout=mock_client.TIMEOUT,
    )

@patch('requests.delete')
@patch('requests.get')
def test_delete_item_without_a_version_reads_the_precondition(mock_get, mock_delete, mock_client):
    """Omitting the version must still work: the API requires a precondition.

    A write with no `If-Unmodified-Since-Version` is rejected with 428
    Precondition Required, and this is exactly the call the web delete route
    makes -- `delete_item(item_id)` with no version -- which is why that button
    could never work.
    """
    item_id = "DELETEITEM789"

    get_response = Mock()
    get_response.json.return_value = {
        "key": item_id,
        "version": 9,
        "data": {
            "key": item_id, "itemType": "book", "title": "x",
            "creators": [], "date": "", "url": "",
        },
    }
    get_response.raise_for_status.return_value = None
    mock_get.return_value = get_response

    delete_response = Mock()
    delete_response.status_code = 204
    delete_response.raise_for_status.return_value = None
    mock_delete.return_value = delete_response

    mock_client.delete_item(item_id)

    mock_get.assert_called_once_with(
        f'{mock_client.BASE_URL}/{mock_client.library_type}/{mock_client.user_id}/items/{item_id}',
        headers=mock_client.headers,
        timeout=mock_client.TIMEOUT,
    )
    mock_delete.assert_called_once_with(
        f'{mock_client.BASE_URL}/{mock_client.library_type}/{mock_client.user_id}/items/{item_id}',
        headers={**mock_client.headers, 'If-Unmodified-Since-Version': '9'},
        timeout=mock_client.TIMEOUT,
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
        'q': "search term",
        'qmode': "everything",
        'itemType': "journalArticle",
        'tag': "biology",
        'includeTrashed': 1,
        'limit': 5,
        'start': 0
    }

    mock_get.assert_called_once_with(
        f'{mock_client.BASE_URL}/{mock_client.library_type}/{mock_client.user_id}/items',
        headers=mock_client.headers,
        params=expected_params,
        timeout=mock_client.TIMEOUT,
    )
    assert len(items) == 1
    assert items[0].title == "Search Result Article"
    assert items[0].item_type == "journalArticle"

@patch('requests.get')
def test_get_collection_items(mock_get, mock_client):
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = [{
        "key": "COLLECTIONITEM1",
        "version": 1,
        "data": {
            "key": "COLLECTIONITEM1",
            "itemType": "journalArticle",
            "title": "Collection Article",
            "creators": [],
            "date": "2021",
            "url": ""
        }
    }]
    mock_get.return_value = mock_response

    items = mock_client.get_collection_items("COLLECTION1")

    mock_get.assert_called_once_with(
        f'{mock_client.BASE_URL}/{mock_client.library_type}/{mock_client.user_id}/collections/COLLECTION1/items',
        headers=mock_client.headers,
        params={'limit': 100, 'start': 0},
        timeout=mock_client.TIMEOUT,
    )
    assert len(items) == 1
    assert items[0].title == "Collection Article"

@patch('requests.get')
def test_get_collection_items_with_filters(mock_get, mock_client):
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = [{
        "key": "COLLECTIONITEM2",
        "version": 1,
        "data": {
            "key": "COLLECTIONITEM2",
            "itemType": "book",
            "title": "Filtered Collection Book",
            "creators": [],
            "date": "2022",
            "url": ""
        }
    }]
    mock_get.return_value = mock_response

    items = mock_client.get_collection_items(
        "COLLECTION1",
        limit=5,
        q="search term",
        qmode="everything",
        item_type="book",
        tag="biology",
        include_trashed=True
    )

    expected_params = {
        'q': "search term",
        'qmode': "everything",
        'itemType': "book",
        'tag': "biology",
        'includeTrashed': 1,
        'limit': 5,
        'start': 0
    }

    mock_get.assert_called_once_with(
        f'{mock_client.BASE_URL}/{mock_client.library_type}/{mock_client.user_id}/collections/COLLECTION1/items',
        headers=mock_client.headers,
        params=expected_params,
        timeout=mock_client.TIMEOUT,
    )
    assert len(items) == 1
    assert items[0].title == "Filtered Collection Book"

@patch('requests.get')
def test_get_attachments_for_item_reads_children(mock_get, mock_client):
    """An item's attachments come from its children.

    `/items?parentItem=` is silently ignored by the API -- it returns
    attachments from the whole library, not the named parent -- so the child
    endpoint is the only correct route. This asserts the resulting items, not
    merely the outgoing request, because a request-shape assertion is what let
    the ignored filter pass for so long.
    """
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = [{
        "key": "CHILDATTACH1",
        "version": 1,
        "data": {
            "key": "CHILDATTACH1",
            "itemType": "attachment",
            "title": "Child Attachment",
            "parentItem": "PARENTITEM123",
            "creators": [],
            "date": "2024",
            "url": ""
        }
    }]
    mock_response.raise_for_status.return_value = None
    mock_get.return_value = mock_response

    attachments = mock_client.get_attachments(item_id="PARENTITEM123")

    mock_get.assert_called_once_with(
        f'{mock_client.BASE_URL}/{mock_client.library_type}/{mock_client.user_id}/items/PARENTITEM123/children',
        headers=mock_client.headers,
        params={'itemType': 'attachment', 'limit': 100, 'start': 0},
        timeout=mock_client.TIMEOUT,
    )
    assert [a.key for a in attachments] == ["CHILDATTACH1"]
    assert attachments[0].parent_item == "PARENTITEM123"


@patch('requests.get')
def test_get_attachments_library_wide(mock_get, mock_client):
    """Without an item_id, attachments come from the library as a whole."""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = [{
        "key": "LIBATTACH1",
        "version": 1,
        "data": {
            "key": "LIBATTACH1",
            "itemType": "attachment",
            "title": "Library Attachment",
            "creators": [],
            "date": "2024",
            "url": ""
        }
    }]
    mock_response.raise_for_status.return_value = None
    mock_get.return_value = mock_response

    attachments = mock_client.get_attachments(limit=1)

    mock_get.assert_called_once_with(
        f'{mock_client.BASE_URL}/{mock_client.library_type}/{mock_client.user_id}/items',
        headers=mock_client.headers,
        params={'itemType': 'attachment', 'limit': 1, 'start': 0},
        timeout=mock_client.TIMEOUT,
    )
    assert [a.key for a in attachments] == ["LIBATTACH1"]
    assert attachments[0].item_type == "attachment"

@patch('requests.post')
@patch('requests.get')
def test_upload_attachment_follows_documented_flow(mock_get, mock_post, mock_client, tmp_path):
    """Upload is create -> authorize -> POST to storage -> register."""
    parent_item_id = "PARENTITEM123"
    file_path = tmp_path / "paper.pdf"
    file_bytes = b"file content"
    file_path.write_bytes(file_bytes)
    md5 = hashlib.md5(file_bytes).hexdigest()
    title = "My Custom Attachment Title"

    items_url = f'{mock_client.BASE_URL}/{mock_client.library_type}/{mock_client.user_id}/items'

    # GET 1: attachment template
    template_response = Mock()
    template_response.json.return_value = {
        "itemType": "attachment",
        "linkMode": "imported_file",
        "title": "",
        "filename": "",
        "contentType": "",
        "md5": None,
        "mtime": None,
    }
    template_response.raise_for_status.return_value = None

    # GET 2: the attachment item, read back after the upload
    attachment_response = Mock()
    attachment_response.json.return_value = {
        "key": "UPLOADATTACHMENT1",
        "version": 2,
        "data": {
            "key": "UPLOADATTACHMENT1",
            "itemType": "attachment",
            "title": title,
            "parentItem": parent_item_id,
            "creators": [],
            "date": "",
            "url": "",
        },
    }
    attachment_response.raise_for_status.return_value = None
    mock_get.side_effect = [template_response, attachment_response]

    # POST 1: create the attachment item
    create_response = Mock()
    create_response.json.return_value = {
        "successful": {"0": {"key": "UPLOADATTACHMENT1", "version": 1, "data": {}}},
        "failed": {},
    }
    create_response.raise_for_status.return_value = None

    # POST 2: authorization for the upload
    auth_response = Mock()
    auth_response.json.return_value = {
        "url": "https://storage.example.com/upload",
        "contentType": "multipart/form-data; boundary=xyz",
        "prefix": "--xyz\r\n",
        "suffix": "\r\n--xyz--",
        "uploadKey": "UPLOADKEY123",
    }
    auth_response.raise_for_status.return_value = None

    # POST 3: the file itself, POST 4: registration
    storage_response = Mock()
    storage_response.raise_for_status.return_value = None
    register_response = Mock()
    register_response.raise_for_status.return_value = None
    mock_post.side_effect = [create_response, auth_response, storage_response, register_response]

    uploaded = mock_client.upload_attachment(parent_item_id, str(file_path), title)

    mock_get.assert_any_call(
        f'{mock_client.BASE_URL}/items/new',
        headers=mock_client.headers,
        params={'itemType': 'attachment', 'linkMode': 'imported_file'},
        timeout=mock_client.TIMEOUT,
    )

    create_call = mock_post.call_args_list[0]
    assert create_call.args[0] == items_url
    assert create_call.kwargs['json'] == [{
        "itemType": "attachment",
        "linkMode": "imported_file",
        "title": title,
        "filename": "paper.pdf",
        "contentType": "application/pdf",
        "parentItem": parent_item_id,
        "md5": None,
        "mtime": None,
    }]

    auth_call = mock_post.call_args_list[1]
    assert auth_call.args[0] == f'{items_url}/UPLOADATTACHMENT1/file'
    assert auth_call.kwargs['data'] == {
        'md5': md5,
        'filename': 'paper.pdf',
        'filesize': len(file_bytes),
        'mtime': str(int(os.path.getmtime(file_path) * 1000)),
    }
    assert auth_call.kwargs['headers']['If-None-Match'] == '*'

    storage_call = mock_post.call_args_list[2]
    assert storage_call.args[0] == 'https://storage.example.com/upload'
    assert storage_call.kwargs['data'] == b'--xyz\r\n' + file_bytes + b'\r\n--xyz--'
    assert storage_call.kwargs['headers'] == {'Content-Type': 'multipart/form-data; boundary=xyz'}

    register_call = mock_post.call_args_list[3]
    assert register_call.args[0] == f'{items_url}/UPLOADATTACHMENT1/file'
    assert register_call.kwargs['data'] == {'upload': 'UPLOADKEY123'}

    assert isinstance(uploaded, Item)
    assert uploaded.key == "UPLOADATTACHMENT1"
    assert uploaded.title == title
    assert uploaded.parent_item == parent_item_id


@patch('requests.post')
@patch('requests.get')
def test_upload_attachment_skips_storage_when_file_exists(mock_get, mock_post, mock_client, tmp_path):
    """An `exists` authorization means the file is already stored."""
    file_path = tmp_path / "paper.pdf"
    file_path.write_bytes(b"file content")
    items_url = f'{mock_client.BASE_URL}/{mock_client.library_type}/{mock_client.user_id}/items'

    template_response = Mock()
    template_response.json.return_value = {
        "itemType": "attachment", "linkMode": "imported_file", "title": "",
        "filename": "", "contentType": "", "md5": None, "mtime": None,
    }
    template_response.raise_for_status.return_value = None
    attachment_response = Mock()
    attachment_response.json.return_value = {
        "key": "ATT1", "version": 2,
        "data": {"key": "ATT1", "itemType": "attachment", "title": "paper.pdf",
                 "creators": [], "date": "", "url": ""},
    }
    attachment_response.raise_for_status.return_value = None
    mock_get.side_effect = [template_response, attachment_response]

    create_response = Mock()
    create_response.json.return_value = {
        "successful": {"0": {"key": "ATT1", "version": 1, "data": {}}}, "failed": {},
    }
    create_response.raise_for_status.return_value = None
    auth_response = Mock()
    auth_response.json.return_value = {"exists": 1}
    auth_response.raise_for_status.return_value = None
    mock_post.side_effect = [create_response, auth_response]

    uploaded = mock_client.upload_attachment("PARENTITEM123", str(file_path))

    assert mock_post.call_count == 2
    assert mock_post.call_args_list[1].args[0] == f'{items_url}/ATT1/file'
    assert uploaded.key == "ATT1"


def test_upload_attachment_missing_file(mock_client):
    """The file is checked before any request is made."""
    with pytest.raises(FileNotFoundError):
        mock_client.upload_attachment("PARENTITEM123", "/does/not/exist.pdf")

@patch('requests.get')
@patch('builtins.open', new_callable=Mock)
def test_download_attachment(mock_open, mock_get, mock_client):
    attachment_id = "ATTACHMENT123"
    output_path = "/tmp/downloaded_file.pdf"
    file_content = b"This is the content of the downloaded file."

    # Mock get_item call for the attachment
    mock_item_response = Mock()
    mock_item_response.json.return_value = {
        "key": attachment_id,
        "version": 1,
        "data": {
            "key": attachment_id,
            "itemType": "attachment",
            "title": "Downloaded Attachment",
            "parentItem": "PARENTITEM123",
            "creators": [],
            "date": "2024",
            "url": ""
        },
        "links": {
            "file": {"href": "https://api.zotero.org/users/test_user/items/ATTACHMENT123/file"}
        }
    }
    mock_item_response.raise_for_status.return_value = None

    # Mock the actual file download call
    mock_file_download_response = Mock()
    mock_file_download_response.iter_content.return_value = [file_content]
    mock_file_download_response.raise_for_status.return_value = None

    # Configure mock_get to return different responses for sequential calls
    mock_get.side_effect = [mock_item_response, mock_file_download_response]

    # Mock file writing
    mock_file_handle = Mock()
    mock_open.return_value = MagicMock()
    mock_open.return_value.__enter__.return_value = mock_file_handle
    mock_open.return_value.__exit__.return_value = None

    downloaded_path = mock_client.download_attachment(attachment_id, output_path)

    # Assert get_item was called
    mock_get.assert_any_call(
        f'{mock_client.BASE_URL}/{mock_client.library_type}/{mock_client.user_id}/items/{attachment_id}',
        headers=mock_client.headers,
        timeout=mock_client.TIMEOUT,
    )

    # Assert file download was called
    mock_get.assert_any_call(
        "https://api.zotero.org/users/test_user/items/ATTACHMENT123/file",
        headers=mock_client.headers,
        stream=True,
        timeout=mock_client.TIMEOUT,
    )

    # Assert file was opened and content written
    mock_open.assert_called_once_with(output_path, 'wb')
    mock_file_handle.write.assert_called_once_with(file_content)

    assert downloaded_path == output_path

@patch('requests.get')
def test_download_attachment_not_attachment(mock_get, mock_client):
    attachment_id = "NOTATTACHMENT123"
    output_path = "/tmp/output.pdf"

    mock_item_response = Mock()
    mock_item_response.json.return_value = {
        "key": attachment_id,
        "version": 1,
        "data": {
            "key": attachment_id,
            "itemType": "book", # Not an attachment
            "title": "Not an Attachment",
            "creators": [],
            "date": "2024",
            "url": ""
        },
        "links": {}
    }
    mock_item_response.raise_for_status.return_value = None
    mock_get.return_value = mock_item_response

    with pytest.raises(ValueError, match=f"Item {attachment_id} is not an attachment."):
        mock_client.download_attachment(attachment_id, output_path)

@patch('builtins.open', new_callable=Mock)
@patch('requests.get')
def test_download_attachment_uses_file_endpoint(mock_get, mock_open, mock_client):
    """The file comes from /items/<key>/file; item links are not consulted."""
    attachment_id = "NOFILELINK123"
    output_path = "/tmp/output.pdf"

    item_response = Mock()
    item_response.json.return_value = {
        "key": attachment_id,
        "version": 1,
        "data": {
            "key": attachment_id,
            "itemType": "attachment",
            "title": "No File Link",
            "creators": [],
            "date": "2024",
            "url": ""
        },
        "links": {}  # no usable link, and none is needed
    }
    item_response.raise_for_status.return_value = None

    file_response = Mock()
    file_response.iter_content.return_value = [b"file bytes"]
    file_response.raise_for_status.return_value = None
    mock_get.side_effect = [item_response, file_response]

    mock_open.return_value = MagicMock()
    mock_open.return_value.__enter__.return_value = Mock()
    mock_open.return_value.__exit__.return_value = None

    assert mock_client.download_attachment(attachment_id, output_path) == output_path

    mock_get.assert_any_call(
        f'{mock_client.BASE_URL}/{mock_client.library_type}/{mock_client.user_id}/items/{attachment_id}/file',
        headers=mock_client.headers,
        stream=True,
        timeout=mock_client.TIMEOUT,
    )

@patch('zotero_client.api.client.openai.OpenAI')
@patch('zotero_client.api.client.ZoteroClient.get_item')
def test_summarize_item_content(mock_get_item, mock_openai, mock_client):
    mock_client.openai_api_key = "test_openai_key"
    item_id = "ITEMTOSUMMARIZE"
    item_title = "A Study on Advanced AI"
    item_abstract = "This paper explores the latest advancements in artificial intelligence, focusing on machine learning and neural networks."
    expected_summary = "The paper discusses recent AI progress, particularly in machine learning and neural networks."

    mock_item = Item(
        key=item_id,
        version=1,
        item_type="journalArticle",
        title=item_title,
        creators=[],
        date="2023",
        url="",
        abstract_note=item_abstract
    )
    mock_get_item.return_value = mock_item

    mock_chat_completion = Mock()
    mock_chat_completion.choices = [Mock()]
    mock_chat_completion.choices[0].message.content = expected_summary
    mock_openai.return_value.chat.completions.create.return_value = mock_chat_completion

    summary = mock_client.summarize_item_content(item_id)

    mock_get_item.assert_called_once_with(item_id)
    mock_openai.assert_called_once_with(api_key="test_openai_key")
    mock_openai.return_value.chat.completions.create.assert_called_once_with(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "Summarize the following text:"},
            {"role": "user", "content": f"{item_title}\n\nAbstract: {item_abstract}"}
        ]
    )
    assert summary == expected_summary

@patch('zotero_client.api.client.ZoteroClient.get_item')
def test_summarize_item_content_no_openai_key(mock_get_item, mock_client):
    mock_client.openai_api_key = None
    item_id = "ITEMTOSUMMARIZE"

    with pytest.raises(ValueError, match="OpenAI API key is not configured."):
        mock_client.summarize_item_content(item_id)

@patch('zotero_client.api.client.openai.OpenAI')
@patch('zotero_client.api.client.ZoteroClient.get_item')
def test_summarize_item_content_openai_error(mock_get_item, mock_openai, mock_client):
    mock_client.openai_api_key = "test_openai_key"
    item_id = "ITEMTOSUMMARIZE"
    item_title = "A Study on Advanced AI"

    mock_item = Item(
        key=item_id,
        version=1,
        item_type="journalArticle",
        title=item_title,
        creators=[],
        date="2023",
        url="",
        abstract_note=None
    )
    mock_get_item.return_value = mock_item

    mock_openai.return_value.chat.completions.create.side_effect = Exception("API connection error")

    with pytest.raises(RuntimeError, match="OpenAI API error: API connection error"):
        mock_client.summarize_item_content(item_id)

@patch('zotero_client.api.client.ZoteroClient.get_items')
def test_find_duplicates(mock_get_items, mock_client):
    item1 = Item(key="ITEM1", item_type="journalArticle", title="Test Article", creators=[{'creatorType': 'author', 'firstName': 'John', 'lastName': 'Doe'}], date="2023-01-01", url="", version=1)
    item2 = Item(key="ITEM2", item_type="journalArticle", title="Test Article", creators=[{'creatorType': 'author', 'firstName': 'John', 'lastName': 'Doe'}], date="2023-02-01", url="", version=1)
    item3 = Item(key="ITEM3", item_type="book", title="Another Article", creators=[{'creatorType': 'author', 'firstName': 'Jane', 'lastName': 'Smith'}], date="2022-01-01", url="", version=1)
    item4 = Item(key="ITEM4", item_type="journalArticle", title="Test Article", creators=[{'creatorType': 'author', 'firstName': 'J.', 'lastName': 'Doe'}], date="2023-03-01", url="", version=1) # Different first name, same last name
    item5 = Item(key="ITEM5", item_type="journalArticle", title="Test Article", creators=[{'creatorType': 'author', 'firstName': 'John', 'lastName': 'Doe'}], date="2024-01-01", url="", version=1) # Different year

    mock_get_items.return_value = [item1, item2, item3, item4, item5]

    duplicates = mock_client.find_duplicates()

    assert len(duplicates) == 1
    duplicate_key = "testarticle-doe-2023"
    assert duplicate_key in duplicates
    assert len(duplicates[duplicate_key]) == 3
    assert item1 in duplicates[duplicate_key]
    assert item2 in duplicates[duplicate_key]
    assert item5 not in duplicates[duplicate_key] # Different year, so not a duplicate

@patch('zotero_client.api.client.ZoteroClient.get_items')
def test_find_duplicates_no_duplicates(mock_get_items, mock_client):
    item1 = Item(key="ITEM1", item_type="journalArticle", title="Unique Article 1", creators=[{'creatorType': 'author', 'firstName': 'John', 'lastName': 'Doe'}], date="2023-01-01", url="", version=1)
    item2 = Item(key="ITEM2", item_type="book", title="Unique Article 2", creators=[{'creatorType': 'author', 'firstName': 'Jane', 'lastName': 'Smith'}], date="2022-01-01", url="", version=1)

    mock_get_items.return_value = [item1, item2]

    duplicates = mock_client.find_duplicates()

    assert len(duplicates) == 0

@patch('zotero_client.api.client.ZoteroClient.get_items')
def test_find_duplicates_missing_data(mock_get_items, mock_client):
    item1 = Item(key="ITEM1", item_type="journalArticle", title="Article with no creators", creators=[], date="2023-01-01", url="", version=1)
    item2 = Item(key="ITEM2", item_type="book", title="Article with no date", creators=[{'creatorType': 'author', 'firstName': 'John', 'lastName': 'Doe'}], date="", url="", version=1)

    mock_get_items.return_value = [item1, item2]

    duplicates = mock_client.find_duplicates()

    assert len(duplicates) == 0
