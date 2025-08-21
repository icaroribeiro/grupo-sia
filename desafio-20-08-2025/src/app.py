from src.layers.business_layer.services.meal_voucher_service import MealVoucherService
from src.layers.core_logic_layer.container.container import Container
from src.layers.data_access_layer.pandas.models.dataframe_params import DataFrameParams
from src.layers.core_logic_layer.settings import ai_settings, app_settings
from src.layers.data_access_layer.pandas.pandas import Pandas


class App:
    def __init__(self, meal_voucher_service: MealVoucherService) -> None:
        pandas: Pandas = Pandas()
        dataframes_dict: dict[str, DataFrameParams] = (
            pandas.create_input_dataframes_from_files(app_settings.input_data_dir_path)
        )
        container: Container = Container()
        container.config.ai_settings.from_value(ai_settings)
        container.config.dataframes_dict.from_value(dataframes_dict)
        container.wire(
            packages=[
                "src.layers.business_layer.services",
            ]
        )
        self.meal_voucher_service = meal_voucher_service

    async def run(self) -> None:
        await self.meal_voucher_service.run()
