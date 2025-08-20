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
                                "employee_id_employee_admission_df",
                                "admission_date_employee_admission_df",
                                "job_title_employee_admission_df",
                                "column_4_employee_admission_df",
                            ],
                            index_col=None,
                        )
                        dataframes_dict["employee_admission_df"] = DataFrameParams(
                            name="employee_admission_df", description="", content=df
                        )
                    case "AFASTAMENTOS.xlsx":
                        df = pd.read_excel(
                            file_path,
                            header=0,
                            names=[
                                "employee_id_employee_absense_df",
                                "situation_desc_employee_absense_df",
                                "column_3_employee_absense_df",
                                "detail_employee_absense_df",
                            ],
                            index_col=None,
                        )
                        dataframes_dict["employee_absense_df"] = DataFrameParams(
                            name="employee_absense_df", description="", content=df
                        )
                    case "APRENDIZ.xlsx":
                        df = pd.read_excel(
                            file_path,
                            header=0,
                            names=[
                                "employee_id_apprentice_employee_df",
                                "job_title_apprentice_employee_df",
                            ],
                            index_col=None,
                        )
                        dataframes_dict["apprentice_employee_df"] = DataFrameParams(
                            name="apprentice_employee_df", description="", content=df
                        )
                    case "ATIVOS.xlsx":
                        df = pd.read_excel(
                            file_path,
                            header=0,
                            names=[
                                "employee_id_active_employee_df",
                                "company_id_active_employee_df",
                                "job_title_active_employee_df",
                                "situation_desc_active_employee_df",
                                "syndicate_name_active_employee_df",
                            ],
                            index_col=None,
                        )
                        dataframes_dict["active_employee_df"] = DataFrameParams(
                            name="active_employee_df",
                            description="",
                            content=df,
                        )
                    case "Base dias uteis.xlsx":
                        df = pd.read_excel(
                            file_path,
                            header=1,
                            names=[
                                "name_syndicate_working_days_df",
                                "working_days_syndicate_working_days_df",
                            ],
                            index_col=None,
                        ).dropna()
                        dataframes_dict["syndicate_working_days_df"] = DataFrameParams(
                            name="syndicate_working_days_df",
                            description="",
                            content=df,
                        )
                    case "Base sindicato x valor.xlsx":
                        df = pd.read_excel(
                            file_path,
                            header=0,
                            names=[
                                "state_syndicate_meal_voucher_value_df",
                                "meal_voucher_value_syndicate_meal_voucher_value_df",
                            ],
                            index_col=None,
                        ).dropna()
                        dataframes_dict["syndicate_meal_voucher_value_df"] = (
                            DataFrameParams(
                                name="syndicate_meal_voucher_value_df",
                                description="",
                                content=df,
                            )
                        )
                    case "DESLIGADOS.xlsx":
                        df = pd.read_excel(
                            file_path,
                            header=0,
                            names=[
                                "employee_id_employee_dismissal_df",
                                "termination_date_employee_dismissal_df",
                                "termination_notice_employee_dismissal_df",
                            ],
                            index_col=None,
                        )
                        dataframes_dict["employee_dismissal_df"] = DataFrameParams(
                            name="employee_dismissal_df", description="", content=df
                        )
                    case "ESTÁGIO.xlsx":
                        df = pd.read_excel(
                            file_path,
                            header=0,
                            names=[
                                "employee_id_intern_employee_df",
                                "job_title_intern_employee_df",
                                "column_3_intern_employee_df",
                            ],
                            index_col=None,
                        )
                        dataframes_dict["intern_employee_df"] = DataFrameParams(
                            name="intern_employee_df", description="", content=df
                        )
                    case "EXTERIOR.xlsx":
                        df = pd.read_excel(
                            file_path,
                            header=0,
                            names=[
                                "register_employee_abroad_df",
                                "value_employee_abroad_df",
                                "column_3_employee_abroad_df",
                            ],
                            index_col=None,
                        )
                        # Drop the last two columns using iloc
                        # df = df.iloc[:, :-2]
                        dataframes_dict["employee_abroad_df"] = DataFrameParams(
                            name="employee_abroad_df", description="", content=df
                        )
                    case "FÉRIAS.xlsx":
                        df = pd.read_excel(
                            file_path,
                            header=0,
                            names=[
                                "employee_id_employee_vacation_df",
                                "situation_desc_employee_vacation_df",
                                "vacation_days_employee_vacation_df",
                            ],
                            index_col=None,
                        )
                        dataframes_dict["employee_vacation_df"] = DataFrameParams(
                            name="employee_vacation_df", description="", content=df
                        )

        # Save each DataFrame to a CSV file and return the dictionary
        output_dir = f"{app_settings.output_data_dir_path}/tmp/"
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        for name, df_params in dataframes_dict.items():
            if not df_params.content.empty:
                df_params.content.to_csv(
                    os.path.join(output_dir, f"{name}.csv"), index=False
                )

        return dataframes_dict
