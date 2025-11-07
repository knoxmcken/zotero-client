from dataclasses import dataclass
from typing import Optional, List, Dict, Any

@dataclass
class Collection:
    key: str
    name: str
    version: int
    parent_collection: Optional[str] = None

    @classmethod
    def from_api_response(cls, data: Dict[str, Any]) -> 'Collection':
        """Creates a Collection object from the Zotero API response."""
        collection_data = data.get('data', {})
        return cls(
            key=collection_data.get('key', ''),
            name=collection_data.get('name', ''),
            version=data.get('version', 0),
            parent_collection=collection_data.get('parentCollection', None)
        )
