import os
from pathlib import Path

_PACKAGE_DIR = Path(__file__).resolve().parent.parent
REFERENCES_DIR = _PACKAGE_DIR / "references"
DATA_DIR = Path(os.environ.get("OAKLEY_FINANCE_DATA_DIR", Path.home() / ".oakley-finance" / "data"))
CACHE_DIR = DATA_DIR / "cache"

TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")

WATCHED_INDICES = ["^AXJO", "^GSPC", "^DJI", "^IXIC", "^FTSE", "^N225"]
WATCHED_COMMODITIES = ["GC=F", "SI=F", "CL=F", "HG=F"]  # gold, silver, oil, copper
IRON_ORE_TICKER = "GLD"  # proxy — no direct iron ore ticker on Yahoo
DEFAULT_FOREX_PAIR = "AUDUSD=X"

CACHE_TTL = {
    "market_data": 300,     # 5 minutes
    "news": 900,            # 15 minutes
    "calendar": 3600,       # 1 hour
    "portfolio_prices": 300,  # 5 minutes
}

STALE_CACHE_MAX_AGE = 86400  # 24 hours — fallback if API fails

RATE_LIMIT_CALLS = 30
RATE_LIMIT_PERIOD = 60  # seconds

TELEGRAM_MAX_LENGTH = 4096

TIMEZONE = "Australia/Sydney"


class Config:
    """Central access point for all configuration."""

    package_dir = _PACKAGE_DIR
    references_dir = REFERENCES_DIR
    data_dir = DATA_DIR
    cache_dir = CACHE_DIR
    telegram_chat_id = TELEGRAM_CHAT_ID

    watched_indices = WATCHED_INDICES
    watched_commodities = WATCHED_COMMODITIES
    iron_ore_ticker = IRON_ORE_TICKER
    default_forex_pair = DEFAULT_FOREX_PAIR

    cache_ttl = CACHE_TTL
    stale_cache_max_age = STALE_CACHE_MAX_AGE

    rate_limit_calls = RATE_LIMIT_CALLS
    rate_limit_period = RATE_LIMIT_PERIOD

    telegram_max_length = TELEGRAM_MAX_LENGTH
    timezone = TIMEZONE

    @classmethod
    def ensure_dirs(cls):
        cls.data_dir.mkdir(parents=True, exist_ok=True)
        cls.cache_dir.mkdir(parents=True, exist_ok=True)
