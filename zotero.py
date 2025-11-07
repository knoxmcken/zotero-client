import requests

# Load Environment variables
import os
from dotenv import load_dotenv
load_dotenv()





API_KEY = os.getenv('ZOTERO_API_KEY')
USER_ID = os.getenv('ZOTERO_USER_ID')
LIBRARY_TYPE = 'users'  # or 'groups' for group libraries

url = f'https://api.zotero.org/{LIBRARY_TYPE}/{USER_ID}/items'
headers = {'Zotero-API-Key': API_KEY}

response = requests.get(url, headers=headers)
items = response.json()

for item in items:
    print(item)
