from pathlib import Path

from superspec.engine.plan_loader import resolve_change_dir


DESIGN_TRIGGER_TERMS = (
    "cross-cutting",
    "architecture",
    "refactor",
    "redesign",
    "breaking change",
    "migration",
    "multiple components",
)


def needs_design_doc(repo_root: str | Path, change_name: str) -> bool:
    change_dir = resolve_change_dir(str(repo_root), change_name)

    specs_dir = change_dir / "specs"
    if specs_dir.exists():
        spec_docs = sum(1 for path in specs_dir.rglob("*.md") if path.is_file())
        if spec_docs > 2:
            return True

    proposal_path = change_dir / "proposal.md"
    if proposal_path.exists():
        proposal_text = proposal_path.read_text(encoding="utf-8").lower()
        if any(term in proposal_text for term in DESIGN_TRIGGER_TERMS):
            return True

    return False
