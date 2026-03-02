import tempfile
import unittest
from pathlib import Path

from superspec.engine.orchestrator import run_plan
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
            "schemaVersion": "superspec.plan/v0.1",
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

    def test_full_plan_path_executes_sequentially(self):
        root, change_name, change_dir = self.setup_temp_change()
        actions = [
            {"id": "a1", "type": "openspec.proposal", "executor": "script", "script": "printf proposal > proposal.txt"},
            {"id": "a2", "type": "openspec.specs", "dependsOn": ["a1"], "executor": "script", "script": "printf specs > specs.txt"},
            {"id": "a3", "type": "openspec.design", "dependsOn": ["a2"], "executor": "script", "script": "printf design > design.txt"},
            {"id": "a4", "type": "openspec.tasks", "dependsOn": ["a3"], "executor": "script", "script": "printf tasks > tasks.txt"},
            {"id": "a5", "type": "openspec.apply", "dependsOn": ["a4"], "executor": "script", "script": "printf apply > apply.txt"},
        ]
        plan = self.build_plan(root, change_name, actions)

        validate_plan(plan)
        state = run_plan(plan)

        self.assertEqual(state["status"], "success")
        self.assertEqual(len([a for a in state["actions"] if a["status"] == "SUCCESS"]), 5)

        for file_name in ["proposal.txt", "specs.txt", "design.txt", "tasks.txt", "apply.txt"]:
            self.assertTrue((root / file_name).exists())

        self.assertTrue((change_dir / "run-state.json").exists())

    def test_resume_continues_after_failed_action(self):
        root, change_name, _ = self.setup_temp_change()

        first_plan = self.build_plan(
            root,
            change_name,
            [
                {"id": "a1", "type": "openspec.proposal", "executor": "script", "script": "printf done > a1.txt"},
                {"id": "a2", "type": "openspec.specs", "dependsOn": ["a1"], "executor": "script", "script": "exit 1"},
                {"id": "a3", "type": "openspec.design", "dependsOn": ["a2"], "executor": "script", "script": "printf done > a3.txt"},
            ],
        )

        failed = run_plan(first_plan)
        self.assertEqual(failed["status"], "failed")
        self.assertEqual(next(a for a in failed["actions"] if a["id"] == "a1")["status"], "SUCCESS")
        self.assertEqual(next(a for a in failed["actions"] if a["id"] == "a2")["status"], "FAILED")

        second_plan = self.build_plan(
            root,
            change_name,
            [
                {"id": "a1", "type": "openspec.proposal", "executor": "script", "script": "printf done > a1.txt"},
                {"id": "a2", "type": "openspec.specs", "dependsOn": ["a1"], "executor": "script", "script": "printf recovered > a2.txt"},
                {"id": "a3", "type": "openspec.design", "dependsOn": ["a2"], "executor": "script", "script": "printf done > a3.txt"},
            ],
        )

        resumed = run_plan(second_plan, {"resume": True})
        self.assertEqual(resumed["status"], "success")
        self.assertTrue((root / "a2.txt").exists())
        self.assertTrue((root / "a3.txt").exists())


if __name__ == "__main__":
    unittest.main()
