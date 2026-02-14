# CLAUDE.md - Oakley Finance Skill

## Project Status: BUILT — Ready to Deploy

All modules implemented, tested locally, and packaged as `oakley-finance` CLI tool. Pending deployment to `oakley@bot.oakroad`.

---

## Implementation Summary

OpenClaw custom skill providing daily market briefings, forex monitoring, news aggregation, portfolio tracking, price alerts, and economic calendar — delivered via Telegram.

### What's Built

- **`oakley-finance` CLI tool** with 8 subcommands: brief, forex, news, portfolio, alerts, calendar, movers, commodities
- **Daily briefing orchestrator** — assembles all sections, truncates to 4096 chars for Telegram
- **Market data** via yfinance — forex (7 AUD pairs + 6 major crosses), indices (ASX/S&P/Dow/NASDAQ/FTSE/Nikkei), commodities (gold/silver/oil/copper), individual stocks
- **News scanner** — RSS aggregation from 8 feeds (RBA, Google News AU, Reuters) with keyword relevance scoring
- **Portfolio manager** — CRUD operations, live P&L, sector allocation
- **Alert system** — price/news/volatility alerts with check cycle
- **Economic calendar** — template-based upcoming events (manually maintained)
- **Caching** — file-based JSON cache with TTL (5min market, 15min news, 1hr calendar) + 24hr stale fallback
- **Rate limiting** — token-bucket at 5 calls/min for Yahoo Finance

---

## File Structure

```
/home/adza/code/Oakley_finance/
├── SKILL.md                              # OpenClaw skill definition
├── claude.md                             # This file
├── pyproject.toml                        # Package metadata + entry point
├── setup.cfg                             # Fallback for older pip
├── setup.py                              # Minimal setup shim
├── .gitignore                            # Ignores data/, __pycache__/, .env
├── oakley_finance/                       # Python package
│   ├── __init__.py                       # Package init, version
│   ├── cli.py                            # CLI dispatcher (argparse subcommands)
│   ├── daily_briefing.py                 # Morning brief orchestrator
│   ├── market_data.py                    # yfinance wrapper
│   ├── news_scanner.py                   # RSS aggregation + scoring
│   ├── portfolio.py                      # Holdings CRUD + live P&L
│   ├── alerts.py                         # Price/news/volatility alerts
│   ├── economic_calendar.py              # Template-based events
│   ├── references/                       # Bundled reference data
│   │   ├── asx_codes.json                # Top 50 ASX tickers with sectors
│   │   ├── forex_pairs.json              # AUD pairs + major crosses
│   │   ├── rss_feeds.json                # RSS feed URLs + keyword weights
│   │   └── economic_calendar_template.json
│   └── common/
│       ├── __init__.py
│       ├── config.py                     # Paths, constants, env vars
│       ├── cache.py                      # FileCache with TTL + stale fallback
│       ├── rate_limiter.py               # Token-bucket limiter
│       └── formatting.py                 # Telegram-safe formatting, AEDT timezone
└── data/                                 # Local dev runtime (gitignored)
```

---

## Installation

```bash
pip install .                # Standard install
pip install -e .             # Editable (dev) — requires pip >= 21.3
```

Creates the `oakley-finance` binary in PATH.

## Usage

```bash
oakley-finance brief                           # Full morning briefing
oakley-finance forex                           # AUD/USD
oakley-finance forex --dashboard               # All pairs
oakley-finance news --category forex --limit 5 # Filtered news
oakley-finance portfolio show                  # Portfolio with live P&L
oakley-finance alerts check                    # Check triggered alerts
oakley-finance calendar --country AU           # AU economic events
oakley-finance movers                          # ASX top movers
oakley-finance commodities                     # Gold, silver, oil, copper
```

## Data Location

Runtime data (portfolio, alerts, cache) stored at `~/.oakley-finance/data/`.
Override with `OAKLEY_FINANCE_DATA_DIR` env var.

---

## Deployment — Next Steps

**Target server:** `oakley@bot.oakroad` (192.168.1.65)
- Python 3.12.3
- OpenClaw workspace at `~/.openclaw/workspace`
- Skills dir at `~/.openclaw/workspace/skills/`

### Remaining deployment tasks:

1. **ROTATE ALL API KEYS** — openclaw.json credentials were exposed

2. **Install on server:**
   ```bash
   sudo apt install python3-pip -y
   cd ~/oakley-finance-staging && pip install .
   ```

3. **Verify CLI works:**
   ```bash
   oakley-finance brief
   ```

4. **Copy SKILL.md to skills dir:**
   ```bash
   cp ~/oakley-finance-staging/SKILL.md ~/.openclaw/workspace/skills/oakley-finance/SKILL.md
   ```

5. **Add `TELEGRAM_CHAT_ID` to openclaw.json env vars**

6. **Set up cron jobs** (either via OpenClaw or system crontab)

---

## Key Design Decisions

1. **Proper CLI tool** — `pip install` creates `oakley-finance` binary, just like other OpenClaw skills wrap CLI tools
2. **Scripts print to stdout, OpenClaw delivers** — Python never calls Telegram directly
3. **File-based JSON cache** with TTL — no external cache deps
4. **Token-bucket rate limiter** — prevents Yahoo Finance blocking
5. **Each briefing section wrapped in try/except** — one failing source doesn't kill the briefing
6. **Stale cache fallback** — expired cache (up to 24hr) returned if API fails
7. **Telegram 4096 char limit** — `truncate_for_telegram()` ensures output fits
8. **Voice/email for URGENT alerts** — SKILL.md instructs OpenClaw agent to use TTS + Gmail
9. **`from __future__ import annotations`** on all modules — Python 3.8+ compatibility

## Plan Reference

Full implementation plan at: `~/.claude/plans/immutable-questing-sedgewick.md`
