from scraper import scrape_opta_predictions
from db import insert_predictions

if __name__ == "__main__":
    df = scrape_opta_predictions()

    if df.empty:
        raise ValueError("No predictions returned")

    insert_predictions(df)
    print(f"Inserted {len(df)} rows")
