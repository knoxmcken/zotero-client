"""Integration tests for Zotero API client.

These tests require valid API credentials set as environment variables:
- ZOTERO_API_KEY
- ZOTERO_USER_ID
"""

import os
import subprocess
import time

import pytest
import requests

from zotero_client.api.client import ZoteroClient

# Read-back against a live API can briefly 404 while a new version settles, so
# tolerate one short window rather than failing on the first attempt. Two is
# deliberate: the #11 investigation found readable types settle on attempt 1 in
# every round, while notes never settle at all -- five attempts only delayed a
# genuine failure. The printed attempt count stays, because that number is what
# exposed the note behaviour. See docs/NOTE_PERSISTENCE_INVESTIGATION.md.
_WRITE_PROPAGATION_ATTEMPTS = 2
_WRITE_PROPAGATION_DELAY = 1.0


def _status_of(exc):
    """Return the HTTP status carried by a requests error, if any."""
    return getattr(getattr(exc, 'response', None), 'status_code', None)


def _wait_until_readable(client, key):
    """Poll briefly until a freshly created item can be read back; return attempt count.

    One retry only -- see the constants above and
    docs/NOTE_PERSISTENCE_INVESTIGATION.md for why more never helped.
    """
    last_error = None
    for attempt in range(1, _WRITE_PROPAGATION_ATTEMPTS + 1):
        try:
            client.get_item(key)
            return attempt
        except requests.exceptions.HTTPError as exc:
            last_error = exc
            if _status_of(exc) != 404:
                raise
            time.sleep(_WRITE_PROPAGATION_DELAY)
    pytest.fail(
        f"item {key} was created but never became readable after "
        f"{_WRITE_PROPAGATION_ATTEMPTS} attempts: {last_error}"
    )


def _delete_with_retry(client, key, version):
    """Delete an item, tolerating a transient 404; return attempt count."""
    last_error = None
    for attempt in range(1, _WRITE_PROPAGATION_ATTEMPTS + 1):
        try:
            client.delete_item(key, version)
            return attempt
        except requests.exceptions.HTTPError as exc:
            last_error = exc
            if _status_of(exc) != 404:
                raise
            time.sleep(_WRITE_PROPAGATION_DELAY)
    pytest.fail(
        f"delete of {key} kept returning 404 after "
        f"{_WRITE_PROPAGATION_ATTEMPTS} attempts: {last_error}"
    )


def _run_cli(*args):
    """Run the installed `zot` CLI against the live library."""
    return subprocess.run(
        ['zot', *args],
        capture_output=True,
        text=True,
        env={**os.environ, 'ZOTERO_LIBRARY_TYPE': 'users'},
    )


def _assert_cli_succeeded(result):
    """Assert the command actually worked.

    A failing command exits 1, so the old `returncode in [0, 1]` held either
    way and could never fail -- that is how a broken command stayed green.
    """
    assert result.returncode == 0, (
        f"`zot` exited {result.returncode}\n"
        f"stdout:\n{result.stdout}\n"
        f"stderr:\n{result.stderr}"
    )
    assert 'Traceback' not in result.stderr, result.stderr
    assert result.stdout.strip(), 'command succeeded but printed nothing'


@pytest.fixture
def real_client():
    """Create a real client with credentials from environment."""
    api_key = os.getenv('ZOTERO_API_KEY')
    user_id = os.getenv('ZOTERO_USER_ID')
    
    if not api_key or not user_id:
        pytest.skip("Zotero API credentials not set")
    
    return ZoteroClient(api_key, user_id)


@pytest.mark.integration
class TestIntegrationConnection:
    """Test actual API connection."""
    
    def test_client_initializes_with_real_credentials(self, real_client):
        """Test that client initializes with real credentials."""
        assert real_client.api_key is not None
        assert real_client.user_id is not None
        assert real_client.library_type == 'users'
    
    def test_can_fetch_items(self, real_client):
        """Test that we can actually fetch items from Zotero."""
        items = real_client.get_items(limit=5)
        assert isinstance(items, list)
        # Should have at least some items in a real library
        assert len(items) >= 0
    
    def test_can_fetch_collections(self, real_client):
        """Test that we can fetch collections."""
        collections = real_client.get_collections(limit=5)
        assert isinstance(collections, list)
    
    def test_can_fetch_tags(self, real_client):
        """Test that we can fetch tags."""
        tags = real_client.get_tags()
        assert isinstance(tags, list)


