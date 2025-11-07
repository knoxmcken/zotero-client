# API Documentation

## ZoteroClient

The main client class for interacting with the Zotero API.

### Initialization

```python
from zotero_client import ZoteroClient

client = ZoteroClient(
    api_key='your_api_key',
    user_id='your_user_id',
    library_type='users'  # or 'groups'
)
```

### Methods

#### `get_items(limit: Optional[int] = None, q: Optional[str] = None, qmode: Optional[str] = None, item_type: Optional[str] = None, tag: Optional[str] = None, include_trashed: Optional[bool] = None) -> List[Item]`

Retrieve items from the Zotero library with advanced search capabilities.

**Parameters:**
- `limit` (int, optional): Maximum number of items to retrieve.
- `q` (str, optional): Search query for quick search across titles and creator fields.
- `qmode` (str, optional): Query mode for 'q' parameter (e.g., 'everything' for full-text search).
- `item_type` (str, optional): Filter by item type (e.g., 'book', 'journalArticle').
- `tag` (str, optional): Filter by tag (supports boolean search syntax).
- `include_trashed` (bool, optional): If True, include trashed items in the results.

**Returns:**
- List of Item objects

**Example:**
```python
items = client.get_items(limit=10, q="test", qmode="everything", item_type="journalArticle", tag="research", include_trashed=True)
for item in items:
    print(item.title)
```

#### `get_item(item_id: str) -> Item`

Retrieve a specific item by ID.

**Parameters:**
- `item_id` (str): The item ID

**Returns:**
- Item object

**Example:**
```python
item = client.get_item('ABC123XYZ')
print(item.title)
```

#### `create_item(item_data: Dict[str, Any]) -> Item`

Create a new item in the Zotero library.

**Parameters:**
- `item_data` (Dict[str, Any]): A dictionary containing the item's data.

**Returns:**
- The created Item object.

**Example:**
```python
new_item_data = {
    "itemType": "book",
    "title": "My New Book",
    "creators": [
        {
            "creatorType": "author",
            "firstName": "Jane",
            "lastName": "Doe"
        }
    ],
    "date": "2024",
    "abstractNote": "This is a test book."
}
created_item = client.create_item(new_item_data)
print(f"Created item: {created_item.title} (Key: {created_item.key})")
```

#### `update_item(item_id: str, item_data: Dict[str, Any], if_unmodified_since_version: Optional[int] = None) -> Item`

Update an existing item in the Zotero library.

**Parameters:**
- `item_id` (str): The ID of the item to update.
- `item_data` (Dict[str, Any]): A dictionary containing the updated item's data.
- `if_unmodified_since_version` (int, optional): The version of the item to ensure no conflicts.

**Returns:**
- The updated Item object.

**Example:**
```python
item_to_update = client.get_item('ABC123XYZ')
updated_data = {"title": "Updated Book Title"}
updated_item = client.update_item(item_to_update.key, updated_data, item_to_update.version)
print(f"Updated item: {updated_item.title} (Version: {updated_item.version})")
```

#### `delete_item(item_id: str, if_unmodified_since_version: Optional[int] = None) -> None`

Delete an item from the Zotero library.

**Parameters:**
- `item_id` (str): The ID of the item to delete.
- `if_unmodified_since_version` (int, optional): The version of the item to ensure no conflicts.

**Returns:**
- None

**Example:**
```python
item_to_delete = client.get_item('ABC123XYZ')
client.delete_item(item_to_delete.key, item_to_delete.version)
print(f"Deleted item with key: {item_to_delete.key}")
```

#### `get_attachments(item_id: Optional[str] = None, limit: Optional[int] = None) -> List[Item]`

Retrieve attachment items from the Zotero library.

**Parameters:**
- `item_id` (str, optional): The ID of the parent item to retrieve attachments for.
- `limit` (int, optional): Maximum number of attachments to retrieve.

**Returns:**
- List of Item objects (representing attachments).

**Example:**
```python
attachments = client.get_attachments(limit=5)
for attachment in attachments:
    print(f"Attachment: {attachment.title} (Parent: {attachment.parent_item})")

item_attachments = client.get_attachments(item_id='PARENTITEM123')
for attachment in item_attachments:
    print(f"Attachment: {attachment.title}")
```

#### `upload_attachment(parent_item_id: str, file_path: str, title: Optional[str] = None) -> Item`

Upload a file as an an attachment to a Zotero item.

**Parameters:**
- `parent_item_id` (str): The ID of the parent item to attach the file to.
- `file_path` (str): The path to the file to upload.
- `title` (str, optional): The title for the attachment item. If not provided, uses the filename.

**Returns:**
- The created Item object representing the attachment.

