import pytest
from unittest.mock import patch, MagicMock, call
from zotero_client.cli.main import configure_cli

@patch('builtins.input')
@patch('zotero_client.cli.main.set_key')
def test_configure_cli(mock_set_key, mock_input):
    mock_input.side_effect = ["test_api_key_input", "test_user_id_input"]

    # Mock sys.stdout to capture print statements
    with patch('sys.stdout', new=MagicMock()) as mock_stdout:
        configure_cli(MagicMock()) # args are not used in configure_cli

    mock_input.assert_any_call("Enter your Zotero API Key: ")
    mock_input.assert_any_call("Enter your Zotero User ID: ")
    mock_set_key.assert_any_call('.env', 'ZOTERO_API_KEY', 'test_api_key_input')
    mock_set_key.assert_any_call('.env', 'ZOTERO_USER_ID', 'test_user_id_input')

    # Capture all calls to mock_stdout.write and join them
    captured_output = "".join([c.args[0] for c in mock_stdout.write.call_args_list])

    assert "--- Zotero Client Configuration ---\n" in captured_output
    assert "Configuration saved to .env\n" in captured_output
    assert "Please restart your shell or run 'load_dotenv()' if you are in an interactive session.\n" in captured_output

@patch('builtins.input')
@patch('sys.exit')
def test_configure_cli_keyboard_interrupt(mock_exit, mock_input):
    mock_input.side_effect = [KeyboardInterrupt]

    with patch('sys.stdout', new=MagicMock()) as mock_stdout:
        configure_cli(MagicMock())

    mock_input.assert_called_once_with("Enter your Zotero API Key: ")
    mock_exit.assert_called_once_with(0)

    # Capture all calls to mock_stdout.write and join them
    captured_output = "".join([c.args[0] for c in mock_stdout.write.call_args_list])

    assert "--- Zotero Client Configuration ---\n" in captured_output
    assert "\nConfiguration cancelled.\n" in captured_output
