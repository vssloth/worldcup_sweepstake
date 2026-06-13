import os

import streamlit as st
import pandas as pd
import plotly.express as px

from db import load_predictions, ensure_table_exists


# ----------------------------
# SETUP
# ----------------------------
st.set_page_config(page_title="World Cup Sweepstake", layout="wide")

ensure_table_exists()


# ----------------------------
# LOAD DATA
# ----------------------------
df = load_predictions()

if df.empty:
    st.warning("No prediction data available yet.")
    st.stop()


# ----------------------------
# DATES
# ----------------------------
latest_date = sorted(df["date"].unique())[-1]


def get_previous_date(df, latest_date):
    dates = sorted(df["date"].unique())
    idx = dates.index(latest_date)
    return dates[idx - 1] if idx > 0 else latest_date


previous_date = get_previous_date(df, latest_date)

latest_df = df[df["date"] == latest_date]
prev_df = df[df["date"] == previous_date]


# ----------------------------
# PLAYERS (WORLD CUP)
# ----------------------------
PLAYERS = {
    "Miles": ["Argentina", "Iraq", "Iran", "England"],
    "James": ["New Zealand", "Algeria", "Haiti", "Brazil"],
    "Henry": ["France", "South Africa", "Côte d'Ivoire", "Paraguay"],
    "Maggie": ["Curaçao", "Senegal", "Switzerland", "Australia"],
    "Simy": ["Ghana", "Sweden", "Belgium", "Norway"],
    "Fiona": ["Spain", "Colombia", "Portugal", "Morocco"],
    "Helen": ["Croatia", "Congo DR", "Panama", "Bosnia"],
    "Dan": ["Egypt", "Korea Rep", "Ecuador", "Uzbekistan"],
    "Anne": ["Austria", "Germany", "Saudi Arabia", "Czechia"],
    "Rich": ["Cabo Verde", "Mexico", "Japan", "Tunisia"],
    "Grandma": ["Türkiye", "Scotland", "Netherlands", "Canada"],
    "Janet": ["United States", "Jordan", "Uruguay", "Qatar"]
}


# =========================================================
# STORM CUP DATA (IMPORT INSIDE TO AVOID BREAKING APP START)
# =========================================================
@st.cache_data(ttl=3600)
def load_stormcup_data():
    import requests

    API_KEY = st.secrets["FOOTBALL_DATA_API_KEY"]

    headers = {"X-Auth-Token": API_KEY}

    url = "https://api.football-data.org/v4/competitions/WC/matches"

    r = requests.get(url, headers=headers)
    r.raise_for_status()

    data = r.json()

    rows = []

    for m in data["matches"]:
        rows.append({
            "date": pd.to_datetime(m["utcDate"]).date(),
            "stage": m["stage"],
            "status": m["status"],
            "home_team": m["homeTeam"]["name"],
            "away_team": m["awayTeam"]["name"],
            "home_score": m["score"]["fullTime"]["home"],
            "away_score": m["score"]["fullTime"]["away"],
            "winner": m["score"]["winner"]
        })

    return pd.DataFrame(rows)


# ----------------------------
# STORM CUP SCORING (SIMPLE VERSION FROM YOUR ORIGINAL)
# ----------------------------
TEAM_NAME_MAP = {
    "Korea Rep": "Korea Republic",
    "South Korea": "Korea Republic",

    "USA": "United States",
    "United States of America": "United States",

    "Czechia": "Czech Republic",
    "Czech Republic": "Czech Republic",

    "Turkey": "Türkiye",
    "Türkiye": "Türkiye",

    "Congo DR": "DR Congo",
    "DR Congo": "DR Congo",

    "Ivory Coast": "Côte d'Ivoire",

    "Cape Verde": "Cabo Verde",

    "Curacao": "Curaçao",

    # 🔥 IMPORTANT FIXES FOR YOUR BUGS
    "Bosnia": "Bosnia and Herzegovina",
    "Bosnia-Herzegovina": "Bosnia and Herzegovina",

    "Korea Republic": "Korea Republic",
}

def normalise(team):
    return TEAM_NAME_MAP.get(team, team)

