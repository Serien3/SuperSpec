import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from superspec.cli import _run_openspec_new_change, build_parser, command_change_new


class ChangeNewCommandTest(unittest.TestCase):
    def test_run_openspec_new_change_does_not_pass_summary(self):
        root = Path(tempfile.mkdtemp(prefix="superspec-"))
        with patch("superspec.cli.subprocess.run") as mock_run:
            mock_run.return_value = SimpleNamespace(returncode=0, stdout="ok\n", stderr="")
            _run_openspec_new_change(root, "demo-change")

        mock_run.assert_called_once_with(
            ["openspec", "new", "change", "demo-change"],
            cwd=root,
            text=True,
            capture_output=True,
        )

    def test_command_change_new_invokes_openspec_without_summary(self):
        root = Path(tempfile.mkdtemp(prefix="superspec-"))
        args = SimpleNamespace(change="demo-change")

        with patch("superspec.cli.subprocess.run") as mock_run:
            mock_run.return_value = SimpleNamespace(returncode=0, stdout="", stderr="")
            command_change_new(root, args)

        mock_run.assert_called_once_with(
            ["openspec", "new", "change", "demo-change"],
            cwd=root,
            text=True,
            capture_output=True,
        )

    def test_change_new_parser_rejects_summary_flag(self):
        parser = build_parser()

        with self.assertRaises(SystemExit):
            parser.parse_args(["change", "new", "demo-change", "--summary", "demo"])

    def test_change_new_parser_rejects_init_plan_flags(self):
        parser = build_parser()

        with self.assertRaises(SystemExit):
            parser.parse_args(["change", "new", "demo-change", "--init-plan"])
        with self.assertRaises(SystemExit):
            parser.parse_args(["change", "new", "demo-change", "--plan-schema", "SDD"])

    def test_plan_init_parser_requires_schema(self):
        parser = build_parser()

        with self.assertRaises(SystemExit):
            parser.parse_args(["plan", "init", "demo-change"])


if __name__ == "__main__":
    unittest.main()
