import argparse
import json
import shutil
from importlib import metadata
from pathlib import Path

from superspec import __version__
from superspec.engine.errors import ProtocolError
from superspec.engine.git_ops import commit_for_change
from superspec.engine.orchestrator import run_protocol_action_from_cli, to_json
from superspec.engine.plan_loader import resolve_change_dir, state_path_for_change, validate_change_name
from superspec.engine.state_store import initialize_execution_snapshot
from superspec.engine.workflow_loader import build_plan_from_workflow, validate_workflow_source, workflow_schema_version
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


def _write_execution_snapshot(repo_root: Path, change_name: str, schema: str | None):
    change_dir = resolve_change_dir(str(repo_root), change_name)
    change_dir.mkdir(parents=True, exist_ok=True)

    runtime_blueprint, selected_schema, _ = build_plan_from_workflow(
        repo_root,
        change_name,
        schema=schema,
    )
    initialize_execution_snapshot(
        str(change_dir),
        runtime_blueprint,
        workflow_schema_version=workflow_schema_version(),
    )
    return state_path_for_change(str(repo_root), change_name), selected_schema


def _parse_new_selector(raw: str):
    if not isinstance(raw, str) or not raw.strip():
        raise ProtocolError(
            "Invalid --new value: expected '<workflow-type>/<change-name>'.",
            code="invalid_selector",
            details={"selector": raw},
        )
    parts = raw.split("/", 1)
    if len(parts) != 2:
        raise ProtocolError(
            "Invalid --new value: expected '<workflow-type>/<change-name>'.",
            code="invalid_selector",
            details={"selector": raw},
        )
    workflow_type, local_name = parts[0].strip(), parts[1].strip()
    if not workflow_type or not local_name:
        raise ProtocolError(
            "Invalid --new value: expected '<workflow-type>/<change-name>'.",
            code="invalid_selector",
            details={"selector": raw},
        )
    if "/" in local_name:
        raise ProtocolError(
            "Invalid --new value: expected exactly one slash in '<workflow-type>/<change-name>'.",
            code="invalid_selector",
            details={"selector": raw},
        )
    validate_change_name(workflow_type)
    validate_change_name(local_name)
    return workflow_type, local_name


def _bound_workflow_id(change_dir: Path):
    snapshot_path = change_dir / "execution" / "state.json"
    if not snapshot_path.exists():
        return None
    try:
        snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    meta = snapshot.get("meta") if isinstance(snapshot, dict) else None
    workflow_id = meta.get("workflowId") if isinstance(meta, dict) else None
    return workflow_id if isinstance(workflow_id, str) and workflow_id else None


def _create_change_with_workflow(repo_root: Path, selector: str):
    workflow_type, change_name = _parse_new_selector(selector)
    change_dir = resolve_change_dir(str(repo_root), change_name)
    if change_dir.exists():
        bound = _bound_workflow_id(change_dir)
        if bound and bound != workflow_type:
            raise ProtocolError(
                f"Change '{change_name}' is already bound to workflow '{bound}'.",
                code="workflow_binding_conflict",
                details={"change": change_name, "existing": bound, "requested": workflow_type},
            )
        raise ProtocolError(
            f"Change '{change_name}' already exists.",
            code="change_exists",
            details={"change": change_name, "path": str(change_dir)},
        )
    state_path, selected_schema = _write_execution_snapshot(repo_root, change_name, workflow_type)
    return change_name, state_path, selected_schema


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
        raise ProtocolError(
            f"Unsupported agent '{agent}'. Supported: {', '.join(sorted(AGENT_CONFIG_DIR_MAP.keys()))}.",
            code="invalid_payload",
        ) from exc
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
    (repo_root / "superspec" / "changes" / "archive").mkdir(parents=True, exist_ok=True)
    (repo_root / "superspec" / "specs").mkdir(parents=True, exist_ok=True)

    _sync_skills_for_agent(repo_root, args.agent)
    _sync_agents_to_repo_root(repo_root)
    _sync_config_for_agent(repo_root, args.agent)
    print(f"SuperSpec initialization succeeded (agent={args.agent}).")


