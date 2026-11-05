"""Run the reference normalizers on the real M0 staged files. No Iceberg, no AWS. Usage: m2_smoke_silver.py <data/m0 dir>"""
import os
import sys
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from pyspark.sql import functions as F  # noqa: E402

from pipeline.normalize import silver_from_json, silver_from_tall, spark_session  # noqa: E402

D = sys.argv[1]
spark = spark_session("smoke")
spark.sparkContext.setLogLevel("ERROR")
CPT = ["70553", "74177", "76700", "77067", "45378", "43235", "66984", "29881", "80053"]
for name, reader, path in [
    ("vumc_main", "tall", "vumc_main.parquet"),
    ("ascension_west", "tall", "ascension_west.parquet"),
    ("ascension_midtown", "tall", "ascension_midtown.parquet"),
    ("vumc_clarksville", "json", "vumc_clarksville.ndjson.gz"),
    ("tristar_centennial", "json", "tristar_centennial.ndjson.gz"),
]:
    t = time.time()
    try:
        p = os.path.join(D, path)
        df = silver_from_tall(spark.read.parquet(p)) if reader == "tall" else silver_from_json(spark.read.json(p))
        df = df.cache()
        n = df.count()
        sel = df.where(
            (F.col("code").isin(CPT) & F.col("code_type").isin("CPT", "HCPCS"))
            | ((F.col("code") == "470") & F.col("code_type").isin("MS-DRG", "DRG"))
        )
        m = sel.agg(
            F.count("*").alias("rows"),
            F.countDistinct("code").alias("codes"),
            F.count("negotiated_dollar").alias("dollars"),
            F.min("negotiated_dollar").alias("min"),
            F.max("negotiated_dollar").alias("max"),
        ).first()
        nonpos = sel.where("negotiated_dollar <= 0").count()
        print(f"{name}: silver_rows={n} ten_code_rows={m['rows']} codes={m['codes']} dollars={m['dollars']} "
              f"min={m['min']} max={m['max']} nonpositive={nonpos} secs={time.time() - t:.0f}", flush=True)
        df.unpersist()
    except Exception as e:
        print(f"{name}: FAILED {type(e).__name__}: {str(e)[:400]}", flush=True)
spark.stop()
