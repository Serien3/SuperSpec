# State Snapshot

当前 change 的运行态快照位于：

- `superspec/changes/<change>/execution/state.json`

核心约定：

- `meta` 保存 workflow 顶层字段（不含 `steps`）
- `meta.finishPolicy` 是 workflow 的默认 finish 策略，允许值为 `archive`、`delete`、`keep`
- `runtime` 保存执行时状态，例如 `changeName`、`status`、`startedAt`、`updatedAt`、`goal`
- 顶层 `runtime.finishedAt` 当前不存在；`finishedAt` 只存在于 `runtime.steps[*]`

示例：

```json
{
  "meta": {
    "workflowId": "spec-dev",
    "version": "1.2.0",
    "description": "Default spec-dev workflow",
    "finishPolicy": "archive"
  },
  "runtime": {
    "changeName": "demo-change",
    "status": "running",
    "startedAt": "<iso-8601>",
    "updatedAt": "<iso-8601>",
    "steps": []
  }
}
```
