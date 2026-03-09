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


def _resolve_executor(step):
    executor = step.get("executor")
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
        "steps": runtime_seed.get("steps", []),
    }


def _build_step_payload(step: dict):
    executor = _resolve_executor(step)
    if executor is None:
        raise ProtocolError(
            f"Invalid step '{step['id']}': missing executor.",
            code="invalid_step_payload",
        )
    if executor not in _VALID_EXECUTORS:
        raise ProtocolError(
            f"Invalid step '{step['id']}': unsupported executor '{executor}'.",
            code="invalid_step_payload",
        )

    rendered_prompt = step.get("prompt")
    if rendered_prompt is not None and not isinstance(rendered_prompt, str):
        raise ProtocolError(
            f"Invalid step '{step['id']}': prompt must be a string.",
            code="invalid_step_payload",
        )
    payload = {
        "stepId": step["id"],
        "executor": executor,
    }

    if executor == "script":
        command = step.get("script")
        if not isinstance(command, str) or not command:
            raise ProtocolError(
                f"Invalid step '{step['id']}': script executor requires a non-empty script command.",
                code="invalid_step_payload",
            )
        payload["script_command"] = command
        payload["prompt"] = rendered_prompt or f"Run script command for step {step['id']}"
        return payload

    if executor == "human":
        human = step.get("human")
        if not isinstance(human, dict) or not isinstance(human.get("instruction"), str) or not human.get("instruction"):
            raise ProtocolError(
                f"Invalid step '{step['id']}': human executor requires a non-empty instruction.",
                code="invalid_step_payload",
            )
        payload["human"] = human
        payload["prompt"] = rendered_prompt or human.get("instruction") or f"Wait for human review on step {step['id']}"
        return payload

    skill_name = step.get("skill")
    if not isinstance(skill_name, str) or not skill_name:
        raise ProtocolError(
            f"Invalid step '{step['id']}': skill executor requires a non-empty skill name.",
            code="invalid_step_payload",
        )
    payload["skillName"] = skill_name
    payload["prompt"] = rendered_prompt or f"Invoke skill {skill_name} for step {step['id']}"

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
        step["id"]
        for step in state["steps"]
        if step["status"] == "SUCCESS"
    }


def _dependencies_satisfied(step_state: dict, completed: set[str]):
    for dep in step_state.get("dependsOn", []):
        if dep not in completed:
            return False
    return True


def _refresh_ready_steps(state: dict):
    completed = _completed_ids(state)
    for step_state in state["steps"]:
        if step_state["status"] not in {"PENDING", "READY"}:
            continue

        if _dependencies_satisfied(step_state, completed):
            step_state["status"] = "READY"
        else:
            step_state["status"] = "PENDING"


def _step_state_by_id(state: dict, step_id: str):
    for step in state["steps"]:
        if step["id"] == step_id:
            return step
    return None


def _propagate_dependency_failures(change_dir: str, state: dict):
    # Repeatedly collapse blocked dependents into FAILED for deterministic termination.
    while True:
        transitioned = False
        for step_state in state["steps"]:
            if step_state["status"] not in {"PENDING", "READY"}:
                continue

            failed_dep = None
            for dep in step_state.get("dependsOn", []):
                dep_state = _step_state_by_id(state, dep)
                if dep_state and dep_state["status"] == "FAILED":
                    failed_dep = dep
                    break
            if not failed_dep:
                continue

            step_state["status"] = "FAILED"
            step_state["finishedAt"] = _now_iso()
            append_event(
                change_dir,
                {
                    "event": "step.failed",
                    "stepId": step_state["id"],
                    "reason": "dependency_failed",
                    "dependency": failed_dep,
                },
            )
            transitioned = True

        if not transitioned:
            return


def _fail_remaining_steps(change_dir: str, state: dict, failed_by_step_id: str):
    for step_state in state["steps"]:
        if step_state["status"] not in {"PENDING", "READY", "RUNNING"}:
            continue
        if step_state["id"] == failed_by_step_id:
            continue

        step_state["status"] = "FAILED"
        step_state["finishedAt"] = _now_iso()
        append_event(
            change_dir,
            {
                "event": "step.failed",
                "stepId": step_state["id"],
                "reason": "workflow_failed",
                "failedBy": failed_by_step_id,
            },
        )


def _terminalize_if_done(change_dir: str, state: dict):
    remaining = [s for s in state["steps"] if s["status"] in {"PENDING", "READY", "RUNNING"}]
    if not remaining:
        has_failed = any(s["status"] == "FAILED" for s in state["steps"])
        state["status"] = "failed" if has_failed else "success"
        state["finishedAt"] = _now_iso()
        append_event(change_dir, {"event": "state.terminal", "status": state["status"]})


