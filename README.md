# SuperSpec

**A customizable AI coding framework designed for long-running, minimally supervised agentic development**

## Overview

Vibe-coding has proven that software can be produced quickly with AI in the loop, but making it reliable at scale requires turning an improvised chat-driven process into structured, standardized engineering. In parallel, there has been growing research and practical work on making long-running, minimally supervised AI agents feasible through durable plans, explicit artifacts, repeatable skills, and checkpointable execution.  In parallel, **Agent Skills** have become a popular way to productionize agentic development: packaging repeatable workflows, tool-use patterns, and prompting strategies into composable units that teams can share, evolve, and reuse.

For example :
- **OpenSpec**: structured SDD artifacts and a spec-first alignment discipline.
- **Superpowers**: an agentic skills framework paired with a software development methodology that works in practice.
- **planning-with-files**: Manus-style, persistent Markdown planning—so long-running work stays grounded in durable files rather than fragile chat context.

However, adopting only one of them often leaves gaps in real-world workflows:

### Why not OpenSpec?
OpenSpec is excellent for SDD, but it can be restrictive when you need a more flexible, customizable workflow (e.g., mixing research/implementation/ops, reordering phases, or introducing project-specific gates and templates) beyond a single, fixed SDD path.

### Why not Superpowers?
Superpowers provides a strong development workflow and a solid skills framework, but relying entirely on the Agent to *discover* and *select* the right skills can be unpredictable—especially in long tasks where consistency and process guardrails matter.

### Why not planning-in-files?
Persistent, file-based planning is a powerful foundation for long-running agents, but by itself it does not ship with a built-in software development workflow or prompting playbooks—so teams still need to define “what happens next”, “what artifacts are expected”, and “how to validate progress”.

**Superspec** aims to integrate the strengths of these frameworks to create an agent coding framework that can combine skill-based custom workflows and run for extended periods with minimal supervision.


1. An SDD workflow plus **CLI-friendly progressive disclosure prompting** (show the right constraints at the right time).
2. Superpowers-style **agentic skills framework** and a **software development methodology that works**.
3. Manus-style **persistent Markdown planning** for durable, restartable execution with minimal human interruptions.

## Installation

```bash
pip install git+https://github.com/Serien3/SuperSpec
-- OR --
git clone https://github.com/Serien3/SuperSpec.git && cd SuperSpec/ && pip install .
```

### Requirements
- Python >= 3.10 (tested on v3.12.3)
- jsonschema >= 4.0

The following tools must be available in your system path :
- Git
- ~~OpenSpec >= v1.1.0 (reference [OpenSpec](https://github.com/Fission-AI/OpenSpec))~~
- 🚀 SuperSpec has now internally implemented a Spec-driven development workflow and associated skills.There is no longer any need to download OpenSpec.


## Getting Started

After installation, try **SuperSpec** with the following steps:

1. Navigate to one of your project directories and initialize it
   
   ```bash
   cd <your-project>
   superspec init --agent codex
   ```
2. If you want to customize a built-in workflow, fork one into your project first:

   ```bash
   superspec workflow fork spec-dev my-spec-dev
   ```

   This creates `superspec/schemas/workflows/my-spec-dev.workflow.json`, which you can edit locally and then use with `superspec change advance --new my-spec-dev/<change-name>`.
3. Once requirements are clear, tell your AI to use the `superspec-finish-a-change` skill to implement them.
4. During the process you'll see new files/directories created (for example `.codex/skills/`):
   ```text
   <your-project>/
   ├── .codex/
   │   └── skills/
   │       └── ...                     # Skills installed by `superspec init` for AI execution
   └── superspec/
       ├── schemas/
       │   └── workflows/
       │       └── my-spec-dev.workflow.json
       └── changes/
           └── <change-name>/
               └── execution/
                   ├── state.json      # Current execution state snapshot (meta + runtime goal/steps/progress/terminal status)
                   └── events.log      # Event log (e.g. action.started/completed/failed)
   ```

`execution/state.json` may also contain helper metadata written by CLI utilities, for example:

- `runtime.goal`: optional one-line change goal written by `superspec change advance --new ... --goal "..."`.

The repository root `progress.md` is also maintained by SuperSpec:
- `superspec git commit` appends the latest structured commit record into `Current Session`.
- `superspec progress` turns the current-session ledger into a completed `## YYYY-MM-DD Session x` summary and resets the current-session block for the next work period.

For the full command reference, see [`docs/cli.md`](./docs/cli.md).
