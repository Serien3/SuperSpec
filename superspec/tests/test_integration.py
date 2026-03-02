import tempfile
import unittest
from pathlib import Path

from superspec.engine.errors import ProtocolError
from superspec.engine.protocol import complete_action, fail_action, next_action, status_snapshot
from superspec.engine.validator import validate_plan


class IntegrationTest(unittest.TestCase):
    def setup_temp_change(self):
        root = Path(tempfile.mkdtemp(prefix="superspec-"))
        change_name = "demo-change"
        change_dir = root / "openspec" / "changes" / change_name
        change_dir.mkdir(parents=True, exist_ok=True)
        return root, change_name, change_dir

    def build_plan(self, root: Path, change_name: str, actions):
        return {
            "schemaVersion": "superspec.plan/v0.3",
            "planId": "main",
            "title": "Integration Plan",
            "goal": "Test plan execution",
            "context": {
                "changeName": change_name,
                "changeDir": f"openspec/changes/{change_name}",
                "repoRoot": str(root),
                "specRoot": "openspec",
            },
            "defaults": {
                "executor": "script",
                "timeoutSec": 5,
                "onFail": "stop",
                "retry": {
                    "maxAttempts": 1,
                    "backoffSec": 0,
                    "strategy": "fixed",
                },
            },
            "actions": actions,
        }

    def test_pull_loop_next_complete_until_done(self):
        root, change_name, change_dir = self.setup_temp_change()
        plan = self.build_plan(
            root,
            change_name,
            [
                {"id": "a1", "type": "openspec.proposal", "executor": "script", "script": "echo one"},
                {"id": "a2", "type": "openspec.specs", "dependsOn": ["a1"], "executor": "skill", "skill": "openspec-continue-change", "inputs": {"prompt": "draft specs"}},
                {"id": "a3", "type": "openspec.design", "dependsOn": ["a2"], "executor": "script", "script": "echo three"},
            ],
        )
        validate_plan(plan)

        completed = 0
        while True:
            nxt = next_action(plan, str(change_dir), owner="tester")
            if nxt["state"] == "done":
                break
            self.assertEqual(nxt["state"], "ready")
            action_id = nxt["action"]["actionId"]
            complete_action(plan, str(change_dir), action_id, {"ok": True, "actionId": action_id})
            completed += 1

        self.assertEqual(completed, 3)
        status = status_snapshot(plan, str(change_dir))
        self.assertEqual(status["status"], "success")
        self.assertEqual(status["progress"]["done"], 3)

    def test_complete_requires_running_action(self):
        root, change_name, change_dir = self.setup_temp_change()
        plan = self.build_plan(
            root,
            change_name,
            [{"id": "a1", "type": "openspec.proposal", "executor": "script", "script": "echo one"}],
        )
        validate_plan(plan)

        with self.assertRaises(ProtocolError) as ctx:
            complete_action(plan, str(change_dir), "a1", {"ok": True})

        self.assertEqual(ctx.exception.code, "invalid_state")

    def test_execution_storage_files_are_created(self):
        root, change_name, change_dir = self.setup_temp_change()
        plan = self.build_plan(
            root,
            change_name,
            [{"id": "a1", "type": "openspec.proposal", "executor": "script", "script": "echo one"}],
        )
        validate_plan(plan)

        nxt = next_action(plan, str(change_dir), owner="agent")
        complete_action(plan, str(change_dir), "a1", {"ok": True})
        _ = status_snapshot(plan, str(change_dir))

        self.assertEqual(nxt["state"], "ready")
        self.assertTrue((change_dir / "execution" / "state.json").exists())
        self.assertTrue((change_dir / "execution" / "events.log").exists())
        self.assertFalse((change_dir / "execution" / "leases.json").exists())

    def test_blocked_polling_preserves_running_action(self):
        root, change_name, change_dir = self.setup_temp_change()
        plan = self.build_plan(
            root,
            change_name,
            [
                {"id": "a1", "type": "openspec.proposal", "executor": "script", "script": "echo one"},
                {"id": "a2", "type": "openspec.specs", "dependsOn": ["a1"], "executor": "script", "script": "echo two"},
            ],
        )
        validate_plan(plan)

        first = next_action(plan, str(change_dir), owner="agent-a")
        self.assertEqual(first["state"], "ready")
        self.assertEqual(first["action"]["actionId"], "a1")

        blocked = next_action(plan, str(change_dir), owner="agent-a")
        self.assertEqual(blocked["state"], "blocked")

        status = status_snapshot(plan, str(change_dir))
        a1 = next(action for action in status["actions"] if action["id"] == "a1")
        self.assertEqual(a1["status"], "RUNNING")

        complete_action(plan, str(change_dir), "a1", {"ok": True})
        nxt = next_action(plan, str(change_dir), owner="agent-a")
        self.assertEqual(nxt["state"], "ready")
        self.assertEqual(nxt["action"]["actionId"], "a2")

    def test_fail_retry_without_leases(self):
        root, change_name, change_dir = self.setup_temp_change()
        plan = self.build_plan(
            root,
            change_name,
            [
                {
                    "id": "a1",
                    "type": "openspec.proposal",
                    "executor": "script",
                    "script": "echo one",
                    "retry": {"maxAttempts": 2, "backoffSec": 0, "strategy": "fixed"},
                }
            ],
        )
        validate_plan(plan)

        _ = next_action(plan, str(change_dir), owner="agent-a")
        status_after_first_fail = fail_action(plan, str(change_dir), "a1", {"code": "boom", "message": "fail once"})
        a1 = next(action for action in status_after_first_fail["actions"] if action["id"] == "a1")
        self.assertEqual(a1["status"], "PENDING")

        nxt = next_action(plan, str(change_dir), owner="agent-a")
        self.assertEqual(nxt["state"], "ready")
        complete_action(plan, str(change_dir), "a1", {"ok": True})
        terminal = status_snapshot(plan, str(change_dir))
        self.assertEqual(terminal["status"], "success")


if __name__ == "__main__":
    unittest.main()
