from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from nba_api.live.nba.endpoints import scoreboard
from nba_api.stats.endpoints import leaguestandingsv3
from fastapi.staticfiles import StaticFiles
from nba_api.stats.endpoints import boxscoresummaryv2

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_methods=["*"], allow_headers=["*"],
)

app.mount("/logos", StaticFiles(directory="logos"), name="logos")

@app.get("/nba/today")
def get_today_games():
    data = scoreboard.ScoreBoard()
    games = data.get_dict()["scoreboard"]["games"]
    return [
        {
            "gameId": g["gameId"],
            "home": g["homeTeam"]["teamName"],
            "away": g["awayTeam"]["teamName"],
            "homeScore": g["homeTeam"]["score"],
            "awayScore": g["awayTeam"]["score"],
            "status": g["gameStatusText"],
            "gameLabel": g.get("gameLabel", ""),
            "seriesGameNumber": g.get("seriesGameNumber", ""),
            "seriesText": g.get("seriesText", ""),
            "homeTeamId": g["homeTeam"].get("teamId", ""),
            "awayTeamId": g["awayTeam"].get("teamId", ""),
        }
        for g in games
    ]

@app.get("/nba/standings")
def get_standings():
    try:
        res = leaguestandingsv3.LeagueStandingsV3().get_dict()
        result = res["resultSets"][0]
        headers = result["headers"]
        data = result["rowSet"]

        east = []
        west = []

        for row in data:
            team_data = dict(zip(headers, row))
            entry = {
                "team": f"{team_data['TeamCity']} {team_data['TeamName']}",
                "wins": team_data["WINS"],
                "losses": team_data["LOSSES"],
                "winPct": round(team_data["WinPCT"] * 100, 1),
                "rank": team_data["PlayoffRank"],
                "conf": team_data["Conference"],
                "streak": team_data["strCurrentStreak"],
                "teamId": team_data["TeamID"]
            }
            if entry["conf"] == "East":
                east.append(entry)
            else:
                west.append(entry)

        return {
            "east": sorted(east, key=lambda x: int(x["rank"])),
            "west": sorted(west, key=lambda x: int(x["rank"])),
        }

    except Exception as e:
        return {"error": str(e)}

@app.get("/nba/live")
def get_live_games():
    data = scoreboard.ScoreBoard()
    live_games = []
    for g in data.get_dict()["scoreboard"]["games"]:
        if g["gameStatus"] == 2:
            return g
    return {"error": "No live games found"}

@app.get("/nba/ended/{game_id}")
def get_ended_game_by_id(game_id: str):
    data = scoreboard.ScoreBoard()
    for g in data.get_dict()["scoreboard"]["games"]:
        if g["gameStatus"] == 3 and g["gameId"] == game_id:
            return g
    return {"error": "Game not found or not finished"}


@app.get("/nba/game-details/{game_id}")
def get_game_details(game_id: str):
    try:
        # === 1. Ottieni dati dalla parte "live.ended" ===
        data = scoreboard.ScoreBoard()
        ended_game = None
        for g in data.get_dict()["scoreboard"]["games"]:
            if g["gameId"] == game_id and g["gameStatus"] == 3:
                ended_game = g
                break

        if not ended_game:
            return {"error": "Game not found or not ended."}

        # === 2. Ottieni dati da BoxScoreSummaryV2 ===
        recap_raw = boxscoresummaryv2.BoxScoreSummaryV2(game_id=game_id).get_dict()
        recap = {}

        for rs in recap_raw["resultSets"]:
            name = rs["name"]
            headers = rs["headers"]
            rows = rs["rowSet"]

            if not rows:
                continue

            if name == "GameSummary":
                values = dict(zip(headers, rows[0]))
                recap["gameSummary"] = {
                    "gameDate": values.get("GAME_DATE_EST"),
                    "arena": values.get("ARENA_NAME"),
                    "attendance": values.get("ATTENDANCE"),
                    "broadcaster": values.get("NATL_TV_BROADCASTER_ABBREVIATION"),
                    "videoAvailable": values.get("VIDEO_AVAILABLE_FLAG", 0) == 1,
                }

            elif name == "GameInfo":
                values = dict(zip(headers, rows[0]))
                recap["info"] = {
                    "headline": values.get("GAME_DATE"),
                    "gameTime": values.get("GAME_TIME"),
                    "gameNarrative": values.get("GAME_NARRATIVE"),
                }

            elif name == "LastMeeting":
                values = dict(zip(headers, rows[0]))
                recap["lastMeeting"] = {
                    "matchup": values.get("MATCHUP"),
                    "lastWinner": values.get("W_L"),
                    "lastDate": values.get("GAME_DATE"),
                }

            elif name == "Officials":
                recap["officials"] = [
                    dict(zip(headers, row)) for row in rows
                ]

            elif name == "InactivePlayers":
                recap["inactivePlayers"] = [
                    dict(zip(headers, row)) for row in rows
                ]

            elif name == "AvailableVideo":
                values = dict(zip(headers, rows[0]))
                recap["availableVideo"] = {
                    "videoUrls": values.get("VIDEO_URL", ""),
                    "videoId": values.get("VIDEO_ID", "")
                }

            elif name == "OtherStats":
                recap["otherStats"] = [
                    dict(zip(headers, row)) for row in rows
                ]

        return {
            "game": ended_game,
            "recap": recap
        }

    except Exception as e:
        return {"error": str(e)}
