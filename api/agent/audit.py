"""Log of every /ask request, one JSON object per line.

ASK_LOG_PATH is a file locally ("logs/ask.jsonl") and "-" in production, where
entries go to stdout: Cloud Run's disk does not survive restarts, and Cloud
Logging stores stdout lines as structured entries.
"""
from __future__ import annotations

import json
import sys
import threading
from datetime import datetime, timezone
from pathlib import Path

_lock = threading.Lock()
STDOUT = "-"


def log_ask(path: str | Path, record: dict) -> None:
    entry = {"timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds"), **record}
    line = json.dumps({"message": "ask", **entry} if str(path) == STDOUT else entry, default=str)
    with _lock:
        if str(path) == STDOUT:
            print(line, file=sys.stdout, flush=True)
            return
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as log:
            log.write(line + "\n")
