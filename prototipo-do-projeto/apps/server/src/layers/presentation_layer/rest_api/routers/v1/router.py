from fastapi import APIRouter

from src.layers.presentation_layer.rest_api.routers.v1 import (
    healthcheck_router,
    database_ingestion_router,
    send_queries_router,
    test_router,
)

router = APIRouter()
router.include_router(router=healthcheck_router.router, tags=["healthcheck"])
router.include_router(
    router=database_ingestion_router.router, tags=["database-ingestion"]
)
router.include_router(router=send_queries_router.router, tags=["send-queries"])
router.include_router(router=test_router.router, tags=["tests"])
