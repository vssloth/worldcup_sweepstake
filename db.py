import os
import sqlite3
import pandas as pd

DB_PATH = os.path.join(os.path.dirname(__file__), "data.db")


# ============================
# PREDICTIONS
# ============================
def ensure_table_exists():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS predictions (
        date TEXT,
        team TEXT,
        champ REAL
    )
    """)

    conn.commit()
    conn.close()


def insert_predictions(df):
    ensure_table_exists()

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    snapshot_date = df["date"].iloc[0]

    cur.execute("""
        DELETE FROM predictions
        WHERE date = ?
    """, (snapshot_date,))

    rows = df[["date", "team", "champ"]].values.tolist()

    cur.executemany("""
        INSERT INTO predictions (date, team, champ)
        VALUES (?, ?, ?)
    """, rows)

    conn.commit()
    conn.close()


def load_predictions():
    ensure_table_exists()

    conn = sqlite3.connect(DB_PATH)

    df = pd.read_sql_query("""
        SELECT date, team, champ
        FROM predictions
    """, conn)

    conn.close()
    return df


# ============================
# FIXTURES (MISSING BEFORE)
# ============================
def ensure_fixtures_table():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS fixtures (
        date TEXT,
        home_team TEXT,
        away_team TEXT,
        home_win REAL,
        draw REAL,
        away_win REAL
    )
    """)

    conn.commit()
    conn.close()


def insert_fixtures(df):
    ensure_fixtures_table()

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    snapshot_date = df["date"].iloc[0]

    cur.execute("""
        DELETE FROM fixtures
        WHERE date = ?
    """, (snapshot_date,))

    rows = df[
        ["date", "home_team", "away_team", "home_win", "draw", "away_win"]
    ].values.tolist()

    cur.executemany("""
        INSERT INTO fixtures
        VALUES (?, ?, ?, ?, ?, ?)
    """, rows)

    conn.commit()
    conn.close()


def load_fixtures():
    ensure_fixtures_table()

    conn = sqlite3.connect(DB_PATH)

    df = pd.read_sql_query("""
        SELECT date, home_team, away_team, home_win, draw, away_win
        FROM fixtures
    """, conn)

    conn.close()
    return df
