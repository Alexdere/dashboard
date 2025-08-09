import os
import json
from pathlib import Path
from typing import Optional, List, Dict, Any
from fastapi import FastAPI, Body, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse, PlainTextResponse
from pydantic import BaseModel

from .modules import llmchat, notes, weather, rss

BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = BASE_DIR / "frontend"
DATA_DIR = BASE_DIR / "backend" / "data"
if not DATA_DIR.exists():
    DATA_DIR.mkdir(parents=True, exist_ok=True)

SHELL_HISTORY_FILE = DATA_DIR / "shell_history.txt"

# Ensure directories exist
(DATA_DIR / "notes").mkdir(parents=True, exist_ok=True)
(DATA_DIR / "chats").mkdir(parents=True, exist_ok=True)

app = FastAPI(title="Personal Shell Dashboard V1")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static assets
app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")

# Root -> index.html
@app.get("/")
def index():
    index_path = FRONTEND_DIR / "index.html"
    return FileResponse(str(index_path))


class CommandRequest(BaseModel):
    command: str


@app.post("/api/command")
def handle_command(payload: CommandRequest):
    cmd = payload.command.strip()
    if not cmd:
        return {"type": "text", "text": ""}

    # Log history
    with open(SHELL_HISTORY_FILE, "a", encoding="utf-8") as f:
        f.write(cmd + "\n")

    # Dispatch
    lower = cmd.lower()
    if lower == "help":
        return {
            "type": "text",
            "text": (
                "Commands: llmchat | notes | notes new \"Title\" | notes open \"Title\" | "
                "history | weather | rss | help"
            ),
        }

    if lower == "llmchat":
        return {"type": "action", "action": "open", "panel": "llmchat"}

    if lower.startswith("notes"):
        # Accept:
        #   notes
        #   notes new <title...>
        #   notes open <title...>
        # Quotes optional. If no title after 'new', generate timestamped name.
        raw = cmd.strip()
        tail = raw[5:].strip()  # after 'notes'
        if not tail:
            return {"type": "action", "action": "open", "panel": "notes", "title": None}
        parts = tail.split(None, 1)
        sub = parts[0].lower()
        rest = parts[1].strip() if len(parts) > 1 else ""
        if sub == "new":
            title = rest.strip().strip('"').strip("'") if rest else notes.generate_default_title()
            title = notes.sanitize_title(title)
            notes_path = notes.get_notes_dir()
            fp = notes_path / f"{title}.md"
            if not fp.exists():
                fp.write_text("# " + title + "\n\n", encoding="utf-8")
            return {"type": "action", "action": "open", "panel": "notes", "title": title}
        if sub == "open":
            title = rest.strip().strip('"').strip("'") if rest else None
            if title:
                title = notes.sanitize_title(title)
            return {"type": "action", "action": "open", "panel": "notes", "title": title}
        # default to open panel
        return {"type": "action", "action": "open", "panel": "notes", "title": None}
    if lower == "history":
        if SHELL_HISTORY_FILE.exists():
            hist = SHELL_HISTORY_FILE.read_text(encoding="utf-8").splitlines()[-50:]
        else:
            hist = []
        return {"type": "text", "text": "\n".join(hist) or "(no history yet)"}

    if lower == "weather":
        data = weather.get_weather()
        return {"type": "text", "text": weather.render_text(data)}

    if lower == "rss":
        items = rss.get_headlines(limit=10)
        if not items:
            return {"type": "text", "text": "(no RSS configured or available)"}
        lines = [f"- {it['title']} ({it.get('source','')})" for it in items]
        return {"type": "text", "text": "\n".join(lines)}

    # Unknown -> show a hint
    return {"type": "text", "text": f"Unknown command: {cmd}\nType 'help' for commands."}


# LLM endpoints
class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    system_prompt: Optional[str] = None
    model: Optional[str] = None


@app.post("/api/llm/send")
def llm_send(req: ChatRequest):
    return llmchat.send_message(
        message=req.message,
        session_id=req.session_id,
        system_prompt=req.system_prompt,
        model_override=req.model,
    )


@app.get("/api/llm/history")
def llm_history(session_id: str):
    return llmchat.get_history(session_id)


# Notes endpoints
@app.get("/api/notes/list")
def notes_list():
    return {"notes": notes.list_notes()}


@app.get("/api/notes/open")
def notes_open(title: Optional[str] = Query(default=None)):
    return notes.open_note(title)


class NoteSave(BaseModel):
    title: str
    content: str


@app.post("/api/notes/save")
def notes_save(payload: NoteSave):
    return notes.save_note(payload.title, payload.content)


# Ambient endpoints
@app.get("/api/weather/current")
def weather_current():
    return weather.get_weather()


@app.get("/api/rss")
def rss_feed():
    items = rss.get_headlines(limit=15)
    return {"items": items}
