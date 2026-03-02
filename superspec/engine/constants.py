SUPPORTED_SCHEMA_VERSION = "superspec.plan/v0.3"
SUPPORTED_PROTOCOL_VERSION = "superspec.protocol/v0.3"

SUPPORTED_ACTION_TYPES = {
    "openspec.proposal",
    "openspec.specs",
    "openspec.design",
    "openspec.tasks",
    "openspec.apply",
}

DEFAULTS = {
    "executor": "skill",
    "timeoutSec": 900,
    "onFail": "stop",
    "ifExists": "fail",
    "retry": {
        "maxAttempts": 1,
        "backoffSec": 0,
        "strategy": "fixed",
    },
}

ACTION_STATUSES = {"PENDING", "RUNNING", "SUCCESS", "FAILED", "SKIPPED"}
