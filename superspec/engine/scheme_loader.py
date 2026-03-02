import json
from pathlib import Path

from jsonschema import Draft202012Validator

from superspec.engine.errors import ProtocolError

def _load_json(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ProtocolError(f"File not found: {path}", code="missing_file", details={"path": str(path)}) from exc
    except json.JSONDecodeError as exc:
        raise ProtocolError(f"Invalid JSON in {path}", code="invalid_json", details={"path": str(path)}) from exc


def _deep_merge(base, overlay):
    if not isinstance(base, dict) or not isinstance(overlay, dict):
        return overlay

    merged = dict(base)
    for key, value in overlay.items():
        if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
            merged[key] = _deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def _resolve_scheme_name(scheme: str | None):
    return scheme or "sdd"


def _load_scheme_schema(repo_root: Path):
    return _load_json(repo_root / "superspec" / "schemas" / "plan.scheme.schema.json")


def _load_base_template(repo_root: Path):
    return _load_json(repo_root / "superspec" / "templates" / "plan.base.json")


def _load_scheme(repo_root: Path, scheme_name: str):
    path = repo_root / "superspec" / "schemes" / f"{scheme_name}.scheme.json"
    if not path.exists():
        raise ProtocolError(
            f"Unknown plan scheme '{scheme_name}'. Expected file: {path}",
            code="invalid_plan_scheme",
            details={"scheme": scheme_name, "path": str(path)},
        )
    return _load_json(path), path


def _validate_scheme(repo_root: Path, scheme: dict, scheme_name: str):
    schema = _load_scheme_schema(repo_root)
    validator = Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(scheme), key=lambda e: list(e.path))
    if errors:
        first = errors[0]
        loc = ".".join(str(p) for p in first.path) or "$"
        raise ProtocolError(
            f"Invalid scheme '{scheme_name}': {first.message}",
            code="invalid_plan_scheme",
            details={"scheme": scheme_name, "location": loc},
        )


def _scheme_payload(scheme: dict):
    payload = {}
    for key in ("planId", "title", "goal", "variables", "defaults", "actions", "metadata"):
        if key in scheme:
            payload[key] = scheme[key]

    plan_overlay = scheme.get("plan", {})
    if isinstance(plan_overlay, dict):
        payload = _deep_merge(payload, plan_overlay)

    # Keep scheme identity in generated metadata for traceability.
    payload.setdefault("metadata", {})
    payload["metadata"] = _deep_merge(
        payload.get("metadata", {}),
        {
            "scheme": {
                "id": scheme["schemeId"],
                "version": scheme["version"],
            }
        },
    )
    return payload


def build_plan_from_scheme(repo_root: Path, change_name: str, scheme: str | None = None, overrides=None):
    selected_scheme = _resolve_scheme_name(scheme)
    base = _load_base_template(repo_root)
    scheme_doc, scheme_path = _load_scheme(repo_root, selected_scheme)
    _validate_scheme(repo_root, scheme_doc, selected_scheme)

    generated = _deep_merge(base, _scheme_payload(scheme_doc))
    generated = _deep_merge(generated, overrides or {})

    generated.setdefault("context", {})
    generated["context"]["changeName"] = change_name
    generated["context"]["changeDir"] = f"openspec/changes/{change_name}"
    generated["context"].setdefault("repoRoot", ".")
    generated["context"].setdefault("specRoot", "openspec")

    return generated, selected_scheme, str(scheme_path)
