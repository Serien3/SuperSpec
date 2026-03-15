# SuperSpec CLI

## Global Options

| Option            | Description                                  |
| ----------------- | -------------------------------------------- |
| `-h`, `--help`    | Show help for `superspec` or any subcommand. |
| `-v`, `--version` | Print the SuperSpec version and exit.        |

## Core Commands

### `superspec init`

Initialize SuperSpec support files in the current repository.

```bash
superspec init --agent codex
```

**Arguments**

None.

**Options**

| Option    | Description                             | Default  |
| --------- | --------------------------------------- | -------- |
| `--agent` | Agent package to install into the repo. | Required |

Behavior:
- Creates `superspec/changes/archive` and `superspec/specs` if they do not already exist.
- Syncs packaged skills into `.codex/skills`.
- Syncs packaged agent definitions into `.codex/agents`.
- Syncs packaged Codex configuration into `.codex/config.toml`.

### `superspec validate`

Validate a workflow file or a packaged workflow schema.

```bash
superspec validate [--schema <workflow-id> | --file <path>] [--json]
```

**Arguments**

None.

**Options**

| Option     | Description                                                           | Default |
| ---------- | --------------------------------------------------------------------- | ------- |
| `--schema` | Validate a packaged workflow from `src/superspec/schemas/workflows/`. | `None`  |
| `--file`   | Validate a workflow file by path.                                     | `None`  |
| `--json`   | Print machine-readable validation output.                             | `false` |

Notes:
- Provide exactly one of `--schema` or `--file`.
- Non-JSON mode prints a human summary and exits non-zero on validation failure.

### `superspec progress`

Summarize all current-session commit entries in the root `progress.md` into a completed session block.

```bash
superspec progress
```

**Arguments**

None.

**Options**

None.

Behavior:
- Reads commit entries between `<!-- superspec:current-session:start -->` and `<!-- superspec:current-session:end -->`.
- Generates a Markdown summary headed by `## YYYY-MM-DD Session x`.
- Writes `Done`, `Changes`, `Files`, `Next`, and `Finish` sections into `progress.md`.
- Keeps `Current Session` at the top of the file.
- Inserts the newest completed session immediately below `Current Session`.
- Clears the current-session commit ledger after a successful write.
- Fails with a structured protocol error if the current-session block is empty.

## Change Commands

### `superspec change list`

List all active changes.

```bash
superspec change list
```

**Arguments**

None.

**Options**

None.

### `superspec change advance`

Advance an existing change, or create a new change bound to a workflow and immediately pull its next step.

```bash
superspec change advance [<change>] [--new <workflow-type>/<change-name>] [--goal "<one-line goal>"] [--owner <owner>] [--json]
```

Modes:
- `superspec change advance`
  Lists active changes.
- `superspec change advance <change>`
  Pulls the next runnable step for an existing change.
- `superspec change advance --new <workflow>/<change>`
  Creates the change, initializes `execution/state.json`, and immediately executes the first `next` pull.

**Arguments**

| Argument | Description | Default |
| --- | --- | --- |
| `<change>` | Existing change name to advance. | Optional |

**Options**

| Option    | Description                                                                | Default |
| --------- | -------------------------------------------------------------------------- | ------- |
| `--new`   | Create a change bound to a workflow using `<workflow-type>/<change-name>`. | `None`  |
| `--goal`  | Write a one-line goal into `runtime.goal` when creating a change.          | `None`  |
| `--owner` | Owner label returned to the protocol layer.                                | `agent` |
| `--json`  | Print JSON instead of human-readable text.                                 | `false` |

Notes:
- Do not provide both `<change>` and `--new`.
- Compact JSON mode returns `changeName`, `status`, and `progress`.

### `superspec change status`

Read the execution state of a change.

```bash
superspec change status <change> [--json] [--debug] [--full] [--step-limit <n>]
```

**Arguments**

| Argument | Description | Default |
| --- | --- | --- |
| `<change>` | Change name to inspect. | Required |

**Options**

| Option         | Description                                | Default |
| -------------- | ------------------------------------------ | ------- |
| `--json`       | Print JSON output.                         | `false` |
| `--debug`      | Include debug protocol fields.             | `false` |
| `--full`       | With `--json`, include full step objects.  | `false` |
| `--step-limit` | Limit step summaries in compact JSON mode. | `40`    |

### `superspec change stepComplete`

Mark a step as completed.

```bash
superspec change stepComplete <change> <step_id>
```

**Arguments**

| Argument | Description | Default |
| --- | --- | --- |
| `<change>` | Change name to update. | Required |
| `<step_id>` | Step identifier to mark as complete. | Required |

**Options**

None.

### `superspec change stepFail`

Mark a step as failed.

```bash
superspec change stepFail <change> <step_id>
```

**Arguments**

| Argument | Description | Default |
| --- | --- | --- |
| `<change>` | Change name to update. | Required |
| `<step_id>` | Step identifier to mark as failed. | Required |

**Options**

None.


## Git Commands

### `superspec git create-worktree`

Create a git worktree and print a JSON description of the created state.

```bash
superspec git create-worktree --slug <slug> [--base <ref>] [--branch <name>] [--path <path>]
```

**Arguments**

None.

**Options**

| Option     | Description                                              | Default        |
| ---------- | -------------------------------------------------------- | -------------- |
| `--slug`   | Short identifier used for branch naming and saved state. | Required       |
| `--base`   | Base branch or ref.                                      | Current branch |
| `--branch` | Explicit branch name to create or reuse.                 | `""`           |
| `--path`   | Worktree path, absolute or repo-relative.                | `""`           |

### `superspec git finish-worktree`

Preview or execute merge/cleanup operations for a managed worktree.

```bash
superspec git finish-worktree [--slug <slug>] [--yes] [--merge] [--cleanup] [--strategy merge|squash] [--commit-message "<msg>"]
```

**Arguments**

None.

**Options**

| Option             | Description                                       | Default |
| ------------------ | ------------------------------------------------- | ------- |
| `--slug`           | Target worktree slug.                             | `""`    |
| `--yes`            | Execute the plan instead of previewing it.        | `false` |
| `--merge`          | Merge the worktree branch into its target branch. | `false` |
| `--cleanup`        | Remove the worktree and delete the branch safely. | `false` |
| `--strategy`       | Merge strategy.                                   | `merge` |
| `--commit-message` | Commit message for merge or squash flows.         | `""`    |

### `superspec git commit`

Create a Git commit and update SuperSpec session-progress state for a running change.

```bash
superspec git commit <change> --summary "<subject>" [--details "<body>"] --next "<next step>"
```

**Arguments**

| Argument | Description | Default |
| --- | --- | --- |
| `<change>` | Target change whose execution runtime will be updated. | Required |

**Options**

| Option | Description | Default |
| --- | --- | --- |
| `--summary` | Commit subject line. | Required |
| `--details` | Optional commit body narrative. Blank details are omitted from Git body and `progress.md`. | `""` |
| `--next` | Next-step note written into session progress. | Required |

Behavior:
- Runs `git add -A` before committing.
- Creates a Git commit whose subject comes from `--summary`.
- Uses `--details` as the commit body only when it is non-empty.
- Merges files from the resulting `HEAD` commit into `execution/state.json.runtime.files_changed`.
- Appends one normalized commit entry into the root `progress.md` current-session section.
- Includes changed runtime files such as `execution/state.json` and `execution/events.log` if they were part of the staged changes.
- Fails if the target change has no readable `execution/state.json` runtime or is not in `running` state.
