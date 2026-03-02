import hashlib
import json
import os
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

from superspec.engine.constants import DEFAULTS, DEFAULT_LEASE_TTL_SEC, SUPPORTED_PROTOCOL_VERSION
from superspec.engine.context import resolve_value
from superspec.engine.errors import ProtocolError
from superspec.engine.state_store import (
    append_event,
    read_execution_leases,
    read_execution_state,
    write_execution_leases,
    write_execution_state,
)


def _now():
    return datetime.now(timezone.utc)


def _now_iso():
    return _now().isoformat()


def _parse_iso(ts: str):
    return datetime.fromisoformat(ts)


def _lease_id(change_name: str, action_id: str):
    raw = f"{change_name}:{action_id}:{time.time_ns()}:{os.getpid()}"
    digest = hashlib.sha1(raw.encode("utf-8")).hexdigest()[:12]
    return f"lease_{action_id}_{digest}"


def _context_files(change_dir: Path):
    return {
        "proposal": str(change_dir / "proposal.md"),
        "design": str(change_dir / "design.md"),
        "tasks": str(change_dir / "tasks.md"),
        "specs": str(change_dir / "specs" / "**" / "*.md"),
    }


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
    return resolve_value(action, expr_context)


def _build_action_payload(action: dict, resolved_action: dict, change_dir: Path, debug: bool):
    executor = _resolve_executor(resolved_action, {**DEFAULTS, **action.get("defaults", {})})
    payload = {
        "actionId": action["id"],
        "type": action["type"],
        "executor": executor,
        "contextFiles": _context_files(change_dir),
    }

    if executor == "script":
        command = resolved_action.get("script")
        if not command:
            raise ProtocolError(
                f"Action {action['id']} script executor requires script field",
                code="invalid_action_payload",
            )
        payload["script"] = {
            "command": command,
            "timeoutSec": resolved_action.get("timeoutSec", DEFAULTS["timeoutSec"]),
        }
        payload["instruction"] = f"Run script command for action {action['id']}"
        return payload

    skill_name = resolved_action.get("skill") or action.get("skill") or action.get("type")
    skill_payload = {
        "name": skill_name,
        "version": str((resolved_action.get("skillVersion") or "1.0")),
        "input": resolved_action.get("inputs", {}),
        "contextFiles": _context_files(change_dir),
    }
    payload["skill"] = skill_payload
    payload["instruction"] = f"Invoke skill {skill_name} for action {action['id']}"

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
                "leaseId": None,
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
        write_execution_leases(change_dir, {"leases": {}})
        append_event(change_dir, {"event": "state.initialized", "planId": plan["planId"]})
    return state


def _persist(change_dir: str, state: dict, leases: dict):
    state["updatedAt"] = _now_iso()
    write_execution_state(change_dir, state)
    write_execution_leases(change_dir, leases)


def _expire_stale_leases(change_dir: str, state: dict, leases: dict):
    now = _now()
    by_id = {a["id"]: a for a in state["actions"]}
    expired_ids = []
    for action_id, lease in list(leases["leases"].items()):
        expires_at = _parse_iso(lease["expiresAt"])
        if now >= expires_at:
            expired_ids.append(action_id)
            action = by_id.get(action_id)
            if action and action["status"] == "LEASED":
                action["status"] = "PENDING"
                action["leaseId"] = None
    for action_id in expired_ids:
        del leases["leases"][action_id]
        append_event(change_dir, {"event": "lease.expired", "actionId": action_id})


def _completed_ids(state: dict):
    return {
        a["id"]
        for a in state["actions"]
        if a["status"] in {"SUCCESS", "SKIPPED"}
    }


def _is_ready(action_state: dict, completed: set[str]):
    if action_state["status"] != "PENDING":
        return False
    if action_state.get("nextEligibleAt"):
        if _now() < _parse_iso(action_state["nextEligibleAt"]):
            return False
    for dep in action_state.get("dependsOn", []):
        if dep not in completed:
            return False
    return True


def _action_by_id(plan: dict, action_id: str):
    for action in plan["actions"]:
        if action["id"] == action_id:
            return action
    return None


def _terminalize_if_done(change_dir: str, state: dict):
    remaining = [a for a in state["actions"] if a["status"] in {"PENDING", "LEASED", "RUNNING"}]
    if not remaining:
        has_failed = any(a["status"] == "FAILED" for a in state["actions"])
        state["status"] = "failed" if has_failed else "success"
        state["finishedAt"] = _now_iso()
        append_event(change_dir, {"event": "state.terminal", "status": state["status"]})


