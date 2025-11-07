"""Zotero API client implementation."""

import requests
from typing import List, Dict, Optional, Any
import os
from zotero_client.models.item import Item
from zotero_client.models.collection import Collection
from zotero_client.models.tag import Tag


class ZoteroClient:
    """Client for interacting with the Zotero API."""
    
    BASE_URL = 'https://api.zotero.org'
    
    def __init__(self, api_key: str, user_id: str, library_type: str = 'users'):
        """
        Initialize the Zotero client.
        
        Args:
            api_key: Zotero API key
            user_id: Zotero user ID
            library_type: Type of library ('users' or 'groups')
        """
        self.api_key = api_key
        self.user_id = user_id
        self.library_type = library_type
        self.headers = {'Zotero-API-Key': self.api_key}
    
    def get_items(self, limit: Optional[int] = None, q: Optional[str] = None, qmode: Optional[str] = None, item_type: Optional[str] = None, tag: Optional[str] = None, include_trashed: Optional[bool] = None) -> List[Item]:
        """
        Retrieve items from the Zotero library with advanced search capabilities.
        
        Args:
            limit: Maximum number of items to retrieve.
            q: Search query for quick search across titles and creator fields.
            qmode: Query mode for 'q' parameter (e.g., 'everything' for full-text search).
            item_type: Filter by item type (e.g., 'book', 'journalArticle').
            tag: Filter by tag (supports boolean search syntax).
            include_trashed: If True, include trashed items in the results.
            
        Returns:
            List of Item objects
        """
        url = f'{self.BASE_URL}/{self.library_type}/{self.user_id}/items'
        params = {}
        if limit:
            params['limit'] = limit
        if q:
            params['q'] = q
        if qmode:
            params['qmode'] = qmode
        if item_type:
            params['itemType'] = item_type
        if tag:
            params['tag'] = tag
        if include_trashed:
            params['includeTrashed'] = 1
            
        response = requests.get(url, headers=self.headers, params=params)
        response.raise_for_status()
        return [Item.from_api_response(item_data) for item_data in response.json()]
    
    def get_item(self, item_id: str) -> Item:
        """
        Retrieve a specific item by ID.
        
        Args:
            item_id: The item ID
            
        Returns:
            Item object
        """
        url = f'{self.BASE_URL}/{self.library_type}/{self.user_id}/items/{item_id}'
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        return Item.from_api_response(response.json())
    
    def create_item(self, item_data: Dict[str, Any]) -> Item:
        """
        Create a new item in the Zotero library.

        Args:
            item_data: A dictionary containing the item's data.

        Returns:
            The created Item object.
        """
        url = f'{self.BASE_URL}/{self.library_type}/{self.user_id}/items'
        response = requests.post(url, headers=self.headers, json=[item_data])
        response.raise_for_status()
        return Item.from_api_response(response.json()[0])

    def update_item(self, item_id: str, item_data: Dict[str, Any], if_unmodified_since_version: Optional[int] = None) -> Item:
        """
        Update an existing item in the Zotero library.

        Args:
            item_id: The ID of the item to update.
            item_data: A dictionary containing the updated item's data.
            if_unmodified_since_version: Optional. The version of the item to ensure no conflicts.

        Returns:
            The updated Item object.
        """
        url = f'{self.BASE_URL}/{self.library_type}/{self.user_id}/items/{item_id}'
        headers = self.headers.copy()
        if if_unmodified_since_version:
            headers['If-Unmodified-Since-Version'] = str(if_unmodified_since_version)
        response = requests.put(url, headers=headers, json=item_data)
        response.raise_for_status()
        return Item.from_api_response(response.json()[0])

    def delete_item(self, item_id: str, if_unmodified_since_version: Optional[int] = None) -> None:
        """
        Delete an item from the Zotero library.

        Args:
            item_id: The ID of the item to delete.
            if_unmodified_since_version: Optional. The version of the item to ensure no conflicts.
        """
        url = f'{self.BASE_URL}/{self.library_type}/{self.user_id}/items/{item_id}'
        headers = self.headers.copy()
        if if_unmodified_since_version:
            headers['If-Unmodified-Since-Version'] = str(if_unmodified_since_version)
        response = requests.delete(url, headers=headers)
        response.raise_for_status()
        return None
    
    def get_attachments(self, item_id: Optional[str] = None, limit: Optional[int] = None) -> List[Item]:
        """
        Retrieve attachment items from the Zotero library.

        Args:
            item_id: Optional. The ID of the parent item to retrieve attachments for.
            limit: Maximum number of attachments to retrieve.

        Returns:
            List of Item objects (representing attachments).
        """
        url = f'{self.BASE_URL}/{self.library_type}/{self.user_id}/items'
        params = {'itemType': 'attachment'}
        if item_id:
            params['parentItem'] = item_id
        if limit:
            params['limit'] = limit

        response = requests.get(url, headers=self.headers, params=params)
        response.raise_for_status()
        return [Item.from_api_response(item_data) for item_data in response.json()]

    def upload_attachment(self, parent_item_id: str, file_path: str, title: Optional[str] = None) -> Item:
        """
        Upload a file as an attachment to a Zotero item.

        Args:
            parent_item_id: The ID of the parent item to attach the file to.
            file_path: The path to the file to upload.
            title: Optional. The title for the attachment item. If not provided, uses the filename.

        Returns:
            The created Item object representing the attachment.
        """
        # 1. Get an attachment item template
        template = self.get_attachment_template(item_id=parent_item_id)

        # Prepare attachment metadata
        filename = os.path.basename(file_path)
        if title is None:
            title = filename

        template['title'] = title
        template['parentItem'] = parent_item_id
        template['filename'] = filename
        template['contentType'] = 'application/octet-stream' # Generic content type
        template['linkMode'] = 'imported_file'

        # 2. Create the attachment item
        create_url = f'{self.BASE_URL}/{self.library_type}/{self.user_id}/items'
        create_response = requests.post(create_url, headers=self.headers, json=[template])
        create_response.raise_for_status()
        created_attachment_data = create_response.json()[0]
        created_attachment_item = Item.from_api_response(created_attachment_data)

        # 3. Upload the file content
        file_upload_url = created_attachment_data['links']['file']['href']
        with open(file_path, 'rb') as f:
            file_content = f.read()

        upload_headers = self.headers.copy()
        upload_headers['Content-Type'] = 'application/octet-stream'
        upload_response = requests.put(file_upload_url, headers=upload_headers, data=file_content)
        upload_response.raise_for_status()

        return created_attachment_item

    def get_attachment_template(self, item_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Retrieve an attachment item template from the Zotero API.

        Args:
            item_id: Optional. The ID of the parent item for which to get the attachment template.

        Returns:
            A dictionary representing the attachment item template.
        """
        url = f'{self.BASE_URL}/{self.library_type}/{self.user_id}/items/new'
        params = {'itemType': 'attachment'}
        if item_id:
            params['linkMode'] = 'imported_url' # Or 'imported_file' depending on the use case
            params['parentItem'] = item_id

        response = requests.get(url, headers=self.headers, params=params)
        response.raise_for_status()
        return response.json()

    def get_collections(self) -> List[Collection]:
        """
        Retrieve collections from the Zotero library.
        
        Returns:
            List of Collection objects
        """
        url = f'{self.BASE_URL}/{self.library_type}/{self.user_id}/collections'
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        return [Collection.from_api_response(collection_data) for collection_data in response.json()]

    def create_collection(self, collection_data: Dict[str, Any]) -> Collection:
        """
        Create a new collection in the Zotero library.

        Args:
            collection_data: A dictionary containing the collection's data.

        Returns:
            The created Collection object.
        """
        url = f'{self.BASE_URL}/{self.library_type}/{self.user_id}/collections'
        response = requests.post(url, headers=self.headers, json=[collection_data])
        response.raise_for_status()
        return Collection.from_api_response(response.json()[0])

    def update_collection(self, collection_id: str, collection_data: Dict[str, Any], if_unmodified_since_version: Optional[int] = None) -> Collection:
        """
        Update an existing collection in the Zotero library.

        Args:
            collection_id: The ID of the collection to update.
            collection_data: A dictionary containing the updated collection's data.
            if_unmodified_since_version: Optional. The version of the collection to ensure no conflicts.

        Returns:
            The updated Collection object.
        """
        url = f'{self.BASE_URL}/{self.library_type}/{self.user_id}/collections/{collection_id}'
        headers = self.headers.copy()
        if if_unmodified_since_version:
            headers['If-Unmodified-Since-Version'] = str(if_unmodified_since_version)
        response = requests.put(url, headers=headers, json=collection_data)
        response.raise_for_status()
        return Collection.from_api_response(response.json()[0])

    def delete_collection(self, collection_id: str, if_unmodified_since_version: Optional[int] = None) -> None:
        """
        Delete a collection from the Zotero library.

        Args:
            collection_id: The ID of the collection to delete.
            if_unmodified_since_version: Optional. The version of the collection to ensure no conflicts.
        """
        url = f'{self.BASE_URL}/{self.library_type}/{self.user_id}/collections/{collection_id}'
        headers = self.headers.copy()
        if if_unmodified_since_version:
            headers['If-Unmodified-Since-Version'] = str(if_unmodified_since_version)
        response = requests.delete(url, headers=headers)
        response.raise_for_status()
        return None

    def get_tags(self, item_id: Optional[str] = None) -> List[Tag]:
        """
        Retrieve tags from the Zotero library. Can be filtered by item.

        Args:
            item_id: Optional. The ID of the item to retrieve tags for.

        Returns:
            List of Tag objects.
        """
        if item_id:
            url = f'{self.BASE_URL}/{self.library_type}/{self.user_id}/items/{item_id}/tags'
        else:
            url = f'{self.BASE_URL}/{self.library_type}/{self.user_id}/tags'
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        return [Tag.from_api_response(tag_data) for tag_data in response.json()]

    def add_tags_to_item(self, item_id: str, tags: List[str], if_unmodified_since_version: Optional[int] = None) -> None:
        """
        Add tags to a specific item.

        Args:
            item_id: The ID of the item to add tags to.
            tags: A list of tag names to add.
            if_unmodified_since_version: Optional. The version of the item to ensure no conflicts.
        """
        url = f'{self.BASE_URL}/{self.library_type}/{self.user_id}/items/{item_id}/tags'
        headers = self.headers.copy()
        if if_unmodified_since_version:
            headers['If-Unmodified-Since-Version'] = str(if_unmodified_since_version)
        tag_data = [{'tag': tag_name} for tag_name in tags]
        response = requests.post(url, headers=headers, json=tag_data)
        response.raise_for_status()
        return None

    def remove_tags_from_item(self, item_id: str, tags: List[str], if_unmodified_since_version: Optional[int] = None) -> None:
        """
        Remove tags from a specific item.

        Args:
            item_id: The ID of the item to remove tags from.
            tags: A list of tag names to remove.
            if_unmodified_since_version: Optional. The version of the item to ensure no conflicts.
        """
        for tag_name in tags:
            url = f'{self.BASE_URL}/{self.library_type}/{self.user_id}/items/{item_id}/tags/{tag_name}'
            headers = self.headers.copy()
            if if_unmodified_since_version:
                headers['If-Unmodified-Since-Version'] = str(if_unmodified_since_version)
            response = requests.delete(url, headers=headers)
            response.raise_for_status()
        return None
