import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from superspec.engine.errors import ProtocolError
from superspec.engine.scm.git_commit import commit_for_change


class GitCommitTest(unittest.TestCase):
    def _run(self, args, cwd: Path):
        proc = subprocess.run(args, cwd=cwd, text=True, capture_output=True)
        if proc.returncode != 0:
            raise RuntimeError(f"command failed: {' '.join(args)}\nstdout:\n{proc.stdout}\nstderr:\n{proc.stderr}")
        return proc.stdout.strip()

    def test_commit_for_change_records_files_changed_into_execution_state(self):
        root = Path(tempfile.mkdtemp(prefix="superspec-"))
        self._run(["git", "init"], root)
        self._run(["git", "config", "user.name", "SuperSpec Test"], root)
        self._run(["git", "config", "user.email", "test@example.com"], root)

        tracked = root / "tracked.txt"
        tracked.write_text("one\n", encoding="utf-8")
        self._run(["git", "add", "tracked.txt"], root)
        self._run(["git", "commit", "-m", "chore: init"], root)

        change_dir = root / "superspec" / "changes" / "demo-change"
        state_path = change_dir / "execution" / "state.json"
        state_path.parent.mkdir(parents=True, exist_ok=True)
        state_path.write_text(
            json.dumps(
                {
                    "meta": {
                        "schemaVersion": "https://superspec.dev/schemas/workflow-v1.json",
                        "changeName": "demo-change",
                    },
                    "runtime": {
                        "changeName": "demo-change",
                        "status": "running",
                        "steps": [],
                    },
                },
                indent=2,
            ),
            encoding="utf-8",
        )

        tracked.write_text("one\ntwo\n", encoding="utf-8")
        self._run(["git", "add", "tracked.txt"], root)

        payload = commit_for_change(root, "demo-change", "feat: test commit")

        head = self._run(["git", "rev-parse", "HEAD"], root)
        self.assertEqual(payload["commit_hash"], head)
        self.assertEqual(payload["files_changed"], ["tracked.txt"])

        state = json.loads(state_path.read_text(encoding="utf-8"))
        self.assertEqual(state["runtime"]["files_changed"], ["tracked.txt"])
        self.assertNotIn("commit_by_superspec_last", state["runtime"])

    def test_commit_for_change_appends_non_overlapping_files_changed(self):
        root = Path(tempfile.mkdtemp(prefix="superspec-"))
        self._run(["git", "init"], root)
        self._run(["git", "config", "user.name", "SuperSpec Test"], root)
        self._run(["git", "config", "user.email", "test@example.com"], root)

        tracked = root / "tracked.txt"
        tracked.write_text("one\n", encoding="utf-8")
        self._run(["git", "add", "tracked.txt"], root)
        self._run(["git", "commit", "-m", "chore: init"], root)

        change_dir = root / "superspec" / "changes" / "demo-change"
        state_path = change_dir / "execution" / "state.json"
        state_path.parent.mkdir(parents=True, exist_ok=True)
        state_path.write_text(
            json.dumps(
                {
                    "meta": {
                        "schemaVersion": "https://superspec.dev/schemas/workflow-v1.json",
                        "changeName": "demo-change",
                    },
                    "runtime": {
                        "changeName": "demo-change",
                        "status": "running",
                        "steps": [],
                        "files_changed": ["tracked.txt"],
                    },
                },
                indent=2,
            ),
            encoding="utf-8",
        )

        another = root / "another.txt"
        another.write_text("new\n", encoding="utf-8")
        tracked.write_text("one\ntwo\n", encoding="utf-8")
        self._run(["git", "add", "tracked.txt", "another.txt"], root)

        payload = commit_for_change(root, "demo-change", "feat: second commit")

        self.assertEqual(payload["files_changed"], ["tracked.txt", "another.txt"])

        state = json.loads(state_path.read_text(encoding="utf-8"))
        self.assertEqual(state["runtime"]["files_changed"], ["tracked.txt", "another.txt"])

    def test_commit_for_change_requires_running_state(self):
        root = Path(tempfile.mkdtemp(prefix="superspec-"))
        self._run(["git", "init"], root)
        self._run(["git", "config", "user.name", "SuperSpec Test"], root)
        self._run(["git", "config", "user.email", "test@example.com"], root)

        tracked = root / "tracked.txt"
        tracked.write_text("one\n", encoding="utf-8")
        self._run(["git", "add", "tracked.txt"], root)
        self._run(["git", "commit", "-m", "chore: init"], root)

        change_dir = root / "superspec" / "changes" / "demo-change"
        state_path = change_dir / "execution" / "state.json"
        state_path.parent.mkdir(parents=True, exist_ok=True)
        state_path.write_text(
            json.dumps(
                {
                    "meta": {
                        "schemaVersion": "https://superspec.dev/schemas/workflow-v1.json",
                        "changeName": "demo-change",
                    },
                    "runtime": {
                        "status": "success",
                        "steps": [],
                    },
                },
                indent=2,
            ),
            encoding="utf-8",
        )

        tracked.write_text("one\ntwo\n", encoding="utf-8")
        self._run(["git", "add", "tracked.txt"], root)

        with self.assertRaises(ProtocolError) as ctx:
            commit_for_change(root, "demo-change", "feat: test commit")

        self.assertEqual(ctx.exception.code, "invalid_state")


if __name__ == "__main__":
    unittest.main()