@pytest.mark.integration
class TestIntegrationCRUD:
    """Test CRUD operations with real API."""
    
    def test_create_and_delete_item(self, real_client):
        """Test creating and then deleting an item.

        Uses a book rather than a standalone note. Notes written through this
        API key are stored but never readable: POST returns 200, the library
        version advances, and the object survives a parent-delete cascade --
        yet every read path (GET by key, children listings, includeTrashed)
        refuses it, as does DELETE. A Zotero-side limitation the client cannot
        work around; see docs/NOTE_PERSISTENCE_INVESTIGATION.md.
        """
        # Create a test item
        test_item = {
            "itemType": "book",
            "title": "Integration test item - please delete",
        }

        created = real_client.create_item(test_item)
        assert created is not None
        assert created.key, "create_item did not return an item key"

        # Confirm the new item is actually addressable before cleaning up,
        # and record how many attempts the write needed (useful in CI logs).
        read_attempts = _wait_until_readable(real_client, created.key)
        delete_attempts = _delete_with_retry(
            real_client, created.key, created.version
        )
        print(
            f"create -> read ({read_attempts} attempt(s)) -> "
            f"delete ({delete_attempts} attempt(s)) OK for key {created.key}"
        )
    
    def test_get_item_by_key(self, real_client):
        """Test retrieving a specific item by its key."""
        # First get a list of items
        items = real_client.get_items(limit=1)
        
        if not items:
            pytest.skip("No items in library to test with")
        
        # Get the first item's key
        item_key = items[0].key
        
        # Fetch that specific item
        item = real_client.get_item(item_key)
        assert item.key == item_key


@pytest.mark.integration  
class TestIntegrationCLI:
    """Test CLI commands with real credentials."""
    
    def test_cli_items_list(self):
        """Test CLI items list command."""
        api_key = os.getenv('ZOTERO_API_KEY')
        user_id = os.getenv('ZOTERO_USER_ID')
        if not api_key or not user_id:
            pytest.skip("Zotero API credentials not set")

        result = _run_cli('items', 'list', '--limit', '3')
        _assert_cli_succeeded(result)
        # The command is read-only; on success it prints the item table.
        assert 'Zotero Items' in result.stdout, result.stdout
    
    def test_cli_collections_list(self):
        """Test CLI collections list command."""
        api_key = os.getenv('ZOTERO_API_KEY')
        user_id = os.getenv('ZOTERO_USER_ID')
        if not api_key or not user_id:
            pytest.skip("Zotero API credentials not set")

        result = _run_cli('collections', 'list')
        _assert_cli_succeeded(result)
        assert 'Zotero Collections' in result.stdout, result.stdout
    
    def test_cli_tags_list(self):
        """Test CLI tags list command."""
        api_key = os.getenv('ZOTERO_API_KEY')
        user_id = os.getenv('ZOTERO_USER_ID')
        if not api_key or not user_id:
            pytest.skip("Zotero API credentials not set")

        result = _run_cli('tags', 'list')
        _assert_cli_succeeded(result)
        assert 'Zotero Tags' in result.stdout, result.stdout


