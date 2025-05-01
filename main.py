
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from nba_api.live.nba.endpoints import scoreboard, standings

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
    data = standings.Standings().get_dict()["standings"]["teams"]
    east = []
    west = []

    for team in data:
        team_data = {
            "team": team["teamSitesOnly"]["teamName"],
            "wins": team["win"],
            "losses": team["loss"],
            "conf": team["conference"]["name"],
            "rank": team["conference"]["rank"]
        }
        if team_data["conf"] == "East":
            east.append(team_data)
        else:
            west.append(team_data)

    east_sorted = sorted(east, key=lambda x: int(x["rank"]))
    west_sorted = sorted(west, key=lambda x: int(x["rank"]))

    return {
        "east": east_sorted,
        "west": west_sorted,
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
