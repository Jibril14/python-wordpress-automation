import json
from datetime import datetime

LOG_FILE = "log.json"

def log_event(event_type: str, message: str, extra: dict = None):
    """
    Logs events to a JSON file for debugging & monitoring.
    """
    entry = {
        "time": datetime.now().isoformat(),
        "type": event_type,
        "message": message
    }
    if extra:
        entry["extra"] = extra

    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")
    except Exception as e:
        print(f"Log write error: {e}")
