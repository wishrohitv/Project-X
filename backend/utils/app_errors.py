from werkzeug.exceptions import HTTPException


class RepoError(Exception):
    """Custom error class for repository error"""

    def __init__(
        self, statusCode: int = 500, message: str = "Error while querying database"
    ) -> None:
        super().__init__()
        self.statusCode = statusCode
        self.message = message

    def __str__(self) -> str:
        return f"{self.statusCode} {self.message}"


class AppError(HTTPException):
    def __init__(self, code=500, error="AppError", message="Something went wrong"):
        super().__init__(description=message)
        self.code = code
        self.error = error
        self.message = message


class IndternalServerError(AppError):
    def __init__(
        self,
        message="Internal sever error",
    ):
        super().__init__(code=500, error="IndternalServerError", message=message)


class ResourceNotFoundError(AppError):
    def __init__(self, message="Resource not found"):
        super().__init__(code=404, error="ResourceNotFoundError", message=message)


class BadRequestError(AppError):
    def __init__(self, error="Bad request"):
        super().__init__(code=400, error="BaddRequestError", message=error)


class InvalidCredentialsError(AppError):
    def __init__(
        self,
        message="Invalid credentials",
    ):
        super().__init__(code=401, error="InvalidCredentialsError", message=message)


class RateLimitExceededError(AppError):
    def __init__(
        self,
        message="Rate limit exceeded",
    ):
        super().__init__(code=429, error="RateLimitExceededError", message=message)


class ConflictError(AppError):
    def __init__(
        self,
        message="Conflict",
    ):
        super().__init__(code=409, error="ConflictError", message=message)
