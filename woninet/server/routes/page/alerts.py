from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from woninet.server.dependencies import get_static_path, require_monitor

TEMPLATES_DIR, STATIC_DIR = get_static_path()
templates = Jinja2Templates(directory=TEMPLATES_DIR)

router = APIRouter(prefix="/alerts", tags=["alerts"])


@router.get("", response_class=HTMLResponse)
def alerts(
    request: Request,
    monitor=Depends(require_monitor),
):
    return templates.TemplateResponse(request=request, name="alerts.html")
