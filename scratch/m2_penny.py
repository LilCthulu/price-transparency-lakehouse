"""Explain low VUMC dollar rates, and compare Midtown against West prices. Usage: m2_penny.py <data/m0 dir>"""
import sys

import duckdb

D = sys.argv[1].replace("\\", "/")
CPT = ("70553", "74177", "76700", "77067", "45378", "43235", "66984", "29881", "80053")
con = duckdb.connect()


def ten_codes(name):
    p = f"{D}/{name}.parquet"
    cols = [r[0] for r in con.sql(f"describe select * from '{p}'").fetchall()]
    codes = [c for c in cols if c.startswith("code|") and not c.endswith("|type")]
    u = " union all ".join(f"""select "{c}" code, "{c}|type" t, * from '{p}'""" for c in codes)
    return f"(select * from ({u}) where (code in {CPT} and t in ('CPT','HCPCS')) or (code='470' and t='MS-DRG'))"


v = ten_codes("vumc_main")
d = '"standard_charge|negotiated_dollar"'
print("VUMC lowest dollar values, 10 codes")
for r in con.sql(f"select try_cast({d} as double) x, count(*) from {v} where try_cast({d} as double) is not null "
                 "group by 1 order by 1 limit 12").fetchall():
    print(" ", r)
print("VUMC rows under $5, 10 codes")
cols = ['code', 't', 'description', 'setting', 'payer_name', 'plan_name', d,
        '"standard_charge|negotiated_percentage"', '"standard_charge|negotiated_algorithm"',
        '"standard_charge|methodology"', '"standard_charge|gross"', '"standard_charge|discounted_cash"',
        '"estimated_amount"', '"additional_payer_notes"', '"additional_generic_notes"']
have = {r[0] for r in con.sql(f"describe select * from {v}").fetchall()}
use = [c for c in cols if c.strip('"') in have]
print(" ", [c.strip('"') for c in use])
for r in con.sql(f"select {','.join(use)} from {v} where try_cast({d} as double) < 5 order by try_cast({d} as double) limit 25").fetchall():
    print(" ", r)
print("Same payer and plan, same code, other VUMC rows: median and count")
for r in con.sql(f"""with low as (select distinct code, setting, payer_name, plan_name from {v} where try_cast({d} as double) < 5)
  select a.code, a.setting, a.payer_name, a.plan_name, count(*), median(try_cast(a.{d} as double)), max(try_cast(a.{d} as double))
  from {v} a join low using (code, setting, payer_name, plan_name) group by all order by 1,2,3,4 limit 25""").fetchall():
    print(" ", r)
n = '"additional_generic_notes"'
ptype = f"regexp_extract({n}, 'Provider Type: ([^|]*)', 1)"
print("VUMC 10 codes: by provider type present, code")
for r in con.sql(f"""select code, {ptype} <> '' prof, count(*), count(try_cast({d} as double)),
   median(try_cast({d} as double)), min(try_cast({d} as double)), max(try_cast({d} as double))
   from {v} group by all order by 1,2""").fetchall():
    print(" ", r)
print("VUMC top note shapes")
for r in con.sql(f"""select regexp_replace(regexp_extract({n}, 'Provider Type: ([^|]*)', 1), ';.*', '') p, count(*) from {v} group by 1 order by 2 desc limit 12""").fetchall():
    print(" ", r)
print("VUMC sample notes without provider type")
for r in con.sql(f"select code, payer_name, {d}, {n} from {v} where {ptype} = '' and {d} is not null limit 6").fetchall():
    print(" ", r)

w, m = ten_codes("ascension_west"), ten_codes("ascension_midtown")
print("West vs Midtown on code, setting, payer, plan")
q = lambda s: f"select code, setting, payer_name, plan_name, median(try_cast({d} as double)) x from {s} group by all"
print(" ", con.sql(f"""select count(*), count(*) filter (where a.x = b.x), count(*) filter (where a.x <> b.x)
  from ({q(w)}) a join ({q(m)}) b using (code, setting, payer_name, plan_name)""").fetchall())
print("  rows west, midtown:", con.sql(f"select count(*) from {w}").fetchall(), con.sql(f"select count(*) from {m}").fetchall())
for name, s in (("west", w), ("midtown", m)):
    print(" ", name, "sample", con.sql(f"select code, payer_name, {d}, {n} from {s} where {d} is not null limit 2").fetchall())
