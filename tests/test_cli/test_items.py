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
    mock_load_config.return_value = ("test_api_key", "test_user_id", "test_openai_key")
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

    mock_zotero_client.assert_called_once_with("test_api_key", "test_user_id", openai_api_key="test_openai_key")
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
    mock_load_config.return_value = ("test_api_key", "test_user_id", "test_openai_key")
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

        mock_zotero_client.assert_called_once_with("test_api_key", "test_user_id", openai_api_key="test_openai_key")
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
    mock_load_config.return_value = ("test_api_key", "test_user_id", "test_openai_key")
    mock_zotero_client.return_value = mock_client_with_attachments

    mock_args = MagicMock(
        item_id="PARENTITEM123",
        limit=5
    )

    with patch('sys.stdout', new=MagicMock()) as mock_stdout:
        from zotero_client.cli.main import list_attachments # Import here to avoid circular dependency issues with patching
        list_attachments(mock_args)

    mock_zotero_client.assert_called_once_with("test_api_key", "test_user_id", openai_api_key="test_openai_key")
    mock_client_with_attachments.get_attachments.assert_called_once_with(
        item_id="PARENTITEM123",
        limit=5
    )
    captured_output = "".join([c.args[0] for c in mock_stdout.write.call_args_list])
    assert "[Attachment] Test Attachment (Key: ATTACHMENT1, Parent: PARENTITEM123)\n" in captured_output

@patch('zotero_client.cli.main.load_config')
@patch('zotero_client.cli.main.ZoteroClient')
def test_upload_attachment_cli(mock_zotero_client, mock_load_config):
    mock_load_config.return_value = ("test_api_key", "test_user_id", "test_openai_key")
    
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

    mock_zotero_client.assert_called_once_with("test_api_key", "test_user_id", openai_api_key="test_openai_key")
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
    mock_load_config.return_value = ("test_api_key", "test_user_id", "test_openai_key")
    
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

    mock_zotero_client.assert_called_once_with("test_api_key", "test_user_id", openai_api_key="test_openai_key")
    mock_client_instance.upload_attachment.assert_called_once_with(
        "PARENT456",
        "/tmp/non_existent_file.pdf",
        "Non Existent File"
    )
    captured_output = "".join([c.args[0] for c in mock_stdout.write.call_args_list])
    assert "Error: File not found at /tmp/non_existent_file.pdf\n" in captured_output
    mock_exit.assert_called_once_with(1)

@patch('zotero_client.cli.main.load_config')
@patch('zotero_client.cli.main.ZoteroClient')
def test_download_attachment_cli(mock_zotero_client, mock_load_config):
    mock_load_config.return_value = ("test_api_key", "test_user_id", "test_openai_key")
    
    mock_client_instance = MagicMock()
    mock_client_instance.download_attachment.return_value = "/tmp/downloaded_file.pdf"
    mock_zotero_client.return_value = mock_client_instance

    mock_args = MagicMock(
        attachment_id="ATTACHMENT123",
        output_path="/tmp/downloaded_file.pdf"
    )

    with patch('sys.stdout', new=MagicMock()) as mock_stdout:
        from zotero_client.cli.main import download_attachment_cli
        download_attachment_cli(mock_args)

    mock_zotero_client.assert_called_once_with("test_api_key", "test_user_id", openai_api_key="test_openai_key")
    mock_client_instance.download_attachment.assert_called_once_with(
        "ATTACHMENT123",
        "/tmp/downloaded_file.pdf"
    )
    captured_output = "".join([c.args[0] for c in mock_stdout.write.call_args_list])
    assert "Successfully downloaded attachment ATTACHMENT123 to: /tmp/downloaded_file.pdf\n" in captured_output

@patch('zotero_client.cli.main.load_config')
@patch('zotero_client.cli.main.ZoteroClient')
@patch('sys.exit')
def test_download_attachment_cli_value_error(mock_exit, mock_zotero_client, mock_load_config):
    mock_load_config.return_value = ("test_api_key", "test_user_id", "test_openai_key")
    
    mock_client_instance = MagicMock()
    mock_client_instance.download_attachment.side_effect = ValueError("Item is not an attachment.")
    mock_zotero_client.return_value = mock_client_instance

    mock_args = MagicMock(
        attachment_id="NOTATTACHMENT123",
        output_path="/tmp/output.pdf"
    )

    with patch('sys.stdout', new=MagicMock()) as mock_stdout:
        from zotero_client.cli.main import download_attachment_cli
        download_attachment_cli(mock_args)

    mock_zotero_client.assert_called_once_with("test_api_key", "test_user_id", openai_api_key="test_openai_key")
    mock_client_instance.download_attachment.assert_called_once_with(
        "NOTATTACHMENT123",
        "/tmp/output.pdf"
    )
    captured_output = "".join([c.args[0] for c in mock_stdout.write.call_args_list])
    assert "Error: Item is not an attachment.\n" in captured_output
    mock_exit.assert_called_once_with(1)

