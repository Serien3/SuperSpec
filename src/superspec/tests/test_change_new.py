import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from superspec.cli import (
    _run_openspec_new_change,
    build_parser,
    command_change_new,
    command_plan_approve,
    command_plan_reject,
)


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

    def test_plan_complete_parser_requires_output_json(self):
        parser = build_parser()

        with self.assertRaises(SystemExit):
            parser.parse_args(["plan", "complete", "demo-change", "a1", "--result-json", '{"ok": true}'])

        args = parser.parse_args(["plan", "complete", "demo-change", "a1", "--output-json", '{"ok": true}'])
        self.assertEqual(args.output_json, '{"ok": true}')

    def test_plan_status_parser_rejects_retry_flag(self):
        parser = build_parser()
        with self.assertRaises(SystemExit):
            parser.parse_args(["plan", "status", "demo-change", "--retry"])

    def test_plan_approve_parser_defaults(self):
        parser = build_parser()
        args = parser.parse_args(["plan", "approve", "demo-change", "a1"])
        self.assertEqual(args.change, "demo-change")
        self.assertEqual(args.action_id, "a1")
        self.assertEqual(args.summary, "")

    def test_plan_reject_parser_defaults(self):
        parser = build_parser()
        args = parser.parse_args(["plan", "reject", "demo-change", "a1"])
        self.assertEqual(args.change, "demo-change")
        self.assertEqual(args.action_id, "a1")
        self.assertEqual(args.code, "human_rejected")
        self.assertEqual(args.message, "human review rejected")

    def test_command_plan_approve_maps_to_complete(self):
        root = Path(tempfile.mkdtemp(prefix="superspec-"))
        args = SimpleNamespace(change="demo-change", action_id="a1", summary="approved by reviewer")

        with patch("superspec.cli.run_protocol_action_from_cli") as mock_run:
            stdout = StringIO()
            with redirect_stdout(stdout):
                command_plan_approve(root, args)

        mock_run.assert_called_once_with(
            root,
            "demo-change",
            "complete",
            action_id="a1",
            output_payload={
                "ok": True,
                "executor": "human",
                "actionId": "a1",
                "summary": "approved by reviewer",
            },
        )
        self.assertIn("Action a1 approved.", stdout.getvalue())

    def test_command_plan_reject_maps_to_fail(self):
        root = Path(tempfile.mkdtemp(prefix="superspec-"))
        args = SimpleNamespace(
            change="demo-change",
            action_id="a1",
            code="human_rejected",
            message="needs changes",
        )

        with patch("superspec.cli.run_protocol_action_from_cli") as mock_run:
            stdout = StringIO()
            with redirect_stdout(stdout):
                command_plan_reject(root, args)

        mock_run.assert_called_once_with(
            root,
            "demo-change",
            "fail",
            action_id="a1",
            error_payload={
                "code": "human_rejected",
                "message": "needs changes",
                "executor": "human",
            },
        )
        self.assertIn("Action a1 rejected.", stdout.getvalue())


if __name__ == "__main__":
    unittest.main()
