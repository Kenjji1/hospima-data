import requests
from bs4 import BeautifulSoup
import json

url = "https://www.indexsante.ca/urgences/montreal.php"
headers = {
    "User-Agent": "Mozilla/5.0"
}

res = requests.get(url, headers=headers)
soup = BeautifulSoup(res.content, "html.parser")

hopitaux = []

for row in soup.select("tr"):
    cols = row.find_all("td")
    if len(cols) >= 5:
        hopitaux.append({
            "hopital": cols[0].text.strip(),
            "attente": cols[1].text.strip(),
            "en_attente": cols[2].text.strip(),
            "total": cols[3].text.strip(),
            "occupation": cols[4].text.strip()
        })

with open("urgences.json", "w", encoding="utf-8") as f:
    json.dump(hopitaux, f, ensure_ascii=False, indent=2)
