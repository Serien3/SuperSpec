#!/usr/bin/env python3
import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Callable, Optional, Dict, Any


def run(args: list[str], *, cwd: Optional[Path] = None) -> str:
    proc = subprocess.run(
        args,
        cwd=str(cwd) if cwd else None,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    if proc.returncode != 0:
        raise RuntimeError(
            f"command failed: {' '.join(args)}\nstdout:\n{proc.stdout}\nstderr:\n{proc.stderr}"
        )
    return proc.stdout.strip()


def slugify(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    value = value.strip("-")
    return value or "work"


def _resolve_state_path_from_git_common_dir(git_common_dir: Path, explicit_slug: Optional[str]) -> Path:
    state_dir = git_common_dir / "codex-worktree-flow"
    if explicit_slug:
        slug = slugify(explicit_slug)
        state_path = state_dir / f"{slug}.json"
        if not state_path.exists():
            raise RuntimeError(f"state not found for slug '{slug}': {state_path}")
        return state_path

    state_files = sorted(path for path in state_dir.glob("*.json") if path.name != "state.json")
    if len(state_files) == 1:
        return state_files[0]
    if len(state_files) > 1:
        names = ", ".join(path.stem for path in state_files)
        raise RuntimeError(
            f"multiple state files found ({names}). Pass --slug to disambiguate."
        )
    raise RuntimeError(f"state not found under: {state_dir}")


def load_state(explicit_slug: Optional[str]) -> Dict[str, Any]:
    toplevel = Path(run(["git", "rev-parse", "--show-toplevel"]))
    git_common_dir = Path(
        run(["git", "-C", str(toplevel), "rev-parse", "--git-common-dir"])
    )
    state_path = _resolve_state_path_from_git_common_dir(git_common_dir, explicit_slug)
    try:
        return json.loads(state_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"invalid JSON in state file: {state_path}") from exc


def git_is_clean(repo_root: Path) -> bool:
    out = run(["git", "-C", str(repo_root), "status", "--porcelain"])
    return out.strip() == ""


def _confirm_cleanup_without_merge(prompt_fn: Callable[[str], str]) -> bool:
    warning = (
        "WARNING: You are running --cleanup without --merge. "
        "This will remove the worktree and branch, and unmerged work may be lost."
    )
    answer = prompt_fn(f"{warning}\nType 'yes' to continue: ").strip().lower()
    return answer == "yes"


def finish_worktree_flow(
    *,
    slug: str = "",
    yes: bool = False,
    merge: bool = False,
    cleanup: bool = False,
    strategy: str = "merge",
    commit_message: str = "",
    prompt_fn: Callable[[str], str] = input,
) -> Dict[str, Any]:
    state = load_state(slug or None)
    repo_root = Path(state["repo_root"])
    base = state["base"]
    merge_target = state["merge_target"]
    branch = state["branch"]
    worktree_path = Path(state["worktree_path"])

    planned = []
    normalized_commit_message = commit_message.strip()
    if merge:
        if strategy == "merge":
            planned.append(f"git checkout {merge_target} (in {repo_root})")
            planned.append(f'git merge --no-ff -m "<commit-message>" {branch}')
        else:
            planned.append(f"git checkout {merge_target} (in {repo_root})")
            planned.append(f"git merge --squash {branch}")
            planned.append('git commit -m "<commit-message>"')
    if cleanup:
        planned.append(f"git worktree remove {worktree_path}")
        planned.append(f"git branch -d {branch}")
        planned.append(f"remove {state.get('state_path') or '<state file>'}")

    if not yes:
        payload = {
            "repo_root": str(repo_root),
            "base": base,
            "merge_target": merge_target,
            "branch": branch,
            "worktree_path": str(worktree_path),
            "planned": planned,
            "note": "Add --yes to execute.",
        }
        if cleanup and not merge:
            payload["warning"] = (
                "cleanup without merge can remove the worktree branch without preserving unmerged changes"
            )
        return payload

    if cleanup and not merge and not _confirm_cleanup_without_merge(prompt_fn):
        raise RuntimeError("cleanup aborted by user")

    if merge:
        if not git_is_clean(repo_root):
            raise RuntimeError(
                f"main worktree not clean: {repo_root} (commit/stash first)"
            )

        run(["git", "-C", str(repo_root), "checkout", merge_target])
        if strategy == "merge":
            if not normalized_commit_message:
                raise RuntimeError(
                    "--strategy merge requires --commit-message to avoid opening an editor"
                )
            run(
                [
                    "git",
                    "-C",
                    str(repo_root),
                    "-c",
                    "merge.autoEdit=false",
                    "merge",
                    "--no-ff",
                    "-m",
                    normalized_commit_message,
                    branch,
                ]
            )
        else:
            if not normalized_commit_message:
                raise RuntimeError(
                    "--strategy squash requires --commit-message to avoid opening an editor"
                )
            run(["git", "-C", str(repo_root), "merge", "--squash", branch])
            run(["git", "-C", str(repo_root), "commit", "-m", normalized_commit_message])

    if cleanup:
        run(["git", "-C", str(repo_root), "worktree", "remove", str(worktree_path)])
        # Safe delete only; if not merged, Git will refuse.
        run(["git", "-C", str(repo_root), "branch", "-d", branch])
        if state.get("state_path"):
            resolved_state_path = Path(state["state_path"])
        else:
            resolved_state_path = _resolve_state_path_from_git_common_dir(Path(state["git_common_dir"]), state.get("slug"))
        if resolved_state_path.exists():
            resolved_state_path.unlink()

    return {
        "done": True,
        "repo_root": str(repo_root),
        "base": base,
        "merge_target": merge_target,
        "branch": branch,
        "worktree_path": str(worktree_path),
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Merge back and/or cleanup a git worktree (Codex helper)."
    )
    parser.add_argument(
        "--slug",
        default="",
        help="Slug of target worktree state (optional).",
    )
    parser.add_argument(
        "--yes",
        action="store_true",
        help="Actually perform actions. Without this, only prints plan.",
    )
    parser.add_argument(
        "--merge",
        action="store_true",
        help="Merge branch into base in the main worktree.",
    )
    parser.add_argument(
        "--cleanup",
        action="store_true",
        help="Remove worktree and delete branch (safe delete).",
    )
    parser.add_argument(
        "--strategy",
        default="merge",
        choices=["merge", "squash"],
        help="Merge strategy.",
    )
    parser.add_argument(
        "--commit-message",
        default="",
        help="Commit message to use for merge commit (strategy=merge) or squash commit (strategy=squash).",
    )
    args = parser.parse_args()

    payload = finish_worktree_flow(
        slug=args.slug,
        yes=bool(args.yes),
        merge=bool(args.merge),
        cleanup=bool(args.cleanup),
        strategy=args.strategy,
        commit_message=args.commit_message,
    )
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as e:
        print(f"[git-worktree-flow] ERROR: {e}", file=sys.stderr)
        raise SystemExit(1)
