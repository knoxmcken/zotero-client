import pytest
from unittest.mock import patch, MagicMock
from zotero_client.cli.main import list_items
from zotero_client.models.item import Item

@pytest.fixture
def mock_client_with_items():
    mock_item = Item(key="ITEM123", version=1, item_type="book", title="Test Book", creators=[], date="2023", url="")
    mock_client = MagicMock()
    mock_client.get_items.return_value = [mock_item]
    return mock_client

@patch('zotero_client.cli.main.load_config')
@patch('zotero_client.cli.main.ZoteroClient')
def test_list_items_with_search_parameters(mock_zotero_client, mock_load_config, mock_client_with_items):
    mock_load_config.return_value = ("test_api_key", "test_user_id")
    mock_zotero_client.return_value = mock_client_with_items

    mock_args = MagicMock(
        limit=10,
        query="search term",
        qmode="everything",
        item_type="journalArticle",
        tag="biology",
        include_trashed=True
    )

    with patch('sys.stdout', new=MagicMock()) as mock_stdout:
        list_items(mock_args)

    mock_zotero_client.assert_called_once_with("test_api_key", "test_user_id")
    mock_client_with_items.get_items.assert_called_once_with(
        limit=10,
        q="search term",
        qmode="everything",
        item_type="journalArticle",
        tag="biology",
        include_trashed=True
    )
    captured_output = "".join([c.args[0] for c in mock_stdout.write.call_args_list])
    assert "[book] Test Book\n" in captured_output

@patch('zotero_client.cli.main.load_config')
@patch('zotero_client.cli.main.ZoteroClient')
def test_list_items_no_search_parameters(mock_zotero_client, mock_load_config, mock_client_with_items):
    mock_load_config.return_value = ("test_api_key", "test_user_id")
    mock_zotero_client.return_value = mock_client_with_items

    mock_args = MagicMock(
        limit=None,
        query=None,
        qmode=None,
        item_type=None,
        tag=None,
        include_trashed=False
    )

    with patch('sys.stdout', new=MagicMock()) as mock_stdout:
        list_items(mock_args)

        mock_zotero_client.assert_called_once_with("test_api_key", "test_user_id")
        mock_client_with_items.get_items.assert_called_once_with(
            limit=None,
            q=None,
            qmode=None,
            item_type=None,
            tag=None,
            include_trashed=False
        )
        captured_output = "".join([c.args[0] for c in mock_stdout.write.call_args_list])
        assert "[book] Test Book\n" in captured_output

@pytest.fixture
def mock_client_with_attachments():
    mock_attachment = Item(key="ATTACHMENT1", version=1, item_type="attachment", title="Test Attachment", parent_item="PARENTITEM123", creators=[], date="2024", url="")
    mock_client = MagicMock()
    mock_client.get_attachments.return_value = [mock_attachment]
    return mock_client

@patch('zotero_client.cli.main.load_config')
@patch('zotero_client.cli.main.ZoteroClient')
def test_list_attachments_cli(mock_zotero_client, mock_load_config, mock_client_with_attachments):
    mock_load_config.return_value = ("test_api_key", "test_user_id")
    mock_zotero_client.return_value = mock_client_with_attachments

    mock_args = MagicMock(
        item_id="PARENTITEM123",
        limit=5
    )

    with patch('sys.stdout', new=MagicMock()) as mock_stdout:
        from zotero_client.cli.main import list_attachments # Import here to avoid circular dependency issues with patching
        list_attachments(mock_args)

    mock_zotero_client.assert_called_once_with("test_api_key", "test_user_id")
    mock_client_with_attachments.get_attachments.assert_called_once_with(
        item_id="PARENTITEM123",
        limit=5
    )
    captured_output = "".join([c.args[0] for c in mock_stdout.write.call_args_list])
    assert "[Attachment] Test Attachment (Key: ATTACHMENT1, Parent: PARENTITEM123)\n" in captured_output

@patch('zotero_client.cli.main.load_config')
@patch('zotero_client.cli.main.ZoteroClient')
def test_upload_attachment_cli(mock_zotero_client, mock_load_config):
    mock_load_config.return_value = ("test_api_key", "test_user_id")
    
    mock_uploaded_item = Item(key="UPLOADED1", version=1, item_type="attachment", title="Uploaded File", parent_item="PARENT456", creators=[], date="2024", url="")
    mock_client_instance = MagicMock()
    mock_client_instance.upload_attachment.return_value = mock_uploaded_item
    mock_zotero_client.return_value = mock_client_instance

    mock_args = MagicMock(
        parent_item_id="PARENT456",
        file_path="/tmp/test_upload.pdf",
        title="Uploaded File"
    )

    with patch('sys.stdout', new=MagicMock()) as mock_stdout:
        from zotero_client.cli.main import upload_attachment_cli
        upload_attachment_cli(mock_args)

    mock_zotero_client.assert_called_once_with("test_api_key", "test_user_id")
    mock_client_instance.upload_attachment.assert_called_once_with(
        "PARENT456",
        "/tmp/test_upload.pdf",
        "Uploaded File"
    )
    captured_output = "".join([c.args[0] for c in mock_stdout.write.call_args_list])
    assert "Successfully uploaded attachment: Uploaded File (Key: UPLOADED1)\n" in captured_output

@patch('zotero_client.cli.main.load_config')
@patch('zotero_client.cli.main.ZoteroClient')
@patch('sys.exit')
def test_upload_attachment_cli_file_not_found(mock_exit, mock_zotero_client, mock_load_config):
    mock_load_config.return_value = ("test_api_key", "test_user_id")
    
    mock_client_instance = MagicMock()
    mock_client_instance.upload_attachment.side_effect = FileNotFoundError("File not found")
    mock_zotero_client.return_value = mock_client_instance

    mock_args = MagicMock(
        parent_item_id="PARENT456",
        file_path="/tmp/non_existent_file.pdf",
        title="Non Existent File"
    )

    with patch('sys.stdout', new=MagicMock()) as mock_stdout:
        from zotero_client.cli.main import upload_attachment_cli
        upload_attachment_cli(mock_args)

    mock_zotero_client.assert_called_once_with("test_api_key", "test_user_id")
    mock_client_instance.upload_attachment.assert_called_once_with(
        "PARENT456",
        "/tmp/non_existent_file.pdf",
        "Non Existent File"
    )
    captured_output = "".join([c.args[0] for c in mock_stdout.write.call_args_list])
    assert "Error: File not found at /tmp/non_existent_file.pdf\n" in captured_output
    mock_exit.assert_called_once_with(1)
