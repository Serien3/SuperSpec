from __future__ import annotations

import re
from datetime import datetime, timezone
from pathlib import Path

from superspec.engine.errors import ProtocolError

CURRENT_SESSION_HEADING = "## Current Session"
CURRENT_SESSION_START = "<!-- superspec:current-session:start -->"
CURRENT_SESSION_END = "<!-- superspec:current-session:end -->"
DETAILS_START = "<!-- superspec:details:start -->"
DETAILS_END = "<!-- superspec:details:end -->"
SESSION_HEADING_PATTERN = re.compile(r"^## (?P<date>\d{4}-\d{2}-\d{2}) Session (?P<number>\d+)$", re.MULTILINE)
COMMIT_HEADER_PATTERN = re.compile(r"^### Commit (?P<hash>\S+)$", re.MULTILINE)


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
    details = entry.get("details", "")
    lines = [
        f"### Commit {entry['commit_hash']}",
        f"- Time: {entry['committed_at']}",
        f"- Change: {entry['change']}",
        f"- Summary: {entry['summary']}",
        f"- Next: {entry['next']}",
        "- Files:",
    ]
    if details.strip():
        lines[4:4] = [
            "- Details:",
            DETAILS_START,
            details,
            DETAILS_END,
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
            CURRENT_SESSION_HEADING,
            CURRENT_SESSION_START,
            CURRENT_SESSION_END,
        ]
    )
    return "\n".join(lines) + "\n"


def _current_session_bounds(content: str) -> tuple[int, int, int]:
    heading = content.find(CURRENT_SESSION_HEADING)
    start = content.find(CURRENT_SESSION_START)
    end = content.find(CURRENT_SESSION_END)
    if start == -1 or end == -1 or start > end:
        raise ProtocolError(
            "Current-session markers are invalid in progress.md.",
            code="invalid_progress_file",
            details={},
        )
    return heading, start, end


def _current_session_section(content: str) -> tuple[int, int, str]:
    _, start, end = _current_session_bounds(content)
    section_start = start + len(CURRENT_SESSION_START)
    return section_start, end, content[section_start:end]


def _extract_field(block: str, prefix: str) -> str | None:
    for line in block.splitlines():
        if line.startswith(prefix):
            return line[len(prefix) :].strip()
    return None


def _extract_details(block: str) -> str:
    marker = f"- Details:\n{DETAILS_START}\n"
    start = block.find(marker)
    if start == -1:
        return ""
    details_start = start + len(marker)
    end = block.find(f"\n{DETAILS_END}", details_start)
    if end == -1:
        raise ProtocolError(
            "Details markers are invalid in progress.md.",
            code="invalid_progress_file",
            details={},
        )
    return block[details_start:end]


def _extract_files(block: str) -> list[str]:
    lines = block.splitlines()
    try:
        files_index = lines.index("- Files:")
    except ValueError:
        return []

    files: list[str] = []
    for line in lines[files_index + 1 :]:
        if line.startswith("  - "):
            value = line[4:].strip()
            if value and value != "(none)":
                files.append(value)
            continue
        if line.strip():
            break
    return files


def parse_progress_entries(section: str) -> list[dict]:
    trimmed = section.strip()
    if not trimmed:
        return []

    matches = list(COMMIT_HEADER_PATTERN.finditer(trimmed))
    if not matches:
        raise ProtocolError(
            "Current-session entries are invalid in progress.md.",
            code="invalid_progress_file",
            details={},
        )

    entries: list[dict] = []
    for index, match in enumerate(matches):
        block_start = match.start()
        block_end = matches[index + 1].start() if index + 1 < len(matches) else len(trimmed)
        block = trimmed[block_start:block_end].strip()

        commit_hash = match.group("hash")
        committed_at = _extract_field(block, "- Time: ")
        change = _extract_field(block, "- Change: ")
        summary = _extract_field(block, "- Summary: ")
        next_steps = _extract_field(block, "- Next: ")
        if not all([committed_at, change, summary, next_steps]):
            raise ProtocolError(
                "Current-session entries are invalid in progress.md.",
                code="invalid_progress_file",
                details={"commit_hash": commit_hash},
            )
        entries.append(
            build_progress_entry(
                commit_hash=commit_hash,
                change=change,
                summary=summary,
                details=_extract_details(block),
                next_steps=next_steps,
                committed_at=committed_at,
                files_changed=_extract_files(block),
            )
        )
    return entries


