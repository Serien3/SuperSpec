import json
from pathlib import Path

from jsonschema import Draft202012Validator

from superspec.engine.errors import ProtocolError, ValidationError
from superspec.engine.validator import validate_plan

WORKFLOW_ALLOWED_TOP_LEVEL_FIELDS = (
    "workflowId",
    "version",
    "description",
    "planId",
    "title",
    "goal",
    "variables",
    "actions",
    "metadata",
)

WORKFLOW_PLAN_CUSTOMIZATION_FIELDS = (
    "planId",
    "title",
    "goal",
    "variables",
    "actions",
    "metadata",
)


def _package_root():
    return Path(__file__).resolve().parents[1]


def _load_json(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ProtocolError(f"File not found: {path}", code="missing_file", details={"path": str(path)}) from exc
    except json.JSONDecodeError as exc:
        raise ProtocolError(f"Invalid JSON in {path}", code="invalid_json", details={"path": str(path)}) from exc


def _deep_merge(base, overlay):
    if not isinstance(base, dict) or not isinstance(overlay, dict):
        return overlay

    merged = dict(base)
    for key, value in overlay.items():
        if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
            merged[key] = _deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def _resolve_workflow_name(workflow: str | None):
    return workflow or "SDD"


def _load_workflow_schema(repo_root: Path):
    return _load_json(_package_root() / "schemas" / "workflow.schema.json")


def _load_base_template(repo_root: Path):
    return _load_json(_package_root() / "schemas" / "templates" / "plan.base.json")


def _load_workflow(repo_root: Path, workflow_name: str):
    local_path = repo_root / "superspec" / "schemas" / "workflows" / f"{workflow_name}.workflow.json"
    package_path = _package_root() / "schemas" / "workflows" / f"{workflow_name}.workflow.json"

    if local_path.exists():
        return _load_json(local_path), local_path
    if package_path.exists():
        return _load_json(package_path), package_path

    raise ProtocolError(
        f"Unknown plan schema '{workflow_name}'. Expected workflow at {local_path} or {package_path}",
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
                f"Use top-level customization fields: {', '.join(WORKFLOW_PLAN_CUSTOMIZATION_FIELDS)}",
            )
        return _error(
            "unsupported_field",
            field,
            f"Unsupported field '{field}' in workflow '{workflow_name}'",
            f"Supported top-level fields: {', '.join(WORKFLOW_ALLOWED_TOP_LEVEL_FIELDS)}",
        )
    return None


def _schema_errors(repo_root: Path, workflow: dict):
    schema = _load_workflow_schema(repo_root)
    validator = Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(workflow), key=lambda e: list(e.path))
    mapped = []
    for err in errors:
        mapped.append(
            _error(
                "invalid_schema",
                _dot_path(list(err.path)),
                err.message,
            )
        )
    return mapped


