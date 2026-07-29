import logging
from typing import Any

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.exceptions import AppError
from app.core.request_context import get_request_id


logger = logging.getLogger(__name__)


def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(AppError, app_error_handler)
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(
        RequestValidationError,
        validation_exception_handler,
    )
    app.add_exception_handler(Exception, unhandled_exception_handler)


def _get_request_id(request: Request) -> str:
    return (
        getattr(request.state, "request_id", None) or get_request_id() or "-"
    )


def _build_error_response(
    *,
    status_code: int,
    error_code: str,
    message: str,
    request_id: str,
    errors: list[dict[str, Any]] | None = None,
    headers: dict[str, str] | None = None,
) -> JSONResponse:
    content: dict[str, Any] = {
        "detail": message,
        "error": {
            "code": error_code,
            "message": message,
            "request_id": request_id,
        },
    }

    if errors is not None:
        content["error"]["errors"] = errors

    response_headers = {
        settings.REQUEST_ID_HEADER: request_id,
    }

    if headers:
        response_headers.update(headers)

    return JSONResponse(
        status_code=status_code,
        content=content,
        headers=response_headers,
    )


async def app_error_handler(
    request: Request,
    exc: AppError,
) -> JSONResponse:
    request_id = _get_request_id(request)

    logger.warning(
        "application_error",
        extra={
            "error_code": exc.error_code,
            "status_code": exc.status_code,
            "method": request.method,
            "path": request.url.path,
        },
    )

    return _build_error_response(
        status_code=exc.status_code,
        error_code=exc.error_code,
        message=exc.message,
        request_id=request_id,
        headers=exc.headers,
    )


async def http_exception_handler(
    request: Request,
    exc: HTTPException,
) -> JSONResponse:
    request_id = _get_request_id(request)

    message = str(exc.detail)

    logger.warning(
        "http_error",
        extra={
            "error_code": f"http_{exc.status_code}",
            "status_code": exc.status_code,
            "method": request.method,
            "path": request.url.path,
        },
    )

    return _build_error_response(
        status_code=exc.status_code,
        error_code=f"http_{exc.status_code}",
        message=message,
        request_id=request_id,
        headers=exc.headers,
    )


async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    request_id = _get_request_id(request)

    logger.warning(
        "validation_error",
        extra={
            "error_code": "validation_error",
            "status_code": status.HTTP_422_UNPROCESSABLE_CONTENT,
            "method": request.method,
            "path": request.url.path,
        },
    )

    return _build_error_response(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        error_code="validation_error",
        message="Request validation failed",
        request_id=request_id,
        errors=[
            {
                "loc": list(error["loc"]),
                "msg": error["msg"],
                "type": error["type"],
            }
            for error in exc.errors()
        ],
    )


async def unhandled_exception_handler(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    request_id = _get_request_id(request)

    logger.exception(
        "unhandled_error",
        extra={
            "error_code": "internal_server_error",
            "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
            "method": request.method,
            "path": request.url.path,
        },
    )

    message = "Internal server error" if not settings.DEBUG else str(exc)

    return _build_error_response(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        error_code="internal_server_error",
        message=message,
        request_id=request_id,
    )
