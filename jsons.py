import pandas as pd
from pathlib import Path


path = Path(__file__).parents[0]

df = pd.read_json(path / "file.json", index)

print(df)