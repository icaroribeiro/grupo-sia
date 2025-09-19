import pandas as pd


class Pandas:
    @staticmethod
    def create_input_dataframe_from_file(
        file_path: str,
    ) -> pd.DataFrame:
        return pd.read_csv(
            file_path,
            header=0,
            index_col=None,
        )
