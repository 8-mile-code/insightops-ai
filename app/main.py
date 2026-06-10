from fastapi import FastAPI

from app.api.routers import auth, datasets, db_check, health, projects
from app.core.config import settings

app = FastAPI(
    title=settings.APP_TITLE,
    description=settings.APP_DESCRIPTION,
    debug=settings.DEBUG,
)

app.include_router(health.router)
app.include_router(db_check.router)
app.include_router(auth.router)
app.include_router(projects.router)
app.include_router(datasets.router)
