import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from superspec.cli import (
    _create_change_scaffold,
    build_parser,
    command_changelist,
    command_change_new,
    command_plan_approve,
    command_plan_reject,
)


class ChangeNewCommandTest(unittest.TestCase):
    def test_create_change_scaffold_creates_change_directory_only(self):
        root = Path(tempfile.mkdtemp(prefix="superspec-"))
        change_dir = _create_change_scaffold(root, "demo-change")

        self.assertEqual(change_dir, root / "superspec" / "changes" / "demo-change")
        self.assertTrue(change_dir.is_dir())

    def test_command_change_new_creates_scaffold(self):
        root = Path(tempfile.mkdtemp(prefix="superspec-"))
        args = SimpleNamespace(change="demo-change")

        stdout = StringIO()
        with redirect_stdout(stdout):
            command_change_new(root, args)

        change_dir = root / "superspec" / "changes" / "demo-change"
        self.assertTrue(change_dir.is_dir())
        self.assertIn("Plan not initialized for change 'demo-change'.", stdout.getvalue())

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

    def test_changelist_parser_works(self):
        parser = build_parser()
        args = parser.parse_args(["change", "list"])
        self.assertEqual(args.group, "change")
        self.assertEqual(args.sub, "list")

    def test_command_changelist_prints_sorted_change_names(self):
        root = Path(tempfile.mkdtemp(prefix="superspec-"))
        (root / "superspec" / "changes" / "z-last").mkdir(parents=True, exist_ok=True)
        (root / "superspec" / "changes" / "a-first").mkdir(parents=True, exist_ok=True)
        (root / "superspec" / "changes" / "README.md").write_text("not a dir", encoding="utf-8")

        stdout = StringIO()
        with redirect_stdout(stdout):
            command_changelist(root, SimpleNamespace())

        self.assertEqual(stdout.getvalue().splitlines(), ["a-first", "z-last"])

    def test_command_changelist_prints_empty_message_when_missing(self):
        root = Path(tempfile.mkdtemp(prefix="superspec-"))
        stdout = StringIO()
        with redirect_stdout(stdout):
            command_changelist(root, SimpleNamespace())

        self.assertEqual(stdout.getvalue().strip(), "No changes found.")

    def test_version_flag_prints_version(self):
        parser = build_parser()
        stdout = StringIO()
        with redirect_stdout(stdout):
            with self.assertRaises(SystemExit) as ctx:
                parser.parse_args(["--version"])

        self.assertEqual(ctx.exception.code, 0)
        self.assertIn("superspec", stdout.getvalue())

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
