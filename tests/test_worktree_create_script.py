import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from superspec.scripts.worktree_create import create_worktree_state, detect_default_base


class WorktreeCreateScriptTest(unittest.TestCase):
    def test_detect_default_base_rejects_wt_branch_from_symbolic_ref(self):
        root = Path(tempfile.mkdtemp(prefix="superspec-"))
        with patch("superspec.scripts.worktree_create.try_run", return_value="wt/20260303-1230-demo"):
            with self.assertRaises(RuntimeError):
                detect_default_base(root)

    def test_detect_default_base_rejects_wt_branch_from_rev_parse(self):
        root = Path(tempfile.mkdtemp(prefix="superspec-"))
        with patch("superspec.scripts.worktree_create.try_run", return_value=None):
            with patch("superspec.scripts.worktree_create.run", return_value="wt/20260303-1230-demo"):
                with self.assertRaises(RuntimeError):
                    detect_default_base(root)

    def test_create_worktree_state_writes_slug_named_state_file(self):
        root = Path(tempfile.mkdtemp(prefix="superspec-"))
        git_common_dir = root / ".git"
        worktree_path = root / ".worktrees" / "wt-demo"

        def fake_run(args, *, cwd=None):
            if args[:4] == ["git", "-C", str(root), "rev-parse"] and args[-1] == "--git-common-dir":
                return str(git_common_dir)
            if args[:4] == ["git", "-C", str(root), "worktree"] and args[4] == "add":
                return ""
            raise AssertionError(f"unexpected run() call: {args}")

        with patch("superspec.scripts.worktree_create.run", side_effect=fake_run):
            with patch(
                "superspec.scripts.worktree_create.subprocess.run",
                return_value=SimpleNamespace(returncode=1),
            ):
                state = create_worktree_state(
                    repo_root=root,
                    slug="Feature Demo",
                    base="main",
                    branch="wt/demo",
                    path=str(worktree_path),
                )

        expected_state_path = git_common_dir / "codex-worktree-flow" / "feature-demo.json"
        self.assertTrue(expected_state_path.exists())
        self.assertEqual(state["state_path"], str(expected_state_path))
        self.assertEqual(state["slug"], "feature-demo")

    def test_create_worktree_state_rejects_conflicting_slug(self):
        root = Path(tempfile.mkdtemp(prefix="superspec-"))
        git_common_dir = root / ".git"
        state_dir = git_common_dir / "codex-worktree-flow"
        state_dir.mkdir(parents=True, exist_ok=True)
        (state_dir / "feature-demo.json").write_text("{}", encoding="utf-8")

        def fake_run(args, *, cwd=None):
            if args[:4] == ["git", "-C", str(root), "rev-parse"] and args[-1] == "--git-common-dir":
                return str(git_common_dir)
            raise AssertionError(f"unexpected run() call: {args}")

        with patch("superspec.scripts.worktree_create.run", side_effect=fake_run):
            with self.assertRaises(RuntimeError):
                create_worktree_state(
                    repo_root=root,
                    slug="Feature Demo",
                    base="main",
                    branch="wt/demo",
                    path=str(root / ".worktrees" / "wt-demo"),
                )


if __name__ == "__main__":
    unittest.main()
