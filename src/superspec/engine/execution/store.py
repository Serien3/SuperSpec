from superspec.engine.errors import ProtocolError
from superspec.engine.execution.helpers import now_iso
from superspec.engine.execution.payloads import runtime_blueprint_from_seed
from superspec.engine.storage.execution_snapshot import initialize_execution_snapshot, read_execution_state, write_execution_state


def ensure_protocol_state(runtime_seed: dict | None, change_dir: str):
    state = read_execution_state(change_dir)
    if state is None:
        if not isinstance(runtime_seed, dict):
            raise ProtocolError(
                "Execution state not found. Initialize the change first.",
                code="missing_file",
            )
        snapshot = initialize_execution_snapshot(change_dir, runtime_blueprint_from_seed(runtime_seed))
        state = snapshot["runtime"]
    return state


def persist_runtime_state(change_dir: str, state: dict):
    state["updatedAt"] = now_iso()
    write_execution_state(change_dir, state)
