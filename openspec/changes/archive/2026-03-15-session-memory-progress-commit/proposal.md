## Why

`superspec git commit` 目前只负责执行提交并记录变更文件，无法把一次开发会话中每次提交的关键信息持续沉淀下来。为了让后续“结束会话并生成上个会话总结”的脚本能够稳定工作，提交时就需要把结构化上下文写入项目根目录的 `progress.md` 当前会话区域。

## What Changes

- 扩展 `superspec git commit` 的输出模型，返回本次提交的结构化上下文，包括提交标题、关联 change、提交文件列表和时间戳等字段。
- 在项目根目录维护 `progress.md`，由 `superspec git commit` 自动创建或更新 `Current Session` 区域，并为每次提交追加一条结构化记录。
- 让提交记录尽量由机械化数据构成，并允许少量由命令输入提供的人类摘要内容，以便后续脚本直接读取 `progress.md` 做会话总结。

## Capabilities

### New Capabilities
- `session-progress-memory`: Maintain a root `progress.md` current-session section that is updated on each `superspec git commit`.

### Modified Capabilities

## Impact

- Affected code: `src/superspec/engine/scm/git_commit.py`, `src/superspec/cli.py`
- New helper logic for reading/writing `progress.md`
- Tests for commit payload shape and `progress.md` updates
