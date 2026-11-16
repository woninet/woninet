from pathlib import Path
from fastapi import HTTPException, status


def get_static_path() -> tuple[Path, Path]:
    """
    Return the paths to the templates and static directories.

    Returns:
        tuple[Path, Path]: A tuple containing (TEMPLATES_DIR, STATIC_DIR)
    """
    STATIC_DIR = Path(__file__).parent / "static"
    TEMPLATES_DIR = Path(__file__).parent / "templates"

    return TEMPLATES_DIR, STATIC_DIR


def get_monitor_gracefully():
    """
    Call get_monitor() and return the instance of NetworkMonitorCore class
    to prevent circular import error.
    """
    from woninet.main import get_monitor

    monitor = get_monitor()
    return monitor


def require_monitor():
    """
    Ensure the monitoring service is available before continuing.

    Returns:
        The initialized NetworkMonitorCore instance.

    Raises:
        HTTPException: If the monitor has been degraded.
    """
    monitor = get_monitor_gracefully()

    if not monitor.is_healthy():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Monitor is not initialized.",
        )

    return monitor


def get_diagnostics():
    """
    Call `woninet.main.get_diagnostics()` and return the instance of `DiagnosticManager`
    to prevent circular import error.
    """
    from woninet.main import get_diagnostics

    diagnostics = get_diagnostics()
    return diagnostics
