from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.api.v1.router import api_router
from app.core.bootstrap import bootstrap_application
from app.core.config import settings
from app.web.router import router as web_router
from app.web.templating import templates

from fastapi import Request
from fastapi.responses import HTMLResponse, JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException


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

    @app.exception_handler(StarletteHTTPException)
    async def custom_http_exception_handler(request: Request, exc: StarletteHTTPException):
        if request.url.path.startswith("/api") or request.url.path.startswith("/admin/api"):
            return JSONResponse({"detail": exc.detail}, status_code=exc.status_code)
        if exc.status_code == 404:
            return templates.TemplateResponse("storefront/404.html", {"request": request, "page_title": "Not Found"}, status_code=404)
        return HTMLResponse(content=f"<h1>Error {exc.status_code}</h1><p>{exc.detail}</p>", status_code=exc.status_code)

    @app.exception_handler(Exception)
    async def custom_server_error_handler(request: Request, exc: Exception):
        if request.url.path.startswith("/api") or request.url.path.startswith("/admin/api"):
            return JSONResponse({"detail": "Internal Server Error"}, status_code=500)
        import traceback
        traceback.print_exc()
        return templates.TemplateResponse("storefront/500.html", {"request": request, "page_title": "Server Error"}, status_code=500)

    return app


app = create_application()
