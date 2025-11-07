"""Command-line interface for Zotero client."""

import argparse
import os
import sys
from dotenv import load_dotenv
from zotero_client.api.client import ZoteroClient


def load_config():
    """Load configuration from environment variables."""
    load_dotenv()
    api_key = os.getenv('ZOTERO_API_KEY')
    user_id = os.getenv('ZOTERO_USER_ID')
    
    if not api_key or not user_id:
        print("Error: ZOTERO_API_KEY and ZOTERO_USER_ID must be set in .env file")
        sys.exit(1)
    
    return api_key, user_id


def list_items(args):
    """List items from Zotero library."""
    api_key, user_id = load_config()
    client = ZoteroClient(api_key, user_id)
    
    items = client.get_items(limit=args.limit)
    
    for item in items:
        data = item.get('data', {})
        title = data.get('title', 'Untitled')
        item_type = data.get('itemType', 'unknown')
        print(f"[{item_type}] {title}")


def list_collections(args):
    """List collections from Zotero library."""
    api_key, user_id = load_config()
    client = ZoteroClient(api_key, user_id)
    
    collections = client.get_collections()
    
    for collection in collections:
        data = collection.get('data', {})
        name = data.get('name', 'Unnamed')
        key = data.get('key', '')
        print(f"{name} (key: {key})")


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description='Zotero API Client - Interact with your Zotero library'
    )
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # List items command
    items_parser = subparsers.add_parser('items', help='List items from library')
    items_parser.add_argument(
        '--limit',
        type=int,
        default=None,
        help='Maximum number of items to retrieve'
    )
    items_parser.set_defaults(func=list_items)
    
    # List collections command
    collections_parser = subparsers.add_parser('collections', help='List collections')
    collections_parser.set_defaults(func=list_collections)
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    args.func(args)


if __name__ == "__main__":
    main()
