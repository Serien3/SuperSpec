import argparse
import json
import shutil
import subprocess
from importlib import metadata
from pathlib import Path

from superspec import __version__
from superspec.engine.errors import ProtocolError
from superspec.engine.git_ops import commit_for_change
from superspec.engine.orchestrator import run_protocol_action_from_cli, to_json
from superspec.engine.plan_loader import resolve_change_dir
from superspec.engine.workflow_loader import build_plan_from_workflow, validate_workflow_source
from superspec.engine.validator import validate_plan
from superspec.scripts.worktree_create import create_worktree_state
from superspec.scripts.worktree_finish import finish_worktree_flow

AGENT_CONFIG_DIR_MAP = {
    "codex": ".codex",
}


def _resolve_version():
    try:
        return metadata.version("superspec")
    except metadata.PackageNotFoundError:
        return __version__


def _copy_children(source: Path, target: Path):
    target.mkdir(parents=True, exist_ok=True)
    copied = 0
    for item in source.iterdir():
        dest = target / item.name
        if item.is_dir():
            shutil.copytree(item, dest, dirs_exist_ok=True)
            copied += 1
        elif item.is_file():
            shutil.copy2(item, dest)
            copied += 1
    return copied


def _write_plan(repo_root: Path, change_name: str, schema: str | None):
    change_dir = resolve_change_dir(str(repo_root), change_name)
    change_dir.mkdir(parents=True, exist_ok=True)
    plan_path = change_dir / "plan.json"

    plan, selected_schema, _ = build_plan_from_workflow(
        repo_root,
        change_name,
        schema=schema,
    )
    validate_plan(plan)
    plan_path.write_text(f"{json.dumps(plan, indent=2, ensure_ascii=True)}\n", encoding="utf-8")
    return plan_path, selected_schema


def _run_openspec_new_change(repo_root: Path, change_name: str):
    cmd = ["openspec", "new", "change", change_name]
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


def _skills_source_dir():
    package_skills = Path(__file__).resolve().parent / "skills"
    if package_skills.exists() and package_skills.is_dir():
        return package_skills

    raise RuntimeError("No packaged skills directory found.")


def _agents_source_dir():
    package_agents = Path(__file__).resolve().parent / "agents"
    if package_agents.exists() and package_agents.is_dir():
        return package_agents

    raise RuntimeError("No packaged agents directory found.")


def _config_source_dir():
    package_config = Path(__file__).resolve().parent / "config"
    if package_config.exists() and package_config.is_dir():
        return package_config

    raise RuntimeError("No packaged config directory found.")


def _agent_config_dir(repo_root: Path, agent: str):
    try:
        config_dir = AGENT_CONFIG_DIR_MAP[agent]
    except KeyError as exc:
        raise ProtocolError(f"Unsupported agent. Only {', '.join(sorted(AGENT_CONFIG_DIR_MAP.keys()))} is supported.", code="invalid_payload") from exc
    return repo_root / config_dir


def _sync_skills_for_agent(repo_root: Path, agent: str):
    source = _skills_source_dir()
    target = _agent_config_dir(repo_root, agent) / "skills"
    copied = _copy_children(source, target)
    return source, target, copied


def _sync_agents_to_repo_root(repo_root: Path):
    source = _agents_source_dir()
    target = repo_root / "agents"
    copied = _copy_children(source, target)
    return source, target, copied


def _sync_config_for_agent(repo_root: Path, agent: str):
    source = _config_source_dir()
    target = _agent_config_dir(repo_root, agent)
    copied = _copy_children(source, target)
    return source, target, copied


def command_init(repo_root: Path, args):
    _agent_config_dir(repo_root, args.agent)

    cmd = ["openspec", "init", "--tools", args.agent]
    result = subprocess.run(cmd, cwd=repo_root, text=True, capture_output=True)
    if result.returncode != 0:
        raise RuntimeError(result.stderr or result.stdout or "openspec init failed")
    print(result.stdout, end="")

    _sync_skills_for_agent(repo_root, args.agent)
    _sync_agents_to_repo_root(repo_root)
    _sync_config_for_agent(repo_root, args.agent)
    print(f"SuperSpec initialization succeeded (agent={args.agent}).")


def command_change_new(repo_root: Path, args):
    _run_openspec_new_change(repo_root, args.change)
    print(f"Plan not initialized for change '{args.change}'.")
    print(f"Run: superspec plan init {args.change} --schema <schema>")


