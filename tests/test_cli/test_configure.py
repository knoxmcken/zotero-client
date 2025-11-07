import pytest
from unittest.mock import patch, MagicMock
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
    mock_stdout.write.assert_any_call("Configuration saved to .env")
    mock_stdout.write.assert_any_call("\n") # Newline after "Configuration saved to .env"
    mock_stdout.write.assert_any_call("Please restart your shell or run 'load_dotenv()' if you are in an interactive session.")
    mock_stdout.write.assert_any_call("\n") # Newline after the restart message
