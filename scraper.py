import asyncio, json, re, unicodedata
from datetime import datetime, timezone
from difflib import get_close_matches
from pathlib import Path
from playwright.async_api import async_playwright

HOSPITALS_JSON = Path("hospitals.json")
WAITTIMES_JSON = Path("waittimes.json")
DEBUG_JSON = Path("scrape_debug.json")
URL = "https://www.indexsante.ca/urgences/montreal.php"

# --- utils ---
def norm(s: str) -> str:
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode("ascii")
    return re.sub(r"\s+", " ", s).strip().lower()

def parse_minutes(txt: str):
    t = txt.lower().strip()
    if not t or t in {"-", "n/d", "n.a.", "na"}:
        return None
    t = t.replace("heures", "h").replace("heure", "h").replace("min.", "min").replace("minutes", "min")
    # formes possibles: "1 h 15", "2h", "45 min", "1h15", "75"
    m = re.match(r"^\s*(\d+)\s*h(?:\s*(\d+))?\s*$", t)
    if m:
        h = int(m.group(1))
        mm = int(m.group(2) or 0)
        return h * 60 + mm
    m = re.match(r"^\s*(\d+)\s*min\s*$", t)
    if m:
        return int(m.group(1))
    if t.isdigit():
        return int(t)
    return None

async def scrape_rows():
    out = []
    async with async_playwright() as p:
        browser = await p.chromium.launch(args=["--no-sandbox","--disable-setuid-sandbox"])
        page = await browser.new_page(user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome Safari")
        await page.goto(URL, timeout=60000, wait_until="domcontentloaded")
        await page.wait_for_timeout(4000)

        # récupérer toutes les lignes d'un tableau
        rows = await page.query_selector_all("table tr")
        for row in rows:
            cols = await row.query_selector_all("td")
            if len(cols) < 5:
                continue
            name = (await cols[0].inner_text()).strip()
            occ  = (await cols[2].inner_text()).strip()
            wait = (await cols[4].inner_text()).strip()
            out.append({"name_raw": name, "occupation_raw": occ, "wait_raw": wait})
        await browser.close()
    return out

def build_id_map(hospitals):
    # { normalized_name: (id, original_name) }
    m = {}
    for h in hospitals:
        m[norm(h["name"])] = (h["id"], h["name"])
    return m

# Aliases manuels (si besoin) -> "nom vu sur IndexSanté": "nom de ton hospitals.json"
ALIASES = {
    # "hopital du sacre-coeur de montreal": "L'Hôpital général juif Sir Mortimer B. Davis"  # exemple fictif, à adapter
}

async def run():
    # 1) charger tes hôpitaux
    if not HOSPITALS_JSON.exists():
        raise FileNotFoundError("hospitals.json introuvable à la racine du repo")
    hospitals = json.loads(HOSPITALS_JSON.read_text(encoding="utf-8"))
    id_map = build_id_map(hospitals)
    names_norm = list(id_map.keys())

    # 2) scraper brut
    raw = await scrape_rows()
    DEBUG_JSON.write_text(json.dumps(raw, ensure_ascii=False, indent=2), encoding="utf-8")

    results = []
    now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    for row in raw:
        name_raw = row["name_raw"].strip()
        wait_raw = row["wait_raw"].strip()
        minutes = parse_minutes(wait_raw)
        if minutes is None:
            continue

        key = norm(name_raw)
        # alias direct ?
        if key in ALIASES:
            key = norm(ALIASES[key])

        # match exact
        if key in id_map:
            hid = id_map[key][0]
        else:
            # fuzzy: chercher le plus proche dans ta liste
            cand = get_close_matches(key, names_norm, n=1, cutoff=0.72)
            if cand:
                hid = id_map[cand[0]][0]
            else:
                # pas de match -> on ignore, mais on le laisse dans debug
                continue

        results.append({
            "hospitalId": hid,
            "waitMinutes": minutes,
            "updatedAt": now
        })

    WAITTIMES_JSON.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")

if __name__ == "__main__":
    asyncio.run(run())
