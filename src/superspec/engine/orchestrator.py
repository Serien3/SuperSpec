import json
from pathlib import Path

from superspec.engine.errors import ProtocolError
from superspec.engine.plan_loader import load_plan_from_change, resolve_change_dir_from_plan_context
from superspec.engine.protocol import complete_action, fail_action, next_action, status_snapshot


def run_protocol_action_from_cli(repo_root: Path, change_name: str, action: str, **kwargs):
    plan, _ = load_plan_from_change(str(repo_root), change_name)
    change_dir = str(resolve_change_dir_from_plan_context(repo_root, plan["context"]["changeDir"]))

    if action == "next":
        return next_action(plan, change_dir, owner=kwargs.get("owner", "agent"), debug=kwargs.get("debug", False))
    if action == "complete":
        return complete_action(plan, change_dir, kwargs["action_id"], kwargs["output_payload"])
    if action == "fail":
        return fail_action(plan, change_dir, kwargs["action_id"], kwargs["error_payload"])
    if action == "status":
        return status_snapshot(
            plan,
            change_dir,
            debug=bool(kwargs.get("debug", False)),
            compact=bool(kwargs.get("compact", False)),
            action_limit=int(kwargs.get("action_limit", 40)),
        )
    raise ProtocolError(f"Unknown protocol action: {action}")


def to_json(payload: dict):
    return json.dumps(payload, indent=2, ensure_ascii=True)
