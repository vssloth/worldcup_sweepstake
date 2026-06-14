from playwright.sync_api import sync_playwright
import pandas as pd
from datetime import datetime
import json


URL = "https://theanalyst.com/competition/fifa-world-cup/predictions"


def scrape_opta_predictions():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        captured = []

        def handle_response(response):
            try:
                url = response.url

                # 🎯 Narrow filter: only likely API calls
                if "prediction" in url.lower() or "world-cup" in url.lower():
                    data = response.json()

                    if isinstance(data, list):
                        captured.extend(data)

                    if isinstance(data, dict):
                        for key in ["teams", "data", "items", "results"]:
                            if key in data and isinstance(data[key], list):
                                captured.extend(data[key])

            except:
                pass

        page.on("response", handle_response)

        page.goto(URL, timeout=60000)
        page.wait_for_timeout(12000)

        browser.close()

        rows = []
        for item in captured:
            try:
                team = item.get("team") or item.get("name")
                champ = item.get("championshipProbability") or item.get("champ") or item.get("prob")

                if team is None or champ is None:
                    continue

                rows.append({
                    "date": datetime.utcnow().date().isoformat(),
                    "team": team,
                    "champ": float(str(champ).replace("%", ""))
                })

            except:
                continue

        df = pd.DataFrame(rows)

        print("DEBUG scraped rows:", len(df))
        return df


# ----------------------------
# FIXTURES SCRAPER (BASIC VERSION)
# ----------------------------
from playwright.sync_api import sync_playwright
import pandas as pd
from datetime import datetime


URL = "https://theanalyst.com/competition/fifa-world-cup/fixtures"


def scrape_fixtures():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        fixtures = []

        def handle_response(response):
            url = response.url

            # 🔥 THIS is the key: capture JSON API calls
            if "fixture" in url or "match" in url:
                try:
                    data = response.json()

                    # structure varies, so we safely inspect it
                    if isinstance(data, list):
                        for m in data:
                            fixtures.append(m)

                    if isinstance(data, dict) and "matches" in data:
                        fixtures.extend(data["matches"])

                except:
                    pass

        page.on("response", handle_response)

        page.goto(URL, timeout=60000)
        page.wait_for_timeout(12000)

        browser.close()

        # ----------------------------
        # fallback normalized output
        # ----------------------------
        rows = []

        for f in fixtures:
            try:
                rows.append({
                    "date": datetime.utcnow().date().isoformat(),
                    "home_team": f.get("homeTeam", {}).get("name", "TBD"),
                    "away_team": f.get("awayTeam", {}).get("name", "TBD"),
                    "home_win": f.get("probabilities", {}).get("homeWin", 0),
                    "draw": f.get("probabilities", {}).get("draw", 0),
                    "away_win": f.get("probabilities", {}).get("awayWin", 0),
                })
            except:
                continue

        return pd.DataFrame(rows)
