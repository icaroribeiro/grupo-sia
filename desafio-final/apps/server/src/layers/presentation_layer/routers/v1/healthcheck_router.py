from fastapi import APIRouter, Depends
from openai import BaseModel
from src.layers.core_logic_layer.logging import logger
from dependency_injector.wiring import inject
from dependency_injector.wiring import Provide
from src.layers.core_logic_layer.container.container import Container
from fastapi import status
from motor.motor_asyncio import AsyncIOMotorDatabase

router = APIRouter()


class MyData(BaseModel):
    name: str


@router.get("/", status_code=status.HTTP_200_OK)
@inject
async def healthcheck(
    database: AsyncIOMotorDatabase = Depends(
        Provide[Container.mongodb_database_resource]
    ),
):
    try:
        await database.command("ping")
        return {"status": "Healthy"}
    except Exception as error:
        message = f"Got an error when checking if MongoDB is alive: {error}"
        logger.error(message)
        raise
