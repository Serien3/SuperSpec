# SuperSpec CLI

## Global Options

| option         | description                                       |
| -------------- | ------------------------------------------------- |
| `-h`, `--help` | 显示帮助信息（适用于 `superspec` 及各级子命令）。 |

## Human-Only Commands

### `superspec init`

初始化当前仓库的 SuperSpec/OpenSpec 基础环境，并同步内置 skills 到 `.codex/skills`。

```bash
superspec init [options]
```

**Options:**

| option    | description                      | default  |
| --------- | -------------------------------- | -------- |
| `--agent` | 代理类型（当前仅支持 `codex`）。 | Required |

### `superspec validate`

校验 workflow 文件是否符合 SuperSpec 支持的模板/字段约束。

```bash
superspec validate [options]
```

**Options:**

| option     | description                                                             | default |
| ---------- | ----------------------------------------------------------------------- | ------- |
| `--schema` | workflow 名称（`superspec/schemas/workflows/<schema>.workflow.json`）。 | `None`  |
| `--file`   | workflow 文件路径（绝对路径或相对仓库路径）。                           | `None`  |
| `--json`   | 输出机器可读 JSON（`ok/errors/warnings`）。                             | `false` |

> `--schema` 与 `--file` 必须且只能提供一个。

## Git Commands

### `superspec git create-worktree`

创建 git worktree 并输出状态 JSON。

| option     | description                       | default  |
| ---------- | --------------------------------- | -------- |
| `--slug`   | 分支命名短标识。                  | Required |
| `--base`   | 基线分支/引用。                   | `""`     |
| `--branch` | 显式分支名。                      | `""`     |
| `--path`   | worktree 路径（绝对或仓库相对）。 | `""`     |

### `superspec git finish-worktree`

合并和/或清理 worktree，并输出结果 JSON。

| option             | description                    | default |
| ------------------ | ------------------------------ | ------- |
| `--slug`           | 目标 worktree slug。           | `""`    |
| `--yes`            | 实际执行（不加则仅预览）。     | `false` |
| `--merge`          | 执行合并流程。                 | `false` |
| `--cleanup`        | 执行清理流程。                 | `false` |
| `--strategy`       | 合并策略：`merge` / `squash`。 | `merge` |
| `--commit-message` | 合并提交信息。                 | `""`    |

## Change Commands

## Plan Commands

### `superspec plan init <change> --schema <schema>`

生成 `openspec/changes/<change>/plan.json`。

| option     | description          | default  |
| ---------- | -------------------- | -------- |
| `--schema` | plan workflow 名称。 | Required |

### `superspec plan next <change>`

拉取下一个可执行 action。

| option    | description    | default |
| --------- | -------------- | ------- |
| `--owner` | 执行者标识。   | `agent` |
| `--debug` | 返回调试字段。 | `false` |
| `--json`  | JSON 输出。    | `false` |

### `superspec plan complete <change> <action_id> --output-json <json-object>`

将 action 标记为完成并提交输出 payload。

### `superspec plan fail <change> <action_id> --error-json <json-object>`

将 action 标记为失败并提交错误 payload。

### `superspec plan approve <change> <action_id>`

人类审批通过快捷命令（内部映射为 `complete`，`executor=human`）。

| option      | description | default |
| ----------- | ----------- | ------- |
| `--summary` | 审批备注。  | `""`    |

### `superspec plan reject <change> <action_id>`

人类审批拒绝快捷命令（内部映射为 `fail`，`executor=human`）。

| option      | description  | default                 |
| ----------- | ------------ | ----------------------- |
| `--code`    | 拒绝错误码。 | `human_rejected`        |
| `--message` | 拒绝信息。   | `human review rejected` |

### `superspec plan status <change>`

查询执行状态、进度和 action 列表。

| option           | description                    | default |
| ---------------- | ------------------------------ | ------- |
| `--json`         | JSON 输出。                    | `false` |
| `--debug`        | 返回协议调试字段。             | `false` |
| `--full`         | 返回完整 action 对象。         | `false` |
| `--action-limit` | 精简模式返回 action 摘要上限。 | `40`    |
