import pytest
from zotero_client.models.collection import Collection, group_collections_by_parent

def test_collection_from_api_response():
    api_response = {
        "key": "COLLECTION123",
        "version": 1,
        "library": {},
        "links": {},
        "meta": {},
        "data": {
            "key": "COLLECTION123",
            "version": 1,
            "name": "Test Collection",
            "parentCollection": False
        }
    }

    collection = Collection.from_api_response(api_response)

    assert collection.key == "COLLECTION123"
    assert collection.name == "Test Collection"
    assert collection.version == 1
    assert collection.parent_collection is False

def test_collection_from_api_response_with_parent():
    api_response = {
        "key": "SUBCOLLECTION456",
        "version": 2,
        "library": {},
        "links": {},
        "meta": {},
        "data": {
            "key": "SUBCOLLECTION456",
            "version": 2,
            "name": "Sub Collection",
            "parentCollection": "PARENTCOLLECTION123"
        }
    }

    collection = Collection.from_api_response(api_response)

    assert collection.key == "SUBCOLLECTION456"
    assert collection.name == "Sub Collection"
    assert collection.version == 2
    assert collection.parent_collection == "PARENTCOLLECTION123"


def test_group_collections_by_parent_basic():
    parent = Collection(key="PARENT", name="Parent", version=1)
    child = Collection(key="CHILD", name="Child", version=1, parent_collection="PARENT")

    grouped = group_collections_by_parent([parent, child])

    assert grouped[None] == [parent]
    assert grouped["PARENT"] == [child]


def test_group_collections_by_parent_missing_parent_becomes_root():
    orphan = Collection(key="ORPHAN", name="Orphan", version=1, parent_collection="MISSING")

    grouped = group_collections_by_parent([orphan])

    assert grouped[None] == [orphan]
    assert "MISSING" not in grouped


def test_group_collections_by_parent_self_referential_cycle():
    selfie = Collection(key="SELF", name="Selfie", version=1, parent_collection="SELF")

    grouped = group_collections_by_parent([selfie])

    assert grouped[None] == [selfie]


def test_group_collections_by_parent_mutual_cycle():
    a = Collection(key="A", name="Alpha", version=1, parent_collection="B")
    b = Collection(key="B", name="Beta", version=1, parent_collection="A")

    grouped = group_collections_by_parent([a, b])

    assert grouped[None] == [a, b]


def test_group_collections_by_parent_cycle_with_noncyclic_descendant():
    """
    A 3-way cycle (A->C, B->A, C->B) becomes three roots, but D, a normal
    child of A that is NOT itself part of the cycle, must keep its real
    parent link rather than being incorrectly promoted to root too.
    """
    a = Collection(key="A", name="Alpha", version=1, parent_collection="C")
    b = Collection(key="B", name="Beta", version=1, parent_collection="A")
    c = Collection(key="C", name="Gamma", version=1, parent_collection="B")
    d = Collection(key="D", name="Delta", version=1, parent_collection="A")

    grouped = group_collections_by_parent([a, b, c, d])

    assert set(collection.key for collection in grouped[None]) == {"A", "B", "C"}
    assert grouped["A"] == [d]
