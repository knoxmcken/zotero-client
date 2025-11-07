"""Zotero API client implementation."""

import requests
from typing import List, Dict, Optional, Any
from zotero_client.models.item import Item


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
    
    def get_items(self, limit: Optional[int] = None) -> List[Item]:
        """
        Retrieve items from the Zotero library.
        
        Args:
            limit: Maximum number of items to retrieve
            
        Returns:
            List of Item objects
        """
        url = f'{self.BASE_URL}/{self.library_type}/{self.user_id}/items'
        params = {}
        if limit:
            params['limit'] = limit
            
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
    
    def get_collections(self) -> List[Dict]:
        """
        Retrieve collections from the Zotero library.
        
        Returns:
            List of collection dictionaries
        """
        url = f'{self.BASE_URL}/{self.library_type}/{self.user_id}/collections'
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        return response.json()
