from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from nba_api.live.nba.endpoints import scoreboard
from nba_api.stats.endpoints import leaguestandings

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_methods=["*"], allow_headers=["*"],
)

@app.get("/nba/today")
def get_today_games():
    data = scoreboard.ScoreBoard()
    games = data.get_dict()["scoreboard"]["games"]
    return [
        {
            "home": g["homeTeam"]["teamName"],
            "away": g["awayTeam"]["teamName"],
            "homeScore": g["homeTeam"]["score"],
            "awayScore": g["awayTeam"]["score"],
            "status": g["gameStatusText"],
            "gameLabel": g.get("gameLabel", "")  # aggiunto qui
        }
        for g in games
    ]

@app.get("/nba/standings")
def get_standings():
    data = leaguestandings.LeagueStandings().get_dict()["resultSet"]["rowSet"]
    headers = leaguestandings.LeagueStandings().get_dict()["resultSet"]["headers"]

    east = []
    west = []

    for row in data:
        team_data = dict(zip(headers, row))
        entry = {
            "team": team_data["TeamName"],
            "wins": team_data["WINS"],
            "losses": team_data["LOSSES"],
            "conf": team_data["Conference"],
            "rank": team_data["ConferenceRank"]
        }
        if entry["conf"] == "East":
            east.append(entry)
        else:
            west.append(entry)

    return {
        "east": sorted(east, key=lambda x: int(x["rank"])),
        "west": sorted(west, key=lambda x: int(x["rank"])),
    }

@app.get("/nba/live")
def get_live_games():
    data = scoreboard.ScoreBoard()
    live_games = []
    for g in data.get_dict()["scoreboard"]["games"]:
        if g["gameStatus"] == 2:
            live_games.append({
                "home": g["homeTeam"]["teamName"],
                "away": g["awayTeam"]["teamName"],
                "homeScore": g["homeTeam"]["score"],
                "awayScore": g["awayTeam"]["score"],
                "clock": g["gameClock"],
                "period": g["period"],
                "gameLabel": g.get("gameLabel", "")  # aggiunto anche qui
            })
    return live_games
