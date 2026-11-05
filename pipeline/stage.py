"""Staging: turn one CMS hospital MRF into a splittable file plus a metadata dict.

CSV  -> Parquet (all columns as strings, headers normalized), metadata from rows 1-2.
JSON -> NDJSON.gz (one standard_charge_information item per line), metadata from top-level keys.
Both run in near-constant memory, so a 1 GB file never has to fit in RAM.
"""
import csv
import gzip
import json
import sys

import ijson
import pyarrow as pa
import pyarrow.csv as pacsv
import pyarrow.parquet as pq

ATTEST_PREFIX = "to the best of its knowledge and belief"
PAYER_PREFIXES = {
    "standard_charge", "median_amount", "10th_percentile", "90th_percentile",
    "count", "additional_payer_notes", "estimated_amount",  # estimated_amount = v2.x only
}
GENERAL_TWO_PART = {"gross", "discounted_cash", "min", "max", "negotiated_dollar",
                    "negotiated_percentage", "negotiated_algorithm", "methodology"}
MULTI_VALUE_META = ("location_name", "hospital_location", "hospital_address", "type_2_npi")


def normalize_header(h: str) -> str:
    """Trim spaces around pipes and lowercase CMS keywords, keeping payer and plan names as written.

    'Code | 1 | Type' -> 'code|1|type'
    'standard_charge | Aetna | PPO | Negotiated_Dollar' -> 'standard_charge|Aetna|PPO|negotiated_dollar'
    CMS says headers are case-insensitive, so keywords are lowercased; payer names are data.
    """
    parts = [p.strip() for p in h.replace("\ufeff", "").split("|")]
    head = parts[0].lower()
    is_wide_payer_col = (
        head in PAYER_PREFIXES
        and len(parts) >= 3
        and not (len(parts) == 2 and parts[1].lower() in GENERAL_TWO_PART)
    )
    if is_wide_payer_col:
        return "|".join([head, parts[1], parts[2]] + [p.lower() for p in parts[3:]])
    return "|".join(p.lower() for p in parts)


def read_csv_meta(path: str) -> tuple[dict, list[str]]:
    """Rows 1-2 are file-level headers and values; row 3 is the item header row."""
    with open(path, newline="", encoding="utf-8-sig") as f:
        r = csv.reader(f)
        keys, vals, header = next(r), next(r), next(r)
    meta: dict = {}
    for k, v in zip(keys, vals):
        nk = normalize_header(k)
        if not nk:
            continue
        if nk.startswith(ATTEST_PREFIX):          # the attestation text IS the header
            meta["attestation_confirmed"] = v.strip().lower() == "true"
        elif nk.startswith("license_number|"):    # license_number|TN
            meta["license_state"] = nk.split("|", 1)[1].upper()
            meta["license_number"] = v.strip() or None
        else:
            meta[nk] = v.strip()
    for k in MULTI_VALUE_META:
        if k in meta:
            meta[k] = [p.strip() for p in meta[k].split("|") if p.strip()]
    if "hospital_location" in meta and "location_name" not in meta:   # v2.x name
        meta["location_name"] = meta.pop("hospital_location")
    return meta, [normalize_header(h) for h in header]


def detect_csv_layout(cols: list[str]) -> str:
    wide = any(c.startswith("standard_charge|") and c.count("|") == 3 for c in cols)
    return "wide" if wide else "tall"


def stage_csv(path: str, out_parquet: str) -> tuple[dict, str, int]:
    meta, cols = read_csv_meta(path)
    if len(set(cols)) != len(cols):
        dupes = sorted({c for c in cols if cols.count(c) > 1})
        raise ValueError(f"duplicate column headers after normalization: {dupes[:5]}")
    reader = pacsv.open_csv(
        path,
        read_options=pacsv.ReadOptions(skip_rows=3, column_names=cols,
                                       block_size=1 << 24, encoding="utf8"),
        parse_options=pacsv.ParseOptions(newlines_in_values=True),
        convert_options=pacsv.ConvertOptions(column_types={c: pa.string() for c in cols},
                                             strings_can_be_null=True),
    )
    writer, rows = None, 0
    for batch in reader:
        if writer is None:
            writer = pq.ParquetWriter(out_parquet, batch.schema)
        writer.write_batch(batch)
        rows += batch.num_rows
    if writer:
        writer.close()
    return meta, detect_csv_layout(cols), rows


SKIP_KEYS = ("standard_charge_information", "modifier_information")


def read_json_meta(path: str) -> dict:
    """Collect every top-level key except the two big arrays, in one streaming pass."""
    meta: dict = {}
    with open(path, "rb") as f:
        builder, key = None, None
        for prefix, event, value in ijson.parse(f, use_float=True):
            if prefix == "" and event == "map_key":
                key = value
                builder = None if key in SKIP_KEYS else ijson.ObjectBuilder()
                continue
            if builder is not None and (prefix == key or prefix.startswith(key + ".")):
                builder.event(event, value)
                if prefix == key and event in ("end_map", "end_array", "string",
                                               "number", "boolean", "null"):
                    meta[key] = builder.value
    if "hospital_location" in meta and "location_name" not in meta:   # v2.x name
        meta["location_name"] = meta.pop("hospital_location")
    return meta


def stage_json(path: str, out_ndjson_gz: str, out_modifiers_gz: str | None = None) -> tuple[dict, int]:
    rows = 0
    with open(path, "rb") as f, gzip.open(out_ndjson_gz, "wt", encoding="utf-8") as out:
        for item in ijson.items(f, "standard_charge_information.item", use_float=True):
            out.write(json.dumps(item, separators=(",", ":")) + "\n")
            rows += 1
    if out_modifiers_gz:
        with open(path, "rb") as f, gzip.open(out_modifiers_gz, "wt", encoding="utf-8") as out:
            for item in ijson.items(f, "modifier_information.item", use_float=True):
                out.write(json.dumps(item, separators=(",", ":")) + "\n")
    return read_json_meta(path), rows


if __name__ == "__main__":
    p = sys.argv[1]
    if p.endswith(".csv"):
        print(stage_csv(p, sys.argv[2]))
    else:
        print(stage_json(p, sys.argv[2]))
