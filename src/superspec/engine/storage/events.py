import json
from datetime import datetime, timezone

from superspec.engine.storage.execution_files import ensure_execution_layout


def now_iso():
    return datetime.now(timezone.utc).isoformat()


def append_event(change_dir: str, event: dict):
    layout = ensure_execution_layout(change_dir)
    event_line = {"ts": now_iso(), **event}
    with layout["events"].open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(event_line, ensure_ascii=True) + "\n")
