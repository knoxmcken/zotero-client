import pytest
from zotero_client.models.collection import Collection

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
