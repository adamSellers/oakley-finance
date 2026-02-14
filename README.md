# oakley-finance

Australian finance CLI tool and [OpenClaw](https://github.com/openclaw/openclaw) skill providing daily market briefings, forex monitoring, news aggregation, portfolio tracking, price alerts, and economic calendar data — delivered via Telegram.

## Features

- **Daily Briefings** — Automated weekday morning reports with forex, indices, commodities, news, and portfolio summary
- **Forex Monitoring** — AUD/USD and 12 other currency pairs with live prices from Yahoo Finance
- **Global Indices** — ASX 200, S&P 500, Dow Jones, NASDAQ, FTSE 100, Nikkei 225
- **Commodities** — Gold, silver, crude oil, copper
- **News Aggregation** — RSS feeds from RBA, Google News AU, and Reuters with keyword relevance scoring
- **Portfolio Tracking** — Add/remove holdings, live P&L, sector allocation
- **Price Alerts** — Price targets, news keyword watches, and volatility threshold alerts
- **Economic Calendar** — Upcoming AU/US/EU/CN economic events with impact ratings
- **ASX Market Movers** — Top gainers and losers from the ASX 200

## Installation

Requires Python 3.8+.

```bash
# Standard install
pip install .

# With pipx (recommended for CLI tools)
pipx install .

# Editable mode (development)
pip install -e .
```

## Usage

```bash
# Full morning briefing
oakley-finance brief

# Forex
oakley-finance forex                           # AUD/USD (default)
oakley-finance forex --pair EURUSD=X           # Specific pair
oakley-finance forex --dashboard               # All tracked pairs

# News
oakley-finance news                            # Top stories by relevance
oakley-finance news --category forex --limit 5 # Filtered
oakley-finance news --verbose                  # Include links and scores

# Portfolio
oakley-finance portfolio show                  # Holdings with live P&L
oakley-finance portfolio add CBA.AX 1000 95.50 # Add holding
oakley-finance portfolio remove CBA.AX 500     # Remove shares
oakley-finance portfolio sectors               # Sector allocation

# Alerts
oakley-finance alerts list
oakley-finance alerts add price AUDUSD=X below 0.6400
oakley-finance alerts add news --keywords RBA "interest rate"
oakley-finance alerts add volatility AUDUSD=X --threshold 1.5
oakley-finance alerts check                    # Check for triggered alerts

# Economic Calendar
oakley-finance calendar                        # Next 7 days
oakley-finance calendar --days 14 --country AU # AU events, 14 days

# Market Movers & Commodities
oakley-finance movers --limit 10
oakley-finance commodities
```

## OpenClaw Integration

This tool is designed as an [OpenClaw](https://github.com/openclaw/openclaw) skill. Place the `SKILL.md` in your workspace skills directory:

```
~/.openclaw/workspace/skills/oakley-finance/
└── SKILL.md
```

OpenClaw's agent will call `oakley-finance` CLI commands and deliver output to Telegram via its native `message` tool.

### Scheduled Jobs

| Schedule | Command | Description |
|----------|---------|-------------|
| `0 8 * * 1-5` (Sydney) | `oakley-finance brief` | Weekday morning briefing |
| `*/30 * * * *` | `oakley-finance alerts check` | Alert monitoring |

### Environment Variables

| Variable | Purpose |
|----------|---------|
| `TELEGRAM_CHAT_ID` | Required by OpenClaw for message delivery |
| `OAKLEY_FINANCE_DATA_DIR` | Override default data directory (`~/.oakley-finance/data/`) |

## Data Sources

- **Market Data** — [Yahoo Finance](https://finance.yahoo.com/) via yfinance (free tier, rate-limited to 5 calls/min)
- **News** — Public RSS feeds from RBA, Google News AU, Reuters
- **Economic Calendar** — Manually maintained JSON template bundled with the package

## Architecture

```
oakley_finance/
├── cli.py                # CLI entry point (argparse subcommands)
├── daily_briefing.py     # Morning brief orchestrator
├── market_data.py        # yfinance wrapper (forex, indices, commodities, stocks)
├── news_scanner.py       # RSS aggregation + keyword relevance scoring
├── portfolio.py          # Holdings CRUD, live P&L, sector allocation
├── alerts.py             # Price/news/volatility alerts with check cycle
├── economic_calendar.py  # Template-based upcoming events
├── references/           # Bundled reference data (ASX codes, forex pairs, RSS feeds)
└── common/
    ├── config.py         # Paths, constants, env vars
    ├── cache.py          # File-based JSON cache with TTL + 24hr stale fallback
    ├── rate_limiter.py   # Token-bucket rate limiter
    └── formatting.py     # Telegram-safe formatting, AEDT timezone utilities
```

## License

Private use.
