import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from types import SimpleNamespace

from superspec.cli import build_parser, command_workflow_fork
from superspec.engine.errors import ProtocolError


class WorkflowForkCommandTest(unittest.TestCase):
    def _repo_root(self) -> Path:
        for parent in Path(__file__).resolve().parents:
            if (parent / "pyproject.toml").exists():
                return parent
        raise RuntimeError("Could not locate repository root from test path")

    def test_workflow_fork_parser_form(self):
        parser = build_parser()

        args = parser.parse_args(["workflow", "fork", "spec-dev", "team-spec-dev"])
        self.assertEqual(args.group, "workflow")
        self.assertEqual(args.sub, "fork")
        self.assertEqual(args.source, "spec-dev")
        self.assertEqual(args.target, "team-spec-dev")

    def test_command_workflow_fork_clones_packaged_workflow_to_project(self):
        root = Path(tempfile.mkdtemp(prefix="superspec-"))
        repo_root = self._repo_root()
        packaged = repo_root / "src" / "superspec" / "schemas" / "workflows" / "spec-dev.workflow.json"
        args = SimpleNamespace(source="spec-dev", target="team-spec-dev")

        stdout = StringIO()
        with redirect_stdout(stdout):
            command_workflow_fork(root, args)

        forked = root / "superspec" / "schemas" / "workflows" / "team-spec-dev.workflow.json"
        self.assertTrue(forked.exists())
        self.assertEqual(forked.read_text(encoding="utf-8"), packaged.read_text(encoding="utf-8"))
        self.assertIn(str(forked), stdout.getvalue())

    def test_command_workflow_fork_rejects_existing_target(self):
        root = Path(tempfile.mkdtemp(prefix="superspec-"))
        target = root / "superspec" / "schemas" / "workflows" / "team-spec-dev.workflow.json"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("{}", encoding="utf-8")
        args = SimpleNamespace(source="spec-dev", target="team-spec-dev")

        with self.assertRaises(ProtocolError) as ctx:
            command_workflow_fork(root, args)

        self.assertEqual(ctx.exception.code, "workflow_exists")

    def test_command_workflow_fork_rejects_unknown_builtin_workflow(self):
        root = Path(tempfile.mkdtemp(prefix="superspec-"))
        args = SimpleNamespace(source="missing-workflow", target="team-spec-dev")

        with self.assertRaises(ProtocolError) as ctx:
            command_workflow_fork(root, args)

        self.assertEqual(ctx.exception.code, "invalid_plan_schema")


if __name__ == "__main__":
    unittest.main()
