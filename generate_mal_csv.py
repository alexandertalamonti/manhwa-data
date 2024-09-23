import requests
import pandas as pd
from dotenv import load_dotenv
import os
import time
import json
import re

load_dotenv()

CLIENT_ID = os.getenv("CLIENT_ID")

def clean_title(title):
    # Remove "(manga)" from the end of the title if present
    return re.sub(r'\s*\(manga\)\s*$', '', title, flags=re.IGNORECASE)

def get_manga_details(mal_id):
    url = f"https://api.myanimelist.net/v2/manga/{mal_id}?fields=id,title,main_picture,alternative_titles,start_date,end_date,synopsis,mean,rank,popularity,num_list_users,num_scoring_users,nsfw,created_at,updated_at,media_type,status,genres,my_list_status,num_volumes,num_chapters,authors{{first_name,last_name}},pictures,background,related_anime,related_manga,recommendations,serialization{{name}}"
    headers = {
        'X-MAL-CLIENT-ID': CLIENT_ID
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error fetching data for ID {mal_id}: {response.status_code} - {response.text}")
        return None

# Function to flatten nested dictionaries
def flatten_dict(d, parent_key='', sep='_'):
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        elif isinstance(v, list):
            items.append((new_key, json.dumps(v)))
        else:
            items.append((new_key, v))
    return dict(items)

# Read manga titles and IDs from the file
with open("manga_mal_ids.txt", "r", encoding="utf-8") as file:
    manga_ids = {line.rsplit(": ", 1)[0].strip(): int(line.rsplit(": ", 1)[1].strip()) for line in file if line.strip()}

manga_details = []

# Process each manga ID to get its details
for title, mal_id in manga_ids.items():
    details = get_manga_details(mal_id)
    if details:
        manga_details.append(details)
        print(f"Fetched details for '{title}' with ID {mal_id}")
    time.sleep(1)  # To avoid hitting rate limits

# Flatten each manga detail dictionary
flattened_details = [flatten_dict(detail) for detail in manga_details]

# Create a DataFrame
manga_df = pd.DataFrame(flattened_details)

# Save to CSV
csv_filename = "manga_details.csv"
manga_df.to_csv(csv_filename, index=False, encoding='utf-8')

print(f"Manga details saved to {csv_filename}")