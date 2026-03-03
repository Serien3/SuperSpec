# SuperSpec CLI

## Human-Only Commands

### `superspec init`

初始化当前仓库的 SuperSpec/OpenSpec 基础环境，并同步内置 skills 到 `.codex/skills`。

**Options**

| Options        | Description                    | Default  |
| -------------- | ------------------------------ | -------- |
| `--agent`      | 代理类型。当前仅支持 `codex`。 | Required |
| `-h`, `--help` | 显示帮助信息。                 | `false`  |

### `superspec validate`

校验用户定义的 workflow 模板（`*.workflow.json`）是否符合字段契约并可用于后续 `superspec plan init` 生成计划。

**Options**

| Options        | Description                                                                                        | Default |
| -------------- | -------------------------------------------------------------------------------------------------- | ------- |
| `--schema`     | workflow 名称（解析 `superspec/schemas/workflows/<schema>.workflow.json`，无本地时回退内置模板）。 | `None`  |
| `--file`       | workflow 文件路径（绝对路径或相对当前仓库）。                                                      | `None`  |
| `--json`       | 输出机器可读结果（`ok/errors/warnings`）。                                                         | `false` |
| `-h`, `--help` | 显示帮助信息。                                                                                     | `false` |

> `--schema` 与 `--file` 必须且只能提供一个。\
> **BREAKING**: 该命令语义已替代旧的 `superspec plan validate`（后者已移除）。

## Git Commands

### `superspec git create-worktree`

创建或复用分支并新增 git worktree，同时写入 `git-common-dir/codex-worktree-flow/<slug>.json` 保存该 worktree 的状态。  
若 `<slug>.json` 已存在，命令会报错，避免状态冲突/覆盖。  

**Options**

| Options        | Description                                 | Default                                        |
| -------------- | ------------------------------------------- | ---------------------------------------------- |
| `--slug`       | 分支名短标识（用于自动生成分支名）          | Required                                       |
| `--base`       | 基线分支/引用                               | 使用当前分支，若当前处在其他工作树分支上则报错 |
| `--branch`     | 工作树的分支名                              | 自动生成 `wt/<timestamp>-<slug>`               |
| `--path`       | worktree 路径（支持仓库相对路径或绝对路径） | 当前项目的`.wroktree`文件夹中                  |
| `-h`, `--help` | 显示帮助信息                                | `false`                                        |

### `superspec git finish-worktree`

基于 worktree 状态文件执行收尾操作（预览或执行）：支持合并（`--merge`）、清理（`--cleanup`）或二者组合。
当仅执行 `--cleanup`（未带 `--merge`）且使用 `--yes` 时，命令会先给出风险警示并要求输入 `yes` 确认后才继续。

**Options**

| Options            | Description                                                    | Default   |
| ------------------ | -------------------------------------------------------------- | --------- |
| `--slug`           | 状态文件 slug（解析为 `codex-worktree-flow/<slug>.json`）     | `""`      |
| `--yes`            | 真正执行；不加时只输出 planned 预览                           | `false`   |
| `--merge`          | 在主工作区执行分支合并                                         | `false`   |
| `--cleanup`        | 删除 worktree、删除分支，并删除对应状态文件                   | `false`   |
| `--strategy`       | 合并策略：`merge` 或 `squash`                                 | `merge`   |
| `--commit-message` | 合并提交信息（`merge/squash` 策略都建议显式给出）             | `""`      |
| `-h`, `--help`     | 显示帮助信息                                                   | `false`   |

## Change Commands

### `superspec change new`

创建新的 OpenSpec change 骨架；不会自动初始化计划文件。

**Arguments**

| Arguments | Description                                         | Default  |
| --------- | --------------------------------------------------- | -------- |
| `change`  | 变更名称（用于创建 `openspec/changes/<change>/`）。 | Required |

**Options**

| Options        | Description    | Default |
| -------------- | -------------- | ------- |
| `-h`, `--help` | 显示帮助信息。 | `false` |

## Plan Commands

### `superspec plan init`

基于指定 schema 生成 `openspec/changes/<change>/plan.json`。

**Arguments**

| Arguments | Description | Default  |
| --------- | ----------- | -------- |
| `change`  | 变更名称。  | Required |

**Options**

| Options        | Description        | Default  |
| -------------- | ------------------ | -------- |
| `--schema`     | 计划 schema 名称。 | Required |
| `--title`      | 计划标题覆盖值。   | `None`   |
| `--goal`       | 计划目标覆盖值。   | `None`   |
| `-h`, `--help` | 显示帮助信息。     | `false`  |

### `superspec plan next`

获取下一个可执行 action（Agent 拉取下一步任务的入口）。

**Arguments**

| Arguments | Description | Default  |
| --------- | ----------- | -------- |
| `change`  | 变更名称。  | Required |

**Options**

| Options        | Description                     | Default |
| -------------- | ------------------------------- | ------- |
| `--owner`      | 领取该 action 的执行者标识。    | `agent` |
| `--debug`      | 在返回 payload 中附加调试字段。 | `false` |
| `--json`       | 使用 JSON 输出。                | `false` |
| `-h`, `--help` | 显示帮助信息。                  | `false` |

### `superspec plan complete`

将指定 action 标记为完成，并提交结果 payload。

**Arguments**

| Arguments   | Description          | Default  |
| ----------- | -------------------- | -------- |
| `change`    | 变更名称。           | Required |
| `action_id` | 要完成的 action ID。 | Required |

**Options**

| Options         | Description                  | Default  |
| --------------- | ---------------------------- | -------- |
| `--output-json` | 完成结果的 JSON 对象字符串。 | Required |
| `-h`, `--help`  | 显示帮助信息。               | `false`  |

### `superspec plan fail`

将指定 action 标记为失败，并提交错误 payload。

**Arguments**

| Arguments   | Description              | Default  |
| ----------- | ------------------------ | -------- |
| `change`    | 变更名称。               | Required |
| `action_id` | 要标记失败的 action ID。 | Required |

**Options**

| Options        | Description                  | Default  |
| -------------- | ---------------------------- | -------- |
| `--error-json` | 错误信息的 JSON 对象字符串。 | Required |
| `-h`, `--help` | 显示帮助信息。               | `false`  |

### `superspec plan status`

查询执行状态、进度与动作列表。

**Arguments**

| Arguments | Description | Default  |
| --------- | ----------- | -------- |
| `change`  | 变更名称。  | Required |

**Options**

| Options          | Description                                       | Default |
| ---------------- | ------------------------------------------------- | ------- |
| `--json`         | 使用 JSON 输出。                                  | `false` |
| `--debug`        | 在状态输出中附加 `contracts` 调试字段。           | `false` |
| `--full`         | JSON 输出返回完整 action 对象；默认返回精简摘要。 | `false` |
| `--action-limit` | 精简模式下返回的 action 摘要数量上限。            | `40`    |
| `-h`, `--help`   | 显示帮助信息。                                    | `false` |
