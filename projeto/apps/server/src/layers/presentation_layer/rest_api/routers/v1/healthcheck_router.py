from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, Response, status
# from motor.motor_asyncio import AsyncIOMotorClient

from src.layers.core_logic_layer.container.container import Container
from sqlalchemy import text
from src.layers.core_logic_layer.logging import logger
from src.layers.data_access_layer.postgresdb.models.consumer_model import Consumer
from src.layers.presentation_layer.rest_api.schemas.healthcheck_schema import (
    HealthcheckResponse,
)
from sqlalchemy.ext.asyncio import AsyncSession

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
    # mongodb_client_resource: AsyncIOMotorClient = Depends(
    #     Provide[Container.mongodb_client_resource]
    # ),
    postgresdb_async_session: AsyncSession = Depends(
        Provide[Container.postgresdb_async_session]
    ),
):
    healthcheck_response: HealthcheckResponse
    try:
        print("AAAAAAAA")
        # await mongodb_client_resource["admin"].command("ping")
        result = await postgresdb_async_session.execute(statement=text("""SELECT 1"""))
        print(f"result: {result}")
        for data in result:
            if data[0] == 1:
                print("funciona!")

                result = await postgresdb_async_session.get(Consumer, 1)
                # result = await postgresdb_async_session.execute(query)
                print(result.name)

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
