import json
from pathlib import Path

from superspec.engine.changes.paths import (
    load_execution_snapshot_for_change,
    resolve_change_dir,
)
from superspec.engine.execution.actions import complete_step, fail_step, next_step
from superspec.engine.execution.status import status_snapshot
from superspec.engine.errors import ProtocolError


def run_protocol_action_from_cli(repo_root: Path, change_name: str, command: str, **kwargs):
    snapshot, _ = load_execution_snapshot_for_change(str(repo_root), change_name)
    runtime = snapshot["runtime"]
    expected_change_dir = resolve_change_dir(str(repo_root), change_name)
    runtime_change_name = runtime.get("changeName")
    if runtime_change_name and runtime_change_name != change_name:
        raise ProtocolError(
            "Execution state belongs to a different change.",
            code="invalid_path",
            details={
                "change": change_name,
                "actual": runtime_change_name,
            },
        )

    change_dir = str(expected_change_dir)

    if command == "next":
        return next_step(None, change_dir, owner=kwargs.get("owner", "agent"))
    if command == "complete":
        return complete_step(None, change_dir, kwargs["step_id"])
    if command == "fail":
        return fail_step(None, change_dir, kwargs["step_id"])
    if command == "status":
        return status_snapshot(
            None,
            change_dir,
            debug=bool(kwargs.get("debug", False)),
            compact=bool(kwargs.get("compact", False)),
            step_limit=int(kwargs.get("step_limit", 40)),
        )
    raise ProtocolError(f"Unsupported protocol command '{command}'.", code="invalid_arguments")


def to_json(payload: dict):
    return json.dumps(payload, indent=2, ensure_ascii=True)
