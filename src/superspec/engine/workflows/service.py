from pathlib import Path

from superspec.engine.errors import ProtocolError
from superspec.engine.workflows.definitions import error_payload
from superspec.engine.workflows.runtime_blueprint import workflow_runtime_blueprint_payload
from superspec.engine.workflows.sources import (
    load_workflow,
    load_workflow_from_file,
    resolve_workflow_name,
)
from superspec.engine.workflows.validation import validate_workflow, validate_workflow_diagnostics


def validate_workflow_source(repo_root: Path, schema: str | None = None, workflow_file: str | None = None):
    if bool(schema) == bool(workflow_file):
        return {
            "ok": False,
            "target": None,
            "errors": [
                error_payload(
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
            selected = resolve_workflow_name(schema)
            workflow, workflow_path = load_workflow(repo_root, selected)
            workflow_name = selected
        else:
            workflow, workflow_path = load_workflow_from_file(repo_root, str(workflow_file))
            workflow_name = workflow.get("workflowId") if isinstance(workflow, dict) else workflow_path.stem
    except ProtocolError as exc:
        details = exc.details if isinstance(exc.details, dict) else {}
        return {
            "ok": False,
            "target": str(details.get("path") or details.get("localPath") or details.get("defaultPath") or ""),
            "errors": [
                error_payload(
                    exc.code,
                    "$",
                    str(exc),
                )
            ],
            "warnings": [],
        }

    errors = validate_workflow_diagnostics(repo_root, workflow, str(workflow_name))
    return {
        "ok": len(errors) == 0,
        "target": str(workflow_path),
        "schema": workflow_name,
        "errors": errors,
        "warnings": [],
    }


def build_runtime_blueprint_from_workflow(repo_root: Path, change_name: str, schema: str | None = None):
    selected_workflow = resolve_workflow_name(schema)
    workflow_doc, workflow_path = load_workflow(repo_root, selected_workflow)
    validate_workflow(repo_root, workflow_doc, selected_workflow)

    generated = workflow_runtime_blueprint_payload(workflow_doc, change_name)
    return generated, selected_workflow, str(workflow_path)
