from dataclasses import dataclass
from typing import List, Dict, Any

@dataclass
class Item:
    key: str
    title: str
    item_type: str
    creators: List[Dict[str, Any]]
    date: str
    url: str
    version: int

    @classmethod
    def from_api_response(cls, data: Dict[str, Any]) -> 'Item':
        """Creates an Item object from the Zotero API response."""
        item_data = data.get('data', {})
        return cls(
            key=item_data.get('key', ''),
            title=item_data.get('title', ''),
            item_type=item_data.get('itemType', ''),
            creators=item_data.get('creators', []),
            date=item_data.get('date', ''),
            url=item_data.get('url', ''),
            version=data.get('version', 0) # Version is at the top level of the response
        )
