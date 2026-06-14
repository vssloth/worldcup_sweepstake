import requests
import pandas as pd
from datetime import datetime
import json
import re

URL = "https://theanalyst.com/competition/fifa-world-cup/predictions"


def scrape_opta_predictions():
    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    r = requests.get(URL, headers=headers, timeout=30)
    r.raise_for_status()

    html = r.text

    # -------------------------------------------------------
    # STEP 1: Extract Next.js embedded JSON (MOST IMPORTANT)
    # -------------------------------------------------------
    match = re.search(
        r'__NEXT_DATA__\s*=\s*({.*?})\s*</script>',
        html,
        re.DOTALL
    )

    data = []

    if match:
        try:
            next_data = json.loads(match.group(1))

            # recursively search JSON for probabilities
            def walk(obj):
                if isinstance(obj, dict):

                    # common Opta pattern
                    if "name" in obj and ("championshipProbability" in obj or "champ" in obj):
                        team = obj.get("name")
                        champ = obj.get("championshipProbability") or obj.get("champ")

                        if team and champ is not None:
                            data.append({
                                "date": datetime.utcnow().date().isoformat(),
                                "team": team,
                                "champ": float(str(champ).replace("%", ""))
                            })

                    for v in obj.values():
                        walk(v)

                elif isinstance(obj, list):
                    for i in obj:
                        walk(i)

            walk(next_data)

        except Exception as e:
            print("Next.js parse failed:", e)

    # -------------------------------------------------------
    # STEP 2: fallback JSON-in-page scan (backup)
    # -------------------------------------------------------
    if not data:
        json_blocks = re.findall(r'\{[^{}]*"name"[^{}]*\}', html)

        for block in json_blocks:
            try:
                obj = json.loads(block)
                if "name" in obj and "champ" in obj:
                    data.append({
                        "date": datetime.utcnow().date().isoformat(),
                        "team": obj["name"],
                        "champ": float(str(obj["champ"]).replace("%", ""))
                    })
            except:
                continue

    df = pd.DataFrame(data)

    # -------------------------------------------------------
    # HARD FAIL SAFETY
    # -------------------------------------------------------
    if df.empty:
        raise ValueError("Scraper returned no data — site structure changed")

    # clean duplicates
    df = df.groupby(["date", "team"], as_index=False).mean()

    return df
