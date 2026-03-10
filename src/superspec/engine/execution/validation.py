from superspec.engine.errors import ValidationError
from superspec.engine.execution.helpers import VALID_EXECUTORS


def assert_valid(condition, message, details=None):
    if not condition:
        raise ValidationError(message, details)


def detect_cycle(steps):
    by_id = {step["id"]: step for step in steps}
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
        step_id = step["id"]
        if state.get(step_id) is None:
            cycle = dfs(step_id, [])
            if cycle:
                return cycle
    return None


def validate_runtime_seed(seed):
    assert_valid(isinstance(seed, dict), "Runtime seed must be an object")
    context = seed.get("context")
    assert_valid(isinstance(context, dict), "Missing runtime seed context")
    assert_valid(
        isinstance(context.get("changeName"), str) and context["changeName"],
        "Missing change name in runtime seed context",
    )

    steps = seed.get("steps")
    assert_valid(isinstance(steps, list) and len(steps) > 0, "steps must be a non-empty array")

    ids = set()
    by_id = {}
    for step in steps:
        step_id = step.get("id")
        assert_valid(isinstance(step_id, str) and step_id, "step.id is required", step)
        assert_valid(step_id not in ids, f"Duplicate step id: {step_id}")
        ids.add(step_id)
        by_id[step_id] = step

        description = step.get("description")
        assert_valid(isinstance(description, str) and description, f"Step {step_id} description is required")

        executor = step.get("executor")
        assert_valid(isinstance(executor, str) and executor, f"Step {step_id} executor is required")
        assert_valid(executor in VALID_EXECUTORS, f"Step {step_id} has invalid executor: {executor}")

        has_skill = "skill" in step
        has_script = "script" in step
        has_option = "option" in step

        if executor == "skill":
            assert_valid(isinstance(step.get("skill"), str) and step["skill"], f"Step {step_id} must set skill for skill executor")
            assert_valid(not has_script and not has_option, f"Step {step_id} skill executor cannot define script/option payload")
        if executor == "script":
            assert_valid(isinstance(step.get("script"), str) and step["script"], f"Step {step_id} must set script for script executor")
            assert_valid(not has_skill and not has_option, f"Step {step_id} script executor cannot define skill/option payload")
        if executor == "human":
            option = step.get("option")
            assert_valid(option is None or isinstance(option, dict), f"Step {step_id} option payload must be an object when provided")
            if isinstance(option, dict):
                assert_valid(isinstance(option.get("approveLabel"), str) and option["approveLabel"], f"Step {step_id} option payload requires option.approveLabel")
                assert_valid(isinstance(option.get("rejectLabel"), str) and option["rejectLabel"], f"Step {step_id} option payload requires option.rejectLabel")
            assert_valid(not has_skill and not has_script, f"Step {step_id} human executor cannot define skill/script payload")

    for step in steps:
        for dep in step.get("dependsOn", []):
            assert_valid(dep in by_id, f"Step {step['id']} depends on unknown step: {dep}")

    cycle = detect_cycle(steps)
    if cycle is not None:
        raise ValidationError(f"Step dependency cycle detected: {' -> '.join(cycle)}")
    return True
