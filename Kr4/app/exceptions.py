class AppException(Exception):
    status_code = 500
    error_code = "application_error"
    message = "Application error"

    def __init__(self, msg=None):
        if msg is not None:
            self.message = msg
        super().__init__(self.message)


class ConditionFailedException(AppException):
    status_code = 400
    error_code = "condition_failed"
    message = "The requested condition failed"


class ResourceNotFoundException(AppException):
    status_code = 404
    error_code = "resource_not_found"
    message = "Resource not found"
