class AppError(Exception):
    """Base application error."""


class UserAlreadyExistsError(AppError):
    """Raised when a user with the same email already exists."""


class InvalidCredentialsError(AppError):
    """Raised when login credentials are invalid."""


class ProjectNotFoundError(Exception):
    """Raised when a project does not exist or not owned by the user."""
