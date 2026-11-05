"""Finish notes/m0_findings.md: per-file tables come straight from the reports, narrative from m0_narrative.md."""
import json
import os

order = ["vumc_main", "vumc_clarksville", "tristar_centennial", "ascension_west", "ascension_midtown"]
R = {b: json.load(open(f"notes/m0/{b}.json", encoding="utf-8")) for b in order}
V = {b: json.load(open(f"notes/validator_{b}.json", encoding="utf-8")) for b in order}
# the validator stores the local absolute path; keep only the file name in a public repo
for b, v in V.items():
    v["file"] = os.path.basename(v["file"])
    with open(f"notes/validator_{b}.json", "w", encoding="utf-8") as f:
        json.dump(v, f, indent=1)

out = [
    "## 0.7 Midtown", "",
    "Midtown is not a location in the West file. West lists only `Ascension Saint Thomas West`. Midtown has its own "
    "file (the third link above), which lists `Ascension Saint Thomas Midtown`, but its `hospital_name` still says "
    "Saint Thomas West and it carries the same type 2 NPI (1629025648). It validates clean and has all 10 codes. "
    "Status: out of scope under the locked 11 files, `STRETCH` as source 12 until Chaz decides.", "",
    "## 0.5, 0.6, 0.8 Per-file facts", "",
    "| file | MB | layout | columns | items or rows | version | file date | type_2_npi | attester | valid | errors | alerts |",
    "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
]
for b in order:
    r, v, m = R[b], V[b], R[b]["meta"]
    att = m.get("attester_name") or (m.get("attestation") or {}).get("attester_name")
    out.append(f"| {b} | {r['bytes'] / 1e6:.0f} | {r['layout']} | {r.get('column_count', 'n/a')} | {r['rows']:,} "
               f"| {m['version']} | {m['last_updated_on']} | {'yes' if m.get('type_2_npi') else 'no'} "
               f"| {'yes' if att else 'no'} | {v['valid']} | {v['errorCount']} | {v['alertCount']} |")
out += ["", "The validator reported no errors, so there are no common error messages to list for any file.", "",
        "## 0.9 Raw code matches (rows, by code and code type)", ""]
for b in order:
    out.append(f"- **{b}:** " + ", ".join(f"{k.replace('|', ' ')} ({n})" for k, n in R[b]["code_hits"].items()))
out += ["", "## 0.10 Payer names (up to 50 per file)", ""]
for b in order:
    p = R[b]["payers"]
    out.append(f"- **{b} ({len(p)} total):** " + "; ".join(f"`{x}`" for x in p[:50]))
narrative = open("scratch/m0_narrative.md", encoding="utf-8").read()
with open("notes/m0_findings.md", "a", encoding="utf-8", newline="\n") as f:
    f.write("\n" + "\n".join(out) + "\n\n" + narrative)

p = "PROJECT_CONTEXT.md"
t = open(p, encoding="utf-8", newline="").read()
nl = "\r\n" if "\r\n" in t else "\n"
old = nl.join(["Milestone: M0", "Last finished step:", "Next step:", "Open questions:", "Known broken:"])
new = nl.join(["Milestone: M1", "Last finished step: 0.12 (M0 gate: GO, no scope change, see notes/m0_findings.md)",
               "Next step: 1.4 scaffold; 1.1 AWS account needs Chaz",
               "Open questions: Midtown as source 12 or out of scope (currently out, STRETCH)",
               "Known broken: nothing known"])
assert old in t
t = t.replace(old, new)
assert "(Midtown possibly a location in this file)" in t
t = t.replace("(Midtown possibly a location in this file)", "(Midtown is not in this file; it has its own, see m0_findings)")
t = t.replace("Tall CSV (v2.x in January)", "Tall CSV (v3.0.0 on 2026-11-05)")
i = t.index("20. `dbt parse` and `sqlfluff` in CI")
j = t.index(nl, i)
extra = nl.join(["",
                 "21. Code 470 also appears as a revenue code (`RC`) and a local `TRIS-DRG`. Always filter 470 on code type `MS-DRG` or `DRG` (found in M0).",
                 "22. CPT codes may be typed `HCPCS`; VUMC labels 80053 only that way. Accept both for the nine CPT codes (found in M0).",
                 "23. JSON nests `attester_name` under `attestation`; CSV has it at the top level (found in M0)."])
t = t[:j] + extra + t[j:]
with open(p, "w", encoding="utf-8", newline="") as f:
    f.write(t)
