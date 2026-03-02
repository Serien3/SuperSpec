import json
import subprocess

from superspec.engine.errors import ActionExecutionError


def _run_openspec_instruction(instruction_id: str, change_name: str, repo_root: str, timeout_sec=900):
    result = subprocess.run(
        ["openspec", "instructions", instruction_id, "--change", change_name, "--json"],
        cwd=repo_root,
        text=True,
        capture_output=True,
        timeout=timeout_sec,
    )
    if result.returncode != 0:
        raise ActionExecutionError(
            f"openspec {instruction_id} failed",
            {"stderr": result.stderr, "status": result.returncode},
        )

    lines = result.stdout.splitlines()
    json_start = next((i for i, line in enumerate(lines) if line.strip().startswith("{")), -1)
    json_text = "\n".join(lines[json_start:]) if json_start >= 0 else "{}"

    try:
        parsed = json.loads(json_text)
    except json.JSONDecodeError:
        parsed = {"raw": result.stdout}

    return {
        "instructionId": instruction_id,
        "status": "success",
        "parsed": parsed,
        "stdout": result.stdout,
    }


def handle_openspec_proposal(action: dict, context: dict):
    return _run_openspec_instruction("proposal", context["changeName"], context["repoRoot"], action.get("timeoutSec", 900))


def handle_openspec_specs(action: dict, context: dict):
    return _run_openspec_instruction("specs", context["changeName"], context["repoRoot"], action.get("timeoutSec", 900))


def handle_openspec_design(action: dict, context: dict):
    return _run_openspec_instruction("design", context["changeName"], context["repoRoot"], action.get("timeoutSec", 900))


def handle_openspec_tasks(action: dict, context: dict):
    return _run_openspec_instruction("tasks", context["changeName"], context["repoRoot"], action.get("timeoutSec", 900))


def handle_openspec_apply(action: dict, context: dict):
    return _run_openspec_instruction("apply", context["changeName"], context["repoRoot"], action.get("timeoutSec", 900))
