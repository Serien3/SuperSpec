import tempfile
import unittest
from pathlib import Path

from superspec.engine.errors import ProtocolError, ValidationError
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

    def test_complete_refreshes_ready_dependents(self):
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

        after_complete = complete_action(plan, str(change_dir), "a1", {"ok": True})
        by_id = {action["id"]: action for action in after_complete["actions"]}
        self.assertEqual(by_id["a2"]["status"], "READY")

    def test_fail_is_terminal_without_retry(self):
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
                }
            ],
        )
        validate_plan(plan)

        _ = next_action(plan, str(change_dir), owner="agent-a")
        status_after_fail = fail_action(plan, str(change_dir), "a1", {"code": "boom", "message": "failed"})
        a1 = next(action for action in status_after_fail["actions"] if action["id"] == "a1")
        self.assertEqual(a1["status"], "FAILED")
        self.assertEqual(status_after_fail["status"], "failed")

        nxt = next_action(plan, str(change_dir), owner="agent-a")
        self.assertEqual(nxt["state"], "done")
        terminal = status_snapshot(plan, str(change_dir))
        self.assertEqual(terminal["status"], "failed")
        self.assertEqual(terminal["progress"]["failed"], 1)

    def test_fail_stops_even_if_independent_actions_exist(self):
        root, change_name, change_dir = self.setup_temp_change()
        plan = self.build_plan(
            root,
            change_name,
            [
                {"id": "a1", "type": "openspec.proposal", "executor": "script", "script": "echo one"},
                {"id": "a2", "type": "openspec.specs", "dependsOn": ["a1"], "executor": "script", "script": "echo two"},
                {"id": "b1", "type": "openspec.tasks", "executor": "script", "script": "echo independent"},
            ],
        )
        validate_plan(plan)

        first = next_action(plan, str(change_dir), owner="agent-a")
        self.assertEqual(first["state"], "ready")
        self.assertEqual(first["action"]["actionId"], "a1")

        after_fail = fail_action(plan, str(change_dir), "a1", {"code": "boom", "message": "root failure"})
        by_id = {action["id"]: action for action in after_fail["actions"]}
        self.assertEqual(by_id["a1"]["status"], "FAILED")
        self.assertEqual(by_id["a2"]["status"], "FAILED")
        self.assertEqual(by_id["a2"]["error"]["code"], "dependency_failed")
        self.assertEqual(after_fail["status"], "failed")

        nxt = next_action(plan, str(change_dir), owner="agent-a")
        self.assertEqual(nxt["state"], "done")

        terminal = status_snapshot(plan, str(change_dir))
        self.assertEqual(terminal["status"], "failed")
        self.assertEqual(terminal["progress"]["done"], 0)
        self.assertEqual(terminal["progress"]["failed"], 2)
        self.assertEqual(terminal["progress"]["remaining"], 1)

    def test_dependency_failure_propagates_and_never_emits_skipped(self):
        root, change_name, change_dir = self.setup_temp_change()
        plan = self.build_plan(
            root,
            change_name,
            [
                {"id": "a1", "type": "openspec.proposal", "executor": "script", "script": "echo one"},
                {"id": "a2", "type": "openspec.specs", "dependsOn": ["a1"], "executor": "script", "script": "echo two"},
                {"id": "a3", "type": "openspec.design", "dependsOn": ["a2"], "executor": "script", "script": "echo three"},
                {"id": "b1", "type": "openspec.tasks", "executor": "script", "script": "echo independent"},
            ],
        )
        validate_plan(plan)

        first = next_action(plan, str(change_dir), owner="agent-a")
        self.assertEqual(first["state"], "ready")
        self.assertEqual(first["action"]["actionId"], "a1")

        after_fail = fail_action(plan, str(change_dir), "a1", {"code": "boom", "message": "root failure"})
        by_id = {action["id"]: action for action in after_fail["actions"]}
        self.assertEqual(by_id["a1"]["status"], "FAILED")
        self.assertEqual(by_id["a2"]["status"], "FAILED")
        self.assertEqual(by_id["a3"]["status"], "FAILED")
        self.assertEqual(by_id["a2"]["error"]["code"], "dependency_failed")
        self.assertEqual(by_id["a3"]["error"]["code"], "dependency_failed")
        self.assertEqual(after_fail["progress"]["done"], 0)
        self.assertEqual(after_fail["progress"]["failed"], 3)
        self.assertEqual(after_fail["progress"]["remaining"], 1)
        self.assertTrue(all(action["status"] != "SKIPPED" for action in after_fail["actions"]))

        nxt = next_action(plan, str(change_dir), owner="agent-a")
        self.assertEqual(nxt["state"], "done")

        terminal = status_snapshot(plan, str(change_dir))
        self.assertEqual(terminal["status"], "failed")
        self.assertEqual(terminal["progress"]["done"], 0)
        self.assertEqual(terminal["progress"]["failed"], 3)
        self.assertEqual(terminal["progress"]["remaining"], 1)
        self.assertTrue(all(action["status"] != "SKIPPED" for action in terminal["actions"]))

    def test_next_infers_executor_from_skill_when_executor_is_missing(self):
        root, change_name, change_dir = self.setup_temp_change()
        plan = self.build_plan(
            root,
            change_name,
            [{"id": "a1", "type": "openspec.proposal", "skill": "openspec-continue-change"}],
        )
        validate_plan(plan)

        nxt = next_action(plan, str(change_dir), owner="agent-a")
        self.assertEqual(nxt["state"], "ready")
        self.assertEqual(nxt["action"]["executor"], "skill")
        self.assertEqual(nxt["action"]["skillName"], "openspec-continue-change")

    def test_validate_rejects_missing_executor_and_no_inferable_payload(self):
        root, change_name, _ = self.setup_temp_change()
        plan = self.build_plan(
            root,
            change_name,
            [{"id": "a1", "type": "openspec.proposal"}],
        )

        with self.assertRaises(ValidationError):
            validate_plan(plan)

    def test_validate_rejects_ambiguous_inferred_executor(self):
        root, change_name, _ = self.setup_temp_change()
        plan = self.build_plan(
            root,
            change_name,
            [
                {
                    "id": "a1",
                    "type": "ambiguous.executor",
                    "skill": "openspec-continue-change",
                    "script": "echo hi",
                }
            ],
        )

        with self.assertRaises(ValidationError):
            validate_plan(plan)

    def test_validate_accepts_custom_action_type_and_protocol_executes(self):
        root, change_name, change_dir = self.setup_temp_change()
        plan = self.build_plan(
            root,
            change_name,
            [{"id": "a1", "type": "custom.anything", "executor": "script", "script": "echo one"}],
        )
        validate_plan(plan)

        nxt = next_action(plan, str(change_dir), owner="agent-a")
        self.assertEqual(nxt["state"], "ready")
        self.assertEqual(nxt["action"]["actionId"], "a1")

    def test_next_reports_invalid_expression_as_protocol_error(self):
        root, change_name, change_dir = self.setup_temp_change()
        plan = self.build_plan(
            root,
            change_name,
            [
                {
                    "id": "a1",
                    "type": "openspec.proposal",
                    "executor": "script",
                    "script": "echo ${variables.missingVar}",
                }
            ],
        )
        validate_plan(plan)

        with self.assertRaises(ProtocolError) as ctx:
            next_action(plan, str(change_dir), owner="agent-a")

        self.assertEqual(ctx.exception.code, "invalid_expression")
        self.assertIn("invalid runtime expression", str(ctx.exception))

    def test_next_ignores_unresolved_expressions_outside_runtime_fields(self):
        root, change_name, change_dir = self.setup_temp_change()
        plan = self.build_plan(
            root,
            change_name,
            [
                {
                    "id": "a1",
                    "type": "custom.unresolved-field",
                    "executor": "script",
                    "script": "echo one",
                    "notes": "${variables.never_defined}",
                }
            ],
        )
        validate_plan(plan)

        nxt = next_action(plan, str(change_dir), owner="agent-a")
        self.assertEqual(nxt["state"], "ready")
        self.assertEqual(nxt["action"]["actionId"], "a1")
        self.assertEqual(nxt["action"]["script_command"], "echo one")

    def test_next_uses_inputs_prompt_as_action_prompt_with_runtime_substitution(self):
        root, change_name, change_dir = self.setup_temp_change()
        plan = self.build_plan(
            root,
            change_name,
            [
                {"id": "a1", "type": "prepare", "executor": "script", "script": "echo one"},
                {
                    "id": "a2",
                    "type": "openspec.specs",
                    "dependsOn": ["a1"],
                    "executor": "skill",
                    "skill": "openspec-continue-change",
                    "inputs": {"prompt": "Write specs for ${context.changeName}; seed=${actions.a1.outputs.summary}"},
                },
            ],
        )
        validate_plan(plan)
        first = next_action(plan, str(change_dir), owner="agent-a")
        self.assertEqual(first["action"]["actionId"], "a1")
        complete_action(plan, str(change_dir), "a1", {"ok": True, "summary": "from-a1"})

        nxt = next_action(plan, str(change_dir), owner="agent-a")
        self.assertEqual(nxt["state"], "ready")
        self.assertEqual(nxt["action"]["prompt"], f"Write specs for {change_name}; seed=from-a1")

    def test_human_executor_blocks_until_completion_and_emits_human_payload(self):
        root, change_name, change_dir = self.setup_temp_change()
        plan = self.build_plan(
            root,
            change_name,
            [
                {
                    "id": "a1",
                    "type": "human.review",
                    "executor": "human",
                    "human": {
                        "instruction": "Review generated code and approve to continue",
                        "approveLabel": "Approve",
                        "rejectLabel": "Reject",
                    },
                },
                {"id": "a2", "type": "openspec.apply", "dependsOn": ["a1"], "executor": "script", "script": "echo go"},
            ],
        )
        validate_plan(plan)

        first = next_action(plan, str(change_dir), owner="agent-a")
        self.assertEqual(first["state"], "ready")
        self.assertEqual(first["action"]["executor"], "human")
        self.assertEqual(first["action"]["actionId"], "a1")
        self.assertEqual(first["action"]["human"]["instruction"], "Review generated code and approve to continue")
        self.assertEqual(first["action"]["human"]["approveLabel"], "Approve")
        self.assertEqual(first["action"]["human"]["rejectLabel"], "Reject")
        self.assertIn("prompt", first["action"])

        blocked = next_action(plan, str(change_dir), owner="agent-a")
        self.assertEqual(blocked["state"], "blocked")

        after_complete = complete_action(plan, str(change_dir), "a1", {"ok": True, "executor": "human", "actionId": "a1"})
        by_id = {action["id"]: action for action in after_complete["actions"]}
        self.assertEqual(by_id["a1"]["status"], "SUCCESS")
        self.assertEqual(by_id["a2"]["status"], "READY")

    def test_validate_rejects_human_executor_without_instruction(self):
        root, change_name, _ = self.setup_temp_change()
        plan = self.build_plan(
            root,
            change_name,
            [
                {
                    "id": "a1",
                    "type": "human.review",
                    "executor": "human",
                    "human": {},
                }
            ],
        )

        with self.assertRaises(ValidationError):
            validate_plan(plan)

    def test_validate_rejects_invalid_explicit_executor_value(self):
        root, change_name, _ = self.setup_temp_change()
        plan = self.build_plan(
            root,
            change_name,
            [
                {
                    "id": "a1",
                    "type": "custom.invalid-executor",
                    "executor": "plugin",
                }
            ],
        )

        with self.assertRaises(ValidationError):
            validate_plan(plan)

    def test_validate_rejects_non_string_explicit_executor(self):
        root, change_name, _ = self.setup_temp_change()
        plan = self.build_plan(
            root,
            change_name,
            [
                {
                    "id": "a1",
                    "type": "custom.invalid-executor-type",
                    "executor": 123,
                }
            ],
        )

        with self.assertRaises(ValidationError):
            validate_plan(plan)

    def test_status_snapshot_compact_mode_summarizes_and_truncates_actions(self):
        root, change_name, change_dir = self.setup_temp_change()
        plan = self.build_plan(
            root,
            change_name,
            [
                {"id": "a1", "type": "openspec.proposal", "executor": "script", "script": "echo one"},
                {"id": "a2", "type": "openspec.specs", "executor": "script", "script": "echo two"},
                {"id": "a3", "type": "openspec.design", "executor": "script", "script": "echo three"},
            ],
        )
        validate_plan(plan)

        compact = status_snapshot(plan, str(change_dir), compact=True, action_limit=2)
        self.assertEqual(len(compact["actions"]), 2)
        self.assertEqual(compact["actionsOmitted"], 1)
        self.assertEqual(set(compact["actions"][0].keys()), {"id", "status"})

        full = status_snapshot(plan, str(change_dir), compact=False)
        self.assertIn("dependsOn", full["actions"][0])
        self.assertIn("startedAt", full["actions"][0])
        self.assertNotIn("actionsOmitted", full)

if __name__ == "__main__":
    unittest.main()
