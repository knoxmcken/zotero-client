"""Command-line interface for Zotero client."""

import argparse
import os
import sys
import json
from dotenv import load_dotenv, set_key
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


def configure_cli(args):
    """
    Interactively configure Zotero API key and user ID.
    """
    print("--- Zotero Client Configuration ---")
    api_key = None
    user_id = None
    try:
        api_key = input("Enter your Zotero API Key: ")
        user_id = input("Enter your Zotero User ID: ")
    except KeyboardInterrupt:
        print("\nConfiguration cancelled.")
        sys.exit(0)

    if api_key is not None and user_id is not None:
        env_path = '.env'
        set_key(env_path, 'ZOTERO_API_KEY', api_key)
        set_key(env_path, 'ZOTERO_USER_ID', user_id)

        print(f"Configuration saved to {env_path}")
        print("Please restart your shell or run 'load_dotenv()' if you are in an interactive session.")


def list_items(args):
    """
    List items from Zotero library with optional search filters.
    """
    api_key, user_id = load_config()
    client = ZoteroClient(api_key, user_id)
    
    items = client.get_items(
        limit=args.limit,
        q=args.query,
        qmode=args.qmode,
        item_type=args.item_type,
        tag=args.tag,
        include_trashed=args.include_trashed
    )
    
    for item in items:
        print(f"[{item.item_type}] {item.title}")


def create_item_cli(args):
    """
    Create a new item in the Zotero library via CLI.
    """
    api_key, user_id = load_config()
    client = ZoteroClient(api_key, user_id)
    
    try:
        item_data = json.loads(args.data)
        created_item = client.create_item(item_data)
        print(f"Successfully created item: {created_item.title} (Key: {created_item.key})")
    except json.JSONDecodeError:
        print("Error: Invalid JSON data provided for item creation.")
        sys.exit(1)
    except Exception as e:
        print(f"Error creating item: {e}")
        sys.exit(1)


def update_item_cli(args):
    """
    Update an existing item in the Zotero library via CLI.
    """
    api_key, user_id = load_config()
    client = ZoteroClient(api_key, user_id)

    try:
        item_data = json.loads(args.data)
        updated_item = client.update_item(args.item_id, item_data, args.version)
        print(f"Successfully updated item: {updated_item.title} (Key: {updated_item.key}, Version: {updated_item.version})")
    except json.JSONDecodeError:
        print("Error: Invalid JSON data provided for item update.")
        sys.exit(1)
    except Exception as e:
        print(f"Error updating item: {e}")
        sys.exit(1)


def delete_item_cli(args):
    """
    Delete an item from the Zotero library via CLI.
    """
    api_key, user_id = load_config()
    client = ZoteroClient(api_key, user_id)

    try:
        client.delete_item(args.item_id, args.version)
        print(f"Successfully deleted item with key: {args.item_id}")
    except Exception as e:
        print(f"Error deleting item: {e}")
        sys.exit(1)


def list_attachments(args):
    """
    List attachments from Zotero library, optionally filtered by parent item.
    """
    api_key, user_id = load_config()
    client = ZoteroClient(api_key, user_id)

    attachments = client.get_attachments(item_id=args.item_id, limit=args.limit)

    for attachment in attachments:
        parent_item_key = attachment.parent_item if hasattr(attachment, 'parent_item') else 'N/A'
        print(f"[Attachment] {attachment.title} (Key: {attachment.key}, Parent: {parent_item_key})")


def list_collections(args):
    """
    List collections from Zotero library."""
    api_key, user_id = load_config()
    client = ZoteroClient(api_key, user_id)
    
    collections = client.get_collections()
    
    for collection in collections:
        print(f"{collection.name} (key: {collection.key})")


def create_collection_cli(args):
    """
    Create a new collection in the Zotero library via CLI.
    """
    api_key, user_id = load_config()
    client = ZoteroClient(api_key, user_id)

    try:
        collection_data = json.loads(args.data)
        created_collection = client.create_collection(collection_data)
        print(f"Successfully created collection: {created_collection.name} (Key: {created_collection.key})")
    except json.JSONDecodeError:
        print("Error: Invalid JSON data provided for collection creation.")
        sys.exit(1)
    except Exception as e:
        print(f"Error creating collection: {e}")
        sys.exit(1)