def command_changelist(repo_root: Path, args):
    changes_root = repo_root / "openspec" / "changes"
    if not changes_root.exists():
        print("No changes found.")
        return

    changes = sorted(item.name for item in changes_root.iterdir() if item.is_dir())
    if not changes:
        print("No changes found.")
        return

    for change_name in changes:
        print(change_name)


def command_plan_init(repo_root: Path, args):
    plan_path, selected_schema = _write_plan(repo_root, args.change, args.schema)
    print(f"Initialized {plan_path} (schema={selected_schema})")


def command_validate(repo_root: Path, args):
    payload = validate_workflow_source(
        repo_root,
        schema=args.schema,
        workflow_file=args.file,
    )
    if args.json:
        print(to_json(payload))
    elif payload["ok"]:
        print(f"Workflow is valid: {payload['target']}")
    else:
        print(f"Workflow validation failed: {payload.get('target') or '<unknown>'}")
        for error in payload.get("errors", []):
            hint = f" (hint: {error['hint']})" if error.get("hint") else ""
            print(f"- [{error['code']}] {error['path']}: {error['message']}{hint}")

    if not payload["ok"]:
        raise SystemExit(1)


def command_git_worktree_create(repo_root: Path, args):
    state = create_worktree_state(
        repo_root=repo_root,
        slug=args.slug,
        base=args.base,
        branch=args.branch,
        path=args.path,
    )
    print(json.dumps(state, ensure_ascii=False, indent=2))


def command_git_worktree_finish(repo_root: Path, args):
    payload = finish_worktree_flow(
        slug=args.slug,
        yes=bool(args.yes),
        merge=bool(args.merge),
        cleanup=bool(args.cleanup),
        strategy=args.strategy,
        commit_message=args.commit_message,
    )
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def command_git_commit(repo_root: Path, args):
    payload = commit_for_change(
        repo_root=repo_root,
        change_name=args.change,
        message=args.message,
    )
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def command_plan_next(repo_root: Path, args):
    payload = run_protocol_action_from_cli(
        repo_root,
        args.change,
        "next",
        owner=args.owner,
    )
    if args.json:
        print(to_json(payload))
    else:
        action = payload.get("action") or {}
        print(action.get("prompt") or payload.get("state", ""))


def command_plan_complete(repo_root: Path, args):
    output_payload = _parse_object_json(args.output_json, "output-json")
    run_protocol_action_from_cli(
        repo_root,
        args.change,
        "complete",
        action_id=args.action_id,
        output_payload=output_payload,
    )
    print(f"Action {args.action_id} marked complete.")


def command_plan_fail(repo_root: Path, args):
    error_payload = _parse_object_json(args.error_json, "error-json")
    run_protocol_action_from_cli(
        repo_root,
        args.change,
        "fail",
        action_id=args.action_id,
        error_payload=error_payload,
    )
    print(f"Action {args.action_id} marked failed.")


def command_plan_approve(repo_root: Path, args):
    output_payload = {
        "ok": True,
        "executor": "human",
        "actionId": args.action_id,
    }
    if args.summary:
        output_payload["summary"] = args.summary

    run_protocol_action_from_cli(
        repo_root,
        args.change,
        "complete",
        action_id=args.action_id,
        output_payload=output_payload,
    )
    print(f"Action {args.action_id} approved.")


def command_plan_reject(repo_root: Path, args):
    error_payload = {
        "code": args.code,
        "message": args.message,
        "executor": "human",
    }
    run_protocol_action_from_cli(
        repo_root,
        args.change,
        "fail",
        action_id=args.action_id,
        error_payload=error_payload,
    )
    print(f"Action {args.action_id} rejected.")


