# 1xBet Scraper

## ⚠️ Disclaimer

**This project is a showcase of my work building an asynchronous, scheduler-based web scraper.** 

Please note that this scraper may not work in the future due to:
- Frequent changes to the sportsbook's API endpoints and data structure
- Evolving bot detection strategies and anti-scraping measures
- Updates to authentication mechanisms or rate limiting policies

The primary purpose of this repository is to demonstrate:
- Building a production-grade asynchronous Python scraper
- Implementing a scheduler-based architecture for continuous data collection
- Handling real-time and pre-match data streams
- Managing complex state transitions (prematch → live games)
- Parallel processing and subgame handling
- Error handling and resilience patterns

**This is not intended for production use or commercial purposes.**

## Overview

The 1xBet scraper is an asynchronous Python-based web scraper designed to extract real-time and pre-match betting odds from the 1xBet sportsbook platform. The scraper continuously monitors multiple sports, leagues, and markets, collecting odds data and uploading it to a Kafka topic for further processing.

## Architecture

The scraper follows a modular, event-driven architecture with the following key components:

### Core Components

1. **Scheduler (`scheduler.py`)**: The main orchestration module that:
   - Continuously fetches available games from 1xBet's API endpoints
   - Manages separate task queues for live and pre-match games
   - Handles game lifecycle transitions (prematch → live)
   - Implements automatic cleanup of stale games (games not updated in 5+ minutes)
   - Starts a Prometheus metrics server on port 8000

2. **Game Discovery (`scrape_game_ids.py`)**: 
   - Fetches game listings from 1xBet's API for multiple sports
   - Supports both live and pre-match game discovery
   - Filters games based on configured league whitelists
   - Maps sport IDs to standardized sport names
   - Parses game metadata (teams, dates, game IDs)

3. **Game Scraper (`scrape.py`)**:
   - Fetches detailed game pages containing all available markets
   - Handles both live and pre-match game pages via different API endpoints
   - Coordinates subgame fetching for period-specific markets (quarters, halves, innings, sets)
   - Parses raw market data into standardized `ScrapeGame` models
   - Distinguishes between team sports (ScrapeTeamGame) and individual sports (ScrapeH2HGame)

4. **Subgame Scraper (`subgame_scraper.py`)**:
   - Identifies and fetches subgames (period-specific markets like "1st Quarter", "2nd Half", etc.)
   - Parallelizes subgame fetching for performance
   - Merges subgame markets with main game markets
   - Preserves subgame metadata (period number, subgame name) for proper market classification

5. **Market Parsing (`common.py`)**:
   - Provides generic market parsing functions for core bet types:
     - Moneyline (1x2, winner markets)
     - Spread/Handicap markets
     - Over/Under (totals) markets
   - Converts decimal odds to American and fractional formats
   - Generates deeplinks for each betting market
   - Handles alternative lines (alt spreads/totals)

6. **Market Configuration (`get_markets_config.py`)**:
   - Fetches and parses JavaScript files from 1xBet's CDN containing market name mappings
   - Extracts `betsModel` and `betsModelGroup` dictionaries
   - Provides market name resolution for outcome templates
   - Initializes once at startup to avoid repeated API calls

7. **Utilities (`utils.py`)**:
   - Market type detection using pattern matching and exact matches
   - Outcome name resolution with team/player name substitution
   - Standardized outcome mapping (e.g., "Team 1" → "HOME_WINS")
   - Period extraction (quarter/half/inning/set numbers)
   - URL path generation for deeplinks
   - Odds format conversion utilities

8. **Sport-Specific Parsers (`helpers/`)**:
   - Individual parser modules for each supported sport:
     - Basketball (`basketball.py`) - Moneyline, Spread, Totals, Team Totals, First to Score
     - American Football (`american_football.py`) - Moneyline, Spread, Totals, Team Totals
     - Soccer/Football (`soccer.py`) - Moneyline, Spread, Totals, Team Totals, First to Score
     - Baseball (`baseball.py`) - Moneyline, Spread, Totals, Team Totals, First to Score, Hits markets, Home Runs
     - Tennis (`tennis.py`) - Moneyline, Set Totals, Set Spreads
     - Ice Hockey (`hockey.py`) - Moneyline, Spread, Totals, Team Totals
     - MMA/UFC (`mma.py`) - Moneyline, Totals
     - Boxing (`boxing.py`) - Moneyline, Spread, Totals
   - Each parser filters and processes only the supported market types for that sport

## Key Features

### Dual-Mode Operation
- **Pre-match scraping**: Monitors upcoming games with 60-second intervals
- **Live scraping**: Monitors in-progress games with 2-second intervals for real-time odds updates
- Automatic transition handling when games move from pre-match to live status

### Subgame Support
The scraper intelligently handles period-specific markets:
- **Basketball**: Quarter markets (1st-4th quarter)
- **Football/Soccer**: Half markets (1st-2nd half)
- **Baseball**: Inning markets (1st-9th inning)
- **Tennis**: Set markets (1st-2nd set)

These subgames are fetched in parallel and merged with main game markets, allowing for comprehensive coverage of period-specific betting opportunities.

