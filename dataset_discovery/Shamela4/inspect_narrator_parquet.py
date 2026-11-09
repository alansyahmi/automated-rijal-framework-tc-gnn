
import argparse
import json
from pathlib import Path

import pyarrow.parquet as pq


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("--sample", type=int, default=3)
    args = parser.parse_args()

    pf = pq.ParquetFile(args.input)

    print("=== PARQUET METADATA ===")
    print("File:", args.input)
    print("Rows:", pf.metadata.num_rows)
    print("Row groups:", pf.metadata.num_row_groups)
    print("Columns:", pf.metadata.num_columns)
    print("File size:", args.input.stat().st_size)

    print("\n=== SCHEMA ===")
    print(pf.schema)

    print("\n=== ARROW SCHEMA ===")
    print(pf.schema_arrow)

    print("\n=== SAMPLE RECORDS ===")

    count = 0
    for batch in pf.iter_batches(batch_size=args.sample):
        for record in batch.to_pylist():
            count += 1
            print(f"\n--- RECORD {count} ---")

            # Keep the output manageable while inspecting
            # large nested quotation structures.
            rendered = json.dumps(
                record,
                ensure_ascii=False,
                indent=2,
                default=str
            )

            print(rendered[:12000])

            if count >= args.sample:
                return


if __name__ == "__main__":
    main()