def _semantic_errors(workflow: dict):
    errors = []
    actions = workflow.get("actions")
    if not isinstance(actions, list):
        return errors

    by_id = {}
    for idx, action in enumerate(actions):
        if not isinstance(action, dict):
            continue

        action_id = action.get("id")
        if isinstance(action_id, str):
            if action_id in by_id:
                errors.append(
                    _error(
                        "duplicate_action_id",
                        f"actions.{idx}.id",
                        f"Duplicate action id '{action_id}'",
                    )
                )
            else:
                by_id[action_id] = idx

        executor = action.get("executor")
        if executor == "skill" and not action.get("skill"):
            errors.append(
                _error(
                    "invalid_executor_payload",
                    f"actions.{idx}.skill",
                    "Action with executor 'skill' must define a non-empty 'skill' field",
                )
            )
        if executor == "script" and not action.get("script"):
            errors.append(
                _error(
                    "invalid_executor_payload",
                    f"actions.{idx}.script",
                    "Action with executor 'script' must define a non-empty 'script' field",
                )
            )
        if executor == "human":
            human = action.get("human")
            if not isinstance(human, dict):
                errors.append(
                    _error(
                        "invalid_executor_payload",
                        f"actions.{idx}.human",
                        "Action with executor 'human' must define a 'human' object",
                    )
                )
            elif not isinstance(human.get("instruction"), str) or not human.get("instruction"):
                errors.append(
                    _error(
                        "invalid_executor_payload",
                        f"actions.{idx}.human.instruction",
                        "Action with executor 'human' must define non-empty 'human.instruction'",
                    )
                )

    # Validate dependency references and detect cycles.
    for idx, action in enumerate(actions):
        if not isinstance(action, dict):
            continue
        deps = action.get("dependsOn")
        if not isinstance(deps, list):
            continue
        for dep_idx, dep in enumerate(deps):
            if dep not in by_id:
                errors.append(
                    _error(
                        "unknown_dependency",
                        f"actions.{idx}.dependsOn.{dep_idx}",
                        f"Unknown dependency action id '{dep}'",
                    )
                )

    visited = {}

    def dfs(action_id: str):
        visited[action_id] = "visiting"
        action = actions[by_id[action_id]]
        for dep in action.get("dependsOn", []):
            if dep not in by_id:
                continue
            dep_state = visited.get(dep)
            if dep_state == "visiting":
                return [action_id, dep]
            if dep_state is None:
                cycle = dfs(dep)
                if cycle:
                    return [action_id] + cycle
        visited[action_id] = "done"
        return None

    for action_id in by_id:
        if visited.get(action_id) is None:
            cycle = dfs(action_id)
            if cycle:
                pretty_cycle = " -> ".join(cycle)
                errors.append(
                    _error(
                        "dependency_cycle",
                        "actions",
                        f"Action dependency cycle detected: {pretty_cycle}",
                    )
                )
                break
    return errors


def _generation_readiness_errors(repo_root: Path, workflow: dict):
    base = _load_base_template(repo_root)
    generated = _deep_merge(base, _workflow_payload(workflow))
    generated.setdefault("context", {})
    generated["context"]["changeName"] = "validate-only"
    generated["context"]["changeDir"] = "openspec/changes/validate-only"
    generated["context"].setdefault("repoRoot", ".")
    generated["context"].setdefault("specRoot", "openspec")

    try:
        validate_plan(generated)
    except ValidationError as exc:
        return [_error("not_generation_ready", "$", str(exc))]
    return []


def _validate_workflow_diagnostics(repo_root: Path, workflow: dict, workflow_name: str):
    unknown = _unknown_top_level_field_error(workflow, workflow_name)
    if unknown:
        return [unknown]

    schema_errors = _schema_errors(repo_root, workflow)
    if schema_errors:
        return schema_errors

    semantic_errors = _semantic_errors(workflow)
    if semantic_errors:
        return semantic_errors

    return _generation_readiness_errors(repo_root, workflow)


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
        f"Invalid plan schema '{workflow_name}': {first['message']}",
        code="invalid_plan_schema",
        details={"schema": workflow_name, "location": first["path"]},
    )


def _workflow_payload(workflow: dict):
    payload = {}
    for key in WORKFLOW_PLAN_CUSTOMIZATION_FIELDS:
        if key in workflow:
            payload[key] = workflow[key]

    # Keep workflow identity in generated metadata for traceability.
    payload.setdefault("metadata", {})
    payload["metadata"] = _deep_merge(
        payload.get("metadata", {}),
        {
            "schema": {
                "id": workflow["workflowId"],
                "version": workflow["version"],
            }
        },
    )
    return payload


def build_plan_from_workflow(repo_root: Path, change_name: str, schema: str | None = None, overrides=None):
    selected_workflow = _resolve_workflow_name(schema)
    base = _load_base_template(repo_root)
    workflow_doc, workflow_path = _load_workflow(repo_root, selected_workflow)
    _validate_workflow(repo_root, workflow_doc, selected_workflow)

    generated = _deep_merge(base, _workflow_payload(workflow_doc))
    generated = _deep_merge(generated, overrides or {})

    generated.setdefault("context", {})
    generated["context"]["changeName"] = change_name
    generated["context"]["changeDir"] = f"openspec/changes/{change_name}"
    generated["context"].setdefault("repoRoot", ".")
    generated["context"].setdefault("specRoot", "openspec")

    return generated, selected_workflow, str(workflow_path)
