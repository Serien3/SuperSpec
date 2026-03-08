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


def _initial_runtime_state(definition: dict):
    now = _now_iso()
    runtime_actions = []
    for action in definition["actions"]:
        runtime_action = {
            "id": action["id"],
            "type": action["type"],
            "status": "PENDING",
            "dependsOn": action.get("dependsOn", []),
            "startedAt": None,
            "finishedAt": None,
            "error": None,
            "output": None,
        }
        for field in ("executor", "skill", "script", "prompt", "inputs"):
            if field in action:
                runtime_action[field] = action[field]
        if "human" in action:
            runtime_action["human"] = action["human"]
        runtime_actions.append(runtime_action)

    return {
        "schemaVersion": definition["schemaVersion"],
        "planId": definition["planId"],
        "changeName": definition["context"]["changeName"],
        "status": "running",
        "startedAt": now,
        "updatedAt": now,
        "actions": runtime_actions,
    }


def initialize_execution_snapshot(change_dir: str, definition: dict):
    layout = ensure_execution_layout(change_dir)
    workflow_meta = ((definition.get("metadata") or {}).get("workflow") or {})
    snapshot = {
        "meta": {
            "schemaVersion": "superspec.state/v1.0.0",
            "changeName": definition["context"]["changeName"],
            "workflowId": workflow_meta.get("id"),
            "workflowVersion": workflow_meta.get("version"),
            "createdAt": _now_iso(),
            "updatedAt": _now_iso(),
        },
        "runtime": _initial_runtime_state(definition),
    }
    write_json(layout["state"], snapshot)
    append_event(change_dir, {"event": "state.initialized", "planId": definition["planId"]})
    return snapshot


def read_execution_snapshot(change_dir: str):
    layout = ensure_execution_layout(change_dir)
    return read_json(layout["state"])


def write_execution_snapshot(change_dir: str, payload: dict):
    layout = ensure_execution_layout(change_dir)
    write_json(layout["state"], payload)


def write_execution_state(change_dir: str, payload: dict):
    layout = ensure_execution_layout(change_dir)
    snapshot = read_json(layout["state"])
    if not isinstance(snapshot, dict):
        raise ProtocolError(
            "execution snapshot not found",
            code="missing_file",
            details={"path": str(layout["state"])},
        )
    snapshot["runtime"] = payload
    meta = snapshot.get("meta")
    if isinstance(meta, dict):
        meta["updatedAt"] = _now_iso()
    write_json(layout["state"], snapshot)


def read_execution_state(change_dir: str):
    layout = ensure_execution_layout(change_dir)
    snapshot = read_json(layout["state"])
    if snapshot is None:
        return None
    if not isinstance(snapshot, dict):
        raise ProtocolError(
            f"Invalid execution snapshot file: {layout['state']}",
            code="invalid_json",
            details={"path": str(layout["state"])},
        )
    runtime = snapshot.get("runtime")
    if runtime is None:
        return None
    if not isinstance(runtime, dict):
        raise ProtocolError(
            f"Invalid runtime state in execution snapshot: {layout['state']}",
            code="invalid_json",
            details={"path": str(layout["state"])},
        )
    return runtime
