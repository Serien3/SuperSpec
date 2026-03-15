from __future__ import annotations

import subprocess
from datetime import datetime, timezone
from pathlib import Path

from superspec.engine.changes.paths import resolve_change_dir
from superspec.engine.errors import ProtocolError
from superspec.engine.scm.progress_file import append_progress_entry, build_progress_entry
from superspec.engine.storage.events import append_event
from superspec.engine.storage.execution_files import execution_dir
from superspec.engine.storage.execution_snapshot import read_execution_state, write_execution_state


def run_git(repo_root: Path, args: list[str]) -> str:
    proc = subprocess.run(
        ["git", "-C", str(repo_root), *args],
        text=True,
        capture_output=True,
    )
    if proc.returncode != 0:
        raise ProtocolError(
            f"Git command failed: {' '.join(args)}.",
            code="git_command_failed",
            details={
                "command": ["git", "-C", str(repo_root), *args],
                "stdout": proc.stdout,
                "stderr": proc.stderr,
                "returncode": proc.returncode,
            },
        )
    return proc.stdout.strip()


def committed_files_for_head(repo_root: Path) -> list[str]:
    output = run_git(repo_root, ["show", "--pretty=format:", "--name-only", "HEAD"])
    files: list[str] = []
    seen: set[str] = set()
    for line in output.splitlines():
        path = line.strip()
        if not path or path in seen:
            continue
        seen.add(path)
        files.append(path)
    return files


def committed_at_for_head(repo_root: Path) -> str:
    return run_git(repo_root, ["show", "-s", "--format=%cI", "HEAD"])


def merge_files_changed(existing: object, new_files: list[str]) -> list[str]:
    merged: list[str] = []
    seen: set[str] = set()

    if isinstance(existing, list):
        for item in existing:
            if isinstance(item, str) and item and item not in seen:
                seen.add(item)
                merged.append(item)

    for path in new_files:
        if path not in seen:
            seen.add(path)
            merged.append(path)

    return merged


def stage_commit_inputs(repo_root: Path, change_dir: Path) -> None:
    state_path = (execution_dir(str(change_dir)) / "state.json").relative_to(repo_root)
    events_path = (execution_dir(str(change_dir)) / "events.log").relative_to(repo_root)
    run_git(
        repo_root,
        [
            "add",
            "-A",
            "--",
            ".",
            f":(exclude){state_path.as_posix()}",
            f":(exclude){events_path.as_posix()}",
        ],
    )


def commit_for_change(repo_root: Path, change_name: str, summary: str, details: str, next_steps: str) -> dict:
    normalized_summary = summary.strip()
    if not normalized_summary:
        raise ProtocolError("Invalid commit summary: expected a non-empty string.", code="invalid_payload")
    normalized_details = details.strip()
    if not normalized_details:
        raise ProtocolError("Invalid commit details: expected a non-empty string.", code="invalid_payload")
    normalized_next = next_steps.strip()
    if not normalized_next:
        raise ProtocolError("Invalid next field: expected a non-empty string.", code="invalid_payload")

    change_dir = resolve_change_dir(str(repo_root), change_name)
    state = read_execution_state(str(change_dir))
    if not isinstance(state, dict):
        state_path = execution_dir(str(change_dir)) / "state.json"
        raise ProtocolError(
            "Execution state not found for this change.",
            code="missing_file",
            details={"path": str(state_path), "change": change_name},
        )

    if state.get("status") != "running":
        raise ProtocolError(
            "Change is not in a running state.",
            code="invalid_state",
            details={"change": change_name, "status": state.get("status")},
        )

    stage_commit_inputs(repo_root, change_dir)
    commit_output = run_git(repo_root, ["commit", "-m", normalized_summary, "-m", normalized_details])
    commit_hash = run_git(repo_root, ["rev-parse", "HEAD"])
    committed_at = committed_at_for_head(repo_root)
    committed_files = committed_files_for_head(repo_root)
    state["files_changed"] = merge_files_changed(state.get("files_changed"), committed_files)
    state["updatedAt"] = datetime.now(timezone.utc).isoformat()
    write_execution_state(str(change_dir), state)
    progress_entry = build_progress_entry(
        commit_hash=commit_hash,
        change=change_name,
        summary=normalized_summary,
        details=normalized_details,
        next_steps=normalized_next,
        committed_at=committed_at,
        files_changed=committed_files,
    )
    progress_path = append_progress_entry(repo_root, progress_entry)
    append_event(
        str(change_dir),
        {
            "event": "git.commit",
            "change": change_name,
            "commit_hash": commit_hash,
            "summary": normalized_summary,
            "details": normalized_details,
            "next": normalized_next,
            "committed_at": committed_at,
            "files_changed": committed_files,
        },
    )

    return {
        "change": change_name,
        "commit_hash": commit_hash,
        "summary": normalized_summary,
        "details": normalized_details,
        "next": normalized_next,
        "committed_at": committed_at,
        "files_changed": list(state["files_changed"]),
        "progress_file": str(progress_path),
        "progress_entry": progress_entry,
        "commit_output": commit_output,
    }
