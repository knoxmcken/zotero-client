# Zotero API Client

A Python CLI app for managing a Zotero web library.

## Getting Started

Follow these steps to get a local copy of the project up and running.

### Prerequisites

*   Python 3.8+
*   `pip` (Python package installer)

### Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/knoxmcken/zotero-app.git
    cd zotero-app
    ```

2.  **Create and activate a virtual environment:**
    ```bash
    python -m venv .venv
    # On Windows
    .\.venv\Scripts\activate
    # On macOS/Linux
    source ./.venv/bin/activate
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configure API Keys:**
    Copy the example environment file and fill in your Zotero API key and user ID.
    ```bash
    cp .env.example .env
    ```
    Edit the `.env` file:
    ```
    ZOTERO_API_KEY=your_api_key_here
    ZOTERO_USER_ID=your_user_id_here
    ```
    Alternatively, you can use the CLI to configure your API keys:
    ```bash
    zot configure
    ```

5.  **Run the CLI:**
    ```bash
    zot --help
    ```
