from typing import Dict, Tuple, Optional
from get_markets_config import is_initialized, get_bets_model_group, get_bets_model
import logging
from scrape_game_ids import OneXBetGame
import re

INDIVIDUAL_SPORT_LIST = {"UFC","MMA","Martial Arts","Boxing","Tennis"}
QUARTER_RANGE = r'(?:[1-4](?:st|nd|rd|th)?\s+quarter)'
HALF_RANGE = r'(?:[1-2](?:st|nd)?\s+half)'
INNINGS_RANGE = r'(?:[1-9](?:st|nd|th)?\s+inning)'
SET_RANGE = r'(?:[1-2](?:st|nd)?\s+set)'
MARKET_PATTERNS = {
    "MONEYLINE_Q": [
            rf'^1x2\.\s*{QUARTER_RANGE}$',
            rf'^winner\.\s*{QUARTER_RANGE}$', 
            rf'^result\.\s*{QUARTER_RANGE}$'
        ],
    "OVER_UNDER_Q": [
            rf'^total\.\s*{QUARTER_RANGE}$',
            rf'^over/under\.\s*{QUARTER_RANGE}$'
        ],
    "SPREAD_Q": [
            rf'^handicap\.\s*{QUARTER_RANGE}$',
            rf'^point spread\.\s*{QUARTER_RANGE}$'
        ],
    "HOME_TOTAL_Q":[
        rf'^total 1\.\s*{QUARTER_RANGE}$'
    ],
    "AWAY_TOTAL_Q":[
        rf'^total 2\.\s*{QUARTER_RANGE}$'
    ],
    "ODD_EVEN_Q":[
        rf'^even/odd\.\s*{QUARTER_RANGE}$'
    ],
    "MONEYLINE_I": [
            rf'^1x2\.\s*{INNINGS_RANGE}$',
            rf'^winner\.\s*{INNINGS_RANGE}$', 
            rf'^result\.\s*{INNINGS_RANGE}$'
        ],
    "OVER_UNDER_I": [
            rf'\btotal\.\s*{INNINGS_RANGE}$',
            rf'\bover/under\.\s*{INNINGS_RANGE}$'
        ],
    "SPREAD_I": [
            rf'^handicap\.\s*{INNINGS_RANGE}$',
            rf'^point spread\.\s*{INNINGS_RANGE}$'
        ],
    "MONEYLINE_H": [
            rf'^1x2\.\s*{HALF_RANGE}$',
            rf'^winner\.\s*{HALF_RANGE}$',
            rf'^result\.\s*{HALF_RANGE}$'
        ],
    "OVER_UNDER_H": [
            rf'^total\.\s*{HALF_RANGE}$',
            rf'^over/under\.\s*{HALF_RANGE}$'
        ],
    "SPREAD_H": [
            rf'^handicap\.\s*{HALF_RANGE}$',
            rf'^point spread\.\s*{HALF_RANGE}$'
        ],
    "HOME_TOTAL_H":[
        rf'^total 1\.\s*{HALF_RANGE}$'
    ],
    "AWAY_TOTAL_H":[
        rf'^total 2\.\s*{HALF_RANGE}$'
    ],
    "ODD_EVEN_H":[
        rf'^even/odd\.\s*{HALF_RANGE}$'
    ],
    "MONEYLINE_S": [
            rf'^1x2\.\s*{SET_RANGE}$',
    ],
    "OVER_UNDER_S": [
            rf'^total\.\s*{SET_RANGE}$',
            rf'^over/under\.\s*{SET_RANGE}$'
    ],
    "SPREAD_S": [
            rf'^handicap\.\s*{SET_RANGE}$',
            rf'^point spread\.\s*{SET_RANGE}$'
    ],  
}

