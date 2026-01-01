import sys
import pandas as pd
print("arguments", sys.argv)

day = int(sys.argv[1])

df = pd.DataFrame({"A": [1, 2], "B": [3, 4]})
df['day'] = day

df.to_parquet(f"output_day_{day}.parquet")

print(df.head())

print(f"Running pipeline for day {day}")