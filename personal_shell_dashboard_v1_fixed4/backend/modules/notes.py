import re
from pathlib import Path
from typing import List, Dict, Any, Optional

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "backend" / "data"
NOTES_DIR = DATA_DIR / "notes"
NOTES_DIR.mkdir(parents=True, exist_ok=True)

def sanitize_title(title: str) -> str:
    title = title.strip()
    title = re.sub(r"[^\w\-. ]", "_", title)
    title = re.sub(r"\s+", "_", title)
    if not title:
        title = "untitled"
    return title

def list_notes() -> List[str]:
    return sorted([p.stem for p in NOTES_DIR.glob("*.md")])

def open_note(title: Optional[str] = None) -> Dict[str, Any]:
    if title:
        filename = sanitize_title(title) + ".md"
    else:
        # Use last modified note if any, else default
        notes = sorted(NOTES_DIR.glob("*.md"), key=lambda p: p.stat().st_mtime, reverse=True)
        if notes:
            filename = notes[0].name
        else:
            filename = "default.md"
            (NOTES_DIR / filename).write_text("# default\n\n", encoding="utf-8")
    fp = NOTES_DIR / filename
    if not fp.exists():
        fp.write_text("# " + fp.stem + "\n\n", encoding="utf-8")
    return {"title": fp.stem, "content": fp.read_text(encoding="utf-8")}

def save_note(title: str, content: str) -> Dict[str, Any]:
    filename = sanitize_title(title) + ".md"
    fp = NOTES_DIR / filename
    fp.write_text(content, encoding="utf-8")
    return {"ok": True, "title": Path(filename).stem}
