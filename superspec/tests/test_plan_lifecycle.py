import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from superspec.cli import command_plan_init
from superspec.engine.errors import ProtocolError
from superspec.engine.orchestrator import run_protocol_action_from_cli


class PlanLifecycleTest(unittest.TestCase):
    def _seed_plan_template(self, root: Path):
        src = Path(__file__).resolve().parents[2] / "superspec" / "templates" / "plan.template.json"
        dst = root / "superspec" / "templates" / "plan.template.json"
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_text(src.read_text(encoding="utf-8"), encoding="utf-8")

    def test_plan_init_with_mode_sdd_writes_plan_file(self):
        root = Path(tempfile.mkdtemp(prefix="superspec-"))
        self._seed_plan_template(root)
        args = SimpleNamespace(change="demo-change", mode="sdd")

        command_plan_init(root, args)

        plan_path = root / "openspec" / "changes" / "demo-change" / "plan.json"
        self.assertTrue(plan_path.exists())
        plan = json.loads(plan_path.read_text(encoding="utf-8"))
        self.assertEqual(plan["context"]["changeName"], "demo-change")

    def test_plan_init_rejects_unsupported_mode(self):
        root = Path(tempfile.mkdtemp(prefix="superspec-"))
        self._seed_plan_template(root)
        args = SimpleNamespace(change="demo-change", mode="unknown-mode")

        with self.assertRaises(ProtocolError) as ctx:
            command_plan_init(root, args)

        self.assertEqual(ctx.exception.code, "invalid_plan_mode")

    def test_protocol_actions_require_explicit_plan_init(self):
        root = Path(tempfile.mkdtemp(prefix="superspec-"))
        change_dir = root / "openspec" / "changes" / "demo-change"
        change_dir.mkdir(parents=True, exist_ok=True)

        with self.assertRaises(FileNotFoundError):
            run_protocol_action_from_cli(root, "demo-change", "next", owner="agent", debug=False)


if __name__ == "__main__":
    unittest.main()
