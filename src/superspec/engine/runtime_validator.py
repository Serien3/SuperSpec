from .errors import ValidationError

_VALID_EXECUTORS = {"skill", "script", "human"}


def _assert(cond, message, details=None):
    if not cond:
        raise ValidationError(message, details)


def _detect_cycle(steps):
    by_id = {a["id"]: a for a in steps}
    state = {}

    def dfs(node_id, stack):
        state[node_id] = "visiting"
        step = by_id[node_id]
        for dep in step.get("dependsOn", []):
            dep_state = state.get(dep)
            if dep_state == "visiting":
                return stack + [node_id, dep]
            if dep_state is None:
                cycle = dfs(dep, stack + [node_id])
                if cycle:
                    return cycle
        state[node_id] = "visited"
        return None

    for step in steps:
        aid = step["id"]
        if state.get(aid) is None:
            cycle = dfs(aid, [])
            if cycle:
                return cycle
    return None


def validate_runtime_seed(seed):
    _assert(isinstance(seed, dict), "Runtime seed must be an object")
    context = seed.get("context")
    _assert(isinstance(context, dict), "Missing runtime seed context")
    _assert(
        isinstance(context.get("changeName"), str) and context["changeName"],
        "Missing change name in runtime seed context",
    )

    steps = seed.get("steps")
    _assert(isinstance(steps, list) and len(steps) > 0, "steps must be a non-empty array")

    ids = set()
    by_id = {}
    for step in steps:
        aid = step.get("id")
        _assert(isinstance(aid, str) and aid, "step.id is required", step)
        _assert(aid not in ids, f"Duplicate step id: {aid}")
        ids.add(aid)
        by_id[aid] = step

        description = step.get("description")
        _assert(isinstance(description, str) and description, f"Step {aid} description is required")

        executor = step.get("executor")
        _assert(isinstance(executor, str) and executor, f"Step {aid} executor is required")
        _assert(executor in _VALID_EXECUTORS, f"Step {aid} has invalid executor: {executor}")

        has_skill = "skill" in step
        has_script = "script" in step
        has_human = "human" in step

        if executor == "skill":
            _assert(isinstance(step.get("skill"), str) and step["skill"], f"Step {aid} must set skill for skill executor")
            _assert(not has_script and not has_human, f"Step {aid} skill executor cannot define script/human payload")
        if executor == "script":
            _assert(isinstance(step.get("script"), str) and step["script"], f"Step {aid} must set script for script executor")
            _assert(not has_skill and not has_human, f"Step {aid} script executor cannot define skill/human payload")
        if executor == "human":
            human = step.get("human")
            _assert(isinstance(human, dict), f"Step {aid} must set human object for human executor")
            _assert(isinstance(human.get("instruction"), str) and human["instruction"], f"Step {aid} human executor requires human.instruction")
            _assert(not has_skill and not has_script, f"Step {aid} human executor cannot define skill/script payload")

    for step in steps:
        for dep in step.get("dependsOn", []):
            _assert(dep in by_id, f"Step {step['id']} depends on unknown step: {dep}")

    cycle = _detect_cycle(steps)
    if cycle is not None:
        raise ValidationError(f"Step dependency cycle detected: {' -> '.join(cycle)}")
    return True
