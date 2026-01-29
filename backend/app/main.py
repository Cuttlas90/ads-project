from fastapi import FastAPI

from app.api.router import api_router
from app.logging import configure_logging
from app.settings import get_settings


def create_app() -> FastAPI:
    settings = get_settings()
    configure_logging(settings)
    app = FastAPI(title=settings.APP_NAME)
    app.include_router(api_router)
    return app


app = create_app()
