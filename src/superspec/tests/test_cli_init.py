import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from superspec.cli import command_init


class CliInitCommandTest(unittest.TestCase):
    def test_init_runs_openspec_and_syncs_packaged_skills_to_codex(self):
        root = Path(tempfile.mkdtemp(prefix="superspec-"))

        args = SimpleNamespace(agent="codex")
        with patch("superspec.cli.subprocess.run") as mock_run:
            mock_run.return_value = SimpleNamespace(returncode=0, stdout="ok\n", stderr="")
            command_init(root, args)

        mock_run.assert_called_once_with(
            ["openspec", "init", "--tools", "codex"],
            cwd=root,
            text=True,
            capture_output=True,
        )
        self.assertTrue((root / ".codex" / "skills" / "superspec-run-change-to-done" / "SKILL.md").exists())

    def test_init_ignores_project_skills_and_uses_packaged_skills(self):
        root = Path(tempfile.mkdtemp(prefix="superspec-"))
        project_skill = root / "skills" / "project-only" / "SKILL.md"
        project_skill.parent.mkdir(parents=True, exist_ok=True)
        project_skill.write_text("# project-only", encoding="utf-8")

        args = SimpleNamespace(agent="codex")
        with patch("superspec.cli.subprocess.run") as mock_run:
            mock_run.return_value = SimpleNamespace(returncode=0, stdout="", stderr="")
            command_init(root, args)

        self.assertTrue((root / ".codex" / "skills" / "superspec-run-change-to-done" / "SKILL.md").exists())
        self.assertFalse((root / ".codex" / "skills" / "project-only" / "SKILL.md").exists())

    def test_init_requires_available_skills_source(self):
        root = Path(tempfile.mkdtemp(prefix="superspec-"))
        args = SimpleNamespace(agent="codex")
        with patch("superspec.cli.subprocess.run") as mock_run:
            mock_run.return_value = SimpleNamespace(returncode=0, stdout="", stderr="")
            with patch("superspec.cli._skills_source_dir", side_effect=RuntimeError("missing")):
                with self.assertRaises(RuntimeError):
                    command_init(root, args)


if __name__ == "__main__":
    unittest.main()