def next_step(runtime_seed: dict | None, change_dir: str, owner: str = "agent"):
    state = ensure_protocol_state(runtime_seed, change_dir)
    _refresh_ready_steps(state)

    if state["status"] in {"success", "failed"}:
        _persist(change_dir, state)
        return {
            "state": "done",
            "step": None,
        }

    for step_state in state["steps"]:
        if step_state["status"] != "RUNNING":
            continue
        payload = _build_step_payload(step_state)
        _persist(change_dir, state)
        return {
            "state": "ready",
            "step": payload,
        }

    for step_state in state["steps"]:
        if step_state["status"] != "READY":
            continue

        step_state["status"] = "RUNNING"
        step_state["startedAt"] = _now_iso()

        payload = _build_step_payload(step_state)
        append_event(
            change_dir,
            {
                "event": "step.started",
                "stepId": step_state["id"],
                "owner": owner,
            },
        )
        _persist(change_dir, state)
        return {
            "state": "ready",
            "step": payload,
        }

    _terminalize_if_done(change_dir, state)
    _persist(change_dir, state)
    if state["status"] in {"success", "failed"}:
        return {
            "state": "done",
            "step": None,
        }

    return {
        "state": "blocked",
        "step": None,
    }


def complete_step(runtime_seed: dict | None, change_dir: str, step_id: str):
    state = ensure_protocol_state(runtime_seed, change_dir)

    step_state = next((s for s in state["steps"] if s["id"] == step_id), None)
    if not step_state:
        raise ProtocolError(f"Unknown step: '{step_id}'.", code="unknown_step")
    if step_state["status"] != "RUNNING":
        raise ProtocolError(
            f"Step '{step_id}' cannot be completed from status '{step_state['status']}'.",
            code="invalid_state",
        )

    step_state["status"] = "SUCCESS"
    step_state["finishedAt"] = _now_iso()

    append_event(change_dir, {"event": "step.completed", "stepId": step_id})
    _refresh_ready_steps(state)
    _terminalize_if_done(change_dir, state)
    _persist(change_dir, state)
    return status_snapshot(runtime_seed, change_dir)


def fail_step(runtime_seed: dict | None, change_dir: str, step_id: str):
    state = ensure_protocol_state(runtime_seed, change_dir)

    step_state = next((s for s in state["steps"] if s["id"] == step_id), None)
    if not step_state:
        raise ProtocolError(f"Unknown step: '{step_id}'.", code="unknown_step")
    if step_state["status"] != "RUNNING":
        raise ProtocolError(
            f"Step '{step_id}' cannot be failed from status '{step_state['status']}'.",
            code="invalid_state",
        )

    step_state["finishedAt"] = _now_iso()
    step_state["status"] = "FAILED"
    state["status"] = "failed"
    state["finishedAt"] = _now_iso()

    append_event(change_dir, {"event": "step.failed", "stepId": step_id, "reason": "reported_failure"})
    _propagate_dependency_failures(change_dir, state)
    _fail_remaining_steps(change_dir, state, step_id)
    _refresh_ready_steps(state)
    _terminalize_if_done(change_dir, state)
    _persist(change_dir, state)
    return status_snapshot(runtime_seed, change_dir)


def _contracts_payload():
    return {
        "next": {
            "states": ["ready", "blocked", "done"],
            "fields": ["state", "step"],
            "errors": ["invalid_step_payload"],
        },
        "stepComplete": {
            "request": ["change", "step-id"],
            "errors": ["unknown_step", "invalid_state"],
        },
        "stepFail": {
            "request": ["change", "step-id"],
            "errors": ["unknown_step", "invalid_state"],
        },
        "status": {
            "fields": ["changeName", "status", "progress"],
            "stepStates": ["PENDING", "READY", "RUNNING", "SUCCESS", "FAILED"],
            "debugFields": ["contracts", "lastFailure", "steps", "stepsOmitted", "protocolVersion"],
            "modes": {
                "default": "status --json returns minimal fields only",
                "full": "status --json --full returns full step objects",
                "debug": "status --json --debug returns contracts and compact step summaries",
            },
        },
        "stepPayload": {
            "script": ["stepId", "executor", "script_command", "prompt"],
            "skill": ["stepId", "executor", "skillName", "prompt"],
            "human": ["stepId", "executor", "human", "prompt"],
        },
    }


def _compact_step_entry(step: dict):
    return {
        "id": step["id"],
        "status": step["status"],
    }


def status_snapshot(
    runtime_seed: dict | None,
    change_dir: str,
    debug: bool = False,
    compact: bool = False,
    step_limit: int = 40,
):
    state = ensure_protocol_state(runtime_seed, change_dir)
    done = len([s for s in state["steps"] if s["status"] == "SUCCESS"])
    failed = len([s for s in state["steps"] if s["status"] == "FAILED"])
    running = len([s for s in state["steps"] if s["status"] == "RUNNING"])

    last_failure = None
    for step in reversed(state["steps"]):
        if step.get("status") == "FAILED":
            last_failure = {"stepId": step["id"]}
            break

    payload = {
        "changeName": state.get("changeName"),
        "protocolVersion": SUPPORTED_PROTOCOL_VERSION,
        "status": state["status"],
        "progress": {
            "total": len(state["steps"]),
            "done": done,
            "failed": failed,
            "running": running,
            "remaining": len(state["steps"]) - done - failed - running,
        },
        "lastFailure": last_failure,
    }
    if compact:
        limit = max(1, int(step_limit))
        compact_steps = [_compact_step_entry(step) for step in state["steps"][:limit]]
        payload["steps"] = compact_steps
        payload["stepsOmitted"] = max(0, len(state["steps"]) - len(compact_steps))
    else:
        payload["steps"] = state["steps"]
    if debug:
        payload["contracts"] = _contracts_payload()
    return payload