### Market Type Detection
Uses a sophisticated two-tier matching system:
1. **Exact matches**: Direct mapping for common market names
2. **Pattern matching**: Regex-based detection for period-specific markets (e.g., "Total. 1st Quarter")

### Market Coverage
Supports core market types:
- **Moneyline/1x2**: Winner markets for full game and periods
- **Spread/Handicap**: Point spread markets (including Asian and European handicaps)
- **Over/Under Totals**: Game totals and period-specific totals
- **Team Totals**: Home and away team totals
- **First to Score**: First team/player to score markets (Basketball, Soccer, Baseball)
- **Baseball-Specific**: 
  - Team with most hits (3-way)
  - Total hits over/under
  - Total home runs over/under
- **Tennis-Specific**:
  - Set totals
  - Set spreads
- Period-specific variants of all above markets (quarters, halves, innings, sets)

### Error Handling & Resilience
- Graceful handling of API failures
- Validation error tracking with separate metrics for live/prematch
- Automatic cleanup of stale games
- Exception handling at multiple levels to prevent cascading failures

## Data Flow

1. **Initialization**: 
   - Market name mappings are fetched and initialized
   - Prometheus metrics server starts

2. **Game Discovery Loop** (every 30 seconds):
   - Fetches all available games from 1xBet API for all supported sports
   - Filters games based on league whitelist
   - Creates or updates monitoring tasks for each game

3. **Game Processing**:
   - For each game, fetches the detailed game page
   - Identifies and fetches subgames if available
   - Parses markets using sport-specific parsers
   - Validates and creates standardized data models
   - Uploads to Kafka topic (configurable via environment variables)

4. **Task Management**:
   - Live games: Processed every 2 seconds
   - Pre-match games: Processed every 60 seconds
   - Stale games (not seen in 5+ minutes): Automatically removed

## Supported Sports & Leagues

### Team Sports
- **Basketball**: NBA Summer League, WNBA, NBL1, LNB leagues
- **Soccer/Football**: Premier League, La Liga, Bundesliga, Serie A, MLS, Champions League, and more
- **American Football**: NFL, CFL, NCAA
- **Ice Hockey**: NHL, SHL
- **Baseball**: MLB, KBO, various international leagues

### Individual Sports
- **Tennis**: All major tournaments
- **MMA/UFC**: All events
- **Boxing**: All events

## Technical Implementation

### Technology Stack
- **Python 3.12**: Core language
- **aiohttp**: Asynchronous HTTP client for API requests
- **asyncio**: Async/await concurrency for parallel operations
- **Pydantic**: Data validation and model serialization
- **Prometheus**: Metrics collection and monitoring

### API Endpoints
- **Pre-match games**: `https://1xbet.com/LineFeed/Get1x2_VZip`
- **Live games**: `https://1xbet.com/LiveFeed/Get1x2_VZip`
- **Game details**: `https://1xbet.com/LineFeed/GetGameZip` (prematch) / `https://1xbet.com/LiveFeed/GetGameZip` (live)
- **Market names**: `https://v2l.traincdn.com/genfiles/cms/betstemplates/betsNames_full_en.js`

### Data Models
- **OneXBetGame**: Internal representation of a game with metadata
- **OneXBetSubGame**: Subgame/period information
- **ScrapeTeamGame**: Standardized team sport game model
- **ScrapeH2HGame**: Standardized head-to-head/individual sport game model
- **ScrapeMarket**: Market with associated odds
- **ScrapeOdds**: Individual betting outcome with all odds formats

### Metrics & Monitoring
The scraper exposes Prometheus metrics:
- Successful request counts
- End-to-end processing time
- Number of games being monitored
- Validation errors
- Successful uploads
- Odds pages scraped
- Separate metrics for live vs. pre-match operations

All metrics are labeled by scraper name and live/prematch status, enabling detailed monitoring and alerting.

## Configuration

The scraper can be configured via environment variables:

- `KAFKA_BOOTSTRAP_SERVERS`: Kafka broker address (default: `localhost:9092`)
- `KAFKA_TOPIC`: Kafka topic name for scraped data (default: `scrape_games`)

See `.env.example` for configuration template.

## Deployment

The scraper is containerized using Docker and runs as a long-lived service. It automatically handles:
- Connection retries
- Rate limiting through configurable intervals
- Resource cleanup
- Health monitoring via metrics endpoint

To run with custom configuration:
```bash
docker run -e KAFKA_BOOTSTRAP_SERVERS=your-kafka:9092 -e KAFKA_TOPIC=your-topic your-image
```

## Challenges & Solutions

### Challenge: Dynamic Market Names
1xBet uses numeric IDs for markets that require lookup in JavaScript files. The scraper fetches and caches these mappings at startup, enabling efficient market type detection.

### Challenge: Period-Specific Markets
Subgames (quarters, halves, etc.) are stored separately and require additional API calls. The scraper parallelizes these requests and merges results efficiently.

### Challenge: Outcome Name Templates
1xBet uses templates with placeholders (^1^, ^2^, etc.) for team names. The scraper resolves these templates by substituting actual team/player names.

### Challenge: Live vs. Pre-match Transitions
Games can transition from pre-match to live status. The scraper detects this and seamlessly cancels prematch tasks while starting live monitoring tasks.


