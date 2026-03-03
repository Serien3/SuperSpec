import re


def _get_path_value(source, path: str):
    current = source
    for part in path.split("."):
        if not isinstance(current, dict) or part not in current:
            return None
        current = current[part]
    return current


def resolve_template_string(value, context):
    if not isinstance(value, str):
        return value

    full = re.fullmatch(r"\$\{(.+)}", value)
    if full:
        expr = full.group(1).strip()
        found = _get_path_value(context, expr)
        if found is None:
            raise ValueError(f"Unresolved expression: {value}")
        return found

    def replace(match):
        expr = match.group(1).strip()
        found = _get_path_value(context, expr)
        if found is None:
            raise ValueError(f"Unresolved expression: ${{{expr}}}")
        return str(found)

    return re.sub(r"\$\{([^}]+)}", replace, value)


def resolve_runtime_action_fields(action: dict, context: dict):
    resolved = {}
    for field in ("executor", "script", "skill"):
        if field in action:
            resolved[field] = resolve_template_string(action[field], context)

    inputs = action.get("inputs")
    if isinstance(inputs, dict) and "prompt" in inputs:
        resolved["inputs"] = {
            "prompt": resolve_template_string(inputs["prompt"], context),
        }

    return resolved
