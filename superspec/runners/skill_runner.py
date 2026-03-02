import subprocess

from superspec.engine.errors import ActionExecutionError


def run_skill_action(action: dict, context: dict):
    skill = action.get("skill")
    if not skill:
        raise ActionExecutionError(f"Action {action['id']} is missing skill")

    timeout_sec = action.get("timeoutSec") or context["defaults"].get("timeoutSec", 900)
    prompt = (action.get("inputs") or {}).get("prompt")

    if not prompt:
        return {
            "executor": "skill",
            "skill": skill,
            "status": "noop",
            "message": "Skill wiring placeholder: no prompt provided in action.inputs.prompt",
        }

    result = subprocess.run(
        ["echo", prompt],
        cwd=context["repoRoot"],
        text=True,
        capture_output=True,
        timeout=timeout_sec,
    )

    if result.returncode != 0:
        raise ActionExecutionError(
            f"Skill action failed: {action['id']}",
            {"status": result.returncode, "stderr": result.stderr},
        )

    return {
        "executor": "skill",
        "skill": skill,
        "status": "success",
        "output": result.stdout.strip(),
    }
