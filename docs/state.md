# SuperSpec State Snapshot

`superspec/changes/<change>/execution/state.json` 使用以下结构：

```json
{
  "meta": {
    "schemaVersion": "https://superspec.dev/schemas/workflow-v1.json",
    "workflowId": "<workflow-id>",
    "workflowDescription": "<workflow-description|null>"
  },
  "runtime": {
    "changeName": "<change-name>",
    "status": "running|success|failed",
    "startedAt": "<iso-8601>",
    "updatedAt": "<iso-8601>",
    "finishedAt": "<iso-8601|null>",
    "actions": []
  }
}
```

## 字段约束

- `meta` 只保存 workflow 身份信息，不包含 `workflowVersion`、`createdAt`、`updatedAt`。
- `meta.schemaVersion` 来自 `workflow.schema.json` 的 `$id`（当前为 `https://superspec.dev/schemas/workflow-v1.json`）。
- `runtime.updatedAt` 在每次协议写入（`next/complete/fail`）时刷新。
- `runtime.actions[*]` 的执行状态只允许：`PENDING`、`READY`、`RUNNING`、`SUCCESS`、`FAILED`。
