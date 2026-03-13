# SuperSpec CLI

## Global Options

**Options:**
| option            | description                                       |
| ----------------- | ------------------------------------------------- |
| `-h`, `--help`    | 显示帮助信息（适用于 `superspec` 及各级子命令）。 |
| `-v`, `--version` | 显示 SuperSpec 版本号并退出。                     |

## Core Commands

### `superspec init`

初始化当前仓库的 SuperSpec 基础环境。

**Behavior:**
| 行为         | 说明                                                                           |
| ------------ | ------------------------------------------------------------------------------ |
| 目录初始化   | 创建 `superspec/changes/archive` 与 `superspec/specs`（已存在则复用）。        |
| 同步技能     | 将内置 skills 同步到 `.codex/skills`。                                         |
| 同步代理配置 | 将内置 `agents/*` 同步到仓库根目录 `agents/`，并同步内置 config 到 `.codex/`。 |

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

```bash
superspec git create-worktree [options]
```

**Options:**
| option     | description                               | default              |
| ---------- | ----------------------------------------- | -------------------- |
| `--slug`   | 分支命名短标识。                          | Required             |
| `--base`   | 基线分支/引用。未提供时自动推断当前分支。 | 当前分支（自动推断） |
| `--branch` | 显式分支名。                              | `""`                 |
| `--path`   | worktree 路径（绝对或仓库相对）。         | `""`                 |

### `superspec git finish-worktree`

合并和/或清理 worktree，并输出结果 JSON。

**Behavior:**
| 行为         | 说明                                                                     |
| ------------ | ------------------------------------------------------------------------ |
| 预览执行     | 未提供 `--yes` 时仅输出计划，不执行。                                    |
| 合并前检查   | `--merge` 执行前要求主工作区无未提交改动。                               |
| 提交信息约束 | `--merge` 且策略为 `merge` 或 `squash` 时，`--commit-message` 不能为空。 |
| 清理确认     | `--yes --cleanup` 且未启用 `--merge` 时，执行期会二次确认。              |

```bash
superspec git finish-worktree [options]
```

**Options:**
| option             | description                      | default |
| ------------------ | -------------------------------- | ------- |
| `--slug`           | 目标 worktree slug。             | `""`    |
| `--yes`            | 实际执行（不加则仅预览）。       | `false` |
| `--merge`          | 执行合并流程。                   | `false` |
| `--cleanup`        | 执行清理流程。                   | `false` |
| `--strategy`       | 合并策略：`merge` / `squash`。   | `merge` |
| `--commit-message` | 合并提交信息（执行合并时必填）。 | `""`    |


### `superspec git commit`

执行一次 `git commit`，并把本次提交涉及的文件路径合并写入指定 change 的运行态 `execution/state.json` 的 `runtime.files_changed`。

```bash
superspec git commit <change> --message "<commit message>"
```

**Behavior:**
| 行为        | 说明                                                                                  |
| ----------- | ------------------------------------------------------------------------------------- |
| 执行 commit | 在仓库根目录执行 `git commit -m <message>`。                                          |
| 写入运行态  | 读取本次 `HEAD` 提交涉及的文件，并合并写入 `state.json.runtime.files_changed`。       |
| 合并规则    | 若 `runtime.files_changed` 已存在，则保留已有条目，只追加当前提交中不重合的文件路径。 |
| 校验状态    | 若 `execution/state.json` 不存在，或 state 非 `running`，则命令失败。                 |

**Arguments:**
| Argument   | description                                   | default  |
| ---------- | --------------------------------------------- | -------- |
| `<change>` | 要更新 `runtime.files_changed` 的 change 名。 | Required |

**Options:**
| option      | description | default  |
| ----------- | ----------- | -------- |
| `--message` | commit 信息 | Required |



## Change Commands

### `superspec change list`

列出所有未归档 change。

```bash
superspec change list
```

### `superspec change advance`

推进现有 change，或创建并推进新 change。

```bash
superspec change advance [<change>] [--new <workflow-type>/<change-name>] [--goal "<one-line goal>"] [--owner <owner>] [--json]
```

**Modes:**
| 模式       | 用法                                           | 说明                                                                                                                           |
| ---------- | ---------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------ |
| 推进模式   | `superspec change advance <change>`            | 拉取下一个可执行 step。                                                                                                        |
| 创建并推进 | `superspec change advance --new <type>/<name>` | 使用 `<type>` 选择 workflow，初始化 `superspec/changes/<name>/execution/state.json` 与 `events.log` 并立即执行一次 next pull。 |
| 列表模式   | `superspec change advance`                     | 列出所有未归档 change。                                                                                                        |

**Options:**
| option    | description                                    | default |
| --------- | ---------------------------------------------- | ------- |
| `--new`   | 新建选择器，格式 `workflow-type/change-name`。 | `None`  |
| `--goal`  | 创建新 change 时写入 `runtime.goal` 的一句话目标。 | `None`  |
| `--owner` | 执行者标识。                                   | `agent` |
| `--json`  | JSON 输出。                                    | `false` |

> 不允许同时提供 `<change>` 和 `--new`。

**`--json` 返回说明：**
- 顶层字段固定为 `change`、`goal`、`state`、`step`。
- `goal` 来自 `execution/state.json.runtime.goal`，未设置时为 `null`。
- `step` 总是包含 `stepId` 和 `prompt`。
- `script` step 额外返回 `script_command`。
- `skill` step 额外返回 `skillName`。
- `human` step 可额外返回 `option`。
- `step` 不再返回 `executor` 字段；执行方式由返回字段本身决定。

### `superspec change status`

查询执行状态、进度和 step 列表。

```bash
superspec change status <change> [options]
```

**Arguments:**
| Argument   | description  | default  |
| ---------- | ------------ | -------- |
| `<change>` | `change`名称 | Required |

**Options:**
| option         | description                                | default |
| -------------- | ------------------------------------------ | ------- |
| `--json`       | JSON 输出。                                | `false` |
| `--debug`      | 返回协议调试字段。                         | `false` |
| `--full`       | 与 `--json` 一起使用时返回完整 step 对象。 | `false` |
| `--step-limit` | 精简模式返回 step 摘要上限。               | `40`    |

**JSON 输出规则:**
| 条件                                  | 输出                                   |
| ------------------------------------- | -------------------------------------- |
| `--json` 且未开启 `--full/--debug`    | 精简对象：`changeName/status/progress` |
| `--json` 且开启 `--full` 或 `--debug` | 完整协议 payload                       |

### `superspec change stepComplete`

将 step 标记为完成。

```bash
superspec change stepComplete <change> <step_id>
```

**Arguments:**
| Argument    | description          | default  |
| ----------- | -------------------- | -------- |
| `<change>`  | `change`名称         | Required |
| `<step_id>` | 要完成的 step 标识。 | Required |

### `superspec change stepFail`

将 step 标记为失败。

```bash
superspec change stepFail <change> <step_id>
```

**Arguments:**
| Argument    | description          | default  |
| ----------- | -------------------- | -------- |
| `<change>`  | `change`名称         | Required |
| `<step_id>` | 要失败的 step 标识。 | Required |
