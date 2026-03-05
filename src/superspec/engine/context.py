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


def _resolve_template_value(value, context):
    if isinstance(value, str):
        return resolve_template_string(value, context)
    if isinstance(value, list):
        return [_resolve_template_value(item, context) for item in value]
    if isinstance(value, dict):
        return {key: _resolve_template_value(item, context) for key, item in value.items()}
    return value


def resolve_runtime_action_fields(action: dict, context: dict):
    resolved = {}
    for field in ("executor", "script", "skill", "prompt"):
        if field in action:
            resolved[field] = resolve_template_string(action[field], context)

    human = action.get("human")
    if isinstance(human, dict):
        resolved_human = {}
        for field in ("instruction", "approveLabel", "rejectLabel"):
            if field in human:
                resolved_human[field] = resolve_template_string(human[field], context)
        if resolved_human:
            resolved["human"] = resolved_human

    inputs = action.get("inputs")
    if isinstance(inputs, dict):
        resolved["inputs"] = _resolve_template_value(inputs, context)

    return resolved