def command_plan_status(repo_root: Path, args):
    payload = run_protocol_action_from_cli(
        repo_root,
        args.change,
        "status",
        debug=bool(args.debug),
        compact=(not bool(args.full)),
        action_limit=int(args.action_limit),
    )
    if args.json:
        if args.full or args.debug:
            print(to_json(payload))
            return
        minimal = {
            "changeName": payload["changeName"],
            "status": payload["status"],
            "progress": payload["progress"],
        }
        print(to_json(minimal))
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
    parser.add_argument("-v", "--version", action="version", version=f"%(prog)s {_resolve_version()}")
    sub = parser.add_subparsers(dest="group")

    init = sub.add_parser("init")
    init.add_argument("--agent", choices=["codex"], required=True)

    change = sub.add_parser("change")
    change_sub = change.add_subparsers(dest="sub")
    change_new = change_sub.add_parser("new")
    change_new.add_argument("change")
    change_sub.add_parser("list")

    plan = sub.add_parser("plan")
    plan_sub = plan.add_subparsers(dest="sub")

    plan_init = plan_sub.add_parser("init")
    plan_init.add_argument("change")
    plan_init.add_argument("--schema", required=True)

    plan_next = plan_sub.add_parser("next")
    plan_next.add_argument("change")
    plan_next.add_argument("--owner", default="agent")
    plan_next.add_argument("--json", action="store_true")

    plan_complete = plan_sub.add_parser("complete")
    plan_complete.add_argument("change")
    plan_complete.add_argument("action_id")
    plan_complete.add_argument("--output-json", required=True)

    plan_fail = plan_sub.add_parser("fail")
    plan_fail.add_argument("change")
    plan_fail.add_argument("action_id")
    plan_fail.add_argument("--error-json", required=True)

    plan_approve = plan_sub.add_parser("approve")
    plan_approve.add_argument("change")
    plan_approve.add_argument("action_id")
    plan_approve.add_argument("--summary", default="")

    plan_reject = plan_sub.add_parser("reject")
    plan_reject.add_argument("change")
    plan_reject.add_argument("action_id")
    plan_reject.add_argument("--code", default="human_rejected")
    plan_reject.add_argument("--message", default="human review rejected")

    plan_status = plan_sub.add_parser("status")
    plan_status.add_argument("change")
    plan_status.add_argument("--json", action="store_true")
    plan_status.add_argument("--debug", action="store_true")
    plan_status.add_argument("--full", action="store_true", help="Return full action objects in JSON output.")
    plan_status.add_argument(
        "--action-limit",
        type=int,
        default=40,
        help="Compact JSON mode: max number of action summaries to include.",
    )

    validate = sub.add_parser("validate")
    validate.add_argument("--schema")
    validate.add_argument("--file")
    validate.add_argument("--json", action="store_true")

    git = sub.add_parser("git")
    git_sub = git.add_subparsers(dest="sub")
    git_worktree_create = git_sub.add_parser(
        "create-worktree",
        help="Create a git worktree and persist creation state.",
    )
    git_worktree_create.add_argument("--slug", required=True, help="Short slug for branch naming.")
    git_worktree_create.add_argument("--base", default="", help="Base branch/ref (defaults to current branch).")
    git_worktree_create.add_argument("--branch", default="", help="Explicit branch name to create or reuse.")
    git_worktree_create.add_argument("--path", default="", help="Worktree path (absolute or repo-relative).")
    git_worktree_finish = git_sub.add_parser(
        "finish-worktree",
        help="Merge and/or clean up a git worktree from saved state.",
    )
    git_worktree_finish.add_argument("--slug", default="", help="Slug of target worktree state (optional).")
    git_worktree_finish.add_argument(
        "--yes",
        action="store_true",
        help="Actually perform actions. Without this, only prints plan.",
    )
    git_worktree_finish.add_argument(
        "--merge",
        action="store_true",
        help="Merge branch into merge target in the main worktree.",
    )
    git_worktree_finish.add_argument(
        "--cleanup",
        action="store_true",
        help="Remove worktree and delete branch (safe delete).",
    )
    git_worktree_finish.add_argument(
        "--strategy",
        default="merge",
        choices=["merge", "squash"],
        help="Merge strategy.",
    )
    git_worktree_finish.add_argument(
        "--commit-message",
        default="",
        help="Commit message for merge/squash workflow.",
    )
    git_commit = git_sub.add_parser(
        "commit",
        help="Run git commit and persist commit metadata to change execution state.",
    )
    git_commit.add_argument("change", help="Target change name whose execution state will be updated.")
    git_commit.add_argument("--message", required=True, help="Commit message.")

    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()
    repo_root = Path.cwd()

    try:
        if args.group == "init":
            command_init(repo_root, args)
            return
        if args.group == "change" and args.sub == "new":
            command_change_new(repo_root, args)
            return
        if args.group == "change" and args.sub == "list":
            command_changelist(repo_root, args)
            return
        if args.group == "plan" and args.sub == "init":
            command_plan_init(repo_root, args)
            return
        if args.group == "validate":
            command_validate(repo_root, args)
            return
        if args.group == "git" and args.sub == "create-worktree":
            command_git_worktree_create(repo_root, args)
            return
        if args.group == "git" and args.sub == "finish-worktree":
            command_git_worktree_finish(repo_root, args)
            return
        if args.group == "git" and args.sub == "commit":
            command_git_commit(repo_root, args)
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
        if args.group == "plan" and args.sub == "approve":
            command_plan_approve(repo_root, args)
            return
        if args.group == "plan" and args.sub == "reject":
            command_plan_reject(repo_root, args)
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
