import shutil
from datetime import datetime
from pathlib import Path

from superspec.engine.changes.paths import changes_root, load_execution_snapshot_for_change, resolve_change_dir
from superspec.engine.errors import ProtocolError


COMPLETION_POLICIES = ("archive", "delete", "keep")


def _archive_date(value: str, change_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ProtocolError(
            f"Change '{change_name}' is missing execution start time.",
            code="invalid_finish_source",
            details={"change": change_name, "field": "runtime.startedAt"},
        )
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise ProtocolError(
            f"Change '{change_name}' has invalid execution start time.",
            code="invalid_finish_source",
            details={"change": change_name, "field": "runtime.startedAt", "value": value},
        ) from exc
    return parsed.date().isoformat()


def _load_finish_metadata(repo_root: str | Path, change_name: str) -> dict:
    change_dir = resolve_change_dir(str(repo_root), change_name)
    if not change_dir.exists():
        raise ProtocolError(
            f"Change '{change_name}' not found.",
            code="change_not_found",
            details={"change": change_name, "path": str(change_dir)},
        )

    try:
        snapshot, _ = load_execution_snapshot_for_change(str(repo_root), change_name)
    except FileNotFoundError as exc:
        raise ProtocolError(
            f"Change '{change_name}' is missing execution state.",
            code="invalid_finish_source",
            details={"change": change_name},
        ) from exc

    meta = snapshot.get("meta")
    runtime = snapshot.get("runtime")
    workflow_id = meta.get("workflowId") if isinstance(meta, dict) else None
    runtime_status = runtime.get("status") if isinstance(runtime, dict) else None
    started_at = runtime.get("startedAt") if isinstance(runtime, dict) else None
    finish_policy = meta.get("finishPolicy") if isinstance(meta, dict) else None

    if not isinstance(workflow_id, str) or not workflow_id:
        raise ProtocolError(
            f"Change '{change_name}' is missing workflow binding metadata.",
            code="invalid_finish_source",
            details={"change": change_name, "field": "meta.workflowId"},
        )
    if not isinstance(runtime_status, str) or not runtime_status:
        raise ProtocolError(
            f"Change '{change_name}' is missing runtime status.",
            code="invalid_finish_source",
            details={"change": change_name, "field": "runtime.status"},
        )
    if finish_policy not in COMPLETION_POLICIES:
        raise ProtocolError(
            f"Change '{change_name}' is missing a valid workflow finish policy.",
            code="invalid_finish_source",
            details={"change": change_name, "field": "meta.finishPolicy"},
        )

    return {
        "change_dir": change_dir,
        "workflow_id": workflow_id,
        "runtime_status": runtime_status,
        "started_date": _archive_date(started_at, change_name),
        "finish_policy": finish_policy,
    }


def _unique_archive_path(repo_root: str | Path, started_date: str, change_name: str, workflow_id: str) -> Path:
    archive_root = changes_root(repo_root) / "archive"
    archive_root.mkdir(parents=True, exist_ok=True)
    base_name = f"{started_date}-{change_name}-{workflow_id}"
    candidate = archive_root / base_name
    suffix = 2
    while candidate.exists():
        candidate = archive_root / f"{base_name}-{suffix}"
        suffix += 1
    return candidate


def finish_change(repo_root: str | Path, change_name: str, *, mode: str | None = None, force: bool = False) -> dict:
    metadata = _load_finish_metadata(repo_root, change_name)
    selected_mode = mode or metadata["finish_policy"]
    if selected_mode not in COMPLETION_POLICIES:
        raise ProtocolError(
            f"Unsupported finish mode '{selected_mode}'.",
            code="invalid_arguments",
            details={"mode": selected_mode},
        )

    runtime_status = metadata["runtime_status"]
    if selected_mode in {"archive", "delete"} and runtime_status == "running" and not force:
        raise ProtocolError(
            f"Change '{change_name}' is still running. Re-run with --force to finish it anyway.",
            code="invalid_state",
            details={"change": change_name, "status": runtime_status, "mode": selected_mode},
        )

    change_dir = metadata["change_dir"]
    payload = {
        "change": change_name,
        "workflowId": metadata["workflow_id"],
        "startedDate": metadata["started_date"],
        "defaultMode": metadata["finish_policy"],
        "selectedMode": selected_mode,
        "forced": bool(force),
    }

    if selected_mode == "keep":
        payload["keptAt"] = str(change_dir)
        return payload

    if selected_mode == "delete":
        shutil.rmtree(change_dir)
        payload["deletedFrom"] = str(change_dir)
        return payload

    execution_dir = change_dir / "execution"
    if execution_dir.exists():
        shutil.rmtree(execution_dir)

    destination = _unique_archive_path(
        repo_root,
        metadata["started_date"],
        change_name,
        metadata["workflow_id"],
    )
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(change_dir), str(destination))
    payload["archivedTo"] = str(destination)
    return payload
