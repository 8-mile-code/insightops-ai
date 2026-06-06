from fastapi import FastAPI

from app.api.routers import health
from app.core.config import settings


app = FastAPI(
    title=settings.APP_TITLE,
    description=settings.APP_DESCRIPTION,
    debug=settings.DEBUG,
)

app.include_router(health.router)
