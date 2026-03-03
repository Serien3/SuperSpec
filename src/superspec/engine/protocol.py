import os
from datetime import datetime, timezone

from superspec.engine.constants import DEFAULT_EXECUTOR, SUPPORTED_PROTOCOL_VERSION
from superspec.engine.context import resolve_runtime_action_fields
from superspec.engine.errors import ProtocolError
from superspec.engine.state_store import append_event, read_execution_state, write_execution_state


def _now():
    return datetime.now(timezone.utc)


def _now_iso():
    return _now().isoformat()


def _resolve_executor(action):
    if action.get("executor"):
        return action["executor"]
    if action.get("script"):
        return "script"
    if action.get("skill"):
        return "skill"
    if action.get("human"):
        return "human"
    return DEFAULT_EXECUTOR


def _action_runtime_outputs(state: dict):
    outputs = {}
    for action in state["actions"]:
        if action.get("output") is not None:
            outputs[action["id"]] = {"outputs": action["output"]}
    return outputs


def _resolve_action_for_payload(action: dict, state: dict, plan: dict):
    expr_context = {
        "context": plan["context"],
        "variables": plan.get("variables", {}),
        "actions": _action_runtime_outputs(state),
        "env": dict(os.environ),
    }
    try:
        return resolve_runtime_action_fields(action, expr_context)
    except ValueError as exc:
        raise ProtocolError(
            f"Action {action['id']} has invalid runtime expression: {exc}",
            code="invalid_expression",
            details={"actionId": action["id"]},
        ) from exc


def _build_action_payload(action: dict, resolved_action: dict, debug: bool):
    executor = _resolve_executor(resolved_action)
    payload = {
        "actionId": action["id"],
        "executor": executor,
    }

    if executor == "script":
        command = resolved_action.get("script")
        if not command:
            raise ProtocolError(
                f"Action {action['id']} script executor requires script field",
                code="invalid_action_payload",
            )
        payload["script_command"] = command
        payload["prompt"] = f"Run script command for action {action['id']}"
        return payload

    if executor == "human":
        human = resolved_action.get("human") or action.get("human")
        if not isinstance(human, dict) or not human.get("instruction"):
            raise ProtocolError(
                f"Action {action['id']} human executor requires human.instruction",
                code="invalid_action_payload",
            )
        payload["human"] = human
        payload["prompt"] = human.get("instruction") or f"Wait for human review on action {action['id']}"
        return payload

    skill_name = resolved_action.get("skill") or action.get("skill") or action.get("type")
    payload["skillName"] = skill_name
    payload["prompt"] = f"Invoke skill {skill_name} for action {action['id']}"

    if debug:
        prompt = (resolved_action.get("inputs") or {}).get("prompt")
        if prompt:
            payload["debug"] = {"renderedPrompt": prompt}

    return payload


def _initial_protocol_state(plan: dict):
    now = _now_iso()
    return {
        "schemaVersion": plan["schemaVersion"],
        "planId": plan["planId"],
        "changeName": plan["context"]["changeName"],
        "status": "running",
        "startedAt": now,
        "updatedAt": now,
        "actions": [
            {
                "id": action["id"],
                "type": action["type"],
                "status": "PENDING",
                "dependsOn": action.get("dependsOn", []),
                "startedAt": None,
                "finishedAt": None,
                "error": None,
                "output": None,
            }
            for action in plan["actions"]
        ],
    }


def ensure_protocol_state(plan: dict, change_dir: str):
    state = read_execution_state(change_dir)
    if state is None:
        state = _initial_protocol_state(plan)
        write_execution_state(change_dir, state)
        append_event(change_dir, {"event": "state.initialized", "planId": plan["planId"]})
    return state


def _persist(change_dir: str, state: dict):
    state["updatedAt"] = _now_iso()
    write_execution_state(change_dir, state)


def _completed_ids(state: dict):
    return {
        a["id"]
        for a in state["actions"]
        if a["status"] == "SUCCESS"
    }


def _dependencies_satisfied(action_state: dict, completed: set[str]):
    for dep in action_state.get("dependsOn", []):
        if dep not in completed:
            return False
    return True


