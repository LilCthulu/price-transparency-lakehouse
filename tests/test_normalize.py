"""The three CMS v3.0.0 example files encode the same hospital; all three readers must agree."""
import os

import pytest

from pipeline.normalize import silver_from_json, silver_from_tall, silver_from_wide, spark_session
from pipeline.stage import normalize_header, stage_csv, stage_json

E = os.path.join(os.path.dirname(__file__), "fixtures")
TALL = f"{E}/V3.0.0_Tall_CSV_Format_Example.csv"
WIDE = f"{E}/V3.0.0_Wide_CSV_Format_Example.csv"
JSON = f"{E}/v3_json_format_example.json"

@pytest.fixture(scope="session")
def spark():
    s = spark_session("tests"); yield s; s.stop()

@pytest.fixture(scope="session")
def silvers(spark, tmp_path_factory):
    d = tmp_path_factory.mktemp("staged")
    _, tl, _ = stage_csv(TALL, str(d / "tall.parquet")); assert tl == "tall"
    _, wl, _ = stage_csv(WIDE, str(d / "wide.parquet")); assert wl == "wide"
    stage_json(JSON, str(d / "items.ndjson.gz"))
    return {
        "tall": silver_from_tall(spark.read.parquet(str(d / "tall.parquet"))),
        "wide": silver_from_wide(spark.read.parquet(str(d / "wide.parquet"))),
        "json": silver_from_json(spark.read.json(str(d / "items.ndjson.gz"))),
    }

KEY = ["description", "code", "code_type", "setting", "payer_name", "plan_name",
       "negotiated_dollar", "negotiated_percentage", "methodology", "median_amount", "allowed_count_raw"]

def rows(df):
    return sorted(tuple("" if v is None else str(v) for v in r) for r in df.select(*KEY).distinct().collect())

def test_header_normalization():
    assert normalize_header("Code | 1 | Type") == "code|1|type"
    assert normalize_header("standard_charge | Aetna | PPO | Negotiated_Dollar") == "standard_charge|Aetna|PPO|negotiated_dollar"
    assert normalize_header("standard_charge|Gross") == "standard_charge|gross"

def test_formats_agree(silvers):
    t, w, j = rows(silvers["tall"]), rows(silvers["wide"]), rows(silvers["json"])
    assert t == w, set(t) ^ set(w)
    assert t == j, set(t) ^ set(j)

def test_count_bounds(silvers):
    df = silvers["tall"].where("allowed_count_raw is not null")
    for r in df.select("allowed_count_raw", "allowed_count_low", "allowed_count_high").collect():
        if r[0].lower() == "1 through 10":
            assert (r[1], r[2]) == (1, 10)
        else:
            assert r[1] == r[2] == int(r[0])
