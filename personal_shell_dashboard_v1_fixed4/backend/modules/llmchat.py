import os
import json
import time
import uuid
from pathlib import Path
from typing import Optional, Dict, Any, List
import httpx

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "backend" / "data"
CHATS_DIR = DATA_DIR / "chats"
CONFIG_FILE = DATA_DIR / "config.json"
CHATS_DIR.mkdir(parents=True, exist_ok=True)

def _load_config() -> Dict[str, Any]:
    if CONFIG_FILE.exists():
        try:
            return json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}

def _model_and_key() -> (str, str):
    cfg = _load_config()
    api_key = os.getenv("OPENAI_API_KEY") or cfg.get("openai", {}).get("api_key", "")
    model = cfg.get("openai", {}).get("model", "gpt-4o-mini")
    return model, api_key

def _session_path(session_id: str) -> Path:
    return CHATS_DIR / f"{session_id}.json"

def _new_session() -> str:
    sid = time.strftime("sess-%Y%m%d-%H%M%S-") + uuid.uuid4().hex[:8]
    path = _session_path(sid)
    path.write_text(json.dumps({"session_id": sid, "messages": []}, indent=2), encoding="utf-8")
    return sid

def get_history(session_id: str) -> Dict[str, Any]:
    fp = _session_path(session_id)
    if not fp.exists():
        return {"session_id": session_id, "messages": []}
    try:
        return json.loads(fp.read_text(encoding="utf-8"))
    except Exception:
        return {"session_id": session_id, "messages": []}

def _save_history(session_id: str, messages: List[Dict[str, str]]):
    fp = _session_path(session_id)
    payload = {"session_id": session_id, "messages": messages}
    fp.write_text(json.dumps(payload, indent=2), encoding="utf-8")

def _openai_chat(messages: List[Dict[str, str]], model: str, api_key: str) -> str:
    if not api_key:
        return "(No API key configured. Set OPENAI_API_KEY env var or backend/data/config.json)"
    url = "https://api.openai.com/v1/chat/completions"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    data = {"model": model, "messages": messages, "temperature": 0.7}
    try:
        with httpx.Client(timeout=60.0) as client:
            r = client.post(url, headers=headers, json=data)
            r.raise_for_status()
            js = r.json()
            return js["choices"][0]["message"]["content"]
    except Exception as e:
        return f"(OpenAI error: {e})"

def send_message(message: str, session_id: Optional[str] = None, system_prompt: Optional[str] = None, model_override: Optional[str] = None):
    if not session_id:
        session_id = _new_session()

    state = get_history(session_id)
    msgs: List[Dict[str, str]] = state.get("messages", [])

    if system_prompt:
        # Ensure system prompt is only applied once at the top
        if len(msgs) == 0 or msgs[0].get("role") != "system":
            msgs.insert(0, {"role": "system", "content": system_prompt})

    msgs.append({"role": "user", "content": message})
    model, key = _model_and_key()
    if model_override:
        model = model_override

    reply = _openai_chat(msgs, model=model, api_key=key)
    msgs.append({"role": "assistant", "content": reply})
    _save_history(session_id, msgs)

    return {"session_id": session_id, "reply": reply, "messages": msgs}
