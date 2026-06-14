from playwright.sync_api import sync_playwright
import pandas as pd
from datetime import datetime


# =========================================================
# PREDICTIONS SCRAPER (WORKING DOM VERSION)
# =========================================================

PREDICTIONS_URL = "https://theanalyst.com/competition/fifa-world-cup/predictions"


def scrape_opta_predictions():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        page.goto(PREDICTIONS_URL, timeout=60000)

        # Wait for table to exist (more stable than sleep)
        page.wait_for_selector("tr", timeout=30000)

        rows = page.query_selector_all("tr")

        data = []

        for r in rows:
            cols = r.query_selector_all("td")

            if len(cols) < 3:
                continue

            team = cols[0].inner_text().strip()
            champ_text = cols[-1].inner_text().strip().replace("%", "")

            try:
                champ = float(champ_text)
            except:
                continue

            data.append({
                "date": datetime.utcnow().date().isoformat(),
                "team": team,
                "champ": champ
            })

        browser.close()

        df = pd.DataFrame(data)

        print(f"DEBUG scraped prediction rows: {len(df)}")

        return df


# =========================================================
# FIXTURES SCRAPER (ROBUST NETWORK INTERCEPT VERSION)
# =========================================================

FIXTURES_URL = "https://theanalyst.com/competition/fifa-world-cup/fixtures"


def scrape_fixtures():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        fixtures = []

        def handle_response(response):
            url = response.url

            # capture any football-related API payloads
            if "match" in url or "fixture" in url:
                try:
                    data = response.json()

                    if isinstance(data, list):
                        fixtures.extend(data)

                    elif isinstance(data, dict):
                        if "matches" in data:
                            fixtures.extend(data["matches"])
                        elif "fixtures" in data:
                            fixtures.extend(data["fixtures"])

                except:
                    pass

        page.on("response", handle_response)

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
            except:
                continue

        df = pd.DataFrame(rows)

        print(f"DEBUG scraped fixture rows: {len(df)}")

        return df
