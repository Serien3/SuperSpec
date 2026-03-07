import json
from pathlib import Path

from superspec.engine.errors import ProtocolError
from superspec.engine.plan_loader import (
    load_state_snapshot_from_change,
    resolve_change_dir,
    resolve_change_dir_from_definition_context,
)
from superspec.engine.protocol import complete_action, fail_action, next_action, status_snapshot


def run_protocol_action_from_cli(repo_root: Path, change_name: str, action: str, **kwargs):
    snapshot, _ = load_state_snapshot_from_change(str(repo_root), change_name)
    definition = snapshot["definition"]
    expected_change_dir = resolve_change_dir(str(repo_root), change_name)
    resolved_change_dir = resolve_change_dir_from_definition_context(repo_root, definition["context"]["changeDir"])
    if resolved_change_dir != expected_change_dir:
        raise ProtocolError(
            "context.changeDir does not match requested change",
            code="invalid_path",
            details={
                "change": change_name,
                "expected": str(expected_change_dir),
                "actual": str(resolved_change_dir),
            },
        )

    change_dir = str(resolved_change_dir)

    if action == "next":
        return next_action(definition, change_dir, owner=kwargs.get("owner", "agent"))
    if action == "complete":
        return complete_action(definition, change_dir, kwargs["action_id"], kwargs["output_payload"])
    if action == "fail":
        return fail_action(definition, change_dir, kwargs["action_id"], kwargs["error_payload"])
    if action == "status":
        return status_snapshot(
            definition,
            change_dir,
            debug=bool(kwargs.get("debug", False)),
            compact=bool(kwargs.get("compact", False)),
            action_limit=int(kwargs.get("action_limit", 40)),
        )
    raise ProtocolError(f"Unknown protocol action: {action}")


def to_json(payload: dict):
    return json.dumps(payload, indent=2, ensure_ascii=True)
