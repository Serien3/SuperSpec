import subprocess
import os

from superspec.engine.errors import ActionExecutionError


def run_script_action(action: dict, context: dict):
    script = action.get("script")
    if not script:
        raise ActionExecutionError(f"Action {action['id']} is missing script")

    timeout_sec = action.get("timeoutSec") or context["defaults"].get("timeoutSec", 900)
    result = subprocess.run(
        script,
        shell=True,
        cwd=context["repoRoot"],
        env={**os.environ, **context.get("environment", {})},
        text=True,
        capture_output=True,
        timeout=timeout_sec,
    )

    if result.returncode != 0:
        raise ActionExecutionError(
            f"Script action failed: {action['id']}",
            {"status": result.returncode, "stderr": result.stderr},
        )

    return {
        "executor": "script",
        "command": script,
        "stdout": result.stdout,
        "stderr": result.stderr,
        "status": "success",
    }
