import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from superspec.cli import command_init


class CliInitCommandTest(unittest.TestCase):
    def _repo_root(self) -> Path:
        for parent in Path(__file__).resolve().parents:
            if (parent / "pyproject.toml").exists():
                return parent
        raise RuntimeError("Could not locate repository root from test path")

    def test_init_creates_superspec_dirs_and_syncs_packaged_skills_to_codex(self):
        root = Path(tempfile.mkdtemp(prefix="superspec-"))

        args = SimpleNamespace(agent="codex")
        command_init(root, args)
        changes_root = root / "superspec" / "changes"
        archive_dir = changes_root / "archive"
        specs_root = root / "superspec" / "specs"
        self.assertTrue(archive_dir.exists())
        self.assertTrue(specs_root.exists())
        self.assertEqual(sorted(item.name for item in changes_root.iterdir()), ["archive"])
        self.assertEqual(list(archive_dir.iterdir()), [])
        self.assertEqual(list(specs_root.iterdir()), [])
        self.assertEqual((root / "progress.md").read_text(encoding="utf-8"), "# progress\n")
        self.assertEqual((root / ".gitignore").read_text(encoding="utf-8"), "superspec/**/execution/**\n")
        self.assertTrue((root / ".codex" / "skills" / "superspec-finish-a-change" / "SKILL.md").exists())
        self.assertTrue((root / ".codex" / "agents" / "code-reviewer.toml").exists())
        self.assertTrue((root / ".codex" / "config.toml").exists())

    def test_init_reads_codex_agents_and_config_from_codex_bundle(self):
        root = Path(tempfile.mkdtemp(prefix="superspec-"))
        repo_root = self._repo_root()

        args = SimpleNamespace(agent="codex")
        command_init(root, args)

        packaged_agent = repo_root / "src" / "superspec" / "codex" / "agents" / "code-reviewer.toml"
        packaged_config = repo_root / "src" / "superspec" / "codex" / "config.toml"

        self.assertEqual(
            (root / ".codex" / "agents" / "code-reviewer.toml").read_text(encoding="utf-8"),
            packaged_agent.read_text(encoding="utf-8"),
        )
        self.assertEqual(
            (root / ".codex" / "config.toml").read_text(encoding="utf-8"),
            packaged_config.read_text(encoding="utf-8"),
        )

    def test_init_ignores_project_skills_and_uses_packaged_skills(self):
        root = Path(tempfile.mkdtemp(prefix="superspec-"))
        project_skill = root / "skills" / "project-only" / "SKILL.md"
        project_skill.parent.mkdir(parents=True, exist_ok=True)
        project_skill.write_text("# project-only", encoding="utf-8")

        args = SimpleNamespace(agent="codex")
        command_init(root, args)
        self.assertTrue((root / ".codex" / "skills" / "superspec-finish-a-change" / "SKILL.md").exists())
        self.assertFalse((root / ".codex" / "skills" / "project-only" / "SKILL.md").exists())
        self.assertTrue((root / ".codex" / "agents" / "code-reviewer.toml").exists())
        self.assertTrue((root / ".codex" / "config.toml").exists())

    def test_init_requires_available_skills_source(self):
        root = Path(tempfile.mkdtemp(prefix="superspec-"))
        args = SimpleNamespace(agent="codex")
        with patch("superspec.cli._skills_source_dir", side_effect=RuntimeError("missing")):
            with self.assertRaises(RuntimeError):
                command_init(root, args)

    def test_init_preserves_existing_progress_file(self):
        root = Path(tempfile.mkdtemp(prefix="superspec-"))
        progress_path = root / "progress.md"
        progress_path.write_text("# custom progress\nexisting content\n", encoding="utf-8")

        args = SimpleNamespace(agent="codex")
        command_init(root, args)

        self.assertEqual(
            progress_path.read_text(encoding="utf-8"),
            "# custom progress\nexisting content\n",
        )

    def test_init_appends_execution_rule_to_existing_gitignore(self):
        root = Path(tempfile.mkdtemp(prefix="superspec-"))
        gitignore_path = root / ".gitignore"
        gitignore_path.write_text("__pycache__/\n*.pyc\n", encoding="utf-8")

        args = SimpleNamespace(agent="codex")
        command_init(root, args)

        self.assertEqual(
            gitignore_path.read_text(encoding="utf-8"),
            "__pycache__/\n*.pyc\nsuperspec/**/execution/**\n",
        )

    def test_init_does_not_duplicate_execution_rule_in_gitignore(self):
        root = Path(tempfile.mkdtemp(prefix="superspec-"))
        gitignore_path = root / ".gitignore"
        gitignore_path.write_text("__pycache__/\nsuperspec/**/execution/**\n", encoding="utf-8")

        args = SimpleNamespace(agent="codex")
        command_init(root, args)

        self.assertEqual(
            gitignore_path.read_text(encoding="utf-8"),
            "__pycache__/\nsuperspec/**/execution/**\n",
        )


if __name__ == "__main__":
    unittest.main()
