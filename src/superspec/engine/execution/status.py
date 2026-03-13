from superspec.engine.constants import SUPPORTED_PROTOCOL_VERSION
from superspec.engine.execution.store import ensure_protocol_state


def contracts_payload():
    return {
        "next": {
            "states": ["ready", "blocked", "done"],
            "fields": ["change", "goal", "state", "step"],
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
            "script": ["stepId", "script_command", "prompt"],
            "skill": ["stepId", "skillName", "prompt"],
            "human": ["stepId", "prompt", "option(optional)"],
        },
    }


def compact_step_entry(step: dict):
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
        compact_steps = [compact_step_entry(step) for step in state["steps"][:limit]]
        payload["steps"] = compact_steps
        payload["stepsOmitted"] = max(0, len(state["steps"]) - len(compact_steps))
    else:
        payload["steps"] = state["steps"]
    if debug:
        payload["contracts"] = contracts_payload()
    return payload
