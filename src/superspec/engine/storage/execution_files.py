from pathlib import Path


def execution_dir(change_dir: str) -> Path:
    return Path(change_dir) / "execution"


def ensure_execution_layout(change_dir: str):
    base = execution_dir(change_dir)
    base.mkdir(parents=True, exist_ok=True)
    return {
        "dir": base,
        "state": base / "state.json",
        "events": base / "events.log",
    }
