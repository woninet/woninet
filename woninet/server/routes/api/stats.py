from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from woninet.server.dependencies import require_monitor

router = APIRouter(prefix="/api/stats", tags=["stats"])


@router.get("")
def stats(monitor=Depends(require_monitor)):
    from woninet.__init__ import __version__

    devices_total, metrics_total = monitor.count_resources()

    return JSONResponse(
        content={
            "identity": {
                "service": "woninet",
                "version": __version__,
                "server_ip": monitor.local_ip,
            },
            "health": {
                "engine_alive": monitor.is_alive(),
                "database": monitor.database_health(),
            },
            "stats": {
                "devices_total": devices_total,
                "metrics_total": metrics_total,
                "uptime_seconds": monitor.uptime(),
            },
            "recent_alert_events": monitor.classify_recent_alert_events(),
        },
        status_code=status.HTTP_200_OK,
    )
