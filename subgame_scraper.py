import aiohttp
import logging
import asyncio
from typing import Dict, List, cast
from scrape_game_ids import OneXBetGame, OneXBetSubGame
from common import LIVE_MATCH_URL, PREMATCH_URL


def parse_subgames(subgames_data: List[Dict]) -> List[OneXBetSubGame]:
    """Parse subgames from the SG array"""
    subgames = []
    
    for sg in subgames_data:
        try:
            ci_or_i = sg.get("CI") or sg.get("I")
            pn = sg.get("PN", "")
            tg = sg.get("TG", "")
            if ci_or_i is None:
                raise ValueError(f"No 'CI' or 'I' found in subgame")
            subgame_id = int(ci_or_i)
            name = pn + " " + tg if pn and tg else pn or tg or ''
            period=sg.get("P") if sg.get("P") else sg.get("TI",0)
            subgame = OneXBetSubGame(
                subgame_id=subgame_id,
                name=name,
                period=period,
            )
            subgames.append(subgame)
            logging.debug(f"Parsed subgame: {subgame.name} (ID: {subgame.subgame_id})")
        except (KeyError, ValueError) as e:
            logging.error(f"Error parsing subgame {e}")
    return subgames


async def fetch_single_subgame(subgame, url: str) -> Dict:
    """Fetch a single subgame page - subgame as in innings, player stats etc"""
    try:
        async with aiohttp.ClientSession() as session:
            response = await session.get(url, timeout=10)
            if response.status != 200:
                logging.error(f"Failed to fetch subgame {subgame.subgame_id}: {response.status}")
                return {}
            return await response.json()
    except Exception as e:
        logging.error(f"Error fetching subgame {subgame.subgame_id}: {e}")
        return {}

    
async def fetch_subgames(game:OneXBetGame,game_page: Dict, is_live : bool) -> Dict:
    value = game_page.get("Value", {})
    
    subgames = None
    if "SG" in value and value["SG"]:
        subgames = parse_subgames(value["SG"])
        logging.info(f"Found {len(subgames)} subgames for game {game.game_id}")
    if not subgames:
        return game_page
    
    game.subgames = subgames


    tasks = []
    for subgame in subgames:
        url = LIVE_MATCH_URL.format(game_id=subgame.subgame_id) if is_live else PREMATCH_URL.format(game_id=subgame.subgame_id)
        tasks.append(fetch_single_subgame(subgame, url))
        
    subgame_results = await asyncio.gather(*tasks, return_exceptions=True)

    main_markets = value.get("GE", [])

    all_markets = main_markets.copy()
    
    for i, result in enumerate(subgame_results):
        if isinstance(result, Exception):
            logging.error(f"Failed to fetch subgame {subgames[i].subgame_id}: {result}")
            continue
        else:
            result = cast(Dict, result)
            if result and result.get("Success"):
                subgame_markets = result.get("Value", {}).get("GE", [])
                for market in subgame_markets:
                    market["subgame_name"] = subgames[i].name 
                    market["subgame_period"] = subgames[i].period
                    market["subgame_id"] = subgames[i].subgame_id
                all_markets.extend(subgame_markets)

    modified_game_page = game_page.copy()
    modified_game_page["Value"]["GE"] = all_markets

    logging.info(f"Combined {len(main_markets)} main markets with {len(all_markets) - len(main_markets)} subgame markets")

    return modified_game_page