**Example:**
```python
# Assuming 'my_document.pdf' exists in the current directory
# and 'PARENTITEM123' is a valid item ID
attachment = client.upload_attachment('PARENTITEM123', 'my_document.pdf', title='My Uploaded Document')
print(f"Uploaded attachment: {attachment.title} (Key: {attachment.key})")
```

#### `download_attachment(attachment_id: str, output_path: str) -> str`

Download the file content of an attachment.

**Parameters:**
- `attachment_id` (str): The ID of the attachment item to download.
- `output_path` (str): The path where the downloaded file should be saved.

**Returns:**
- The path to the downloaded file.

**Example:**
```python
# Assuming 'ATTACHMENT123' is a valid attachment ID
downloaded_file = client.download_attachment('ATTACHMENT123', './downloaded_file.pdf')
print(f"Downloaded attachment to: {downloaded_file}")
```

#### `get_citations(item_ids: List[str], style: str, format: str = 'html', locale: Optional[str] = None) -> str`

Generate formatted citations or a bibliography for a list of item IDs.

**Parameters:**
- `item_ids` (List[str]): A list of Zotero item keys for which to generate citations.
- `style` (str): The CSL style to use (e.g., 'apa', 'chicago-fullnote-bibliography').
- `format` (str, optional): The output format ('html' or 'text'). Defaults to 'html'.
- `locale` (str, optional): The bibliography locale (e.g., 'en-US').

**Returns:**
- A string containing the formatted citations or bibliography.

**Example:**
```python
citations = client.get_citations(['ITEM123', 'ITEM456'], style='apa', format='text')
print(citations)
```

#### `get_attachment_template(item_id: Optional[str] = None) -> Dict[str, Any]:

#### `get_collections() -> List[Collection]`

Retrieve collections from the Zotero library.

**Returns:**
- List of Collection objects

**Example:**
```python
collections = client.get_collections()
for collection in collections:
    print(collection.name)
```

#### `create_collection(collection_data: Dict[str, Any]) -> Collection`

Create a new collection in the Zotero library.

**Parameters:**
- `collection_data` (Dict[str, Any]): A dictionary containing the collection's data.

**Returns:**
- The created Collection object.

**Example:**
```python
new_collection_data = {"name": "My New Collection"}
created_collection = client.create_collection(new_collection_data)
print(f"Created collection: {created_collection.name} (Key: {created_collection.key})")
```

#### `update_collection(collection_id: str, collection_data: Dict[str, Any], if_unmodified_since_version: Optional[int] = None) -> Collection`

Update an existing collection in the Zotero library.

**Parameters:**
- `collection_id` (str): The ID of the collection to update.
- `collection_data` (Dict[str, Any]): A dictionary containing the updated collection's data.
- `if_unmodified_since_version` (int, optional): The version of the collection to ensure no conflicts.

**Returns:**
- The updated Collection object.

**Example:**
```python
collection_to_update = client.get_collections()[0] # Assuming at least one collection exists
updated_data = {"name": "Renamed Collection"}
updated_collection = client.update_collection(collection_to_update.key, updated_data, collection_to_update.version)
print(f"Updated collection: {updated_collection.name} (Version: {updated_collection.version})")
```

#### `delete_collection(collection_id: str, if_unmodified_since_version: Optional[int] = None) -> None`

Delete a collection from the Zotero library.

**Parameters:**
- `collection_id` (str): The ID of the collection to delete.
- `if_unmodified_since_version` (int, optional): The version of the collection to ensure no conflicts.

**Returns:**
- None

**Example:**
```python
collection_to_delete = client.get_collections()[0] # Assuming at least one collection exists
client.delete_collection(collection_to_delete.key, collection_to_delete.version)
print(f"Deleted collection with key: {collection_to_delete.key}")
```

#### `get_tags(item_id: Optional[str] = None) -> List[Tag]`

Retrieve tags from the Zotero library. Can be filtered by item.

**Parameters:**
- `item_id` (str, optional): The ID of the item to retrieve tags for.

**Returns:**
- List of Tag objects.

**Example:**
```python
all_tags = client.get_tags()
print(f"All tags: {[tag.tag for tag in all_tags]}")

item_tags = client.get_tags(item_id='ABC123XYZ')
print(f"Tags for item ABC123XYZ: {[tag.tag for tag in item_tags]}")
```

#### `add_tags_to_item(item_id: str, tags: List[str], if_unmodified_since_version: Optional[int] = None) -> None`

Add tags to a specific item.

**Parameters:**
- `item_id` (str): The ID of the item to add tags to.
- `tags` (List[str]): A list of tag names to add.
- `if_unmodified_since_version` (int, optional): The version of the item to ensure no conflicts.