def _print_change_list(repo_root: Path):
    changes_root = repo_root / "superspec" / "changes"
    if not changes_root.exists():
        print("No changes found.")
        return

    changes = sorted(
        item.name
        for item in changes_root.iterdir()
        if item.is_dir() and item.name != "archive"
    )
    if not changes:
        print("No changes found.")
        return
    for change_name in changes:
        print(change_name)


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


def command_change_advance(repo_root: Path, args):
    if args.new and args.change:
        raise ProtocolError(
            "Invalid arguments: provide either --new or <change>, not both.",
            code="invalid_arguments",
        )
    if args.new:
        change_name, _, _ = _create_change_with_workflow(repo_root, args.new)
        payload = run_protocol_action_from_cli(
            repo_root,
            change_name,
            "next",
            owner=args.owner,
        )
        if args.json:
            print(to_json(payload))
        else:
            step = payload.get("step") or {}
            print(step.get("prompt") or payload.get("state", ""))
        return
    if args.change:
        payload = run_protocol_action_from_cli(
            repo_root,
            args.change,
            "next",
            owner=args.owner,
        )
        if args.json:
            print(to_json(payload))
        else:
            step = payload.get("step") or {}
            print(step.get("prompt") or payload.get("state", ""))
        return
    _print_change_list(repo_root)


def command_change_step_complete(repo_root: Path, args):
    run_protocol_action_from_cli(
        repo_root,
        args.change,
        "complete",
        step_id=args.step_id,
    )
    print(f"Step {args.step_id} marked complete.")


def command_change_step_fail(repo_root: Path, args):
    run_protocol_action_from_cli(
        repo_root,
        args.change,
        "fail",
        step_id=args.step_id,
    )
    print(f"Step {args.step_id} marked failed.")


def command_change_status(repo_root: Path, args):
    payload = run_protocol_action_from_cli(
        repo_root,
        args.change,
        "status",
        debug=bool(args.debug),
        compact=(not bool(args.full)),
        step_limit=int(args.step_limit),
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
    for step in payload["steps"]:
        print(f"- {step['id']} [{step['status']}]")


def build_parser():
    parser = argparse.ArgumentParser(prog="superspec")
    parser.add_argument("-v", "--version", action="version", version=f"%(prog)s {_resolve_version()}")
    sub = parser.add_subparsers(dest="group")

    init = sub.add_parser("init")
    init.add_argument("--agent", choices=["codex"], required=True)

    change = sub.add_parser("change")
    change_sub = change.add_subparsers(dest="sub")
    change_advance = change_sub.add_parser("advance")
    change_advance.add_argument("change", nargs="?")
    change_advance.add_argument("--new")
    change_advance.add_argument("--owner", default="agent")
    change_advance.add_argument("--json", action="store_true")
    change_status = change_sub.add_parser("status")
    change_status.add_argument("change")
    change_status.add_argument("--json", action="store_true")
    change_status.add_argument("--debug", action="store_true")
    change_status.add_argument("--full", action="store_true", help="Return full step objects in JSON output.")
    change_status.add_argument(
        "--step-limit",
        type=int,
        default=40,
        help="Compact JSON mode: max number of step summaries to include.",
    )
    change_step_complete = change_sub.add_parser("stepComplete")
    change_step_complete.add_argument("change")
    change_step_complete.add_argument("step_id")
    change_step_fail = change_sub.add_parser("stepFail")
    change_step_fail.add_argument("change")
    change_step_fail.add_argument("step_id")

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
        help="Actually perform steps. Without this, only prints plan.",
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
        if args.group == "change" and args.sub == "advance":
            command_change_advance(repo_root, args)
            return
        if args.group == "change" and args.sub == "status":
            command_change_status(repo_root, args)
            return
        if args.group == "change" and args.sub == "stepComplete":
            command_change_step_complete(repo_root, args)
            return
        if args.group == "change" and args.sub == "stepFail":
            command_change_step_fail(repo_root, args)
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
