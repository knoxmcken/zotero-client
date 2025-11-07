import pytest
from unittest.mock import Mock, patch, MagicMock
import builtins
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

@patch('requests.put')
@patch('requests.post')
@patch('requests.get')
@patch('os.path.basename', return_value="test_file.pdf")
@patch('builtins.open', new_callable=Mock)
def test_upload_attachment(mock_open, mock_basename, mock_get, mock_post, mock_put, mock_client):
    parent_item_id = "PARENTITEM123"
    file_path = "/path/to/test_file.pdf"
    title = "My Custom Attachment Title"

    # Mock get_attachment_template
    mock_get.return_value.json.return_value = {
        "itemType": "attachment",
        "parentItem": "PARENTITEM123",
        "linkMode": "imported_url", # Changed to imported_url
        "contentType": "application/pdf",
        "filename": "test_file.pdf",
        "title": "Test Attachment"
    }
    mock_get.return_value.raise_for_status.return_value = None

    # Mock create_item (requests.post)
    mock_post.return_value.json.return_value = [{
        "key": "UPLOADATTACHMENT1",
        "version": 1,
        "data": {
            "key": "UPLOADATTACHMENT1",
            "itemType": "attachment",
            "title": title, # Dynamically set title
            "parentItem": "PARENTITEM123",
            "filename": "test_file.pdf",
            "contentType": "application/pdf",
            "linkMode": "imported_file"
        },
        "links": {
            "file": {"href": "https://api.zotero.org/users/test_user/items/UPLOADATTACHMENT1/file"}
        }
    }]
    mock_post.return_value.raise_for_status.return_value = None

    # Mock file content
    mock_file_handle = Mock()
    mock_file_handle.read.return_value = b"file content"
    
    mock_open.return_value = MagicMock()
    mock_open.return_value.__enter__.return_value = mock_file_handle
    mock_open.return_value.__exit__.return_value = None

    # Mock upload file (requests.put)
    mock_put.return_value.raise_for_status.return_value = None

    parent_item_id = "PARENTITEM123"
    file_path = "/path/to/test_file.pdf"
    title = "My Custom Attachment Title"

    uploaded_attachment = mock_client.upload_attachment(parent_item_id, file_path, title)

    # Assert get_attachment_template was called
    mock_get.assert_called_once_with(
        f'{mock_client.BASE_URL}/{mock_client.library_type}/{mock_client.user_id}/items/new',
        headers=mock_client.headers,
        params={'itemType': 'attachment', 'linkMode': 'imported_url', 'parentItem': parent_item_id}
    )

    # Assert create_item was called
    expected_post_data = {
        "itemType": "attachment",
        "parentItem": parent_item_id,
        "linkMode": "imported_file",
        "contentType": "application/octet-stream", # This is set in the client, not from template
        "filename": "test_file.pdf",
        "title": title
    }
    mock_post.assert_called_once_with(
        f'{mock_client.BASE_URL}/{mock_client.library_type}/{mock_client.user_id}/items',
        headers=mock_client.headers,
        json=[expected_post_data]
    )

    # Assert file was opened
    mock_open.assert_called_once_with(file_path, 'rb')

    # Assert file upload was called
    expected_upload_headers = mock_client.headers.copy()
    expected_upload_headers['Content-Type'] = 'application/octet-stream'
    mock_put.assert_called_once_with(
        "https://api.zotero.org/users/test_user/items/UPLOADATTACHMENT1/file",
        headers=expected_upload_headers,
        data=b"file content"
    )

    assert isinstance(uploaded_attachment, Item)
    assert uploaded_attachment.key == "UPLOADATTACHMENT1"
    assert uploaded_attachment.title == title
    assert uploaded_attachment.parent_item == parent_item_id

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
        headers=mock_client.headers
    )

    # Assert file download was called
    mock_get.assert_any_call(
        "https://api.zotero.org/users/test_user/items/ATTACHMENT123/file",
        headers=mock_client.headers,
        stream=True
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

@patch('requests.get')
def test_download_attachment_no_file_link(mock_get, mock_client):
    attachment_id = "NOFILELINK123"
    output_path = "/tmp/output.pdf"

    mock_item_response = Mock()
    mock_item_response.json.return_value = {
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
        "links": {} # No file link
    }
    mock_item_response.raise_for_status.return_value = None
    mock_get.return_value = mock_item_response

    with pytest.raises(ValueError, match=f"Attachment {attachment_id} does not have a downloadable file."):
        mock_client.download_attachment(attachment_id, output_path)

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
