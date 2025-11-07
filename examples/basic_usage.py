"""Basic usage example for Zotero API client."""

import os
from dotenv import load_dotenv
from zotero_client import ZoteroClient

# Load environment variables
load_dotenv()

# Initialize client
client = ZoteroClient(
    api_key=os.getenv('ZOTERO_API_KEY'),
    user_id=os.getenv('ZOTERO_USER_ID')
)

# Get and display items
print("Fetching items from Zotero library...\n")
items = client.get_items(limit=5)

for item in items:
    data = item.get('data', {})
    title = data.get('title', 'Untitled')
    item_type = data.get('itemType', 'unknown')
    creators = data.get('creators', [])
    
    print(f"Title: {title}")
    print(f"Type: {item_type}")
    
    if creators:
        author_names = [
            f"{c.get('firstName', '')} {c.get('lastName', '')}".strip()
            for c in creators
        ]
        print(f"Authors: {', '.join(author_names)}")
    
    print("-" * 80)

# Get and display collections
print("\nFetching collections...\n")
collections = client.get_collections()

for collection in collections:
    data = collection.get('data', {})
    name = data.get('name', 'Unnamed')
    print(f"Collection: {name}")
