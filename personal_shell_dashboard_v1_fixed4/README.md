# Personal Shell Dashboard — V1

This is a keyboard-first, browser-based personal dashboard with a shell-style command interface. 
It runs a Python (FastAPI) backend and a minimal frontend that can spawn modules like an LLM chat panel and a notes editor. 
Ambient background shows weather and an RSS ticker.

## Quick start

1) Create a virtual environment and install deps:
   python3 -m venv .venv
   source .venv/bin/activate   # Windows: .venv\Scripts\activate
   pip install -r requirements.txt

2) (Optional) Configure API keys and feeds in `backend/data/config.json`:
   {
     "openai": { "api_key": "", "model": "gpt-4o-mini" },
     "openweather": { "api_key": "", "city": "Oslo", "units": "metric" },
     "rss_feeds": ["https://news.ycombinator.com/rss"]
   }

3) Run the server:
   uvicorn backend.main:app --reload

4) Open the app:
   http://localhost:8000

## Shell commands

- `llmchat`  → Opens the LLM chat panel. Requires an OpenAI API key in config.json or env `OPENAI_API_KEY`.
- `notes`    → Opens notes editor with the last or default note.
- `notes new "Title"`   → Creates and opens a new note with Title as filename (sanitized).
- `notes open "Title"`  → Opens an existing note (or creates if missing).
- `history`  → Shows shell command history in the terminal.
- `weather`  → Prints expanded weather info in the terminal.
- `rss`      → Prints recent headlines in the terminal.
- `help`     → Shows available commands.

## Notes

- Keyboard only. Use `Esc` to return to the shell from any module.
- Ambient weather and RSS update periodically in the background.
- All data is local under `backend/data/` (notes, chats, history).