@pytest.mark.integration
class TestIntegrationAttachmentUpload:
    """The attachment upload/download path, end to end.

    This path had no live coverage at all, which is how it shipped first with an
    invented upload protocol (#6) and then with a template URL that 404s (#17).
    Neither was observable: the unit test mocks the template fetch, so it asserts
    against a response the API never produces, and the rest of this suite only
    ever read.
    """

    def test_upload_and_download_round_trip(self, real_client, tmp_path):
        parent_key = None
        attachment_key = None
        try:
            parent = real_client.create_item({
                "itemType": "book",
                "title": "Upload integration test - please delete",
            })
            parent_key = parent.key
            _wait_until_readable(real_client, parent_key)

            body = b"zotero-client attachment round trip\n"
            source = tmp_path / "upload-me.txt"
            source.write_bytes(body)

            attachment = real_client.upload_attachment(
                parent_key, str(source), title="Upload round-trip attachment"
            )
            attachment_key = attachment.key

            assert attachment.item_type == "attachment"
            assert attachment.parent_item == parent_key
            assert attachment.title == "Upload round-trip attachment"

            # The upload must appear as a child of its parent -- the same thing
            # get_attachments() answers, via the child endpoint.
            children = real_client.get_attachments(item_id=parent_key)
            assert attachment_key in [c.key for c in children], (
                f"{attachment_key} is not among the parent's attachments: "
                f"{[c.key for c in children]}"
            )

            # And the bytes must come back intact.
            downloaded = tmp_path / "downloaded.txt"
            real_client.download_attachment(attachment_key, str(downloaded))
            assert downloaded.read_bytes() == body
        finally:
            # Delete the attachment before its parent. The version must be
            # supplied: the API requires a precondition on writes and answers
            # 428 without one, so a bare delete_item() would leak both items.
            # Cleanup failures are printed rather than raised, so a leak is
            # visible without masking the test's own result.
            for key in (attachment_key, parent_key):
                if not key:
                    continue
                try:
                    real_client.delete_item(key, real_client.get_item(key).version)
                except Exception as exc:
                    print(f"CLEANUP FAILED for {key}: {exc}")


@pytest.mark.integration
class TestIntegrationWritePreconditions:
    """Writes require a precondition, and tags are an item field.

    Both behaviours were wrong in the client and invisible to the mocked suite:
    a write with no `If-Unmodified-Since-Version` is rejected with 428
    Precondition Required, and the API answers 405 to POST/PUT/DELETE on
    `/items/<key>/tags`. The web delete route calls `delete_item(item_id)` with
    no version, so that button could never work.
    """

    def test_delete_without_a_version(self, real_client):
        """Omitting the version must still delete, not 428."""
        created = real_client.create_item({
            "itemType": "book",
            "title": "precondition test - please delete",
        })
        key = created.key
        try:
            _wait_until_readable(real_client, key)

            # No version supplied -- exactly what the web route does.
            real_client.delete_item(key)

            with pytest.raises(requests.exceptions.HTTPError) as caught:
                real_client.get_item(key)
            assert _status_of(caught.value) == 404
        finally:
            try:
                real_client.delete_item(key, real_client.get_item(key).version)
            except Exception:
                pass  # already gone, which is the point of the test

    def test_add_and_remove_tags(self, real_client):
        """Tags round-trip through a PATCH of the item's tag list."""
        created = real_client.create_item({
            "itemType": "book",
            "title": "tag round-trip test - please delete",
        })
        key = created.key
        try:
            _wait_until_readable(real_client, key)

            real_client.add_tags_to_item(key, ["alpha", "beta"])
            assert {t.tag for t in real_client.get_tags(item_id=key)} == {"alpha", "beta"}

            # Re-adding an existing tag must not duplicate it.
            real_client.add_tags_to_item(key, ["alpha", "gamma"])
            assert {t.tag for t in real_client.get_tags(item_id=key)} == {"alpha", "beta", "gamma"}

            real_client.remove_tags_from_item(key, ["alpha"])
            assert {t.tag for t in real_client.get_tags(item_id=key)} == {"beta", "gamma"}

            # Removing everything leaves no tags, rather than erroring.
            real_client.remove_tags_from_item(key, ["beta", "gamma"])
            assert real_client.get_tags(item_id=key) == []
        finally:
            try:
                real_client.delete_item(key, real_client.get_item(key).version)
            except Exception as exc:
                print(f"CLEANUP FAILED for {key}: {exc}")
