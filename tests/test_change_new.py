import tempfile
import unittest
from contextlib import redirect_stdout
import json
from io import StringIO
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from superspec.cli import (
    build_parser,
    command_change_advance,
    command_plan_approve,
    command_plan_reject,
)
from superspec.engine.errors import ProtocolError


class ChangeNewCommandTest(unittest.TestCase):
    def test_change_advance_parser_forms(self):
        parser = build_parser()

        args = parser.parse_args(["change", "advance"])
        self.assertEqual(args.group, "change")
        self.assertEqual(args.sub, "advance")
        self.assertIsNone(args.change)
        self.assertIsNone(args.new)

        args = parser.parse_args(["change", "advance", "demo-change"])
        self.assertEqual(args.change, "demo-change")
        self.assertIsNone(args.new)

        args = parser.parse_args(["change", "advance", "--new", "SDD/demo-change", "--json"])
        self.assertEqual(args.new, "SDD/demo-change")
        self.assertTrue(args.json)

    def test_command_change_advance_rejects_mixed_selector_and_change(self):
        root = Path(tempfile.mkdtemp(prefix="superspec-"))
        args = SimpleNamespace(change="demo-change", new="SDD/other", owner="agent", json=False)

        with self.assertRaises(ProtocolError):
            command_change_advance(root, args)

    def test_command_change_advance_without_args_behaves_like_list(self):
        root = Path(tempfile.mkdtemp(prefix="superspec-"))
        (root / "superspec" / "changes" / "add-test").mkdir(parents=True, exist_ok=True)
        (root / "superspec" / "changes" / "legacy").mkdir(parents=True, exist_ok=True)

        args = SimpleNamespace(change=None, new=None, owner="agent", json=False)
        stdout = StringIO()
        with redirect_stdout(stdout):
            command_change_advance(root, args)

        self.assertEqual(stdout.getvalue().splitlines(), ["add-test", "legacy"])

    def test_command_change_advance_existing_maps_to_next(self):
        root = Path(tempfile.mkdtemp(prefix="superspec-"))
        change_dir = root / "superspec" / "changes" / "demo"
        change_dir.mkdir(parents=True, exist_ok=True)
        (change_dir / "plan.json").write_text(
            json.dumps(
                {
                    "metadata": {"workflow": {"id": "SDD", "version": "1.0.0"}},
                }
            ),
            encoding="utf-8",
        )
        args = SimpleNamespace(change="demo", new=None, owner="agent", json=True)

        with patch("superspec.cli.run_protocol_action_from_cli") as mock_run:
            mock_run.return_value = {"state": "blocked", "action": None}
            stdout = StringIO()
            with redirect_stdout(stdout):
                command_change_advance(root, args)

        mock_run.assert_called_once_with(root, "demo", "next", owner="agent")
        self.assertIn('"state": "blocked"', stdout.getvalue())

    def test_command_change_advance_new_creates_change_and_bootstraps_plan(self):
        root = Path(tempfile.mkdtemp(prefix="superspec-"))
        args = SimpleNamespace(change=None, new="SDD/add-test-feature", owner="agent", json=True)

        stdout = StringIO()
        with redirect_stdout(stdout):
            command_change_advance(root, args)

        plan_path = root / "superspec" / "changes" / "add-test-feature" / "plan.json"
        self.assertTrue(plan_path.exists())
        payload = json.loads(stdout.getvalue())
        self.assertIn(payload["state"], {"ready", "blocked", "done"})

    def test_command_change_advance_new_rejects_malformed_selector(self):
        root = Path(tempfile.mkdtemp(prefix="superspec-"))
        args = SimpleNamespace(change=None, new="SDD/add/test", owner="agent", json=False)

        with self.assertRaises(ProtocolError):
            command_change_advance(root, args)

    def test_removed_legacy_parsers_reject_old_commands(self):
        parser = build_parser()
        with self.assertRaises(SystemExit):
            parser.parse_args(["change", "new", "demo-change"])
        with self.assertRaises(SystemExit):
            parser.parse_args(["change", "list"])
        with self.assertRaises(SystemExit):
            parser.parse_args(["plan", "init", "demo-change", "--schema", "SDD"])
        with self.assertRaises(SystemExit):
            parser.parse_args(["plan", "next", "demo-change"])

    def test_plan_complete_parser_requires_output_json(self):
        parser = build_parser()

        with self.assertRaises(SystemExit):
            parser.parse_args(["plan", "complete", "demo-change", "a1", "--result-json", '{"ok": true}'])

        args = parser.parse_args(["plan", "complete", "demo-change", "a1", "--output-json", '{"ok": true}'])
        self.assertEqual(args.output_json, '{"ok": true}')

    def test_change_status_parser_rejects_retry_flag(self):
        parser = build_parser()
        with self.assertRaises(SystemExit):
            parser.parse_args(["change", "status", "demo-change", "--retry"])

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
