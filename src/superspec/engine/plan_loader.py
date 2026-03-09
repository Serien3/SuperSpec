import json
import re
from pathlib import Path

from .errors import ProtocolError


_CHANGE_NAME_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")


def _ensure_path_under_root(path: Path, root: Path, *, field: str):
    resolved_path = path.resolve()
    resolved_root = root.resolve()
    if not resolved_path.is_relative_to(resolved_root):
        raise ProtocolError(
            "Invalid path: value is outside the allowed change directory.",
            code="invalid_path",
            details={"path": str(resolved_path), "root": str(resolved_root), "field": field},
        )
    return resolved_path


def validate_change_name(change_name: str):
    if not isinstance(change_name, str) or not _CHANGE_NAME_PATTERN.fullmatch(change_name):
        raise ProtocolError(
            "Invalid change name. Use letters, numbers, dot, underscore, hyphen; first character must be alphanumeric.",
            code="invalid_change_name",
            details={"change": change_name},
        )
    if change_name in {".", ".."}:
        raise ProtocolError(
            "Invalid change name.",
            code="invalid_change_name",
            details={"change": change_name},
        )


def changes_root(repo_root: str | Path) -> Path:
    return (Path(repo_root).resolve() / "superspec" / "changes").resolve()


def resolve_change_dir(repo_root: str, change_name: str) -> Path:
    validate_change_name(change_name)
    root = changes_root(repo_root)
    return _ensure_path_under_root(root / change_name, root, field="change")


def state_path_for_change(repo_root: str, change_name: str) -> Path:
    return resolve_change_dir(repo_root, change_name) / "execution" / "state.json"


def resolve_change_dir_from_definition_context(repo_root: str | Path, change_dir: str) -> Path:
    if not isinstance(change_dir, str) or not change_dir.strip():
        raise ProtocolError("Invalid change directory: expected a non-empty string.", code="invalid_path")
    repo = Path(repo_root).resolve()
    target = (repo / change_dir).resolve()
    return _ensure_path_under_root(target, changes_root(repo), field="context.changeDir")


def load_state_snapshot_from_change(repo_root: str, change_name: str):
    state_path = state_path_for_change(repo_root, change_name)
    if not state_path.exists():
        raise FileNotFoundError(f"Execution snapshot not found: {state_path}")
    try:
        snapshot = json.loads(state_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ProtocolError(
            f"Invalid JSON in execution snapshot: {state_path}",
            code="invalid_json",
            details={"path": str(state_path)},
        ) from exc
    if not isinstance(snapshot, dict):
        raise ProtocolError(
            "Invalid execution state file: expected a JSON object.",
            code="invalid_json",
            details={"path": str(state_path)},
        )
    runtime = snapshot.get("runtime")
    if not isinstance(runtime, dict):
        raise ProtocolError(
            "Invalid execution state file: missing runtime section.",
            code="invalid_json",
            details={"path": str(state_path)},
        )
    actions = runtime.get("actions")
    if not isinstance(actions, list):
        raise ProtocolError(
            "Invalid execution state file: runtime.actions must be an array.",
            code="invalid_json",
            details={"path": str(state_path)},
        )
    return snapshot, str(state_path)