TEAM_OWNERS = {
    "Argentina": "Daniel",
    "Portugal": "Daniel",
    "Colombia": "Daniel",
    "Switzerland": "Daniel",
    "Croatia": "Daniel",
    "Senegal": "Daniel",
    "Egypt": "Daniel",
    "Algeria": "Daniel",
    "Côte d'Ivoire": "Daniel",
    "Qatar": "Daniel",
    "Saudi Arabia": "Daniel",
    "New Zealand": "Daniel",

    "Spain": "Helen",
    "Netherlands": "Helen",
    "Belgium": "Helen",
    "Japan": "Helen",
    "Mexico": "Helen",
    "Sweden": "Helen",
    "Korea Republic": "Helen",
    "Iran": "Helen",
    "Scotland": "Helen",
    "South Africa": "Helen",
    "Jordan": "Helen",
    "Haiti": "Helen",

    "France": "Maggie",
    "Brazil": "Maggie",
    "Morocco": "Maggie",
    "Uruguay": "Maggie",
    "United States": "Maggie",
    "Austria": "Maggie",
    "Canada": "Maggie",
    "Bosnia and Herzegovina": "Maggie",
    "Ghana": "Maggie",
    "Tunisia": "Maggie",
    "Uzbekistan": "Maggie",
    "Cabo Verde": "Maggie",

    "England": "James",
    "Germany": "James",
    "Norway": "James",
    "Ecuador": "James",
    "Türkiye": "James",
    "Paraguay": "James",
    "Australia": "James",
    "Czech Republic": "James",
    "Panama": "James",
    "Iraq": "James",
    "DR Congo": "James",
    "Curaçao": "James",
}

TEAM_OWNERS = {normalise(k): v for k, v in TEAM_OWNERS.items()}



# =========================
# STORM CUP SCORING ENGINE
# =========================

def compute_stormcup(df):

    players = {"Daniel": 0, "Helen": 0, "Maggie": 0, "James": 0}

    df = df[df["status"] == "FINISHED"].sort_values("date")

    for _, row in df.iterrows():

        home = normalise(row["home_team"])
        away = normalise(row["away_team"])

        home_pts = 0
        away_pts = 0

        # GROUP STAGE
        if row["stage"] == "GROUP_STAGE":
            if row["home_score"] > row["away_score"]:
                home_pts = 3
            elif row["away_score"] > row["home_score"]:
                away_pts = 3
            else:
                home_pts = away_pts = 1

        # KNOCKOUT
        else:
            if row["winner"] == "HOME_TEAM":
                home_pts = 3
            elif row["winner"] == "AWAY_TEAM":
                away_pts = 3

        for team, pts in [(home, home_pts), (away, away_pts)]:
            if team in TEAM_OWNERS:
                players[TEAM_OWNERS[team]] += pts

    return players


# =========================================================
# TABS
# =========================================================
tab1, tab2 = st.tabs([
    "🏆 World Cup Sweepstakes",
    "🌩️ Storm Cup"
])


