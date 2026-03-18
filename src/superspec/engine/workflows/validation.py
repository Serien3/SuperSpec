from jsonschema import Draft202012Validator

from superspec.engine.errors import ProtocolError
from superspec.engine.workflows.definitions import (
    WORKFLOW_ALLOWED_TOP_LEVEL_FIELDS,
    WORKFLOW_EXECUTORS,
    WORKFLOW_OPTIONAL_TOP_LEVEL_FIELDS,
    dot_path,
    error_payload,
)
from superspec.engine.workflows.runtime_blueprint import workflow_runtime_blueprint_payload
from superspec.engine.workflows.sources import load_workflow_schema

COMPLETION_POLICIES = {"archive", "delete", "keep"}


def unknown_top_level_field_error(workflow: dict, workflow_name: str):
    unknown = [key for key in workflow.keys() if key not in WORKFLOW_ALLOWED_TOP_LEVEL_FIELDS]
    if unknown:
        field = unknown[0]
        if field == "plan":
            return error_payload(
                "unsupported_field",
                field,
                f"Unsupported field '{field}' in workflow '{workflow_name}'",
                f"Use optional top-level fields: {', '.join(WORKFLOW_OPTIONAL_TOP_LEVEL_FIELDS)}",
            )
        return error_payload(
            "unsupported_field",
            field,
            f"Unsupported field '{field}' in workflow '{workflow_name}'",
            f"Supported top-level fields: {', '.join(WORKFLOW_ALLOWED_TOP_LEVEL_FIELDS)}",
        )
    return None


def schema_errors(workflow: dict):
    schema = load_workflow_schema()
    validator = Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(workflow), key=lambda e: list(e.path))
    mapped = []
    for err in errors:
        path = dot_path(list(err.path))
        code = "invalid_schema"
        message = err.message
        hint = None

        if err.validator == "required" and isinstance(err.instance, dict):
            missing = [key for key in err.validator_value if key not in err.instance]
            if missing:
                missing_field = str(missing[0])
                if path.startswith("steps.") and missing_field == "executor":
                    code = "missing_required_field"
                    path = f"{path}.executor"
                    message = "Step must define explicit 'executor'"
                    hint = f"Set executor to one of: {', '.join(WORKFLOW_EXECUTORS)}"
                elif path.startswith("steps.") and missing_field in WORKFLOW_EXECUTORS:
                    code = "invalid_executor_payload"
                    path = f"{path}.{missing_field}"
                    message = f"Step executor requires matching '{missing_field}' payload"
                    hint = "Ensure exactly one matching executor payload is present"
                elif path.startswith("steps.") and missing_field in {"approveLabel", "rejectLabel"}:
                    code = "invalid_executor_payload"
                    path = f"{path}.{missing_field}"
                    message = f"Step option payload must define non-empty 'option.{missing_field}'"
                    hint = "When steps[].option is present, set both option.approveLabel and option.rejectLabel"
        elif err.validator == "not" and path.startswith("steps."):
            code = "invalid_executor_payload"
            message = "Step defines mixed executor payload fields"
            hint = "Keep only the payload field that matches steps[].executor"

        mapped.append(error_payload(code, path, message, hint))
    return mapped


