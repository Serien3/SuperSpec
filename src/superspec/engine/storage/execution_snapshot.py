from datetime import datetime, timezone

from superspec.engine.errors import ProtocolError
from superspec.engine.storage.execution_files import ensure_execution_layout
from superspec.engine.storage.json_files import read_json, write_json


def now_iso():
    return datetime.now(timezone.utc).isoformat()


def initial_runtime_state(runtime_blueprint: dict):
    now = now_iso()
    runtime_steps = []
    for step in runtime_blueprint["steps"]:
        runtime_step = {
            "id": step["id"],
            "description": step["description"],
            "status": "PENDING",
            "dependsOn": step.get("dependsOn", []),
            "startedAt": None,
            "finishedAt": None,
        }
        for field in ("executor", "skill", "script", "prompt"):
            if field in step:
                runtime_step[field] = step[field]
        if "option" in step:
            runtime_step["option"] = step["option"]
        runtime_steps.append(runtime_step)

    runtime = {
        "changeName": runtime_blueprint["changeName"],
        "status": "running",
        "startedAt": now,
        "updatedAt": now,
        "steps": runtime_steps,
    }
    runtime_goal = runtime_blueprint.get("goal")
    if runtime_goal is not None:
        runtime["goal"] = runtime_goal
    return runtime


def initialize_execution_snapshot(change_dir: str, runtime_blueprint: dict):
    layout = ensure_execution_layout(change_dir)
    workflow_meta = runtime_blueprint.get("workflow") or {}
    snapshot_meta = dict(workflow_meta) if isinstance(workflow_meta, dict) else {}
    snapshot = {
        "meta": snapshot_meta,
        "runtime": initial_runtime_state(runtime_blueprint),
    }
    write_json(layout["state"], snapshot)
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
            details={"path": str(layout['state'])},
        )
    runtime = snapshot.get("runtime")
    if runtime is None:
        return None
    if not isinstance(runtime, dict):
        raise ProtocolError(
            f"Invalid runtime section in state file: {layout['state']}.",
            code="invalid_json",
            details={"path": str(layout['state'])},
        )
    return runtime
