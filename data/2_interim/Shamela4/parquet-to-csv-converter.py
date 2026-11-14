import pandas as pd
from pathlib import Path

# 1. Get the file path from the user
user_input = input("Enter the path to your parquet file: ")

# 2. Strip accidental quotes that occur when dragging/dropping a file into the terminal
clean_path = user_input.strip("'\"")

# 3. Convert to a system-agnostic Path object
file_path = Path(clean_path)

# 4. Verify existence, read the Parquet file, and convert to CSV
if not file_path.is_file():
    print(f"Error: The file at '{file_path}' does not exist.")
else:
    try:
        # Read the Parquet file directly using pandas
        print(f"Reading '{file_path.name}'...")
        df = pd.read_parquet(file_path)

        # Output CSV path: saves alongside the input file (e.g. data.parquet -> data.csv)
        output_csv = file_path.with_suffix(".csv")

        # Save as CSV (index=False avoids writing extra row index column)
        df.to_csv(output_csv, index=False, encoding="utf-8-sig")
        print(f"Success! Saved to '{output_csv}' ({len(df)} rows)")
    except Exception as e:
        print(f"Error converting file: {e}")

