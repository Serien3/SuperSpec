import json
from datetime import datetime, timezone
from pathlib import Path

from superspec.engine.errors import ProtocolError


def _now_iso():
    return datetime.now(timezone.utc).isoformat()


def execution_dir(change_dir: str) -> Path:
    return Path(change_dir) / "execution"


def ensure_execution_layout(change_dir: str):
    base = execution_dir(change_dir)
    base.mkdir(parents=True, exist_ok=True)
    return {
        "dir": base,
        "state": base / "state.json",
        "events": base / "events.log",
    }


def write_json(path: Path, payload: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def read_json(path: Path, default=None):
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ProtocolError(
            f"Invalid JSON state file: {path}",
            code="invalid_json",
            details={"path": str(path)},
        ) from exc


def append_event(change_dir: str, event: dict):
    layout = ensure_execution_layout(change_dir)
    event_line = {"ts": _now_iso(), **event}
    with layout["events"].open("a", encoding="utf-8") as f:
        f.write(json.dumps(event_line, ensure_ascii=True) + "\n")


def write_execution_state(change_dir: str, payload: dict):
    layout = ensure_execution_layout(change_dir)
    write_json(layout["state"], payload)


def read_execution_state(change_dir: str):
    layout = ensure_execution_layout(change_dir)
    return read_json(layout["state"])
