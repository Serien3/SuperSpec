# SuperSpec

## Introduction
SuperSpec 是一个基于协议（protocol-driven）的变更执行编排器。它通过 `plan next -> complete/fail -> status` 的循环，把计划执行与实际执行器（脚本或 Agent-Skill）解耦。

核心能力：
- 基于工作流（workflow schema）生成 `plan.json`
- 使用 CLI 拉取下一步动作并回传执行结果
- 通过执行状态文件追踪进度、失败与终态

关键目录：
- `src/superspec/`：CLI 与执行引擎
- `src/superspec/schemas/`：计划与工作流 schema
- `src/superspec/schemas/templates/`：基础计划模板
- `openspec/changes/<change>/`：每个变更的计划与执行状态

## Installation
要求：Python 3.10+。

```bash
python3 -m pip install -e .
```

可选检查：
```bash
superspec --help
PYTHONPATH=src python3 -m unittest discover -s src/superspec/tests -p "test_*.py"
```

说明：`superspec change new` 依赖本机可用 `openspec` 命令。

## Getting Start
1. 初始化仓库（OpenSpec + Codex Skills）：
```bash
superspec init --agent codex
```

2. 创建变更并初始化计划：
```bash
superspec change new demo-change --summary "demo" --init-plan --plan-schema sdd
```

3. 校验计划：
```bash
superspec plan validate demo-change
```

4. 拉取下一步动作：
```bash
superspec plan next demo-change --owner agent --json
```

5. 成功/失败回报：
```bash
superspec plan complete demo-change a1 --result-json '{"ok":true,"executor":"skill","actionId":"a1"}'
superspec plan fail demo-change a1 --error-json '{"code":"skill_failed","message":"...","executor":"skill"}'
```

6. 查看状态：
```bash
superspec plan status demo-change --json
superspec plan status demo-change --json --full
```

## Usage
### CLI Commands
- `superspec init --agent codex`（执行 `openspec init --tools codex` 并同步技能到 `.codex/skills`）
- `superspec change new <change> [--summary ...] [--init-plan --plan-schema sdd]`
- `superspec plan init <change> --schema sdd [--title ... --goal ...]`
- `superspec plan validate <change>`
- `superspec plan next <change> --owner <owner> --json [--debug]`
- `superspec plan complete <change> <action_id> --result-json '{...}'`
- `superspec plan fail <change> <action_id> --error-json '{...}'`
- `superspec plan status <change> --json [--full] [--debug] [--action-limit 40]`

### Agent Command
推荐 Agent 拉取执行循环：
```bash
while true; do
  payload=$(superspec plan next demo-change --owner agent --json)
  state=$(echo "$payload" | python3 -c 'import sys,json;print(json.load(sys.stdin)["state"])')
  if [ "$state" = "done" ]; then
    superspec plan status demo-change --json
    break
  fi
  # 根据 payload.action.executor 执行实际任务
  # 成功后调用 plan complete，失败调用 plan fail
  sleep 2
done
```

### 自定义工作流（Custom Workflow）
在仓库创建：`superspec/schemas/workflows/myflow.workflow.json`（项目级覆盖路径，不在 `src/` 下）

最小示例：
```json
{
  "workflowId": "myflow",
  "version": "1.0.0",
  "title": "My custom flow",
  "goal": "Run custom actions",
  "actions": [
    { "id": "a1", "type": "custom.step", "executor": "script", "script": "echo hello" }
  ]
}
```

初始化并使用：
```bash
superspec plan init demo-change --schema myflow
superspec plan validate demo-change
```