def _dedupe_preserving_order(values: list[str]) -> list[str]:
    deduped: list[str] = []
    seen: set[str] = set()
    for value in values:
        if value and value not in seen:
            seen.add(value)
            deduped.append(value)
    return deduped


def _detail_lines(details: str) -> list[str]:
    return [line.strip() for line in details.splitlines() if line.strip()]


def next_session_number(content: str, session_date: str) -> int:
    highest = 0
    for match in SESSION_HEADING_PATTERN.finditer(content):
        if match.group("date") != session_date:
            continue
        highest = max(highest, int(match.group("number")))
    return highest + 1


def render_session_summary(entries: list[dict], *, finished_at: str) -> str:
    session_date = finished_at[:10]
    session_number = next_session_number("", session_date)
    return render_session_summary_with_number(
        entries,
        session_date=session_date,
        session_number=session_number,
        finished_at=finished_at,
    )


def render_session_summary_with_number(
    entries: list[dict],
    *,
    session_date: str,
    session_number: int,
    finished_at: str,
) -> str:
    done_lines: list[str] = []
    changes: list[str] = []
    files: list[str] = []
    for entry in entries:
        done_lines.append(f"- {entry['summary']}")
        for detail in _detail_lines(entry.get("details", "")):
            done_lines.append(f"\t- {detail}")
        changes.append(entry["change"])
        files.extend(entry.get("files_changed", []))

    unique_changes = _dedupe_preserving_order(changes)
    unique_files = _dedupe_preserving_order(files)

    lines = [
        f"## {session_date} Session {session_number}",
        f"- Finish: {finished_at}",
        "",
        "### Done",
    ]
    lines.extend(done_lines or ["- (none)"])
    lines.extend(["", "### Changes"])
    lines.extend([f"- {change}" for change in unique_changes] or ["- (none)"])
    lines.extend(["", "### Files"])
    lines.extend([f"- {path}" for path in unique_files] or ["- (none)"])
    lines.extend(["", "### Next", entries[-1]["next"]])
    return "\n".join(lines)


def summarize_current_session(repo_root: Path, *, finished_at: str | None = None) -> dict:
    path = progress_file_path(repo_root)
    existing = ""
    if path.exists():
        existing = path.read_text(encoding="utf-8")
    content = ensure_progress_markers(existing)
    heading_index, _, end = _current_session_bounds(content)
    section_start, section_end, current_section = _current_session_section(content)
    entries = parse_progress_entries(current_section)
    if not entries:
        raise ProtocolError(
            "Current session has no commit entries to summarize.",
            code="empty_current_session",
            details={"path": str(path)},
        )

    finished = finished_at or datetime.now(timezone.utc).isoformat()
    session_date = finished[:10]
    session_number = next_session_number(content, session_date)
    summary = render_session_summary_with_number(
        entries,
        session_date=session_date,
        session_number=session_number,
        finished_at=finished,
    )

    current_block_end = end + len(CURRENT_SESSION_END)
    current_section_block = (content[heading_index:section_start] + "\n" + content[section_end:current_block_end]).rstrip()
    first_session_match = SESSION_HEADING_PATTERN.search(content)
    first_session_index = first_session_match.start() if first_session_match else heading_index
    managed_start = min(index for index in [heading_index, first_session_index] if index != -1)
    prefix = content[:managed_start].rstrip()
    managed_tail = (content[managed_start:heading_index] + content[current_block_end:]).strip()

    updated_parts: list[str] = []
    if prefix:
        updated_parts.append(prefix)
    updated_parts.append(current_section_block)
    updated_parts.append(summary)
    if managed_tail:
        updated_parts.append(managed_tail)
    updated = "\n\n".join(part for part in updated_parts if part) + "\n"
    path.write_text(updated, encoding="utf-8")
    return {
        "progress_file": str(path),
        "finished_at": finished,
        "session_date": session_date,
        "session_number": session_number,
        "entries": entries,
        "summary": summary,
    }


def append_progress_entry(repo_root: Path, entry: dict) -> Path:
    path = progress_file_path(repo_root)
    existing = ""
    if path.exists():
        existing = path.read_text(encoding="utf-8")
    content = ensure_progress_markers(existing)

    _, start, end = _current_session_bounds(content)
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