EXACT_MATCHES = {
    "MONEYLINE": ["1x2","win (2way)", "winner", "result", "team wins"],
    "OVER_UNDER": ["total","over/under","asian total",],
    "SPREAD": ["handicap", "asian handicap","european handicap", "point spread","who will score more", "win by quarters"],
    "ODD_EVEN": ["even/odd", "odd/even","shirt number of first touchdown scorer","total hits even/odd"],
    "FIRST_TO_SCORE": ["which team will be the first to score points?","first to score" , "first to happen","first run"],
    "FIRST_TO_SCORE_3WAY": ["team goals"],
    "HITS_OVER_UNDER": ["total hits"],
    "TEAM_WITH_MOST_HITS_3WAY":["scoring hits"],
    "HOMERUNS_OVER_UNDER":["total home runs"],

    "ODD_EVEN_HOME_TOTAL":["individual total 1 even/odd"],
    "ODD_EVEN_AWAY_TOTAL":["individual total 2 even/odd"],
    "ODD_EVEN": ["even/odd", "odd/even", "even or odd","shirt number of first touchdown scorer", "total hits even/odd"],
    "OVERTIME": ["will there be overtime? - yes/no","overtime. yes/no",],
    "TEAM_TO_SCORE_FIRST_AND_WIN":[
        "team to score first and win", "first run and win",
        # "to score first goal and win" need to check again in football
    ],
    "HOME_TOTAL": ["total 1", "home total", "team 1 total","asian team total 1"],
    "AWAY_TOTAL": ["total 2", "away total", "team 2 total","asian team total 2"],
    "BTTS":["both teams to score"],

    # Tennis Markets
    "TOTAL_SET":["total sets"],
    "SET_SPREAD":["sets handicap"],
}

def clean_market_name(name: str) -> str:
    return re.sub(r'\s+', ' ', name.lower().strip())

def extract_quarter_or_half_number(text: str, market_type:str) -> Optional[str]:
    if market_type not in {"MONEYLINE_Q","OVER_UNDER_Q","SPREAD_Q","HOME_TOTAL_Q","AWAY_TOTAL_Q","ODD_EVEN_Q","MONEYLINE_I","OVER_UNDER_I","SPREAD_I","MONEYLINE_H","OVER_UNDER_H","SPREAD_H","HOME_TOTAL_H","AWAY_TOTAL_H","ODD_EVEN_H","MONEYLINE_S","OVER_UNDER_S","SPREAD_S"}:
        return None
    quarter_match = re.search(r'([1-4])(?:st|nd|rd|th)?\s+quarter', text, re.IGNORECASE)
    if quarter_match:
        return quarter_match.group(1)
    
    half_match = re.search(r'([1-2])(?:st|nd)?\s+half', text, re.IGNORECASE)
    if half_match:
        return half_match.group(1)
    
    inning_match = re.search(r'([1-9])(?:st|nd|rd|th)?\s+inning', text, re.IGNORECASE)
    if inning_match:
        return inning_match.group(1)
    
    set_match = re.search(r'([1-5])(?:st|nd)?\s+set', text, re.IGNORECASE)
    if set_match:
        return set_match.group(1)
    
    return None

def get_market_type(g_value: str, subgame_name: str = "") -> Tuple[str, Optional[str]]:

    if not is_initialized():
        logging.warning("Market names not initialized, cannot determine market type")
        return ("UNKNOWN", None)
    
    bets_model_group = get_bets_model_group()
    if str(g_value) not in bets_model_group:
        logging.warning(f"Market group {g_value} not found in betsModelGroup")
        return ("UNKNOWN", None)
    
    market_name = bets_model_group[str(g_value)]["N"]
    if subgame_name:
        market_name = f"{market_name}. {subgame_name}"
    cleaned_name = clean_market_name(market_name)
    
    for market_type, exact_patterns in EXACT_MATCHES.items():
        if cleaned_name in exact_patterns:
            return (market_type, cleaned_name)
    
    for market_type, patterns in MARKET_PATTERNS.items():
        for pattern in patterns:
            match = re.fullmatch(pattern, cleaned_name, re.IGNORECASE)
            if match:
                period_number = extract_quarter_or_half_number(cleaned_name,market_type)
                
                if period_number:
                    enhanced_market_type = f"{market_type}{period_number}"
                    return (enhanced_market_type, cleaned_name)
                else:
                    return (market_type, cleaned_name)
                
    return ("UNKNOWN", cleaned_name)

def resolve_outcome_name(t_value: str, p_value: int | None, player1: str, player2: str, player_name : Optional[str] = None) -> str:
    """Convert T value to outcome name and replace all placeholder"""
    bets_model = get_bets_model()
    if str(t_value) not in bets_model:
        return "UNKNOWN"
    
    template = bets_model[str(t_value)]["N"]
    
    template = template.replace("^1^", player1)
    template = template.replace("^2^", player2)
    
    if p_value is not None:
        template = template.replace("()", str(p_value))
    
    if player_name is not None:
        template = template.replace("[]",player_name)
    
    return template

def decimal_to_american(decimal_odds: float) -> str:
    """Convert decimal odds to American format"""
    if decimal_odds >= 2.0:
        return f"+{int((decimal_odds - 1) * 100)}"
    else:
        return f"-{int(100 / (decimal_odds - 1))}"
    