def next_action(plan: dict, change_dir: str, owner: str = "agent", lease_ttl_sec: int | None = None, debug: bool = False):
    state = ensure_protocol_state(plan, change_dir)
    leases = read_execution_leases(change_dir)
    _expire_stale_leases(change_dir, state, leases)

    if state["status"] in {"success", "failed"}:
        _persist(change_dir, state, leases)
        return {
            "state": "done",
            "changeName": plan["context"]["changeName"],
            "status": state["status"],
            "action": None,
            "instruction": "Plan has reached terminal state.",
        }

    completed = _completed_ids(state)
    for action_state in state["actions"]:
        if not _is_ready(action_state, completed):
            continue
        action = _action_by_id(plan, action_state["id"])
        if not action:
            continue

        resolved_action = _resolve_action_for_payload(action, state, plan)
        lease_id = _lease_id(plan["context"]["changeName"], action_state["id"])
        ttl = lease_ttl_sec or int((plan.get("defaults") or {}).get("leaseTtlSec", DEFAULT_LEASE_TTL_SEC))
        issued_at = _now()
        expires_at = issued_at + timedelta(seconds=ttl)

        action_state["status"] = "LEASED"
        action_state["leaseId"] = lease_id
        action_state["startedAt"] = issued_at.isoformat()

        leases["leases"][action_state["id"]] = {
            "leaseId": lease_id,
            "owner": owner,
            "issuedAt": issued_at.isoformat(),
            "expiresAt": expires_at.isoformat(),
            "ttlSec": ttl,
        }

        payload = _build_action_payload(action, resolved_action, Path(change_dir), debug)
        append_event(
            change_dir,
            {
                "event": "action.leased",
                "actionId": action_state["id"],
                "leaseId": lease_id,
                "owner": owner,
            },
        )
        _persist(change_dir, state, leases)
        return {
            "state": "ready",
            "changeName": plan["context"]["changeName"],
            "leaseId": lease_id,
            "action": payload,
            "instruction": payload["instruction"],
        }

    _terminalize_if_done(change_dir, state)
    _persist(change_dir, state, leases)
    if state["status"] in {"success", "failed"}:
        return {
            "state": "done",
            "changeName": plan["context"]["changeName"],
            "status": state["status"],
            "action": None,
            "instruction": "Plan has reached terminal state.",
        }

    return {
        "state": "blocked",
        "changeName": plan["context"]["changeName"],
        "action": None,
        "instruction": "No runnable actions at this time (waiting for dependencies or retry backoff).",
    }


def _validate_report_shape(payload: dict, key: str):
    if not isinstance(payload, dict):
        raise ProtocolError(f"{key} payload must be a JSON object", code="invalid_payload")


def complete_action(plan: dict, change_dir: str, action_id: str, lease_id: str, result_payload: dict):
    _validate_report_shape(result_payload, "result")
    state = ensure_protocol_state(plan, change_dir)
    leases = read_execution_leases(change_dir)
    lease = leases["leases"].get(action_id)
    if not lease or lease.get("leaseId") != lease_id:
        raise ProtocolError("Invalid or stale lease for completion report", code="invalid_lease")

    action_state = next((a for a in state["actions"] if a["id"] == action_id), None)
    if not action_state:
        raise ProtocolError(f"Unknown action id: {action_id}", code="unknown_action")
    if action_state["status"] not in {"LEASED", "RUNNING", "PENDING"}:
        raise ProtocolError(f"Action {action_id} not completable from status {action_state['status']}", code="invalid_state")

    action_state["status"] = "SUCCESS"
    action_state["output"] = result_payload
    action_state["error"] = None
    action_state["finishedAt"] = _now_iso()
    action_state["leaseId"] = None
    leases["leases"].pop(action_id, None)

    append_event(change_dir, {"event": "action.completed", "actionId": action_id})
    _terminalize_if_done(change_dir, state)
    _persist(change_dir, state, leases)
    return status_snapshot(plan, change_dir)


