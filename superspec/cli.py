import argparse
import json
import subprocess
from pathlib import Path

from superspec.engine.orchestrator import run_plan
from superspec.engine.plan_loader import load_plan_from_change, resolve_change_dir
from superspec.engine.state_store import load_latest_run_state
from superspec.engine.validator import validate_plan


def _read_template(repo_root: Path, change_name: str) -> str:
    template_path = repo_root / "superspec" / "templates" / "plan.template.json"
    return template_path.read_text(encoding="utf-8").replace("${CHANGE_NAME}", change_name)


def _run_openspec_new_change(repo_root: Path, change_name: str, summary: str | None):
    cmd = ["openspec", "new", "change", change_name]
    if summary:
        cmd.extend(["--summary", summary])
    result = subprocess.run(cmd, cwd=repo_root, text=True, capture_output=True)
    if result.returncode != 0:
        raise RuntimeError(result.stderr or result.stdout or "openspec new change failed")
    print(result.stdout, end="")


def command_change_new(repo_root: Path, args):
    _run_openspec_new_change(repo_root, args.change, args.summary)
    change_dir = resolve_change_dir(str(repo_root), args.change)
    plan_path = change_dir / "plan.json"
    if not plan_path.exists():
        plan_path.write_text(f"{_read_template(repo_root, args.change)}\n", encoding="utf-8")
    print(f"Initialized {plan_path}")


def command_plan_init(repo_root: Path, args):
    change_dir = resolve_change_dir(str(repo_root), args.change)
    change_dir.mkdir(parents=True, exist_ok=True)
    plan_path = change_dir / "plan.json"
    plan_path.write_text(f"{_read_template(repo_root, args.change)}\n", encoding="utf-8")
    print(f"Initialized {plan_path}")


def command_plan_validate(repo_root: Path, args):
    plan, plan_path = load_plan_from_change(str(repo_root), args.change)
    validate_plan(plan)
    print(f"Plan is valid: {plan_path}")


def command_plan_run(repo_root: Path, args):
    plan, _ = load_plan_from_change(str(repo_root), args.change)
    state = run_plan(
        plan,
        {
            "resume": args.resume,
            "fromAction": args.from_action,
        },
    )
    done = sum(1 for a in state["actions"] if a["status"] == "SUCCESS")
    failed = sum(1 for a in state["actions"] if a["status"] == "FAILED")
    print(f"Run {state['runId']}: {done}/{len(state['actions'])} successful, {failed} failed, status={state['status']}")


def command_plan_status(repo_root: Path, args):
    change_dir = resolve_change_dir(str(repo_root), args.change)
    state = load_latest_run_state(str(change_dir))
    if not state:
        print("No run-state found.")
        return

    done = sum(1 for a in state["actions"] if a["status"] == "SUCCESS")
    print(f"Change: {args.change}")
    print(f"Run: {state['runId']}")
    print(f"Status: {state['status']}")
    print(f"Progress: {done}/{len(state['actions'])}")
    for action in state["actions"]:
        suffix = f" ({action['error']['message']})" if action.get("error") else ""
        print(f"- {action['id']} [{action['status']}]{suffix}")


def build_parser():
    parser = argparse.ArgumentParser(prog="superspec")
    sub = parser.add_subparsers(dest="group")

    change = sub.add_parser("change")
    change_sub = change.add_subparsers(dest="sub")
    change_new = change_sub.add_parser("new")
    change_new.add_argument("change")
    change_new.add_argument("--summary")

    plan = sub.add_parser("plan")
    plan_sub = plan.add_subparsers(dest="sub")

    plan_init = plan_sub.add_parser("init")
    plan_init.add_argument("change")

    plan_validate = plan_sub.add_parser("validate")
    plan_validate.add_argument("change")

    plan_run = plan_sub.add_parser("run")
    plan_run.add_argument("change")
    plan_run.add_argument("--resume", action="store_true")
    plan_run.add_argument("--from", dest="from_action")

    plan_status = plan_sub.add_parser("status")
    plan_status.add_argument("change")

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
        if args.group == "plan" and args.sub == "run":
            command_plan_run(repo_root, args)
            return
        if args.group == "plan" and args.sub == "status":
            command_plan_status(repo_root, args)
            return

        parser.print_help()
        raise SystemExit(1)
    except Exception as exc:  # noqa: BLE001
        print(f"Error: {exc}")
        raise SystemExit(1) from exc


if __name__ == "__main__":
    main()
