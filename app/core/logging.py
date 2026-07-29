import json
import logging
import sys
from datetime import UTC, datetime
from logging.config import dictConfig
from typing import Any

from app.core.config import settings
from app.core.request_context import get_request_id


class RequestIdFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = get_request_id() or "-"
        return True


class JsonLogFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        log_data: dict[str, Any] = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "request_id": getattr(record, "request_id", "-"),
        }

        extra_fields = [
            "method",
            "path",
            "status_code",
            "duration_ms",
            "user_id",
            "project_id",
            "dataset_id",
            "pipeline_run_id",
            "airflow_run_id",
            "agent_action",
            "tool_name",
            "error_code",
        ]

        for field in extra_fields:
            if hasattr(record, field):
                log_data[field] = getattr(record, field)

        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_data, ensure_ascii=False)


def configure_logging() -> None:
    formatter_name = "json" if settings.LOG_JSON else "default"

    dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "filters": {
                "request_id": {
                    "()": RequestIdFilter,
                },
            },
            "formatters": {
                "default": {
                    "format": (
                        "%(asctime)s %(levelname)s "
                        "[%(request_id)s] %(name)s: %(message)s"
                    ),
                },
                "json": {
                    "()": JsonLogFormatter,
                },
            },
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "stream": sys.stdout,
                    "formatter": formatter_name,
                    "filters": ["request_id"],
                },
            },
            "root": {
                "handlers": ["console"],
                "level": settings.LOG_LEVEL,
            },
        }
    )
