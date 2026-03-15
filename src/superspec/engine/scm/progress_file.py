from __future__ import annotations

from pathlib import Path

from superspec.engine.errors import ProtocolError

CURRENT_SESSION_START = "<!-- superspec:current-session:start -->"
CURRENT_SESSION_END = "<!-- superspec:current-session:end -->"
DETAILS_START = "<!-- superspec:details:start -->"
DETAILS_END = "<!-- superspec:details:end -->"


def progress_file_path(repo_root: Path) -> Path:
    return repo_root / "progress.md"


def build_progress_entry(
    *,
    commit_hash: str,
    change: str,
    summary: str,
    details: str,
    next_steps: str,
    committed_at: str,
    files_changed: list[str],
) -> dict:
    return {
        "commit_hash": commit_hash,
        "change": change,
        "summary": summary,
        "details": details,
        "next": next_steps,
        "committed_at": committed_at,
        "files_changed": list(files_changed),
    }


def render_progress_entry(entry: dict) -> str:
    files = entry.get("files_changed") or []
    lines = [
        f"### Commit {entry['commit_hash']}",
        f"- Time: {entry['committed_at']}",
        f"- Change: {entry['change']}",
        f"- Summary: {entry['summary']}",
        "- Details:",
        DETAILS_START,
        entry["details"],
        DETAILS_END,
        f"- Next: {entry['next']}",
        "- Files:",
    ]
    if files:
        for path in files:
            lines.append(f"  - {path}")
    else:
        lines.append("  - (none)")
    return "\n".join(lines)


def ensure_progress_markers(existing: str) -> str:
    if CURRENT_SESSION_START in existing and CURRENT_SESSION_END in existing:
        return existing

    prefix = existing.rstrip()
    lines: list[str] = []
    if prefix:
        lines.append(prefix)
        lines.append("")
    else:
        lines.append("# Progress")
        lines.append("")
    lines.extend(
        [
            "## Current Session",
            CURRENT_SESSION_START,
            CURRENT_SESSION_END,
        ]
    )
    return "\n".join(lines) + "\n"


def append_progress_entry(repo_root: Path, entry: dict) -> Path:
    path = progress_file_path(repo_root)
    existing = ""
    if path.exists():
        existing = path.read_text(encoding="utf-8")
    content = ensure_progress_markers(existing)

    start = content.find(CURRENT_SESSION_START)
    end = content.find(CURRENT_SESSION_END)
    if start == -1 or end == -1 or start > end:
        raise ProtocolError(
            "Current-session markers are invalid in progress.md.",
            code="invalid_progress_file",
            details={"path": str(path)},
        )

    section_start = start + len(CURRENT_SESSION_START)
    current_section = content[section_start:end].strip()
    rendered_entry = render_progress_entry(entry)
    if current_section:
        replacement = f"\n\n{current_section}\n\n{rendered_entry}\n"
    else:
        replacement = f"\n\n{rendered_entry}\n"

    updated = content[:section_start] + replacement + content[end:]
    path.write_text(updated, encoding="utf-8")
    return path
