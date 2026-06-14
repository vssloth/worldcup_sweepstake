from scraper import scrape_opta_predictions
from db import insert_predictions

if __name__ == "__main__":
    df = scrape_opta_predictions()

    # DEBUG (important while fixing)
    print("ROWS:", len(df))
    print(df.head(10))

    insert_predictions(df)

    print("Predictions updated successfully")
