import os
import json
import asyncio
from datetime import datetime, date, time, timedelta

OUTPUT_FILE = "data/odds.json"
write_lock = asyncio.Lock()


def json_encoder(obj):
    if isinstance(obj, (datetime, date, time)):
        return obj.isoformat()
    if isinstance(obj, timedelta):
        return str(obj)
    raise TypeError(f"Type non pris en charge: {type(obj)}")


async def upload_to_ingest(game_data: dict):
    async with write_lock:
        os.makedirs("data", exist_ok=True)

        try:
            with open(OUTPUT_FILE, "r", encoding="utf-8") as file:
                games = json.load(file)
        except (FileNotFoundError, json.JSONDecodeError):
            games = []

        if isinstance(game_data, dict):
            identity = json.dumps({
                "sport": game_data.get("sport"),
                "home": game_data.get("home_team", game_data.get("player_1")),
                "away": game_data.get("away_team", game_data.get("player_2")),
                "date": str(game_data.get("date"))
            }, sort_keys=True)

            games = [
                game for game in games
                if json.dumps({
                    "sport": game.get("sport"),
                    "home": game.get("home_team", game.get("player_1")),
                    "away": game.get("away_team", game.get("player_2")),
                    "date": str(game.get("date"))
                }, sort_keys=True) != identity
            ]

            games.append(game_data)

        with open(OUTPUT_FILE, "w", encoding="utf-8") as file:
            json.dump(
                games,
                file,
                ensure_ascii=False,
                indent=2,
                default=json_encoder
            )
