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

    try:
        r = requests.get(url, headers=headers, timeout=20)
        r.raise_for_status()
        data = r.json()
    except Exception as e:
        st.warning(f"Football API temporarily unavailable: {e}")
        return pd.DataFrame(columns=[
            "match_id", "date", "stage", "status",
            "home_team", "away_team", "home_score", "away_score", "winner"
        ])

    rows = []

    for m in data.get("matches", []):
        rows.append({
            "match_id": m.get("id"),
            "date": pd.to_datetime(m["utcDate"]).date(),
            "stage": m.get("stage"),
            "status": m.get("status"),
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

TEAM_OWNERS = {
    "Argentina": "Daniel",
    "Portugal": "Daniel",
    "Colombia": "Daniel",
    "Switzerland": "Daniel",
    "Croatia": "Daniel",
    "Senegal": "Daniel",
    "Egypt": "Daniel",
    "Algeria": "Daniel",
    "Ivory Coast": "Daniel",
    "Qatar": "Daniel",
    "Saudi Arabia": "Daniel",
    "New Zealand": "Daniel",

    "Spain": "Helen",
    "Netherlands": "Helen",
    "Belgium": "Helen",
    "Japan": "Helen",
    "Mexico": "Helen",
    "Sweden": "Helen",
    "South Korea": "Helen",
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
    "Bosnia-Herzegovina": "Maggie",
    "Ghana": "Maggie",
    "Tunisia": "Maggie",
    "Uzbekistan": "Maggie",
    "Cape Verde Islands": "Maggie",

    "England": "James",
    "Germany": "James",
    "Norway": "James",
    "Ecuador": "James",
    "Turkey": "James",
    "Paraguay": "James",
    "Australia": "James",
    "Czechia": "James",
    "Panama": "James",
    "Iraq": "James",
    "Congo DR": "James",
    "Curaçao": "James",
}




def compute_stormcup(df):

    players = {"Daniel": 0, "Helen": 0, "Maggie": 0, "James": 0}

    df = df[df["status"] == "FINISHED"].sort_values("date")

    for _, row in df.iterrows():

        home = row["home_team"]
        away = row["away_team"]

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

        # assign to owners
        for team, pts in [(home, home_pts), (away, away_pts)]:
            if team in TEAM_OWNERS:
                players[TEAM_OWNERS[team]] += pts

    return players

import requests


# =========================================================
# TABS
# =========================================================
tab1, tab2, tab3, tab4 = st.tabs([
    "🏆 World Cup Sweepstakes",
    "💰 Bonus prizes",
    "⚽ Results so far",
    "😺 Storm Cup",
    
])


# ----------------------------
# TAB 1 - WORLD CUP (UNCHANGED UI)
# ----------------------------
with tab1:

    st.title("🏆 Chance Of Winning")
    st.write("Prizes:🥇£28, 🥈£5, 🥄£5 (first to have all 4 teams eliminated)")
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

        team_strings = []

        for t in teams:

            current_team = latest_df.loc[
                latest_df["team"] == t, "champ"
            ]

            previous_team = prev_df.loc[
                prev_df["team"] == t, "champ"
            ]

            current_val = (
                current_team.iloc[0]
                if len(current_team) > 0 else 0
            )

            previous_val = (
                previous_team.iloc[0]
                if len(previous_team) > 0 else 0
            )

            team_delta = current_val - previous_val

            if team_delta > 0:
                team_delta_html = (
                    f'<span style="color:green;">▲ {team_delta:.1f}%</span>'
                )
                
            elif team_delta < 0:
                team_delta_html = (
                    f'<span style="color:red;">▼ {abs(team_delta):.1f}%</span>'
                )
            else:
                team_delta_html = (
                    '<span style="color:gray;">• 0.0%</span>'
                )

            team_strings.append(
                f"{t}: {current_val:.1f}% ({team_delta_html})"
            )

        team_html = "<br>".join(team_strings)


        
        
        
        chance_html = f"{current:.1f}% ({delta_html})"

        player_rows.append({
            "Rank": 0,
            "Player": player,
            "_sort": current,
            "Chance of winning<br>(daily change)": chance_html,
            "Teams": team_html
        })
        

    player_df = pd.DataFrame(player_rows)

    player_df = player_df.sort_values(
        "_sort",
        ascending=False
    ).reset_index(drop=True)
    
    player_df["Rank"] = player_df.index + 1

    player_df = player_df.drop(columns=["_sort"])


    

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

    fig.update_layout(
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="center",
            x=0.5
        ),
        margin=dict(t=80)
    )

    st.plotly_chart(fig, use_container_width=True)

# ----------------------------
# TAB 2 - BONUSES
# ----------------------------

with tab2:
    
    subtab1, subtab2, subtab3, subtab4 = st.tabs([
        "🔹 Golden boot",
        "🔹 Golden glove",
        "🔹 Naughty list",
        "🔹 Cricket score"
    ])

    with subtab1:
        st.write("Top goalscorer (£10 prize)")
    
        import requests
        import pandas as pd
    
        # ----------------------------
        # TEAM OWNERS (Golden Boot version)
        # ----------------------------
        TEAM_OWNERS_GOLDEN = {
            "Argentina": "Maggie",
            "Portugal": "Helen",
            "Morocco": "Miles",
            "Croatia": "Fiona",
            "Spain": "Dan",
            "Netherlands": "Rich",
            "Belgium": "James",
            "France": "Henry",
            "Brazil": "Simy",
            "England": "Anne",
            "Germany": "Janet",
            "Norway": "Grandma",
        }
    
        DEFAULT_OWNER = "🐾 Holly"
    
        # ----------------------------
        # FETCH SCORERS
        # ----------------------------
        @st.cache_data(ttl=3600)
        def get_scorers():
            API_KEY = st.secrets["FOOTBALL_DATA_API_KEY"]
            headers = {"X-Auth-Token": API_KEY}
    
            url = "https://api.football-data.org/v4/competitions/WC/scorers"
    
            r = requests.get(url, headers=headers, timeout=20)
            r.raise_for_status()
    
            data = r.json()
    
            rows = []
    
            for s in data.get("scorers", []):
                player = s.get("player", {}).get("name")
                team = s.get("team", {}).get("name")
                goals = s.get("goals", 0)
    
                if goals and goals > 0:
                    rows.append({
                        "Player": player,
                        "Team": team,
                        "Goals": goals
                    })
    
            return pd.DataFrame(rows)
    
        df = get_scorers()
    
        if df.empty:
            st.warning("No Golden Boot data available yet.")
            st.stop()
    
        # ----------------------------
        # ADD OWNER COLUMN (FIXED ORDER)
        # ----------------------------
        df["Owner"] = df["Team"].apply(
            lambda x: TEAM_OWNERS_GOLDEN.get(x, DEFAULT_OWNER)
        )
    
        # ----------------------------
        # SORT
        # ----------------------------
        df = df.sort_values("Goals", ascending=False).reset_index(drop=True)
    

    
        # ----------------------------
        # WINNER LOGIC (EXCLUDE HOLLY)
        # ----------------------------
        non_holly = df[df["Owner"] != "🐾 Holly"]
        
        if not non_holly.empty:
            max_goals = non_holly["Goals"].max()
            winners = non_holly[non_holly["Goals"] == max_goals]
        
            # build inner player text
            player_text = ", ".join(
                f"{r['Player']} ({r['Team']})"
                for _, r in winners.iterrows()
            )
        
            # build owner list (could be multiple tied owners)
            owners = non_holly[non_holly["Goals"] == max_goals]["Owner"].unique()
            owner_text = ", ".join(owners)
        
            st.success(
                f"Current leader: **{owner_text}** ({player_text} with {max_goals} goals)"
            )
        else:
            st.info("No eligible (non-Holly) Golden Boot leaders yet.")

    
        # ----------------------------
        # TABLE OUTPUT (BELOW CAPTION + TITLE)
        # ----------------------------
        html_table = df.to_html(index=False, escape=False)
    
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
    with subtab2:

        st.write("Most clean sheets (£10 prize)")
        
        
        TEAM_OWNERS_GOLDEN = {
            "Argentina": "Maggie",
            "Portugal": "Helen",
            "Morocco": "Miles",
            "Croatia": "Fiona",
            "Spain": "Dan",
            "Netherlands": "Rich",
            "Belgium": "James",
            "France": "Henry",
            "Brazil": "Simy",
            "England": "Anne",
            "Germany": "Janet",
            "Norway": "Grandma",
        }
        
        matches = load_stormcup_data()
        
        finished = matches[
            matches["status"] == "FINISHED"
        ].copy()
        
        clean_sheets = {}
        
        for _, row in finished.iterrows():
        
            home_team = row["home_team"]
            away_team = row["away_team"]
        
            home_score = row["home_score"]
            away_score = row["away_score"]
        
            if pd.isna(home_score) or pd.isna(away_score):
                continue
        
            # Home clean sheet
            if away_score == 0:
                clean_sheets[home_team] = (
                    clean_sheets.get(home_team, 0) + 1
                )
        
            # Away clean sheet
            if home_score == 0:
                clean_sheets[away_team] = (
                    clean_sheets.get(away_team, 0) + 1
                )
        
        rows = []
        
        for team, cs in clean_sheets.items():
        
            owner = TEAM_OWNERS_GOLDEN.get(team, "🐾 Holly")
        
            rows.append({
                "Country": team,
                "Clean Sheets": cs,
                "Owner": owner
            })
        
        df_cs = pd.DataFrame(rows)

        # Find leading non-Holly entries
        
        non_holly = df_cs[df_cs["Owner"] != "🐾 Holly"]
        
        if not non_holly.empty:
        
            max_cs = non_holly["Clean Sheets"].max()
        
            leaders = non_holly[
                non_holly["Clean Sheets"] == max_cs
            ]
        
            leader_text = ", ".join(
                [
                    f"**{row['Owner']}** ({row['Country']})"
                    for _, row in leaders.iterrows()
                ]
            )
        
            st.success(
                f"Current leader{'s' if len(leaders) > 1 else ''}: "
                f"{leader_text} with {max_cs} clean sheet{'s' if max_cs != 1 else ''}"
            )
        
        if not df_cs.empty:
        
            df_cs = df_cs.sort_values(
                ["Clean Sheets", "Country"],
                ascending=[False, True]
            ).reset_index(drop=True)
        
            html_table = df_cs.to_html(
                index=False,
                escape=False
            )
        
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
        
            st.markdown(
                html_table,
                unsafe_allow_html=True
            )
        
        else:
            st.info("No clean sheets recorded yet.")
        
        


    with subtab3:
        st.write("Most red cards (£1,000,000 fine)")
        st.title("🔧 work in progress...")
    
        import pandas as pd
    
        TEAM_OWNERS_GOLDEN = {
            "Argentina": "Miles",
            "Portugal": "Helen",
            "Morocco": "Miles",
            "Croatia": "Fiona",
            "Spain": "Dan",
            "Netherlands": "Rich",
            "Belgium": "James",
            "France": "Henry",
            "Brazil": "Simy",
            "England": "Anne",
            "Germany": "Janet",
            "Norway": "Grandma",
        }
    
        DEFAULT_OWNER = "Holly"
    
       @st.cache_data(ttl=3600)
        def get_red_cards_fbref():
        
            import requests
            import pandas as pd
        
            url = "https://fbref.com/en/comps/1/misc/World-Cup-Stats"
        
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
                "Accept-Language": "en-US,en;q=0.9",
            }
        
            r = requests.get(url, headers=headers, timeout=20)
        
            # IMPORTANT: avoid crashing app if blocked
            if r.status_code != 200:
                return pd.DataFrame(columns=["Team", "Red Cards"])
        
            # pass HTML TEXT instead of URL (this avoids urllib layer)
            tables = pd.read_html(r.text)
        
            target = None
        
            for t in tables:
                if any("Red" in str(col) for col in t.columns):
                    target = t
                    break
        
            if target is None:
                return pd.DataFrame(columns=["Team", "Red Cards"])
        
            # detect columns safely
            team_col = [c for c in target.columns if "Squad" in str(c) or "Team" in str(c)][0]
            red_col = [c for c in target.columns if "Red" in str(c)][0]
        
            df = target[[team_col, red_col]].copy()
            df.columns = ["Team", "Red Cards"]
        
            df["Red Cards"] = pd.to_numeric(df["Red Cards"], errors="coerce").fillna(0).astype(int)
        
            return df[df["Red Cards"] > 0]    
    
        df_rc = get_red_cards_fbref()
    
        if df_rc.empty:
            st.info("No red cards recorded yet.")
            st.stop()
    
        # ----------------------------
        # ADD OWNER COLUMN
        # ----------------------------
        df_rc["Owner"] = df_rc["Team"].apply(
            lambda x: TEAM_OWNERS_GOLDEN.get(x, DEFAULT_OWNER)
        )
    
        # ----------------------------
        # SORT
        # ----------------------------
        df_rc = df_rc.sort_values("Red Cards", ascending=False)
    
        # ----------------------------
        # SHOW TABLE
        # ----------------------------
        html_table = df_rc.to_html(index=False, escape=False)
    
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
            }
    
            td {
                padding: 6px;
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
    
    with subtab4:
        st.write("Biggest single loss (£5 prize)")
        matches = load_stormcup_data()
    
        finished = matches[
            matches["status"] == "FINISHED"
        ].sort_values("date", ascending=False)
    
        largest_margin = 0
        biggest_losers = []
    
        for _, row in finished.iterrows():
    
            home_score = row["home_score"]
            away_score = row["away_score"]
    
            if pd.isna(home_score) or pd.isna(away_score):
                continue
    
            margin = abs(home_score - away_score)
    
            if margin == 0:
                continue
    
            # determine loser + winner
            if home_score < away_score:
                losing_team = row["home_team"]
                winning_team = row["away_team"]
                score = f"{int(home_score)}-{int(away_score)}"
            else:
                losing_team = row["away_team"]
                winning_team = row["home_team"]
                score = f"{int(away_score)}-{int(home_score)}"
    
            # update leaderboard
            if margin > largest_margin:
                largest_margin = margin
                biggest_losers = [{
                    "team": losing_team,
                    "winner": winning_team,
                    "score": score
                }]
    
            elif margin == largest_margin:
                biggest_losers.append({
                    "team": losing_team,
                    "winner": winning_team,
                    "score": score
                })
    
        TEAM_OWNER = {
            "Argentina": "Miles",
            "Portugal": "Fiona",
            "Colombia": "Fiona",
            "Switzerland": "Maggie",
            "Croatia": "Helen",
            "Senegal": "Maggie",
            "Egypt": "Dan",
            "Algeria": "James",
            "Ivory Coast": "Henry",
            "Qatar": "Janet",
            "Saudi Arabia": "Anne",
            "New Zealand": "James",
            "Spain": "Fiona",
            "Netherlands": "Grandma",
            "Belgium": "Simy",
            "Japan": "Rich",
            "Mexico": "Rich",
            "Sweden": "Simy",
            "South Korea": "Dan",
            "Iran": "Miles",
            "Scotland": "Grandma",
            "South Africa": "Henry",
            "Jordan": "Janet",
            "Haiti": "James",
            "France": "Henry",
            "Brazil": "James",
            "Morocco": "Fiona",
            "Uruguay": "Janet",
            "United States": "Janet",
            "Austria": "Anne",
            "Canada": "Grandma",
            "Bosnia-Herzegovina": "Helen",
            "Ghana": "Simy",
            "Tunisia": "Rich",
            "Uzbekistan": "Dan",
            "Cape Verde Islands": "Rich",
            "England": "Miles",
            "Germany": "Anne",
            "Norway": "Simy",
            "Ecuador": "Dan",
            "Turkey": "Grandma",
            "Paraguay": "Henry",
            "Australia": "Maggie",
            "Czechia": "Anne",
            "Panama": "Helen",
            "Iraq": "Miles",
            "Congo DR": "Helen",
            "Curaçao": "Maggie",
        }
    
        if biggest_losers:
    
            st.write(
                f"{len(biggest_losers)} teams tied on "
                f"{int(largest_margin)} goal{'s' if largest_margin != 1 else ''}"
            )
    
            for result in biggest_losers:
    
                owner = TEAM_OWNER.get(result["team"], "Unknown")
    
                st.success(f"**{owner}**")
    
                st.write(
                    f"**{result['team']}** lost {result['score']} "
                    f"to {result['winner']}"
                )
        else:
            st.info("No matches found yet.")    
# ----------------------------
# TAB 3 - RESULTS
# ----------------------------

with tab3:


    matches = load_stormcup_data()

    finished = matches[
        matches["status"] == "FINISHED"
    ].sort_values("date", ascending=False)
    
    rows = []

    for _, row in finished.iterrows():

        rows.append({
            "Date": row["date"],
            "Stage": str(row["stage"]).replace("_", " ").title(),
            "Result": (
                f"{row['home_team']} "
                f"{int(row['home_score'])} - {int(row['away_score'])} "
                f"{row['away_team']}"
            )
        })

    results_df = pd.DataFrame(rows)

    html_table = results_df.to_html(index=False, escape=False)

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
# TAB 4 - STORM CUP
# ----------------------------

with tab4:



    matches = load_stormcup_data()

    scores = compute_stormcup(matches)

    finished_matches = matches[matches["status"] == "FINISHED"]

    # build per-team stats
    owner_to_teams = {}
    for team, owner in TEAM_OWNERS.items():
        owner_to_teams.setdefault(owner, []).append(team)

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
            wins = 0
            draws = 0
            losses = 0
            
            for _, r in team_matches.iterrows():
            
                team_is_home = r["home_team"] == team
                team_is_away = r["away_team"] == team
            
                if r["stage"] == "GROUP_STAGE":
            
                    # Draw
                    if r["home_score"] == r["away_score"]:
                        pts += 1
                        draws += 1
            
                    # Team win
                    elif (
                        (team_is_home and r["home_score"] > r["away_score"]) or
                        (team_is_away and r["away_score"] > r["home_score"])
                    ):
                        pts += 3
                        wins += 1
            
                    # Team loss
                    else:
                        losses += 1
            
                else:
                    # Knockout win
                    if (
                        (team_is_home and r["winner"] == "HOME_TEAM") or
                        (team_is_away and r["winner"] == "AWAY_TEAM")
                    ):
                        pts += 3
                        wins += 1
            
                    # Knockout loss
                    else:
                        losses += 1
            
            team_strings.append(
                f"{team} ({pts} points - P {played}, W {wins}, D {draws}, L {losses})"
            )

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

