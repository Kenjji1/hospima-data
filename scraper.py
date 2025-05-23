import requests
from bs4 import BeautifulSoup
import json

URL = "https://www.indexsante.ca/urgences/montreal.php"
headers = {
    "User-Agent": "Mozilla/5.0"
}

res = requests.get(URL, headers=headers)
soup = BeautifulSoup(res.content, "html.parser")

hopitaux = []

for table in soup.select("table"):
    for row in table.select("tbody tr"):
        cols = row.find_all("td")
        if len(cols) >= 5:
            hopital = {
                "nom": cols[0].get_text(strip=True),
                "taux_occupation": cols[2].get_text(strip=True),
                "attente_moyenne": cols[4].get_text(strip=True)
            }
            hopitaux.append(hopital)

with open("urgences.json", "w", encoding="utf-8") as f:
    json.dump(hopitaux, f, ensure_ascii=False, indent=2)

print(f"{len(hopitaux)} hôpitaux scrappés.")