**Returns:**
- None

**Example:**
```python
item_to_tag = client.get_item('ABC123XYZ')
client.add_tags_to_item(item_to_tag.key, ["new-tag", "another-tag"], item_to_tag.version)
print(f"Added tags to item: {item_to_tag.key}")
```

#### `remove_tags_from_item(item_id: str, tags: List[str], if_unmodified_since_version: Optional[int] = None) -> None`

Remove tags from a specific item.

**Parameters:**
- `item_id` (str): The ID of the item to remove tags from.
- `tags` (List[str]): A list of tag names to remove.
- `if_unmodified_since_version` (int, optional): The version of the item to ensure no conflicts.

**Returns:**
- None

**Example:**
```python
item_to_untag = client.get_item('ABC123XYZ')
client.remove_tags_from_item(item_to_untag.key, ["old-tag"], item_to_untag.version)
print(f"Removed tags from item: {item_to_untag.key}")
```

## CLI Commands

### `cl items`

List items from your Zotero library with optional search filters.

**Options:**
- `--limit` (int): Maximum number of items to retrieve.
- `--query` (str): Search query for quick search across titles and creator fields.
- `--qmode` (str): Query mode for `--query` parameter (e.g., "everything" for full-text search).
- `--item-type` (str): Filter by item type (e.g., "book", "journalArticle").
- `--tag` (str): Filter by tag (supports boolean search syntax).
- `--include-trashed`: Include trashed items in the results.

**Examples:**
```bash
cl items
cl items --limit 5
cl items --query "biology" --qmode "everything"
cl items --item-type "journalArticle" --tag "genetics"
cl items --include-trashed
```

### `cl collections`

List collections from your Zotero library.

**Example:**
```bash
cl collections
```

### `cl tags`

List tags from your Zotero library.

**Options:**
- `--item-id`: Filter tags by a specific item ID.

**Examples:**
```bash
cl tags
cl tags --item-id ABC123XYZ
```

### `cl configure`

Interactively configure Zotero API credentials.

**Examples:**
```bash
cl configure
```

### `cl attachments`

Manage Zotero attachments.

**Commands:**
- `list`: List attachments from your Zotero library.
- `upload`: Upload a file as an attachment to an item.
- `download`: Download an attachment file.

**Options for `list`:**
- `--item-id` (str, optional): Filter attachments by a specific parent item ID.
- `--limit` (int, optional): Maximum number of attachments to retrieve.

**Examples for `list`:**
```bash
cl attachments list
cl attachments list --item-id PARENTITEM123
cl attachments list --limit 5
```

**Options for `upload`:**
- `--parent-item-id` (str, required): The ID of the parent item to attach the file to.
- `--file-path` (str, required): The path to the file to upload.
- `--title` (str, optional): The title for the attachment item (defaults to filename).

**Examples for `upload`:**
```bash
# Assuming 'my_document.pdf' exists in the current directory
cl attachments upload --parent-item-id PARENTITEM123 --file-path my_document.pdf --title "My Research Notes"
cl attachments upload --parent-item-id ANOTHERITEM456 --file-path another_file.txt
```

**Options for `download`:**
- `--attachment-id` (str, required): The ID of the attachment item to download.
- `--output-path` (str, required): The path where the downloaded file should be saved.

**Examples for `download`:**
```bash
cl attachments download --attachment-id ATTACHMENT123 --output-path ./downloaded_file.pdf
```

### `cl citations`

Generate citations and bibliographies.

**Commands:**
- `generate`: Generate formatted citations or bibliography.

**Options for `generate`:**
- `--item-ids` (str, required): Comma-separated list of Zotero item keys (e.g., "ITEM1,ITEM2").
- `--style` (str, required): The CSL style to use (e.g., "apa", "chicago-fullnote-bibliography").
- `--format` (str, optional): The output format ("html" or "text"). Defaults to "html".
- `--locale` (str, optional): The bibliography locale (e.g., "en-US").

**Examples for `generate`:**
```bash
cl citations generate --item-ids ITEM123,ITEM456 --style apa --format text
cl citations generate --item-ids ITEM789 --style "chicago-fullnote-bibliography" --locale fr-FR
```

## Response Format

### Collection Response

```json
{
  "key": "COLLECTION_KEY",
  "version": 456,
  "library": {...},
  "links": {...},
  "meta": {...},
  "data": {
    "key": "COLLECTION_KEY",
    "version": 456,
    "name": "My Collection",
    "parentCollection": false
  }
}
```

### Tag Response

```json
{
  "tag": "example-tag",
  "type": 1
}
```