@patch('zotero_client.cli.main.load_config')
@patch('zotero_client.cli.main.ZoteroClient')
def test_generate_citations_cli(mock_zotero_client, mock_load_config):
    mock_load_config.return_value = ("test_api_key", "test_user_id", "test_openai_key")
    
    mock_client_instance = MagicMock()
    mock_client_instance.get_citations.return_value = "<p>Formatted Citation</p>"
    mock_zotero_client.return_value = mock_client_instance

    mock_args = MagicMock(
        item_ids="ITEM123,ITEM456",
        style="apa",
        format="html",
        locale="en-US"
    )

    with patch('sys.stdout', new=MagicMock()) as mock_stdout:
        from zotero_client.cli.main import generate_citations_cli
        generate_citations_cli(mock_args)

    mock_zotero_client.assert_called_once_with("test_api_key", "test_user_id", openai_api_key="test_openai_key")
    mock_client_instance.get_citations.assert_called_once_with(
        ["ITEM123", "ITEM456"],
        "apa",
        "html",
        "en-US"
    )
    captured_output = "".join([c.args[0] for c in mock_stdout.write.call_args_list])
    assert "<p>Formatted Citation</p>\n" in captured_output

@patch('zotero_client.cli.main.load_config')
@patch('zotero_client.cli.main.ZoteroClient')
@patch('sys.exit')
def test_generate_citations_cli_error(mock_exit, mock_zotero_client, mock_load_config):
    mock_load_config.return_value = ("test_api_key", "test_user_id", "test_openai_key")
    
    mock_client_instance = MagicMock()
    mock_client_instance.get_citations.side_effect = Exception("API Error")
    mock_zotero_client.return_value = mock_client_instance

    mock_args = MagicMock(
        item_ids="ITEM123",
        style="apa",
        format="text",
        locale=None
    )

    with patch('sys.stdout', new=MagicMock()) as mock_stdout:
        from zotero_client.cli.main import generate_citations_cli
        generate_citations_cli(mock_args)

    mock_zotero_client.assert_called_once_with("test_api_key", "test_user_id", openai_api_key="test_openai_key")
    mock_client_instance.get_citations.assert_called_once_with(
        ["ITEM123"],
        "apa",
        "text",
        None
    )
    captured_output = "".join([c.args[0] for c in mock_stdout.write.call_args_list])
    assert "Error generating citations: API Error\n" in captured_output
    mock_exit.assert_called_once_with(1)

@patch('zotero_client.cli.main.load_config')
@patch('zotero_client.cli.main.ZoteroClient')
def test_summarize_item_cli(mock_zotero_client, mock_load_config):
    mock_load_config.return_value = ("test_api_key", "test_user_id", "test_openai_key")
    
    mock_client_instance = MagicMock()
    mock_client_instance.summarize_item_content.return_value = "This is a summary."
    mock_zotero_client.return_value = mock_client_instance

    mock_args = MagicMock(
        item_id="ITEMTOSUMMARIZE",
        prompt="Summarize this."
    )

    with patch('sys.stdout', new=MagicMock()) as mock_stdout:
        from zotero_client.cli.main import summarize_item_cli
        summarize_item_cli(mock_args)

    mock_zotero_client.assert_called_once_with("test_api_key", "test_user_id", openai_api_key="test_openai_key")
    mock_client_instance.summarize_item_content.assert_called_once_with(
        "ITEMTOSUMMARIZE",
        "Summarize this."
    )
    captured_output = "".join([c.args[0] for c in mock_stdout.write.call_args_list])
    assert "Summary for item ITEMTOSUMMARIZE:\nThis is a summary.\n" in captured_output

@patch('zotero_client.cli.main.load_config')
@patch('zotero_client.cli.main.ZoteroClient')
@patch('sys.exit')
def test_summarize_item_cli_no_openai_key(mock_exit, mock_zotero_client, mock_load_config):
    mock_load_config.return_value = ("test_api_key", "test_user_id", None)
    
    mock_client_instance = MagicMock()
    mock_zotero_client.return_value = mock_client_instance

    mock_args = MagicMock(
        item_id="ITEMTOSUMMARIZE",
        prompt="Summarize this."
    )

    with patch('sys.stdout', new=MagicMock()) as mock_stdout:
        from zotero_client.cli.main import summarize_item_cli
        summarize_item_cli(mock_args)

    mock_zotero_client.assert_called_once_with("test_api_key", "test_user_id", openai_api_key=None)
    captured_output = "".join([c.args[0] for c in mock_stdout.write.call_args_list])
    assert "Error: OPENAI_API_KEY is not set in .env file. Please configure it using 'cl configure'.\n" in captured_output
    mock_exit.assert_called_once_with(1)

