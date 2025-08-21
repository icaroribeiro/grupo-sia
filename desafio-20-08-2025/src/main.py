import asyncio
from src.app import App
from src.layers.business_layer.services.meal_voucher_service import MealVoucherService
from src.layers.core_logic_layer.logging import logger


async def main() -> None:
    meal_voucher_service: MealVoucherService = MealVoucherService()
    app: App = App(meal_voucher_service=meal_voucher_service)
    try:
        logger.info("Starting Application execution...")
        await app.run()
        logger.info("Application executed successfully")
    except Exception as error:
        message = f"Failed to execute Application: {str(error)}"
        logger.error(message)
        raise


if __name__ == "__main__":
    asyncio.run(main=main())
