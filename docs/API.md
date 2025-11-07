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

#### `get_items(limit: Optional[int] = None) -> List[Item]`

Retrieve items from the Zotero library.

**Parameters:**
- `limit` (int, optional): Maximum number of items to retrieve

**Returns:**
- List of Item objects

**Example:**
```python
items = client.get_items(limit=10)
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

## CLI Commands

### `cl items`

List items from your Zotero library.

**Options:**
- `--limit`: Maximum number of items to retrieve

**Examples:**
```bash
cl items
cl items --limit 5
```

### `cl collections`

List collections from your Zotero library.

**Example:**
```bash
cl collections
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
