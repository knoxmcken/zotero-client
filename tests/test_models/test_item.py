from zotero_client.models.item import Item

def test_item_from_api_response():
    api_response = {
        "key": "ABC123XYZ",
        "version": 123,
        "library": {},
        "links": {},
        "meta": {},
        "data": {
            "key": "ABC123XYZ",
            "version": 123,
            "itemType": "journalArticle",
            "title": "Test Article Title",
            "creators": [
                {
                    "creatorType": "author",
                    "firstName": "John",
                    "lastName": "Doe"
                }
            ],
            "date": "2023",
            "url": "https://example.com"
        }
    }

    item = Item.from_api_response(api_response)

    assert item.key == "ABC123XYZ"
    assert item.title == "Test Article Title"
    assert item.item_type == "journalArticle"
    assert len(item.creators) == 1
    assert item.creators[0]["lastName"] == "Doe"
    assert item.date == "2023"
    assert item.url == "https://example.com"
