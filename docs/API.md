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
