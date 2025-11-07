# Application Architecture

This document outlines the proposed architecture for the Zotero API client application. The architecture is based on a layered approach, separating concerns into distinct components to ensure scalability, testability, and maintainability.

### Proposed Directory Structure

```
zotero-app/
├── zotero_client/
│   ├── api/
│   │   ├── __init__.py
│   │   └── client.py       # Low-level Zotero API communication
│   │
│   ├── cli/
│   │   ├── __init__.py
│   │   └── main.py         # Command-line interface logic
│   │
│   ├── models/
│   │   ├── __init__.py
│   │   ├── item.py         # Data model for a Zotero item
│   │   ├── collection.py   # Data model for a Zotero collection
│   │   └── tag.py          # Data model for a Zotero tag
│   │
│   ├── services/
│   │   ├── __init__.py
│   │   ├── citation.py     # Citation generation logic
│   │   ├── summarization.py# AI summarization logic
│   │   └── duplicate.py    # Duplicate detection logic
│   │
│   └── utils/
│       ├── __init__.py
│       └── config.py       # Configuration loading
│
├── tests/
│   ├── test_api.py
│   ├── test_cli.py
│   └── test_services.py
│
└── ...
```

### Component Responsibilities

#### 1. API Layer (`zotero_client/api/`)

*   **`client.py`**: The `ZoteroClient` class in this file will be the single point of contact with the Zotero API.
    *   **Responsibilities:**
        *   Handle authentication and construct API requests.
        *   Perform HTTP operations (GET, POST, PUT, DELETE).
        *   Handle API-specific errors, rate limiting, and retries.
        *   Parse the JSON responses from the API and convert them into data models from the `models` layer.
    *   **Principle:** This layer should contain no business logic. It is purely for communication and data transformation.

#### 2. Data Model Layer (`zotero_client/models/`)

*   **`item.py`, `collection.py`, etc.**: Each file will define a data model for a Zotero object, likely using `dataclasses` or `pydantic`.
    *   **Responsibilities:**
        *   Define the structure and types of the data (e.g., an `Item` has a `title` which is a string, `creators` which is a list of authors, etc.).
        *   Provide data validation to prevent malformed data from propagating through the application.
    *   **Benefit:** Using models instead of raw dictionaries makes the code strongly typed, easier to read, and less prone to errors.

#### 3. Service Layer (`zotero_client/services/`)

*   This layer will contain the "brains" of the application for features that are not simple API calls.
    *   **Responsibilities:**
        *   Orchestrate calls to the `ZoteroClient` in the API layer.
        *   Implement complex business logic.
    *   **Examples:**
        *   `summarization.py`: Would contain a function that takes an item ID, uses the API client to fetch the item's data and attachment, extracts the text, and then calls the OpenAI API to generate a summary.
        *   `duplicate.py`: Would implement the logic for finding duplicate items by fetching multiple items and comparing their fields.

#### 4. Presentation Layer (`zotero_client/cli/`)

*   **`main.py`**: This will be the user's entry point to the application.
    *   **Responsibilities:**
        *   Define the CLI commands, arguments, and options (using a library like `click` or `argparse`).
        *   Parse user input.
        *   Call the appropriate methods in the `services` or `api` layers.
        *   Format the data returned from the other layers for a clean and user-friendly display in the terminal.

### Benefits of this Architecture

*   **Separation of Concerns:** Each part of the application has a single, well-defined responsibility, making the code easier to understand and maintain.
*   **Testability:** Each layer can be tested in isolation. For example, we can test the service layer by "mocking" the API client, allowing us to run tests without making actual network requests.
*   **Scalability:** Adding a new feature becomes a matter of adding a new service and a new CLI command, without requiring major changes to the existing code.
*   **Reusability:** The `api` and `models` layers are decoupled from the CLI, meaning they could be imported and used in other contexts, such as a web application or a Jupyter notebook.
