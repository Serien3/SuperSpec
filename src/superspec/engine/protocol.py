from datetime import datetime, timezone

from superspec.engine.constants import SUPPORTED_PROTOCOL_VERSION
from superspec.engine.errors import ProtocolError
from superspec.engine.state_store import (
    append_event,
    initialize_execution_snapshot,
    read_execution_state,
    write_execution_state,
)

_VALID_EXECUTORS = {"skill", "script", "human"}


def _now():
    return datetime.now(timezone.utc)


def _now_iso():
    return _now().isoformat()


def _resolve_executor(action):
    executor = action.get("executor")
    if isinstance(executor, str) and executor:
        return executor
    return None


def _runtime_blueprint_from_seed(runtime_seed: dict):
    context = runtime_seed.get("context") if isinstance(runtime_seed, dict) else None
    change_name = context.get("changeName") if isinstance(context, dict) else None
    if not isinstance(change_name, str) or not change_name:
        raise ProtocolError(
            "Missing change name in runtime seed. Provide a non-empty change name when initializing execution state.",
            code="invalid_payload",
        )
    return {
        "changeName": change_name,
        "workflow": {},
        "actions": runtime_seed.get("actions", []),
    }


def _action_runtime_outputs(state: dict):
    outputs = {}
    for action in state["actions"]:
        if action.get("output") is not None:
            outputs[action["id"]] = {"outputs": action["output"]}
    return outputs


def _build_action_payload(action: dict):
    executor = _resolve_executor(action)
    if executor is None:
        raise ProtocolError(
            f"Invalid action '{action['id']}': missing executor.",
            code="invalid_action_payload",
        )
    if executor not in _VALID_EXECUTORS:
        raise ProtocolError(
            f"Invalid action '{action['id']}': unsupported executor '{executor}'.",
            code="invalid_action_payload",
        )

    rendered_prompt = action.get("prompt")
    if rendered_prompt is not None and not isinstance(rendered_prompt, str):
        raise ProtocolError(
            f"Invalid action '{action['id']}': prompt must be a string.",
            code="invalid_action_payload",
        )
    rendered_inputs = action.get("inputs")
    if rendered_inputs is not None and not isinstance(rendered_inputs, dict):
        raise ProtocolError(
            f"Invalid action '{action['id']}': inputs must be an object.",
            code="invalid_action_payload",
        )
    payload = {
        "actionId": action["id"],
        "executor": executor,
    }
    if rendered_inputs is not None:
        payload["inputs"] = rendered_inputs

    if executor == "script":
        command = action.get("script")
        if not isinstance(command, str) or not command:
            raise ProtocolError(
                f"Invalid action '{action['id']}': script executor requires a non-empty script command.",
                code="invalid_action_payload",
            )
        payload["script_command"] = command
        payload["prompt"] = rendered_prompt or f"Run script command for action {action['id']}"
        return payload

    if executor == "human":
        human = action.get("human")
        if not isinstance(human, dict) or not isinstance(human.get("instruction"), str) or not human.get("instruction"):
            raise ProtocolError(
                f"Invalid action '{action['id']}': human executor requires a non-empty instruction.",
                code="invalid_action_payload",
            )
        payload["human"] = human
        payload["prompt"] = rendered_prompt or human.get("instruction") or f"Wait for human review on action {action['id']}"
        return payload

    skill_name = action.get("skill")
    if not isinstance(skill_name, str) or not skill_name:
        raise ProtocolError(
            f"Invalid action '{action['id']}': skill executor requires a non-empty skill name.",
            code="invalid_action_payload",
        )
    payload["skillName"] = skill_name
    payload["prompt"] = rendered_prompt or f"Invoke skill {skill_name} for action {action['id']}"

    return payload


def ensure_protocol_state(runtime_seed: dict | None, change_dir: str):
    state = read_execution_state(change_dir)
    if state is None:
        if not isinstance(runtime_seed, dict):
            raise ProtocolError(
                "Execution state not found. Initialize the change first.",
                code="missing_file",
            )
        snapshot = initialize_execution_snapshot(change_dir, _runtime_blueprint_from_seed(runtime_seed))
        state = snapshot["runtime"]
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


