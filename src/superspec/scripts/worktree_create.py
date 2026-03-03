#!/usr/bin/env python3
import argparse
import datetime as dt
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Optional


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


def try_run(args: list[str], *, cwd: Optional[Path] = None) -> Optional[str]:
    proc = subprocess.run(
        args,
        cwd=str(cwd) if cwd else None,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    if proc.returncode != 0:
        return None
    return proc.stdout.strip()


def slugify(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    value = value.strip("-")
    return value or "work"


def detect_default_base(toplevel: Path) -> str:
    current = try_run(["git", "-C", str(toplevel), "symbolic-ref", "--quiet", "--short", "HEAD"])
    if current:
        if current.startswith("wt/"):
            raise RuntimeError(
                "cannot infer base branch from a worktree branch. Please pass --base explicitly from a mainline branch."
            )
        return current

    fallback = run(["git", "-C", str(toplevel), "rev-parse", "--abbrev-ref", "HEAD"])
    if fallback == "HEAD":
        raise RuntimeError("cannot infer base branch: repository is in detached HEAD state")
    if fallback.startswith("wt/"):
        raise RuntimeError(
            "cannot infer base branch from a worktree branch. Please pass --base explicitly from a mainline branch."
        )
    return fallback


def create_worktree_state(
    *,
    repo_root: Optional[Path] = None,
    slug: str,
    base: str = "",
    branch: str = "",
    path: str = "",
) -> dict[str, str]:
    if repo_root is None:
        toplevel = Path(run(["git", "rev-parse", "--show-toplevel"]))
    else:
        toplevel = Path(repo_root).resolve()
    git_common_dir = Path(run(["git", "-C", str(toplevel), "rev-parse", "--git-common-dir"]))
    selected_base = base.strip() or detect_default_base(toplevel)

    now = dt.datetime.now().strftime("%Y%m%d-%H%M")
    selected_slug = slugify(slug)
    selected_branch = branch.strip() or f"wt/{now}-{selected_slug}"

    worktree_path = path.strip()
    if worktree_path:
        worktree_dir = Path(worktree_path)
        if not worktree_dir.is_absolute():
            worktree_dir = toplevel / worktree_dir
    else:
        safe_dir = selected_branch.replace("/", "__")
        worktree_dir = toplevel / ".worktrees" / safe_dir

    if worktree_dir.exists():
        raise RuntimeError(f"worktree path already exists: {worktree_dir}")

    worktree_dir.parent.mkdir(parents=True, exist_ok=True)

    # Ignore `.worktrees/` locally without touching tracked `.gitignore`.
    info_exclude = git_common_dir / "info" / "exclude"
    info_exclude.parent.mkdir(parents=True, exist_ok=True)
    exclude_line = ".worktrees/"
    existing_exclude = info_exclude.read_text(encoding="utf-8") if info_exclude.exists() else ""
    if exclude_line not in existing_exclude.splitlines():
        with info_exclude.open("a", encoding="utf-8") as f:
            if existing_exclude and not existing_exclude.endswith("\n"):
                f.write("\n")
            f.write(exclude_line + "\n")

    branch_exists = (
        subprocess.run(
            ["git", "-C", str(toplevel), "show-ref", "--verify", "--quiet", f"refs/heads/{selected_branch}"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        ).returncode
        == 0
    )

    if branch_exists:
        run(["git", "-C", str(toplevel), "worktree", "add", str(worktree_dir), selected_branch])
    else:
        run(["git", "-C", str(toplevel), "worktree", "add", "-b", selected_branch, str(worktree_dir), selected_base])

    state_dir = git_common_dir / "codex-worktree-flow"
    state_dir.mkdir(parents=True, exist_ok=True)
    state_path = state_dir / "state.json"
    state = {
        "repo_root": str(toplevel),
        "git_common_dir": str(git_common_dir),
        "base": selected_base,
        "branch": selected_branch,
        "worktree_path": str(worktree_dir),
        "created_at": dt.datetime.now().isoformat(timespec="seconds"),
    }
    state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return state


def main() -> int:
    parser = argparse.ArgumentParser(description="Create a git worktree for a new branch (Codex helper).")
    parser.add_argument("--slug", required=True, help="Short slug for the branch name, e.g. 'fix-player'.")
    parser.add_argument("--base", default="", help="Base branch/ref, e.g. 'main' or 'origin/main'.")
    parser.add_argument("--branch", default="", help="Branch name to create/use, e.g. 'wt/20260203-fix-player'.")
    parser.add_argument("--path", default="", help="Worktree path (relative to repo root or absolute).")
    args = parser.parse_args()

    state = create_worktree_state(
        slug=args.slug,
        base=args.base,
        branch=args.branch,
        path=args.path,
    )

    print(json.dumps(state, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as e:
        print(f"[git-worktree-flow] ERROR: {e}", file=sys.stderr)
        return_code = 1
        raise SystemExit(return_code)
