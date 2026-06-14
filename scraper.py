import requests
import pandas as pd
from datetime import datetime
import json
import re

PRED_URL = "https://theanalyst.com/competition/fifa-world-cup/predictions"


def scrape_opta_predictions():
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept": "text/html,application/json",
    }

    r = requests.get(PRED_URL, headers=headers, timeout=30)
    r.raise_for_status()

    html = r.text

    # ---------------------------------------
    # METHOD 1: Try to find JSON in page
    # ---------------------------------------
    data = []

    json_candidates = re.findall(r'\{.*?\}', html)

    for candidate in json_candidates:
        try:
            obj = json.loads(candidate)

            # look for team + probability patterns
            if isinstance(obj, dict):

                # common patterns seen in Opta/Nuxt dumps
                if "team" in obj and ("champ" in obj or "winProbability" in obj):
                    team = obj.get("team")
                    champ = obj.get("champ") or obj.get("winProbability")

                    if team and champ is not None:
                        data.append({
                            "date": datetime.utcnow().date().isoformat(),
                            "team": team,
                            "champ": float(str(champ).replace("%", ""))
                        })

        except:
            continue

    # ---------------------------------------
    # METHOD 2: fallback regex table scrape
    # ---------------------------------------
    if not data:
        rows = re.findall(r'([A-Za-zÀ-ÿ .\'-]+)\s+([0-9]+(?:\.[0-9]+)?)%', html)

        for team, champ in rows:
            data.append({
                "date": datetime.utcnow().date().isoformat(),
                "team": team.strip(),
                "champ": float(champ)
            })

    df = pd.DataFrame(data)

    # ---------------------------------------
    # HARD FAIL SAFETY
    # ---------------------------------------
    if df.empty:
        raise ValueError("Scraper returned no data — site structure changed or blocked request")

    # cleanup duplicates if any
    df = df.groupby(["date", "team"], as_index=False).mean()

    return df
