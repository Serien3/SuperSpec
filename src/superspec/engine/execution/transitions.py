from superspec.engine.execution.helpers import completed_ids, dependencies_satisfied, now_iso, step_state_by_id
from superspec.engine.storage.events import append_event


def refresh_ready_steps(state: dict):
    completed = completed_ids(state)
    for step_state in state["steps"]:
        if step_state["status"] not in {"PENDING", "READY"}:
            continue

        if dependencies_satisfied(step_state, completed):
            step_state["status"] = "READY"
        else:
            step_state["status"] = "PENDING"


def propagate_dependency_failures(change_dir: str, state: dict):
    while True:
        transitioned = False
        for step_state in state["steps"]:
            if step_state["status"] not in {"PENDING", "READY"}:
                continue

            failed_dep = None
            for dep in step_state.get("dependsOn", []):
                dep_state = step_state_by_id(state, dep)
                if dep_state and dep_state["status"] == "FAILED":
                    failed_dep = dep
                    break
            if not failed_dep:
                continue

            step_state["status"] = "FAILED"
            step_state["finishedAt"] = now_iso()
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


def fail_remaining_steps(change_dir: str, state: dict, failed_by_step_id: str):
    for step_state in state["steps"]:
        if step_state["status"] not in {"PENDING", "READY", "RUNNING"}:
            continue
        if step_state["id"] == failed_by_step_id:
            continue

        step_state["status"] = "FAILED"
        step_state["finishedAt"] = now_iso()
        append_event(
            change_dir,
            {
                "event": "step.failed",
                "stepId": step_state["id"],
                "reason": "workflow_failed",
                "failedBy": failed_by_step_id,
            },
        )


def terminalize_if_done(change_dir: str, state: dict):
    remaining = [s for s in state["steps"] if s["status"] in {"PENDING", "READY", "RUNNING"}]
    if not remaining:
        has_failed = any(s["status"] == "FAILED" for s in state["steps"])
        state["status"] = "failed" if has_failed else "success"
        state["finishedAt"] = now_iso()
        append_event(change_dir, {"event": "state.terminal", "status": state["status"]})