def decimal_to_fraction(decimal_odds: float) -> Tuple[int, int]:
    """Convert decimal odds to Fraction format"""
    if decimal_odds >= 2.0:
        fractional_num = int((decimal_odds - 1) * 100)
        fractional_den = 100
    else:
        fractional_num = 100
        fractional_den = int(100 / (decimal_odds - 1))
    return fractional_num, fractional_den
    
def map_outcome_to_standard(outcome_name: str, player1: str, player2: str, market_type: str, sport:str) -> str:
    """Map 1xBet outcome names to our outcome types"""
    outcome_lower = outcome_name.lower()

    if sport in INDIVIDUAL_SPORT_LIST and market_type.startswith(("MONEYLINE","TEAM_WITH_MOST_HITS_3WAY")):
        if player1.lower() in outcome_lower:
            return "P1_WINS"
        elif player2.lower() in outcome_lower:
            return "P2_WINS"
        else:
            return "DRAW"
    elif sport in INDIVIDUAL_SPORT_LIST and market_type.startswith(("SET_SPREAD","GAME_SPREAD")):
        if player1.lower() in outcome_lower:
            return "P1_COVERS"
        elif player2.lower() in outcome_lower:
            return "P2_COVERS"
        else:
            return "UNKNOWN"
    
    elif market_type.startswith(("MONEYLINE","TEAM_WITH_MOST_HITS_3WAY")):
        if player1.lower() in outcome_lower:
            return "HOME_WINS"
        elif player2.lower() in outcome_lower:
            return "AWAY_WINS"
        else:
            return "DRAW"

    elif market_type.startswith("FIRST_TO_SCORE"):
        if player1.lower() in outcome_lower:
            return "HOME_WINS"
        elif player2.lower() in outcome_lower:
            return "AWAY_WINS"
        else:
            return "NEITHER"
    
    elif  market_type.startswith(("OVER_UNDER", "HOME_TOTAL", "AWAY_TOTAL","HITS_","HOMERUNS_","TOTAL_SET","TOTAL_GAMES")):
        if "over" in outcome_lower:
            return "OVER"
        elif "under" in outcome_lower:
            return "UNDER"
        else:
            return "UNKNOWN"
    
    elif market_type.startswith("SPREAD"):
        if player1.lower() in outcome_lower:
            return "HOME_COVERS"
        elif player2.lower() in outcome_lower:
            return "AWAY_COVERS"
        else:
            return "UNKNOWN"
    
    elif market_type.startswith("SET_SPREAD"):
        if player1.lower() in outcome_lower:
            return "P1_COVERS"
        elif player2.lower() in outcome_lower:
            return "P2_COVERS"
        else:
            return "UNKNOWN"
    
    # YES/NO markets
    elif market_type in {"OVERTIME","BTTS","TEAM_TO_SCORE_FIRST_AND_WIN","HOME_TEAM_TO_SCORE_FIRST_AND_WIN","AWAY_TEAM_TO_SCORE_FIRST_AND_WIN"}:
        if 'yes' in outcome_lower:
            return "YES"
        elif 'no' in outcome_lower:
            return "NO"
        return "YES"

    #ODD EVEN MARKET
    elif market_type.startswith("ODD_EVEN"):
        if 'no' in outcome_lower or "odd" in outcome_lower:
            return "ODD"
        else:
            return "EVEN"

    elif market_type == "PLAYER_PROP":
        if "over" in outcome_lower:
            return "OVER"
        elif "under" in outcome_lower:
            return "UNDER"
        elif "not to score" in outcome_lower:
            return "NO"
        elif "to score" in outcome_lower:
            return "YES"
        elif 'yes' in outcome_lower:
            return "YES"
        elif 'no' in outcome_lower:
            return "NO"
        return "YES"
    
    return "UNKNOWN"

def get_league_path(game: OneXBetGame, game_page: Dict) -> str:

    sport_name = game.sport.lower()
    sport_name = re.sub(r'[^a-z0-9]+', '-', sport_name).strip('-')

    league_id = str(game_page.get("LI"))

    raw_league_name = str(game_page.get("L")).lower()
    league_name = re.sub(r'[^a-z0-9]+', '-', raw_league_name).strip('-')

    url_path = f"{sport_name}/{league_id}-{league_name}"

    return url_path

def get_final_market_path(url_path:str,game: OneXBetGame, subgame_id: int | None) -> str:

    game_id = str(subgame_id) if subgame_id is not None else str(game.game_id)

    match_name = (game.home_team + " " + game.away_team).lower()

    match_name = re.sub(r'[^a-z0-9]+', '-', match_name).strip('-')

    url_path = f"{url_path}/{game_id}-{match_name}"

    return url_path

