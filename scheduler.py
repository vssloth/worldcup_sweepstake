from apscheduler.schedulers.blocking import BlockingScheduler
from datetime import datetime
import pytz

from scraper import scrape_opta_predictions
from db import insert_predictions


def job():
    print("Running 8am Opta refresh:", datetime.now())

    df = scrape_opta_predictions()
    insert_predictions(df)

    print("Update complete:", len(df), "rows")


scheduler = BlockingScheduler(timezone=pytz.timezone("Europe/London"))

# 8am every day
scheduler.add_job(job, 'cron', hour=8, minute=0)

print("Scheduler started... waiting for 8am job")
scheduler.start()