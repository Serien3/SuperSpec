---
name: superspec-finish-a-change
description: Execute a SuperSpec change from selection or creation to a terminal outcome. Use when Agent needs to start or continue workflow on a Superspec change,drive the full change workflow step by step, and coordinate required actions .
---

# SuperSpec Run Change To Done

Start or continue workflow on a Superspec change. Complete each step in a loop and finish the workflow of current change.

## End-to-End Workflow

### Step 1: Resolve the target change.
   - If a change name was provided: `superspec change advance <change-name> --json`
   - If a description was provided: Infer workflow type, then `superspec change advance --new <workflow-type>/<change-name> --json`
     - If `change-name` is missing, derive a kebab-case name (e.g., "add user authentication" → `add-user-auth`).
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
   - You MUST follow the prompt to complete a step.
   - Call or Use `skillName`/`script_command`/`option` according to prompt
   - When you complete a step and confirm that the step has been fully completed,run:
     ```bash
     superspec change stepComplete "<change-name>" "<stepId>"
     ```
   - If you are unable to complete this step after trying and require human intervention, then this step is considered a failure.Run:
     ```bash
     superspec change stepFail "<change-name>" "<stepId>"
     ```

### Step 4: After completing a step, re-run `superspec change advance <change-name> --json` to get next step
   - Continue the loop until `state == done or blocked`. One loop is one step.
   - You must strictly follow **step 2** and **step 3** to complete each step in each loop.
   - If blocked: Goto *Blocked Polling Policy*
   - If done: Goto Step 5**

#### Blocked Polling Policy

When `change advance` returns `state=blocked`:
1. Sleep 2s.
2. Call `change advance` again.
3. Track consecutive blocked cycles; if blocked exceeds 5 consecutive loops, stop and report `execution_stalled`.

### Step 5: Produce terminal result and feedback.
   - Read terminal status:
     ```bash
     superspec change status "<change-name>" --json
     ```
   - Report **Final Feedback** to human

## Currently supported Workflow Types


## Final Feedback Template

On success, report:
- `change-name`
- terminal `status`
- progress (`done/total`, `failed`, `running`)
- key completed steps

On failure, report:
- `change-name`
- terminal `status`
- failed step id(s)
- that human intervention is required
