"""Local log of every /ask request, one JSON object per line."""
from __future__ import annotations

import json
import threading
from datetime import datetime, timezone
from pathlib import Path

_lock = threading.Lock()


def log_ask(path: str | Path, record: dict) -> None:
    path = Path(path)
    entry = {"timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds"), **record}
    with _lock:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as log:
            log.write(json.dumps(entry, default=str) + "\n")
