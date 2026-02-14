"""RSS news aggregation with keyword relevance scoring."""
from __future__ import annotations

import json
from datetime import datetime, timezone

import feedparser

from oakley_finance.common.config import Config
from oakley_finance.common.cache import FileCache
from oakley_finance.common.formatting import format_datetime_aedt

_cache = FileCache("news")


def _load_feeds_config() -> dict:
    path = Config.references_dir / "rss_feeds.json"
    return json.loads(path.read_text())


def _score_item(title: str, summary: str, keywords: dict) -> int:
    """Score a news item by keyword relevance."""
    text = (title + " " + summary).upper()
    score = 0
    for word in keywords.get("high", []):
        if word.upper() in text:
            score += 3
    for word in keywords.get("medium", []):
        if word.upper() in text:
            score += 2
    for word in keywords.get("low", []):
        if word.upper() in text:
            score += 1
    return score


def _parse_feed(url: str, max_items: int = 10, timeout: int = 10) -> list[dict]:
    """Parse a single RSS feed with a socket timeout."""
    import socket
    old_timeout = socket.getdefaulttimeout()
    try:
        socket.setdefaulttimeout(timeout)
        feed = feedparser.parse(url)
        items = []
        for entry in feed.entries[:max_items]:
            published = None
            if hasattr(entry, "published_parsed") and entry.published_parsed:
                published = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)

            items.append({
                "title": entry.get("title", "No title"),
                "summary": entry.get("summary", ""),
                "link": entry.get("link", ""),
                "published": published.isoformat() if published else None,
            })
        return items
    except Exception:
        return []
    finally:
        socket.setdefaulttimeout(old_timeout)


def scan_news(category: Optional[str] = None, limit: int = 15) -> list:
    """Scan all configured RSS feeds, score by relevance, return top items."""
    cache_key = f"news_{category or 'all'}"
    cached = _cache.get(cache_key, ttl=Config.cache_ttl["news"])
    if cached is not None:
        return cached[:limit]

    config = _load_feeds_config()
    feeds = config["feeds"]
    keywords = config["keyword_weights"]
    max_per_feed = config.get("max_items_per_feed", 10)

    all_items = []
    for feed_id, feed_info in feeds.items():
        if category and feed_info.get("category") != category:
            continue

        items = _parse_feed(feed_info["url"], max_per_feed)
        for item in items:
            item["source"] = feed_info["name"]
            item["category"] = feed_info.get("category", "general")
            item["priority"] = feed_info.get("priority", "medium")
            item["score"] = _score_item(
                item["title"], item.get("summary", ""), keywords
            )
        all_items.extend(items)

    # Deduplicate by title similarity
    seen_titles = set()
    unique_items = []
    for item in all_items:
        title_key = item["title"][:60].lower()
        if title_key not in seen_titles:
            seen_titles.add(title_key)
            unique_items.append(item)

    # Sort by score descending, then by priority
    priority_order = {"high": 0, "medium": 1, "low": 2}
    unique_items.sort(
        key=lambda x: (-x["score"], priority_order.get(x["priority"], 1))
    )

    max_total = config.get("max_total_items", 30)
    result = unique_items[:max_total]
    _cache.set(cache_key, result)
    return result[:limit]


def scan_for_keywords(keywords: list[str], limit: int = 10) -> list[dict]:
    """Scan news for specific keywords (used by alert system)."""
    all_news = scan_news(limit=50)
    matched = []
    for item in all_news:
        text = (item["title"] + " " + item.get("summary", "")).upper()
        for kw in keywords:
            if kw.upper() in text:
                item["matched_keyword"] = kw
                matched.append(item)
                break
    return matched[:limit]


def format_news_output(items: list[dict], verbose: bool = False) -> str:
    if not items:
        return "No news items found."

    lines = []
    for i, item in enumerate(items, 1):
        stale = " (cached)" if item.get("_stale") else ""
        score_str = f" [score:{item['score']}]" if verbose else ""
        lines.append(f"{i}. {item['title']}{score_str}{stale}")
        lines.append(f"   Source: {item['source']} | {item['category']}")
        if verbose and item.get("link"):
            lines.append(f"   {item['link']}")
        lines.append("")
    return "\n".join(lines)


if __name__ == "__main__":
    print("=== Financial News ===\n")
    news = scan_news(limit=10)
    print(format_news_output(news, verbose=True))
