from __future__ import annotations

from datetime import datetime

import pytz

from .config import Config

_tz = pytz.timezone(Config.timezone)


def now_aedt() -> datetime:
    return datetime.now(_tz)


def format_datetime_aedt(dt: Optional[datetime] = None, fmt: str = "%d %b %Y %H:%M AEDT") -> str:
    if dt is None:
        dt = now_aedt()
    elif dt.tzinfo is None:
        dt = _tz.localize(dt)
    return dt.strftime(fmt)


def format_price(value: Optional[float] = None, decimals: int = 2, prefix: str = "") -> str:
    if value is None:
        return "N/A"
    return f"{prefix}{value:,.{decimals}f}"


def format_change(value: Optional[float] = None, decimals: int = 2) -> str:
    if value is None:
        return "N/A"
    sign = "+" if value >= 0 else ""
    return f"{sign}{value:.{decimals}f}%"


def format_currency_line(name: str, price: Optional[float] = None, change_pct: Optional[float] = None) -> str:
    p = format_price(price, decimals=4 if price and price < 10 else 2)
    c = format_change(change_pct)
    return f"  {name}: {p} ({c})"


def format_section_header(title: str) -> str:
    return f"**{title}**"


def truncate_for_telegram(text: str, max_length: int = Config.telegram_max_length) -> str:
    if len(text) <= max_length:
        return text
    truncated = text[: max_length - 30]
    last_newline = truncated.rfind("\n")
    if last_newline > max_length // 2:
        truncated = truncated[:last_newline]
    return truncated + "\n\n... (truncated)"
