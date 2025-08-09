import os
import json
import time
from pathlib import Path
from typing import Dict, Any
import httpx

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "backend" / "data"
CACHE_FILE = DATA_DIR / "weather_cache.json"
CONFIG_FILE = DATA_DIR / "config.json"

def _load_config():
    if CONFIG_FILE.exists():
        try:
            return json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}

def _fetch_weather() -> Dict[str, Any]:
    cfg = _load_config()
    ow = cfg.get("openweather", {})
    api_key = os.getenv("OPENWEATHER_API_KEY") or ow.get("api_key", "")
    city = ow.get("city", "Oslo")
    units = ow.get("units", "metric")

    if not api_key:
        return {"status": "unconfigured", "city": city}

    url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units={units}"
    try:
        with httpx.Client(timeout=20.0) as client:
            r = client.get(url)
            r.raise_for_status()
            data = r.json()
            return {"status": "ok", "data": data, "city": city, "units": units}
    except Exception as e:
        return {"status": "error", "error": str(e)}

def get_weather() -> Dict[str, Any]:
    # Cache for 20 minutes
    now = time.time()
    if CACHE_FILE.exists():
        try:
            js = json.loads(CACHE_FILE.read_text(encoding="utf-8"))
            if now - js.get("ts", 0) < 1200:
                return js["payload"]
        except Exception:
            pass
    payload = _fetch_weather()
    CACHE_FILE.write_text(json.dumps({"ts": now, "payload": payload}, indent=2), encoding="utf-8")
    return payload

def render_text(payload: Dict[str, Any]) -> str:
    status = payload.get("status")
    if status == "unconfigured":
        return "(Weather not configured. Set OPENWEATHER_API_KEY or config.json openweather)"
    if status != "ok":
        return f"(Weather error: {payload.get('error','unknown')})"
    data = payload.get("data", {})
    main = data.get("main", {})
    weather_list = data.get("weather", [])
    wdesc = weather_list[0]["description"] if weather_list else "n/a"
    temp = main.get("temp")
    feels = main.get("feels_like")
    city = payload.get("city", "")
    return f"{city}: {wdesc}, {temp}°, feels {feels}°"
