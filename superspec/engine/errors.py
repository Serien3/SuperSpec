class ValidationError(Exception):
    def __init__(self, message: str, details=None):
        super().__init__(message)
        self.details = details or {}


class ActionExecutionError(Exception):
    def __init__(self, message: str, details=None):
        super().__init__(message)
        self.details = details or {}


class ProtocolError(Exception):
    def __init__(self, message: str, code: str = "protocol_error", details=None):
        super().__init__(message)
        self.code = code
        self.details = details or {}
