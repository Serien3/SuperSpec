import tempfile
import unittest
from pathlib import Path

from superspec.engine.errors import ProtocolError, ValidationError
from superspec.engine.protocol import complete_step, fail_step, next_step, status_snapshot
from superspec.engine.runtime_validator import validate_runtime_seed


class IntegrationTest(unittest.TestCase):
    def setup_temp_change(self):
        root = Path(tempfile.mkdtemp(prefix="superspec-"))
        change_name = "demo-change"
        change_dir = root / "superspec" / "changes" / change_name
        change_dir.mkdir(parents=True, exist_ok=True)
        return root, change_name, change_dir

    def build_plan(self, root: Path, change_name: str, steps):
        return {
            "title": "Integration Plan",
            "goal": "Test plan execution",
            "context": {
                "changeName": change_name,
                "changeDir": f"superspec/changes/{change_name}",
                "repoRoot": str(root),
                "specRoot": "superspec",
            },
            "steps": steps,
        }

    def test_pull_loop_next_complete_until_done(self):
        root, change_name, change_dir = self.setup_temp_change()
        plan = self.build_plan(
            root,
            change_name,
            [
                {"id": "a1", "description": "openspec.proposal", "executor": "script", "script": "echo one"},
                {"id": "a2", "description": "openspec.specs", "dependsOn": ["a1"], "executor": "skill", "skill": "openspec-continue-change"},
                {"id": "a3", "description": "openspec.design", "dependsOn": ["a2"], "executor": "script", "script": "echo three"},
            ],
        )
        validate_runtime_seed(plan)

        completed = 0
        while True:
            nxt = next_step(plan, str(change_dir), owner="tester")
            if nxt["state"] == "done":
                break
            self.assertEqual(nxt["state"], "ready")
            step_id = nxt["step"]["stepId"]
            complete_step(plan, str(change_dir), step_id)
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
            [{"id": "a1", "description": "openspec.proposal", "executor": "script", "script": "echo one"}],
        )
        validate_runtime_seed(plan)

        with self.assertRaises(ProtocolError) as ctx:
            complete_step(plan, str(change_dir), "a1")

        self.assertEqual(ctx.exception.code, "invalid_state")

    def test_execution_storage_files_are_created(self):
        root, change_name, change_dir = self.setup_temp_change()
        plan = self.build_plan(
            root,
            change_name,
            [{"id": "a1", "description": "openspec.proposal", "executor": "script", "script": "echo one"}],
        )
        validate_runtime_seed(plan)

        nxt = next_step(plan, str(change_dir), owner="agent")
        complete_step(plan, str(change_dir), "a1")
        _ = status_snapshot(plan, str(change_dir))

        self.assertEqual(nxt["state"], "ready")
        self.assertTrue((change_dir / "execution" / "state.json").exists())
        self.assertTrue((change_dir / "execution" / "events.log").exists())
        self.assertFalse((change_dir / "execution" / "leases.json").exists())

    def test_status_rejects_invalid_execution_state_json(self):
        root, change_name, change_dir = self.setup_temp_change()
        plan = self.build_plan(
            root,
            change_name,
            [{"id": "a1", "description": "openspec.proposal", "executor": "script", "script": "echo one"}],
        )
        validate_runtime_seed(plan)

        execution_dir = change_dir / "execution"
        execution_dir.mkdir(parents=True, exist_ok=True)
        state_path = execution_dir / "state.json"
        state_path.write_text("{invalid", encoding="utf-8")

        with self.assertRaises(ProtocolError) as ctx:
            status_snapshot(plan, str(change_dir))

        self.assertEqual(ctx.exception.code, "invalid_json")
        self.assertEqual(ctx.exception.details["path"], str(state_path))

    def test_next_returns_running_action_until_reported(self):
        root, change_name, change_dir = self.setup_temp_change()
        plan = self.build_plan(
            root,
            change_name,
            [
                {"id": "a1", "description": "openspec.proposal", "executor": "script", "script": "echo one"},
                {"id": "a2", "description": "openspec.specs", "dependsOn": ["a1"], "executor": "script", "script": "echo two"},
            ],
        )
        validate_runtime_seed(plan)

        first = next_step(plan, str(change_dir), owner="agent-a")
        self.assertEqual(first["state"], "ready")
        self.assertEqual(first["step"]["stepId"], "a1")

        resumed = next_step(plan, str(change_dir), owner="agent-a")
        self.assertEqual(resumed["state"], "ready")
        self.assertEqual(resumed["step"]["stepId"], "a1")

        status = status_snapshot(plan, str(change_dir))
        a1 = next(step for step in status["steps"] if step["id"] == "a1")
        self.assertEqual(a1["status"], "RUNNING")

        complete_step(plan, str(change_dir), "a1")
        nxt = next_step(plan, str(change_dir), owner="agent-a")
        self.assertEqual(nxt["state"], "ready")
        self.assertEqual(nxt["step"]["stepId"], "a2")

    def test_complete_refreshes_ready_dependents(self):
        root, change_name, change_dir = self.setup_temp_change()
        plan = self.build_plan(
            root,
            change_name,
            [
                {"id": "a1", "description": "openspec.proposal", "executor": "script", "script": "echo one"},
                {"id": "a2", "description": "openspec.specs", "dependsOn": ["a1"], "executor": "script", "script": "echo two"},
            ],
        )
        validate_runtime_seed(plan)

        first = next_step(plan, str(change_dir), owner="agent-a")
        self.assertEqual(first["state"], "ready")
        self.assertEqual(first["step"]["stepId"], "a1")

        after_complete = complete_step(plan, str(change_dir), "a1")
        by_id = {step["id"]: step for step in after_complete["steps"]}
        self.assertEqual(by_id["a2"]["status"], "READY")

    def test_fail_is_terminal_without_retry(self):
        root, change_name, change_dir = self.setup_temp_change()
        plan = self.build_plan(
            root,
            change_name,
            [
                {
                    "id": "a1",
                    "description": "openspec.proposal",
                    "executor": "script",
                    "script": "echo one",
                }
            ],
        )
        validate_runtime_seed(plan)

        _ = next_step(plan, str(change_dir), owner="agent-a")
        status_after_fail = fail_step(plan, str(change_dir), "a1")
        a1 = next(step for step in status_after_fail["steps"] if step["id"] == "a1")
        self.assertEqual(a1["status"], "FAILED")
        self.assertEqual(status_after_fail["status"], "failed")

        nxt = next_step(plan, str(change_dir), owner="agent-a")
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
                {"id": "a1", "description": "openspec.proposal", "executor": "script", "script": "echo one"},
                {"id": "a2", "description": "openspec.specs", "dependsOn": ["a1"], "executor": "script", "script": "echo two"},
                {"id": "b1", "description": "openspec.tasks", "executor": "script", "script": "echo independent"},
            ],
        )
        validate_runtime_seed(plan)

        first = next_step(plan, str(change_dir), owner="agent-a")
        self.assertEqual(first["state"], "ready")
        self.assertEqual(first["step"]["stepId"], "a1")

        after_fail = fail_step(plan, str(change_dir), "a1")
        by_id = {step["id"]: step for step in after_fail["steps"]}
        self.assertEqual(by_id["a1"]["status"], "FAILED")
        self.assertEqual(by_id["a2"]["status"], "FAILED")
        self.assertEqual(by_id["b1"]["status"], "FAILED")
        self.assertNotIn("error", by_id["a2"])
        self.assertEqual(after_fail["status"], "failed")

        nxt = next_step(plan, str(change_dir), owner="agent-a")
        self.assertEqual(nxt["state"], "done")

        terminal = status_snapshot(plan, str(change_dir))
        self.assertEqual(terminal["status"], "failed")
        self.assertEqual(terminal["progress"]["done"], 0)
        self.assertEqual(terminal["progress"]["failed"], 3)
        self.assertEqual(terminal["progress"]["remaining"], 0)

    def test_dependency_failure_propagates_and_never_emits_skipped(self):
        root, change_name, change_dir = self.setup_temp_change()
        plan = self.build_plan(
            root,
            change_name,
            [
                {"id": "a1", "description": "openspec.proposal", "executor": "script", "script": "echo one"},
                {"id": "a2", "description": "openspec.specs", "dependsOn": ["a1"], "executor": "script", "script": "echo two"},
                {"id": "a3", "description": "openspec.design", "dependsOn": ["a2"], "executor": "script", "script": "echo three"},
                {"id": "b1", "description": "openspec.tasks", "executor": "script", "script": "echo independent"},
            ],
        )
        validate_runtime_seed(plan)

        first = next_step(plan, str(change_dir), owner="agent-a")
        self.assertEqual(first["state"], "ready")
        self.assertEqual(first["step"]["stepId"], "a1")

        after_fail = fail_step(plan, str(change_dir), "a1")
        by_id = {step["id"]: step for step in after_fail["steps"]}
        self.assertEqual(by_id["a1"]["status"], "FAILED")
        self.assertEqual(by_id["a2"]["status"], "FAILED")
        self.assertEqual(by_id["a3"]["status"], "FAILED")
        self.assertEqual(by_id["b1"]["status"], "FAILED")
        self.assertNotIn("error", by_id["a2"])
        self.assertNotIn("error", by_id["a3"])
        self.assertEqual(after_fail["progress"]["done"], 0)
        self.assertEqual(after_fail["progress"]["failed"], 4)
        self.assertEqual(after_fail["progress"]["remaining"], 0)
        self.assertTrue(all(step["status"] != "SKIPPED" for step in after_fail["steps"]))

        nxt = next_step(plan, str(change_dir), owner="agent-a")
        self.assertEqual(nxt["state"], "done")

        terminal = status_snapshot(plan, str(change_dir))
        self.assertEqual(terminal["status"], "failed")
        self.assertEqual(terminal["progress"]["done"], 0)
        self.assertEqual(terminal["progress"]["failed"], 4)
        self.assertEqual(terminal["progress"]["remaining"], 0)
        self.assertTrue(all(step["status"] != "SKIPPED" for step in terminal["steps"]))

    def test_validate_rejects_missing_explicit_executor_even_with_skill_payload(self):
        root, change_name, change_dir = self.setup_temp_change()
        plan = self.build_plan(
            root,
            change_name,
            [{"id": "a1", "description": "openspec.proposal", "skill": "openspec-continue-change"}],
        )
        with self.assertRaises(ValidationError):
            validate_runtime_seed(plan)

    def test_validate_rejects_missing_executor_and_no_inferable_payload(self):
        root, change_name, _ = self.setup_temp_change()
        plan = self.build_plan(
            root,
            change_name,
            [{"id": "a1", "description": "openspec.proposal"}],
        )

        with self.assertRaises(ValidationError):
            validate_runtime_seed(plan)

    def test_validate_rejects_mixed_executor_payloads(self):
        root, change_name, _ = self.setup_temp_change()
        plan = self.build_plan(
            root,
            change_name,
            [
                {
                    "id": "a1",
                    "description": "mixed.payloads",
                    "executor": "skill",
                    "skill": "openspec-continue-change",
                    "script": "echo hi",
                }
            ],
        )

        with self.assertRaises(ValidationError):
            validate_runtime_seed(plan)

    def test_validate_accepts_custom_action_type_and_protocol_executes(self):
        root, change_name, change_dir = self.setup_temp_change()
        plan = self.build_plan(
            root,
            change_name,
            [{"id": "a1", "description": "custom.anything", "executor": "script", "script": "echo one"}],
        )
        validate_runtime_seed(plan)

        nxt = next_step(plan, str(change_dir), owner="agent-a")
        self.assertEqual(nxt["state"], "ready")
        self.assertEqual(nxt["step"]["stepId"], "a1")

    def test_next_treats_expression_like_tokens_as_literal_script(self):
        root, change_name, change_dir = self.setup_temp_change()
        plan = self.build_plan(
            root,
            change_name,
            [
                {
                    "id": "a1",
                    "description": "openspec.proposal",
                    "executor": "script",
                    "script": "echo ${variables.missingVar}",
                }
            ],
        )
        validate_runtime_seed(plan)

        nxt = next_step(plan, str(change_dir), owner="agent-a")
        self.assertEqual(nxt["state"], "ready")
        self.assertEqual(nxt["step"]["script_command"], "echo ${variables.missingVar}")

    def test_next_keeps_script_field_literal_without_runtime_resolution(self):
        root, change_name, change_dir = self.setup_temp_change()
        plan = self.build_plan(
            root,
            change_name,
            [
                {
                    "id": "a1",
                    "description": "runtime.script.type.mismatch",
                    "executor": "script",
                    "script": "${variables.command}",
                }
            ],
        )
        plan["variables"] = {"command": {"cmd": "echo hi"}}
        validate_runtime_seed(plan)

        nxt = next_step(plan, str(change_dir), owner="agent-a")
        self.assertEqual(nxt["state"], "ready")
        self.assertEqual(nxt["step"]["script_command"], "${variables.command}")

    def test_next_keeps_human_instruction_literal_without_runtime_resolution(self):
        root, change_name, change_dir = self.setup_temp_change()
        plan = self.build_plan(
            root,
            change_name,
            [
                {
                    "id": "a1",
                    "description": "runtime.human.type.mismatch",
                    "executor": "human",
                    "human": {
                        "instruction": "${variables.instruction}",
                    },
                }
            ],
        )
        plan["variables"] = {"instruction": {"text": "review"}}
        validate_runtime_seed(plan)

        nxt = next_step(plan, str(change_dir), owner="agent-a")
        self.assertEqual(nxt["state"], "ready")
        self.assertEqual(nxt["step"]["human"]["instruction"], "${variables.instruction}")

    def test_next_ignores_unresolved_expressions_outside_runtime_fields(self):
        root, change_name, change_dir = self.setup_temp_change()
        plan = self.build_plan(
            root,
            change_name,
            [
                {
                    "id": "a1",
                    "description": "custom.unresolved-field",
                    "executor": "script",
                    "script": "echo one",
                    "notes": "${variables.never_defined}",
                }
            ],
        )
        validate_runtime_seed(plan)

        nxt = next_step(plan, str(change_dir), owner="agent-a")
        self.assertEqual(nxt["state"], "ready")
        self.assertEqual(nxt["step"]["stepId"], "a1")
        self.assertEqual(nxt["step"]["script_command"], "echo one")

    def test_next_keeps_action_prompt_literal_without_runtime_substitution(self):
        root, change_name, change_dir = self.setup_temp_change()
        plan = self.build_plan(
            root,
            change_name,
            [
                {"id": "a1", "description": "prepare", "executor": "script", "script": "echo one"},
                {
                    "id": "a2",
                    "description": "openspec.specs",
                    "dependsOn": ["a1"],
                    "executor": "skill",
                    "skill": "openspec-continue-change",
                    "prompt": "Write specs for ${context.changeName}; seed=${steps.a1.outputs.summary}",
                },
            ],
        )
        validate_runtime_seed(plan)
        first = next_step(plan, str(change_dir), owner="agent-a")
        self.assertEqual(first["step"]["stepId"], "a1")
        complete_step(plan, str(change_dir), "a1")

        nxt = next_step(plan, str(change_dir), owner="agent-a")
        self.assertEqual(nxt["state"], "ready")
        self.assertEqual(nxt["step"]["prompt"], "Write specs for ${context.changeName}; seed=${steps.a1.outputs.summary}")

    def test_next_keeps_state_expression_literal_in_script_field(self):
        root, change_name, change_dir = self.setup_temp_change()
        plan = self.build_plan(
            root,
            change_name,
            [
                {"id": "a1", "description": "prepare", "executor": "script", "script": "echo one"},
                {
                    "id": "a2",
                    "description": "openspec.apply",
                    "dependsOn": ["a1"],
                    "executor": "script",
                    "script": "echo ${state.commit_by_superspec_last.commit_hash}",
                },
            ],
        )
        validate_runtime_seed(plan)

        first = next_step(plan, str(change_dir), owner="agent-a")
        self.assertEqual(first["state"], "ready")
        self.assertEqual(first["step"]["stepId"], "a1")
        complete_step(plan, str(change_dir), "a1")

        nxt = next_step(plan, str(change_dir), owner="agent-a")
        self.assertEqual(nxt["state"], "ready")
        self.assertEqual(nxt["step"]["script_command"], "echo ${state.commit_by_superspec_last.commit_hash}")

    def test_human_executor_blocks_until_completion_and_emits_human_payload(self):
        root, change_name, change_dir = self.setup_temp_change()
        plan = self.build_plan(
            root,
            change_name,
            [
                {
                    "id": "a1",
                    "description": "human.review",
                    "executor": "human",
                    "human": {
                        "instruction": "Review generated code and approve to continue",
                    },
                },
                {"id": "a2", "description": "openspec.apply", "dependsOn": ["a1"], "executor": "script", "script": "echo go"},
            ],
        )
        validate_runtime_seed(plan)

        first = next_step(plan, str(change_dir), owner="agent-a")
        self.assertEqual(first["state"], "ready")
        self.assertEqual(first["step"]["executor"], "human")
        self.assertEqual(first["step"]["stepId"], "a1")
        self.assertEqual(first["step"]["human"]["instruction"], "Review generated code and approve to continue")
        self.assertIn("prompt", first["step"])

        resumed = next_step(plan, str(change_dir), owner="agent-a")
        self.assertEqual(resumed["state"], "ready")
        self.assertEqual(resumed["step"]["stepId"], "a1")

        after_complete = complete_step(plan, str(change_dir), "a1")
        by_id = {step["id"]: step for step in after_complete["steps"]}
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
                    "description": "human.review",
                    "executor": "human",
                    "human": {},
                }
            ],
        )

        with self.assertRaises(ValidationError):
            validate_runtime_seed(plan)

    def test_validate_rejects_invalid_explicit_executor_value(self):
        root, change_name, _ = self.setup_temp_change()
        plan = self.build_plan(
            root,
            change_name,
            [
                {
                    "id": "a1",
                    "description": "custom.invalid-executor",
                    "executor": "plugin",
                }
            ],
        )

        with self.assertRaises(ValidationError):
            validate_runtime_seed(plan)

    def test_validate_rejects_non_string_explicit_executor(self):
        root, change_name, _ = self.setup_temp_change()
        plan = self.build_plan(
            root,
            change_name,
            [
                {
                    "id": "a1",
                    "description": "custom.invalid-executor-type",
                    "executor": 123,
                }
            ],
        )

        with self.assertRaises(ValidationError):
            validate_runtime_seed(plan)

    def test_status_snapshot_compact_mode_summarizes_and_truncates_actions(self):
        root, change_name, change_dir = self.setup_temp_change()
        plan = self.build_plan(
            root,
            change_name,
            [
                {"id": "a1", "description": "openspec.proposal", "executor": "script", "script": "echo one"},
                {"id": "a2", "description": "openspec.specs", "executor": "script", "script": "echo two"},
                {"id": "a3", "description": "openspec.design", "executor": "script", "script": "echo three"},
            ],
        )
        validate_runtime_seed(plan)

        compact = status_snapshot(plan, str(change_dir), compact=True, step_limit=2)
        self.assertEqual(len(compact["steps"]), 2)
        self.assertEqual(compact["stepsOmitted"], 1)
        self.assertEqual(set(compact["steps"][0].keys()), {"id", "status"})

        full = status_snapshot(plan, str(change_dir), compact=False)
        self.assertIn("dependsOn", full["steps"][0])
        self.assertIn("startedAt", full["steps"][0])
        self.assertNotIn("stepsOmitted", full)

if __name__ == "__main__":
    unittest.main()
