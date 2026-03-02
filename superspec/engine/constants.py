SUPPORTED_SCHEMA_VERSION = "superspec.plan/v0.2"
SUPPORTED_PROTOCOL_VERSION = "superspec.protocol/v0.2"

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

DEFAULT_LEASE_TTL_SEC = 300
ACTION_STATUSES = {"PENDING", "LEASED", "RUNNING", "SUCCESS", "FAILED", "SKIPPED"}
