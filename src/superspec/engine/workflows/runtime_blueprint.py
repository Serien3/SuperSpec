from superspec.engine.workflows.definitions import WORKFLOW_RUNTIME_CUSTOMIZATION_FIELDS


def workflow_runtime_blueprint_payload(workflow: dict, change_name: str):
    payload = {
        "changeName": change_name,
    }
    for key in WORKFLOW_RUNTIME_CUSTOMIZATION_FIELDS:
        if key in workflow:
            payload[key] = workflow[key]

    normalized_steps = []
    for step in payload.get("steps", []):
        if isinstance(step, dict):
            normalized_steps.append(dict(step))
        else:
            normalized_steps.append(step)
    if normalized_steps:
        payload["steps"] = normalized_steps

    payload["workflow"] = {key: value for key, value in workflow.items() if key != "steps"}
    return payload
