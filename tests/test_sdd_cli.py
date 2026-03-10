import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from types import SimpleNamespace

from superspec.cli import build_parser, command_sdd_design


class SddDesignCommandTest(unittest.TestCase):
    def test_sdd_design_parser_form(self):
        parser = build_parser()

        args = parser.parse_args(["sdd", "design", "demo-change"])
        self.assertEqual(args.group, "sdd")
        self.assertEqual(args.sub, "design")
        self.assertEqual(args.change, "demo-change")

    def test_returns_true_when_specs_markdown_count_exceeds_two(self):
        root = Path(tempfile.mkdtemp(prefix="superspec-"))
        specs_dir = root / "superspec" / "changes" / "demo-change" / "specs"
        (specs_dir / "a").mkdir(parents=True, exist_ok=True)
        (specs_dir / "top.md").write_text("# top", encoding="utf-8")
        (specs_dir / "a" / "one.md").write_text("# one", encoding="utf-8")
        (specs_dir / "a" / "two.md").write_text("# two", encoding="utf-8")

        stdout = StringIO()
        with redirect_stdout(stdout):
            command_sdd_design(root, SimpleNamespace(change="demo-change"))

        self.assertEqual(stdout.getvalue().strip(), "True")

    def test_returns_true_when_proposal_contains_trigger_term(self):
        root = Path(tempfile.mkdtemp(prefix="superspec-"))
        change_dir = root / "superspec" / "changes" / "demo-change"
        change_dir.mkdir(parents=True, exist_ok=True)
        (change_dir / "proposal.md").write_text(
            "This introduces a Breaking Change for downstream clients.",
            encoding="utf-8",
        )

        stdout = StringIO()
        with redirect_stdout(stdout):
            command_sdd_design(root, SimpleNamespace(change="demo-change"))

        self.assertEqual(stdout.getvalue().strip(), "True")

    def test_returns_false_when_no_trigger_matches(self):
        root = Path(tempfile.mkdtemp(prefix="superspec-"))
        change_dir = root / "superspec" / "changes" / "demo-change"
        specs_dir = change_dir / "specs"
        specs_dir.mkdir(parents=True, exist_ok=True)
        (specs_dir / "one.md").write_text("# one", encoding="utf-8")
        (specs_dir / "two.md").write_text("# two", encoding="utf-8")
        (change_dir / "proposal.md").write_text(
            "This is a focused feature addition with limited scope.",
            encoding="utf-8",
        )

        stdout = StringIO()
        with redirect_stdout(stdout):
            command_sdd_design(root, SimpleNamespace(change="demo-change"))

        self.assertEqual(stdout.getvalue().strip(), "False")


if __name__ == "__main__":
    unittest.main()
