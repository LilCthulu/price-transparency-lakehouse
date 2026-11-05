"""For the 10 codes (CPT/HCPCS, MS-DRG only), count rows that actually carry a usable dollar rate, per file."""
import gzip, json, sys, duckdb
CPT = ("70553","74177","76700","77067","45378","43235","66984","29881","80053")
con = duckdb.connect()
for f in ["vumc_main", "ascension_west", "ascension_midtown"]:
    p = f"data/m0/{f}.parquet"
    cols = [r[0] for r in con.sql(f"describe select * from '{p}'").fetchall()]
    codes = [c for c in cols if c.startswith("code|") and not c.endswith("|type")]
    u = " union all ".join(f'select "{c}" code, "{c}|type" t, payer_name, "standard_charge|negotiated_dollar" d, "standard_charge|negotiated_percentage" pc, "standard_charge|negotiated_algorithm" a from \'{p}\'' for c in codes)
    q = f"""select code, count(*) n, count(distinct payer_name) payers, count(d) dollars, count(pc) pct, count(a) algo from ({u})
            where (code in {CPT} and t in ('CPT','HCPCS')) or (code='470' and t='MS-DRG') group by 1 order by 1"""
    print(f); [print(" ", r) for r in con.sql(q).fetchall()]
for f in ["vumc_clarksville", "tristar_centennial"]:
    agg = {}
    with gzip.open(f"data/m0/{f}.ndjson.gz", "rt", encoding="utf-8") as h:
        for line in h:
            it = json.loads(line)
            ks = {str(c.get("code")).strip() for c in it.get("code_information", []) if (str(c.get("code")).strip() in CPT and c.get("type") in ("CPT","HCPCS")) or (str(c.get("code")).strip()=="470" and c.get("type")=="MS-DRG")}
            for k in ks:
                a = agg.setdefault(k, {"n":0,"payers":set(),"d":0,"p":0,"a":0})
                for sc in it.get("standard_charges", []):
                    for pi in sc.get("payers_information") or []:
                        a["n"]+=1; a["payers"].add(pi.get("payer_name")); a["d"]+=pi.get("standard_charge_dollar") is not None; a["p"]+=pi.get("standard_charge_percentage") is not None; a["a"]+=pi.get("standard_charge_algorithm") is not None
    print(f); [print(" ", k, v["n"], len(v["payers"]), v["d"], v["p"], v["a"]) for k,v in sorted(agg.items())]
