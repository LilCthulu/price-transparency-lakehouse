import collections, glob, json, os
for r in sorted(glob.glob("notes/m0/*.json")):
    d = json.load(open(r, encoding="utf-8")); b = os.path.basename(r)[:-5]
    v = json.load(open(f"notes/validator_{b}.json", encoding="utf-8"))
    print("=" * 8, b, d["bytes"], d.get("layout"), "cols", d.get("column_count"), "rows", d.get("rows"), "ERROR" if d.get("error") else "", d.get("error", ""))
    print("meta", d.get("meta")); print("keys", d.get("meta_keys"))
    print("validator", v.get("validatorVersion"), v.get("dataDictionaryVersion"), "valid", v.get("valid"), "errors", v.get("errorCount"), "alerts", v.get("alertCount"), "returned", len(v.get("errors", [])))
    msgs = collections.Counter(str(e.get("message") or e)[:110] for e in v.get("errors", []))
    print("top", msgs.most_common(3))
    a = collections.Counter(str(e.get("message") or e)[:110] for e in v.get("alerts", []))
    print("alerts", a.most_common(2))
    agg = collections.Counter()
    for k, n in d.get("code_hits", {}).items(): agg[k] += n
    print("hits", dict(agg))
    print("payers", len(d.get("payers", [])), d.get("payers", [])[:60])
    print("wide", len(d.get("wide_payer_plans", [])), d.get("wide_payer_plans", [])[:10])
