from prometheus_client import Counter, Gauge
from prometheus_summary import Summary
from prometheus_async.aio import time

time = time
requests_success_counter = Counter('scrapers_num_requests_success', 'number of successful requests made', ['scraper', 'live'])
odds_pages_scraped_counter = Counter('scrapers_num_odds_pages_scraped', 'number of odds pages scraped successfully', ['scraper', 'live'])
validation_errors_counter = Counter('scrapers_num_validation_errors', 'number of validation errors', ['scraper', 'live'])
successful_uploads_counter = Counter('scrapers_num_successful_uploads', 'number of successful uploads', ['scraper', 'live'])
num_games = Gauge('scrapers_num_games', 'number of games scraped right now', ['scraper', 'live'])
end_to_end_time = Summary("scrapers_end_to_end_latency_seconds", "Time spent to scrape and upload", ['scraper', 'live'], max_age_seconds=5 * 60, age_buckets=10)

