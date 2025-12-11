from shared import metrics
scraper = "onexbet"
time = metrics.time

live_requests_success_counter = metrics.requests_success_counter.labels(scraper=scraper, live='true')
live_odds_pages_scraped_counter = metrics.odds_pages_scraped_counter.labels(scraper=scraper, live='true')
live_validation_errors_counter = metrics.validation_errors_counter.labels(scraper=scraper, live='true')
live_successful_uploads_counter = metrics.successful_uploads_counter.labels(scraper=scraper, live='true')
live_num_games = metrics.num_games.labels(scraper=scraper, live='true')
live_end_to_end_time = metrics.end_to_end_time.labels(scraper=scraper, live='true')

# prematch metrics
prematch_requests_success_counter = metrics.requests_success_counter.labels(scraper=scraper, live='false')
prematch_odds_pages_scraped_counter = metrics.odds_pages_scraped_counter.labels(scraper=scraper, live='false')
prematch_validation_errors_counter = metrics.validation_errors_counter.labels(scraper=scraper, live='false')
prematch_successful_uploads_counter = metrics.successful_uploads_counter.labels(scraper=scraper, live='false')
prematch_num_games = metrics.num_games.labels(scraper=scraper, live='false')
prematch_end_to_end_time = metrics.end_to_end_time.labels(scraper=scraper, live='false') 