import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from superspec.cli import command_init


class CliInitCommandTest(unittest.TestCase):
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
        self.assertTrue((root / ".codex" / "skills" / "superspec-finish-a-change" / "SKILL.md").exists())
        self.assertTrue((root / ".codex" / "agents" / "code-reviewer.toml").exists())
        self.assertTrue((root / ".codex" / "config.toml").exists())

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


if __name__ == "__main__":
    unittest.main()
