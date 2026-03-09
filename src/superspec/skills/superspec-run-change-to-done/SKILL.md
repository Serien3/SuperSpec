---
name: superspec-run-change-to-done
description: Entry skill for SuperSpec autonomous delivery. Use when Codex needs to create or select a change, initialize and validate its plan, execute all steps via the protocol loop until terminal done, and return structured success or failure feedback.
---

# SuperSpec Run Change To Done

Drive one change from setup to terminal outcome using the SuperSpec pull protocol.

## Inputs

Resolve these inputs first:
- `change_name` (recommended)
- `owner` for `change advance` (default: `agent`)
- `plan_schema` (workflow type for new change, default: `SDD`)

If `change_name` is missing, derive a kebab-case name (e.g., "add user authentication" → `add-user-auth`).

## End-to-End Workflow

### Step 1: Resolve the target change.
   - List existing changes first:
     ```bash
     superspec change advance
     ```
   - Reuse existing change when the target name already exists in the command output.
   - Create when absent:
     ```bash
     superspec change advance --new "<plan_schema>/<change_name>" --owner "<owner>" --json
     ```
   - New selector format is required: `<workflow-type>/<change-name>` (for example `SDD/add-user-auth`).

### Step 2: Run protocol loop until terminal.
   - Pull next step for existing change:
     ```bash
     superspec change advance "<change_name>" --owner "<owner>" --json
     ```
  - Handle response state:
    - `ready`: dispatch executor and report `complete` or `fail` (may be newly allocated or resumed in-flight step).
    - `blocked`: use fixed-interval polling, then poll again.
    - `done`: stop loop and fetch terminal status.
   - Execution loop contract:
     1. Call `change advance`.
     2. If `state=ready`, **goto step4**. Execute exactly one step and report `complete` or `fail`.
     3. Immediately call `change advance` again.
    4. If `state=blocked`, use **blocked polling policy** and call `change advance` again.
    5. Exit only when `state=done`.

#### Blocked Polling Policy

When `change advance` returns `state=blocked`:
1. Sleep 2s.
2. Call `change advance` again.
3. Track consecutive blocked cycles; if blocked exceeds 30 consecutive loops, stop and report `execution_stalled`.

Note:
- If there is an in-flight `RUNNING` step, `change advance` may return `state=ready` with that same step for session handoff/resume instead of returning `blocked`.

### Step 4: Dispatch `ready` step by executor.
   - `script` executor:
     - Execute `step.script_command`.
     - On success:
       ```bash
       superspec change stepComplete "<change_name>" "<stepId>"
       ```
     - On failure:
       ```bash
       superspec change stepFail "<change_name>" "<stepId>"
       ```
   - `skill` executor:
     - Follow `step.prompt` and invoke `step.skillName`.
     - On success:
       ```bash
       superspec change stepComplete "<change_name>" "<stepId>"
       ```
     - On failure:
       ```bash
       superspec change stepFail "<change_name>" "<stepId>"
       ```
   - `human` executor:
     - Present `step.human.instruction` and wait for human decision.
     - If human approves, run
       ```bash
       superspec plan approve "<change_name>" "<stepId>"
       ```
     - If human rejects, run
       ```bash
       superspec plan reject "<change_name>" "<stepId>"
       ```

### Step 5: Produce terminal result and feedback.
   - Read terminal status:
     ```bash
     superspec change status "<change_name>" --json
     ```
   - Read status after loop exits on `next.state=done` (terminal confirmation), not after each step.

## Guardrails

- Use the exact `step.id` returned by `next`.
- Do not report `complete` or `fail` before real execution.
- Do not call `status` after every success; use checkpoint/terminal reads.
- Do not call `status --full` after every failure; keep the loop pull-driven by `next`.
- Treat `change stepFail` as terminal failure and escalate to a human.
- Do not terminate on first `blocked`; continue polling.
- Stop only when `next` returns `done`.

## Final Feedback Template

On success, report:
- `change_name`
- terminal `status`
- progress (`done/total`, `failed`, `running`)
- key completed steps

On failure, report:
- `change_name`
- terminal `status`
- failed step id(s)
- that human intervention is required
