import tempfile
import unittest
from pathlib import Path

from superspec.engine.errors import ProtocolError
from superspec.engine.scm.progress_file import (
    CURRENT_SESSION_END,
    CURRENT_SESSION_START,
    build_progress_entry,
    parse_progress_entries,
    render_progress_entry,
    summarize_current_session,
)


class ProgressSummaryTest(unittest.TestCase):
    def test_summarize_current_session_keeps_current_session_on_top_and_stacks_newest_summary_first(self):
        root = Path(tempfile.mkdtemp(prefix="superspec-"))
        progress_path = root / "progress.md"
        first_entry = build_progress_entry(
            commit_hash="abc123",
            change="demo-change",
            summary="feat: add parser",
            details="Implemented parser.\nCovered edge cases.",
            next_steps="wire command",
            committed_at="2026-03-15T09:00:00+00:00",
            files_changed=["src/superspec/cli.py", "shared.txt"],
        )
        second_entry = build_progress_entry(
            commit_hash="def456",
            change="demo-change",
            summary="test: add summary coverage",
            details=" \n\n ",
            next_steps="ship session summary",
            committed_at="2026-03-15T10:00:00+00:00",
            files_changed=["shared.txt", "tests/test_progress_summary.py"],
        )
        progress_path.write_text(
            "\n".join(
                [
                    "# Progress",
                    "",
                    "Intro",
                    "",
                    "## 2026-03-15 Session 1",
                    "- Finish: 2026-03-15T08:00:00+00:00",
                    "",
                    "### Done",
                    "- earlier work",
                    "",
                    "## Current Session",
                    CURRENT_SESSION_START,
                    "",
                    render_progress_entry(first_entry),
                    "",
                    render_progress_entry(second_entry),
                    "",
                    CURRENT_SESSION_END,
                    "",
                    "## Notes",
                    "Keep me",
                    "",
                ]
            ),
            encoding="utf-8",
        )

        payload = summarize_current_session(root, finished_at="2026-03-15T11:30:00+00:00")

        self.assertEqual(payload["session_number"], 2)
        self.assertEqual(payload["session_date"], "2026-03-15")
        progress = progress_path.read_text(encoding="utf-8")
        self.assertIn("## 2026-03-15 Session 2", progress)
        self.assertIn("- Finish: 2026-03-15T11:30:00+00:00", progress)
        self.assertIn("### Done\n- feat: add parser\n\t- Implemented parser.\n\t- Covered edge cases.\n- test: add summary coverage", progress)
        self.assertIn("### Changes\n- demo-change", progress)
        self.assertIn("### Files\n- src/superspec/cli.py\n- shared.txt\n- tests/test_progress_summary.py", progress)
        self.assertIn("### Next\nship session summary", progress)
        self.assertIn(f"{CURRENT_SESSION_START}\n{CURRENT_SESSION_END}", progress)
        self.assertNotIn("### Commit abc123", progress)
        self.assertNotIn("### Commit def456", progress)
        self.assertIn("## Notes\nKeep me", progress)
        self.assertLess(progress.index("## Current Session"), progress.index("## 2026-03-15 Session 2"))
        self.assertLess(progress.index("## 2026-03-15 Session 2"), progress.index("## 2026-03-15 Session 1"))

    def test_summarize_current_session_rejects_empty_current_session(self):
        root = Path(tempfile.mkdtemp(prefix="superspec-"))
        progress_path = root / "progress.md"
        original = "\n".join(
            [
                "# Progress",
                "",
                "## Current Session",
                CURRENT_SESSION_START,
                CURRENT_SESSION_END,
                "",
            ]
        )
        progress_path.write_text(original, encoding="utf-8")

        with self.assertRaises(ProtocolError) as ctx:
            summarize_current_session(root, finished_at="2026-03-15T11:30:00+00:00")

        self.assertEqual(ctx.exception.code, "empty_current_session")
        self.assertEqual(progress_path.read_text(encoding="utf-8"), original)

    def test_parse_progress_entries_tolerates_missing_details_block(self):
        section = "\n".join(
            [
                "### Commit abc123",
                "- Time: 2026-03-15T09:00:00+00:00",
                "- Change: demo-change",
                "- Summary: feat: add parser",
                "- Next: wire command",
                "- Files:",
                "  - src/superspec/cli.py",
            ]
        )

        entries = parse_progress_entries(section)

        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0]["details"], "")
        self.assertEqual(entries[0]["files_changed"], ["src/superspec/cli.py"])


if __name__ == "__main__":
    unittest.main()
