from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.api.v1.router import api_router
from app.core.bootstrap import bootstrap_application
from app.core.config import settings
from app.web.router import router as web_router


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    bootstrap_application()
    yield


def create_application() -> FastAPI:
    app = FastAPI(title=settings.project_name, lifespan=lifespan)
    app.include_router(api_router, prefix=settings.api_v1_prefix)
    app.include_router(web_router)
    app.mount("/static", StaticFiles(directory=str(Path(__file__).resolve().parent / "web" / "static")), name="static")

    media_path = Path(settings.media_dir)
    media_path.mkdir(parents=True, exist_ok=True)
    app.mount("/media", StaticFiles(directory=str(media_path)), name="media")

    return app


app = create_application()
