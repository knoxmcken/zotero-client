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


def group_collections_by_parent(collections: List['Collection']) -> Dict[Optional[str], List['Collection']]:
    """
    Group collections by their parent_collection key.

    A collection whose parent_collection key isn't present among the
    given collections, or that is itself part of a parent-reference
    cycle (self-referential or mutual), is grouped under None (root)
    rather than silently dropped. A non-cyclic descendant of a cyclic
    collection keeps its normal parent grouping.
    """
    by_key = {c.key: c for c in collections}
    cycle_members: set = set()
    resolved: set = set()

    for start in by_key:
        if start in resolved or start in cycle_members:
            continue
        path: List[str] = []
        current = start
        while True:
            if current in path:
                idx = path.index(current)
                cycle_members.update(path[idx:])
                resolved.update(path[:idx])
                break
            if current in resolved or current in cycle_members:
                resolved.update(path)
                break
            path.append(current)
            parent = by_key[current].parent_collection
            if parent in (None, '') or parent not in by_key:
                resolved.update(path)
                break
            current = parent

    def resolve_parent(collection: 'Collection') -> Optional[str]:
        if collection.key in cycle_members:
            return None
        parent = collection.parent_collection
        if parent in (None, '') or parent not in by_key:
            return None
        return parent

    grouped: Dict[Optional[str], List['Collection']] = {}
    for c in collections:
        grouped.setdefault(resolve_parent(c), []).append(c)
    return grouped