def semantic_errors(workflow: dict):
    errors = []
    finish_policy = workflow.get("finishPolicy")
    if finish_policy is not None and finish_policy not in COMPLETION_POLICIES:
        errors.append(
            error_payload(
                "invalid_finish_policy",
                "finishPolicy",
                "Workflow finishPolicy must be one of: archive, delete, keep",
            )
        )

    steps = workflow.get("steps")
    if not isinstance(steps, list):
        return errors

    by_id = {}
    for idx, step in enumerate(steps):
        if not isinstance(step, dict):
            continue

        step_id = step.get("id")
        if isinstance(step_id, str):
            if step_id in by_id:
                errors.append(
                    error_payload(
                        "duplicate_step_id",
                        f"steps.{idx}.id",
                        f"Duplicate step id '{step_id}'",
                    )
                )
            else:
                by_id[step_id] = idx

        executor = step.get("executor")
        if not isinstance(executor, str) or not executor:
            errors.append(
                error_payload(
                    "missing_required_field",
                    f"steps.{idx}.executor",
                    "Step must define explicit 'executor'",
                    f"Set executor to one of: {', '.join(WORKFLOW_EXECUTORS)}",
                )
            )
            continue
        if executor not in WORKFLOW_EXECUTORS:
            errors.append(
                error_payload(
                    "invalid_executor_payload",
                    f"steps.{idx}.executor",
                    f"Unsupported executor '{executor}'",
                    f"Supported executors: {', '.join(WORKFLOW_EXECUTORS)}",
                )
            )
            continue

        has_skill = "skill" in step
        has_script = "script" in step
        has_option = "option" in step

        if executor == "skill" and not step.get("skill"):
            errors.append(
                error_payload(
                    "invalid_executor_payload",
                    f"steps.{idx}.skill",
                    "Step with executor 'skill' must define a non-empty 'skill' field",
                    "Set steps[].skill and remove script/option fields",
                )
            )
        if executor == "script" and not step.get("script"):
            errors.append(
                error_payload(
                    "invalid_executor_payload",
                    f"steps.{idx}.script",
                    "Step with executor 'script' must define a non-empty 'script' field",
                    "Set steps[].script and remove skill/option fields",
                )
            )
        if executor == "human":
            option = step.get("option")
            if option is not None and not isinstance(option, dict):
                errors.append(
                    error_payload(
                        "invalid_executor_payload",
                        f"steps.{idx}.option",
                        "Step option payload must be an object when provided",
                        "Set steps[].option as an object with non-empty approveLabel/rejectLabel, or omit it",
                    )
                )
            elif isinstance(option, dict) and (not isinstance(option.get("approveLabel"), str) or not option.get("approveLabel")):
                errors.append(
                    error_payload(
                        "invalid_executor_payload",
                        f"steps.{idx}.option.approveLabel",
                        "Step option payload must define non-empty 'option.approveLabel'",
                        "Set steps[].option.approveLabel to a non-empty string",
                    )
                )
            elif isinstance(option, dict) and (not isinstance(option.get("rejectLabel"), str) or not option.get("rejectLabel")):
                errors.append(
                    error_payload(
                        "invalid_executor_payload",
                        f"steps.{idx}.option.rejectLabel",
                        "Step option payload must define non-empty 'option.rejectLabel'",
                        "Set steps[].option.rejectLabel to a non-empty string",
                    )
                )

        if executor == "skill" and (has_script or has_option):
            errors.append(
                error_payload(
                    "invalid_executor_payload",
                    f"steps.{idx}",
                    "Step with executor 'skill' cannot define script/option payload fields",
                    "Keep only steps[].skill for skill executor",
                )
            )
        if executor == "script" and (has_skill or has_option):
            errors.append(
                error_payload(
                    "invalid_executor_payload",
                    f"steps.{idx}",
                    "Step with executor 'script' cannot define skill/option payload fields",
                    "Keep only steps[].script for script executor",
                )
            )
        if executor == "human" and (has_skill or has_script):
            errors.append(
                error_payload(
                    "invalid_executor_payload",
                    f"steps.{idx}",
                    "Step with executor 'human' cannot define skill/script payload fields",
                    "Keep only steps[].option for human executor",
                )
            )

    for idx, step in enumerate(steps):
        if not isinstance(step, dict):
            continue
        deps = step.get("dependsOn")
        if not isinstance(deps, list):
            continue
        for dep_idx, dep in enumerate(deps):
            if dep not in by_id:
                errors.append(
                    error_payload(
                        "unknown_dependency",
                        f"steps.{idx}.dependsOn.{dep_idx}",
                        f"Unknown dependency step id '{dep}'",
                    )
                )

    visited = {}

    def dfs(step_id: str):
        visited[step_id] = "visiting"
        step = steps[by_id[step_id]]
        for dep in step.get("dependsOn", []):
            if dep not in by_id:
                continue
            dep_state = visited.get(dep)
            if dep_state == "visiting":
                return [step_id, dep]
            if dep_state is None:
                cycle = dfs(dep)
                if cycle:
                    return [step_id] + cycle
        visited[step_id] = "done"
        return None

    for step_id in by_id:
        if visited.get(step_id) is None:
            cycle = dfs(step_id)
            if cycle:
                pretty_cycle = " -> ".join(cycle)
                errors.append(
                    error_payload(
                        "dependency_cycle",
                        "steps",
                        f"Step dependency cycle detected: {pretty_cycle}",
                    )
                )
                break
    return errors


def generation_readiness_errors(workflow: dict):
    generated = workflow_runtime_blueprint_payload(workflow, "validate-only")
    steps = generated.get("steps")
    if not isinstance(steps, list) or not steps:
        return [error_payload("not_generation_ready", "$.steps", "Generated runtime steps must be a non-empty array")]
    for idx, step in enumerate(steps):
        if not isinstance(step, dict):
            return [error_payload("not_generation_ready", f"$.steps.{idx}", "Generated runtime step must be an object")]
        if not isinstance(step.get("description"), str) or not step["description"]:
            return [error_payload("not_generation_ready", f"$.steps.{idx}.description", "Generated runtime step description is required")]
    return []


def validate_workflow_diagnostics(repo_root, workflow: dict, workflow_name: str):
    unknown = unknown_top_level_field_error(workflow, workflow_name)
    if unknown:
        return [unknown]

    shape_errors = schema_errors(workflow)
    if shape_errors:
        return shape_errors

    logical_errors = semantic_errors(workflow)
    if logical_errors:
        return logical_errors

    return generation_readiness_errors(workflow)


def validate_workflow(repo_root, workflow: dict, workflow_name: str):
    errors = validate_workflow_diagnostics(repo_root, workflow, workflow_name)
    if not errors:
        return

    first = errors[0]
    raise ProtocolError(
        f"Invalid workflow schema '{workflow_name}': {first['message']}.",
        code="invalid_plan_schema",
        details={"schema": workflow_name, "location": first["path"]},
    )
