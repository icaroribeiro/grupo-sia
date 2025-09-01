from fastapi import APIRouter

from src.layers.presentation_layer.rest_api.routers.v1 import (
    data_analysis_router,
    data_ingestion_router,
    healthcheck_router,
)

router = APIRouter()
router.include_router(router=healthcheck_router.router, tags=["healthcheck"])
router.include_router(router=data_ingestion_router.router, tags=["data-ingestion"])
router.include_router(router=data_analysis_router.router, tags=["data-reporting"])
