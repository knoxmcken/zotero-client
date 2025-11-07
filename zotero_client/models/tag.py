from dataclasses import dataclass
from typing import Dict, Any

@dataclass
class Tag:
    tag: str
    type: int # 0 for automatic, 1 for manual

    @classmethod
    def from_api_response(cls, data: Dict[str, Any]) -> 'Tag':
        """Creates a Tag object from the Zotero API response."""
        return cls(
            tag=data.get('tag', ''),
            type=data.get('type', 1) # Default to manual tag if type is not specified
        )
