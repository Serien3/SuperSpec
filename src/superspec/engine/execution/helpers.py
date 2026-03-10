from datetime import datetime, timezone


VALID_EXECUTORS = {"skill", "script", "human"}


def now():
    return datetime.now(timezone.utc)


def now_iso():
    return now().isoformat()


def completed_ids(state: dict):
    return {
        step["id"]
        for step in state["steps"]
        if step["status"] == "SUCCESS"
    }


def dependencies_satisfied(step_state: dict, completed: set[str]):
    for dep in step_state.get("dependsOn", []):
        if dep not in completed:
            return False
    return True


def step_state_by_id(state: dict, step_id: str):
    for step in state["steps"]:
        if step["id"] == step_id:
            return step
    return None
