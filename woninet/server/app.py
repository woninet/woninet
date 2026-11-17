import asyncio
from pathlib import Path
from fastapi import FastAPI, Request, HTTPException, Depends, status
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi_swagger import patch_fastapi
from contextlib import asynccontextmanager
from woninet.server.routes.api.devices import router as devices_api
from woninet.server.routes.api.stats import router as stats_api
from woninet.server.routes.api.alerts import router as alerts_api
from woninet.server.routes.api.health import router as health_api
from woninet.server.routes.api.settings import router as settings_api
from woninet.server.routes.page.devices import router as devices_page
from woninet.server.routes.page.alerts import router as alerts_page
from woninet.server.routes.page.health import router as health_page
from woninet.server.routes.page.settings import router as settings_page
from woninet.server.routes.page.about import router as about_page
from woninet.server.dependencies import get_static_path, require_monitor
from woninet.main import MonitorManager
from woninet.__init__ import __version__

# Global variables
TEMPLATES_DIR, STATIC_DIR = get_static_path()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup

    # Assign the instance of Server
    server = app.state.uvicorn_server

    monitor_manager = MonitorManager()
    monitor_manager.start()
    app.state.monitor_manager = monitor_manager

    async def watch():
        """
        Periodic monitor watchdog. Triggers server shutdown when the monitor
        is no longer alive.
        """
        while True:
            await asyncio.sleep(1)
            if not monitor_manager.is_alive():
                server.should_exit = True
                return

    task = asyncio.create_task(watch())

    try:
        yield
    finally:
        # Shutdown
        task.cancel()
        await asyncio.gather(task, return_exceptions=True)
        await asyncio.to_thread(monitor_manager.stop)


app = FastAPI(
    title="woninet",
    description="Network Monitoring Dashboard",
    lifespan=lifespan,
    version=__version__,
    docs_url=None,
    swagger_ui_oauth2_redirect_url=None,
)
patch_fastapi(app=app, redirect_from_root_to_docs=False)

# Templates
templates = Jinja2Templates(directory=TEMPLATES_DIR)

# Static files
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# Routes
app.include_router(devices_api)
app.include_router(stats_api)
app.include_router(alerts_api)
app.include_router(health_api)
app.include_router(settings_api)
app.include_router(devices_page)
app.include_router(alerts_page)
app.include_router(health_page)
app.include_router(settings_page)
app.include_router(about_page)


# The root path
@app.get("/", response_class=HTMLResponse)
def root(request: Request, monitor=Depends(require_monitor)):
    return templates.TemplateResponse(request=request, name="dashboard.html")


@app.exception_handler(404)
def custom_not_found_exception(request: Request, exc: HTTPException):
    if request.url.path.startswith("/api/"):
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND, content={"detail": "Not Found"}
        )
    return templates.TemplateResponse(
        request=request,
        name="404.html",
        context={"request": request},
        status_code=status.HTTP_404_NOT_FOUND,
    )


@app.exception_handler(503)
def custom_service_unavailable_exception(request: Request, exc: HTTPException):
    if request.url.path.startswith("/api/"):
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"detail": "Service Unavailable"},
        )
    return templates.TemplateResponse(
        request=request,
        name="503.html",
        context={"request": request},
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
    )
