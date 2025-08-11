import asyncio
from playwright.async_api import async_playwright
import json
from datetime import datetime

# Charger le mapping nom -> id depuis hospitals.json
with open("hospitals.json", "r", encoding="utf-8") as f:
    hospitals_data = json.load(f)
hospital_id_map = {h["name"]: h["id"] for h in hospitals_data}

async def run():
    url = "https://www.indexsante.ca/urgences/montreal.php"
    waittimes = []

    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        await page.goto(url, timeout=60000)
        await page.wait_for_timeout(8000)

        rows = await page.query_selector_all("table tr")
        for row in rows:
            cols = await row.query_selector_all("td")
            if len(cols) >= 5:
                nom = (await cols[0].inner_text()).strip()
                attente_str = (await cols[4].inner_text()).strip()

                # Convertir en minutes
                minutes = None
                try:
                    if "h" in attente_str:
                        parts = attente_str.replace("min", "").replace("h", "h ").split()
                        h = int(parts[0])
                        m = int(parts[2]) if len(parts) > 2 else 0
                        minutes = h * 60 + m
                    else:
                        minutes = int(attente_str)
                except:
                    continue

                if nom in hospital_id_map:
                    waittimes.append({
                        "hospitalId": hospital_id_map[nom],
                        "waitMinutes": minutes,
                        "updatedAt": datetime.utcnow().isoformat() + "Z"
                    })

        await browser.close()

    with open("waittimes.json", "w", encoding="utf-8") as f:
        json.dump(waittimes, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    asyncio.run(run())
