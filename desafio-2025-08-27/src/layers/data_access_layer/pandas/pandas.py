import os

import pandas as pd
from src.layers.data_access_layer.pandas.models.dataframe_params import DataFrameParams
from src.layers.core_logic_layer.settings import app_settings


class Pandas:
    @staticmethod
    def create_input_dataframes_from_files(
        directory_path: str,
    ) -> dict[str, DataFrameParams]:
        dataframes_dict = {}

        for filename in os.listdir(directory_path):
            if filename.endswith(".xlsx"):
                file_path = os.path.join(directory_path, filename)

                match filename:
                    case "ADMISSÃO ABRIL.xlsx":
                        df = pd.read_excel(
                            file_path,
                            header=0,
                            names=[
                                "employee_id",
                                "admission_date",
                                "job_title",
                                "column_4",
                            ],
                            index_col=None,
                        )
                        dataframes_dict["df_employee_admission"] = DataFrameParams(
                            name="df_employee_admission", description="", content=df
                        )
                    case "AFASTAMENTOS.xlsx":
                        df = pd.read_excel(
                            file_path,
                            header=0,
                            names=[
                                "employee_id",
                                "situation_desc",
                                "column_3",
                                "detail",
                            ],
                            index_col=None,
                        )
                        dataframes_dict["df_employee_absense"] = DataFrameParams(
                            name="df_employee_absense", description="", content=df
                        )
                    case "APRENDIZ.xlsx":
                        df = pd.read_excel(
                            file_path,
                            header=0,
                            names=[
                                "employee_id",
                                "job_title",
                            ],
                            index_col=None,
                        )
                        dataframes_dict["df_apprentice_employee"] = DataFrameParams(
                            name="df_apprentice_employee", description="", content=df
                        )
                    case "ATIVOS.xlsx":
                        df = pd.read_excel(
                            file_path,
                            header=0,
                            names=[
                                "employee_id",
                                "company_id",
                                "job_title",
                                "situation_desc",
                                "syndicate_name",
                            ],
                            index_col=None,
                        )
                        dataframes_dict["df_active_employee"] = DataFrameParams(
                            name="df_active_employee",
                            description="",
                            content=df,
                        )
                    case "Base dias uteis.xlsx":
                        df = pd.read_excel(
                            file_path,
                            header=1,
                            names=[
                                "name",
                                "working_days",
                            ],
                            index_col=None,
                        ).dropna()
                        dataframes_dict["df_syndicate_working_days"] = DataFrameParams(
                            name="df_syndicate_working_days",
                            description="",
                            content=df,
                        )
                    case "Base sindicato x valor.xlsx":
                        df = pd.read_excel(
                            file_path,
                            header=0,
                            names=[
                                "state",
                                "meal_voucher_value",
                            ],
                            index_col=None,
                        ).dropna()
                        dataframes_dict["df_syndicate_meal_voucher_value"] = (
                            DataFrameParams(
                                name="df_syndicate_meal_voucher_value",
                                description="",
                                content=df,
                            )
                        )
                    case "DESLIGADOS.xlsx":
                        df = pd.read_excel(
                            file_path,
                            header=0,
                            names=[
                                "employee_id",
                                "termination_date",
                                "termination_notice",
                            ],
                            index_col=None,
                        )
                        dataframes_dict["df_employee_dismissal"] = DataFrameParams(
                            name="df_employee_dismissal", description="", content=df
                        )
                    case "ESTÁGIO.xlsx":
                        df = pd.read_excel(
                            file_path,
                            header=0,
                            names=[
                                "employee_id",
                                "job_title",
                                "column_3",
                            ],
                            index_col=None,
                        )
                        dataframes_dict["df_intern_employee"] = DataFrameParams(
                            name="df_intern_employee", description="", content=df
                        )
                    case "EXTERIOR.xlsx":
                        df = pd.read_excel(
                            file_path,
                            header=0,
                            names=[
                                "register",
                                "value",
                                "column_3",
                            ],
                            index_col=None,
                        )
                        dataframes_dict["df_employee_abroad"] = DataFrameParams(
                            name="df_employee_abroad", description="", content=df
                        )
                    case "FÉRIAS.xlsx":
                        df = pd.read_excel(
                            file_path,
                            header=0,
                            names=[
                                "employee_id",
                                "situation_desc",
                                "vacation_days",
                            ],
                            index_col=None,
                        )
                        dataframes_dict["df_employee_vacation"] = DataFrameParams(
                            name="df_employee_vacation", description="", content=df
                        )

        # Save each DataFrame to a CSV file and return the dictionary
        output_dir = f"{app_settings.output_data_dir_path}"
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        for name, df_params in dataframes_dict.items():
            if not df_params.content.empty:
                df_params.content.to_csv(
                    os.path.join(output_dir, f"{name}.csv"), index=False
                )

        return dataframes_dict
