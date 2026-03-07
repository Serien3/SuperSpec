from .constants import SUPPORTED_SCHEMA_VERSION
from .errors import ValidationError

_VALID_EXECUTORS = {"skill", "script", "human"}


def _assert(cond, message, details=None):
    if not cond:
        raise ValidationError(message, details)


def _detect_cycle(actions):
    by_id = {a["id"]: a for a in actions}
    state = {}

    def dfs(node_id, stack):
        state[node_id] = "visiting"
        action = by_id[node_id]
        for dep in action.get("dependsOn", []):
            dep_state = state.get(dep)
            if dep_state == "visiting":
                return stack + [node_id, dep]
            if dep_state is None:
                cycle = dfs(dep, stack + [node_id])
                if cycle:
                    return cycle
        state[node_id] = "visited"
        return None

    for action in actions:
        aid = action["id"]
        if state.get(aid) is None:
            cycle = dfs(aid, [])
            if cycle:
                return cycle
    return None


def validate_plan(plan):
    _assert(isinstance(plan, dict), "Plan must be an object")
    _assert(plan.get("schemaVersion") == SUPPORTED_SCHEMA_VERSION, f"Unsupported schemaVersion: {plan.get('schemaVersion')}")
    _assert(isinstance(plan.get("planId"), str) and plan["planId"], "planId is required")
    _assert(isinstance(plan.get("title"), str) and plan["title"], "title is required")
    _assert(isinstance(plan.get("goal"), str) and plan["goal"], "goal is required")
    context = plan.get("context")
    _assert(isinstance(context, dict), "context is required")
    _assert(isinstance(context.get("changeName"), str) and context["changeName"], "context.changeName is required")

    actions = plan.get("actions")
    _assert(isinstance(actions, list) and len(actions) > 0, "actions must be a non-empty array")

    ids = set()
    by_id = {}
    for action in actions:
        aid = action.get("id")
        _assert(isinstance(aid, str) and aid, "action.id is required", action)
        _assert(aid not in ids, f"Duplicate action id: {aid}")
        ids.add(aid)
        by_id[aid] = action

        atype = action.get("type")
        _assert(isinstance(atype, str) and atype, f"Action {aid} type is required")

        executor = action.get("executor")
        _assert(isinstance(executor, str) and executor, f"Action {aid} executor is required")
        _assert(executor in _VALID_EXECUTORS, f"Action {aid} has invalid executor: {executor}")

        has_skill = "skill" in action
        has_script = "script" in action
        has_human = "human" in action

        if executor == "skill":
            _assert(isinstance(action.get("skill"), str) and action["skill"], f"Action {aid} must set skill for skill executor")
            _assert(not has_script and not has_human, f"Action {aid} skill executor cannot define script/human payload")
        if executor == "script":
            _assert(isinstance(action.get("script"), str) and action["script"], f"Action {aid} must set script for script executor")
            _assert(not has_skill and not has_human, f"Action {aid} script executor cannot define skill/human payload")
        if executor == "human":
            human = action.get("human")
            _assert(isinstance(human, dict), f"Action {aid} must set human object for human executor")
            _assert(isinstance(human.get("instruction"), str) and human["instruction"], f"Action {aid} human executor requires human.instruction")
            _assert(not has_skill and not has_script, f"Action {aid} human executor cannot define skill/script payload")

    for action in actions:
        for dep in action.get("dependsOn", []):
            _assert(dep in by_id, f"Action {action['id']} depends on unknown action: {dep}")

    cycle = _detect_cycle(actions)
    if cycle is not None:
        raise ValidationError(f"Action dependency cycle detected: {' -> '.join(cycle)}")
    return True
