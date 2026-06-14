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
        page.wait_for_timeout(8000)

        # wait for table to actually render
        page.wait_for_selector("text=champ", timeout=60000)

        rows = page.query_selector_all("tr")

        data = []

        for r in rows:
            text = r.inner_text()

            # skip header rows
            if "champ" in text.lower() and "%" not in text:
                continue

            cols = r.query_selector_all("td")
            if len(cols) < 2:
                continue

            try:
                # TEAM NAME (first column)
                team_raw = cols[0].inner_text().strip()

                # remove "team logo" prefix if present
                team = re.sub(r"team\s*logo", "", team_raw, flags=re.I).strip()

                # LAST COLUMN = champ %
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

        # safety cleanup: remove duplicates if any
        df = df.groupby(["date", "team"], as_index=False).mean()

        return df
