import json
from pathlib import Path

import pandas as pd

from config.settings import RAW_DATA_DIR


class DataLoader:
    """
    Loads datasets from the raw data directory.
    """

    def __init__(self):
        self.data_dir = RAW_DATA_DIR

    def load_json(self, filename: str):
        """
        Load a JSON file.
        """

        file_path = self.data_dir / filename

        if not file_path.exists():
            raise FileNotFoundError(
                f"{filename} not found inside {self.data_dir}"
            )

        with open(file_path, "r", encoding="utf-8") as file:
            return json.load(file)

    def load_csv(self, filename: str):
        """
        Load a CSV file.
        """

        file_path = self.data_dir / filename

        if not file_path.exists():
            raise FileNotFoundError(
                f"{filename} not found inside {self.data_dir}"
            )

        return pd.read_csv(file_path)