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
            f"Invalid JSON in state file: {path}.",
            code="invalid_json",
            details={"path": str(path)},
        ) from exc


def append_event(change_dir: str, event: dict):
    layout = ensure_execution_layout(change_dir)
    event_line = {"ts": _now_iso(), **event}
    with layout["events"].open("a", encoding="utf-8") as f:
        f.write(json.dumps(event_line, ensure_ascii=True) + "\n")


def _initial_runtime_state(runtime_blueprint: dict):
    now = _now_iso()
    runtime_actions = []
    for action in runtime_blueprint["actions"]:
        runtime_action = {
            "id": action["id"],
            "description": action["description"],
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
        "changeName": runtime_blueprint["changeName"],
        "status": "running",
        "startedAt": now,
        "updatedAt": now,
        "actions": runtime_actions,
    }


def initialize_execution_snapshot(change_dir: str, runtime_blueprint: dict, workflow_schema_version: str | None = None):
    layout = ensure_execution_layout(change_dir)
    workflow_meta = runtime_blueprint.get("workflow") or {}
    snapshot = {
        "meta": {
            "schemaVersion": workflow_schema_version or "workflow.schema/unknown",
            "workflowId": workflow_meta.get("id"),
            "workflowDescription": workflow_meta.get("description"),
        },
        "runtime": _initial_runtime_state(runtime_blueprint),
    }
    write_json(layout["state"], snapshot)
    append_event(change_dir, {"event": "state.initialized", "changeName": runtime_blueprint["changeName"]})
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
            "Execution state file not found or unreadable.",
            code="missing_file",
            details={"path": str(layout["state"])},
    )
    snapshot["runtime"] = payload
    write_json(layout["state"], snapshot)


def read_execution_state(change_dir: str):
    layout = ensure_execution_layout(change_dir)
    snapshot = read_json(layout["state"])
    if snapshot is None:
        return None
    if not isinstance(snapshot, dict):
        raise ProtocolError(
            f"Invalid execution state file: {layout['state']}.",
            code="invalid_json",
            details={"path": str(layout["state"])},
        )
    runtime = snapshot.get("runtime")
    if runtime is None:
        return None
    if not isinstance(runtime, dict):
        raise ProtocolError(
            f"Invalid runtime section in state file: {layout['state']}.",
            code="invalid_json",
            details={"path": str(layout["state"])},
        )
    return runtime
