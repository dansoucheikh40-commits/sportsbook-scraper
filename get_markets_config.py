import re
import json
import aiohttp
import logging
from typing import Dict, Tuple

BETS_MODEL: Dict = {}
BETS_MODEL_GROUP: Dict = {}
_INITIALIZED = False

async def fetch_and_parse_market_names() -> Tuple[Dict[str, Dict], Dict[str, Dict]]:
    """Get the market name mappings"""
    url = "https://v2l.traincdn.com/genfiles/cms/betstemplates/betsNames_full_en.js"
    
    try:
        async with aiohttp.ClientSession() as session:
            response = await session.get(url, timeout=10)
            if response.status != 200:
                logging.error(f"Failed to fetch market names: {response.status}")
                return {}, {}
            
            js_content = await response.text()
            
            bets_model_pattern = r'var\s+betsModel\s*=\s*(\{.*?\});'
            bets_model_match = re.search(bets_model_pattern, js_content, re.DOTALL)
              
            bets_model_group_pattern = r'var\s+betsModelGroup\s*=\s*(\{.*?\});'
            bets_model_group_match = re.search(bets_model_group_pattern, js_content, re.DOTALL)
            
            if not bets_model_match:
                logging.error("Could not find betsModel in JavaScript file")
                return {}, {}
                
            if not bets_model_group_match:
                logging.error("Could not find betsModelGroup in JavaScript file")
                return {}, {}
            
            bets_model_json = bets_model_match.group(1)
            bets_model_group_json = bets_model_group_match.group(1)
            
            bets_model = json.loads(bets_model_json)
            bets_model_group = json.loads(bets_model_group_json)
            
            return bets_model, bets_model_group
            
    except Exception as e:
        logging.error(f"Error fetching market names: {e}")
        return {}, {}

async def initialize_market_names():
    """Initialize the market names"""
    global BETS_MODEL, BETS_MODEL_GROUP, _INITIALIZED
    
    if _INITIALIZED:
        logging.info("Market names already initialized, skipping")
        return
        
    try:
        bets_model, bets_model_group = await fetch_and_parse_market_names()
        
        if not bets_model or not bets_model_group:
            logging.error("Failed to initialize market names - empty dictionaries returned")
            return
            
        BETS_MODEL = bets_model
        BETS_MODEL_GROUP = bets_model_group
        _INITIALIZED = True
        
        logging.info(f"Market names initialized")
        
    except Exception as e:
        logging.error(f"Failed to initialize market names: {e}")

def get_bets_model() -> Dict:
    """Get the betsModel dictionary"""
    return BETS_MODEL

def get_bets_model_group() -> Dict:
    """Get the betsModelGroup dictionary"""
    return BETS_MODEL_GROUP

def is_initialized() -> bool:
    """Check if market names have been initialized"""
    return _INITIALIZED