from pathlib import Path

def save_draft(title: str, content: str):
    path = Path("data/drafts")
    path.mkdir(parents=True, exist_ok=True)
    safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '_')).rstrip()
    file_path = path / f"{safe_title}.txt"
    with file_path.open("w", encoding="utf-8") as f:
        f.write(content)
    return file_path
