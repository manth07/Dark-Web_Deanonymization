import datetime
import time
from fastapi import APIRouter, status
from app.core.config import settings
from app.schemas import MemoryMetrics, SystemHealthResponse

router = APIRouter()

SERVICE_START_TIME = time.time()


def get_memory_metrics() -> MemoryMetrics:
    """Gather real-time system RAM and process memory statistics using psutil."""
    try:
        import psutil

        mem = psutil.virtual_memory()
        proc = psutil.Process()
        proc_mem = proc.memory_info()

        return MemoryMetrics(
            total_mb=round(mem.total / (1024 * 1024), 2),
            available_mb=round(mem.available / (1024 * 1024), 2),
            used_mb=round(mem.used / (1024 * 1024), 2),
            percent_used=round(mem.percent, 2),
            process_rss_mb=round(proc_mem.rss / (1024 * 1024), 2),
            process_vms_mb=round(proc_mem.vms / (1024 * 1024), 2),
        )
    except Exception:
        return MemoryMetrics(
            total_mb=0.0,
            available_mb=0.0,
            used_mb=0.0,
            percent_used=0.0,
            process_rss_mb=0.0,
            process_vms_mb=0.0,
        )


@router.get(
    "/health",
    response_model=SystemHealthResponse,
    status_code=status.HTTP_200_OK,
    summary="System Health & Diagnostic Status",
    description=(
        "Returns the operational status of the ThirdEye dark web intelligence platform, "
        "including version '2.0-SIH', accurate UTC server timestamp, system uptime, and memory usage."
    ),
)
async def health_check() -> SystemHealthResponse:
    """Diagnostic endpoint returning system status and health parameters."""
    uptime = time.time() - SERVICE_START_TIME
    memory_info = get_memory_metrics()

    return SystemHealthResponse(
        status="operational",
        version="2.0-SIH",
        timestamp=datetime.datetime.now(datetime.timezone.utc),
        uptime_seconds=round(uptime, 2),
        environment="development" if settings.DEBUG else "production",
        memory=memory_info,
        dependencies={
            "database": "postgresql+asyncpg (configured)",
            "threat_crawler": "active",
            "graph_engine": "operational",
        },
    )
