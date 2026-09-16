"""Zotero API client implementation."""

import hashlib
import mimetypes
import os
import time
from typing import List, Dict, Optional, Any

import openai
import requests
from bs4 import BeautifulSoup

from zotero_client.models.item import Item
from zotero_client.models.collection import Collection
from zotero_client.models.tag import Tag


class ZoteroClient:
    """Client for interacting with the Zotero API."""
    
    BASE_URL = 'https://api.zotero.org'

    #: Connect/read timeout applied to every request.
    TIMEOUT = (10, 30)

    #: The Web API returns at most 100 objects per request.
    PAGE_SIZE = 100

    #: Longest we will sleep for a server-supplied backoff hint, in seconds.
    MAX_BACKOFF = 60.0
    
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

    def _request(self, method: str, url: str, retries: int = 2, **kwargs):
        """
        Perform an API request, honouring the API's rate-limit hints.

        Zotero may attach ``Backoff: <seconds>`` to any response, successful ones
        included, and asks clients to refrain from further requests for that long.
        429 and 503 responses may carry ``Retry-After`` and are retried.

        Args:
            method: HTTP method name ('get', 'post', 'put', 'delete').
            url: The URL to request.
            retries: Extra attempts allowed for 429/503 responses.
            **kwargs: Passed through to requests.

        Returns:
            The requests.Response.
        """
        kwargs.setdefault('timeout', self.TIMEOUT)
        response = None
        for attempt in range(retries + 1):
            response = getattr(requests, method)(url, **kwargs)

            backoff = response.headers.get('Backoff')
            if backoff:
                self._pause(backoff)

            if response.status_code in (429, 503) and attempt < retries:
                self._pause(response.headers.get('Retry-After') or (2 ** attempt))
                continue
            return response
        return response

    def _pause(self, seconds) -> None:
        """Sleep for a server-supplied delay, capped so the CLI stays usable."""
        try:
            delay = float(seconds)
        except (TypeError, ValueError):
            return
        time.sleep(max(0.0, min(delay, self.MAX_BACKOFF)))

    def _get_pages(self, url: str, params: Optional[Dict[str, Any]] = None, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Read a multi-object endpoint, following pagination.

        The Web API defaults to 25 results per request and caps a page at 100,
        so a single call only ever sees a slice of a library.

        Args:
            url: The endpoint to read.
            params: Query parameters, excluding paging.
            limit: Cap on the total number of objects returned; None means all.

        Returns:
            The raw JSON entries, in API order.
        """
        params = dict(params or {})
        page_size = self.PAGE_SIZE if limit is None else max(1, min(limit, self.PAGE_SIZE))
        results: List[Dict[str, Any]] = []
        start = 0
        while True:
            response = self._request(
                'get',
                url,
                headers=self.headers,
                params=dict(params, limit=page_size, start=start),
            )
            response.raise_for_status()
            batch = response.json()
            results.extend(batch)
            if len(batch) < page_size or (limit is not None and len(results) >= limit):
                break
            start += len(batch)
        return results[:limit] if limit is not None else results

    def _parse_single_write_response(self, result: Dict[str, Any]) -> Dict[str, Any]:
        if result.get('failed'):
            raise RuntimeError(f"Zotero write failed: {result['failed'].get('0')}")
        try:
            return result['successful']['0']
        except KeyError:
            raise RuntimeError(f"Unexpected write response: {result}")

    def get_items(self, limit: Optional[int] = None, q: Optional[str] = None, qmode: Optional[str] = None, item_type: Optional[str] = None, tag: Optional[str] = None, include_trashed: Optional[bool] = None) -> List[Item]:
        """
        Retrieve items from the Zotero library with advanced search capabilities.
        
        Args:
            limit: Maximum number of items to retrieve; None retrieves all
                matching items, following pagination.
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
            
        return [
            Item.from_api_response(item_data)
            for item_data in self._get_pages(url, params, limit)
        ]
    
    def get_item(self, item_id: str) -> Item:
        """
        Retrieve a specific item by ID.
        
        Args:
            item_id: The item ID
            
        Returns:
            Item object
        """
        url = f'{self.BASE_URL}/{self.library_type}/{self.user_id}/items/{item_id}'
        response = self._request('get', url, headers=self.headers)
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
        response = self._request('post', url, headers=self.headers, json=[item_data])
        response.raise_for_status()
        entry = self._parse_single_write_response(response.json())
        if isinstance(entry, str):
            # Some responses carry only the new key; read the object back.
            return self.get_item(entry)
        return Item.from_api_response(entry)

    def update_item(self, item_id: str, item_data: Dict[str, Any], if_unmodified_since_version: Optional[int] = None) -> Item:
        """
        Update an existing item in the Zotero library.

        A successful update answers 204 No Content, in which case the item is
        re-fetched to return its new state.

        Args:
            item_id: The ID of the item to update.
            item_data: A dictionary containing the updated item's data.
            if_unmodified_since_version: Optional. The version of the item to ensure no conflicts.

        Returns:
            The updated Item object.
        """
        url = f'{self.BASE_URL}/{self.library_type}/{self.user_id}/items/{item_id}'
        version = if_unmodified_since_version
        if version is None:
            version = item_data.get('version')
        version = self._version_for_write(version, lambda: self.get_item(item_id).version)
        headers = dict(self.headers, **{'If-Unmodified-Since-Version': str(version)})
        response = self._request('put', url, headers=headers, json=item_data)
        response.raise_for_status()
        if not response.content:
            return self.get_item(item_id)
        return Item.from_api_response(response.json())

    def delete_item(self, item_id: str, if_unmodified_since_version: Optional[int] = None) -> None:
        """
        Delete an item from the Zotero library.

        Args:
            item_id: The ID of the item to delete.
            if_unmodified_since_version: Optional. The version of the item to ensure no conflicts.
        """
        url = f'{self.BASE_URL}/{self.library_type}/{self.user_id}/items/{item_id}'
        version = self._version_for_write(
            if_unmodified_since_version, lambda: self.get_item(item_id).version
        )
        headers = dict(self.headers, **{'If-Unmodified-Since-Version': str(version)})
        response = self._request('delete', url, headers=headers)
        response.raise_for_status()
        return None
    
    def get_attachments(self, item_id: Optional[str] = None, limit: Optional[int] = None) -> List[Item]:
        """
        Retrieve attachment items from the Zotero library.

        With `item_id`, this reads that item's children and keeps the
        attachments. There is no `parentItem` filter on `/items`: passing one is
        silently ignored and returns attachments from the whole library, so the
        child endpoint is the only way to scope this.

        Args:
            item_id: Optional. The ID of the parent item to retrieve attachments for.
            limit: Maximum number of attachments to retrieve; None retrieves all.

        Returns:
            List of Item objects (representing attachments).
        """
        params = {'itemType': 'attachment'}
        if item_id:
            url = (
                f'{self.BASE_URL}/{self.library_type}/{self.user_id}'
                f'/items/{item_id}/children'
            )
        else:
            url = f'{self.BASE_URL}/{self.library_type}/{self.user_id}/items'

        return [
            Item.from_api_response(item_data)
            for item_data in self._get_pages(url, params, limit)
        ]

    def upload_attachment(self, parent_item_id: str, file_path: str, title: Optional[str] = None) -> Item:
        """
        Upload a file as an attachment to a Zotero item.

        Implements the documented three-step file upload: create the attachment
        item, authorize and perform the upload, then register the upload key.
        See https://www.zotero.org/support/dev/web_api/v3/file_upload

        Args:
            parent_item_id: The ID of the parent item to attach the file to.
            file_path: The path to the file to upload.
            title: Optional. The title for the attachment item. If not provided, uses the filename.

        Returns:
            The created Item object representing the attachment.
        """
        if not os.path.isfile(file_path):
            raise FileNotFoundError(f"No such file: {file_path}")

        filename = os.path.basename(file_path)
        file_size = os.path.getsize(file_path)
        with open(file_path, 'rb') as f:
            file_content = f.read()

        md5 = hashlib.md5(file_content).hexdigest()
        mtime = str(int(os.path.getmtime(file_path) * 1000))  # milliseconds

        # 1. Create the attachment item. The template endpoint is global, and the
        # parent link is set on the payload rather than requested from the API.
        template = self.get_attachment_template(link_mode='imported_file')
        template.update({
            'title': title if title is not None else filename,
            'parentItem': parent_item_id,
            'filename': filename,
            'linkMode': 'imported_file',
            'contentType': mimetypes.guess_type(filename)[0] or 'application/octet-stream',
        })
        items_url = f'{self.BASE_URL}/{self.library_type}/{self.user_id}/items'
        create_response = self._request('post', 
            items_url,
            headers={**self.headers, 'Content-Type': 'application/json'},
            json=[template],
        )
        create_response.raise_for_status()
        entry = self._parse_single_write_response(create_response.json())
        attachment_key = entry if isinstance(entry, str) else (
            entry.get('key') or entry.get('data', {}).get('key')
        )
        if not attachment_key:
            raise RuntimeError(f"Unexpected write response: {entry}")

        file_url = f'{items_url}/{attachment_key}/file'
        auth_headers = {
            **self.headers,
            'Content-Type': 'application/x-www-form-urlencoded',
            'If-None-Match': '*',
        }

        # 2. Ask the API to authorize the upload
        auth_response = self._request('post', 
            file_url,
            headers=auth_headers,
            data={'md5': md5, 'filename': filename, 'filesize': file_size, 'mtime': mtime},
        )
        auth_response.raise_for_status()
        auth = auth_response.json()

        if not auth.get('exists'):
            # 3. POST prefix + file + suffix to the storage url
            body = auth['prefix'].encode('utf-8') + file_content + auth['suffix'].encode('utf-8')
            upload_response = self._request('post', 
                auth['url'],
                headers={'Content-Type': auth['contentType']},
                data=body,
            )
            upload_response.raise_for_status()

            # 4. Register the upload
            register_response = self._request('post', file_url, headers=auth_headers, data={'upload': auth['uploadKey']})
            register_response.raise_for_status()

        return self.get_item(attachment_key)

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

        # Documented file endpoint; the item's links carry no 'file' entry.
        download_url = (
            f'{self.BASE_URL}/{self.library_type}/{self.user_id}'
            f'/items/{attachment_id}/file'
        )
        response = self._request('get', download_url, headers=self.headers, stream=True)
        response.raise_for_status()

        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        return output_path

    def get_citations(self, item_ids: List[str], style: str, format: str = 'html', locale: Optional[str] = None) -> str:
        """
        Generate formatted citations for a list of item IDs.

        The API returns citations as XHTML through `format=json&include=citation`
        (there is no `citation` query parameter). `format='text'` strips the
        markup from each citation locally.

        Args:
            item_ids: A list of Zotero item keys for which to generate citations.
            style: The CSL style to use (e.g., 'apa', 'chicago-fullnote-bibliography').
            format: The output format ('html' or 'text'). Defaults to 'html'.
            locale: Optional. The bibliography locale (e.g., 'en-US').

        Returns:
            A string containing the formatted citations, one per line.
        """
        if format not in ('html', 'text'):
            raise ValueError(f"Unsupported citation format: {format!r} (use 'html' or 'text')")

        url = f'{self.BASE_URL}/{self.library_type}/{self.user_id}/items'
        params = {
            'itemKey': ','.join(item_ids),
            'include': 'citation',
            'style': style,
        }
        if locale:
            params['locale'] = locale

        response = self._request('get', url, headers=self.headers, params=params)
        response.raise_for_status()

        citations = [entry.get('citation', '') for entry in response.json()]
        if format == 'text':
            citations = [BeautifulSoup(c, 'html.parser').get_text() for c in citations]
        return '\n'.join(citations)

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

    def export_items(self, format: str = 'bibtex', limit: Optional[int] = None) -> str:
        """
        Export items from the Zotero library to a specified format.

        Args:
            format: The export format ('bibtex' or 'csv'). Defaults to 'bibtex'.
            limit: Passed to the API, which requires a limit for export formats.
                Export formats are processed as a whole feed, not a page.

        Returns:
            A string containing the exported data.
        """
        url = f'{self.BASE_URL}/{self.library_type}/{self.user_id}/items'
        params = {'format': format, 'limit': limit if limit is not None else self.PAGE_SIZE}
        
        response = self._request('get', url, headers=self.headers, params=params)
        response.raise_for_status()
        return response.text

    def get_attachment_template(self, link_mode: str = 'imported_file') -> Dict[str, Any]:
        """
        Retrieve an attachment item template from the Zotero API.

        The template endpoint is global, not library-scoped: it lives at
        `/items/new`, alongside the other schema endpoints. The library-scoped
        form (`/users/<id>/items/new`) returns 404.

        Args:
            link_mode: The link mode to request a template for. The API requires
                this for attachment templates (400 without it).

        Returns:
            A dictionary representing the attachment item template.
        """
        url = f'{self.BASE_URL}/items/new'
        params = {'itemType': 'attachment', 'linkMode': link_mode}

        response = self._request('get', url, headers=self.headers, params=params)
        response.raise_for_status()
        return response.json()

    def get_collections(self, limit: Optional[int] = None) -> List[Collection]:
        """
        Retrieve collections from the Zotero library.

        Args:
            limit: Maximum number of collections to retrieve; None retrieves all.

        Returns:
            List of Collection objects
        """
        url = f'{self.BASE_URL}/{self.library_type}/{self.user_id}/collections'
        params = {}
        return [
            Collection.from_api_response(collection_data)
            for collection_data in self._get_pages(url, params, limit)
        ]

    def create_collection(self, collection_data: Dict[str, Any]) -> Collection:
        """
        Create a new collection in the Zotero library.

        Args:
            collection_data: A dictionary containing the collection's data.

        Returns:
            The created Collection object.
        """
        url = f'{self.BASE_URL}/{self.library_type}/{self.user_id}/collections'
        response = self._request('post', url, headers=self.headers, json=[collection_data])
        response.raise_for_status()
        return Collection.from_api_response(self._parse_single_write_response(response.json()))

    def get_collection(self, collection_id: str) -> Collection:
        """
        Retrieve a specific collection by ID.

        Args:
            collection_id: The collection key.

        Returns:
            Collection object
        """
        url = f'{self.BASE_URL}/{self.library_type}/{self.user_id}/collections/{collection_id}'
        response = self._request('get', url, headers=self.headers)
        response.raise_for_status()
        return Collection.from_api_response(response.json())

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
        version = if_unmodified_since_version
        if version is None:
            version = collection_data.get('version')
        version = self._version_for_write(version, lambda: self.get_collection(collection_id).version)
        headers = dict(self.headers, **{'If-Unmodified-Since-Version': str(version)})
        response = self._request('put', url, headers=headers, json=collection_data)
        response.raise_for_status()
        if not response.content:
            # A successful PUT answers 204 No Content.
            return self.get_collection(collection_id)
        return Collection.from_api_response(response.json())

    def delete_collection(self, collection_id: str, if_unmodified_since_version: Optional[int] = None) -> None:
        """
        Delete a collection from the Zotero library.

        Args:
            collection_id: The ID of the collection to delete.
            if_unmodified_since_version: Optional. The version of the collection to ensure no conflicts.
        """
        url = f'{self.BASE_URL}/{self.library_type}/{self.user_id}/collections/{collection_id}'
        version = self._version_for_write(
            if_unmodified_since_version, lambda: self.get_collection(collection_id).version
        )
        headers = dict(self.headers, **{'If-Unmodified-Since-Version': str(version)})
        response = self._request('delete', url, headers=headers)
        response.raise_for_status()
        return None

    def get_tags(self, item_id: Optional[str] = None, limit: Optional[int] = None) -> List[Tag]:
        """
        Retrieve tags from the Zotero library. Can be filtered by item.

        Args:
            item_id: Optional. The ID of the item to retrieve tags for.
            limit: Maximum number of tags to retrieve; None retrieves all.

        Returns:
            List of Tag objects.
        """
        if item_id:
            url = f'{self.BASE_URL}/{self.library_type}/{self.user_id}/items/{item_id}/tags'
        else:
            url = f'{self.BASE_URL}/{self.library_type}/{self.user_id}/tags'
        return [
            Tag.from_api_response(tag_data)
            for tag_data in self._get_pages(url, {}, limit)
        ]

    def add_tags_to_item(self, item_id: str, tags: List[str], if_unmodified_since_version: Optional[int] = None) -> None:
        """
        Add tags to a specific item.

        Tags are an item field, not a sub-resource: the API answers 405 Method
        Not Allowed to POST and PUT on `/items/<key>/tags`, so this reads the
        item's current tags, merges in the new ones and PATCHes the result.
        Array properties are complete lists, so sending only the added tags
        would silently drop every existing one.

        Args:
            item_id: The ID of the item to add tags to.
            tags: A list of tag names to add.
            if_unmodified_since_version: Optional. The version of the item to ensure no conflicts.
        """
        existing, version = self._read_item_tags(item_id)
        known = {tag.get('tag') for tag in existing}
        merged = list(existing) + [{'tag': name} for name in tags if name not in known]
        self._patch_item(
            item_id,
            {'tags': merged},
            if_unmodified_since_version if if_unmodified_since_version is not None else version,
        )

    def remove_tags_from_item(self, item_id: str, tags: List[str], if_unmodified_since_version: Optional[int] = None) -> None:
        """
        Remove tags from a specific item.

        As with `add_tags_to_item`, this PATCHes the item's tag list rather than
        looping over the `/items/<key>/tags/<tag>` DELETE that the API rejects
        with 405 (and that could not reuse one version across several tags
        anyway).

        Args:
            item_id: The ID of the item to remove tags from.
            tags: A list of tag names to remove.
            if_unmodified_since_version: Optional. The version of the item to ensure no conflicts.
        """
        existing, version = self._read_item_tags(item_id)
        dropping = set(tags)
        remaining = [tag for tag in existing if tag.get('tag') not in dropping]
        self._patch_item(
            item_id,
            {'tags': remaining},
            if_unmodified_since_version if if_unmodified_since_version is not None else version,
        )

    def _read_item_tags(self, item_id: str) -> tuple:
        """Read an item's current tag list and version, in one request."""
        url = f'{self.BASE_URL}/{self.library_type}/{self.user_id}/items/{item_id}'
        response = self._request('get', url, headers=self.headers)
        response.raise_for_status()
        data = response.json()
        return data.get('data', {}).get('tags', []), data.get('version')

    def _patch_item(self, item_id: str, payload: Dict[str, Any], version: Optional[int] = None) -> None:
        """Apply a partial update, supplying the precondition the API requires."""
        url = f'{self.BASE_URL}/{self.library_type}/{self.user_id}/items/{item_id}'
        if version is None:
            version = self.get_item(item_id).version
        headers = dict(self.headers, **{
            'Content-Type': 'application/json',
            'If-Unmodified-Since-Version': str(version),
        })
        response = self._request('patch', url, headers=headers, json=payload)
        response.raise_for_status()
        return None

    def _version_for_write(self, current: Optional[int], fetch_current) -> int:
        """
        Return the version to send as a write precondition.

        Zotero requires one: a write with no `If-Unmodified-Since-Version`
        header (and no `version` property in the body) is rejected with 428
        Precondition Required. When the caller supplies no version, read the
        object's current one, which makes the argument genuinely optional -- at
        the cost of one extra GET and no conflict protection.
        """
        if current is not None:
            return current
        return fetch_current()
