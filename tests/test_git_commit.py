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

        payload = commit_for_change(
            root,
            "demo-change",
            "feat: test commit",
            "Agent wrote the body for this commit.",
            "wire finish-session script",
        )

        head = self._run(["git", "rev-parse", "HEAD"], root)
        self.assertEqual(payload["commit_hash"], head)
        self.assertEqual(payload["summary"], "feat: test commit")
        self.assertEqual(payload["details"], "Agent wrote the body for this commit.")
        self.assertEqual(payload["next"], "wire finish-session script")
        self.assertEqual(
            payload["files_changed"],
            ["superspec/changes/demo-change/execution/state.json", "tracked.txt"],
        )
        self.assertEqual(payload["progress_file"], str(root / "progress.md"))
        self.assertEqual(payload["progress_entry"]["commit_hash"], head)
        self.assertEqual(payload["progress_entry"]["change"], "demo-change")
        self.assertEqual(payload["progress_entry"]["summary"], "feat: test commit")
        self.assertEqual(payload["progress_entry"]["details"], "Agent wrote the body for this commit.")
        self.assertEqual(payload["progress_entry"]["next"], "wire finish-session script")
        self.assertEqual(
            payload["progress_entry"]["files_changed"],
            ["superspec/changes/demo-change/execution/state.json", "tracked.txt"],
        )
        self.assertTrue(payload["committed_at"])
        self.assertIn("feat: test commit", payload["commit_output"])
        body = self._run(["git", "show", "-s", "--format=%B", "HEAD"], root)
        self.assertIn("feat: test commit", body)
        self.assertIn("Agent wrote the body for this commit.", body)

        state = json.loads(state_path.read_text(encoding="utf-8"))
        self.assertEqual(
            state["runtime"]["files_changed"],
            ["superspec/changes/demo-change/execution/state.json", "tracked.txt"],
        )
        self.assertNotIn("commit_by_superspec_last", state["runtime"])

        progress_path = root / "progress.md"
        self.assertTrue(progress_path.exists())
        progress = progress_path.read_text(encoding="utf-8")
        self.assertIn("<!-- superspec:current-session:start -->", progress)
        self.assertIn("<!-- superspec:current-session:end -->", progress)
        self.assertIn(f"### Commit {head}", progress)
        self.assertIn("- Change: demo-change", progress)
        self.assertIn("- Summary: feat: test commit", progress)
        self.assertIn("- Details:\n<!-- superspec:details:start -->\nAgent wrote the body for this commit.\n<!-- superspec:details:end -->", progress)
        self.assertIn("- Next: wire finish-session script", progress)
        self.assertIn("  - superspec/changes/demo-change/execution/state.json", progress)
        self.assertIn("  - tracked.txt", progress)

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

        payload = commit_for_change(
            root,
            "demo-change",
            "feat: second commit",
            "Body for the second commit.",
            "review progress template",
        )

        self.assertEqual(
            payload["files_changed"],
            [
                "tracked.txt",
                "another.txt",
                "superspec/changes/demo-change/execution/state.json",
            ],
        )

        state = json.loads(state_path.read_text(encoding="utf-8"))
        self.assertEqual(
            state["runtime"]["files_changed"],
            [
                "tracked.txt",
                "another.txt",
                "superspec/changes/demo-change/execution/state.json",
            ],
        )

    def test_commit_for_change_appends_progress_entries_and_preserves_other_content(self):
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

        progress_path = root / "progress.md"
        progress_path.write_text(
            "# Progress\n\nCustom intro\n\n## Current Session\n<!-- superspec:current-session:start -->\n<!-- superspec:current-session:end -->\n\n## Notes\nKeep me\n",
            encoding="utf-8",
        )

        tracked.write_text("one\ntwo\n", encoding="utf-8")
        first_payload = commit_for_change(
            root,
            "demo-change",
            "feat: first commit",
            "First body block.",
            "draft finish-session",
        )

        another = root / "another.txt"
        another.write_text("new\n", encoding="utf-8")
        second_payload = commit_for_change(
            root,
            "demo-change",
            "feat: second commit",
            "Second body block.",
            "connect summary script",
        )

        progress = progress_path.read_text(encoding="utf-8")
        self.assertIn("Custom intro", progress)
        self.assertIn("## Notes\nKeep me", progress)
        self.assertIn(f"### Commit {first_payload['commit_hash']}", progress)
        self.assertIn(f"### Commit {second_payload['commit_hash']}", progress)
        self.assertIn("- Summary: feat: first commit", progress)
        self.assertIn("- Summary: feat: second commit", progress)
        self.assertIn("<!-- superspec:details:start -->", progress)
        self.assertIn("<!-- superspec:details:end -->", progress)
        self.assertIn("First body block.", progress)
        self.assertIn("Second body block.", progress)
        self.assertIn("- Next: draft finish-session", progress)
        self.assertIn("- Next: connect summary script", progress)
        self.assertIn("  - superspec/changes/demo-change/execution/state.json", progress)
        self.assertIn("  - tracked.txt", progress)
        self.assertIn("  - another.txt", progress)

    def test_commit_for_change_stages_existing_progress_file_changes(self):
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

        progress_path = root / "progress.md"
        progress_path.write_text(
            "# Progress\n\nHuman note before commit\n\n## Current Session\n<!-- superspec:current-session:start -->\n<!-- superspec:current-session:end -->\n",
            encoding="utf-8",
        )
        tracked.write_text("one\ntwo\n", encoding="utf-8")

        payload = commit_for_change(
            root,
            "demo-change",
            "feat: include progress file",
            "Body that explains why progress is part of the commit.",
            "continue session memory",
        )

        self.assertIn("progress.md", payload["files_changed"])
        show = self._run(["git", "show", "--pretty=format:", "--name-only", "HEAD"], root)
        self.assertIn("progress.md", show.splitlines())

    def test_commit_for_change_preserves_multiline_details_in_git_and_progress(self):
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
        details = "Line one of the body.\nLine two keeps context.\nLine three records follow-up."

        payload = commit_for_change(
            root,
            "demo-change",
            "feat: multiline details",
            details,
            "prepare session closeout",
        )

        body = self._run(["git", "show", "-s", "--format=%B", "HEAD"], root)
        self.assertIn("feat: multiline details", body)
        self.assertIn(details, body)

        progress = (root / "progress.md").read_text(encoding="utf-8")
        self.assertIn(payload["progress_entry"]["details"], progress)
        self.assertIn(
            "<!-- superspec:details:start -->\nLine one of the body.\nLine two keeps context.\nLine three records follow-up.\n<!-- superspec:details:end -->",
            progress,
        )

    def test_commit_for_change_decodes_escaped_newlines_in_details(self):
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
        escaped_details = "Line one of the body.\\nLine two keeps context.\\nLine three records follow-up."

        payload = commit_for_change(
            root,
            "demo-change",
            "feat: escaped details",
            escaped_details,
            "prepare session closeout",
        )

        expected_details = "Line one of the body.\nLine two keeps context.\nLine three records follow-up."
        self.assertEqual(payload["details"], expected_details)

        body = self._run(["git", "show", "-s", "--format=%B", "HEAD"], root)
        self.assertIn("feat: escaped details", body)
        self.assertIn(expected_details, body)
        self.assertNotIn("\\n", body)

        progress = (root / "progress.md").read_text(encoding="utf-8")
        self.assertIn(expected_details, progress)
        self.assertNotIn("\\n", progress)

    def test_commit_for_change_allows_blank_details_and_omits_details_block(self):
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

        payload = commit_for_change(
            root,
            "demo-change",
            "feat: summary only",
            " \n",
            "continue with docs",
        )

        self.assertEqual(payload["details"], "")
        body = self._run(["git", "show", "-s", "--format=%B", "HEAD"], root)
        self.assertEqual(body, "feat: summary only")

        progress = (root / "progress.md").read_text(encoding="utf-8")
        self.assertNotIn("- Details:", progress)
        self.assertNotIn("<!-- superspec:details:start -->", progress)
        self.assertNotIn("<!-- superspec:details:end -->", progress)

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

        with self.assertRaises(ProtocolError) as ctx:
            commit_for_change(root, "demo-change", "feat: test commit", "Body goes here.", "resume later")

        self.assertEqual(ctx.exception.code, "invalid_state")


if __name__ == "__main__":
    unittest.main()
