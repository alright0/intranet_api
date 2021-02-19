import pandas as pd

from pathlib import Path


def make_table():

    path = Path(__file__).parents[0]
    df = pd.read_csv(path / "TP.csv", sep=";", index_col=None)

    return df.to_html()