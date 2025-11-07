"""Zotero API client implementation."""

import requests
from typing import List, Dict, Optional


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
    
    def get_items(self, limit: Optional[int] = None) -> List[Dict]:
        """
        Retrieve items from the Zotero library.
        
        Args:
            limit: Maximum number of items to retrieve
            
        Returns:
            List of item dictionaries
        """
        url = f'{self.BASE_URL}/{self.library_type}/{self.user_id}/items'
        params = {}
        if limit:
            params['limit'] = limit
            
        response = requests.get(url, headers=self.headers, params=params)
        response.raise_for_status()
        return response.json()
    
    def get_item(self, item_id: str) -> Dict:
        """
        Retrieve a specific item by ID.
        
        Args:
            item_id: The item ID
            
        Returns:
            Item dictionary
        """
        url = f'{self.BASE_URL}/{self.library_type}/{self.user_id}/items/{item_id}'
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        return response.json()
    
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
