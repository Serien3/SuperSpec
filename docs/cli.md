# SuperSpec CLI

## Global Options

**Options:**
| option         | description                                       |
| -------------- | ------------------------------------------------- |
| `-h`, `--help` | 显示帮助信息（适用于 `superspec` 及各级子命令）。 |
| `-v`, `--version` | 显示 SuperSpec 版本号并退出。                  |

## Init Commands

### `superspec init`

初始化当前仓库的 SuperSpec 基础环境。

```bash
superspec init [options]
```

**Options:**
| option    | description                      | default  |
| --------- | -------------------------------- | -------- |
| `--agent` | 代理类型（当前仅支持 `codex`）。 | Required |

**Behavior:**
| 行为 | 说明 |
| ---- | ---- |
| 目录初始化 | 创建 `superspec/changes/archive` 与 `superspec/specs`（已存在则复用）。 |
| 同步技能 | 将内置 skills 同步到 `.codex/skills`。 |
| 同步代理配置 | 将内置 `agents/*` 同步到仓库根目录 `agents/`，并同步内置 config 到 `.codex/`。 |

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
| option     | description                       | default  |
| ---------- | --------------------------------- | -------- |
| `--slug`   | 分支命名短标识。                  | Required |
| `--base`   | 基线分支/引用。                   | `""`     |
| `--branch` | 显式分支名。                      | `""`     |
| `--path`   | worktree 路径（绝对或仓库相对）。 | `""`     |

### `superspec git finish-worktree`

合并和/或清理 worktree，并输出结果 JSON。

```bash
superspec git finish-worktree [options]
```

**Options:**
| option             | description                    | default |
| ------------------ | ------------------------------ | ------- |
| `--slug`           | 目标 worktree slug。           | `""`    |
| `--yes`            | 实际执行（不加则仅预览）。     | `false` |
| `--merge`          | 执行合并流程。                 | `false` |
| `--cleanup`        | 执行清理流程。                 | `false` |
| `--strategy`       | 合并策略：`merge` / `squash`。 | `merge` |
| `--commit-message` | 合并提交信息。                 | `""`    |

### `superspec git commit`

执行一次 `git commit`，并把本次提交信息写入指定 change 的运行态 `execution/state.json`。

```bash
superspec git commit <change> --message "<commit message>"
```

**Arguments:**
| Argument   | description               | default  |
| ---------- | ------------------------- | -------- |
| `<change>` | 要写入运行态的 change 名。 | Required |

**Options:**
| option      | description | default  |
| ----------- | ----------- | -------- |
| `--message` | commit 信息 | Required |

**Behavior:**
| 行为 | 说明 |
| ---- | ---- |
| 执行 commit | 在仓库根目录执行 `git commit -m <message>`。 |
| 写入运行态 | 将 `state.commit_by_superspec_last` 更新为 `{ \"commit_hash\": \"...\", \"message\": \"...\" }`。 |
| 校验状态 | 若 `execution/state.json` 不存在，或 state 非 `running`，则命令失败。 |

## Change Commands

### `superspec change advance`

统一入口：列出 change、推进现有 change，或创建并推进新 change。

```bash
superspec change advance [<change>] [--new <workflow-type>/<change-name>] [--owner <owner>] [--json]
```

**Modes:**
| 模式 | 用法 | 说明 |
| ---- | ---- | ---- |
| 列表模式 | `superspec change advance` | 列出当前 changes。 |
| 推进模式 | `superspec change advance <change>` | 拉取下一个可执行 action。 |
| 创建并推进 | `superspec change advance --new <type>/<name>` | 使用 `<type>` 选择 workflow，创建 `superspec/changes/<name>/plan.json` 并立即执行一次 next pull。 |

**Options:**
| option    | description | default |
| --------- | ----------- | ------- |
| `--new`   | 新建选择器，格式 `workflow-type/change-name`。 | `None` |
| `--owner` | 执行者标识。 | `agent` |
| `--json`  | JSON 输出。 | `false` |

> 不允许同时提供 `<change>` 和 `--new`。

## Plan Commands

### `superspec plan complete`

将 action 标记为完成并提交输出 payload。

```bash
superspec plan complete <change> <action_id> --output-json <json-object>
```

**Arguments:**
| Argument      | description            | default  |
| ------------- | ---------------------- | -------- |
| `<change>`    | `change`名称           | Required |
| `<action_id>` | 要完成的 action 标识。 | Required |

**Options:**
| option          | description            | default  |
| --------------- | ---------------------- | -------- |
| `--output-json` | 完成输出 JSON 对象。   | Required |

### `superspec plan fail`

将 action 标记为失败并提交错误 payload。

```bash
superspec plan fail <change> <action_id> --error-json <json-object>
```

**Arguments:**
| Argument      | description            | default  |
| ------------- | ---------------------- | -------- |
| `<change>`    | `change`名称           | Required |
| `<action_id>` | 要失败的 action 标识。 | Required |

**Options:**
| option         | description          | default  |
| -------------- | -------------------- | -------- |
| `--error-json` | 失败错误 JSON 对象。 | Required |

### `superspec plan approve`

人类审批通过快捷命令（内部映射为 `complete`，`executor=human`）。

```bash
superspec plan approve <change> <action_id> [options]
```

**Arguments:**
| Argument      | description            | default  |
| ------------- | ---------------------- | -------- |
| `<change>`    | `change`名称           | Required |
| `<action_id>` | 要审批的 action 标识。 | Required |

**Options:**

| option      | description | default |
| ----------- | ----------- | ------- |
| `--summary` | 审批备注。  | `""`    |

### `superspec plan reject`

人类审批拒绝快捷命令（内部映射为 `fail`，`executor=human`）。

```bash
superspec plan reject <change> <action_id> [options]
```

**Arguments:**
| Argument      | description            | default  |
| ------------- | ---------------------- | -------- |
| `<change>`    | `change`名称           | Required |
| `<action_id>` | 要拒绝的 action 标识。 | Required |

**Options:**

| option      | description  | default                 |
| ----------- | ------------ | ----------------------- |
| `--code`    | 拒绝错误码。 | `human_rejected`        |
| `--message` | 拒绝信息。   | `human review rejected` |

### `superspec plan status`

查询执行状态、进度和 action 列表。

```bash
superspec plan status <change> [options]
```

**Arguments:**
| Argument   | description  | default  |
| ---------- | ------------ | -------- |
| `<change>` | `change`名称 | Required |

**Options:**
| option           | description                    | default |
| ---------------- | ------------------------------ | ------- |
| `--json`         | JSON 输出。                    | `false` |
| `--debug`        | 返回协议调试字段。             | `false` |
| `--full`         | 与 `--json` 一起使用时返回完整 action 对象。 | `false` |
| `--action-limit` | 精简模式返回 action 摘要上限。 | `40`    |

**JSON 输出规则:**
| 条件 | 输出 |
| ---- | ---- |
| `--json` 且未开启 `--full/--debug` | 精简对象：`changeName/status/progress` |
| `--json` 且开启 `--full` 或 `--debug` | 完整协议 payload |
