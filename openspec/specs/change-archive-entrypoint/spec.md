# change-archive-entrypoint Specification

## Purpose

Record the removal of the standalone `superspec change archive` lifecycle command.

## REMOVED Requirements

### Requirement: Explicit change archive command
**Reason**: Terminal cleanup now belongs to `superspec change finish`, which chooses archive or delete behavior from workflow retention policy or an explicit override.
**Migration**: Use `superspec change finish <change-name> --archive` when archive retention is desired.

### Requirement: Running changes require force
**Reason**: Force semantics are now defined by `change finish` for destructive retention outcomes instead of by a dedicated archive command.
**Migration**: Use `superspec change finish <change-name> --archive --force` or `--delete --force` for running changes.

### Requirement: Missing changes fail clearly
**Reason**: Missing-change validation is now part of the `change finish` command contract.
**Migration**: Use `superspec change finish <change-name>` and handle the same `change_not_found` error code.
