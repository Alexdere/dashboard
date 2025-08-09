import json
from typing import List, Dict, Any
from pathlib import Path
import feedparser

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "backend" / "data"
CONFIG_FILE = DATA_DIR / "config.json"

def _load_config():
    if CONFIG_FILE.exists():
        try:
            return json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}

def get_headlines(limit: int = 10) -> List[Dict[str, Any]]:
    cfg = _load_config()
    feeds = cfg.get("rss_feeds", [])
    items: List[Dict[str, Any]] = []
    for url in feeds:
        try:
            parsed = feedparser.parse(url)
            src = parsed.feed.get("title", url) if hasattr(parsed, "feed") else url
            for entry in parsed.entries[:limit]:
                items.append({
                    "title": entry.get("title", ""),
                    "link": entry.get("link", ""),
                    "source": src
                })
        except Exception:
            continue
    # De-duplicate and trim
    seen = set()
    unique = []
    for it in items:
        key = (it["title"], it["link"])
        if key in seen:
            continue
        seen.add(key)
        unique.append(it)
    return unique[:limit]
