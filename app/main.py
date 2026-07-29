from fastapi import FastAPI

from app.api.routers import (
    agent,
    analytics,
    auth,
    datasets,
    db_check,
    health,
    pipeline_runs,
    projects,
    reports,
)
from app.core.config import settings
from app.core.exception_handlers import register_exception_handlers
from app.core.logging import configure_logging
from app.middleware.request_id import RequestIDMiddleware

configure_logging()

app = FastAPI(
    title=settings.APP_TITLE,
    description=settings.APP_DESCRIPTION,
    debug=settings.DEBUG,
)

app.add_middleware(RequestIDMiddleware)
register_exception_handlers(app)

app.include_router(health.router)
app.include_router(db_check.router)
app.include_router(auth.router)
app.include_router(projects.router)
app.include_router(datasets.router)
app.include_router(pipeline_runs.router)
app.include_router(analytics.router)
app.include_router(reports.router)
app.include_router(agent.router)
