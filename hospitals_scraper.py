import csv
import io
import json
import requests

URL = "https://www.donneesquebec.ca/recherche/dataset/51998b55-7d4c-4381-8c20-0ac1cd9c1b87/resource/2aa06e66-c1d0-4e2f-bf3c-c2e413c3f84d/download/installationscsv.csv"


def fetch_hospitals():
    resp = requests.get(URL, timeout=60)
    resp.raise_for_status()
    content = resp.content.decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(content))
    hospitals = []
    for row in reader:
        if row.get("CHSGS", "").strip().lower() == "oui":
            try:
                lon = float(row["LONGITUDE"])
                lat = float(row["LATITUDE"])
            except ValueError:
                continue
            hospitals.append({
                "nom": row["INSTAL_NOM"].strip(),
                "longitude": lon,
                "latitude": lat
            })
    return hospitals


def main():
    hospitals = fetch_hospitals()
    with open("hospitals_qc.json", "w", encoding="utf-8") as f:
        json.dump(hospitals, f, ensure_ascii=False, indent=2)
    print(f"Wrote {len(hospitals)} hospitals to hospitals_qc.json")


if __name__ == "__main__":
    main()
