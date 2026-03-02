import json
from pathlib import Path

from .validator import validate_plan


def resolve_change_dir(repo_root: str, change_name: str) -> Path:
    return Path(repo_root).resolve() / "openspec" / "changes" / change_name


def plan_path_for_change(repo_root: str, change_name: str) -> Path:
    return resolve_change_dir(repo_root, change_name) / "plan.json"


def load_plan_from_change(repo_root: str, change_name: str):
    plan_path = plan_path_for_change(repo_root, change_name)
    if not plan_path.exists():
        raise FileNotFoundError(f"Plan file not found: {plan_path}")
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    validate_plan(plan)
    return plan, str(plan_path)
