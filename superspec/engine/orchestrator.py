import json
from pathlib import Path

from superspec.engine.errors import ProtocolError
from superspec.engine.plan_loader import load_plan_from_change
from superspec.engine.protocol import complete_action, fail_action, next_action, status_snapshot


def run_protocol_next(plan: dict, change_dir: str, owner: str, lease_ttl_sec: int | None, debug: bool):
    return next_action(plan, change_dir, owner=owner, lease_ttl_sec=lease_ttl_sec, debug=debug)


def run_protocol_complete(plan: dict, change_dir: str, action_id: str, lease_id: str, result_payload: dict):
    return complete_action(plan, change_dir, action_id, lease_id, result_payload)


def run_protocol_fail(plan: dict, change_dir: str, action_id: str, lease_id: str, error_payload: dict):
    return fail_action(plan, change_dir, action_id, lease_id, error_payload)


def run_protocol_status(plan: dict, change_dir: str):
    return status_snapshot(plan, change_dir)


def run_protocol_action_from_cli(repo_root: Path, change_name: str, action: str, **kwargs):
    plan, _ = load_plan_from_change(str(repo_root), change_name)
    change_dir = str((repo_root / plan["context"]["changeDir"]).resolve())

    if action == "next":
        return run_protocol_next(plan, change_dir, kwargs.get("owner", "agent"), kwargs.get("lease_ttl_sec"), kwargs.get("debug", False))
    if action == "complete":
        return run_protocol_complete(plan, change_dir, kwargs["action_id"], kwargs["lease_id"], kwargs["result_payload"])
    if action == "fail":
        return run_protocol_fail(plan, change_dir, kwargs["action_id"], kwargs["lease_id"], kwargs["error_payload"])
    if action == "status":
        return run_protocol_status(plan, change_dir)
    raise ProtocolError(f"Unknown protocol action: {action}")


def to_json(payload: dict):
    return json.dumps(payload, indent=2, ensure_ascii=True)
