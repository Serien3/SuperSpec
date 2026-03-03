import json
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from superspec.cli import build_parser, command_git_worktree_create


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


if __name__ == "__main__":
    unittest.main()
