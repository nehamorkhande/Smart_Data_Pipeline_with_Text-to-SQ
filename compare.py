
import glob
import pandas as pd

rows = []
for file in glob.glob("results/*.csv"):
    df = pd.read_csv(file)
    rows.append({
        "model": df["model"][0],
        "tests": len(df),
        "accuracy_%": round(df["passed"].mean() * 100, 1),
        "errors": df["error"].sum(),
        "avg_seconds": round(df["seconds"].mean(), 1),
    })

table = pd.DataFrame(rows).sort_values("accuracy_%", ascending=False)
print(table.to_string(index=False))