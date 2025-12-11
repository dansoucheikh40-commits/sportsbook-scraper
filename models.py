from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field


class Odds(BaseModel):
    american_odds: int
    decimal_odds: float
    fractional_num: int
    fractional_den: int


class ScrapeOdds(Odds):
    outcome_type: str
    sportsbook: str
    scrape_ts: datetime
    spread: Optional[float]
    live: bool
    available: bool
    deeplink: str = Field(default="")
    alt: bool = False

    def implied_prob(self) -> float:
        if self.american_odds < 0:
            return self.american_odds / (self.american_odds - 100)
        else:
            return 100 / (self.american_odds + 100)

    def set_is_alt(self):
        self.alt = True


class ScrapeMarket(BaseModel):
    market_type: str
    odds: List[ScrapeOdds]


class ScrapeGame(BaseModel):
    sport: str
    markets: List[ScrapeMarket]
    league: Optional[str] = None
    date: Optional[datetime] = None


class ScrapeTeamGame(ScrapeGame):
    home_team: str
    away_team: str


class ScrapeH2HGame(ScrapeGame):
    player_1: str
    player_2: str

