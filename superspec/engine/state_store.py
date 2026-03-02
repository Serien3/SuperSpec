import json
from datetime import datetime, timezone
from pathlib import Path


def _now_iso():
    return datetime.now(timezone.utc).isoformat()


def create_run_layout(change_dir: str, run_id: str):
    run_dir = Path(change_dir) / "runs" / run_id
    logs_dir = run_dir / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    return run_dir, logs_dir


def write_run_state(change_dir: str, run_id: str, state: dict):
    run_dir, _ = create_run_layout(change_dir, run_id)
    run_state_path = run_dir / "state.json"
    run_state_path.write_text(json.dumps(state, indent=2), encoding="utf-8")

    latest_path = Path(change_dir) / "run-state.json"
    latest_path.write_text(json.dumps(state, indent=2), encoding="utf-8")
    return str(run_state_path), str(latest_path)


def load_latest_run_state(change_dir: str):
    latest_path = Path(change_dir) / "run-state.json"
    if not latest_path.exists():
        return None
    return json.loads(latest_path.read_text(encoding="utf-8"))


def create_initial_state(plan: dict, run_id: str):
    now = _now_iso()
    return {
        "runId": run_id,
        "planId": plan["planId"],
        "changeName": plan["context"]["changeName"],
        "schemaVersion": plan["schemaVersion"],
        "status": "running",
        "startedAt": now,
        "updatedAt": now,
        "actions": [
            {
                "id": action["id"],
                "type": action["type"],
                "status": "PENDING",
                "attempts": 0,
                "startedAt": None,
                "finishedAt": None,
                "error": None,
                "output": None,
            }
            for action in plan["actions"]
        ],
    }


def patch_state_timestamps(state: dict):
    state["updatedAt"] = _now_iso()


def finalise_state(state: dict, status: str):
    state["status"] = status
    state["finishedAt"] = _now_iso()
    patch_state_timestamps(state)