def _refresh_ready_actions(state: dict):
    completed = _completed_ids(state)
    for action_state in state["actions"]:
        if action_state["status"] not in {"PENDING", "READY"}:
            continue

        if _dependencies_satisfied(action_state, completed):
            action_state["status"] = "READY"
        else:
            action_state["status"] = "PENDING"


def _action_by_id(plan: dict, action_id: str):
    for action in plan["actions"]:
        if action["id"] == action_id:
            return action
    return None


def _action_state_by_id(state: dict, action_id: str):
    for action in state["actions"]:
        if action["id"] == action_id:
            return action
    return None


def _propagate_dependency_failures(change_dir: str, state: dict):
    # Repeatedly collapse blocked dependents into FAILED for deterministic termination.
    while True:
        transitioned = False
        for action_state in state["actions"]:
            if action_state["status"] not in {"PENDING", "READY"}:
                continue

            failed_dep = None
            for dep in action_state.get("dependsOn", []):
                dep_state = _action_state_by_id(state, dep)
                if dep_state and dep_state["status"] == "FAILED":
                    failed_dep = dep
                    break
            if not failed_dep:
                continue

            action_state["status"] = "FAILED"
            action_state["finishedAt"] = _now_iso()
            action_state["error"] = {
                "code": "dependency_failed",
                "message": f"Blocked by failed dependency: {failed_dep}",
                "dependency": failed_dep,
            }
            append_event(
                change_dir,
                {
                    "event": "action.failed",
                    "actionId": action_state["id"],
                    "reason": "dependency_failed",
                    "dependency": failed_dep,
                },
            )
            transitioned = True

        if not transitioned:
            return


def _terminalize_if_done(change_dir: str, state: dict):
    remaining = [a for a in state["actions"] if a["status"] in {"PENDING", "READY", "RUNNING"}]
    if not remaining:
        has_failed = any(a["status"] == "FAILED" for a in state["actions"])
        state["status"] = "failed" if has_failed else "success"
        state["finishedAt"] = _now_iso()
        append_event(change_dir, {"event": "state.terminal", "status": state["status"]})


def next_action(plan: dict, change_dir: str, owner: str = "agent", debug: bool = False):
    state = ensure_protocol_state(plan, change_dir)
    _refresh_ready_actions(state)

    if state["status"] in {"success", "failed"}:
        _persist(change_dir, state)
        return {
            "state": "done",
            "changeName": plan["context"]["changeName"],
            "action": None,
        }

    for action_state in state["actions"]:
        if action_state["status"] != "READY":
            continue
        action = _action_by_id(plan, action_state["id"])
        if not action:
            continue

        resolved_action = _resolve_action_for_payload(action, state, plan)
        action_state["status"] = "RUNNING"
        action_state["startedAt"] = _now_iso()

        payload = _build_action_payload(action, resolved_action, debug)
        append_event(
            change_dir,
            {
                "event": "action.started",
                "actionId": action_state["id"],
                "owner": owner,
            },
        )
        _persist(change_dir, state)
        return {
            "state": "ready",
            "changeName": plan["context"]["changeName"],
            "action": payload,
        }

    _terminalize_if_done(change_dir, state)
    _persist(change_dir, state)
    if state["status"] in {"success", "failed"}:
        return {
            "state": "done",
            "changeName": plan["context"]["changeName"],
            "action": None,
        }

    return {
        "state": "blocked",
        "changeName": plan["context"]["changeName"],
        "action": None,
    }


def _validate_report_shape(payload: dict, key: str):
    if not isinstance(payload, dict):
        raise ProtocolError(f"{key} payload must be a JSON object", code="invalid_payload")


def complete_action(plan: dict, change_dir: str, action_id: str, output_payload: dict):
    _validate_report_shape(output_payload, "output")
    state = ensure_protocol_state(plan, change_dir)

    action_state = next((a for a in state["actions"] if a["id"] == action_id), None)
    if not action_state:
        raise ProtocolError(f"Unknown action id: {action_id}", code="unknown_action")
    if action_state["status"] != "RUNNING":
        raise ProtocolError(f"Action {action_id} not completable from status {action_state['status']}", code="invalid_state")

    action_state["status"] = "SUCCESS"
    action_state["output"] = output_payload
    action_state["error"] = None
    action_state["finishedAt"] = _now_iso()

    append_event(change_dir, {"event": "action.completed", "actionId": action_id})
    _refresh_ready_actions(state)
    _terminalize_if_done(change_dir, state)
    _persist(change_dir, state)
    return status_snapshot(plan, change_dir)