def update_collection_cli(args):
    """
    Update an existing collection in the Zotero library via CLI.
    """
    api_key, user_id = load_config()
    client = ZoteroClient(api_key, user_id)

    try:
        collection_data = json.loads(args.data)
        updated_collection = client.update_collection(args.collection_id, collection_data, args.version)
        print(f"Successfully updated collection: {updated_collection.name} (Key: {updated_collection.key}, Version: {updated_collection.version})")
    except json.JSONDecodeError:
        print("Error: Invalid JSON data provided for collection update.")
        sys.exit(1)
    except Exception as e:
        print(f"Error updating collection: {e}")
        sys.exit(1)


def delete_collection_cli(args):
    """
    Delete a collection from the Zotero library via CLI.
    """
    api_key, user_id = load_config()
    client = ZoteroClient(api_key, user_id)

    try:
        client.delete_collection(args.collection_id, args.version)
        print(f"Successfully deleted collection with key: {args.collection_id}")
    except Exception as e:
        print(f"Error deleting collection: {e}")
        sys.exit(1)


def list_tags(args):
    """
    List tags from Zotero library.
    """
    api_key, user_id = load_config()
    client = ZoteroClient(api_key, user_id)

    tags = client.get_tags(item_id=args.item_id)

    for tag in tags:
        print(f"{tag.tag} (Type: {'Manual' if tag.type == 1 else 'Automatic'})")


def add_tags_to_item_cli(args):
    """
    Add tags to a specific item via CLI.
    """
    api_key, user_id = load_config()
    client = ZoteroClient(api_key, user_id)

    try:
        tags_list = args.tags.split(',')
        client.add_tags_to_item(args.item_id, tags_list, args.version)
        print(f"Successfully added tags {tags_list} to item: {args.item_id}")
    except Exception as e:
        print(f"Error adding tags to item: {e}")
        sys.exit(1)


