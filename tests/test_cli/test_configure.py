import pytest
from unittest.mock import patch, MagicMock, call
from zotero_client.cli.main import configure_cli

@patch('rich.prompt.Prompt.ask')
@patch('zotero_client.cli.main.set_key')
def test_configure_cli(mock_set_key, mock_ask):
    mock_ask.side_effect = ["test_api_key_input", "test_user_id_input"]

    with patch('zotero_client.cli.main.console.print') as mock_print:
        configure_cli(MagicMock())

    mock_ask.assert_any_call("Enter your Zotero API Key")
    mock_ask.assert_any_call("Enter your Zotero User ID")
    mock_set_key.assert_any_call('.env', 'ZOTERO_API_KEY', 'test_api_key_input')
    mock_set_key.assert_any_call('.env', 'ZOTERO_USER_ID', 'test_user_id_input')

@patch('rich.prompt.Prompt.ask')
@patch('sys.exit')
def test_configure_cli_keyboard_interrupt(mock_exit, mock_ask):
    mock_ask.side_effect = [KeyboardInterrupt]

    with patch('zotero_client.cli.main.console.print') as mock_print:
        configure_cli(MagicMock())

    mock_ask.assert_called_once_with("Enter your Zotero API Key")
    mock_exit.assert_called_once_with(0)
