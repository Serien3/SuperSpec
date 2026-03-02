import argparse
import json
import subprocess
from pathlib import Path

from superspec.engine.errors import ProtocolError
from superspec.engine.orchestrator import run_protocol_action_from_cli, to_json
from superspec.engine.plan_loader import load_plan_from_change, resolve_change_dir
from superspec.engine.validator import validate_plan

PLAN_MODE_TEMPLATES = {
    "sdd": "plan.template.json",
}


def _read_template(repo_root: Path, change_name: str, mode: str) -> str:
    template_name = PLAN_MODE_TEMPLATES.get(mode)
    if not template_name:
        supported = ", ".join(sorted(PLAN_MODE_TEMPLATES.keys()))
        raise ProtocolError(
            f"Unsupported plan mode '{mode}'. Supported modes: {supported}",
            code="invalid_plan_mode",
            details={"mode": mode, "supportedModes": sorted(PLAN_MODE_TEMPLATES.keys())},
        )
    template_path = repo_root / "superspec" / "templates" / template_name
    return template_path.read_text(encoding="utf-8").replace("${CHANGE_NAME}", change_name)


def _write_plan(repo_root: Path, change_name: str, mode: str):
    change_dir = resolve_change_dir(str(repo_root), change_name)
    change_dir.mkdir(parents=True, exist_ok=True)
    plan_path = change_dir / "plan.json"
    plan_path.write_text(f"{_read_template(repo_root, change_name, mode)}\n", encoding="utf-8")
    return plan_path


def _run_openspec_new_change(repo_root: Path, change_name: str, summary: str | None):
    cmd = ["openspec", "new", "change", change_name]
    if summary:
        cmd.extend(["--summary", summary])
    result = subprocess.run(cmd, cwd=repo_root, text=True, capture_output=True)
    if result.returncode != 0:
        raise RuntimeError(result.stderr or result.stdout or "openspec new change failed")
    print(result.stdout, end="")


def _parse_object_json(raw: str, field: str):
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ProtocolError(f"{field} must be valid JSON", code="invalid_payload") from exc
    if not isinstance(parsed, dict):
        raise ProtocolError(f"{field} must be a JSON object", code="invalid_payload")
    return parsed


def command_change_new(repo_root: Path, args):
    _run_openspec_new_change(repo_root, args.change, args.summary)
    if args.init_plan:
        plan_path = _write_plan(repo_root, args.change, args.plan_mode)
        print(f"Initialized {plan_path} (mode={args.plan_mode})")
        return
    print(f"Plan not initialized for change '{args.change}'.")
    print(f"Run: superspec plan init {args.change} --mode sdd")


def command_plan_init(repo_root: Path, args):
    plan_path = _write_plan(repo_root, args.change, args.mode)
    print(f"Initialized {plan_path} (mode={args.mode})")


def command_plan_validate(repo_root: Path, args):
    plan, plan_path = load_plan_from_change(str(repo_root), args.change)
    validate_plan(plan)
    print(f"Plan is valid: {plan_path}")


def command_plan_next(repo_root: Path, args):
    payload = run_protocol_action_from_cli(
        repo_root,
        args.change,
        "next",
        owner=args.owner,
        debug=bool(args.debug),
    )
    if args.json:
        print(to_json(payload))
    else:
        print(payload.get("instruction", ""))


def command_plan_complete(repo_root: Path, args):
    result_payload = _parse_object_json(args.result_json, "result-json")
    payload = run_protocol_action_from_cli(
        repo_root,
        args.change,
        "complete",
        action_id=args.action_id,
        result_payload=result_payload,
    )
    if args.json:
        print(to_json(payload))
    else:
        print(f"Action {args.action_id} marked complete.")


def command_plan_fail(repo_root: Path, args):
    error_payload = _parse_object_json(args.error_json, "error-json")
    payload = run_protocol_action_from_cli(
        repo_root,
        args.change,
        "fail",
        action_id=args.action_id,
        error_payload=error_payload,
    )
    if args.json:
        print(to_json(payload))
    else:
        print(f"Action {args.action_id} marked failed.")


def command_plan_status(repo_root: Path, args):
    payload = run_protocol_action_from_cli(repo_root, args.change, "status")
    if args.json:
        print(to_json(payload))
        return

    print(f"Change: {args.change}")
    print(f"Status: {payload['status']}")
    progress = payload["progress"]
    print(f"Progress: {progress['done']}/{progress['total']} (failed={progress['failed']}, running={progress['running']})")
    for action in payload["actions"]:
        suffix = f" ({action['error']['message']})" if action.get("error") and action["error"].get("message") else ""
        print(f"- {action['id']} [{action['status']}]{suffix}")


def build_parser():
    parser = argparse.ArgumentParser(prog="superspec")
    sub = parser.add_subparsers(dest="group")

    change = sub.add_parser("change")
    change_sub = change.add_subparsers(dest="sub")
    change_new = change_sub.add_parser("new")
    change_new.add_argument("change")
    change_new.add_argument("--summary")
    change_new.add_argument("--init-plan", action="store_true")
    change_new.add_argument("--plan-mode", default="sdd")

    plan = sub.add_parser("plan")
    plan_sub = plan.add_subparsers(dest="sub")

    plan_init = plan_sub.add_parser("init")
    plan_init.add_argument("change")
    plan_init.add_argument("--mode", default="sdd")

    plan_validate = plan_sub.add_parser("validate")
    plan_validate.add_argument("change")

    plan_next = plan_sub.add_parser("next")
    plan_next.add_argument("change")
    plan_next.add_argument("--owner", default="agent")
    plan_next.add_argument("--debug", action="store_true")
    plan_next.add_argument("--json", action="store_true")

    plan_complete = plan_sub.add_parser("complete")
    plan_complete.add_argument("change")
    plan_complete.add_argument("action_id")
    plan_complete.add_argument("--result-json", required=True)
    plan_complete.add_argument("--json", action="store_true")

    plan_fail = plan_sub.add_parser("fail")
    plan_fail.add_argument("change")
    plan_fail.add_argument("action_id")
    plan_fail.add_argument("--error-json", required=True)
    plan_fail.add_argument("--json", action="store_true")

    plan_status = plan_sub.add_parser("status")
    plan_status.add_argument("change")
    plan_status.add_argument("--json", action="store_true")

    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()
    repo_root = Path.cwd()

    try:
        if args.group == "change" and args.sub == "new":
            command_change_new(repo_root, args)
            return
        if args.group == "plan" and args.sub == "init":
            command_plan_init(repo_root, args)
            return
        if args.group == "plan" and args.sub == "validate":
            command_plan_validate(repo_root, args)
            return
        if args.group == "plan" and args.sub == "next":
            command_plan_next(repo_root, args)
            return
        if args.group == "plan" and args.sub == "complete":
            command_plan_complete(repo_root, args)
            return
        if args.group == "plan" and args.sub == "fail":
            command_plan_fail(repo_root, args)
            return
        if args.group == "plan" and args.sub == "status":
            command_plan_status(repo_root, args)
            return

        parser.print_help()
        raise SystemExit(1)
    except ProtocolError as exc:
        payload = {"error": {"code": exc.code, "message": str(exc), "details": exc.details}}
        print(to_json(payload))
        raise SystemExit(1) from exc
    except Exception as exc:  # noqa: BLE001
        print(f"Error: {exc}")
        raise SystemExit(1) from exc


if __name__ == "__main__":
    main()
