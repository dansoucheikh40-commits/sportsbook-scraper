from models import ScrapeMarket
from scrape_game_ids import OneXBetGame
from typing import Dict, List
from datetime import datetime
import logging
from utils import get_market_type, get_final_market_path
from common import scrape_moneyline, scrape_spread, scrape_total


def parse(game: OneXBetGame, markets: List[Dict], scrape_ts: datetime, url_path: str) -> List[ScrapeMarket]:
    logging.info("Starting market parsing")
    
    scrape_markets = []
    
    logging.info(f"Parsing {len(markets)} markets for Basketball: {game.home_team} vs {game.away_team}")
    
    for market in markets:
        try:
            g_value = market.get("G", "")
            subgame_name = market.get("subgame_name","")
            subgame_id = market.get("subgame_id",None)
            market_type, market_name = get_market_type(g_value, subgame_name)

            final_url_path = get_final_market_path(url_path,game,subgame_id)

            logging.debug(f"G={g_value}")
            
            if market_type.startswith("MONEYLINE"):
                scrape_market = ScrapeMarket(
                    market_type = market_type,
                    odds = scrape_moneyline(market, game, market_type, scrape_ts, final_url_path)
                )
                scrape_markets.append(scrape_market)

            elif market_type.startswith(("OVER_UNDER")):
                scrape_market = ScrapeMarket(
                    market_type = market_type,
                    odds = scrape_total(market, game, market_type, scrape_ts, final_url_path)
                )
                scrape_markets.append(scrape_market)
            
            elif market_type.startswith("SPREAD"):
                scrape_market = ScrapeMarket(
                    market_type = market_type,
                    odds = scrape_spread(market, game, market_type, scrape_ts, final_url_path)
                )
                scrape_markets.append(scrape_market)
            
            else:
                logging.info(f"Skipping unknown market G={g_value} market_name={market_name} type={market_type}")
                continue
            logging.info(f"Successfully parsed {market_type}")
            
        except Exception as e:
            logging.error(f"Error parsing market : {e}")
            continue
    
    logging.info(f"Parsed {len(scrape_markets)} markets total")

    return scrape_markets
