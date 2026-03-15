## 1. Commit Context Model

- [x] 1.1 Extend `superspec git commit` to return a structured commit context payload with message, timestamp, and progress metadata.
- [x] 1.2 Add helper logic to build a normalized progress entry from a successful commit.

## 2. Progress File Maintenance

- [x] 2.1 Implement root `progress.md` creation and current-session marker management.
- [x] 2.2 Append normalized commit entries into the current-session section while preserving unrelated content.

## 3. Verification

- [x] 3.1 Add or update tests for expanded commit payload fields and `progress.md` creation/update behavior.
- [x] 3.2 Run targeted test coverage for git commit behavior.
