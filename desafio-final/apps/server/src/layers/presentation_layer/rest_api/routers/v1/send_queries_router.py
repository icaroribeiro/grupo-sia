from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, Response, status

from src.layers.core_logic_layer.container.container import Container
from src.layers.core_logic_layer.logging import logger
from src.layers.presentation_layer.rest_api.schemas.send_queries_schema import (
    SendQueryRequest,
    SendQueryResponse,
)

router = APIRouter()


@router.post(
    "/send-query",
    response_model=SendQueryResponse,
    response_model_exclude_none=True,
    status_code=status.HTTP_201_CREATED,
)
@inject
async def send_query(
    response: Response,
    send_query_request: SendQueryRequest,
    config: dict = Depends(Provide[Container.config]),
):
    logger.info(f"send_query_request.query: {send_query_request.query}")

    return SendQueryResponse(answer="I have no idea!")
