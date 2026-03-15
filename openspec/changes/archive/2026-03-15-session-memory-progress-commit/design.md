## Context

当前 `superspec git commit` 只执行 `git commit -m`，然后把本次提交的文件路径并入 change 的 execution runtime，并记录一条 `git.commit` 事件。这满足了执行状态追踪，但不足以为“结束会话时总结上一个会话”提供稳定输入，因为项目根目录缺少一个持续更新的、面向当前会话的摘要载体。

本次改动只覆盖第一阶段能力：
- 为每次 `superspec git commit` 生成结构化 commit context
- 把该 context 追加到根目录 `progress.md` 的当前会话区域

会话结束后的汇总脚本暂不实现，但本次设计会为其保留稳定边界。

## Goals / Non-Goals

**Goals:**
- 在不改变 `superspec git commit <change> --message ...` 基本调用方式的前提下，扩展命令返回 payload
- 保证每次成功 commit 后，项目根目录存在一个可持续追加的 `progress.md`
- 将 `progress.md` 当前会话区域设计成稳定、可重复写入、易于后续脚本读取的结构
- 优先使用机械可得的数据构建记录，例如 commit hash、文件列表、change 名称、时间戳和提交标题

**Non-Goals:**
- 不在本次实现中生成 “Last Session Summary”
- 不引入新的外部依赖或 LLM 调用
- 不尝试从多个 commits 聚合成完整会话总结
- 不改变现有 OpenSpec workflow 或归档机制

## Decisions

### Decision: Introduce a commit context payload owned by `git_commit`

`commit_for_change` 在成功提交后构建结构化 payload，并继续作为 CLI JSON 输出的核心来源。首批字段包含：
- `change`
- `commit_hash`
- `message`
- `committed_at`
- `files_changed`
- `progress_file`
- `progress_entry`

其中 `progress_entry` 表示实际写入当前会话区域的记录内容，便于测试和未来复用。

选择这一方案而不是只返回 `commit_hash` + `files_changed`，是因为后续 `finish-session` 脚本和测试都需要稳定读取同一份上下文模型。

### Decision: Maintain `progress.md` as a marker-delimited document

根目录 `progress.md` 使用固定标记管理当前会话区域：
- `<!-- superspec:current-session:start -->`
- `<!-- superspec:current-session:end -->`

命令首次运行时自动创建文件和基础结构；后续运行只替换该标记对之间的内容，其余区域保持原样。这种方式比整文件重写更安全，也为之后增加 `last-session` 区域留下空间。

备选方案是改写整个 `progress.md` 或使用 JSON sidecar 文件。前者对人工编辑不友好，后者又偏离了用户希望直接在根目录维护 Markdown 的目标。

### Decision: Append one normalized Markdown entry per commit

当前会话区域保存一个提交列表，每次 commit 追加一段标准化 Markdown 条目，包含：
- commit hash
- change
- title/message
- timestamp
- changed files

首版不要求复杂 prose，总结信息以稳定字段为主，避免让后续脚本依赖脆弱的自然语言解析。

### Decision: Keep event logging behavior and align progress writing after successful commit

`progress.md` 更新只能发生在 `git commit` 成功之后，并与 execution state / events.log 更新位于同一执行路径。若 progress 写入失败，命令应返回结构化错误，避免出现“提交已完成但 progress 未更新却静默成功”的状态漂移。

## Risks / Trade-offs

- [Risk] `progress.md` 被用户手工编辑破坏标记结构 → Mitigation: 缺失标记时自动重建标准骨架；保留标记外内容
- [Risk] 当前会话区域随 commit 增多而变长 → Mitigation: 首阶段接受线性增长，后续通过 finish-session 脚本收口
- [Risk] CLI payload 变更影响依赖命令输出的测试或脚本 → Mitigation: 保持现有字段兼容，仅追加新字段
- [Risk] 写入 `progress.md` 失败导致 Git 与 Superspec 状态不一致 → Mitigation: 失败时返回明确错误，让调用方感知需要修复
