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


def resolve_value(value, context):
    if isinstance(value, list):
        return [resolve_value(item, context) for item in value]
    if isinstance(value, dict):
        return {k: resolve_value(v, context) for k, v in value.items()}
    return resolve_template_string(value, context)


def set_path(target, path: str, value):
    parts = path.split(".")
    current = target
    for part in parts[:-1]:
        if part not in current or not isinstance(current[part], dict):
            current[part] = {}
        current = current[part]
    current[parts[-1]] = value
