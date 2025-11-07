"""Configuration utilities."""

import os
from dotenv import load_dotenv


def load_environment():
    """Load environment variables from .env file."""
    load_dotenv()
    
    return {
        'api_key': os.getenv('ZOTERO_API_KEY'),
        'user_id': os.getenv('ZOTERO_USER_ID'),
        'library_type': os.getenv('ZOTERO_LIBRARY_TYPE', 'users')
    }
