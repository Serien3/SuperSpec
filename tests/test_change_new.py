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
    command_change_finish,
    command_change_list,
    command_change_step_complete,
    command_change_step_fail,
)
from superspec.engine.errors import ProtocolError
from superspec.engine.storage.json_files import write_json


class ChangeNewCommandTest(unittest.TestCase):
    def _write_state_snapshot(
        self,
        root: Path,
        change_name: str,
        *,
        started_at: str = "2026-03-18T01:02:03+00:00",
        workflow_id: str = "spec-dev",
        status: str = "success",
    ) -> Path:
        change_dir = root / "superspec" / "changes" / change_name
        execution_dir = change_dir / "execution"
        execution_dir.mkdir(parents=True, exist_ok=True)
        write_json(
            execution_dir / "state.json",
            {
                "meta": {
                    "workflowId": workflow_id,
                    "finishPolicy": "archive" if workflow_id == "spec-dev" else "delete",
                },
                "runtime": {
                    "changeName": change_name,
                    "status": status,
                    "startedAt": started_at,
                    "updatedAt": started_at,
                    "steps": [],
                },
            },
        )
        (execution_dir / "events.log").write_text('{"event":"state.created"}\n', encoding="utf-8")
        (change_dir / "proposal.md").write_text("proposal\n", encoding="utf-8")
        return change_dir

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

        args = parser.parse_args(["change", "advance", "--new", "spec-dev/demo-change", "--json"])
        self.assertEqual(args.new, "spec-dev/demo-change")
        self.assertTrue(args.json)
        self.assertIsNone(args.goal)

        args = parser.parse_args(
            ["change", "advance", "--new", "spec-dev/demo-change", "--goal", "Ship the first draft", "--json"]
        )
        self.assertEqual(args.goal, "Ship the first draft")

    def test_command_change_advance_rejects_mixed_selector_and_change(self):
        root = Path(tempfile.mkdtemp(prefix="superspec-"))
        args = SimpleNamespace(change="demo-change", new="spec-dev/other", goal=None, owner="agent", json=False)

        with self.assertRaises(ProtocolError):
            command_change_advance(root, args)

    def test_command_change_advance_without_args_behaves_like_list(self):
        root = Path(tempfile.mkdtemp(prefix="superspec-"))
        (root / "superspec" / "changes" / "add-test").mkdir(parents=True, exist_ok=True)
        (root / "superspec" / "changes" / "legacy").mkdir(parents=True, exist_ok=True)

        args = SimpleNamespace(change=None, new=None, goal=None, owner="agent", json=False)
        stdout = StringIO()
        with redirect_stdout(stdout):
            command_change_advance(root, args)

        self.assertEqual(stdout.getvalue().splitlines(), ["add-test", "legacy"])

    def test_change_list_parser_form(self):
        parser = build_parser()

        args = parser.parse_args(["change", "list"])
        self.assertEqual(args.group, "change")
        self.assertEqual(args.sub, "list")

    def test_change_finish_parser_form(self):
        parser = build_parser()

        args = parser.parse_args(["change", "finish", "demo-change"])
        self.assertEqual(args.group, "change")
        self.assertEqual(args.sub, "finish")
        self.assertEqual(args.change, "demo-change")
        self.assertFalse(args.force)
        self.assertFalse(args.archive)
        self.assertFalse(args.delete)
        self.assertFalse(args.keep)

        args = parser.parse_args(["change", "finish", "demo-change", "--force", "--delete"])
        self.assertTrue(args.force)
        self.assertTrue(args.delete)

    def test_command_change_list_prints_unarchived_changes_only(self):
        root = Path(tempfile.mkdtemp(prefix="superspec-"))
        changes_root = root / "superspec" / "changes"
        (changes_root / "archive").mkdir(parents=True, exist_ok=True)
        (changes_root / "add-test").mkdir(parents=True, exist_ok=True)
        (changes_root / "legacy").mkdir(parents=True, exist_ok=True)

        stdout = StringIO()
        with redirect_stdout(stdout):
            command_change_list(root, SimpleNamespace())

        self.assertEqual(stdout.getvalue().splitlines(), ["add-test", "legacy"])

    def test_command_change_advance_existing_maps_to_next(self):
        root = Path(tempfile.mkdtemp(prefix="superspec-"))
        args = SimpleNamespace(change="demo", new=None, goal=None, owner="agent", json=True)

        with patch("superspec.cli.run_protocol_action_from_cli") as mock_run:
            mock_run.return_value = {"change": "demo", "goal": "Ship the first draft", "state": "blocked", "step": None}
            stdout = StringIO()
            with redirect_stdout(stdout):
                command_change_advance(root, args)

        mock_run.assert_called_once_with(root, "demo", "next", owner="agent")
        self.assertIn('"change": "demo"', stdout.getvalue())
        self.assertIn('"goal": "Ship the first draft"', stdout.getvalue())
        self.assertIn('"state": "blocked"', stdout.getvalue())

    def test_command_change_advance_new_creates_change_and_bootstraps_state_snapshot(self):
        root = Path(tempfile.mkdtemp(prefix="superspec-"))
        args = SimpleNamespace(
            change=None,
            new="spec-dev/add-test-feature",
            goal="Ship the first draft",
            owner="agent",
            json=True,
        )

        stdout = StringIO()
        with redirect_stdout(stdout):
            command_change_advance(root, args)

        state_path = root / "superspec" / "changes" / "add-test-feature" / "execution" / "state.json"
        self.assertTrue(state_path.exists())
        payload = json.loads(stdout.getvalue())
        self.assertEqual(payload["change"], "add-test-feature")
        self.assertEqual(payload["goal"], "Ship the first draft")
        self.assertIn(payload["state"], {"ready", "blocked", "done"})
        snapshot = json.loads(state_path.read_text(encoding="utf-8"))
        self.assertEqual(snapshot["runtime"]["goal"], "Ship the first draft")

    def test_command_change_advance_new_rejects_blank_goal(self):
        root = Path(tempfile.mkdtemp(prefix="superspec-"))
        args = SimpleNamespace(change=None, new="spec-dev/add-test-feature", goal="   ", owner="agent", json=False)

        with self.assertRaises(ProtocolError) as ctx:
            command_change_advance(root, args)

        self.assertEqual(ctx.exception.code, "invalid_arguments")

    def test_command_change_advance_new_rejects_malformed_selector(self):
        root = Path(tempfile.mkdtemp(prefix="superspec-"))
        args = SimpleNamespace(change=None, new="spec-dev/add/test", goal=None, owner="agent", json=False)

        with self.assertRaises(ProtocolError):
            command_change_advance(root, args)

    def test_command_change_finish_uses_archive_default_and_removes_execution_dir(self):
        root = Path(tempfile.mkdtemp(prefix="superspec-"))
        change_dir = self._write_state_snapshot(root, "demo-change", status="success")
        args = SimpleNamespace(change="demo-change", force=False, archive=False, delete=False, keep=False)

        stdout = StringIO()
        with redirect_stdout(stdout):
            command_change_finish(root, args)

        archived_dir = root / "superspec" / "changes" / "archive" / "2026-03-18-demo-change-spec-dev"
        self.assertFalse(change_dir.exists())
        self.assertTrue(archived_dir.exists())
        self.assertTrue((archived_dir / "proposal.md").exists())
        self.assertFalse((archived_dir / "execution").exists())
        self.assertIn(str(archived_dir), stdout.getvalue())

    def test_command_change_finish_deletes_delete_default_change(self):
        root = Path(tempfile.mkdtemp(prefix="superspec-"))
        change_dir = self._write_state_snapshot(root, "demo-change", workflow_id="bug-fix", status="success")
        args = SimpleNamespace(change="demo-change", force=False, archive=False, delete=False, keep=False)

        stdout = StringIO()
        with redirect_stdout(stdout):
            command_change_finish(root, args)

        self.assertFalse(change_dir.exists())
        self.assertNotIn("archive", stdout.getvalue())
        self.assertIn("deleting", stdout.getvalue())

    def test_command_change_finish_keep_override_leaves_change_in_place(self):
        root = Path(tempfile.mkdtemp(prefix="superspec-"))
        change_dir = self._write_state_snapshot(root, "demo-change", workflow_id="bug-fix", status="success")
        args = SimpleNamespace(change="demo-change", force=False, archive=False, delete=False, keep=True)

        command_change_finish(root, args)

        self.assertTrue(change_dir.exists())
        self.assertTrue((change_dir / "execution").exists())

    def test_command_change_finish_archive_override_archives_delete_default_change(self):
        root = Path(tempfile.mkdtemp(prefix="superspec-"))
        change_dir = self._write_state_snapshot(root, "demo-change", workflow_id="bug-fix", status="success")
        args = SimpleNamespace(change="demo-change", force=False, archive=True, delete=False, keep=False)

        command_change_finish(root, args)

        archived_dir = root / "superspec" / "changes" / "archive" / "2026-03-18-demo-change-bug-fix"
        self.assertFalse(change_dir.exists())
        self.assertTrue(archived_dir.exists())

    def test_command_change_finish_rejects_missing_change(self):
        root = Path(tempfile.mkdtemp(prefix="superspec-"))
        args = SimpleNamespace(change="missing-change", force=False, archive=False, delete=False, keep=False)

        with self.assertRaises(ProtocolError) as ctx:
            command_change_finish(root, args)

        self.assertEqual(ctx.exception.code, "change_not_found")

    def test_command_change_finish_rejects_running_destructive_action_without_force(self):
        root = Path(tempfile.mkdtemp(prefix="superspec-"))
        change_dir = self._write_state_snapshot(root, "demo-change", workflow_id="bug-fix", status="running")
        args = SimpleNamespace(change="demo-change", force=False, archive=False, delete=False, keep=False)

        with self.assertRaises(ProtocolError) as ctx:
            command_change_finish(root, args)

        self.assertEqual(ctx.exception.code, "invalid_state")
        self.assertTrue(change_dir.exists())
        self.assertTrue((change_dir / "execution").exists())

    def test_command_change_finish_force_allows_running_delete(self):
        root = Path(tempfile.mkdtemp(prefix="superspec-"))
        change_dir = self._write_state_snapshot(root, "demo-change", workflow_id="bug-fix", status="running")
        args = SimpleNamespace(change="demo-change", force=True, archive=False, delete=False, keep=False)

        command_change_finish(root, args)

        self.assertFalse(change_dir.exists())

    def test_command_change_finish_allows_keep_for_running_change_without_force(self):
        root = Path(tempfile.mkdtemp(prefix="superspec-"))
        change_dir = self._write_state_snapshot(root, "demo-change", workflow_id="bug-fix", status="running")
        args = SimpleNamespace(change="demo-change", force=False, archive=False, delete=False, keep=True)

        command_change_finish(root, args)

        self.assertTrue(change_dir.exists())

    def test_removed_legacy_parsers_reject_old_commands(self):
        parser = build_parser()
        with self.assertRaises(SystemExit):
            parser.parse_args(["change", "new", "demo-change"])
        with self.assertRaises(SystemExit):
            parser.parse_args(["change", "archive", "demo-change"])
        with self.assertRaises(SystemExit):
            parser.parse_args(["plan", "init", "demo-change", "--schema", "spec-dev"])
        with self.assertRaises(SystemExit):
            parser.parse_args(["plan", "next", "demo-change"])
        with self.assertRaises(SystemExit):
            parser.parse_args(["plan", "approve", "demo-change", "a1"])
        with self.assertRaises(SystemExit):
            parser.parse_args(["plan", "reject", "demo-change", "a1"])

    def test_step_complete_parser_and_plan_complete_removal(self):
        parser = build_parser()

        with self.assertRaises(SystemExit):
            parser.parse_args(["plan", "complete", "demo-change", "a1", "--output-json", '{"ok": true}'])

        args = parser.parse_args(["change", "stepComplete", "demo-change", "a1"])
        self.assertEqual(args.group, "change")
        self.assertEqual(args.sub, "stepComplete")
        self.assertEqual(args.change, "demo-change")
        self.assertEqual(args.step_id, "a1")

    def test_step_fail_parser_and_plan_fail_removal(self):
        parser = build_parser()

        with self.assertRaises(SystemExit):
            parser.parse_args(["plan", "fail", "demo-change", "a1"])

        args = parser.parse_args(["change", "stepFail", "demo-change", "a1"])
        self.assertEqual(args.group, "change")
        self.assertEqual(args.sub, "stepFail")
        self.assertEqual(args.change, "demo-change")
        self.assertEqual(args.step_id, "a1")

    def test_change_status_parser_rejects_retry_flag(self):
        parser = build_parser()
        with self.assertRaises(SystemExit):
            parser.parse_args(["change", "status", "demo-change", "--retry"])

    def test_version_flag_prints_version(self):
        parser = build_parser()
        stdout = StringIO()
        with redirect_stdout(stdout):
            with self.assertRaises(SystemExit) as ctx:
                parser.parse_args(["--version"])

        self.assertEqual(ctx.exception.code, 0)
        self.assertIn("superspec", stdout.getvalue())

    def test_command_change_step_complete_maps_to_complete(self):
        root = Path(tempfile.mkdtemp(prefix="superspec-"))
        args = SimpleNamespace(change="demo-change", step_id="a1")

        with patch("superspec.cli.run_protocol_action_from_cli") as mock_run:
            stdout = StringIO()
            with redirect_stdout(stdout):
                command_change_step_complete(root, args)

        mock_run.assert_called_once_with(
            root,
            "demo-change",
            "complete",
            step_id="a1",
        )
        self.assertIn("Step a1 marked complete.", stdout.getvalue())

    def test_command_change_step_fail_maps_to_fail(self):
        root = Path(tempfile.mkdtemp(prefix="superspec-"))
        args = SimpleNamespace(change="demo-change", step_id="a1")

        with patch("superspec.cli.run_protocol_action_from_cli") as mock_run:
            stdout = StringIO()
            with redirect_stdout(stdout):
                command_change_step_fail(root, args)

        mock_run.assert_called_once_with(
            root,
            "demo-change",
            "fail",
            step_id="a1",
        )
        self.assertIn("Step a1 marked failed.", stdout.getvalue())


if __name__ == "__main__":
    unittest.main()
