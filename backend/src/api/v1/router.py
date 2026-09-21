from fastapi import APIRouter

from backend.src.api.v1.chat import (
    router as chat_router,
)
from backend.src.api.v1.files import (
    router as files_router,
)
from backend.src.api.v1.measurements import (
    router as measurements_router,
)
from backend.src.api.v1.reports import (
    router as reports_router,
)
from backend.src.api.v1.search import (
    router as search_router,
)

api_v1_router = APIRouter(
    prefix="/api/v1",
)


api_v1_router.include_router(
    files_router,
)

api_v1_router.include_router(
    measurements_router,
)

api_v1_router.include_router(
    reports_router,
)

api_v1_router.include_router(
    search_router,
)

api_v1_router.include_router(
    chat_router,
)