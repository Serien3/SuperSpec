---
name: excuting-tasks
description: Implement tasks from an SuperSpec change. Use when the user wants to start implementing, continue implementation, or work through tasks.
---

# Executing Tasks

## Overview

Implement tasks from an SuperSpec change. DRY. YAGNI. TDD. Frequent commits.

**Announce at start:** "I'm using the executing-tasks skill to implement tasks."

## **The Process**

### Step 1: Read context files

- Read context document created for developing in this change, especially `tasks.md`. 
- If needed, recall `proposal.md`, `specs`, `design.md`(if present).

### Step 2: Implement tasks(loop until done or blocked)

**You MUST follow **

```
 For each pending task:
   - You must select and proceed **in order**.
   - Make the code changes required or complete the work according to the task requirements.
   - Keep changes minimal and focused
   - You MUST check tasks off as you complete a task or a task group
     - Mark task complete in the tasks file: `- [ ]` → `- [x]`
```

**Skip a task or Pause if:**

- Task is unclear → ask for clarification
- Implementation reveals a design issue → suggest updating specs or design
- Error or blocker encountered → Try your best. If you are unable to complete this task, you can choose to skip it.

### Step 3: **If skip a task or paused**
   If skip a task:
   - Errors Encountered

   If paused, Display:
   - Tasks completed this session
   - Overall progress: "N/M tasks complete"
   - Explain why and wait for guidance

### Step 4: **Complete Development**

After all tasks complete and verified:
- Report "All tasks complete! "

**Guardrails**

- Keep going through tasks until done or blocked.
- Always read context files before starting .
- If implementation reveals issues, pause and read related context documents. Try updating them.
- Keep code changes minimal and scoped to each task.
- Update task checkbox immediately after completing each task.
- Pause on errors, blockers, or unclear requirements - don't guess.

## **Fluid Workflow Integration**

This skill supports the "steps on a change" model:

- **Can be invoked anytime**: Before all context document are done (if tasks exist), after partial implementation, interleaved with other steps
- **Allows document updates**: If implementation reveals design issues, suggest updating documents - not phase-locked, work fluidly
