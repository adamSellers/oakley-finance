"""Market data fetcher using yfinance — forex, indices, commodities, stocks, movers."""
from __future__ import annotations

import json

import yfinance as yf

from oakley_finance.common.config import Config
from oakley_finance.common.cache import FileCache
from oakley_finance.common.rate_limiter import RateLimiter
from oakley_finance.common.formatting import format_price, format_change

_cache = FileCache("market_data")
_limiter = RateLimiter()


def _load_reference(filename: str) -> dict:
    path = Config.references_dir / filename
    return json.loads(path.read_text())


def _fetch_ticker(symbol: str, period: str = "5d") -> Optional[dict]:
    """Fetch ticker data with caching and rate limiting."""
    cache_key = f"{symbol}_{period}"
    cached = _cache.get(cache_key, ttl=Config.cache_ttl["market_data"])
    if cached is not None:
        return cached

    _limiter.acquire()
    try:
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period=period)
        if hist.empty:
            return None

        last = hist.iloc[-1]
        prev = hist.iloc[-2] if len(hist) > 1 else hist.iloc[0]
        close = float(last["Close"])
        prev_close = float(prev["Close"])
        change_pct = ((close - prev_close) / prev_close) * 100 if prev_close else 0

        result = {
            "symbol": symbol,
            "price": close,
            "previous_close": prev_close,
            "change_pct": change_pct,
            "high": float(last["High"]),
            "low": float(last["Low"]),
            "volume": int(last["Volume"]) if last["Volume"] else 0,
        }
        _cache.set(cache_key, result)
        return result
    except Exception:
        # Stale fallback
        stale = _cache.get(cache_key, ttl=Config.stale_cache_max_age)
        return stale


def get_forex(pair: Optional[str] = None, period: str = "5d") -> Optional[dict]:
    """Get forex pair data. Defaults to AUD/USD."""
    if pair is None:
        pair = Config.default_forex_pair
    return _fetch_ticker(pair, period)


def get_forex_dashboard() -> list[dict]:
    """Get all AUD pairs and major crosses."""
    ref = _load_reference("forex_pairs.json")
    results = []
    for symbol, info in ref["primary"].items():
        data = _fetch_ticker(symbol)
        if data:
            data["name"] = info["name"]
            results.append(data)
    return results


def get_indices() -> list[dict]:
    """Get major world indices."""
    index_names = {
        "^AXJO": "ASX 200",
        "^GSPC": "S&P 500",
        "^DJI": "Dow Jones",
        "^IXIC": "NASDAQ",
        "^FTSE": "FTSE 100",
        "^N225": "Nikkei 225",
    }
    results = []
    for symbol in Config.watched_indices:
        data = _fetch_ticker(symbol)
        if data:
            data["name"] = index_names.get(symbol, symbol)
            results.append(data)
    return results


def get_commodities() -> list[dict]:
    """Get commodity prices."""
    commodity_names = {
        "GC=F": "Gold",
        "SI=F": "Silver",
        "CL=F": "Crude Oil (WTI)",
        "HG=F": "Copper",
    }
    results = []
    for symbol in Config.watched_commodities:
        data = _fetch_ticker(symbol)
        if data:
            data["name"] = commodity_names.get(symbol, symbol)
            results.append(data)
    return results


def get_stock(symbol: str) -> Optional[dict]:
    """Get single stock data."""
    return _fetch_ticker(symbol)


def get_movers(market: str = "asx", limit: int = 5) -> dict:
    """Get top movers from ASX stocks."""
    ref = _load_reference("asx_codes.json")
    stocks = ref.get("stocks", {})

    all_data = []
    for symbol, info in stocks.items():
        data = _fetch_ticker(symbol)
        if data:
            data["name"] = info["name"]
            data["sector"] = info["sector"]
            all_data.append(data)

    all_data.sort(key=lambda x: abs(x.get("change_pct", 0)), reverse=True)

    gainers = sorted(
        [d for d in all_data if d.get("change_pct", 0) > 0],
        key=lambda x: x["change_pct"],
        reverse=True,
    )[:limit]

    losers = sorted(
        [d for d in all_data if d.get("change_pct", 0) < 0],
        key=lambda x: x["change_pct"],
    )[:limit]

    return {"gainers": gainers, "losers": losers}


def format_forex_output(data: Optional[dict]) -> str:
    if not data:
        return "Forex data unavailable"
    stale = " (stale)" if data.get("_stale") else ""
    return (
        f"{data.get('name', data['symbol'])}: "
        f"{format_price(data['price'], decimals=4)} "
        f"({format_change(data['change_pct'])}){stale}\n"
        f"  High: {format_price(data['high'], decimals=4)} | "
        f"Low: {format_price(data['low'], decimals=4)}"
    )


def format_indices_output(indices: list[dict]) -> str:
    lines = []
    for idx in indices:
        stale = " *" if idx.get("_stale") else ""
        lines.append(
            f"  {idx['name']}: {format_price(idx['price'])} "
            f"({format_change(idx['change_pct'])}){stale}"
        )
    return "\n".join(lines)


def format_commodities_output(commodities: list[dict]) -> str:
    lines = []
    for c in commodities:
        stale = " *" if c.get("_stale") else ""
        lines.append(
            f"  {c['name']}: {format_price(c['price'])} "
            f"({format_change(c['change_pct'])}){stale}"
        )
    return "\n".join(lines)


def format_movers_output(movers: dict) -> str:
    lines = ["Top Gainers:"]
    for g in movers.get("gainers", []):
        lines.append(
            f"  {g['name']} ({g['symbol']}): "
            f"{format_price(g['price'])} ({format_change(g['change_pct'])})"
        )
    lines.append("\nTop Losers:")
    for l in movers.get("losers", []):
        lines.append(
            f"  {l['name']} ({l['symbol']}): "
            f"{format_price(l['price'])} ({format_change(l['change_pct'])})"
        )
    return "\n".join(lines)


if __name__ == "__main__":
    print("=== AUD/USD ===")
    audusd = get_forex()
    print(format_forex_output(audusd))

    print("\n=== Indices ===")
    print(format_indices_output(get_indices()))

    print("\n=== Commodities ===")
    print(format_commodities_output(get_commodities()))
