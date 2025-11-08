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
    openai_api_key = os.getenv('OPENAI_API_KEY')
    
    if not api_key or not user_id:
        print("Error: ZOTERO_API_KEY and ZOTERO_USER_ID must be set in .env file")
        sys.exit(1)
    
    return api_key, user_id, openai_api_key


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
    api_key, user_id, openai_api_key = load_config()
    client = ZoteroClient(api_key, user_id, openai_api_key=openai_api_key)
    
    items = client.get_items(
        limit=args.limit,
        q=args.query,
        qmode=args.qmode,
        item_type=getattr(args, 'item_type', None),
        tag=args.tag,
        include_trashed=getattr(args, 'include_trashed', None)
    )
    
    for item in items:
        print(f"[{item.item_type}] {item.title}")


def create_item_cli(args):
    """
    Create a new item in the Zotero library via CLI.
    """
    api_key, user_id, openai_api_key = load_config()
    client = ZoteroClient(api_key, user_id, openai_api_key=openai_api_key)
    
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
    api_key, user_id, openai_api_key = load_config()
    client = ZoteroClient(api_key, user_id, openai_api_key=openai_api_key)

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
    api_key, user_id, openai_api_key = load_config()
    client = ZoteroClient(api_key, user_id, openai_api_key=openai_api_key)

    try:
        client.delete_item(args.item_id, args.version)
        print(f"Successfully deleted item with key: {args.item_id}")
    except Exception as e:
        print(f"Error deleting item: {e}")
        sys.exit(1)


def summarize_item_cli(args):
    """
    Summarize the content of a Zotero item using OpenAI via CLI.
    """
    api_key, user_id, openai_api_key = load_config()
    client = ZoteroClient(api_key, user_id, openai_api_key=openai_api_key)

    if not openai_api_key:
        print("Error: OPENAI_API_KEY is not set in .env file. Please configure it using 'cl configure'.")
        sys.exit(1)

    try:
        summary = client.summarize_item_content(args.item_id, args.prompt)
        print(f"Summary for item {args.item_id}:\n{summary}")
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except RuntimeError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        sys.exit(1)


def find_duplicates_cli(args):
    """
    Find potential duplicate items in the Zotero library via CLI.
    """
    api_key, user_id, openai_api_key = load_config()
    client = ZoteroClient(api_key, user_id, openai_api_key=openai_api_key)

    try:
        duplicates = client.find_duplicates()
        if duplicates:
            print("Potential duplicate items found:")
            for key, items in duplicates.items():
                print(f"\nGroup: {key}")
                for item in items:
                    print(f"  - [{item.item_type}] {item.title} (Key: {item.key}, Date: {item.date})")
        else:
            print("No potential duplicate items found.")
    except Exception as e:
        print(f"Error finding duplicates: {e}")
        sys.exit(1)


def export_items_cli(args):
    """
    Export items from the Zotero library to a specified format via CLI.
    """
    api_key, user_id, openai_api_key = load_config()
    client = ZoteroClient(api_key, user_id, openai_api_key=openai_api_key)

    try:
        exported_data = client.export_items(format=args.format)
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(exported_data)
            print(f"Successfully exported items to {args.output}")
        else:
            print(exported_data)
    except Exception as e:
        print(f"Error exporting items: {e}")
        sys.exit(1)


def generate_citations_cli(args):
    """
    Generate formatted citations or a bibliography for Zotero items via CLI.
    """
    api_key, user_id, openai_api_key = load_config()
    client = ZoteroClient(api_key, user_id, openai_api_key=openai_api_key)

    try:
        item_ids = args.item_ids.split(',')
        citations = client.get_citations(item_ids, args.style, args.format, args.locale)
        print(citations)
    except Exception as e:
        print(f"Error generating citations: {e}")
        sys.exit(1)


