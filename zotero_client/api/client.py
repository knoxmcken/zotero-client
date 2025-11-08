"""Zotero API client implementation."""

import requests
from typing import List, Dict, Optional, Any
import os
import openai
from zotero_client.models.item import Item
from zotero_client.models.collection import Collection
from zotero_client.models.tag import Tag


class ZoteroClient:
    """Client for interacting with the Zotero API."""
    
    BASE_URL = 'https://api.zotero.org'
    
    def __init__(self, api_key: str, user_id: str, openai_api_key: Optional[str] = None, library_type: str = 'users'):
        """
        Initialize the Zotero client.
        
        Args:
            api_key: Zotero API key
            user_id: Zotero user ID
            openai_api_key: Optional. OpenAI API key for AI-powered features.
            library_type: Type of library ('users' or 'groups')
        """
        self.api_key = api_key
        self.user_id = user_id
        self.openai_api_key = openai_api_key
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

    def download_attachment(self, attachment_id: str, output_path: str) -> str:
        """
        Download the file content of an attachment.

        Args:
            attachment_id: The ID of the attachment item to download.
            output_path: The path where the downloaded file should be saved.

        Returns:
            The path to the downloaded file.
        """
        attachment_item = self.get_item(attachment_id)

        if attachment_item.item_type != 'attachment':
            raise ValueError(f"Item {attachment_id} is not an attachment.")

        if 'file' not in attachment_item.links:
            raise ValueError(f"Attachment {attachment_id} does not have a downloadable file.")

        download_url = attachment_item.links['file']['href']
        response = requests.get(download_url, headers=self.headers, stream=True)
        response.raise_for_status()

        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        return output_path

    def get_citations(self, item_ids: List[str], style: str, format: str = 'html', locale: Optional[str] = None) -> str:
        """
        Generate formatted citations or a bibliography for a list of item IDs.

        Args:
            item_ids: A list of Zotero item keys for which to generate citations.
            style: The CSL style to use (e.g., 'apa', 'chicago-fullnote-bibliography').
            format: The output format ('html' or 'text'). Defaults to 'html'.
            locale: Optional. The bibliography locale (e.g., 'en-US').

        Returns:
            A string containing the formatted citations or bibliography.
        """
        url = f'{self.BASE_URL}/{self.library_type}/{self.user_id}/items'
        params = {
            'itemKey': ','.join(item_ids),
            'style': style,
            'format': format,
            'citation': '1' # Request individual citations
        }
        if locale:
            params['locale'] = locale

        response = requests.get(url, headers=self.headers, params=params)
        response.raise_for_status()
        return response.text

    def summarize_item_content(self, item_id: str, prompt: str = "Summarize the following text:") -> str:
        """
        Summarize the content of a Zotero item using OpenAI.

        Args:
            item_id: The ID of the item to summarize.
            prompt: The prompt to send to the OpenAI model. Defaults to "Summarize the following text:".

        Returns:
            A string containing the summary.
        """
        if not self.openai_api_key:
            raise ValueError("OpenAI API key is not configured.")

        item = self.get_item(item_id)
        content_to_summarize = item.title # Start with title, can be expanded to abstract/notes/attachments

        if hasattr(item, 'abstract_note') and item.abstract_note:
            content_to_summarize += f"\n\nAbstract: {item.abstract_note}"
        # Further expansion could involve fetching full-text from attachments

        if not content_to_summarize:
            return "No content available to summarize."

        try:
            client = openai.OpenAI(api_key=self.openai_api_key)
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": content_to_summarize}
                ]
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            raise RuntimeError(f"OpenAI API error: {e}")

    def find_duplicates(self) -> Dict[str, List[Item]]:
        """
        Find potential duplicate items based on title, creators, and year.

        Returns:
            A dictionary where keys are a concatenated string of (title, creators, year)
            and values are lists of Item objects identified as duplicates.
        """
        all_items = self.get_items(limit=None) # Fetch all items
        item_map = {}
        duplicates = {}

        for item in all_items:
            # Normalize title for comparison (lowercase, remove non-alphanumeric)
            normalized_title = ''.join(filter(str.isalnum, item.title)).lower()

            # Extract creator last names and sort them for consistent comparison
            creator_last_names = sorted([c.get('lastName', '').lower() for c in item.creators if c.get('lastName')])
            creators_key = '_'.join(creator_last_names)

            # Extract year from date, handle various date formats
            year = None
            if item.date:
                try:
                    year = str(item.date).split('-')[0] # Assumes YYYY-MM-DD or YYYY
                except IndexError:
                    pass # Handle cases where date might be malformed
            
            # Create a unique key for comparison
            # Only consider items with title, creators, and year for duplication check
            if normalized_title and creators_key and year:
                duplicate_key = f"{normalized_title}-{creators_key}-{year}"

                if duplicate_key in item_map:
                    if duplicate_key not in duplicates:
                        duplicates[duplicate_key] = [item_map[duplicate_key]]
                    duplicates[duplicate_key].append(item)
                else:
                    item_map[duplicate_key] = item
        return duplicates

    def export_items(self, format: str = 'bibtex') -> str:
        """
        Export items from the Zotero library to a specified format.

        Args:
            format: The export format ('bibtex' or 'csv'). Defaults to 'bibtex'.

        Returns:
            A string containing the exported data.
        """
        url = f'{self.BASE_URL}/{self.library_type}/{self.user_id}/items'
        params = {'format': format}
        
        response = requests.get(url, headers=self.headers, params=params)
        response.raise_for_status()
        return response.text

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
