import json
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from types import SimpleNamespace

from superspec.cli import command_plan_init, command_validate
from superspec.engine.errors import ProtocolError
from superspec.engine.orchestrator import run_protocol_action_from_cli


class PlanLifecycleTest(unittest.TestCase):
    def _repo_root(self) -> Path:
        for parent in Path(__file__).resolve().parents:
            if (parent / "pyproject.toml").exists():
                return parent
        raise RuntimeError("Could not locate repository root from test path")

    def _seed_generation_assets(self, root: Path):
        repo_root = self._repo_root()

        base_template_src = repo_root / "src" / "superspec" / "schemas" / "templates" / "plan.base.json"
        base_template_dst = root / "superspec" / "schemas" / "templates" / "plan.base.json"
        base_template_dst.parent.mkdir(parents=True, exist_ok=True)
        base_template_dst.write_text(base_template_src.read_text(encoding="utf-8"), encoding="utf-8")

        workflow_src = repo_root / "src" / "superspec" / "schemas" / "workflows" / "SDD.workflow.json"
        workflow_dst = root / "superspec" / "schemas" / "workflows" / "SDD.workflow.json"
        workflow_dst.parent.mkdir(parents=True, exist_ok=True)
        workflow_dst.write_text(workflow_src.read_text(encoding="utf-8"), encoding="utf-8")

        schema_src = repo_root / "src" / "superspec" / "schemas" / "workflow.schema.json"
        schema_dst = root / "superspec" / "schemas" / "workflow.schema.json"
        schema_dst.parent.mkdir(parents=True, exist_ok=True)
        schema_dst.write_text(schema_src.read_text(encoding="utf-8"), encoding="utf-8")

    def test_plan_init_with_default_schema_writes_plan_file(self):
        root = Path(tempfile.mkdtemp(prefix="superspec-"))
        self._seed_generation_assets(root)
        args = SimpleNamespace(change="demo-change", schema="SDD", title=None, goal=None)

        command_plan_init(root, args)

        plan_path = root / "openspec" / "changes" / "demo-change" / "plan.json"
        self.assertTrue(plan_path.exists())
        plan = json.loads(plan_path.read_text(encoding="utf-8"))
        self.assertEqual(plan["context"]["changeName"], "demo-change")
        self.assertEqual(plan["metadata"]["workflow"]["id"], "SDD")

    def test_plan_init_falls_back_to_packaged_default_workflow(self):
        root = Path(tempfile.mkdtemp(prefix="superspec-"))
        # No local superspec/schemas/workflows assets are created.
        args = SimpleNamespace(change="demo-change", schema="SDD", title=None, goal=None)

        command_plan_init(root, args)

        plan_path = root / "openspec" / "changes" / "demo-change" / "plan.json"
        self.assertTrue(plan_path.exists())
        plan = json.loads(plan_path.read_text(encoding="utf-8"))
        self.assertEqual(plan["metadata"]["workflow"]["id"], "SDD")

    def test_plan_init_ignores_local_plan_base_template(self):
        root = Path(tempfile.mkdtemp(prefix="superspec-"))
        self._seed_generation_assets(root)
        # If local base template were used, init would fail validation.
        local_base = root / "superspec" / "schemas" / "templates" / "plan.base.json"
        local_base.write_text(json.dumps({"schemaVersion": "broken"}, indent=2), encoding="utf-8")

        args = SimpleNamespace(change="demo-change", schema="SDD", title=None, goal=None)
        command_plan_init(root, args)

        plan_path = root / "openspec" / "changes" / "demo-change" / "plan.json"
        plan = json.loads(plan_path.read_text(encoding="utf-8"))
        self.assertEqual(plan["schemaVersion"], "superspec.plan/v1.0.0")

    def test_plan_init_supports_explicit_schema_selection(self):
        root = Path(tempfile.mkdtemp(prefix="superspec-"))
        self._seed_generation_assets(root)

        custom = {
            "workflowId": "custom-flow",
            "version": "1.0.0",
            "title": "Custom title from workflow",
            "goal": "Custom goal from workflow",
            "actions": [
                {
                    "id": "x1",
                    "type": "openspec.apply",
                    "executor": "skill",
                    "skill": "openspec-apply-change",
                }
            ],
        }
        custom_path = root / "superspec" / "schemas" / "workflows" / "custom-flow.workflow.json"
        custom_path.write_text(json.dumps(custom, indent=2), encoding="utf-8")

        args = SimpleNamespace(change="demo-change", schema="custom-flow", title=None, goal=None)
        command_plan_init(root, args)

        plan_path = root / "openspec" / "changes" / "demo-change" / "plan.json"
        plan = json.loads(plan_path.read_text(encoding="utf-8"))
        self.assertEqual(plan["title"], "Custom title from workflow")
        self.assertEqual(plan["goal"], "Custom goal from workflow")
        self.assertEqual(plan["context"]["changeName"], "demo-change")
        self.assertEqual(plan["context"]["changeDir"], "openspec/changes/demo-change")

    def test_plan_init_rejects_legacy_plan_overlay_field(self):
        root = Path(tempfile.mkdtemp(prefix="superspec-"))
        self._seed_generation_assets(root)

        custom = {
            "workflowId": "legacy-plan",
            "version": "1.0.0",
            "actions": [
                {
                    "id": "x1",
                    "type": "openspec.apply",
                    "executor": "skill",
                    "skill": "openspec-apply-change",
                }
            ],
            "plan": {
                "context": {
                    "changeName": "bad",
                    "changeDir": "bad/path",
                }
            },
        }
        custom_path = root / "superspec" / "schemas" / "workflows" / "legacy-plan.workflow.json"
        custom_path.write_text(json.dumps(custom, indent=2), encoding="utf-8")

        args = SimpleNamespace(change="demo-change", schema="legacy-plan", title=None, goal=None)
        with self.assertRaises(ProtocolError) as ctx:
            command_plan_init(root, args)

        self.assertEqual(ctx.exception.code, "invalid_plan_schema")
        self.assertEqual(ctx.exception.details["location"], "plan")

    def test_plan_init_rejects_unknown_top_level_workflow_field(self):
        root = Path(tempfile.mkdtemp(prefix="superspec-"))
        self._seed_generation_assets(root)

        custom = {
            "workflowId": "unknown-field",
            "version": "1.0.0",
            "actions": [
                {
                    "id": "x1",
                    "type": "openspec.apply",
                    "executor": "skill",
                    "skill": "openspec-apply-change",
                }
            ],
            "context": {
                "changeName": "bad",
            },
        }
        custom_path = root / "superspec" / "schemas" / "workflows" / "unknown-field.workflow.json"
        custom_path.write_text(json.dumps(custom, indent=2), encoding="utf-8")

        args = SimpleNamespace(change="demo-change", schema="unknown-field", title=None, goal=None)
        with self.assertRaises(ProtocolError) as ctx:
            command_plan_init(root, args)

        self.assertEqual(ctx.exception.code, "invalid_plan_schema")
        self.assertEqual(ctx.exception.details["location"], "context")

    def test_plan_init_uses_workflow_defaults_without_cli_inputs(self):
        root = Path(tempfile.mkdtemp(prefix="superspec-"))
        self._seed_generation_assets(root)
        args = SimpleNamespace(
            change="demo-change",
            schema=None,
        )

        command_plan_init(root, args)

        plan_path = root / "openspec" / "changes" / "demo-change" / "plan.json"
        plan = json.loads(plan_path.read_text(encoding="utf-8"))
        self.assertEqual(plan["title"], "Main delivery plan")
        self.assertEqual(plan["goal"], "Execute this change in a single-agent serial loop")

    def test_plan_init_uses_workflow_title_and_goal(self):
        root = Path(tempfile.mkdtemp(prefix="superspec-"))
        self._seed_generation_assets(root)

        custom = {
            "workflowId": "with-customization",
            "version": "1.0.0",
            "title": "Workflow title",
            "goal": "Workflow goal",
            "variables": {
                "channel": "test",
            },
            "actions": [
                {
                    "id": "x1",
                    "type": "openspec.apply",
                    "executor": "skill",
                    "skill": "openspec-apply-change",
                }
            ],
        }
        custom_path = root / "superspec" / "schemas" / "workflows" / "with-customization.workflow.json"
        custom_path.write_text(json.dumps(custom, indent=2), encoding="utf-8")

        args = SimpleNamespace(
            change="demo-change",
            schema="with-customization",
        )
        command_plan_init(root, args)

        plan_path = root / "openspec" / "changes" / "demo-change" / "plan.json"
        plan = json.loads(plan_path.read_text(encoding="utf-8"))
        self.assertEqual(plan["title"], "Workflow title")
        self.assertEqual(plan["goal"], "Workflow goal")
        self.assertEqual(plan["variables"]["channel"], "test")

    def test_plan_init_rejects_unknown_schema(self):
        root = Path(tempfile.mkdtemp(prefix="superspec-"))
        self._seed_generation_assets(root)
        args = SimpleNamespace(change="demo-change", schema="missing", title=None, goal=None)

        with self.assertRaises(ProtocolError) as ctx:
            command_plan_init(root, args)

        self.assertEqual(ctx.exception.code, "invalid_plan_schema")

    def test_plan_init_rejects_invalid_workflow_document(self):
        root = Path(tempfile.mkdtemp(prefix="superspec-"))
        self._seed_generation_assets(root)

        invalid_path = root / "superspec" / "schemas" / "workflows" / "broken.workflow.json"
        invalid_path.write_text(
            json.dumps(
                {
                    "workflowId": "broken",
                    # Missing required version and actions.
                },
                indent=2,
            ),
            encoding="utf-8",
        )
        args = SimpleNamespace(change="demo-change", schema="broken", title=None, goal=None)

        with self.assertRaises(ProtocolError) as ctx:
            command_plan_init(root, args)

        self.assertEqual(ctx.exception.code, "invalid_plan_schema")

    def test_protocol_actions_require_explicit_plan_init(self):
        root = Path(tempfile.mkdtemp(prefix="superspec-"))
        change_dir = root / "openspec" / "changes" / "demo-change"
        change_dir.mkdir(parents=True, exist_ok=True)

        with self.assertRaises(FileNotFoundError):
            run_protocol_action_from_cli(root, "demo-change", "next", owner="agent", debug=False)

    def test_protocol_actions_reject_invalid_plan_json(self):
        root = Path(tempfile.mkdtemp(prefix="superspec-"))
        change_dir = root / "openspec" / "changes" / "demo-change"
        change_dir.mkdir(parents=True, exist_ok=True)
        plan_path = change_dir / "plan.json"
        plan_path.write_text("{invalid", encoding="utf-8")

        with self.assertRaises(ProtocolError) as ctx:
            run_protocol_action_from_cli(root, "demo-change", "status", debug=False)

        self.assertEqual(ctx.exception.code, "invalid_json")
        self.assertEqual(ctx.exception.details["path"], str(plan_path))

    def test_plan_init_rejects_invalid_change_name(self):
        root = Path(tempfile.mkdtemp(prefix="superspec-"))
        self._seed_generation_assets(root)
        args = SimpleNamespace(change="../escape", schema="SDD", title=None, goal=None)

        with self.assertRaises(ProtocolError) as ctx:
            command_plan_init(root, args)

        self.assertEqual(ctx.exception.code, "invalid_change_name")

    def test_protocol_actions_reject_context_changedir_outside_changes_root(self):
        root = Path(tempfile.mkdtemp(prefix="superspec-"))
        self._seed_generation_assets(root)
        init_args = SimpleNamespace(change="demo-change", schema="SDD", title=None, goal=None)
        command_plan_init(root, init_args)

        plan_path = root / "openspec" / "changes" / "demo-change" / "plan.json"
        plan = json.loads(plan_path.read_text(encoding="utf-8"))
        plan["context"]["changeDir"] = "../../../tmp/outside"
        plan_path.write_text(json.dumps(plan, indent=2), encoding="utf-8")

        with self.assertRaises(ProtocolError) as ctx:
            run_protocol_action_from_cli(root, "demo-change", "status", debug=False)

        self.assertEqual(ctx.exception.code, "invalid_path")

    def test_protocol_actions_reject_context_changedir_mismatch_with_target_change(self):
        root = Path(tempfile.mkdtemp(prefix="superspec-"))
        self._seed_generation_assets(root)
        init_args = SimpleNamespace(change="demo-change", schema="SDD", title=None, goal=None)
        command_plan_init(root, init_args)

        other_change_dir = root / "openspec" / "changes" / "other-change"
        other_change_dir.mkdir(parents=True, exist_ok=True)

        plan_path = root / "openspec" / "changes" / "demo-change" / "plan.json"
        plan = json.loads(plan_path.read_text(encoding="utf-8"))
        plan["context"]["changeDir"] = "openspec/changes/other-change"
        plan_path.write_text(json.dumps(plan, indent=2), encoding="utf-8")

        with self.assertRaises(ProtocolError) as ctx:
            run_protocol_action_from_cli(root, "demo-change", "status", debug=False)

        self.assertEqual(ctx.exception.code, "invalid_path")
        self.assertFalse((other_change_dir / "execution" / "state.json").exists())

    def test_custom_workflow_generated_plan_can_run_protocol_after_validate(self):
        root = Path(tempfile.mkdtemp(prefix="superspec-"))
        self._seed_generation_assets(root)

        custom = {
            "workflowId": "quick-apply",
            "version": "1.0.0",
            "actions": [
                {
                    "id": "x1",
                    "type": "openspec.apply",
                    "executor": "skill",
                    "skill": "openspec-apply-change",
                }
            ],
        }
        custom_path = root / "superspec" / "schemas" / "workflows" / "quick-apply.workflow.json"
        custom_path.write_text(json.dumps(custom, indent=2), encoding="utf-8")

        command_validate(root, SimpleNamespace(schema="quick-apply", file=None, json=False))

        init_args = SimpleNamespace(change="demo-change", schema="quick-apply", title=None, goal=None)
        command_plan_init(root, init_args)

        nxt = run_protocol_action_from_cli(root, "demo-change", "next", owner="agent", debug=False)
        self.assertEqual(nxt["state"], "ready")
        self.assertEqual(nxt["action"]["actionId"], "x1")

    def test_validate_supports_explicit_file_input(self):
        root = Path(tempfile.mkdtemp(prefix="superspec-"))
        self._seed_generation_assets(root)

        workflow = {
            "workflowId": "by-file",
            "version": "1.0.0",
            "actions": [
                {
                    "id": "x1",
                    "type": "openspec.apply",
                    "executor": "skill",
                    "skill": "openspec-apply-change",
                }
            ],
        }
        workflow_path = root / "custom.workflow.json"
        workflow_path.write_text(json.dumps(workflow, indent=2), encoding="utf-8")

        command_validate(root, SimpleNamespace(schema=None, file=str(workflow_path), json=False))

    def test_validate_rejects_invalid_source_selection(self):
        root = Path(tempfile.mkdtemp(prefix="superspec-"))
        self._seed_generation_assets(root)

        with self.assertRaises(SystemExit):
            command_validate(root, SimpleNamespace(schema=None, file=None, json=False))
        with self.assertRaises(SystemExit):
            command_validate(root, SimpleNamespace(schema="SDD", file="custom.workflow.json", json=False))

    def test_validate_json_output_has_error_shape(self):
        root = Path(tempfile.mkdtemp(prefix="superspec-"))
        self._seed_generation_assets(root)

        broken = {
            "workflowId": "broken",
            "version": "1.0.0",
            "actions": [
                {
                    "id": "x1",
                    "type": "openspec.apply",
                    "executor": "skill",
                    "dependsOn": ["missing"],
                }
            ],
        }
        broken_path = root / "superspec" / "schemas" / "workflows" / "broken.workflow.json"
        broken_path.write_text(json.dumps(broken, indent=2), encoding="utf-8")

        stdout = StringIO()
        with self.assertRaises(SystemExit):
            with redirect_stdout(stdout):
                command_validate(root, SimpleNamespace(schema="broken", file=None, json=True))
        payload = json.loads(stdout.getvalue())
        self.assertFalse(payload["ok"])
        self.assertIn("errors", payload)
        self.assertIn("code", payload["errors"][0])
        self.assertIn("path", payload["errors"][0])
        self.assertIn("message", payload["errors"][0])

    def test_validate_rejects_unsupported_defaults_field(self):
        root = Path(tempfile.mkdtemp(prefix="superspec-"))
        self._seed_generation_assets(root)

        broken = {
            "workflowId": "broken-defaults",
            "version": "1.0.0",
            "defaults": {
                "executor": "skill",
                "unknown": True,
            },
            "actions": [
                {
                    "id": "x1",
                    "type": "openspec.apply",
                }
            ],
        }
        broken_path = root / "superspec" / "schemas" / "workflows" / "broken-defaults.workflow.json"
        broken_path.write_text(json.dumps(broken, indent=2), encoding="utf-8")

        with self.assertRaises(SystemExit):
            command_validate(root, SimpleNamespace(schema="broken-defaults", file=None, json=False))

    def test_validate_rejects_executor_payload_mismatch(self):
        root = Path(tempfile.mkdtemp(prefix="superspec-"))
        self._seed_generation_assets(root)

        broken = {
            "workflowId": "executor-mismatch",
            "version": "1.0.0",
            "actions": [
                {
                    "id": "x1",
                    "type": "run",
                    "executor": "script",
                }
            ],
        }
        broken_path = root / "superspec" / "schemas" / "workflows" / "executor-mismatch.workflow.json"
        broken_path.write_text(json.dumps(broken, indent=2), encoding="utf-8")

        with self.assertRaises(SystemExit):
            command_validate(root, SimpleNamespace(schema="executor-mismatch", file=None, json=False))

    def test_validate_rejects_missing_explicit_executor(self):
        root = Path(tempfile.mkdtemp(prefix="superspec-"))
        self._seed_generation_assets(root)

        broken = {
            "workflowId": "missing-explicit-executor",
            "version": "1.0.0",
            "actions": [
                {
                    "id": "x1",
                    "type": "run",
                    "skill": "openspec-apply-change",
                }
            ],
        }
        broken_path = root / "superspec" / "schemas" / "workflows" / "missing-explicit-executor.workflow.json"
        broken_path.write_text(json.dumps(broken, indent=2), encoding="utf-8")

        stdout = StringIO()
        with self.assertRaises(SystemExit):
            with redirect_stdout(stdout):
                command_validate(root, SimpleNamespace(schema="missing-explicit-executor", file=None, json=True))
        payload = json.loads(stdout.getvalue())
        self.assertEqual(payload["errors"][0]["code"], "missing_required_field")
        self.assertEqual(payload["errors"][0]["path"], "actions.0.executor")

    def test_validate_rejects_mixed_executor_payloads(self):
        root = Path(tempfile.mkdtemp(prefix="superspec-"))
        self._seed_generation_assets(root)

        broken = {
            "workflowId": "mixed-executor-payloads",
            "version": "1.0.0",
            "actions": [
                {
                    "id": "x1",
                    "type": "run",
                    "executor": "skill",
                    "skill": "openspec-apply-change",
                    "script": "echo hi",
                }
            ],
        }
        broken_path = root / "superspec" / "schemas" / "workflows" / "mixed-executor-payloads.workflow.json"
        broken_path.write_text(json.dumps(broken, indent=2), encoding="utf-8")

        stdout = StringIO()
        with self.assertRaises(SystemExit):
            with redirect_stdout(stdout):
                command_validate(root, SimpleNamespace(schema="mixed-executor-payloads", file=None, json=True))
        payload = json.loads(stdout.getvalue())
        self.assertEqual(payload["errors"][0]["code"], "invalid_executor_payload")
        self.assertEqual(payload["errors"][0]["path"], "actions.0")

    def test_validate_accepts_human_executor_payload(self):
        root = Path(tempfile.mkdtemp(prefix="superspec-"))
        self._seed_generation_assets(root)

        workflow = {
            "workflowId": "human-exec",
            "version": "1.0.0",
            "actions": [
                {
                    "id": "x1",
                    "type": "human.review",
                    "executor": "human",
                    "human": {"instruction": "Review and approve"},
                }
            ],
        }
        workflow_path = root / "superspec" / "schemas" / "workflows" / "human-exec.workflow.json"
        workflow_path.write_text(json.dumps(workflow, indent=2), encoding="utf-8")

        command_validate(root, SimpleNamespace(schema="human-exec", file=None, json=False))

    def test_validate_rejects_human_executor_payload_mismatch(self):
        root = Path(tempfile.mkdtemp(prefix="superspec-"))
        self._seed_generation_assets(root)

        workflow = {
            "workflowId": "human-mismatch",
            "version": "1.0.0",
            "actions": [
                {
                    "id": "x1",
                    "type": "human.review",
                    "executor": "human",
                }
            ],
        }
        workflow_path = root / "superspec" / "schemas" / "workflows" / "human-mismatch.workflow.json"
        workflow_path.write_text(json.dumps(workflow, indent=2), encoding="utf-8")

        with self.assertRaises(SystemExit):
            command_validate(root, SimpleNamespace(schema="human-mismatch", file=None, json=False))


if __name__ == "__main__":
    unittest.main()
