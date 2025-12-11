from scrape_game_ids import OneXBetGame
from datetime import datetime
from utils import decimal_to_american, resolve_outcome_name, map_outcome_to_standard, decimal_to_fraction
from typing import Optional, Dict, List
from models import ScrapeOdds
import logging

SPORTSBOOK_NAME = "ONEXBET"
DEEPLINK_PREMATCH_BASE = "https://1xbet.com/en/line/{path}"
DEEPLINK_LIVE_MATCH_BASE = "https://1xbet.com/en/live/{path}"
PREMATCH_URL = "https://1xbet.com/LineFeed/GetGameZip?id={game_id}&lng=en&isSubGames=true&GroupEvents=true&allEventsGroupSubGames=true&countevents=500&country=71&fcountry=71&marketType=1&gr=70&isNewBuilder=true"
LIVE_MATCH_URL = "https://1xbet.com/LiveFeed/GetGameZip?id={game_id}&lng=en&isSubGames=true&GroupEvents=true&allEventsGroupSubGames=true&countevents=500&country=71&fcountry=71&marketType=1&gr=70&isNewBuilder=true"
INDIVIDUAL_SPORT_LIST = {"UFC","MMA","Martial Arts","Boxing","Tennis"}
TEAM_SPORT_LIST = {"Football","Basketball","Baseball","American Football","Ice Hockey"}


def scrape_moneyline(
    market: Dict,
    game: OneXBetGame,
    market_type: str,
    scrape_ts: datetime,
    url_path:str
) -> List[ScrapeOdds]:
    
    scrape_odds = []

    outcomes_groups = market.get("E", [])
    for outcome_group in outcomes_groups:
        for outcome in outcome_group:
            try:
                decimal_odds = outcome.get("C", 0)
                if decimal_odds <= 1.0:
                    continue
                
                t_value = outcome.get("T", "")
                p_value = outcome.get("P", None)
                
                outcome_name = resolve_outcome_name(
                    t_value, 
                    p_value, 
                    game.home_team, 
                    game.away_team
                )
                
                standard_outcome = map_outcome_to_standard(
                    outcome_name, 
                    game.home_team, 
                    game.away_team, 
                    market_type,
                    game.sport
                )
                
                if standard_outcome == "UNKNOWN":
                    logging.debug(f"Could not map outcome: {outcome_name} for market {market_type}")
                    continue
                
                american_odds = decimal_to_american(decimal_odds)
    
                fractional_num, fractional_den = decimal_to_fraction(decimal_odds)
       
                deeplink = DEEPLINK_LIVE_MATCH_BASE.format(path=url_path) if game.live else DEEPLINK_PREMATCH_BASE.format(path=url_path)
    
                scrape_odds.append(ScrapeOdds(
                    american_odds=american_odds,
                    decimal_odds=decimal_odds,
                    fractional_num=fractional_num,
                    fractional_den=fractional_den,
                    outcome_type=standard_outcome,
                    sportsbook=SPORTSBOOK_NAME,
                    scrape_ts=scrape_ts,
                    spread=None,
                    live=game.live,
                    available=True,
                    deeplink=deeplink,
                    alt=False
                ))
                
            except Exception as e:
                logging.error(f"Error parsing outcome {market_type} {outcome}: {e}")
                continue
    return scrape_odds

def scrape_spread(
    market: Dict,
    game: OneXBetGame,
    market_type: str,
    scrape_ts: datetime,
    url_path : str,
) -> List[ScrapeOdds]:
    
    scrape_odds = []

    outcomes_groups = market.get("E", [])
    for outcome_group in outcomes_groups:
        for outcome in outcome_group:
            try:
                decimal_odds = outcome.get("C", 0)
                if decimal_odds <= 1.0:
                    continue
                
                t_value = outcome.get("T", "")
                p_value = outcome.get("P", None)
                alt = False if outcome.get("CE",0) == 1 else True
                
                outcome_name = resolve_outcome_name(
                    t_value, 
                    p_value, 
                    game.home_team, 
                    game.away_team
                )
                
                standard_outcome = map_outcome_to_standard(
                    outcome_name, 
                    game.home_team, 
                    game.away_team, 
                    market_type,
                    game.sport
                )
                
                if standard_outcome == "UNKNOWN":
                    logging.debug(f"Could not map outcome: {outcome_name} for market {market_type}")
                    continue
                
                if p_value is not None:
                    spread = float(p_value)
                else:
                    spread = None

                american_odds = decimal_to_american(decimal_odds)
    
                fractional_num, fractional_den = decimal_to_fraction(decimal_odds)
       
                deeplink = DEEPLINK_LIVE_MATCH_BASE.format(path=url_path) if game.live else DEEPLINK_PREMATCH_BASE.format(path=url_path)                
                scrape_odds.append(ScrapeOdds(
                    american_odds=american_odds,
                    decimal_odds=decimal_odds,
                    fractional_num=fractional_num,
                    fractional_den=fractional_den,
                    outcome_type=standard_outcome,
                    sportsbook=SPORTSBOOK_NAME,
                    scrape_ts=scrape_ts,
                    spread=spread,
                    live=game.live,
                    available=True,
                    deeplink=deeplink,
                    alt=alt
                ))
                
            except Exception as e:
                logging.error(f"Error parsing outcome {market_type} {outcome}: {e}")
                continue
    return scrape_odds

def scrape_total(
    market: Dict,
    game: OneXBetGame,
    market_type: str,
    scrape_ts: datetime,
    url_path: str
) -> List[ScrapeOdds]:
    
    scrape_odds = []

    outcomes_groups = market.get("E", [])
    for outcome_group in outcomes_groups:
        for outcome in outcome_group:
            try:
                decimal_odds = outcome.get("C", 0)
                if decimal_odds <= 1.0:
                    continue
                
                t_value = outcome.get("T", "")
                p_value = outcome.get("P", None)
                player_name = outcome.get("PL", {}).get("N", None)
                alt = False if outcome.get("CE",0) == 1 else True

                outcome_name = resolve_outcome_name(
                    t_value, 
                    p_value, 
                    game.home_team, 
                    game.away_team,
                    player_name
                )
                
                standard_outcome = map_outcome_to_standard(
                    outcome_name, 
                    game.home_team, 
                    game.away_team, 
                    market_type,
                    game.sport
                )
                
                if standard_outcome == "UNKNOWN":
                    logging.debug(f"Could not map outcome: {outcome_name} for market {market_type}")
                    continue
                
                if p_value is not None:
                    spread = float(p_value)
                else:
                    spread = None
                
                american_odds = decimal_to_american(decimal_odds)
    
                fractional_num, fractional_den = decimal_to_fraction(decimal_odds)
       
                deeplink = DEEPLINK_LIVE_MATCH_BASE.format(path=url_path) if game.live else DEEPLINK_PREMATCH_BASE.format(path=url_path)
                                
                scrape_odds.append(ScrapeOdds(
                    american_odds=american_odds,
                    decimal_odds=decimal_odds,
                    fractional_num=fractional_num,
                    fractional_den=fractional_den,
                    outcome_type=standard_outcome,
                    sportsbook=SPORTSBOOK_NAME,
                    scrape_ts=scrape_ts,
                    spread=spread,
                    live=game.live,
                    available=True,
                    deeplink=deeplink,
                    alt=alt
                ))
                
            except Exception as e:
                logging.error(f"Error parsing outcome {market_type} {outcome}: {e}")
                continue
    return scrape_odds