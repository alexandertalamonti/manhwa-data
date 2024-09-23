import requests
import time
from urllib.parse import quote
from dotenv import load_dotenv
import os
import re

load_dotenv()

CLIENT_ID = os.getenv("CLIENT_ID")

def clean_title(title):
    # Remove "(manga)" from the end of the title if present
    return re.sub(r'\s*\(manga\)\s*$', '', title, flags=re.IGNORECASE)

def search_manga(title):
    cleaned_title = clean_title(title)
    url = f"https://api.myanimelist.net/v2/manga?q={quote(cleaned_title)}"
    headers = {
        'X-MAL-CLIENT-ID': CLIENT_ID
    }
    
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        if data['data']:
            return data['data'][0]['node']['id']  # Return the ID of the first result
    return None

# Read manga titles from the file
with open("top_500_underrated_manga.txt", "r", encoding="utf-8") as file:
    manga_titles = [line.strip() for line in file]

# Dictionary to store manga titles and their corresponding MAL IDs
manga_ids = {}

# Process each manga title
for title in manga_titles:
    mal_id = search_manga(title)
    if mal_id:
        manga_ids[title] = mal_id
        print(f"Found ID for '{title}': {mal_id}")
    else:
        print(f"Could not find ID for '{title}'")
    
    time.sleep(1)  # To avoid hitting rate limits

# Save the results to a new file
with open("manga_mal_ids.txt", "w", encoding="utf-8") as file:
    for title, mal_id in manga_ids.items():
        file.write(f"{title}: {mal_id}\n")

print(f"Processed {len(manga_ids)} manga titles. Results saved to manga_mal_ids.txt")