def remove_tags_from_item_cli(args):
    """
    Remove tags from a specific item via CLI.
    """
    api_key, user_id = load_config()
    client = ZoteroClient(api_key, user_id)

    try:
        tags_list = args.tags.split(',')
        client.remove_tags_from_item(args.item_id, tags_list, args.version)
        print(f"Successfully removed tags {tags_list} from item: {args.item_id}")
    except Exception as e:
        print(f"Error removing tags from item: {e}")
        sys.exit(1)


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description='Zotero API Client - Interact with your Zotero library'
    )
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # List items command
    items_parser = subparsers.add_parser('items', help='Manage Zotero items')
    items_subparsers = items_parser.add_subparsers(dest='item_command', help='Item commands')

    # List items sub-command
    list_items_parser = items_subparsers.add_parser('list', help='List items from library')
    list_items_parser.add_argument(
        '--limit',
        type=int,
        default=None,
        help='Maximum number of items to retrieve'
    )
    list_items_parser.set_defaults(func=list_items)

    # Create item sub-command
    create_item_parser = items_subparsers.add_parser('create', help='Create a new item')
    create_item_parser.add_argument(
        '--data',
        type=str,
        required=True,
        help='JSON string of item data (e.g., "{\"itemType\": \"book\", \"title\": \"My Book\"}")'
    )
    create_item_parser.set_defaults(func=create_item_cli)

    # Update item sub-command
    update_item_parser = items_subparsers.add_parser('update', help='Update an existing item')
    update_item_parser.add_argument(
        '--item-id',
        type=str,
        required=True,
        help='The key of the item to update'
    )
    update_item_parser.add_argument(
        '--data',
        type=str,
        required=True,
        help='JSON string of updated item data'
    )
    update_item_parser.add_argument(
        '--version',
        type=int,
        default=None,
        help='The version of the item to ensure no conflicts'
    )
    update_item_parser.set_defaults(func=update_item_cli)

    # Delete item sub-command
    delete_item_parser = items_subparsers.add_parser('delete', help='Delete an item')
    delete_item_parser.add_argument(
        '--item-id',
        type=str,
        required=True,
        help='The key of the item to delete'
    )
    delete_item_parser.add_argument(
        '--version',
        type=int,
        default=None,
        help='The version of the item to ensure no conflicts'
    )
    delete_item_parser.set_defaults(func=delete_item_cli)
    
    # List collections command
    collections_parser = subparsers.add_parser('collections', help='Manage Zotero collections')
    collections_subparsers = collections_parser.add_subparsers(dest='collection_command', help='Collection commands')

    # List collections sub-command
    list_collections_parser = collections_subparsers.add_parser('list', help='List collections from library')
    list_collections_parser.set_defaults(func=list_collections)

    # Create collection sub-command
    create_collection_parser = collections_subparsers.add_parser('create', help='Create a new collection')
    create_collection_parser.add_argument(
        '--data',
        type=str,
        required=True,
        help='JSON string of collection data (e.g., "{\"name\": \"My Collection\"}")'
    )
    create_collection_parser.set_defaults(func=create_collection_cli)

    # Update collection sub-command
    update_collection_parser = collections_subparsers.add_parser('update', help='Update an existing collection')
    update_collection_parser.add_argument(
        '--collection-id',
        type=str,
        required=True,
        help='The key of the collection to update'
    )
    update_collection_parser.add_argument(
        '--data',
        type=str,
        required=True,
        help='JSON string of updated collection data'
    )
    update_collection_parser.add_argument(
        '--version',
        type=int,
        default=None,
        help='The version of the collection to ensure no conflicts'
    )
    update_collection_parser.set_defaults(func=update_collection_cli)

    # Delete collection sub-command
    delete_collection_parser = collections_subparsers.add_parser('delete', help='Delete a collection')
    delete_collection_parser.add_argument(
        '--collection-id',
        type=str,
        required=True,
        help='The key of the collection to delete'
    )
    delete_collection_parser.add_argument(
        '--version',
        type=int,
        default=None,
        help='The version of the collection to ensure no conflicts'
    )
    delete_collection_parser.set_defaults(func=delete_collection_cli)

    # Tags command
    tags_parser = subparsers.add_parser('tags', help='Manage Zotero tags')
    tags_subparsers = tags_parser.add_subparsers(dest='tag_command', help='Tag commands')

    # List tags sub-command
    list_tags_parser = tags_subparsers.add_parser('list', help='List tags from library')
    list_tags_parser.add_argument(
        '--item-id',
        type=str,
        default=None,
        help='Optional: Filter tags by a specific item ID'
    )
    list_tags_parser.set_defaults(func=list_tags)

    # Add tags to item sub-command
    add_tags_parser = tags_subparsers.add_parser('add', help='Add tags to an item')
    add_tags_parser.add_argument(
        '--item-id',
        type=str,
        required=True,
        help='The key of the item to add tags to'
    )
    add_tags_parser.add_argument(
        '--tags',
        type=str,
        required=True,
        help='Comma-separated list of tags to add (e.g., "tag1,tag2")'
    )
    add_tags_parser.add_argument(
        '--version',
        type=int,
        default=None,
        help='The version of the item to ensure no conflicts'
    )
    add_tags_parser.set_defaults(func=add_tags_to_item_cli)

    # Remove tags from item sub-command
    remove_tags_parser = tags_subparsers.add_parser('remove', help='Remove tags from an item')
    remove_tags_parser.add_argument(
        '--item-id',
        type=str,
        required=True,
        help='The key of the item to remove tags from'
    )
    remove_tags_parser.add_argument(
        '--tags',
        type=str,
        required=True,
        help='Comma-separated list of tags to remove (e.g., "tag1,tag2")'
    )
    remove_tags_parser.add_argument(
        '--version',
        type=int,
        default=None,
        help='The version of the item to ensure no conflicts'
    )
    remove_tags_parser.set_defaults(func=remove_tags_from_item_cli)

    # Configure command
    configure_parser = subparsers.add_parser('configure', help='Interactively configure Zotero API credentials')
    configure_parser.set_defaults(func=configure_cli)

    # Attachments command
    attachments_parser = subparsers.add_parser('attachments', help='Manage Zotero attachments')
    attachments_subparsers = attachments_parser.add_subparsers(dest='attachment_command', help='Attachment commands')

    # List attachments sub-command
    list_attachments_parser = attachments_subparsers.add_parser('list', help='List attachments from library')
    list_attachments_parser.add_argument(
        '--item-id',
        type=str,
        default=None,
        help='Optional: Filter attachments by a specific parent item ID'
    )
    list_attachments_parser.add_argument(
        '--limit',
        type=int,
        default=None,
        help='Maximum number of attachments to retrieve'
    )
    list_attachments_parser.set_defaults(func=list_attachments)
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    if args.command == 'items' and not args.item_command:
        items_parser.print_help()
        sys.exit(1)
    
    if args.command == 'collections' and not args.collection_command:
        collections_parser.print_help()
        sys.exit(1)

    if args.command == 'tags' and not args.tag_command:
        tags_parser.print_help()
        sys.exit(1)

    if args.command == 'attachments' and not args.attachment_command:
        attachments_parser.print_help()
        sys.exit(1)
    
    args.func(args)
