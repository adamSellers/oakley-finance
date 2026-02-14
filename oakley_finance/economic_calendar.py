"""Economic calendar from local JSON template."""
from __future__ import annotations

import json
from datetime import datetime, timedelta

from oakley_finance.common.config import Config
from oakley_finance.common.cache import FileCache
from oakley_finance.common.formatting import now_aedt

_cache = FileCache("calendar")


def _load_template() -> dict:
    path = Config.references_dir / "economic_calendar_template.json"
    return json.loads(path.read_text())


def get_upcoming_events(days: int = 7, country: Optional[str] = None) -> list:
    """Get upcoming economic events within the specified number of days."""
    cache_key = f"calendar_{days}_{country or 'all'}"
    cached = _cache.get(cache_key, ttl=Config.cache_ttl["calendar"])
    if cached is not None:
        return cached

    template = _load_template()
    today = now_aedt().date()
    cutoff = today + timedelta(days=days)

    events = []
    for event in template.get("upcoming_events", []):
        try:
            event_date = datetime.strptime(event["date"], "%Y-%m-%d").date()
        except (ValueError, KeyError):
            continue

        if today <= event_date <= cutoff:
            if country and event.get("country") != country:
                continue
            events.append(event)

    events.sort(key=lambda x: x["date"])
    _cache.set(cache_key, events)
    return events


def get_recurring_events(country: Optional[str] = None) -> list:
    """Get recurring event descriptions (for reference)."""
    template = _load_template()
    events = template.get("recurring_events", [])
    if country:
        events = [e for e in events if e.get("country") == country]
    return events


def format_calendar_output(events: list[dict]) -> str:
    if not events:
        return "No upcoming events in the specified period."

    lines = []
    current_date = None
    for event in events:
        event_date = event.get("date", "Unknown")
        if event_date != current_date:
            current_date = event_date
            try:
                dt = datetime.strptime(event_date, "%Y-%m-%d")
                lines.append(f"\n{dt.strftime('%a %d %b %Y')}:")
            except ValueError:
                lines.append(f"\n{event_date}:")

        impact = event.get("impact", "medium").upper()
        time_str = event.get("time_aedt", "")
        time_part = f" ({time_str} AEDT)" if time_str else ""
        flag = {"AU": "AU", "US": "US", "EU": "EU", "CN": "CN"}.get(
            event.get("country", ""), ""
        )
        lines.append(f"  [{impact}] {flag} {event['name']}{time_part}")

    return "\n".join(lines)


if __name__ == "__main__":
    print("=== Economic Calendar (next 14 days) ===")
    events = get_upcoming_events(days=14)
    print(format_calendar_output(events))

    print("\n\n=== Recurring AU Events ===")
    for e in get_recurring_events(country="AU"):
        print(f"  {e['name']} - {e['frequency']} ({e['impact']} impact)")
