import pandas as pd
from db import insert_predictions

# Example: replace this with your real logic / data source
def generate_predictions():
    # MUST return columns: date, team, champ
    data = [
        # example rows (replace with real model output)
        {"date": "2026-06-14", "team": "Argentina", "champ": 18.2},
        {"date": "2026-06-14", "team": "England", "champ": 15.1},
    ]

    return pd.DataFrame(data)


if __name__ == "__main__":
    df = generate_predictions()
    insert_predictions(df)
    print("Predictions updated")
