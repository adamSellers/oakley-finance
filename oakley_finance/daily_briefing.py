"""Morning briefing orchestrator — assembles all sections into a formatted brief."""

import sys

from oakley_finance.common.formatting import (
    format_section_header,
    format_datetime_aedt,
    truncate_for_telegram,
    now_aedt,
)


def _build_forex_section() -> str:
    try:
        from oakley_finance import market_data
        from oakley_finance.common.formatting import format_price, format_change

        audusd = market_data.get_forex()
        if not audusd:
            return ""
        lines = [format_section_header("AUD/USD & Forex")]
        lines.append(market_data.format_forex_output(audusd))

        dashboard = market_data.get_forex_dashboard()
        other_pairs = [d for d in dashboard if d.get("symbol") != "AUDUSD=X"]
        for pair in other_pairs[:4]:

            stale = " *" if pair.get("_stale") else ""
            lines.append(
                f"  {pair['name']}: {format_price(pair['price'], decimals=4)} "
                f"({format_change(pair['change_pct'])}){stale}"
            )
        return "\n".join(lines)
    except Exception as e:
        return f"[Forex data unavailable: {e}]"


def _build_indices_section() -> str:
    try:
        from oakley_finance import market_data

        indices = market_data.get_indices()
        if not indices:
            return ""
        return (
            format_section_header("Global Indices")
            + "\n"
            + market_data.format_indices_output(indices)
        )
    except Exception as e:
        return f"[Indices unavailable: {e}]"


def _build_commodities_section() -> str:
    try:
        from oakley_finance import market_data

        commodities = market_data.get_commodities()
        if not commodities:
            return ""
        return (
            format_section_header("Commodities")
            + "\n"
            + market_data.format_commodities_output(commodities)
        )
    except Exception as e:
        return f"[Commodities unavailable: {e}]"


def _build_news_section() -> str:
    try:
        from oakley_finance import news_scanner

        news = news_scanner.scan_news(limit=5)
        if not news:
            return ""
        lines = [format_section_header("Top Financial News")]
        for i, item in enumerate(news, 1):
            lines.append(f"  {i}. {item['title']}")
            lines.append(f"     ({item['source']})")
        return "\n".join(lines)
    except Exception as e:
        return f"[News unavailable: {e}]"


def _build_calendar_section() -> str:
    try:
        from oakley_finance import economic_calendar

        events = economic_calendar.get_upcoming_events(days=3)
        if not events:
            return ""
        return (
            format_section_header("Economic Calendar (next 3 days)")
            + "\n"
            + economic_calendar.format_calendar_output(events)
        )
    except Exception as e:
        return f"[Calendar unavailable: {e}]"


def _build_portfolio_section() -> str:
    try:
        from oakley_finance import portfolio

        holdings = portfolio.get_portfolio_with_prices()
        if not holdings:
            return ""
        return (
            format_section_header("Portfolio Summary")
            + "\n"
            + portfolio.format_portfolio_output(holdings)
        )
    except Exception as e:
        return f"[Portfolio unavailable: {e}]"


def _build_alerts_section() -> str:
    try:
        from oakley_finance import alerts

        triggered = alerts.check_alerts()
        if not triggered:
            return ""
        return alerts.format_triggered_output(triggered)
    except Exception as e:
        return f"[Alerts unavailable: {e}]"


def build_briefing() -> str:
    """Build the full morning briefing."""
    now = now_aedt()
    date_str = format_datetime_aedt(now, fmt="%A %d %b %Y")

    header = f"Morning Finance Brief — {date_str}"

    sections = [
        _build_alerts_section(),
        _build_forex_section(),
        _build_indices_section(),
        _build_commodities_section(),
        _build_news_section(),
        _build_calendar_section(),
        _build_portfolio_section(),
    ]

    # Filter empty sections
    sections = [s for s in sections if s.strip()]

    body = f"{header}\n{'=' * len(header)}\n\n" + "\n\n".join(sections)
    return truncate_for_telegram(body)


if __name__ == "__main__":
    print(build_briefing())
