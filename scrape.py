from models import ScrapeGame, ScrapeH2HGame, ScrapeTeamGame
from shared.upload import upload_to_ingest
import aiohttp
import logging
import asyncio
from datetime import datetime
from typing import Dict
from scrape_game_ids import OneXBetGame, SPORT_NAME_MAPPING
from helpers import mma, american_football, basketball, soccer, baseball, boxing, tennis, hockey
from get_markets_config import initialize_market_names
from utils import get_league_path
from common import LIVE_MATCH_URL, PREMATCH_URL,INDIVIDUAL_SPORT_LIST,TEAM_SPORT_LIST
from subgame_scraper import fetch_subgames
import metrics
import time

async def fetch_game_page(game_id: str, is_live : bool) -> Dict:
    url = LIVE_MATCH_URL.format(game_id=game_id) if is_live else PREMATCH_URL.format(game_id=game_id)

    requests_success_counter = metrics.live_requests_success_counter if is_live else metrics.prematch_requests_success_counter
    
    async with aiohttp.ClientSession() as session:
        response = await session.get(url, timeout=10)
        if response.status != 200:
            logging.error(f"Failed to fetch game page for {game_id}: {response.status}")
            return {}
        requests_success_counter.inc()
        return await response.json()

def parse_game_page(game: OneXBetGame, game_page: Dict,scrape_ts: datetime) -> ScrapeGame:
    value = game_page.get("Value", {})
    url_league_path = get_league_path(game,value)
    unparsed_markets = value.get("GE",[])
    if game.sport in {"MMA","UFC","Martial Arts"}:
        scrape_markets = mma.parse(game, unparsed_markets, scrape_ts,url_league_path)
    elif game.sport == "American Football":
        scrape_markets = american_football.parse(game, unparsed_markets, scrape_ts,url_league_path)
    elif game.sport == "Basketball":
        scrape_markets = basketball.parse(game,unparsed_markets,scrape_ts,url_league_path)
    elif game.sport == "Football":
        scrape_markets = soccer.parse(game,unparsed_markets,scrape_ts,url_league_path)
    elif game.sport == "Baseball":
        scrape_markets = baseball.parse(game,unparsed_markets,scrape_ts,url_league_path)
    elif game.sport == "Tennis":
        scrape_markets = tennis.parse(game,unparsed_markets,scrape_ts,url_league_path)
    elif game.sport == "Ice Hockey":
        scrape_markets = hockey.parse(game,unparsed_markets,scrape_ts,url_league_path)
    elif game.sport == "Boxing":
        scrape_markets = boxing.parse(game,unparsed_markets,scrape_ts,url_league_path)

    if game.sport in INDIVIDUAL_SPORT_LIST:
        try:
            scrape_h2h_game = ScrapeH2HGame(
                sport=SPORT_NAME_MAPPING[game.sport],
                league=game.league,
                date=game.date,
                player_1=game.home_team,
                player_2=game.away_team,
                markets=scrape_markets,
            )
            return scrape_h2h_game
        except Exception as e:
            logging.error(f"Validation error creating ScrapeH2HGame for game {game.game_id}: {e}")
            if game.live:
                metrics.live_validation_errors_counter.inc()
            else:
                metrics.prematch_validation_errors_counter.inc()
            raise

    else:
        try:
            scrape_team_game = ScrapeTeamGame(
                sport = SPORT_NAME_MAPPING[game.sport],
                league = game.league,
                date = game.date,
                home_team = game.home_team,
                away_team = game.away_team,
                markets = scrape_markets
            )
            return scrape_team_game
        except Exception as e:
            logging.error(f"Validation error creating ScrapeH2HGame for game {game.game_id}: {e}")
            if game.live:
                metrics.live_validation_errors_counter.inc()
            else:
                metrics.prematch_validation_errors_counter.inc()
            raise

    
    
async def scrape_game(game: OneXBetGame) -> Dict:
    scrape_ts = datetime.now()
    game_page = await fetch_game_page(str(game.game_id),game.live)
    if not game_page or not game_page.get("Value", {}): 
        logging.error(f"Failed to fetch game page for {game.game_id}")
        return {}
    game_page = await fetch_subgames(game,game_page, game.live)
    logging.info(f"Finished game page scrape {game.game_id}")
    scrape_game = parse_game_page(game, game_page,scrape_ts)
    if scrape_game:
        if game.live:
            metrics.live_odds_pages_scraped_counter.inc()
        else:
            metrics.prematch_odds_pages_scraped_counter.inc()
    return scrape_game.model_dump()



# async def test_single_game():
#     """Test scraping a single game - useful for development"""
#     logging.info("Starting test")
#     # games = await fetch_all_games()
#     # if games:
#     test_game = OneXBetGame(
#                 sport="Football",
#                 league="England. Premier League",
#                 game_id=266616226,
#                 date=datetime.fromtimestamp(1751823300),
#                 home_team="Liverpool",
#                 away_team="Bournemouth",
#                 live=False,
#                 subgames=None
#     )
#     result = await scrape_game(test_game)
#     #logging.info(f"Test result: {result}")

# async def main():
#     logging.info("Starting 1xBet scraper...")
#     logging.info("Initializing market name mappings...")
#     await initialize_market_names()
#     await test_single_game()
# if __name__ == "__main__":
#     logging.basicConfig(level=logging.INFO)
#     asyncio.run(main())
