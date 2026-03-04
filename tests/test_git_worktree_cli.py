import json
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from superspec.cli import build_parser, command_git_worktree_create, command_git_worktree_finish


class GitWorktreeCliTest(unittest.TestCase):
    def test_command_git_worktree_create_prints_json_state(self):
        root = Path(tempfile.mkdtemp(prefix="superspec-"))
        args = SimpleNamespace(
            slug="feature-x",
            base="main",
            branch="wt/branch",
            path=".worktrees/wt-branch",
        )
        state = {
            "repo_root": str(root),
            "git_common_dir": str(root / ".git"),
            "base": "main",
            "branch": "wt/branch",
            "worktree_path": str(root / ".worktrees" / "wt-branch"),
            "created_at": "2026-03-03T00:00:00",
        }
        output = StringIO()
        with patch("superspec.cli.create_worktree_state", return_value=state) as mock_create:
            with redirect_stdout(output):
                command_git_worktree_create(root, args)

        mock_create.assert_called_once_with(
            repo_root=root,
            slug="feature-x",
            base="main",
            branch="wt/branch",
            path=".worktrees/wt-branch",
        )
        parsed = json.loads(output.getvalue())
        self.assertEqual(parsed["worktree_path"], state["worktree_path"])

    def test_parser_accepts_git_create_worktree_command(self):
        parser = build_parser()
        parsed = parser.parse_args(["git", "create-worktree", "--slug", "abc"])
        self.assertEqual(parsed.group, "git")
        self.assertEqual(parsed.sub, "create-worktree")
        self.assertEqual(parsed.slug, "abc")

    def test_parser_requires_slug(self):
        parser = build_parser()
        with self.assertRaises(SystemExit):
            parser.parse_args(["git", "create-worktree"])

    def test_command_git_worktree_finish_prints_json_payload(self):
        root = Path(tempfile.mkdtemp(prefix="superspec-"))
        args = SimpleNamespace(
            slug="demo",
            yes=False,
            merge=True,
            cleanup=False,
            strategy="merge",
            commit_message="",
        )
        payload = {
            "repo_root": str(root),
            "branch": "wt/20260303-1200-demo",
            "planned": ["git checkout main"],
        }
        output = StringIO()
        with patch("superspec.cli.finish_worktree_flow", return_value=payload) as mock_finish:
            with redirect_stdout(output):
                command_git_worktree_finish(root, args)

        mock_finish.assert_called_once_with(
            slug="demo",
            yes=False,
            merge=True,
            cleanup=False,
            strategy="merge",
            commit_message="",
        )
        parsed = json.loads(output.getvalue())
        self.assertEqual(parsed["branch"], payload["branch"])

    def test_parser_accepts_git_finish_worktree_command(self):
        parser = build_parser()
        parsed = parser.parse_args(
            ["git", "finish-worktree", "--slug", "abc", "--merge", "--cleanup", "--strategy", "squash"]
        )
        self.assertEqual(parsed.group, "git")
        self.assertEqual(parsed.sub, "finish-worktree")
        self.assertEqual(parsed.slug, "abc")
        self.assertTrue(parsed.merge)
        self.assertTrue(parsed.cleanup)
        self.assertEqual(parsed.strategy, "squash")

    def test_parser_rejects_removed_finish_worktree_options(self):
        parser = build_parser()
        with self.assertRaises(SystemExit):
            parser.parse_args(["git", "finish-worktree", "--state", "/tmp/x.json"])
        with self.assertRaises(SystemExit):
            parser.parse_args(["git", "finish-worktree", "--squash-message", "old"])


if __name__ == "__main__":
    unittest.main()
