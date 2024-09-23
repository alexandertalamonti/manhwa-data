import requests
from bs4 import BeautifulSoup
import time
from urllib.parse import quote
from dotenv import load_dotenv
import os
import re
import pandas as pd
import json

url = "https://www.animenewsnetwork.com/encyclopedia/ratings-manga.php?top50=most_underrated&n=500"
titles = []
page = 1

res = requests.get(url)
soup = BeautifulSoup(res.content, 'html.parser')

table = soup.find('table', class_='encyc-ratings')

if table:
    tds = table.find_all('td', class_='t')
    for td in tds:
        a = td.find('a')
        if a:
            title = a.text.strip()
            titles.append(title)

# Save titles to file
with open("top_500_underrated_manga.txt", "w", encoding="utf-8") as file:
    for i, title in enumerate(titles, 1):
        file.write(f"{title}\n")

print(f"Saved {len(titles)} titles to top_500_underrated_manga.txt")


# START OF GET MANGA IDS

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

# START OF GENERAL MAL CSV

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

# Clean the data!
print("Cleaning data")
# Drop some unnecessary columns first
manga_df = manga_df.drop('pictures', axis=1)
manga_df = manga_df.drop('recommendations', axis=1)
manga_df = manga_df.drop('serialization', axis=1)
manga_df = manga_df.drop('related_anime', axis=1)

# Get genre names from arrays
def extract_genre_names(genres_json):
  genres_list = json.loads(genres_json)
  return [genre['name'] for genre in genres_list]

manga_df['genres'] = manga_df['genres'].apply(extract_genre_names)

# Get author names from arrays
def extract_author_names(authors_json):
    authors_list = json.loads(authors_json)
    return [f"{author['node']['first_name']} {author['node']['last_name']}".strip() for author in authors_list]

manga_df['authors'] = manga_df['authors'].apply(extract_author_names)

# Get related manga titles from arrays
def extract_related_manga_titles(related_manga_json):
    related_manga_list = json.loads(related_manga_json)
    return [manga['node']['title'] for manga in related_manga_list]

manga_df['related_manga'] = manga_df['related_manga'].apply(extract_related_manga_titles)

# Save to CSV

manga_df.to_csv("manga_details.csv", index=False, encoding='utf-8')

print("Manga details saved to manga_details.csv")