def fail_action(plan: dict, change_dir: str, action_id: str, error_payload: dict):
    _validate_report_shape(error_payload, "error")
    state = ensure_protocol_state(plan, change_dir)

    action_state = next((a for a in state["actions"] if a["id"] == action_id), None)
    if not action_state or not _action_by_id(plan, action_id):
        raise ProtocolError(f"Unknown action id: {action_id}", code="unknown_action")
    if action_state["status"] != "RUNNING":
        raise ProtocolError(f"Action {action_id} not fail-reportable from status {action_state['status']}", code="invalid_state")

    action_state["error"] = error_payload
    action_state["finishedAt"] = _now_iso()
    action_state["status"] = "FAILED"
    state["status"] = "failed"
    state["finishedAt"] = _now_iso()

    append_event(change_dir, {"event": "action.failed", "actionId": action_id, "reason": "reported_failure"})
    _propagate_dependency_failures(change_dir, state)
    _refresh_ready_actions(state)
    _terminalize_if_done(change_dir, state)
    _persist(change_dir, state)
    return status_snapshot(plan, change_dir)


def _contracts_payload():
    return {
        "next": {
            "states": ["ready", "blocked", "done"],
            "fields": ["state", "changeName", "action"],
            "errors": ["invalid_expression", "invalid_action_payload"],
        },
        "complete": {
            "request": ["change", "action-id", "output-json"],
            "errors": ["invalid_payload", "unknown_action", "invalid_state"],
        },
        "fail": {
            "request": ["change", "action-id", "error-json"],
            "errors": ["invalid_payload", "unknown_action", "invalid_state"],
        },
        "status": {
            "fields": ["status", "progress", "lastFailure", "actions"],
            "actionStates": ["PENDING", "READY", "RUNNING", "SUCCESS", "FAILED"],
            "debugFields": ["contracts"],
            "modes": {
                "default": "compact action summaries",
                "full": "full action objects",
            },
        },
        "actionPayload": {
            "script": ["actionId", "executor", "script_command", "prompt"],
            "skill": ["actionId", "executor", "skillName", "prompt"],
            "human": ["actionId", "executor", "human", "prompt"],
            "debug": "renderedPrompt returned only when debug=true",
        },
    }


def _compact_action_entry(action: dict):
    entry = {
        "id": action["id"],
        "status": action["status"],
    }
    if action.get("error"):
        error = action["error"]
        entry["error"] = {
            "code": error.get("code"),
            "message": error.get("message"),
        }
    return entry


def status_snapshot(
    plan: dict,
    change_dir: str,
    debug: bool = False,
    compact: bool = False,
    action_limit: int = 40,
):
    state = ensure_protocol_state(plan, change_dir)
    done = len([a for a in state["actions"] if a["status"] == "SUCCESS"])
    failed = len([a for a in state["actions"] if a["status"] == "FAILED"])
    running = len([a for a in state["actions"] if a["status"] == "RUNNING"])

    last_failure = None
    for action in reversed(state["actions"]):
        if action.get("status") == "FAILED" and action.get("error"):
            last_failure = {"actionId": action["id"], "error": action["error"]}
            break

    payload = {
        "changeName": plan["context"]["changeName"],
        "schemaVersion": plan["schemaVersion"],
        "protocolVersion": SUPPORTED_PROTOCOL_VERSION,
        "status": state["status"],
        "progress": {
            "total": len(state["actions"]),
            "done": done,
            "failed": failed,
            "running": running,
            "remaining": len(state["actions"]) - done - failed - running,
        },
        "lastFailure": last_failure,
    }
    if compact:
        limit = max(1, int(action_limit))
        compact_actions = [_compact_action_entry(action) for action in state["actions"][:limit]]
        payload["actions"] = compact_actions
        payload["actionsOmitted"] = max(0, len(state["actions"]) - len(compact_actions))
    else:
        payload["actions"] = state["actions"]
    if debug:
        payload["contracts"] = _contracts_payload()
    return payload
