import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from superspec.scripts.worktree_create import detect_default_base


class WorktreeCreateScriptTest(unittest.TestCase):
    def test_detect_default_base_rejects_wt_branch_from_symbolic_ref(self):
        root = Path(tempfile.mkdtemp(prefix="superspec-"))
        with patch("superspec.scripts.worktree_create.try_run", return_value="wt/20260303-1230-demo"):
            with self.assertRaises(RuntimeError):
                detect_default_base(root)

    def test_detect_default_base_rejects_wt_branch_from_rev_parse(self):
        root = Path(tempfile.mkdtemp(prefix="superspec-"))
        with patch("superspec.scripts.worktree_create.try_run", return_value=None):
            with patch("superspec.scripts.worktree_create.run", return_value="wt/20260303-1230-demo"):
                with self.assertRaises(RuntimeError):
                    detect_default_base(root)


if __name__ == "__main__":
    unittest.main()
