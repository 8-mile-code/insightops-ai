from fastapi import status


class AppError(Exception):
    """Base application error."""

    status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR
    error_code: str = "app_error"
    message: str = "Application error"
    headers: dict[str, str] | None = None

    def __init__(
        self,
        message: str | None = None,
        *,
        status_code: int | None = None,
        error_code: str | None = None,
    ) -> None:
        self.message = message or self.message

        if status_code is not None:
            self.status_code = status_code

        if error_code is not None:
            self.error_code = error_code

        super().__init__(self.message)


class UserAlreadyExistsError(AppError):
    """Raised when a user with the same email already exists."""

    status_code = status.HTTP_400_BAD_REQUEST
    error_code = "user_already_exists"
    message = "User with this email already exists"


class InvalidCredentialsError(AppError):
    """Raised when login credentials are invalid."""

    status_code = status.HTTP_401_UNAUTHORIZED
    error_code = "invalid_credentials"
    message = "Invalid email or password"
    headers = {"WWW-Authenticate": "Bearer"}


class ProjectNotFoundError(AppError):
    """Raised when a project does not exist or not owned by the user."""

    status_code = status.HTTP_404_NOT_FOUND
    error_code = "project_not_found"
    message = "Project not found"


class ReportNotFoundError(AppError):
    """Raised when a report does not exist or is not owned by the user."""

    status_code = status.HTTP_404_NOT_FOUND
    error_code = "report_not_found"
    message = "Report not found"


class LLMServiceError(AppError):
    """Raised when LLM report generation fails."""

    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    error_code = "llm_service_error"
    message = "LLM service is unavailable"


class AirflowAPIError(AppError):
    """Raised when Airflow cannot accept an API request."""

    status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    error_code = "airflow_api_error"
    message = "Airflow API is unavailable"


class PipelineRunNotFoundError(AppError):
    """Raised when a pipeline run does not exist or is not accessible."""

    status_code = status.HTTP_404_NOT_FOUND
    error_code = "pipeline_run_not_found"
    message = "Pipeline run not found"


class MCPToolCallError(AppError):
    """Raised when an MCP tool call fails."""

    status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    error_code = "mcp_tool_call_error"
    message = "MCP tool call failed"


class DatasetNotFoundError(AppError):
    """Raised when a dataset does not exist or is not accessible."""

    status_code = status.HTTP_404_NOT_FOUND
    error_code = "dataset_not_found"
    message = "Dataset not found"
