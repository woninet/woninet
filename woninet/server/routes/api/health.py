from fastapi import APIRouter, Request, status
from fastapi.responses import JSONResponse, RedirectResponse
from woninet.server.dependencies import get_diagnostics

router = APIRouter(prefix="/api/health", tags=["health"])


@router.get("")
def health():
    diagnostics = get_diagnostics()

    issues = diagnostics.list_issues()

    monitor_core = issues.get("monitor_core") or {}
    database = issues.get("database") or {}
    configuration = issues.get("configuration") or {}
    utility = issues.get("utility") or {}

    return JSONResponse(
        content={
            "health": {
                "monitor_core": {
                    "error_code": monitor_core.get("code"),
                    "message": monitor_core.get("message"),
                },
                "database": {
                    "error_code": database.get("code"),
                    "message": database.get("message"),
                },
                "configuration": {
                    "error_code": configuration.get("code"),
                    "message": configuration.get("message"),
                },
                "utility": {
                    "error_code": utility.get("code"),
                    "message": utility.get("message"),
                },
            }
        },
        status_code=status.HTTP_200_OK,
    )


@router.get("/restart")
def restart(request: Request):
    monitor_manager = request.app.state.monitor_manager
    monitor_manager.restart()

    return RedirectResponse(url="/health", status_code=status.HTTP_303_SEE_OTHER)
