from pathlib import Path
import pandas as pd
DATA=Path(__file__).resolve().parents[1]/"data"
EXPECTED={"sales.csv":50000,"orders.csv":25000,"customers.csv":10000,"products.csv":40}
for name,minimum in EXPECTED.items():
    p=DATA/name
    if not p.exists(): raise FileNotFoundError(p)
    rows=len(pd.read_csv(p))
    if rows<minimum: raise ValueError(f"{name}: expected at least {minimum:,}, found {rows:,}")
    print(f"{name}: {rows:,} rows")
print("NEXORAAI company dataset validated successfully.")
