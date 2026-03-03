import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from superspec.scripts.worktree_finish import _resolve_state_path_from_git_common_dir, finish_worktree_flow


class WorktreeFinishScriptTest(unittest.TestCase):
    def test_resolve_state_path_with_slug(self):
        git_common_dir = Path(tempfile.mkdtemp(prefix="superspec-")) / ".git"
        state_dir = git_common_dir / "codex-worktree-flow"
        state_dir.mkdir(parents=True, exist_ok=True)
        state_path = state_dir / "demo-slug.json"
        state_path.write_text("{}", encoding="utf-8")

        resolved = _resolve_state_path_from_git_common_dir(git_common_dir, "Demo Slug")
        self.assertEqual(resolved, state_path)

    def test_resolve_state_path_without_slug_rejects_multiple_states(self):
        git_common_dir = Path(tempfile.mkdtemp(prefix="superspec-")) / ".git"
        state_dir = git_common_dir / "codex-worktree-flow"
        state_dir.mkdir(parents=True, exist_ok=True)
        (state_dir / "alpha.json").write_text("{}", encoding="utf-8")
        (state_dir / "beta.json").write_text("{}", encoding="utf-8")

        with self.assertRaises(RuntimeError):
            _resolve_state_path_from_git_common_dir(git_common_dir, None)

    def test_resolve_state_path_without_slug_accepts_single_state(self):
        git_common_dir = Path(tempfile.mkdtemp(prefix="superspec-")) / ".git"
        state_dir = git_common_dir / "codex-worktree-flow"
        state_dir.mkdir(parents=True, exist_ok=True)
        state_path = state_dir / "alpha.json"
        state_path.write_text("{}", encoding="utf-8")

        resolved = _resolve_state_path_from_git_common_dir(git_common_dir, None)
        self.assertEqual(resolved, state_path)

    def test_finish_worktree_flow_preview_cleanup_without_merge_has_warning(self):
        state = {
            "repo_root": "/repo",
            "base": "main",
            "branch": "wt/demo",
            "worktree_path": "/repo/.worktrees/wt-demo",
            "state_path": "/repo/.git/codex-worktree-flow/demo.json",
        }
        with patch("superspec.scripts.worktree_finish.load_state", return_value=state):
            payload = finish_worktree_flow(slug="demo", yes=False, cleanup=True, merge=False)
        self.assertIn("warning", payload)

    def test_finish_worktree_flow_yes_cleanup_without_merge_requires_confirmation(self):
        state = {
            "repo_root": "/repo",
            "base": "main",
            "branch": "wt/demo",
            "worktree_path": "/repo/.worktrees/wt-demo",
            "state_path": "/repo/.git/codex-worktree-flow/demo.json",
        }
        with patch("superspec.scripts.worktree_finish.load_state", return_value=state):
            with self.assertRaises(RuntimeError):
                finish_worktree_flow(
                    slug="demo",
                    yes=True,
                    cleanup=True,
                    merge=False,
                    prompt_fn=lambda _: "no",
                )


if __name__ == "__main__":
    unittest.main()
