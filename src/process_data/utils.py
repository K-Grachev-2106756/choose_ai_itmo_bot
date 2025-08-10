import os

import pandas as pd

from src.config import data_dir


def load_plan(name: str):
    df = pd.read_csv(os.path.join(data_dir, f"uchebny_plan_{name}.csv"))
    return "; ".join([
        "\"" + v.replace("\n", "") + "\"" for v in df["Unnamed: 1"].values[2:]
    ])
