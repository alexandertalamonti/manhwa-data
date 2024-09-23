import requests
from bs4 import BeautifulSoup

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