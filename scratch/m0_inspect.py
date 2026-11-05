"""M0 steps 0.6, 0.7, 0.9, 0.10 for one file: metadata, staging, the 10 codes, payer names.

Usage: m0_inspect.py <source file> <staged output> <report.json>
Each step records its own error, so one bad step still leaves the others' results.
"""
import collections
import gzip
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from stage import detect_csv_layout, read_csv_meta, read_json_meta, stage_csv, stage_json  # noqa: E402

CPT = {"70553", "74177", "76700", "77067", "45378", "43235", "66984", "29881", "80053"}
DRG = re.compile(r"^(?:ms-?drg[\s-]*|drg[\s-]*)?0*470$", re.I)
META_KEYS = ["version", "last_updated_on", "location_name", "hospital_name", "type_2_npi", "attester_name", "attestation"]


def wanted(code: str, typ: str) -> bool:
    return code in CPT or bool(DRG.match(code))


def inspect_csv(src, out, rep):
    meta, cols = read_csv_meta(src)
    rep["layout"] = detect_csv_layout(cols)
    rep["column_count"] = len(cols)
    rep["columns_sample"] = cols[:40]
    rep["meta"] = {k: meta.get(k) for k in META_KEYS if k in meta}
    rep["meta_keys"] = sorted(meta)
    _, _, rep["rows"] = stage_csv(src, out)

    import pyarrow.parquet as pq
    pf = pq.ParquetFile(out)
    code_cols = [c for c in cols if c.startswith("code|") and not c.endswith("|type")]
    read = code_cols + [f"{c}|type" for c in code_cols if f"{c}|type" in cols]
    has_payer = "payer_name" in cols
    if has_payer:
        read.append("payer_name")
    hits, payers = collections.Counter(), collections.Counter()
    for batch in pf.iter_batches(columns=read, batch_size=200_000):
        d = batch.to_pydict()
        for c in code_cols:
            types = d.get(f"{c}|type") or [None] * batch.num_rows
            for code, typ in zip(d[c], types):
                if code and wanted(code.strip(), typ or ""):
                    hits[f"{code.strip()}|{typ}"] += 1
        if has_payer:
            payers.update(p for p in d["payer_name"] if p)
    rep["code_hits"] = dict(sorted(hits.items()))
    rep["payers"] = sorted(payers)
    rep["wide_payer_plans"] = sorted({"|".join(c.split("|")[1:3]) for c in cols
                                      if c.startswith("standard_charge|") and c.count("|") == 3})


def inspect_json(src, out, rep):
    rep["layout"] = "json"
    _, rep["rows"] = stage_json(src, out)
    meta = read_json_meta(src)
    rep["meta"] = {k: meta.get(k) for k in META_KEYS if k in meta}
    rep["meta_keys"] = sorted(meta)
    hits, payers = collections.Counter(), collections.Counter()
    with gzip.open(out, "rt", encoding="utf-8") as f:
        for line in f:
            item = json.loads(line)
            for c in item.get("code_information") or []:
                code = str(c.get("code") or "").strip()
                if wanted(code, c.get("type") or ""):
                    hits[f"{code}|{c.get('type')}"] += 1
            for sc in item.get("standard_charges") or []:
                for p in sc.get("payers_information") or []:
                    if p.get("payer_name"):
                        payers[p["payer_name"]] += 1
    rep["code_hits"] = dict(sorted(hits.items()))
    rep["payers"] = sorted(payers)


def main(src, out, report):
    rep = {"file": os.path.basename(src), "bytes": os.path.getsize(src)}
    try:
        (inspect_csv if src.endswith(".csv") else inspect_json)(src, out, rep)
    except Exception as e:  # record it: a parse failure is itself an M0 finding
        rep["error"] = f"{type(e).__name__}: {e}"
    with open(report, "w", encoding="utf-8") as f:
        json.dump(rep, f, indent=1, ensure_ascii=False)
    print(json.dumps({k: v for k, v in rep.items() if k not in ("payers", "columns_sample", "wide_payer_plans")}, ensure_ascii=False))
    print("payers:", len(rep.get("payers", [])), "wide plans:", len(rep.get("wide_payer_plans", [])))


if __name__ == "__main__":
    main(*sys.argv[1:4])
