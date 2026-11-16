from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from woninet.server.dependencies import get_static_path

TEMPLATES_DIR, STATIC_DIR = get_static_path()
templates = Jinja2Templates(directory=TEMPLATES_DIR)

router = APIRouter(prefix="/health", tags=["health"])


@router.get("", response_class=HTMLResponse)
def health(request: Request):
    return templates.TemplateResponse(request=request, name="health.html")