def download_attachment_cli(args):
    """
    Download an attachment file from Zotero via CLI.
    """
    api_key, user_id, openai_api_key = load_config()
    client = ZoteroClient(api_key, user_id, openai_api_key=openai_api_key)

    try:
        downloaded_path = client.download_attachment(args.attachment_id, args.output_path)
        print(f"Successfully downloaded attachment {args.attachment_id} to: {downloaded_path}")
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error downloading attachment: {e}")
        sys.exit(1)


def upload_attachment_cli(args):
    """
    Upload a file as an attachment to a Zotero item via CLI.
    """
    api_key, user_id, openai_api_key = load_config()
    client = ZoteroClient(api_key, user_id, openai_api_key=openai_api_key)

    try:
        uploaded_attachment = client.upload_attachment(args.parent_item_id, args.file_path, args.title)
        print(f"Successfully uploaded attachment: {uploaded_attachment.title} (Key: {uploaded_attachment.key})")
    except FileNotFoundError:
        print(f"Error: File not found at {args.file_path}")
        sys.exit(1)
    except Exception as e:
        print(f"Error uploading attachment: {e}")
        sys.exit(1)


def list_attachments(args):
    """
    List attachments from Zotero library, optionally filtered by parent item.
    """
    api_key, user_id, openai_api_key = load_config()
    client = ZoteroClient(api_key, user_id, openai_api_key=openai_api_key)

    attachments = client.get_attachments(item_id=args.item_id, limit=args.limit)

    for attachment in attachments:
        parent_item_key = attachment.parent_item if hasattr(attachment, 'parent_item') else 'N/A'
        print(f"[Attachment] {attachment.title} (Key: {attachment.key}, Parent: {parent_item_key})")


def list_collections(args):
    """
    List collections from Zotero library."""
    api_key, user_id, openai_api_key = load_config()
    client = ZoteroClient(api_key, user_id, openai_api_key=openai_api_key)
    
    collections = client.get_collections()
    
    for collection in collections:
        print(f"{collection.name} (key: {collection.key})")


def create_collection_cli(args):
    """
    Create a new collection in the Zotero library via CLI.
    """
    api_key, user_id, openai_api_key = load_config()
    client = ZoteroClient(api_key, user_id, openai_api_key=openai_api_key)

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
    api_key, user_id, openai_api_key = load_config()
    client = ZoteroClient(api_key, user_id, openai_api_key=openai_api_key)

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
    api_key, user_id, openai_api_key = load_config()
    client = ZoteroClient(api_key, user_id, openai_api_key=openai_api_key)

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
    api_key, user_id, openai_api_key = load_config()
    client = ZoteroClient(api_key, user_id, openai_api_key=openai_api_key)

    tags = client.get_tags(item_id=args.item_id)

    for tag in tags:
        print(f"{tag.tag} (Type: {'Manual' if tag.type == 1 else 'Automatic'})")


