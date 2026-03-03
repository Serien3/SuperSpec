import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from superspec.cli import command_init


class CliInitCommandTest(unittest.TestCase):
    def test_init_runs_openspec_and_syncs_skills_to_codex(self):
        root = Path(tempfile.mkdtemp(prefix="superspec-"))
        skills_dir = root / "skills" / "demo-skill"
        skills_dir.mkdir(parents=True, exist_ok=True)
        (skills_dir / "SKILL.md").write_text("# demo", encoding="utf-8")

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
        self.assertTrue((root / ".codex" / "skills" / "demo-skill" / "SKILL.md").exists())

    def test_init_falls_back_to_github_skills_when_skills_dir_missing(self):
        root = Path(tempfile.mkdtemp(prefix="superspec-"))
        skills_dir = root / ".github" / "skills" / "openspec-apply-change"
        skills_dir.mkdir(parents=True, exist_ok=True)
        (skills_dir / "SKILL.md").write_text("# apply", encoding="utf-8")

        args = SimpleNamespace(agent="codex")
        with patch("superspec.cli.subprocess.run") as mock_run:
            mock_run.return_value = SimpleNamespace(returncode=0, stdout="", stderr="")
            command_init(root, args)

        self.assertTrue((root / ".codex" / "skills" / "openspec-apply-change" / "SKILL.md").exists())

    def test_init_requires_available_skills_source(self):
        root = Path(tempfile.mkdtemp(prefix="superspec-"))
        args = SimpleNamespace(agent="codex")
        with patch("superspec.cli.subprocess.run") as mock_run:
            mock_run.return_value = SimpleNamespace(returncode=0, stdout="", stderr="")
            with self.assertRaises(RuntimeError):
                command_init(root, args)


if __name__ == "__main__":
    unittest.main()
