WORKFLOW_ALLOWED_TOP_LEVEL_FIELDS = (
    "workflowId",
    "version",
    "description",
    "finishPolicy",
    "steps",
    "metadata",
)

WORKFLOW_RUNTIME_CUSTOMIZATION_FIELDS = (
    "steps",
)

WORKFLOW_OPTIONAL_TOP_LEVEL_FIELDS = (
    "description",
    "finishPolicy",
    "metadata",
)

WORKFLOW_EXECUTORS = ("skill", "script", "human")


def dot_path(path_parts):
    if not path_parts:
        return "$"
    return ".".join(str(part) for part in path_parts)


def error_payload(code: str, path: str, message: str, hint: str | None = None):
    payload = {
        "code": code,
        "path": path,
        "message": message,
    }
    if hint:
        payload["hint"] = hint
    return payload
