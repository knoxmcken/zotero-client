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
