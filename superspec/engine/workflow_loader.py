import json
from pathlib import Path

from jsonschema import Draft202012Validator

from superspec.engine.errors import ProtocolError


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
    return workflow or "sdd"


def _load_workflow_schema(repo_root: Path):
    return _load_json(_package_root() / "schemas" / "workflow.schema.json")


def _load_base_template(repo_root: Path):
    return _load_json(_package_root() / "templates" / "plan.base.json")


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


def _validate_workflow(repo_root: Path, workflow: dict, workflow_name: str):
    schema = _load_workflow_schema(repo_root)
    validator = Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(workflow), key=lambda e: list(e.path))
    if errors:
        first = errors[0]
        loc = ".".join(str(p) for p in first.path) or "$"
        raise ProtocolError(
            f"Invalid plan schema '{workflow_name}': {first.message}",
            code="invalid_plan_schema",
            details={"schema": workflow_name, "location": loc},
        )


def _workflow_payload(workflow: dict):
    payload = {}
    for key in ("planId", "title", "goal", "variables", "defaults", "actions", "metadata"):
        if key in workflow:
            payload[key] = workflow[key]

    plan_overlay = workflow.get("plan", {})
    if isinstance(plan_overlay, dict):
        payload = _deep_merge(payload, plan_overlay)

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
