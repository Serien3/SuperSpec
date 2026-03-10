from superspec.engine.errors import ProtocolError
from superspec.engine.execution.helpers import VALID_EXECUTORS


def resolve_executor(step):
    executor = step.get("executor")
    if isinstance(executor, str) and executor:
        return executor
    return None


def runtime_blueprint_from_seed(runtime_seed: dict):
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


def build_step_payload(step: dict):
    executor = resolve_executor(step)
    if executor is None:
        raise ProtocolError(
            f"Invalid step '{step['id']}': missing executor.",
            code="invalid_step_payload",
        )
    if executor not in VALID_EXECUTORS:
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
        option = step.get("option")
        if option is not None and (
            not isinstance(option, dict)
            or not isinstance(option.get("approveLabel"), str)
            or not option.get("approveLabel")
            or not isinstance(option.get("rejectLabel"), str)
            or not option.get("rejectLabel")
        ):
            raise ProtocolError(
                f"Invalid step '{step['id']}': option payload requires non-empty approve/reject labels when provided.",
                code="invalid_step_payload",
            )
        if isinstance(option, dict):
            payload["option"] = option
        payload["prompt"] = rendered_prompt or f"Wait for human review on step {step['id']}"
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
