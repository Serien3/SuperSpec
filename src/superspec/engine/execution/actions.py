from superspec.engine.errors import ProtocolError
from superspec.engine.execution.helpers import now_iso
from superspec.engine.execution.payloads import build_step_payload
from superspec.engine.execution.status import status_snapshot
from superspec.engine.execution.store import ensure_protocol_state, persist_runtime_state
from superspec.engine.execution.transitions import (
    fail_remaining_steps,
    propagate_dependency_failures,
    refresh_ready_steps,
    terminalize_if_done,
)
from superspec.engine.storage.events import append_event


def next_step(runtime_seed: dict | None, change_dir: str, owner: str = "agent"):
    state = ensure_protocol_state(runtime_seed, change_dir)
    refresh_ready_steps(state)
    change_name = state.get("changeName")

    if state["status"] in {"success", "failed"}:
        persist_runtime_state(change_dir, state)
        return {
            "change": change_name,
            "state": "done",
            "step": None,
        }

    for step_state in state["steps"]:
        if step_state["status"] != "RUNNING":
            continue
        payload = build_step_payload(step_state)
        persist_runtime_state(change_dir, state)
        return {
            "change": change_name,
            "state": "ready",
            "step": payload,
        }

    for step_state in state["steps"]:
        if step_state["status"] != "READY":
            continue

        step_state["status"] = "RUNNING"
        step_state["startedAt"] = now_iso()

        payload = build_step_payload(step_state)
        append_event(
            change_dir,
            {
                "event": "step.started",
                "stepId": step_state["id"],
                "owner": owner,
            },
        )
        persist_runtime_state(change_dir, state)
        return {
            "change": change_name,
            "state": "ready",
            "step": payload,
        }

    terminalize_if_done(change_dir, state)
    persist_runtime_state(change_dir, state)
    if state["status"] in {"success", "failed"}:
        return {
            "change": change_name,
            "state": "done",
            "step": None,
        }

    return {
        "change": change_name,
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
    step_state["finishedAt"] = now_iso()

    append_event(change_dir, {"event": "step.completed", "stepId": step_id})
    refresh_ready_steps(state)
    terminalize_if_done(change_dir, state)
    persist_runtime_state(change_dir, state)
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

    step_state["finishedAt"] = now_iso()
    step_state["status"] = "FAILED"
    state["status"] = "failed"
    state["finishedAt"] = now_iso()

    append_event(change_dir, {"event": "step.failed", "stepId": step_id, "reason": "reported_failure"})
    propagate_dependency_failures(change_dir, state)
    fail_remaining_steps(change_dir, state, step_id)
    refresh_ready_steps(state)
    terminalize_if_done(change_dir, state)
    persist_runtime_state(change_dir, state)
    return status_snapshot(runtime_seed, change_dir)
