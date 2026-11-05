"""West vs Midtown null-safe price overlap, and physician-fee markers across the M0 files. Usage: m2_compare.py <data/m0 dir>"""
import gzip
import json
import sys
from collections import Counter

import duckdb

D = sys.argv[1].replace("\\", "/")
CPT = ("70553", "74177", "76700", "77067", "45378", "43235", "66984", "29881", "80053")
con = duckdb.connect()
d = '"standard_charge|negotiated_dollar"'
n = '"additional_generic_notes"'


def ten_codes(name):
    p = f"{D}/{name}.parquet"
    cols = [r[0] for r in con.sql(f"describe select * from '{p}'").fetchall()]
    codes = [c for c in cols if c.startswith("code|") and not c.endswith("|type")]
    u = " union all ".join(f"""select "{c}" code, "{c}|type" t, * from '{p}'""" for c in codes)
    return f"(select * from ({u}) where (code in {CPT} and t in ('CPT','HCPCS')) or (code='470' and t='MS-DRG'))"


w, m = ten_codes("ascension_west"), ten_codes("ascension_midtown")
key = "code, coalesce(setting,'') s, coalesce(payer_name,'') p, coalesce(plan_name,'') pl"
q = lambda s: f"select {key}, min(try_cast({d} as double)) lo, max(try_cast({d} as double)) hi from {s} group by all"
print("west/midtown keys joined, identical min and max, differ:", con.sql(
    f"""select count(*), count(*) filter (where a.lo=b.lo and a.hi=b.hi), count(*) filter (where a.lo<>b.lo or a.hi<>b.hi)
    from ({q(w)}) a join ({q(m)}) b on a.code=b.code and a.s=b.s and a.p=b.p and a.pl=b.pl""").fetchall())
for name, s in (("west", w), ("midtown", m)):
    print(name, "keys", con.sql(f"select count(*) from ({q(s)})").fetchall(), "with Provider Type:",
          con.sql(f"select count(*) filter (where {n} ilike '%provider type%' or {n} ilike '%physician%' or {n} ilike '%professional%'), count(*) from {s}").fetchall())
    print("  top notes", con.sql(f"select left({n},70), count(*) from {s} group by 1 order by 2 desc limit 4").fetchall())
print("midtown 70553 by median vs west:", con.sql(f"select median(try_cast({d} as double)) from {w} where code='70553'").fetchall(),
      con.sql(f"select median(try_cast({d} as double)) from {m} where code='70553'").fetchall())

for f in ("vumc_clarksville", "tristar_centennial"):
    notes, total = Counter(), 0
    with gzip.open(f"{D}/{f}.ndjson.gz", "rt", encoding="utf-8") as h:
        for line in h:
            it = json.loads(line)
            if not any((str(c.get("code")).strip() in CPT and c.get("type") in ("CPT", "HCPCS"))
                       or (str(c.get("code")).strip() == "470" and c.get("type") == "MS-DRG") for c in it.get("code_information", [])):
                continue
            for sc in it.get("standard_charges", []):
                for pi in sc.get("payers_information") or []:
                    total += 1
                    x = str(pi.get("additional_payer_notes") or sc.get("additional_generic_notes") or "")
                    notes["prof" if any(k in x.lower() for k in ("provider type", "physician", "professional", "anesthes")) else "other"] += 1
                    notes["note:" + x[:60]] += 1
    print(f, total, notes.most_common(6))
