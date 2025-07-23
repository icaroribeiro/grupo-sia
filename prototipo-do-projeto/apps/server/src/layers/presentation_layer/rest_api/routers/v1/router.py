from fastapi import APIRouter

from src.layers.presentation_layer.rest_api.routers.v1 import (
    healthcheck_router,
    send_queries_router,
    # test_router,
    upload_files_router,
)

router = APIRouter()
router.include_router(router=healthcheck_router.router, tags=["healthcheck"])
router.include_router(router=upload_files_router.router, tags=["upload-files"])
router.include_router(router=send_queries_router.router, tags=["send-queries"])
# router.include_router(router=test_router.router, tags=["tests"])