def next_action(runtime_seed: dict | None, change_dir: str, owner: str = "agent"):
    state = ensure_protocol_state(runtime_seed, change_dir)
    _refresh_ready_actions(state)

    if state["status"] in {"success", "failed"}:
        _persist(change_dir, state)
        return {
            "state": "done",
            "action": None,
        }

    for action_state in state["actions"]:
        if action_state["status"] != "RUNNING":
            continue
        payload = _build_action_payload(action_state)
        _persist(change_dir, state)
        return {
            "state": "ready",
            "action": payload,
        }

    for action_state in state["actions"]:
        if action_state["status"] != "READY":
            continue

        action_state["status"] = "RUNNING"
        action_state["startedAt"] = _now_iso()

        payload = _build_action_payload(action_state)
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
            "action": payload,
        }

    _terminalize_if_done(change_dir, state)
    _persist(change_dir, state)
    if state["status"] in {"success", "failed"}:
        return {
            "state": "done",
            "action": None,
        }

    return {
        "state": "blocked",
        "action": None,
    }


def _validate_report_shape(payload: dict, key: str):
    if not isinstance(payload, dict):
        raise ProtocolError(f"Invalid {key} payload: expected a JSON object.", code="invalid_payload")


def complete_action(runtime_seed: dict | None, change_dir: str, action_id: str, output_payload: dict):
    _validate_report_shape(output_payload, "output")
    state = ensure_protocol_state(runtime_seed, change_dir)

    action_state = next((a for a in state["actions"] if a["id"] == action_id), None)
    if not action_state:
        raise ProtocolError(f"Unknown action: '{action_id}'.", code="unknown_action")
    if action_state["status"] != "RUNNING":
        raise ProtocolError(
            f"Action '{action_id}' cannot be completed from status '{action_state['status']}'.",
            code="invalid_state",
        )

    action_state["status"] = "SUCCESS"
    action_state["output"] = output_payload
    action_state["error"] = None
    action_state["finishedAt"] = _now_iso()

    append_event(change_dir, {"event": "action.completed", "actionId": action_id})
    _refresh_ready_actions(state)
    _terminalize_if_done(change_dir, state)
    _persist(change_dir, state)
    return status_snapshot(runtime_seed, change_dir)


def fail_action(runtime_seed: dict | None, change_dir: str, action_id: str, error_payload: dict):
    _validate_report_shape(error_payload, "error")
    state = ensure_protocol_state(runtime_seed, change_dir)

    action_state = next((a for a in state["actions"] if a["id"] == action_id), None)
    if not action_state:
        raise ProtocolError(f"Unknown action: '{action_id}'.", code="unknown_action")
    if action_state["status"] != "RUNNING":
        raise ProtocolError(
            f"Action '{action_id}' cannot be failed from status '{action_state['status']}'.",
            code="invalid_state",
        )

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
    return status_snapshot(runtime_seed, change_dir)


def _contracts_payload():
    return {
        "next": {
            "states": ["ready", "blocked", "done"],
            "fields": ["state", "action"],
            "errors": ["invalid_action_payload"],
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
            "fields": ["changeName", "status", "progress"],
            "actionStates": ["PENDING", "READY", "RUNNING", "SUCCESS", "FAILED"],
            "debugFields": ["contracts", "lastFailure", "actions", "actionsOmitted", "protocolVersion"],
            "modes": {
                "default": "status --json returns minimal fields only",
                "full": "status --json --full returns full action objects",
                "debug": "status --json --debug returns contracts and compact action summaries",
            },
        },
        "actionPayload": {
            "script": ["actionId", "executor", "script_command", "prompt"],
            "skill": ["actionId", "executor", "skillName", "prompt"],
            "human": ["actionId", "executor", "human", "prompt"],
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
    runtime_seed: dict | None,
    change_dir: str,
    debug: bool = False,
    compact: bool = False,
    action_limit: int = 40,
):
    state = ensure_protocol_state(runtime_seed, change_dir)
    done = len([a for a in state["actions"] if a["status"] == "SUCCESS"])
    failed = len([a for a in state["actions"] if a["status"] == "FAILED"])
    running = len([a for a in state["actions"] if a["status"] == "RUNNING"])

    last_failure = None
    for action in reversed(state["actions"]):
        if action.get("status") == "FAILED" and action.get("error"):
            last_failure = {"actionId": action["id"], "error": action["error"]}
            break

    payload = {
        "changeName": state.get("changeName"),
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
