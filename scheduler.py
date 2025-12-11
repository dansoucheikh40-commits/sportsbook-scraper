from scrape_game_ids import fetch_all_games, OneXBetGame
from get_markets_config import initialize_market_names
from scrape import scrape_game
from typing import Dict
from datetime import datetime, timedelta
import metrics
from shared.upload import upload_to_ingest
import time
import traceback
import logging
import asyncio
from prometheus_client import start_http_server

async def process_game(game: OneXBetGame):
    start_time = time.time()
    
    try:
        game_data = await scrape_game(game)
        
        if game.live:
            metrics.live_end_to_end_time.observe(time.time() - start_time)
        else:
            metrics.prematch_end_to_end_time.observe(time.time() - start_time)
        
        if game_data:
            await upload_to_ingest(game_data)
            if game.live:
                metrics.live_successful_uploads_counter.inc()
                logging.info(f"Uploaded live odds for game: {game.game_id}")
            else:
                metrics.prematch_successful_uploads_counter.inc()
                logging.info(f"Uploaded prematch odds for game: {game.game_id}")
    except Exception as e:
        # Still record timing even on error
        if game.live:
            metrics.live_end_to_end_time.observe(time.time() - start_time)
        else:
            metrics.prematch_end_to_end_time.observe(time.time() - start_time)
        
        logging.error(f"Error processing game {game.game_id}: {str(e)}")
        traceback.print_exc()


async def schedule_live_game(game: OneXBetGame):
    while True:
        asyncio.create_task(process_game(game))
        await asyncio.sleep(2)

async def schedule_prematch_game(game: OneXBetGame):
    while True:
        asyncio.create_task(process_game(game))
        await asyncio.sleep(60)


async def fetch_all_games_loop():

    live_games_tasks: Dict[str, asyncio.Task] = {}
    prematch_games_tasks: Dict[str, asyncio.Task] = {}

    last_updated: Dict[str, datetime] = {}

    while True:
        games = await fetch_all_games()
        for game in games:
            game_id = str(game.game_id)
            last_updated[game_id] = datetime.now()
            if game.live and game.game_id not in live_games_tasks:
	                # Once the game is live, we need to cancel the prematch task if it exists
                if game_id in prematch_games_tasks:
                    logging.info(f"Game {game_id} transitioned from prematch to live")
                    prematch_games_tasks[game_id].cancel()
                    del prematch_games_tasks[game_id]
                    metrics.prematch_num_games.dec()
                
                logging.info(f"Starting live monitoring for game: {game_id}")
                live_games_tasks[game_id] = asyncio.create_task(schedule_live_game(game))
                metrics.live_num_games.inc()

            elif not game.live and game.game_id not in prematch_games_tasks:
                logging.info(f"Starting prematch monitoring for game: {game_id}")
                prematch_games_tasks[str(game.game_id)] = asyncio.create_task(schedule_prematch_game(game))
                metrics.prematch_num_games.inc()
            last_updated[str(game.game_id)] = datetime.now()
        
        # clean up tasks that haven't been updated in the last 5 minutes
        keys_to_remove = [key for key in last_updated if datetime.now() - last_updated[key] > timedelta(minutes=5)]
        for key in keys_to_remove:
            del last_updated[key]
            if key in live_games_tasks:
                logging.info(f"Cancelling live monitoring for stale game: {key}")
                live_games_tasks[key].cancel()
                del live_games_tasks[key]
                metrics.live_num_games.dec()
            if key in prematch_games_tasks:
                logging.info(f"Cancelling prematch monitoring for stale game: {key}")
                prematch_games_tasks[key].cancel()
                del prematch_games_tasks[key]
                metrics.prematch_num_games.dec()
        await asyncio.sleep(30)

async def main():
    start_http_server(8000)
    logging.info("Starting 1xBet scraper...")
    logging.info("Initializing market name mappings...")
    await initialize_market_names()
    await fetch_all_games_loop()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())