@patch('zotero_client.cli.main.load_config')
@patch('zotero_client.cli.main.ZoteroClient')
@patch('sys.exit')
def test_summarize_item_cli_runtime_error(mock_exit, mock_zotero_client, mock_load_config):
    mock_load_config.return_value = ("test_api_key", "test_user_id", "test_openai_key")
    
    mock_client_instance = MagicMock()
    mock_client_instance.summarize_item_content.side_effect = RuntimeError("OpenAI API error")
    mock_zotero_client.return_value = mock_client_instance

    mock_args = MagicMock(
        item_id="ITEMTOSUMMARIZE",
        prompt="Summarize this."
    )

    with patch('sys.stdout', new=MagicMock()) as mock_stdout:
        from zotero_client.cli.main import summarize_item_cli
        summarize_item_cli(mock_args)

    mock_zotero_client.assert_called_once_with("test_api_key", "test_user_id", openai_api_key="test_openai_key")
    mock_client_instance.summarize_item_content.assert_called_once_with(
        "ITEMTOSUMMARIZE",
        "Summarize this."
    )
    captured_output = "".join([c.args[0] for c in mock_stdout.write.call_args_list])
    assert "Error: OpenAI API error\n" in captured_output
    mock_exit.assert_called_once_with(1)

@patch('zotero_client.cli.main.load_config')
@patch('zotero_client.cli.main.ZoteroClient')
def test_find_duplicates_cli(mock_zotero_client, mock_load_config):
    mock_load_config.return_value = ("test_api_key", "test_user_id", "test_openai_key")
    
    item1 = Item(key="ITEM1", item_type="journalArticle", title="Test Article", creators=[{'creatorType': 'author', 'firstName': 'John', 'lastName': 'Doe'}], date="2023-01-01", url="", version=1)
    item2 = Item(key="ITEM2", item_type="journalArticle", title="Test Article", creators=[{'creatorType': 'author', 'firstName': 'John', 'lastName': 'Doe'}], date="2023-02-01", url="", version=1)
    mock_duplicates = {"testarticle-doe-2023": [item1, item2]}

    mock_client_instance = MagicMock()
    mock_client_instance.find_duplicates.return_value = mock_duplicates
    mock_zotero_client.return_value = mock_client_instance

    mock_args = MagicMock()

    with patch('sys.stdout', new=MagicMock()) as mock_stdout:
        from zotero_client.cli.main import find_duplicates_cli
        find_duplicates_cli(mock_args)

    mock_zotero_client.assert_called_once_with("test_api_key", "test_user_id", openai_api_key="test_openai_key")
    mock_client_instance.find_duplicates.assert_called_once_with()
    captured_output = "".join([c.args[0] for c in mock_stdout.write.call_args_list])
    assert "Potential duplicate items found:\n" in captured_output
    assert "\nGroup: testarticle-doe-2023\n" in captured_output
    assert "  - [journalArticle] Test Article (Key: ITEM1, Date: 2023-01-01)\n" in captured_output
    assert "  - [journalArticle] Test Article (Key: ITEM2, Date: 2023-02-01)\n" in captured_output

@patch('zotero_client.cli.main.load_config')
@patch('zotero_client.cli.main.ZoteroClient')
def test_find_duplicates_cli_no_duplicates(mock_zotero_client, mock_load_config):
    mock_load_config.return_value = ("test_api_key", "test_user_id", "test_openai_key")
    
    mock_client_instance = MagicMock()
    mock_client_instance.find_duplicates.return_value = {}
    mock_zotero_client.return_value = mock_client_instance

    mock_args = MagicMock()

    with patch('sys.stdout', new=MagicMock()) as mock_stdout:
        from zotero_client.cli.main import find_duplicates_cli
        find_duplicates_cli(mock_args)

    mock_zotero_client.assert_called_once_with("test_api_key", "test_user_id", openai_api_key="test_openai_key")
    mock_client_instance.find_duplicates.assert_called_once_with()
    captured_output = "".join([c.args[0] for c in mock_stdout.write.call_args_list])
    assert "No potential duplicate items found.\n" in captured_output

@patch('zotero_client.cli.main.load_config')
@patch('zotero_client.cli.main.ZoteroClient')
@patch('sys.exit')
def test_find_duplicates_cli_error(mock_exit, mock_zotero_client, mock_load_config):
    mock_load_config.return_value = ("test_api_key", "test_user_id", "test_openai_key")
    
    mock_client_instance = MagicMock()
    mock_client_instance.find_duplicates.side_effect = Exception("API Error")
    mock_zotero_client.return_value = mock_client_instance

    mock_args = MagicMock()

    with patch('sys.stdout', new=MagicMock()) as mock_stdout:
        from zotero_client.cli.main import find_duplicates_cli
        find_duplicates_cli(mock_args)

    mock_zotero_client.assert_called_once_with("test_api_key", "test_user_id", openai_api_key="test_openai_key")
    mock_client_instance.find_duplicates.assert_called_once_with()
    captured_output = "".join([c.args[0] for c in mock_stdout.write.call_args_list])
    assert "Error finding duplicates: API Error\n" in captured_output
    mock_exit.assert_called_once_with(1)