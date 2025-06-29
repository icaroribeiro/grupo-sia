from fastapi import APIRouter

from src.layers.presentation_layer.routers.v1 import healthcheck_router, uploads_router


v1_router = APIRouter()

v1_router.include_router(
    router=healthcheck_router.router,
    prefix="/healthcheck",
    tags=["healthcheck"],
)

v1_router.include_router(router=uploads_router.router, tags=["uploads"])
