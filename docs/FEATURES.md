# Zotero API Client Features

This document outlines the current and proposed features for the Zotero API Client.

> **Status legend (reviewed 2026-09-13):** `[x]` = implemented, `[ ]` = not implemented (still proposed).

### Core Data Management

-   [x] **List Items:** Retrieve a list of all items in a user's library, with options for filtering by collection, tag, or item type. _(tag / item type / query filters available; collection filter not exposed)_
-   [x] **Get Item Details:** Fetch the complete metadata for a specific item.
-   [x] **Create, Update, and Delete Items:** Add new items, modify existing ones, and move items to the trash.
-   [x] **Attachment Management:**
    -   [x] List all attachments for an item.
    -   [x] Upload and download attachments.
-   [x] **Tag Management:**
    -   [x] List all tags in the library.
    -   [x] Add or remove tags from items.
-   [x] **Collection Management:**
    -   [x] List all collections.
    -   [x] Create, rename, and delete collections.
    -   [ ] Add or remove items from collections. _(no dedicated client method or CLI command yet; only possible via a raw item update)_

### Search and Retrieval

-   [x] **Simple and Advanced Search:** Implement the Zotero API's search capabilities, allowing users to find items based on keywords, fields, and other criteria.
-   [ ] **Full-Text Search:** If the API supports it, allow searching within the text of attached PDFs and other documents. _(only a `qmode='everything'` pass-through exists; no dedicated full-text search)_

### Advanced and AI-Powered Features

-   [x] **Citation Generation:**
    -   [x] Generate formatted citations for items in various styles (e.g., APA, MLA, Chicago).
    -   [ ] This could be enhanced with a natural language interface, e.g., "get me the APA citation for the Smith 2022 paper."
-   [x] **AI-Powered Summarization:**
    -   [x] Integrate with a large language model to provide summaries of articles based on their abstracts or full text.
-   [x] **Duplicate Detection:**
    -   [x] Identify and flag potential duplicate items in the library.
-   [ ] **"Smart" Collections:**
    -   [ ] Create collections automatically based on predefined rules or AI-powered topic modeling of the library's contents.

### Usability and Integration

-   [x] **Interactive CLI:**
    -   [x] An enhanced, interactive command-line interface that guides the user through common tasks.
-   [x] **Configuration Wizard:**
    -   [x] A command to help users set up their API keys and preferences for the first time. _(`zot configure`)_
-   [x] **Export and Backup:**
    -   [x] Export the library or specific collections to various formats (e.g., BibTeX, RIS, CSV). _(bibtex and csv supported)_
-   [x] **Jupyter Notebook Integration:**
    -   [x] Provide helper functions or classes to make it easy to work with Zotero data in a Jupyter environment for research and analysis. _(example notebook in `examples/jupyter/`)_

### Web Interface

-   [x] **Flask Web UI:** Browse items, collections, and tags in a browser, with autocomplete filter fields. _(added in PR #4; routes for items, collections, and tags)_
