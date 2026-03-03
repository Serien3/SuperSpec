import json
import re
from pathlib import Path

from .errors import ProtocolError
from .validator import validate_plan


_CHANGE_NAME_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")


def _ensure_path_under_root(path: Path, root: Path, *, field: str):
    resolved_path = path.resolve()
    resolved_root = root.resolve()
    if not resolved_path.is_relative_to(resolved_root):
        raise ProtocolError(
            f"{field} escapes allowed directory",
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
    return (Path(repo_root).resolve() / "openspec" / "changes").resolve()


def resolve_change_dir(repo_root: str, change_name: str) -> Path:
    validate_change_name(change_name)
    root = changes_root(repo_root)
    return _ensure_path_under_root(root / change_name, root, field="change")


def plan_path_for_change(repo_root: str, change_name: str) -> Path:
    return resolve_change_dir(repo_root, change_name) / "plan.json"


def resolve_change_dir_from_plan_context(repo_root: str | Path, change_dir: str) -> Path:
    if not isinstance(change_dir, str) or not change_dir.strip():
        raise ProtocolError("context.changeDir must be a non-empty string", code="invalid_path")
    repo = Path(repo_root).resolve()
    target = (repo / change_dir).resolve()
    return _ensure_path_under_root(target, changes_root(repo), field="context.changeDir")


def load_plan_from_change(repo_root: str, change_name: str):
    plan_path = plan_path_for_change(repo_root, change_name)
    if not plan_path.exists():
        raise FileNotFoundError(f"Plan file not found: {plan_path}")
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    validate_plan(plan)
    return plan, str(plan_path)
