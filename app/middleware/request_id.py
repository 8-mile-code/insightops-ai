import logging
from time import perf_counter
from uuid import uuid4

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.core.config import settings
from app.core.request_context import reset_request_id, set_request_id

logger = logging.getLogger(__name__)


class RequestIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        request_id = (
            request.headers.get(settings.REQUEST_ID_HEADER) or uuid4().hex
        )

        request.state.request_id = request_id
        token = set_request_id(request_id)

        started_at = perf_counter()

        logger.info(
            "request_started",
            extra={
                "method": request.method,
                "path": request.url.path,
            },
        )

        try:
            response = await call_next(request)
        except Exception:
            duration_ms = round((perf_counter() - started_at) * 1000, 2)

            logger.exception(
                "request_failed",
                extra={
                    "method": request.method,
                    "path": request.url.path,
                    "duration_ms": duration_ms,
                },
            )
            raise

        else:
            duration_ms = round((perf_counter() - started_at) * 1000, 2)

            response.headers[settings.REQUEST_ID_HEADER] = request_id

            logger.info(
                "request_finished",
                extra={
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": response.status_code,
                    "duration_ms": duration_ms,
                },
            )

            return response

        finally:
            reset_request_id(token)
