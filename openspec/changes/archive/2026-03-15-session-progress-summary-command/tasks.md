## 1. Progress Summary Command

- [x] 1.1 Add CLI support for `superspec progress` and route it to a dedicated progress summarization service.
- [x] 1.2 Implement parsing and summarization helpers that read current-session commit entries, generate the requested Markdown session block, append it to `progress.md`, and clear the current-session section.

## 2. Verification

- [x] 2.1 Add unit coverage for progress parsing, session numbering, deduped changes/files, optional details expansion, and current-session clearing behavior.
- [x] 2.2 Add CLI coverage for the new `superspec progress` command and run targeted tests for progress/session behavior.