def fail_action(plan: dict, change_dir: str, action_id: str, lease_id: str, error_payload: dict):
    _validate_report_shape(error_payload, "error")
    state = ensure_protocol_state(plan, change_dir)
    leases = read_execution_leases(change_dir)
    lease = leases["leases"].get(action_id)
    if not lease or lease.get("leaseId") != lease_id:
        raise ProtocolError("Invalid or stale lease for failure report", code="invalid_lease")

    action_state = next((a for a in state["actions"] if a["id"] == action_id), None)
    action_def = _action_by_id(plan, action_id)
    if not action_state or not action_def:
        raise ProtocolError(f"Unknown action id: {action_id}", code="unknown_action")

    defaults = {**DEFAULTS, **plan.get("defaults", {})}
    retry_defaults = defaults.get("retry", {})
    retry = {**retry_defaults, **(action_def.get("retry") or {})}
    max_attempts = int(retry.get("maxAttempts", 1))
    action_state["attempts"] = int(action_state.get("attempts", 0)) + 1
    action_state["error"] = error_payload
    action_state["leaseId"] = None
    action_state["finishedAt"] = _now_iso()
    leases["leases"].pop(action_id, None)

    if action_state["attempts"] < max_attempts:
        backoff = int(retry.get("backoffSec", 0))
        strategy = retry.get("strategy", "fixed")
        if strategy == "exponential":
            backoff *= max(1, 2 ** (action_state["attempts"] - 1))
        action_state["status"] = "PENDING"
        action_state["nextEligibleAt"] = (_now() + timedelta(seconds=backoff)).isoformat() if backoff > 0 else None
        append_event(change_dir, {"event": "action.retry_scheduled", "actionId": action_id, "attempt": action_state["attempts"]})
        _persist(change_dir, state, leases)
        return status_snapshot(plan, change_dir)

    on_fail = action_def.get("onFail") or defaults.get("onFail", "stop")
    if on_fail == "continue":
        action_state["status"] = "FAILED"
    elif on_fail == "skip_dependents":
        action_state["status"] = "SKIPPED"
    else:
        action_state["status"] = "FAILED"
        state["status"] = "failed"
        state["finishedAt"] = _now_iso()

    append_event(change_dir, {"event": "action.failed", "actionId": action_id, "onFail": on_fail})
    _terminalize_if_done(change_dir, state)
    _persist(change_dir, state, leases)
    return status_snapshot(plan, change_dir)


def status_snapshot(plan: dict, change_dir: str):
    state = ensure_protocol_state(plan, change_dir)
    leases = read_execution_leases(change_dir)
    done = len([a for a in state["actions"] if a["status"] in {"SUCCESS", "SKIPPED"}])
    failed = len([a for a in state["actions"] if a["status"] == "FAILED"])
    running = len([a for a in state["actions"] if a["status"] in {"LEASED", "RUNNING"}])

    last_failure = None
    for action in reversed(state["actions"]):
        if action.get("status") == "FAILED" and action.get("error"):
            last_failure = {"actionId": action["id"], "error": action["error"]}
            break

    return {
        "changeName": plan["context"]["changeName"],
        "schemaVersion": plan["schemaVersion"],
        "protocolVersion": SUPPORTED_PROTOCOL_VERSION,
        "status": state["status"],
        "progress": {
            "total": len(state["actions"]),
            "done": done,
            "failed": failed,
            "running": running,
            "remaining": len(state["actions"]) - done - failed,
        },
        "leases": leases.get("leases", {}),
        "lastFailure": last_failure,
        "actions": state["actions"],
        "contracts": {
            "next": {
                "states": ["ready", "blocked", "done"],
                "fields": ["state", "changeName", "action", "leaseId", "instruction"],
            },
            "complete": {
                "request": ["change", "action-id", "lease", "result-json"],
                "errors": ["invalid_payload", "invalid_lease", "unknown_action", "invalid_state"],
            },
            "fail": {
                "request": ["change", "action-id", "lease", "error-json"],
                "errors": ["invalid_payload", "invalid_lease", "unknown_action", "invalid_state"],
            },
            "status": {
                "fields": ["status", "progress", "leases", "lastFailure", "actions"],
            },
            "actionPayload": {
                "script": ["actionId", "type", "executor", "script.command", "contextFiles"],
                "skill": ["actionId", "type", "executor", "skill.name", "skill.version", "skill.input", "contextFiles"],
                "debug": "renderedPrompt returned only when debug=true",
            },
            "leaseLifecycle": {
                "states": ["issued", "validated", "expired", "reclaimed"],
                "fields": ["leaseId", "owner", "issuedAt", "expiresAt", "ttlSec"],
            },
        },
    }


def render_protocol_docs():
    contracts = {
        "next": {
            "states": ["ready", "blocked", "done"],
            "fields": ["state", "changeName", "action", "leaseId", "instruction"],
        },
        "complete": {
            "request": ["change", "action-id", "lease", "result-json"],
            "errors": ["invalid_payload", "invalid_lease", "unknown_action", "invalid_state"],
        },
        "fail": {
            "request": ["change", "action-id", "lease", "error-json"],
            "errors": ["invalid_payload", "invalid_lease", "unknown_action", "invalid_state"],
        },
        "status": {
            "fields": ["status", "progress", "leases", "lastFailure", "actions"],
        },
        "actionPayload": {
            "script": ["actionId", "type", "executor", "script.command", "contextFiles"],
            "skill": ["actionId", "type", "executor", "skill.name", "skill.version", "skill.input", "contextFiles"],
            "debug": "renderedPrompt returned only when debug=true",
        },
        "leaseLifecycle": {
            "states": ["issued", "validated", "expired", "reclaimed"],
            "fields": ["leaseId", "owner", "issuedAt", "expiresAt", "ttlSec"],
        },
    }
    return json.dumps(contracts, indent=2)
