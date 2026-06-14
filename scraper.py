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
import requests
import pandas as pd
from datetime import datetime


PREDICTIONS_URL = "https://theanalyst.com/competition/fifa-world-cup/predictions"


def scrape_opta_predictions():
    session = requests.Session()

    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept": "application/json, text/plain, */*",
        "Referer": PREDICTIONS_URL
    }

    # -----------------------------------------------------
    # TRY LIKELY API ENDPOINTS (THE ANALYST VARIANTS)
    # -----------------------------------------------------
    candidate_urls = [
        "https://theanalyst.com/api/predictions",
        "https://theanalyst.com/api/competition/fifa-world-cup/predictions",
        "https://theanalyst.com/api/v1/predictions",
        "https://theanalyst.com/_next/data/predictions.json",
    ]

    data = None

    for url in candidate_urls:
        try:
            r = session.get(url, headers=headers, timeout=20)
            if r.status_code == 200:
                try:
                    data = r.json()
                    print(f"DEBUG: working API found -> {url}")
                    break
                except Exception:
                    continue
        except Exception:
            continue

    if not data:
        raise ValueError("No valid predictions API found")

    # -----------------------------------------------------
    # NORMALISE OUTPUT (HANDLES MULTIPLE SHAPES)
    # -----------------------------------------------------
    rows = []
    today = datetime.utcnow().date().isoformat()

    # CASE 1: list of teams
    if isinstance(data, list):
        for item in data:
            rows.append({
                "date": today,
                "team": item.get("team") or item.get("name"),
                "champ": float(item.get("champ") or item.get("winProb") or 0)
            })

    # CASE 2: nested dict
    elif isinstance(data, dict):
        # common patterns
        for key in ["teams", "predictions", "data"]:
            if key in data and isinstance(data[key], list):
                for item in data[key]:
                    rows.append({
                        "date": today,
                        "team": item.get("team") or item.get("name"),
                        "champ": float(item.get("champ") or item.get("winProb") or 0)
                    })
                break

    df = pd.DataFrame(rows)

    print(f"DEBUG: parsed prediction rows = {len(df)}")

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
