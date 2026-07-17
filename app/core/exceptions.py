class AppError(Exception):
    """Base application error."""


class UserAlreadyExistsError(AppError):
    """Raised when a user with the same email already exists."""


class InvalidCredentialsError(AppError):
    """Raised when login credentials are invalid."""


class ProjectNotFoundError(AppError):
    """Raised when a project does not exist or not owned by the user."""


class ReportNotFoundError(AppError):
    """Raised when a report does not exist or is not owned by the user."""


class LLMServiceError(AppError):
    """Raised when LLM report generation fails."""


class AirflowAPIError(AppError):
    """Raised when Airflow cannot accept an API request."""


class PipelineRunNotFoundError(AppError):
    """Raised when a pipeline run does not exist or is not accessible."""
