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

#### `get_items(limit: Optional[int] = None) -> List[Dict]`

Retrieve items from the Zotero library.

**Parameters:**
- `limit` (int, optional): Maximum number of items to retrieve

**Returns:**
- List of item dictionaries

**Example:**
```python
items = client.get_items(limit=10)
for item in items:
    print(item['data']['title'])
```

#### `get_item(item_id: str) -> Dict`

Retrieve a specific item by ID.

**Parameters:**
- `item_id` (str): The item ID

**Returns:**
- Item dictionary

**Example:**
```python
item = client.get_item('ABC123XYZ')
print(item['data']['title'])
```

#### `get_collections() -> List[Dict]`

Retrieve collections from the Zotero library.

**Returns:**
- List of collection dictionaries

**Example:**
```python
collections = client.get_collections()
for collection in collections:
    print(collection['data']['name'])
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

### Item Response

```json
{
  "key": "ITEM_KEY",
  "version": 123,
  "library": {...},
  "links": {...},
  "meta": {...},
  "data": {
    "key": "ITEM_KEY",
    "version": 123,
    "itemType": "journalArticle",
    "title": "Article Title",
    "creators": [
      {
        "creatorType": "author",
        "firstName": "John",
        "lastName": "Doe"
      }
    ],
    "date": "2023",
    "url": "https://example.com"
  }
}
```

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