def add_tags_to_item_cli(args):
    """
    Add tags to a specific item via CLI.
    """
    api_key, user_id, openai_api_key = load_config()
    client = ZoteroClient(api_key, user_id, openai_api_key=openai_api_key)

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
    api_key, user_id, openai_api_key = load_config()
    client = ZoteroClient(api_key, user_id, openai_api_key=openai_api_key)

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
    list_items_parser.add_argument(
        '--query',
        type=str,
        default=None,
        help='Search query for quick search across titles and creator fields'
    )
    list_items_parser.add_argument(
        '--qmode',
        type=str,
        default=None,
        help='Query mode for search (e.g., "everything" for full-text search)'
    )
    list_items_parser.add_argument(
        '--item-type',
        type=str,
        default=None,
        help='Filter by item type (e.g., "book", "journalArticle")'
    )
    list_items_parser.add_argument(
        '--tag',
        type=str,
        default=None,
        help='Filter by tag'
    )
    list_items_parser.add_argument(
        '--include-trashed',
        action='store_true',
        help='Include trashed items in the results'
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

    # Upload attachment sub-command
    upload_attachment_parser = attachments_subparsers.add_parser('upload', help='Upload a file as an attachment to an item')
    upload_attachment_parser.add_argument(
        '--parent-item-id',
        type=str,
        required=True,
        help='The ID of the parent item to attach the file to'
    )
    upload_attachment_parser.add_argument(
        '--file-path',
        type=str,
        required=True,
        help='The path to the file to upload'
    )
    upload_attachment_parser.add_argument(
        '--title',
        type=str,
        default=None,
        help='Optional: The title for the attachment item (defaults to filename)'
    )
    # Download attachment sub-command
    download_attachment_parser = attachments_subparsers.add_parser('download', help='Download an attachment file')
    download_attachment_parser.add_argument(
        '--attachment-id',
        type=str,
        required=True,
        help='The ID of the attachment item to download'
    )
    download_attachment_parser.add_argument(
        '--output-path',
        type=str,
        required=True,
        help='The path where the downloaded file should be saved'
    )
    download_attachment_parser.set_defaults(func=download_attachment_cli)

    # Citations command
    citations_parser = subparsers.add_parser('citations', help='Generate citations and bibliographies')
    citations_subparsers = citations_parser.add_subparsers(dest='citation_command', help='Citation commands')

    # Generate citations sub-command
    generate_citations_parser = citations_subparsers.add_parser('generate', help='Generate formatted citations or bibliography')
    generate_citations_parser.add_argument(
        '--item-ids',
        type=str,
        required=True,
        help='Comma-separated list of Zotero item keys (e.g., "ITEM1,ITEM2")'
    )
    generate_citations_parser.add_argument(
        '--style',
        type=str,
        required=True,
        help='The CSL style to use (e.g., "apa", "chicago-fullnote-bibliography")'
    )
    generate_citations_parser.add_argument(
        '--format',
        type=str,
        default='html',
        choices=['html', 'text'],
        help='The output format ("html" or "text"). Defaults to "html".'
    )
    generate_citations_parser.add_argument(
        '--locale',
        type=str,
        default=None,
        help='Optional: The bibliography locale (e.g., "en-US")'
    )
    generate_citations_parser.set_defaults(func=generate_citations_cli)

    # AI command
    ai_parser = subparsers.add_parser('ai', help='AI-powered features')
    ai_subparsers = ai_parser.add_subparsers(dest='ai_command', help='AI commands')

    # Summarize item sub-command
    summarize_item_parser = ai_subparsers.add_parser('summarize', help='Summarize Zotero item content using OpenAI')
    summarize_item_parser.add_argument(
        '--item-id',
        type=str,
        required=True,
        help='The ID of the Zotero item to summarize'
    )
    summarize_item_parser.add_argument(
        '--prompt',
        type=str,
        default="Summarize the following text:",
        help='Optional: Custom prompt for the OpenAI model'
    )
    summarize_item_parser.set_defaults(func=summarize_item_cli)

    # Duplicates command
    duplicates_parser = subparsers.add_parser('duplicates', help='Manage duplicate items')
    duplicates_subparsers = duplicates_parser.add_subparsers(dest='duplicates_command', help='Duplicate commands')

    # Find duplicates sub-command
    find_duplicates_parser = duplicates_subparsers.add_parser('find', help='Find potential duplicate items')
    find_duplicates_parser.set_defaults(func=find_duplicates_cli)

    # Export command
    export_parser = subparsers.add_parser('export', help='Export items from the library')
    export_parser.add_argument(
        '--format',
        type=str,
        default='bibtex',
        choices=['bibtex', 'csv'],
        help='The export format ("bibtex" or "csv"). Defaults to "bibtex".'
    )
    export_parser.add_argument(
        '--output',
        type=str,
        default=None,
        help='Optional: The path to the output file.'
    )
    export_parser.set_defaults(func=export_items_cli)
    
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

    if args.command == 'citations' and not args.citation_command:
        citations_parser.print_help()
        sys.exit(1)

    if args.command == 'ai' and not args.ai_command:
        ai_parser.print_help()
        sys.exit(1)

    if args.command == 'duplicates' and not args.duplicates_command:
        duplicates_parser.print_help()
        sys.exit(1)
    
    args.func(args)


if __name__ == '__main__':
    main()

