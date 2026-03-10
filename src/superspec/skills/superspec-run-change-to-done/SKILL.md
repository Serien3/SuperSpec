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
- `plan_schema` (workflow type for new change, default: `spec-dev`)

If `change_name` is missing, derive a kebab-case name (e.g., "add user authentication" → `add-user-auth`).

## End-to-End Workflow

### Step 1: Resolve the target change.
   - If a change name was provided: `superspec change advance <change_name> --json`
   - If a description was provided: Infer workflow type, then `superspec change advance --new <workflow-type>/<change-name> --json`
   - If nothing provided: `superspec change list` to list active changes, then AskUserQuestion  to ask clarifying questions

### Step 2: Parse JSON response to get prompt
   - `change`: The change name
   - `state`: Current state
   - `step`: Current workflow step
    - `stepID`
    - `executor`: The execution type of this step
    - `skillName`: The skill to be invoked in this step
    - `script_command`: The command to be executed in this step
    - `option`: Human call feedback option
    - `prompt`: **The prompt words for this step(You MUST follow it to complete this step.)**

### Step 3: Execute the workflow step and update it
   - You MUST follow the prompt to complete this step.
   - Call or Use `skillName`/`script_command`/`option` according to prompt
   - When you complete a step and confirm that the step has been fully completed,run:
     ```bash
     superspec change stepComplete "<change_name>" "<stepId>"
     ```
   - If you are unable to complete this step after trying and require human intervention, then this step is considered a failure.Run:
     ```bash
     superspec change stepFail "<change_name>" "<stepId>"

### Step 4: After completing a step, re-run `superspec change advance <change_name> --json` to get next step
   - The state should be "done" before all steps are completed.
   - Continue the loop until `state == done or blocked`
   - If blocked: Goto *Blocked Polling Policy*

#### Blocked Polling Policy

When `change advance` returns `state=blocked`:
1. Sleep 2s.
2. Call `change advance` again.
3. Track consecutive blocked cycles; if blocked exceeds 30 consecutive loops, stop and report `execution_stalled`.

### Step 5: Produce terminal result and feedback.
   - Read terminal status:
     ```bash
     superspec change status "<change_name>" --json
     ```
   - Report **Final Feedback** to human

## Currently supported Workflow Types





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
