import pytest
from unittest.mock import patch, MagicMock
from zotero_client.cli.main import list_collections
from zotero_client.models.collection import Collection
from rich.table import Table
from rich.tree import Tree


@patch('zotero_client.cli.main.load_config')
@patch('zotero_client.cli.main.ZoteroClient')
def test_list_collections_flat_default(mock_zotero_client, mock_load_config):
    """Without --tree, output is the existing flat table."""
    mock_load_config.return_value = ("test_api_key", "test_user_id", "test_openai_key")
    mock_client = MagicMock()
    mock_client.get_collections.return_value = [
        Collection(key="COLLECTION1", name="Science", version=1)
    ]
    mock_zotero_client.return_value = mock_client

    mock_args = MagicMock(tree=False)

    with patch('zotero_client.cli.main.console.print') as mock_print:
        list_collections(mock_args)

    mock_client.get_collections.assert_called_once_with()
    mock_print.assert_called_once()
    assert isinstance(mock_print.call_args[0][0], Table)


@patch('zotero_client.cli.main.load_config')
@patch('zotero_client.cli.main.ZoteroClient')
def test_list_collections_tree(mock_zotero_client, mock_load_config):
    """--tree groups collections into a nested Tree by parent_collection."""
    mock_load_config.return_value = ("test_api_key", "test_user_id", "test_openai_key")
    mock_client = MagicMock()
    mock_client.get_collections.return_value = [
        Collection(key="SCIENCEKEY", name="Science", version=1),
        Collection(key="PHYSICSKEY", name="Physics", version=1, parent_collection="SCIENCEKEY"),
    ]
    mock_zotero_client.return_value = mock_client

    mock_args = MagicMock(tree=True)

    with patch('zotero_client.cli.main.console.print') as mock_print:
        list_collections(mock_args)

    mock_print.assert_called_once()
    tree = mock_print.call_args[0][0]
    assert isinstance(tree, Tree)
    assert len(tree.children) == 1
    root_node = tree.children[0]
    assert "Science" in str(root_node.label)
    assert len(root_node.children) == 1
    assert "Physics" in str(root_node.children[0].label)


@patch('zotero_client.cli.main.load_config')
@patch('zotero_client.cli.main.ZoteroClient')
def test_list_collections_tree_orphaned_parent(mock_zotero_client, mock_load_config):
    """A collection referencing a parent key not present in the fetched set is still shown, as a root."""
    mock_load_config.return_value = ("test_api_key", "test_user_id", "test_openai_key")
    mock_client = MagicMock()
    mock_client.get_collections.return_value = [
        Collection(key="ORPHANKEY", name="Orphan", version=1, parent_collection="MISSINGPARENT")
    ]
    mock_zotero_client.return_value = mock_client

    mock_args = MagicMock(tree=True)

    with patch('zotero_client.cli.main.console.print') as mock_print:
        list_collections(mock_args)

    tree = mock_print.call_args[0][0]
    assert len(tree.children) == 1
    assert "Orphan" in str(tree.children[0].label)
