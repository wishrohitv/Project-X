from werkzeug.exceptions import HTTPException


class AppError(HTTPException):
    def __init__(self, code=500, error="AppError", message="Something went wrong"):
        super().__init__(description=message)
        self.code = code
        self.error = error
        self.message = message


class InternalServerError(AppError):
    """Internal server error : An unexpected error occurred on the server."""

    def __init__(
        self,
        message="Internal sever error",
    ):
        super().__init__(code=500, error="IndternalServerError", message=message)


class ResourceNotFoundError(AppError):
    """Resource not found error : The requested resource could not be found."""

    def __init__(self, message="Resource not found"):
        super().__init__(code=404, error="ResourceNotFoundError", message=message)


class BadRequestError(AppError):
    """Bad request error : The request was invalid or cannot be served."""

    def __init__(self, error="Bad request"):
        super().__init__(code=400, error="BadRequestError", message=error)


class NotAcceptableError(AppError):
    """Not accesptable error : The request was invalid or cannot be served."""

    def __init__(self, error="Not accesptable"):
        super().__init__(code=400, error="NotAcceptableError", message=error)


class InvalidCredentialsError(AppError):
    """Invalid credentials error : The provided credentials are invalid."""

    def __init__(
        self,
        message="Invalid credentials",
    ):
        super().__init__(code=401, error="InvalidCredentialsError", message=message)


class UnAuthorizedError(AppError):
    """Unauthorized error : The request requires user authentication."""

    def __init__(
        self,
        message="Unauthorized error",
    ):
        super().__init__(code=401, error="UnAuthorizedError", message=message)


class TokenExpiredError(AppError):
    """Token expired error : The provided token has expired."""

    def __init__(
        self,
        message="Token expired",
    ):
        super().__init__(code=401, error="TokenExpiredError", message=message)


class ForbiddenError(AppError):
    """
    Forbidden error : The server understood the request but refuses to authorize it.
    """

    def __init__(
        self,
        message="Forbidden error",
    ):
        super().__init__(code=403, error="ForbiddenError", message=message)


class RateLimitExceededError(AppError):
    """Rate limit exceeded error : The request was rate-limited."""

    def __init__(
        self,
        message="Rate limit exceeded",
    ):
        super().__init__(code=429, error="RateLimitExceededError", message=message)


class ConflictError(AppError):
    """Conflict error : The request could not be completed due to a conflict."""

    def __init__(
        self,
        message="Conflict",
    ):
        super().__init__(code=409, error="ConflictError", message=message)
