import json
import re
from pathlib import Path

from superspec.engine.errors import ProtocolError


WORKFLOW_NAME_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")


def package_root():
    return Path(__file__).resolve().parents[2]


def load_json(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ProtocolError(f"Workflow file not found: {path}.", code="missing_file", details={"path": str(path)}) from exc
    except json.JSONDecodeError as exc:
        raise ProtocolError(f"Invalid JSON in workflow file: {path}.", code="invalid_json", details={"path": str(path)}) from exc


def resolve_workflow_name(workflow: str | None):
    return workflow or "spec-dev"


def validate_workflow_name(workflow_name: str, *, field: str = "workflow"):
    if not isinstance(workflow_name, str) or not WORKFLOW_NAME_PATTERN.fullmatch(workflow_name):
        raise ProtocolError(
            "Invalid workflow name. Use letters, numbers, dot, underscore, hyphen; first character must be alphanumeric.",
            code="invalid_workflow_name",
            details={field: workflow_name},
        )
    if workflow_name in {".", ".."}:
        raise ProtocolError(
            "Invalid workflow name.",
            code="invalid_workflow_name",
            details={field: workflow_name},
        )


def load_workflow_schema():
    return load_json(package_root() / "schemas" / "workflow.schema.json")


def workflow_schema_version():
    schema = load_workflow_schema()
    schema_id = schema.get("$id") if isinstance(schema, dict) else None
    if isinstance(schema_id, str) and schema_id:
        return schema_id
    return "workflow.schema/unknown"


def load_workflow(repo_root: Path, workflow_name: str):
    validate_workflow_name(workflow_name)
    local_path = repo_root / "superspec" / "schemas" / "workflows" / f"{workflow_name}.workflow.json"
    package_path = package_root() / "schemas" / "workflows" / f"{workflow_name}.workflow.json"

    if local_path.exists():
        return load_json(local_path), local_path
    if package_path.exists():
        return load_json(package_path), package_path

    raise ProtocolError(
        f"Unknown workflow schema '{workflow_name}'.",
        code="invalid_plan_schema",
        details={"schema": workflow_name, "localPath": str(local_path), "defaultPath": str(package_path)},
    )


def load_workflow_from_file(repo_root: Path, workflow_file: str):
    workflow_path = Path(workflow_file)
    if not workflow_path.is_absolute():
        workflow_path = (repo_root / workflow_path).resolve()
    return load_json(workflow_path), workflow_path


def fork_packaged_workflow(repo_root: Path, source_name: str, target_name: str):
    validate_workflow_name(source_name, field="source")
    validate_workflow_name(target_name, field="target")

    source_path = package_root() / "schemas" / "workflows" / f"{source_name}.workflow.json"
    if not source_path.exists():
        raise ProtocolError(
            f"Unknown built-in workflow '{source_name}'.",
            code="invalid_plan_schema",
            details={"schema": source_name, "defaultPath": str(source_path)},
        )

    target_dir = repo_root / "superspec" / "schemas" / "workflows"
    target_dir.mkdir(parents=True, exist_ok=True)
    target_path = target_dir / f"{target_name}.workflow.json"
    if target_path.exists():
        raise ProtocolError(
            f"Target workflow already exists: {target_path}.",
            code="workflow_exists",
            details={"source": source_name, "target": target_name, "path": str(target_path)},
        )

    target_path.write_text(source_path.read_text(encoding="utf-8"), encoding="utf-8")
    return target_path
