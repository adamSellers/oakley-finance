---
name: oakley-finance
description: "Australian finance CLI providing daily market briefings, AUD/USD forex monitoring, financial news aggregation, ASX portfolio tracking, price/news/volatility alerts, economic calendar, commodity prices, and market movers. Covers forex, ASX 200, S&P 500, gold, oil, RBA, Fed, interest rates, portfolio P&L, sector allocation, and economic events."
---

# Oakley Finance Skill

A secure, custom-built finance intelligence system for Australian markets, forex, and global indices.

## Commands

Output goes to stdout — use `message` to deliver to Telegram.

### finance brief — Full Morning Briefing

```bash
exec oakley-finance brief
```

Assembles a complete morning finance brief including:
- Triggered alerts (if any)
- AUD/USD and forex dashboard
- Global indices (ASX 200, S&P 500, Dow, NASDAQ, FTSE, Nikkei)
- Commodities (gold, silver, oil, copper)
- Top financial news (scored by relevance)
- Economic calendar (next 3 days)
- Portfolio summary (if holdings exist)

Deliver the output to Telegram via `message`. If any alerts are marked URGENT, also:
- Use TTS with the Charlie voice to read the alert summary aloud
- Send an email via Gmail with the alert details

### finance forex — Forex Data

```bash
# Default: AUD/USD
exec oakley-finance forex

# Specific pair
exec oakley-finance forex --pair EURUSD=X

# Full dashboard (all AUD pairs)
exec oakley-finance forex --dashboard

# Custom period
exec oakley-finance forex --pair AUDUSD=X --period 1mo
```

### finance news — Financial News

```bash
# Top news by relevance
exec oakley-finance news

# Filter by category: central_bank, business, markets, forex, commodities
exec oakley-finance news --category forex --limit 5

# Verbose mode (includes links and scores)
exec oakley-finance news --verbose
```

### finance portfolio — Portfolio Management

```bash
# Show portfolio with live prices and P&L
exec oakley-finance portfolio show

# Add a holding (symbol, shares, cost price)
exec oakley-finance portfolio add CBA.AX 1000 95.50

# Remove shares
exec oakley-finance portfolio remove CBA.AX 500

# Remove entire holding
exec oakley-finance portfolio remove CBA.AX

# Sector allocation
exec oakley-finance portfolio sectors

# Performance summary
exec oakley-finance portfolio performance
```

### finance alerts — Alert System

```bash
# List all alerts
exec oakley-finance alerts list

# Price alert
exec oakley-finance alerts add price AUDUSD=X below 0.6400

# News keyword alert
exec oakley-finance alerts add news --keywords RBA "interest rate"

# Volatility alert (triggers if daily move exceeds threshold)
exec oakley-finance alerts add volatility AUDUSD=X --threshold 1.5

# Remove an alert
exec oakley-finance alerts remove --alert-id 3

# Check alerts now (returns only triggered)
exec oakley-finance alerts check
```

### finance calendar — Economic Calendar

```bash
# Next 7 days (default)
exec oakley-finance calendar

# Next 14 days
exec oakley-finance calendar --days 14

# Australia only
exec oakley-finance calendar --country AU

# US events
exec oakley-finance calendar --country US
```

### finance movers — Top Market Movers

```bash
# ASX top movers (default)
exec oakley-finance movers

# Custom limit
exec oakley-finance movers --limit 10
```

### finance commodities — Commodity Prices

```bash
exec oakley-finance commodities
```

## Cron Jobs

### Morning Briefing (Weekdays 8 AM Sydney)

Schedule: `0 8 * * 1-5` (Australia/Sydney timezone)

```bash
exec oakley-finance brief
```

Deliver the full output to Telegram via `message`. This runs automatically on weekday mornings.

### Alert Check (Every 30 Minutes)

Schedule: `*/30 * * * *`

```bash
exec oakley-finance alerts check
```

Only deliver output via `message` if alerts were triggered (output is non-empty and contains "ALERTS TRIGGERED").
For URGENT alerts (e.g., large moves on primary positions), also use TTS with the Charlie voice and send an email via Gmail.

## Data Storage

- **Portfolio**: `~/.oakley-finance/data/portfolio.json` — persisted holdings
- **Alerts**: `~/.oakley-finance/data/alerts.json` — active alert rules
- **Cache**: `~/.oakley-finance/data/cache/` — temporary API response cache (auto-managed)

Set `OAKLEY_FINANCE_DATA_DIR` to override the default data location.

## Notes

- All market data comes from Yahoo Finance (free tier) with rate limiting (5 calls/min)
- News is aggregated from public RSS feeds (RBA, Google News AU, Reuters)
- Cache TTLs: market data 5min, news 15min, calendar 1hr
- If an API fails, stale cached data (up to 24hr) is returned with a stale indicator
- Output is automatically truncated to fit Telegram's 4096 character limit
- Economic calendar events are bundled in the package at `oakley_finance/references/economic_calendar_template.json`
