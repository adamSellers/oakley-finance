"""Price, news, and volatility alerts with check cycle."""
from __future__ import annotations

import json
from pathlib import Path
from datetime import datetime

from oakley_finance.common.config import Config
from oakley_finance.common.formatting import format_price, format_change, now_aedt
from oakley_finance import market_data
from oakley_finance import news_scanner


def _alerts_path() -> Path:
    Config.ensure_dirs()
    return Config.data_dir / "alerts.json"


def _load_alerts() -> list[dict]:
    path = _alerts_path()
    if not path.exists():
        return []
    try:
        return json.loads(path.read_text())
    except (json.JSONDecodeError, OSError):
        return []


def _save_alerts(alerts: list[dict]) -> None:
    path = _alerts_path()
    path.write_text(json.dumps(alerts, indent=2, default=str))


def _next_id(alerts: list[dict]) -> int:
    if not alerts:
        return 1
    return max(a.get("id", 0) for a in alerts) + 1


def add_price_alert(symbol: str, condition: str, target: float) -> str:
    """Add a price alert. condition is 'above' or 'below'."""
    if condition not in ("above", "below"):
        return "Condition must be 'above' or 'below'"

    alerts = _load_alerts()
    alert = {
        "id": _next_id(alerts),
        "type": "price",
        "symbol": symbol.upper(),
        "condition": condition,
        "target": target,
        "created": now_aedt().isoformat(),
        "triggered": False,
    }
    alerts.append(alert)
    _save_alerts(alerts)
    return f"Alert #{alert['id']}: Notify when {symbol.upper()} goes {condition} {format_price(target)}"


def add_news_alert(keywords: list[str]) -> str:
    """Add a news keyword alert."""
    alerts = _load_alerts()
    alert = {
        "id": _next_id(alerts),
        "type": "news",
        "keywords": [k.upper() for k in keywords],
        "created": now_aedt().isoformat(),
        "triggered": False,
    }
    alerts.append(alert)
    _save_alerts(alerts)
    return f"Alert #{alert['id']}: Watching news for: {', '.join(keywords)}"


def add_volatility_alert(symbol: str, threshold_pct: float) -> str:
    """Add a volatility alert — triggers if daily change exceeds threshold."""
    alerts = _load_alerts()
    alert = {
        "id": _next_id(alerts),
        "type": "volatility",
        "symbol": symbol.upper(),
        "threshold_pct": threshold_pct,
        "created": now_aedt().isoformat(),
        "triggered": False,
    }
    alerts.append(alert)
    _save_alerts(alerts)
    return f"Alert #{alert['id']}: Notify when {symbol.upper()} moves more than {threshold_pct}% in a day"


def remove_alert(alert_id: int) -> str:
    """Remove an alert by ID."""
    alerts = _load_alerts()
    for i, a in enumerate(alerts):
        if a.get("id") == alert_id:
            alerts.pop(i)
            _save_alerts(alerts)
            return f"Removed alert #{alert_id}"
    return f"Alert #{alert_id} not found"


def list_alerts() -> list[dict]:
    return _load_alerts()


def check_alerts() -> list[dict]:
    """Check all active alerts and return triggered ones."""
    alerts = _load_alerts()
    triggered = []

    for alert in alerts:
        if alert.get("triggered"):
            continue

        if alert["type"] == "price":
            data = market_data.get_stock(alert["symbol"])
            if data:
                price = data["price"]
                if alert["condition"] == "above" and price >= alert["target"]:
                    alert["triggered"] = True
                    alert["trigger_time"] = now_aedt().isoformat()
                    alert["trigger_price"] = price
                    triggered.append(alert)
                elif alert["condition"] == "below" and price <= alert["target"]:
                    alert["triggered"] = True
                    alert["trigger_time"] = now_aedt().isoformat()
                    alert["trigger_price"] = price
                    triggered.append(alert)

        elif alert["type"] == "volatility":
            data = market_data.get_stock(alert["symbol"])
            if data:
                change = abs(data.get("change_pct", 0))
                if change >= alert["threshold_pct"]:
                    alert["triggered"] = True
                    alert["trigger_time"] = now_aedt().isoformat()
                    alert["trigger_change_pct"] = data["change_pct"]
                    triggered.append(alert)

        elif alert["type"] == "news":
            matches = news_scanner.scan_for_keywords(alert["keywords"], limit=3)
            if matches:
                alert["triggered"] = True
                alert["trigger_time"] = now_aedt().isoformat()
                alert["matched_headlines"] = [m["title"] for m in matches[:3]]
                triggered.append(alert)

    _save_alerts(alerts)
    return triggered


def format_alerts_list(alerts: list[dict]) -> str:
    if not alerts:
        return "No active alerts. Use 'finance alerts add' to create one."

    lines = []
    for a in alerts:
        status = "TRIGGERED" if a.get("triggered") else "active"
        if a["type"] == "price":
            lines.append(
                f"  #{a['id']} [{status}] {a['symbol']} {a['condition']} "
                f"{format_price(a['target'])} (price alert)"
            )
        elif a["type"] == "news":
            lines.append(
                f"  #{a['id']} [{status}] Keywords: {', '.join(a['keywords'])} (news alert)"
            )
        elif a["type"] == "volatility":
            lines.append(
                f"  #{a['id']} [{status}] {a['symbol']} >{a['threshold_pct']}% move (volatility alert)"
            )
    return "\n".join(lines)


def format_triggered_output(triggered: list[dict]) -> str:
    if not triggered:
        return ""

    lines = ["ALERTS TRIGGERED:"]
    for a in triggered:
        if a["type"] == "price":
            lines.append(
                f"  #{a['id']} {a['symbol']} hit {format_price(a.get('trigger_price'))} "
                f"(target: {a['condition']} {format_price(a['target'])})"
            )
        elif a["type"] == "volatility":
            lines.append(
                f"  #{a['id']} {a['symbol']} moved {format_change(a.get('trigger_change_pct'))} "
                f"(threshold: {a['threshold_pct']}%)"
            )
        elif a["type"] == "news":
            lines.append(f"  #{a['id']} News match for: {', '.join(a['keywords'])}")
            for h in a.get("matched_headlines", []):
                lines.append(f"    - {h}")
    return "\n".join(lines)


if __name__ == "__main__":
    print("=== Alerts ===")
    all_alerts = list_alerts()
    print(format_alerts_list(all_alerts))

    print("\n=== Checking Alerts ===")
    triggered = check_alerts()
    if triggered:
        print(format_triggered_output(triggered))
    else:
        print("No alerts triggered.")
