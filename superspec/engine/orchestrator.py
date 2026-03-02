import os
import time
from datetime import datetime, timezone
from pathlib import Path

from superspec.actions.action_registry import get_action_handler
from superspec.engine.constants import DEFAULTS
from superspec.engine.context import resolve_value, set_path
from superspec.engine.state_store import (
    create_initial_state,
    create_run_layout,
    finalise_state,
    load_latest_run_state,
    patch_state_timestamps,
    write_run_state,
)
from superspec.runners.script_runner import run_script_action
from superspec.runners.skill_runner import run_skill_action


def _now_run_id():
    return datetime.now(timezone.utc).isoformat().replace(":", "-").replace(".", "-")


def _should_run(action, action_state, completed):
    if action.get("enabled") is False:
        return False
    if action_state.get("status") == "SUCCESS":
        return False
    for dep in action.get("dependsOn", []):
        if dep not in completed:
            return False
    return True


def _resolve_executor(action, defaults):
    if action.get("executor"):
        return action["executor"]
    if action.get("script"):
        return "script"
    return defaults.get("executor", DEFAULTS["executor"])


def _execute_action(action, context):
    executor = _resolve_executor(action, context["defaults"])
    if action.get("executor"):
        return run_script_action(action, context) if executor == "script" else run_skill_action(action, context)

    handler = get_action_handler(action["type"])
    if handler:
        return handler(action, context)

    return run_script_action(action, context) if executor == "script" else run_skill_action(action, context)


def _log_action(log_path: Path, line: str):
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a", encoding="utf-8") as f:
        f.write(f"{line}\n")


def _backoff_delay_seconds(retry, attempts):
    backoff = retry.get("backoffSec", 0)
    if backoff <= 0:
        return 0
    if retry.get("strategy") == "exponential":
        return backoff * max(1, 2 ** (attempts - 1))
    return backoff


def run_plan(plan: dict, options=None):
    options = options or {}
    run_id = options.get("runId") or _now_run_id()
    resume = bool(options.get("resume"))
    from_action = options.get("fromAction")

    repo_root = Path(plan["context"].get("repoRoot", ".")).resolve()
    change_dir = (repo_root / plan["context"]["changeDir"]).resolve()

    _, logs_dir = create_run_layout(str(change_dir), run_id)

    latest = load_latest_run_state(str(change_dir)) if resume else None
    state = latest if latest else create_initial_state(plan, run_id)

    defaults = {**DEFAULTS, **plan.get("defaults", {})}
    runtime_context = {
        "repoRoot": str(repo_root),
        "changeName": plan["context"]["changeName"],
        "defaults": defaults,
        "environment": plan["context"].get("environment", {}),
        "context": plan["context"],
        "variables": plan.get("variables", {}),
        "actions": {},
    }

    action_state_by_id = {a["id"]: a for a in state["actions"]}

    if from_action:
        for item in state["actions"]:
            if item["id"] == from_action:
                break
            if item["status"] == "PENDING":
                item["status"] = "SKIPPED"

    completed = {
        a["id"]
        for a in state["actions"]
        if a["status"] in {"SUCCESS", "SKIPPED"}
    }

    for action in plan["actions"]:
        action_state = action_state_by_id[action["id"]]
        if not _should_run(action, action_state, completed):
            continue

        retry = {**defaults.get("retry", {}), **action.get("retry", {})}
        max_attempts = retry.get("maxAttempts", 1)
        log_path = Path(logs_dir) / f"{action['id']}.log"

        action_state["status"] = "RUNNING"
        action_state["startedAt"] = datetime.now(timezone.utc).isoformat()
        patch_state_timestamps(state)
        write_run_state(str(change_dir), run_id, state)

        succeeded = False
        last_error = None

        for attempt in range(1, max_attempts + 1):
            action_state["attempts"] = attempt
            _log_action(log_path, f"[attempt {attempt}] action {action['id']} started")

            try:
                expr_context = {
                    "context": runtime_context["context"],
                    "variables": runtime_context["variables"],
                    "actions": runtime_context["actions"],
                    "env": dict(os.environ),
                }
                resolved_action = resolve_value(action, expr_context)
                output = _execute_action(resolved_action, runtime_context)

                action_state["status"] = "SUCCESS"
                action_state["output"] = output
                action_state["error"] = None
                action_state["finishedAt"] = datetime.now(timezone.utc).isoformat()

                runtime_context["actions"][action["id"]] = {"outputs": output}
                for target, source_path in (resolved_action.get("outputs") or {}).items():
                    if isinstance(source_path, str) and source_path.startswith("$."):
                        value = output.get(source_path[2:])
                        set_path(runtime_context, target, value)

                _log_action(log_path, f"[attempt {attempt}] success")
                completed.add(action["id"])
                succeeded = True
                break
            except Exception as exc:  # noqa: BLE001
                last_error = exc
                _log_action(log_path, f"[attempt {attempt}] failed: {exc}")
                time.sleep(_backoff_delay_seconds(retry, attempt))

        if not succeeded:
            action_state["status"] = "FAILED"
            action_state["error"] = {"message": str(last_error) if last_error else "Unknown error"}
            action_state["finishedAt"] = datetime.now(timezone.utc).isoformat()

            on_fail = action.get("onFail") or defaults.get("onFail", "stop")
            if on_fail == "skip_dependents":
                completed.add(action["id"])
            elif on_fail == "continue":
                pass
            else:
                finalise_state(state, "failed")
                write_run_state(str(change_dir), run_id, state)
                return state

        patch_state_timestamps(state)
        write_run_state(str(change_dir), run_id, state)

    has_failed = any(a["status"] == "FAILED" for a in state["actions"])
    finalise_state(state, "failed" if has_failed else "success")
    write_run_state(str(change_dir), run_id, state)
    return state
