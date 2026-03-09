import json
from pathlib import Path

from jsonschema import Draft202012Validator

from superspec.engine.errors import ProtocolError

WORKFLOW_ALLOWED_TOP_LEVEL_FIELDS = (
    "workflowId",
    "version",
    "description",
    "steps",
    "metadata",
)

WORKFLOW_RUNTIME_CUSTOMIZATION_FIELDS = (
    "steps",
)
WORKFLOW_OPTIONAL_TOP_LEVEL_FIELDS = (
    "description",
    "metadata",
)

WORKFLOW_EXECUTORS = ("skill", "script", "human")


def _package_root():
    return Path(__file__).resolve().parents[1]


def _load_json(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ProtocolError(f"Workflow file not found: {path}.", code="missing_file", details={"path": str(path)}) from exc
    except json.JSONDecodeError as exc:
        raise ProtocolError(f"Invalid JSON in workflow file: {path}.", code="invalid_json", details={"path": str(path)}) from exc


def _resolve_workflow_name(workflow: str | None):
    return workflow or "SDD"


def _load_workflow_schema():
    return _load_json(_package_root() / "schemas" / "workflow.schema.json")


def workflow_schema_version():
    schema = _load_workflow_schema()
    schema_id = schema.get("$id") if isinstance(schema, dict) else None
    if isinstance(schema_id, str) and schema_id:
        return schema_id
    return "workflow.schema/unknown"


def _load_workflow(repo_root: Path, workflow_name: str):
    local_path = repo_root / "superspec" / "schemas" / "workflows" / f"{workflow_name}.workflow.json"
    package_path = _package_root() / "schemas" / "workflows" / f"{workflow_name}.workflow.json"

    if local_path.exists():
        return _load_json(local_path), local_path
    if package_path.exists():
        return _load_json(package_path), package_path

    raise ProtocolError(
        f"Unknown workflow schema '{workflow_name}'.",
        code="invalid_plan_schema",
        details={"schema": workflow_name, "localPath": str(local_path), "defaultPath": str(package_path)},
    )


def _load_workflow_from_file(repo_root: Path, workflow_file: str):
    workflow_path = Path(workflow_file)
    if not workflow_path.is_absolute():
        workflow_path = (repo_root / workflow_path).resolve()
    return _load_json(workflow_path), workflow_path


def _dot_path(path_parts):
    if not path_parts:
        return "$"
    return ".".join(str(part) for part in path_parts)


def _error(code: str, path: str, message: str, hint: str | None = None):
    payload = {
        "code": code,
        "path": path,
        "message": message,
    }
    if hint:
        payload["hint"] = hint
    return payload


def _unknown_top_level_field_error(workflow: dict, workflow_name: str):
    unknown = [key for key in workflow.keys() if key not in WORKFLOW_ALLOWED_TOP_LEVEL_FIELDS]
    if unknown:
        field = unknown[0]
        if field == "plan":
            return _error(
                "unsupported_field",
                field,
                f"Unsupported field '{field}' in workflow '{workflow_name}'",
                f"Use optional top-level fields: {', '.join(WORKFLOW_OPTIONAL_TOP_LEVEL_FIELDS)}",
            )
        return _error(
            "unsupported_field",
            field,
            f"Unsupported field '{field}' in workflow '{workflow_name}'",
            f"Supported top-level fields: {', '.join(WORKFLOW_ALLOWED_TOP_LEVEL_FIELDS)}",
        )
    return None


def _schema_errors(workflow: dict):
    schema = _load_workflow_schema()
    validator = Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(workflow), key=lambda e: list(e.path))
    mapped = []
    for err in errors:
        path = _dot_path(list(err.path))
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
                elif path.startswith("steps.") and missing_field == "instruction":
                    code = "invalid_executor_payload"
                    path = f"{path}.instruction"
                    message = "Step with executor 'human' must define non-empty 'human.instruction'"
                    hint = "Set human.instruction to a non-empty string"
        elif err.validator == "not" and path.startswith("steps."):
            code = "invalid_executor_payload"
            message = "Step defines mixed executor payload fields"
            hint = "Keep only the payload field that matches steps[].executor"

        mapped.append(_error(code, path, message, hint))
    return mapped


