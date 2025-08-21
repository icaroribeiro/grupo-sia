from dependency_injector.wiring import inject
from dependency_injector.wiring import Provide

from src.layers.business_layer.ai_agents.workflows.meal_voucher_workflow import (
    MealVoucherWorkflow,
)
from src.layers.core_logic_layer.container.container import Container
from src.layers.core_logic_layer.logging import logger


class MealVoucherService:
    @inject
    async def run(
        self,
        meal_voucher_workflow: MealVoucherWorkflow = Provide[
            Container.meal_voucher_workflow
        ],
    ) -> None:
        input: str = """
            INSTRUCTIONS:     
            - Perform the following steps in the order listed to complete a multi-step data processing task.
            - The data processing consists of three stages, and you must delegate the work to a single agent for each stage.
            - The stages are:
                1. Data Gathering
                2. Data Analysis
                3. Data Reporting
            - You must always delegate to ONE AGENT AT TIME.
            - You must wait for the result of the current agent's task before moving to the next stage.
            CRITICAL RULES:
            - Do NOT ask for additional input. All tasks are fully defined.
            - Each stage is dependent on the successful completion of the previous one.
            - DO NOT begin the next stage until the current one is fully completed and verified.
            """
        formatted_input_message: str = input

        result = await meal_voucher_workflow.run(input_message=formatted_input_message)
        logger.info(f"result: {result}")
