import asyncio
from playwright.async_api import async_playwright
import json

async def run():
    url = "https://www.indexsante.ca/urgences/montreal.php"
    hopitaux = []

    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        await page.goto(url)
        await page.wait_for_selector("table tbody tr")

        rows = await page.query_selector_all("table tbody tr")
        for row in rows:
            cols = await row.query_selector_all("td")
            if len(cols) >= 5:
                nom = (await cols[0].inner_text()).strip()
                taux_occupation = (await cols[2].inner_text()).strip()
                attente_moyenne = (await cols[4].inner_text()).strip()
                hopitaux.append({
                    "nom": nom,
                    "taux_occupation": taux_occupation,
                    "attente_moyenne": attente_moyenne
                })

        await browser.close()

    with open("urgences.json", "w", encoding="utf-8") as f:
        json.dump(hopitaux, f, ensure_ascii=False, indent=2)

asyncio.run(run())
