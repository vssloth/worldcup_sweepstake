from playwright.sync_api import sync_playwright
import pandas as pd
from datetime import datetime
import requests


# =========================================================
# CONFIG
# =========================================================
PREDICTIONS_URL = "https://theanalyst.com/competition/fifa-world-cup/predictions"
FIXTURES_URL = "https://theanalyst.com/competition/fifa-world-cup/fixtures"


# =========================================================
# PREDICTIONS SCRAPER (ROBUST DOM VERSION)
# =========================================================
def scrape_opta_predictions():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        print("Loading predictions page...")
        page.goto(PREDICTIONS_URL, timeout=60000)

        # wait for JS rendering
        page.wait_for_timeout(12000)
        page.wait_for_load_state("networkidle")

        rows = page.query_selector_all("tr")

        print(f"DEBUG: found {len(rows)} table rows")

        data = []

        for r in rows:
            cols = r.query_selector_all("td")

            # relaxed condition (important fix)
            if len(cols) < 2:
                continue

            try:
                team = cols[0].inner_text().strip()
                champ_text = cols[-1].inner_text().strip().replace("%", "")
                champ = float(champ_text)

                data.append({
                    "date": datetime.utcnow().date().isoformat(),
                    "team": team,
                    "champ": champ
                })

            except Exception:
                continue

        browser.close()

        df = pd.DataFrame(data)

        print(f"DEBUG: scraped prediction rows = {len(df)}")

        return df


# =========================================================
# FIXTURES SCRAPER (API LISTENER VERSION)
# =========================================================
def scrape_fixtures():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        fixtures = []

        def handle_response(response):
            url = response.url

            if "match" in url or "fixture" in url:
                try:
                    data = response.json()

                    if isinstance(data, list):
                        fixtures.extend(data)

                    elif isinstance(data, dict) and "matches" in data:
                        fixtures.extend(data["matches"])

                except Exception:
                    pass

        page.on("response", handle_response)

        print("Loading fixtures page...")
        page.goto(FIXTURES_URL, timeout=60000)
        page.wait_for_timeout(12000)

        browser.close()

        rows = []

        for f in fixtures:
            try:
                rows.append({
                    "date": datetime.utcnow().date().isoformat(),
                    "home_team": f.get("homeTeam", {}).get("name", ""),
                    "away_team": f.get("awayTeam", {}).get("name", ""),
                    "home_win": f.get("probabilities", {}).get("homeWin", 0),
                    "draw": f.get("probabilities", {}).get("draw", 0),
                    "away_win": f.get("probabilities", {}).get("awayWin", 0),
                })
            except Exception:
                continue

        df = pd.DataFrame(rows)

        print(f"DEBUG: scraped fixture rows = {len(df)}")

        return df


# =========================================================
# OPTIONAL: API FALLBACK (RECOMMENDED SAFETY NET)
# =========================================================
def scrape_opta_predictions_api_fallback():
    """
    If DOM scraping breaks again, this is your backup path.
    You must inspect Network tab once to get real endpoint.
    """
    try:
        url = "https://theanalyst.com/api/predictions"  # placeholder
        r = requests.get(url, timeout=30)
        r.raise_for_status()

        data = r.json()

        rows = []
        for item in data.get("teams", []):
            rows.append({
                "date": datetime.utcnow().date().isoformat(),
                "team": item["name"],
                "champ": float(item["champWin"])
            })

        return pd.DataFrame(rows)

    except Exception:
        return pd.DataFrame()
