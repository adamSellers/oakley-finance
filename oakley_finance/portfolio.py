"""Portfolio management — holdings CRUD, live P&L, sector allocation."""
from __future__ import annotations

import json
from pathlib import Path

from oakley_finance.common.config import Config
from oakley_finance.common.formatting import format_price, format_change
from oakley_finance import market_data


def _portfolio_path() -> Path:
    Config.ensure_dirs()
    return Config.data_dir / "portfolio.json"


def _load_portfolio() -> dict:
    path = _portfolio_path()
    if not path.exists():
        return {"holdings": []}
    try:
        return json.loads(path.read_text())
    except (json.JSONDecodeError, OSError):
        return {"holdings": []}


def _save_portfolio(data: dict) -> None:
    path = _portfolio_path()
    path.write_text(json.dumps(data, indent=2, default=str))


def add_holding(symbol: str, shares: float, cost_price: float) -> str:
    """Add or update a holding."""
    portfolio = _load_portfolio()
    symbol = symbol.upper()

    # Check if holding exists — add to it
    for h in portfolio["holdings"]:
        if h["symbol"] == symbol:
            total_cost = (h["shares"] * h["cost_price"]) + (shares * cost_price)
            h["shares"] += shares
            h["cost_price"] = total_cost / h["shares"]
            _save_portfolio(portfolio)
            return f"Updated {symbol}: {h['shares']} shares @ avg {format_price(h['cost_price'])}"

    portfolio["holdings"].append({
        "symbol": symbol,
        "shares": shares,
        "cost_price": cost_price,
    })
    _save_portfolio(portfolio)
    return f"Added {symbol}: {shares} shares @ {format_price(cost_price)}"


def remove_holding(symbol: str, shares: Optional[float] = None) -> str:
    """Remove shares or entire holding."""
    portfolio = _load_portfolio()
    symbol = symbol.upper()

    for i, h in enumerate(portfolio["holdings"]):
        if h["symbol"] == symbol:
            if shares is None or shares >= h["shares"]:
                portfolio["holdings"].pop(i)
                _save_portfolio(portfolio)
                return f"Removed all {symbol} from portfolio"
            else:
                h["shares"] -= shares
                _save_portfolio(portfolio)
                return f"Removed {shares} shares of {symbol}. Remaining: {h['shares']}"

    return f"{symbol} not found in portfolio"


def get_portfolio_with_prices() -> list[dict]:
    """Get portfolio with live prices and P&L."""
    portfolio = _load_portfolio()
    results = []

    for h in portfolio["holdings"]:
        data = market_data.get_stock(h["symbol"])
        current_price = data["price"] if data else None
        shares = h["shares"]
        cost_price = h["cost_price"]
        cost_basis = shares * cost_price

        if current_price is not None:
            market_value = shares * current_price
            pnl = market_value - cost_basis
            pnl_pct = (pnl / cost_basis) * 100 if cost_basis else 0
        else:
            market_value = None
            pnl = None
            pnl_pct = None

        results.append({
            "symbol": h["symbol"],
            "shares": shares,
            "cost_price": cost_price,
            "current_price": current_price,
            "cost_basis": cost_basis,
            "market_value": market_value,
            "pnl": pnl,
            "pnl_pct": pnl_pct,
            "day_change_pct": data.get("change_pct") if data else None,
        })

    return results


def get_sector_allocation() -> Dict[str, float]:
    """Get sector allocation based on market value."""
    ref_path = Config.references_dir / "asx_codes.json"
    asx = json.loads(ref_path.read_text())
    stocks = asx.get("stocks", {})

    portfolio = get_portfolio_with_prices()
    total_value = sum(h["market_value"] for h in portfolio if h["market_value"])

    if not total_value:
        return {}

    sectors = {}  # type: Dict[str, float]
    for h in portfolio:
        if h["market_value"] is None:
            continue
        sector = stocks.get(h["symbol"], {}).get("sector", "Other")
        sectors[sector] = sectors.get(sector, 0) + h["market_value"]

    return {s: (v / total_value) * 100 for s, v in sectors.items()}


def format_portfolio_output(holdings: list[dict]) -> str:
    if not holdings:
        return "Portfolio is empty. Use 'finance portfolio add <symbol> <shares> <price>' to add holdings."

    lines = []
    total_cost = 0
    total_value = 0

    for h in holdings:
        symbol = h["symbol"]
        shares = h["shares"]
        price_str = format_price(h["current_price"]) if h["current_price"] else "N/A"
        value_str = format_price(h["market_value"], prefix="$") if h["market_value"] else "N/A"

        pnl_str = ""
        if h["pnl"] is not None:
            sign = "+" if h["pnl"] >= 0 else ""
            pnl_str = f" | P&L: {sign}${h['pnl']:,.2f} ({format_change(h['pnl_pct'])})"

        day_str = ""
        if h["day_change_pct"] is not None:
            day_str = f" | Day: {format_change(h['day_change_pct'])}"

        lines.append(f"  {symbol}: {shares} @ {price_str} = {value_str}{pnl_str}{day_str}")

        total_cost += h["cost_basis"]
        if h["market_value"]:
            total_value += h["market_value"]

    total_pnl = total_value - total_cost
    total_pnl_pct = (total_pnl / total_cost) * 100 if total_cost else 0

    lines.append("")
    lines.append(f"  Total Cost: {format_price(total_cost, prefix='$')}")
    lines.append(f"  Total Value: {format_price(total_value, prefix='$')}")
    sign = "+" if total_pnl >= 0 else ""
    lines.append(f"  Total P&L: {sign}${total_pnl:,.2f} ({format_change(total_pnl_pct)})")

    return "\n".join(lines)


def format_sector_output(sectors: Dict[str, float]) -> str:
    if not sectors:
        return "No sector data available."

    lines = []
    for sector, pct in sorted(sectors.items(), key=lambda x: -x[1]):
        bar_len = int(pct / 5)
        bar = "#" * bar_len
        lines.append(f"  {sector:.<30s} {pct:5.1f}% {bar}")
    return "\n".join(lines)


if __name__ == "__main__":
    print("=== Portfolio ===")
    holdings = get_portfolio_with_prices()
    print(format_portfolio_output(holdings))

    print("\n=== Sector Allocation ===")
    sectors = get_sector_allocation()
    print(format_sector_output(sectors))
