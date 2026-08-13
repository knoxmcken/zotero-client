import pytest
from zotero_client.api.client import ZoteroClient

@pytest.fixture
def mock_client():
    return ZoteroClient(api_key="test_key", user_id="test_user")
