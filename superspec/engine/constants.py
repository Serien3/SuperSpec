SUPPORTED_SCHEMA_VERSION = "superspec.plan/v0.3"
SUPPORTED_PROTOCOL_VERSION = "superspec.protocol/v0.3"

DEFAULTS = {
    "executor": "skill",
    "onFail": "stop",
    "retry": {
        "maxAttempts": 1,
        "backoffSec": 0,
        "strategy": "fixed",
    },
}
