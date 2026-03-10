# SuperSpec State Snapshot

`superspec/changes/<change>/execution/state.json` 是当前 change 的执行快照。

当前结构如下：

```json
{
  "meta": {
    "workflowId": "<workflow-id>",
    "version": "<workflow-version|optional>",
    "description": "<workflow-description|optional>",
    "metadata": {}
  },
  "runtime": {
    "changeName": "<change-name>",
    "status": "running|success|failed",
    "startedAt": "<iso-8601>",
    "updatedAt": "<iso-8601>",
    "finishedAt": "<iso-8601|null>",
    "steps": []
  }
}
```

## 字段约束

- `meta` 只包含 workflow 顶层除 `steps` 外的所有字段。
- 对 workflow 顶层必填字段，只要 workflow 合法就一定会出现在 `meta`。
- 对 workflow 顶层可选字段，只有在 workflow 中显式写出时才会出现在 `meta`。
- `meta` 不包含运行期字段，例如 `createdAt`、`updatedAt`、`finishedAt`。
- `runtime.updatedAt` 在每次协议写入（`next/complete/fail`）时刷新。
- `runtime.steps[*]` 的执行状态只允许：`PENDING`、`READY`、`RUNNING`、`SUCCESS`、`FAILED`。
- `runtime.steps[*]` 会保留 step 的执行定义字段，例如 `executor`、`skill`、`script`、`prompt`、`option`。
- `runtime.steps[*]` 不包含 `output`、`error` 字段。
- 在 fail-fast 失败终态下，所有剩余未终结步骤都会被收敛为 `FAILED`，因此终态快照中不应再出现 `PENDING`、`READY` 或 `RUNNING`。

## `meta` 映射规则

如果 workflow 文件是：

```json
{
  "workflowId": "spec-dev",
  "version": "1.1.0",
  "description": "Default spec-dev workflow",
  "metadata": {
    "channel": "default"
  },
  "steps": []
}
```

那么 `state.json.meta` 会是：

```json
{
  "workflowId": "spec-dev",
  "version": "1.1.0",
  "description": "Default spec-dev workflow",
  "metadata": {
    "channel": "default"
  }
}
```

也就是说，当前实现不会对 workflow 顶层字段做重命名，也不会额外注入 `schemaVersion`。
