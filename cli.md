# CLI Notes

当前 change 生命周期相关命令：

- `superspec change list`
- `superspec change advance [<change>] [--new <workflow>/<change>] [--goal "..."] [--owner <owner>] [--json]`
- `superspec change status <change> [--json] [--debug] [--full] [--step-limit <n>]`
- `superspec change finish <change> [--archive | --delete | --keep] [--force]`
- `superspec change stepComplete <change> <step_id>`
- `superspec change stepFail <change> <step_id>`

finish 约定：

- 默认按 workflow 顶层 `finishPolicy` 执行
- `--archive`、`--delete`、`--keep` 可显式覆盖默认策略
- 对运行中的 change，`archive` 和 `delete` 需要 `--force`
- `change archive` 已移除

详细 CLI 文档见 [`docs/cli.md`](/home/wzsyh/projext/SuperSpec/docs/cli.md)。
