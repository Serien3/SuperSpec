import json
from pathlib import Path

from superspec.engine.errors import ProtocolError
from superspec.engine.plan_loader import (
    load_state_snapshot_from_change,
    resolve_change_dir,
)
from superspec.engine.protocol import complete_action, fail_action, next_action, status_snapshot


def run_protocol_action_from_cli(repo_root: Path, change_name: str, action: str, **kwargs):
    snapshot, _ = load_state_snapshot_from_change(str(repo_root), change_name)
    runtime = snapshot["runtime"]
    expected_change_dir = resolve_change_dir(str(repo_root), change_name)
    runtime_change_name = runtime.get("changeName")
    if runtime_change_name and runtime_change_name != change_name:
        raise ProtocolError(
            "runtime.changeName does not match requested change",
            code="invalid_path",
            details={
                "change": change_name,
                "actual": runtime_change_name,
            },
        )

    change_dir = str(expected_change_dir)

    if action == "next":
        return next_action(None, change_dir, owner=kwargs.get("owner", "agent"))
    if action == "complete":
        return complete_action(None, change_dir, kwargs["action_id"], kwargs["output_payload"])
    if action == "fail":
        return fail_action(None, change_dir, kwargs["action_id"], kwargs["error_payload"])
    if action == "status":
        return status_snapshot(
            None,
            change_dir,
            debug=bool(kwargs.get("debug", False)),
            compact=bool(kwargs.get("compact", False)),
            action_limit=int(kwargs.get("action_limit", 40)),
        )
    raise ProtocolError(f"Unknown protocol action: {action}")


def to_json(payload: dict):
    return json.dumps(payload, indent=2, ensure_ascii=True)
