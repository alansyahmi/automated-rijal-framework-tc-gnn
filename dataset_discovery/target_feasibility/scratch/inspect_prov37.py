import json
import pyarrow.parquet as pq
from pathlib import Path

root = Path(".")
shamela_path = root / "data/1_raw/Shamela4_Full_DB/_meta/narrators.parquet"

table = pq.read_table(shamela_path)
records = table.to_pylist()

rec_37 = next((r for r in records if str(r["id"]) == "1740"), None)
if rec_37:
    print("ID:", rec_37["id"])
    print("Short name:", rec_37["short_name"])
    print("Long name:", rec_37["long_name"])
    print("Narrator type:", rec_37["narrator_type"])
    bio = json.loads(rec_37["biography_text"]) if rec_37["biography_text"] else {}
    print("Summary:")
    for pair in bio.get("summary", []):
        print(f"  {pair[0]}: {pair[1]}")
    crit = json.loads(rec_37["criticism_text"]) if rec_37["criticism_text"] else {}
    print("Criticism critics count:", len(crit.get("garh", [])))
    for critic_item in crit.get("garh", []):
        c_name = critic_item[0]
        q_count = len(critic_item[1])
        first_q = critic_item[1][0][0] if critic_item[1] else ""
        print(f"  Critic: {c_name} ({q_count} quotes) -> {first_q[:120]}...")
else:
    print("Record 1740 not found!")

