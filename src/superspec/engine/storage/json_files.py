import json
from pathlib import Path

from superspec.engine.errors import ProtocolError


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
            f"Invalid JSON in state file: {path}.",
            code="invalid_json",
            details={"path": str(path)},
        ) from exc
