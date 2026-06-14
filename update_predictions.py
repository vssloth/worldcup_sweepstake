# update_predictions.py

from model import generate_predictions   # whatever currently produces your predictions
from db import insert_predictions

df = generate_predictions()

insert_predictions(df)

print("Predictions updated")