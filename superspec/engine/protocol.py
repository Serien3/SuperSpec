import os
from datetime import datetime, timedelta, timezone

from superspec.engine.constants import DEFAULTS, SUPPORTED_PROTOCOL_VERSION
from superspec.engine.context import resolve_runtime_action_fields
from superspec.engine.errors import ProtocolError
from superspec.engine.state_store import append_event, read_execution_state, write_execution_state


def _now():
    return datetime.now(timezone.utc)


def _now_iso():
    return _now().isoformat()


def _parse_iso(ts: str):
    return datetime.fromisoformat(ts)


def _resolve_executor(action, defaults):
    if action.get("executor"):
        return action["executor"]
    if action.get("script"):
        return "script"
    if action.get("skill"):
        return "skill"
    return defaults.get("executor", DEFAULTS["executor"])


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


def _build_action_payload(action: dict, resolved_action: dict, debug: bool, defaults: dict):
    action_defaults = action.get("defaults") if isinstance(action.get("defaults"), dict) else {}
    executor = _resolve_executor(resolved_action, {**DEFAULTS, **defaults, **action_defaults})
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
    defaults = {**DEFAULTS, **plan.get("defaults", {})}
    return {
        "schemaVersion": plan["schemaVersion"],
        "planId": plan["planId"],
        "changeName": plan["context"]["changeName"],
        "status": "running",
        "startedAt": now,
        "updatedAt": now,
        "defaults": defaults,
        "actions": [
            {
                "id": action["id"],
                "type": action["type"],
                "status": "PENDING",
                "dependsOn": action.get("dependsOn", []),
                "attempts": 0,
                "nextEligibleAt": None,
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

        if action_state.get("nextEligibleAt"):
            if _now() < _parse_iso(action_state["nextEligibleAt"]):
                action_state["status"] = "PENDING"
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
            action_state["nextEligibleAt"] = None
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
                    "onFail": "dependency_failed",
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

        payload = _build_action_payload(action, resolved_action, debug, state.get("defaults", {}))
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


def complete_action(plan: dict, change_dir: str, action_id: str, result_payload: dict):
    _validate_report_shape(result_payload, "result")
    state = ensure_protocol_state(plan, change_dir)

    action_state = next((a for a in state["actions"] if a["id"] == action_id), None)
    if not action_state:
        raise ProtocolError(f"Unknown action id: {action_id}", code="unknown_action")
    if action_state["status"] != "RUNNING":
        raise ProtocolError(f"Action {action_id} not completable from status {action_state['status']}", code="invalid_state")

    action_state["status"] = "SUCCESS"
    action_state["output"] = result_payload
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
    action_def = _action_by_id(plan, action_id)
    if not action_state or not action_def:
        raise ProtocolError(f"Unknown action id: {action_id}", code="unknown_action")
    if action_state["status"] != "RUNNING":
        raise ProtocolError(f"Action {action_id} not fail-reportable from status {action_state['status']}", code="invalid_state")

    defaults = {**DEFAULTS, **plan.get("defaults", {})}
    retry_defaults = defaults.get("retry", {})
    retry = {**retry_defaults, **(action_def.get("retry") or {})}
    max_attempts = int(retry.get("maxAttempts", 1))
    action_state["attempts"] = int(action_state.get("attempts", 0)) + 1
    action_state["error"] = error_payload
    action_state["finishedAt"] = _now_iso()

    if action_state["attempts"] < max_attempts:
        backoff = int(retry.get("backoffSec", 0))
        strategy = retry.get("strategy", "fixed")
        if strategy == "exponential":
            backoff *= max(1, 2 ** (action_state["attempts"] - 1))
        action_state["status"] = "PENDING"
        action_state["nextEligibleAt"] = (_now() + timedelta(seconds=backoff)).isoformat() if backoff > 0 else None
        _refresh_ready_actions(state)
        append_event(change_dir, {"event": "action.retry_scheduled", "actionId": action_id, "attempt": action_state["attempts"]})
        _persist(change_dir, state)
        return status_snapshot(plan, change_dir)

    on_fail = action_def.get("onFail") or defaults.get("onFail", "stop")
    action_state["status"] = "FAILED"
    action_state["nextEligibleAt"] = None
    if on_fail == "stop":
        state["status"] = "failed"
        state["finishedAt"] = _now_iso()
    elif on_fail != "continue":
        raise ProtocolError(f"Unsupported onFail policy: {on_fail}", code="invalid_policy")

    append_event(change_dir, {"event": "action.failed", "actionId": action_id, "onFail": on_fail})
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
            "request": ["change", "action-id", "result-json"],
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
        },
        "actionPayload": {
            "script": ["actionId", "executor", "script_command", "prompt"],
            "skill": ["actionId", "executor", "skillName", "prompt"],
            "debug": "renderedPrompt returned only when debug=true",
        },
    }


def _compact_action_entry(action: dict):
    entry = {
        "id": action["id"],
        "status": action["status"],
    }
    attempts = int(action.get("attempts") or 0)
    if attempts > 0:
        entry["attempts"] = attempts
    if action.get("error"):
        error = action["error"]
        entry["error"] = {
            "code": error.get("code"),
            "message": error.get("message"),
        }
    return entry


def status_snapshot(plan: dict, change_dir: str, debug: bool = False, compact: bool = False, action_limit: int = 40):
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
