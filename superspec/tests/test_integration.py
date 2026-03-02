import tempfile
import time
import unittest
from pathlib import Path

from superspec.engine.errors import ProtocolError
from superspec.engine.protocol import complete_action, next_action, status_snapshot
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
            "schemaVersion": "superspec.plan/v0.2",
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
            complete_action(plan, str(change_dir), action_id, nxt["leaseId"], {"ok": True, "actionId": action_id})
            completed += 1

        self.assertEqual(completed, 3)
        status = status_snapshot(plan, str(change_dir))
        self.assertEqual(status["status"], "success")
        self.assertEqual(status["progress"]["done"], 3)

    def test_lease_conflict_and_expiry_reclaim(self):
        root, change_name, change_dir = self.setup_temp_change()
        plan = self.build_plan(
            root,
            change_name,
            [{"id": "a1", "type": "openspec.proposal", "executor": "script", "script": "echo one"}],
        )
        validate_plan(plan)

        first = next_action(plan, str(change_dir), owner="agent-a", lease_ttl_sec=1)
        self.assertEqual(first["state"], "ready")

        with self.assertRaises(ProtocolError):
            complete_action(plan, str(change_dir), "a1", "invalid-lease", {"ok": True})

        time.sleep(1.2)
        second = next_action(plan, str(change_dir), owner="agent-b", lease_ttl_sec=10)
        self.assertEqual(second["state"], "ready")
        self.assertNotEqual(first["leaseId"], second["leaseId"])

    def test_execution_storage_files_are_created(self):
        root, change_name, change_dir = self.setup_temp_change()
        plan = self.build_plan(
            root,
            change_name,
            [{"id": "a1", "type": "openspec.proposal", "executor": "script", "script": "echo one"}],
        )
        validate_plan(plan)

        nxt = next_action(plan, str(change_dir), owner="agent")
        complete_action(plan, str(change_dir), "a1", nxt["leaseId"], {"ok": True})
        _ = status_snapshot(plan, str(change_dir))

        self.assertTrue((change_dir / "execution" / "state.json").exists())
        self.assertTrue((change_dir / "execution" / "leases.json").exists())
        self.assertTrue((change_dir / "execution" / "events.log").exists())


if __name__ == "__main__":
    unittest.main()
