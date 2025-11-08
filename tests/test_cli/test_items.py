import pytest
from unittest.mock import patch, MagicMock
from zotero_client.cli.main import list_items, find_duplicates_cli, list_attachments
from zotero_client.models.item import Item
from rich.table import Table

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

    with patch('zotero_client.cli.main.console.print') as mock_print:
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
    mock_print.assert_called_once()
    assert isinstance(mock_print.call_args[0][0], Table)

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

    with patch('zotero_client.cli.main.console.print') as mock_print:
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
    mock_print.assert_called_once()
    assert isinstance(mock_print.call_args[0][0], Table)

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

    with patch('zotero_client.cli.main.console.print') as mock_print:
        list_attachments(mock_args)

    mock_zotero_client.assert_called_once_with("test_api_key", "test_user_id", openai_api_key="test_openai_key")
    mock_client_with_attachments.get_attachments.assert_called_once_with(
        item_id="PARENTITEM123",
        limit=5
    )
    mock_print.assert_called_once()
    assert isinstance(mock_print.call_args[0][0], Table)

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

    with patch('zotero_client.cli.main.console.print') as mock_print:
        find_duplicates_cli(mock_args)

    mock_zotero_client.assert_called_once_with("test_api_key", "test_user_id", openai_api_key="test_openai_key")
    mock_client_instance.find_duplicates.assert_called_once_with()
    assert mock_print.call_count == 2
    assert isinstance(mock_print.call_args_list[1][0][0], Table)

@patch('zotero_client.cli.main.load_config')
@patch('zotero_client.cli.main.ZoteroClient')
def test_find_duplicates_cli_no_duplicates(mock_zotero_client, mock_load_config):
    mock_load_config.return_value = ("test_api_key", "test_user_id", "test_openai_key")
    
    mock_client_instance = MagicMock()
    mock_client_instance.find_duplicates.return_value = {}
    mock_zotero_client.return_value = mock_client_instance

    mock_args = MagicMock()

    with patch('zotero_client.cli.main.console.print') as mock_print:
        find_duplicates_cli(mock_args)

    mock_zotero_client.assert_called_once_with("test_api_key", "test_user_id", openai_api_key="test_openai_key")
    mock_client_instance.find_duplicates.assert_called_once_with()
    mock_print.assert_called_once_with("[bold green]No potential duplicate items found.[/]")

@patch('zotero_client.cli.main.load_config')
@patch('zotero_client.cli.main.ZoteroClient')
@patch('sys.exit')
def test_find_duplicates_cli_error(mock_exit, mock_zotero_client, mock_load_config):
    mock_load_config.return_value = ("test_api_key", "test_user_id", "test_openai_key")
    
    mock_client_instance = MagicMock()
    mock_client_instance.find_duplicates.side_effect = Exception("API Error")
    mock_zotero_client.return_value = mock_client_instance

    mock_args = MagicMock()

    with patch('zotero_client.cli.main.console.print') as mock_print:
        find_duplicates_cli(mock_args)

    mock_zotero_client.assert_called_once_with("test_api_key", "test_user_id", openai_api_key="test_openai_key")
    mock_client_instance.find_duplicates.assert_called_once_with()
    mock_print.assert_called_once_with("[bold red]Error finding duplicates:[/] API Error")
    mock_exit.assert_called_once_with(1)