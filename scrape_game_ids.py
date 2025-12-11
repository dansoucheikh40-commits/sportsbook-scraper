from datetime import datetime
from typing import List, Any, Coroutine, Optional, Dict
import aiohttp
import logging
import asyncio
from pydantic import BaseModel

class OneXBetSubGame(BaseModel):
    subgame_id: int
    name: str
    period: Optional[int] = None

class OneXBetGame(BaseModel):
    sport: str
    league: str
    date: datetime
    home_team: str
    away_team: str
    live: bool
    game_id: int
    subgames: Optional[List[OneXBetSubGame]] = None

    def has_subgames(self) -> bool:
        return self.subgames is not None and len(self.subgames) > 0

SPORT_ID_TO_NAME = {
    1: "Football",
    2: "Ice Hockey",
    3: "Basketball",
    4: "Tennis",
    5: "Baseball",
    13: "American Football",
    9: "Boxing",
    56:"Martial Arts",
    79: "MMA",
    189: "UFC"
}

SPORT_NAME_MAPPING = {
  "Ice Hockey": "Hockey",
  "Tennis": "Tennis",
  "American Football" : "Football",
  "MMA": "MMA",
  "UFC":"MMA",
  "Martial Arts":"MMA",
  "Boxing": "Boxing",
  "Football": "Soccer",
  "Baseball": "Baseball",
  "Basketball": "Basketball",
}

LEAGUES_TO_SCRAPE = { 
  "Basketball" : ["NBA. Summer League","WNBA"],
  "Ice Hockey": ["SHL", "NHL"],
  "Baseball": ["KBO. Futures League", "MLB. All-Star Game",],
  "Football": ["UEFA Champions League", "USA. MLS"],
   "American Football":["CFL", "NFL. Preseason Games", "NCAA"]
}

PREMATCH_ENDPOINT = "https://1xbet.com/LineFeed/Get1x2_VZip?sports={sport_id}&count=50&lng=en&tf=2200000&tz=5&mode=4&country=71&getEmpty=true&gr=70"

LIVE_MATCH_ENDPOINT = "https://1xbet.com/LiveFeed/Get1x2_VZip?sports={sport_id}&count=50&lng=en&gr=70&mode=4&country=71&getEmpty=true"

def parse_games(sport_id: int, data: dict, is_live:bool) -> List[OneXBetGame]:
    games: List[OneXBetGame] = []
    sport_name = SPORT_ID_TO_NAME[sport_id]

    if 'Value' not in data:
        logging.warning(f"No 'Value' key found in response for sport {sport_id}")
        return games
    
    for fixture in data["Value"]:
        try:
            game_id = int(fixture["I"])
            league = fixture["L"]
            home_team = fixture["O1"]
            away_team = fixture["O2"]
            start_time = datetime.fromtimestamp(fixture["S"])

            # skip unwanted leagues
            if sport_name not in { "Tennis","Boxing","Martial Arts","MMA","UFC"} and league not in LEAGUES_TO_SCRAPE[sport_name]:
                continue
         
            games.append(OneXBetGame(
                sport=sport_name,
                league=league,
                game_id=game_id,
                date=start_time,
                home_team=home_team,
                away_team=away_team,
                live=is_live,
                subgames=None
            ))
        except KeyError as e:
            logging.error(f"Missing key {e} in fixture data: {fixture}")
        except Exception as e:
            logging.error(f"Error parsing fixture: {e}, fixture: {fixture}")

    return games

async def fetch_games_in_sport(sport_id: int, is_live:bool) -> List[OneXBetGame]:
    endpoint = LIVE_MATCH_ENDPOINT if is_live else PREMATCH_ENDPOINT
    endpoint = endpoint.format(sport_id=sport_id)
    game_type = "live" if is_live else "prematch"
    async with aiohttp.ClientSession() as session:
        response = await session.get(endpoint, timeout=8)
        if response.status != 200:
            logging.error(f"Failed to fetch {game_type} for sport {sport_id}: {response.status}")
            return []
        data = await response.json()
        return parse_games(sport_id, data,is_live)
  
async def fetch_all_games() -> List[OneXBetGame]:
    
    all_games: List[OneXBetGame] = []
    all_tasks: List[Coroutine[Any , Any, List[OneXBetGame]]] = []

    for sport_id in SPORT_ID_TO_NAME.keys():
        all_tasks.append(fetch_games_in_sport(sport_id, False)) 
        all_tasks.append(fetch_games_in_sport(sport_id, True))
    all_results = await asyncio.gather(*all_tasks, return_exceptions=True)
    for result in all_results:
        if isinstance(result, BaseException):
            logging.error(f"Error fetching games for sport {sport_id}: {result}", exc_info=result)
        else:
            all_games.extend(result)
    logging.info(f"Found {len(all_games)} games")
    return all_games

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(fetch_all_games())