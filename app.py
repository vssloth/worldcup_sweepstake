import os

import streamlit as st
import pandas as pd
import plotly.express as px

from db import load_predictions, load_fixtures, ensure_table_exists


# ----------------------------
# SETUP
# ----------------------------
st.set_page_config(page_title="World Cup Sweepstake", layout="wide")

ensure_table_exists()


# ----------------------------
# LOAD DATA
# ----------------------------
df = load_predictions()
fixtures_df = load_fixtures()

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
# PLAYERS
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


# ----------------------------
# TABS
# ----------------------------
tab1, tab2, tab3 = st.tabs([
    "Leaderboard",
    "Trends",
    "Fixtures"
])


with tab1:

    st.title("🏆 Chance Of Winning")
    st.caption(f"Latest snapshot: {latest_date}")

    player_rows = []

    for player, teams in PLAYERS.items():

        current = latest_df[latest_df["team"].isin(teams)]["champ"].sum()
        previous = prev_df[prev_df["team"].isin(teams)]["champ"].sum()

        delta = current - previous

        # coloured arrows (HTML)
        if delta > 0:
            delta_html = f'<span style="color:green;">▲ {delta:.1f}%</span>'
        elif delta < 0:
            delta_html = f'<span style="color:red;">▼ {delta:.1f}%</span>'
        else:
            delta_html = f'<span style="color:gray;">• 0.0%</span>'

        # team breakdown
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
            max-width: 750px;   /* 🔥 makes table narrow */
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
# TAB 2 - TRENDS
# ----------------------------
with tab2:

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
# TAB 3 - FIXTURES
# ----------------------------
with tab3:

    st.title("📅 Upcoming Fixtures")

    if fixtures_df.empty:
        st.info("No fixtures loaded yet.")
    else:
        st.dataframe(fixtures_df, use_container_width=True, hide_index=True)