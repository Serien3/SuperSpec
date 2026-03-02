import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from superspec.cli import command_plan_init, command_plan_validate
from superspec.engine.errors import ProtocolError
from superspec.engine.orchestrator import run_protocol_action_from_cli


class PlanLifecycleTest(unittest.TestCase):
    def _seed_generation_assets(self, root: Path):
        repo_root = Path(__file__).resolve().parents[2]

        base_template_src = repo_root / "superspec" / "templates" / "plan.base.json"
        base_template_dst = root / "superspec" / "templates" / "plan.base.json"
        base_template_dst.parent.mkdir(parents=True, exist_ok=True)
        base_template_dst.write_text(base_template_src.read_text(encoding="utf-8"), encoding="utf-8")

        workflow_src = repo_root / "superspec" / "schemas" / "workflows" / "sdd.workflow.json"
        workflow_dst = root / "superspec" / "schemas" / "workflows" / "sdd.workflow.json"
        workflow_dst.parent.mkdir(parents=True, exist_ok=True)
        workflow_dst.write_text(workflow_src.read_text(encoding="utf-8"), encoding="utf-8")

        schema_src = repo_root / "superspec" / "schemas" / "workflow.schema.json"
        schema_dst = root / "superspec" / "schemas" / "workflow.schema.json"
        schema_dst.parent.mkdir(parents=True, exist_ok=True)
        schema_dst.write_text(schema_src.read_text(encoding="utf-8"), encoding="utf-8")

    def test_plan_init_with_default_schema_writes_plan_file(self):
        root = Path(tempfile.mkdtemp(prefix="superspec-"))
        self._seed_generation_assets(root)
        args = SimpleNamespace(change="demo-change", schema="sdd", title=None, goal=None)

        command_plan_init(root, args)

        plan_path = root / "openspec" / "changes" / "demo-change" / "plan.json"
        self.assertTrue(plan_path.exists())
        plan = json.loads(plan_path.read_text(encoding="utf-8"))
        self.assertEqual(plan["context"]["changeName"], "demo-change")
        self.assertEqual(plan["metadata"]["schema"]["id"], "sdd")

    def test_plan_init_falls_back_to_packaged_default_workflow(self):
        root = Path(tempfile.mkdtemp(prefix="superspec-"))
        # No local superspec/schemas/workflows assets are created.
        args = SimpleNamespace(change="demo-change", schema="sdd", title=None, goal=None)

        command_plan_init(root, args)

        plan_path = root / "openspec" / "changes" / "demo-change" / "plan.json"
        self.assertTrue(plan_path.exists())
        plan = json.loads(plan_path.read_text(encoding="utf-8"))
        self.assertEqual(plan["metadata"]["schema"]["id"], "sdd")

    def test_plan_init_ignores_local_plan_base_template(self):
        root = Path(tempfile.mkdtemp(prefix="superspec-"))
        self._seed_generation_assets(root)
        # If local base template were used, init would fail validation.
        local_base = root / "superspec" / "templates" / "plan.base.json"
        local_base.write_text(json.dumps({"schemaVersion": "broken"}, indent=2), encoding="utf-8")

        args = SimpleNamespace(change="demo-change", schema="sdd", title=None, goal=None)
        command_plan_init(root, args)

        plan_path = root / "openspec" / "changes" / "demo-change" / "plan.json"
        plan = json.loads(plan_path.read_text(encoding="utf-8"))
        self.assertEqual(plan["schemaVersion"], "superspec.plan/v0.3")

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

    def test_plan_init_applies_init_time_overrides(self):
        root = Path(tempfile.mkdtemp(prefix="superspec-"))
        self._seed_generation_assets(root)
        args = SimpleNamespace(
            change="demo-change",
            schema=None,
            title="Override title",
            goal="Override goal",
        )

        command_plan_init(root, args)

        plan_path = root / "openspec" / "changes" / "demo-change" / "plan.json"
        plan = json.loads(plan_path.read_text(encoding="utf-8"))
        self.assertEqual(plan["title"], "Override title")
        self.assertEqual(plan["goal"], "Override goal")

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

    def test_plan_init_rejects_invalid_change_name(self):
        root = Path(tempfile.mkdtemp(prefix="superspec-"))
        self._seed_generation_assets(root)
        args = SimpleNamespace(change="../escape", schema="sdd", title=None, goal=None)

        with self.assertRaises(ProtocolError) as ctx:
            command_plan_init(root, args)

        self.assertEqual(ctx.exception.code, "invalid_change_name")

    def test_protocol_actions_reject_context_changedir_outside_changes_root(self):
        root = Path(tempfile.mkdtemp(prefix="superspec-"))
        self._seed_generation_assets(root)
        init_args = SimpleNamespace(change="demo-change", schema="sdd", title=None, goal=None)
        command_plan_init(root, init_args)

        plan_path = root / "openspec" / "changes" / "demo-change" / "plan.json"
        plan = json.loads(plan_path.read_text(encoding="utf-8"))
        plan["context"]["changeDir"] = "../../../tmp/outside"
        plan_path.write_text(json.dumps(plan, indent=2), encoding="utf-8")

        with self.assertRaises(ProtocolError) as ctx:
            run_protocol_action_from_cli(root, "demo-change", "status", debug=False)

        self.assertEqual(ctx.exception.code, "invalid_path")

    def test_custom_workflow_generated_plan_can_validate_and_run_protocol(self):
        root = Path(tempfile.mkdtemp(prefix="superspec-"))
        self._seed_generation_assets(root)

        custom = {
            "workflowId": "quick-apply",
            "version": "1.0.0",
            "actions": [
                {
                    "id": "x1",
                    "type": "openspec.apply",
                    "skill": "openspec-apply-change",
                }
            ],
        }
        custom_path = root / "superspec" / "schemas" / "workflows" / "quick-apply.workflow.json"
        custom_path.write_text(json.dumps(custom, indent=2), encoding="utf-8")

        init_args = SimpleNamespace(change="demo-change", schema="quick-apply", title=None, goal=None)
        command_plan_init(root, init_args)
        command_plan_validate(root, SimpleNamespace(change="demo-change"))

        nxt = run_protocol_action_from_cli(root, "demo-change", "next", owner="agent", debug=False)
        self.assertEqual(nxt["state"], "ready")
        self.assertEqual(nxt["action"]["actionId"], "x1")


if __name__ == "__main__":
    unittest.main()
