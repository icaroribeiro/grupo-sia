from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, Response, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from src.layers.core_logic_layer.container.container import Container
from src.layers.core_logic_layer.logging import logger
from src.layers.presentation_layer.rest_api.schemas.healthcheck_schema import (
    HealthcheckResponse,
)

router = APIRouter()


@router.get(
    "/healthcheck",
    response_model=HealthcheckResponse,
    response_model_exclude_none=True,
    status_code=status.HTTP_200_OK,
)
@inject
async def healthcheck(
    response: Response,
    postgresdb_async_session: AsyncSession = Depends(
        Provide[Container.postgresdb_async_session]
    ),
):
    healthcheck_response: HealthcheckResponse
    try:
        async with postgresdb_async_session as async_session:
            sql_statement = text("""SELECT 1""")
            await async_session.execute(statement=sql_statement)
            healthcheck_response = HealthcheckResponse()
            return healthcheck_response
    except Exception as error:
        message = f"Error: Failed to check if application is healthy: {error}"
        logger.error(message)
        healthcheck_response = HealthcheckResponse.model_validate(
            obj={"status": "Unhealthy"}
        )
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return healthcheck_response
