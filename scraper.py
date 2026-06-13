from playwright.sync_api import sync_playwright
import pandas as pd
from datetime import datetime

from db import insert_predictions, insert_fixtures


URL = "https://theanalyst.com/competition/fifa-world-cup/predictions"


# ----------------------------
# TEAM CHAMPIONSHIP PROBS
# ----------------------------
def scrape_opta_predictions():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        page.goto(URL, timeout=60000)
        page.wait_for_timeout(8000)

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
        return pd.DataFrame(data)


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