def _semantic_errors(workflow: dict):
    errors = []
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
                    _error(
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
                _error(
                    "missing_required_field",
                    f"steps.{idx}.executor",
                    "Step must define explicit 'executor'",
                    f"Set executor to one of: {', '.join(WORKFLOW_EXECUTORS)}",
                )
            )
            continue
        if executor not in WORKFLOW_EXECUTORS:
            errors.append(
                _error(
                    "invalid_executor_payload",
                    f"steps.{idx}.executor",
                    f"Unsupported executor '{executor}'",
                    f"Supported executors: {', '.join(WORKFLOW_EXECUTORS)}",
                )
            )
            continue

        has_skill = "skill" in step
        has_script = "script" in step
        has_human = "human" in step

        if executor == "skill" and not step.get("skill"):
            errors.append(
                _error(
                    "invalid_executor_payload",
                    f"steps.{idx}.skill",
                    "Step with executor 'skill' must define a non-empty 'skill' field",
                    "Set steps[].skill and remove script/human fields",
                )
            )
        if executor == "script" and not step.get("script"):
            errors.append(
                _error(
                    "invalid_executor_payload",
                    f"steps.{idx}.script",
                    "Step with executor 'script' must define a non-empty 'script' field",
                    "Set steps[].script and remove skill/human fields",
                )
            )
        if executor == "human":
            human = step.get("human")
            if not isinstance(human, dict):
                errors.append(
                    _error(
                        "invalid_executor_payload",
                        f"steps.{idx}.human",
                        "Step with executor 'human' must define a 'human' object",
                        "Set steps[].human as an object with non-empty instruction",
                    )
                )
            elif not isinstance(human.get("instruction"), str) or not human.get("instruction"):
                errors.append(
                    _error(
                        "invalid_executor_payload",
                        f"steps.{idx}.human.instruction",
                        "Step with executor 'human' must define non-empty 'human.instruction'",
                        "Set steps[].human.instruction to a non-empty string",
                    )
                )

        if executor == "skill" and (has_script or has_human):
            errors.append(
                _error(
                    "invalid_executor_payload",
                    f"steps.{idx}",
                    "Step with executor 'skill' cannot define script/human payload fields",
                    "Keep only steps[].skill for skill executor",
                )
            )
        if executor == "script" and (has_skill or has_human):
            errors.append(
                _error(
                    "invalid_executor_payload",
                    f"steps.{idx}",
                    "Step with executor 'script' cannot define skill/human payload fields",
                    "Keep only steps[].script for script executor",
                )
            )
        if executor == "human" and (has_skill or has_script):
            errors.append(
                _error(
                    "invalid_executor_payload",
                    f"steps.{idx}",
                    "Step with executor 'human' cannot define skill/script payload fields",
                    "Keep only steps[].human for human executor",
                )
            )

    # Validate dependency references and detect cycles.
    for idx, step in enumerate(steps):
        if not isinstance(step, dict):
            continue
        deps = step.get("dependsOn")
        if not isinstance(deps, list):
            continue
        for dep_idx, dep in enumerate(deps):
            if dep not in by_id:
                errors.append(
                    _error(
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
                    _error(
                        "dependency_cycle",
                        "steps",
                        f"Step dependency cycle detected: {pretty_cycle}",
                    )
                )
                break
    return errors


def _generation_readiness_errors(workflow: dict):
    generated = _workflow_runtime_blueprint_payload(workflow, "validate-only")
    steps = generated.get("steps")
    if not isinstance(steps, list) or not steps:
        return [_error("not_generation_ready", "$.steps", "Generated runtime steps must be a non-empty array")]
    for idx, step in enumerate(steps):
        if not isinstance(step, dict):
            return [_error("not_generation_ready", f"$.steps.{idx}", "Generated runtime step must be an object")]
        if not isinstance(step.get("description"), str) or not step["description"]:
            return [_error("not_generation_ready", f"$.steps.{idx}.description", "Generated runtime step description is required")]
    return []


def _validate_workflow_diagnostics(repo_root: Path, workflow: dict, workflow_name: str):
    unknown = _unknown_top_level_field_error(workflow, workflow_name)
    if unknown:
        return [unknown]

    schema_errors = _schema_errors(workflow)
    if schema_errors:
        return schema_errors

    semantic_errors = _semantic_errors(workflow)
    if semantic_errors:
        return semantic_errors

    return _generation_readiness_errors(workflow)


def validate_workflow_source(repo_root: Path, schema: str | None = None, workflow_file: str | None = None):
    if bool(schema) == bool(workflow_file):
        return {
            "ok": False,
            "target": None,
            "errors": [
                _error(
                    "invalid_arguments",
                    "$",
                    "Provide exactly one workflow source",
                    "Use either --schema <name> or --file <path>",
                )
            ],
            "warnings": [],
        }

    try:
        if schema:
            selected = _resolve_workflow_name(schema)
            workflow, workflow_path = _load_workflow(repo_root, selected)
            workflow_name = selected
        else:
            workflow, workflow_path = _load_workflow_from_file(repo_root, str(workflow_file))
            workflow_name = workflow.get("workflowId") if isinstance(workflow, dict) else workflow_path.stem
    except ProtocolError as exc:
        details = exc.details if isinstance(exc.details, dict) else {}
        return {
            "ok": False,
            "target": str(details.get("path") or details.get("localPath") or details.get("defaultPath") or ""),
            "errors": [
                _error(
                    exc.code,
                    "$",
                    str(exc),
                )
            ],
            "warnings": [],
        }

    errors = _validate_workflow_diagnostics(repo_root, workflow, str(workflow_name))
    return {
        "ok": len(errors) == 0,
        "target": str(workflow_path),
        "schema": workflow_name,
        "errors": errors,
        "warnings": [],
    }


def _validate_workflow(repo_root: Path, workflow: dict, workflow_name: str):
    errors = _validate_workflow_diagnostics(repo_root, workflow, workflow_name)
    if not errors:
        return

    first = errors[0]
    raise ProtocolError(
        f"Invalid workflow schema '{workflow_name}': {first['message']}.",
        code="invalid_plan_schema",
        details={"schema": workflow_name, "location": first["path"]},
    )


def _workflow_runtime_blueprint_payload(workflow: dict, change_name: str):
    payload = {
        "changeName": change_name,
    }
    for key in WORKFLOW_RUNTIME_CUSTOMIZATION_FIELDS:
        if key in workflow:
            payload[key] = workflow[key]

    # Workflow steps already use "description"; runtime snapshot keeps the same field name.
    normalized_actions = []
    for step in payload.get("steps", []):
        if isinstance(step, dict):
            normalized_actions.append(dict(step))
        else:
            normalized_actions.append(step)
    if normalized_actions:
        payload["steps"] = normalized_actions

    payload["workflow"] = {key: value for key, value in workflow.items() if key != "steps"}
    return payload


def build_plan_from_workflow(repo_root: Path, change_name: str, schema: str | None = None):
    selected_workflow = _resolve_workflow_name(schema)
    workflow_doc, workflow_path = _load_workflow(repo_root, selected_workflow)
    _validate_workflow(repo_root, workflow_doc, selected_workflow)

    generated = _workflow_runtime_blueprint_payload(workflow_doc, change_name)

    return generated, selected_workflow, str(workflow_path)