# ----------------------------
# TAB 1 - WORLD CUP (UNCHANGED UI)
# ----------------------------
with tab1:

    st.title("🏆 Chance Of Winning")
    st.caption(f"Latest snapshot: {latest_date}")

    player_rows = []

    for player, teams in PLAYERS.items():

        current = latest_df[latest_df["team"].isin(teams)]["champ"].sum()
        previous = prev_df[prev_df["team"].isin(teams)]["champ"].sum()

        delta = current - previous

        if delta > 0:
            delta_html = f'<span style="color:green;">▲ {delta:.1f}%</span>'
        elif delta < 0:
            delta_html = f'<span style="color:red;">▼ {delta:.1f}%</span>'
        else:
            delta_html = f'<span style="color:gray;">• 0.0%</span>'

        team_html = "<br>".join([
            f"{t}: {latest_df[latest_df['team']==t]['champ'].values[0]:.1f}%"
            if t in latest_df["team"].values else f"{t}: 0.0%"
            for t in teams
        ])

        player_rows.append({
            "Rank": 0,
            "Player": player,
            "Chance of winning": current,
            "Change": delta_html,
            "Teams": team_html
        })

    player_df = pd.DataFrame(player_rows)

    player_df = player_df.sort_values(
        "Chance of winning",
        ascending=False
    ).reset_index(drop=True)

    player_df["Rank"] = player_df.index + 1

    player_df["Chance of winning"] = player_df["Chance of winning"].map(
        lambda x: f"{x:.1f}%"
    )

    html_table = player_df.to_html(index=False, escape=False)

    st.markdown(
        """
        <style>
        .block-container {
            max-width: 750px;
            padding-top: 3rem;
        }

        table {
            margin-left: auto;
            margin-right: auto;
            width: auto;
            font-size: 13px;
            border-collapse: collapse;
        }

        th {
            background-color: #111;
            color: white;
            text-align: center;
            padding: 6px;
            white-space: nowrap;
        }

        td {
            padding: 6px;
            vertical-align: top;
            white-space: nowrap;
        }

        tr:nth-child(even) {
            background-color: #f5f5f5;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    st.markdown(html_table, unsafe_allow_html=True)


    # ----------------------------
    # Trends (UNCHANGED)
    # ----------------------------
    st.subheader("Trends")

    trend_rows = []

    for date in sorted(df["date"].unique()):
        date_df = df[df["date"] == date]

        for player, teams in PLAYERS.items():
            total = date_df[date_df["team"].isin(teams)]["champ"].sum()

            trend_rows.append({
                "Date": date,
                "Player": player,
                "Chance": total
            })

    trend_df = pd.DataFrame(trend_rows)

    fig = px.line(
        trend_df,
        x="Date",
        y="Chance",
        color="Player",
        markers=True
    )

    st.plotly_chart(fig, use_container_width=True)


# ----------------------------
# TAB 2 - STORM CUP
# ----------------------------

with tab2:

    st.title("🌩️ Storm Cup Leaderboard")

    matches = load_stormcup_data()
    st.subheader("Raw API team names (debug)")

all_teams = sorted(
    set(matches["home_team"].dropna().unique())
    | set(matches["away_team"].dropna().unique())
)

st.write(all_teams)
    scores = compute_stormcup(matches)

    # ----------------------------
    # OWNER MAP (reverse)
    # ----------------------------
    owner_to_teams = {}
    for team, owner in TEAM_OWNERS.items():
        team = normalise(team)
        owner_to_teams.setdefault(owner, []).append(team)

    finished_matches = matches[matches["status"] == "FINISHED"]

    rows = []

    for player, points in scores.items():

        teams = owner_to_teams.get(player, [])

        team_strings = []

        for team in teams:

            team_matches = finished_matches[
                (finished_matches["home_team"] == team) |
                (finished_matches["away_team"] == team)
            ]

            played = len(team_matches)

            pts = 0

            for _, r in team_matches.iterrows():

                if r["stage"] == "GROUP_STAGE":
                    if r["home_team"] == team:
                        if r["home_score"] > r["away_score"]:
                            pts += 3
                        elif r["home_score"] == r["away_score"]:
                            pts += 1
                    else:
                        if r["away_score"] > r["home_score"]:
                            pts += 3
                        elif r["home_score"] == r["away_score"]:
                            pts += 1

                else:
                    if r["winner"] == "HOME_TEAM" and r["home_team"] == team:
                        pts += 3
                    elif r["winner"] == "AWAY_TEAM" and r["away_team"] == team:
                        pts += 3

            team_strings.append(f"{team} ({pts} pts, played {played})")

        rows.append({
            "Player": player,
            "Points": points,
            "Teams": "<br>".join(team_strings)
        })

    df_sc = pd.DataFrame(rows)

    df_sc = df_sc.sort_values("Points", ascending=False).reset_index(drop=True)

    html_table = df_sc.to_html(index=False, escape=False)

    st.markdown(
        """
        <style>
        .block-container {
            max-width: 750px;
            padding-top: 3rem;
        }

        table {
            margin-left: auto;
            margin-right: auto;
            width: auto;
            font-size: 13px;
            border-collapse: collapse;
        }

        th {
            background-color: #111;
            color: white;
            text-align: center;
            padding: 6px;
            white-space: nowrap;
        }

        td {
            padding: 6px;
            vertical-align: top;
            white-space: nowrap;
        }

        tr:nth-child(even) {
            background-color: #f5f5f5;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    st.markdown(html_table, unsafe_allow_html=True)
