from __future__ import annotations

import subprocess
from datetime import datetime, timezone
from pathlib import Path

from superspec.engine.errors import ProtocolError
from superspec.engine.plan_loader import resolve_change_dir
from superspec.engine.state_store import append_event, execution_dir, read_execution_state, write_execution_state


def _run_git(repo_root: Path, args: list[str]) -> str:
    proc = subprocess.run(
        ["git", "-C", str(repo_root), *args],
        text=True,
        capture_output=True,
    )
    if proc.returncode != 0:
        raise ProtocolError(
            f"git {' '.join(args)} failed",
            code="git_command_failed",
            details={
                "command": ["git", "-C", str(repo_root), *args],
                "stdout": proc.stdout,
                "stderr": proc.stderr,
                "returncode": proc.returncode,
            },
        )
    return proc.stdout.strip()


def commit_for_change(repo_root: Path, change_name: str, message: str) -> dict:
    normalized_message = message.strip()
    if not normalized_message:
        raise ProtocolError("message must be a non-empty string", code="invalid_payload")

    change_dir = resolve_change_dir(str(repo_root), change_name)
    state = read_execution_state(str(change_dir))
    if not isinstance(state, dict):
        state_path = execution_dir(str(change_dir)) / "state.json"
        raise ProtocolError(
            "execution state not found for change",
            code="missing_file",
            details={"path": str(state_path), "change": change_name},
        )

    if state.get("status") != "running":
        raise ProtocolError(
            "execution state is not running",
            code="invalid_state",
            details={"change": change_name, "status": state.get("status")},
        )

    _run_git(repo_root, ["commit", "-m", normalized_message])
    commit_hash = _run_git(repo_root, ["rev-parse", "HEAD"])

    commit_record = {
        "commit_hash": commit_hash,
        "message": normalized_message,
    }
    state["commit_by_superspec_last"] = commit_record
    state["updatedAt"] = datetime.now(timezone.utc).isoformat()
    write_execution_state(str(change_dir), state)
    append_event(
        str(change_dir),
        {
            "event": "git.commit",
            "change": change_name,
            "commit_hash": commit_hash,
            "message": normalized_message,
        },
    )

    return {
        "change": change_name,
        "commit_by_superspec_last": commit_record,
    }
