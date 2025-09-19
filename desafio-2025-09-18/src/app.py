from src.layers.core_logic_layer.container.container import Container
from src.layers.data_access_layer.pandas.models.dataframe_params import DataFrameParams
from src.layers.core_logic_layer.settings import ai_settings, app_settings
from src.layers.data_access_layer.pandas.pandas import Pandas
from dependency_injector.wiring import inject
from dependency_injector.wiring import Provide

from src.layers.business_layer.ai_agents.workflows.meal_voucher_calculation_workflow import (
    MealVoucherCalculationWorkflow,
)
from src.layers.core_logic_layer.logging import logger


class App:
    def __init__(self) -> None:
        pandas: Pandas = Pandas()
        dataframes_dict: dict[str, DataFrameParams] = (
            pandas.create_input_dataframes_from_files(app_settings.input_data_dir_path)
        )
        container: Container = Container()
        container.config.app_settings.from_value(app_settings)
        container.config.ai_settings.from_value(ai_settings)
        container.config.dataframes_dict.from_value(dataframes_dict)
        container.wire(
            modules=[
                "src.app",
            ]
        )

    @inject
    async def run(
        self,
        meal_voucher_calculation_workflow: MealVoucherCalculationWorkflow = Provide[
            Container.meal_voucher_calculation_workflow
        ],
    ) -> None:
        input_message: str = """
        INSTRUCTIONS:     
        - Perform a multi-step procedure to generate spreadsheets based on data processing.
        - The procedure consists of the following tasks directed to nodes:
            1. Data wrangling
            2. Data analysis
            3. Data reporting
        """

        result = await meal_voucher_calculation_workflow.run(
            input_message=input_message
        )
        logger.info(f"result: {result}")
