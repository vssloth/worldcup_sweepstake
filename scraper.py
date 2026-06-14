from playwright.sync_api import sync_playwright
import pandas as pd
from datetime import datetime
import re


URL = "https://theanalyst.com/competition/fifa-world-cup/predictions"


def scrape_opta_predictions():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        page.goto(URL, timeout=60000)

        # ✅ wait for ANY table rows instead of fake "champ" text
        page.wait_for_selector("tr", timeout=60000)

        # give React time to hydrate table values
        page.wait_for_timeout(8000)

        rows = page.query_selector_all("tr")

        data = []

        for r in rows:
            cols = r.query_selector_all("td")

            if len(cols) < 2:
                continue

            try:
                # team name (clean logo prefix)
                team_raw = cols[0].inner_text().strip()
                team = re.sub(r"team\s*logo", "", team_raw, flags=re.I).strip()

                # last column = champion %
                champ_text = cols[-1].inner_text().strip().replace("%", "")
                champ = float(champ_text)

                data.append({
                    "date": datetime.utcnow().date().isoformat(),
                    "team": team,
                    "champ": champ
                })

            except:
                continue

        browser.close()

        df = pd.DataFrame(data)

        if df.empty:
            raise ValueError("Scraper returned no data")

        return df
