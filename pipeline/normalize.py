"""Spark normalization: staged CMS files -> one silver `standard_charges` schema.

Grain: one row per item x code x setting x modifiers x payer x plan x methodology.
Items with no payer rows (gross or cash only) keep one row with null payer columns.
"""
import re

from pyspark.sql import DataFrame, SparkSession
from pyspark.sql import functions as F
from pyspark.sql import types as T

SILVER_COLUMNS = [
    ("description", T.StringType()), ("code", T.StringType()), ("code_type", T.StringType()),
    ("modifiers", T.StringType()), ("setting", T.StringType()),
    ("drug_unit_of_measurement", T.DoubleType()), ("drug_type_of_measurement", T.StringType()),
    ("gross_charge", T.DoubleType()), ("discounted_cash", T.DoubleType()),
    ("payer_name", T.StringType()), ("plan_name", T.StringType()),
    ("negotiated_dollar", T.DoubleType()), ("negotiated_percentage", T.DoubleType()),
    ("negotiated_algorithm", T.StringType()), ("methodology", T.StringType()),
    ("median_amount", T.DoubleType()), ("p10_amount", T.DoubleType()), ("p90_amount", T.DoubleType()),
    ("allowed_count_raw", T.StringType()),
    ("min_negotiated", T.DoubleType()), ("max_negotiated", T.DoubleType()),
    ("additional_generic_notes", T.StringType()), ("additional_payer_notes", T.StringType()),
]


def to_num(c):
    """CMS numerics are positive numbers; strip stray '$' and ',' that real files contain."""
    return F.regexp_replace(F.trim(c.cast("string")), r"[$,]", "").try_cast("double")


def normalize_code(code_col, type_col):
    """Upper-case code type; strip leading zeros from DRG-family codes ('00470' -> '470')."""
    t = F.upper(F.trim(type_col))
    c = F.trim(code_col.cast("string"))
    return F.when(t.contains("DRG"), F.regexp_replace(c, r"^0+(?=\d)", "")).otherwise(c), t


def finalize(df: DataFrame) -> DataFrame:
    """Cast to the silver schema, normalize codes and enums, parse count bounds."""
    out = df
    for name, dtype in SILVER_COLUMNS:
        if name not in out.columns:
            out = out.withColumn(name, F.lit(None).cast(dtype))
    num_cols = [n for n, t in SILVER_COLUMNS if isinstance(t, T.DoubleType)]
    for n in num_cols:
        out = out.withColumn(n, to_num(F.col(n)))
    code, code_type = normalize_code(F.col("code"), F.col("code_type"))
    raw = F.trim(F.col("allowed_count_raw"))
    out = (out.withColumn("code", code).withColumn("code_type", code_type)
              .withColumn("setting", F.lower(F.trim("setting")))
              .withColumn("methodology", F.lower(F.trim("methodology")))
              .withColumn("allowed_count_low",
                          F.when(F.lower(raw) == "1 through 10", F.lit(1))
                           .otherwise(raw.try_cast("int")))
              .withColumn("allowed_count_high",
                          F.when(F.lower(raw) == "1 through 10", F.lit(10))
                           .otherwise(raw.try_cast("int"))))
    keep = [n for n, _ in SILVER_COLUMNS] + ["allowed_count_low", "allowed_count_high"]
    return out.select(*keep).where(F.col("code").isNotNull() & (F.col("code") != ""))


# ---------- JSON (NDJSON from staging) ----------
def silver_from_json(items: DataFrame) -> DataFrame:
    """items: one row per standard_charge_information object."""
    x = (items
         .withColumn("ci", F.explode_outer("code_information"))
         .withColumn("sc", F.explode_outer("standard_charges")))
    x = x.withColumn("pi", F.explode_outer("sc.payers_information"))
    has_drug = "drug_information" in items.columns
    pi_fields = set(items.schema["standard_charges"].dataType.elementType["payers_information"]
                    .dataType.elementType.fieldNames())

    def pi(name):
        return F.col(f"pi.{name}") if name in pi_fields else F.lit(None)

    sc_fields = set(items.schema["standard_charges"].dataType.elementType.fieldNames())

    def sc(name):
        return F.col(f"sc.{name}") if name in sc_fields else F.lit(None)

    df = x.select(
        F.col("description"),
        F.col("ci.code").alias("code"), F.col("ci.type").alias("code_type"),
        (F.array_join(sc("modifier_code"), "|") if "modifier_code" in sc_fields else F.lit(None)).alias("modifiers"),
        sc("setting").alias("setting"),
        (F.col("drug_information.unit") if has_drug else F.lit(None)).alias("drug_unit_of_measurement"),
        (F.col("drug_information.type") if has_drug else F.lit(None)).alias("drug_type_of_measurement"),
        sc("gross_charge").alias("gross_charge"), sc("discounted_cash").alias("discounted_cash"),
        pi("payer_name").alias("payer_name"), pi("plan_name").alias("plan_name"),
        pi("standard_charge_dollar").alias("negotiated_dollar"),
        pi("standard_charge_percentage").alias("negotiated_percentage"),
        pi("standard_charge_algorithm").alias("negotiated_algorithm"),
        pi("methodology").alias("methodology"),
        pi("median_amount").alias("median_amount"),
        pi("10th_percentile").alias("p10_amount"), pi("90th_percentile").alias("p90_amount"),
        pi("count").cast("string").alias("allowed_count_raw"),
        sc("minimum").alias("min_negotiated"), sc("maximum").alias("max_negotiated"),
        sc("additional_generic_notes").alias("additional_generic_notes"),
        pi("additional_payer_notes").alias("additional_payer_notes"),
    )
    return finalize(df)


# ---------- CSV shared: unpivot code|1..n ----------
def explode_codes(df: DataFrame) -> DataFrame:
    idx = sorted({int(m.group(1)) for c in df.columns if (m := re.fullmatch(r"code\|(\d+)", c))})
    pairs = [F.struct(F.col(f"`code|{i}`").alias("code"),
                      F.col(f"`code|{i}|type`").alias("code_type")) for i in idx]
    return df.withColumn("_c", F.explode(F.array(*pairs))).withColumn("code", F.col("_c.code")) \
             .withColumn("code_type", F.col("_c.code_type")).drop("_c")


TALL_RENAMES = {
    "standard_charge|gross": "gross_charge", "standard_charge|discounted_cash": "discounted_cash",
    "standard_charge|negotiated_dollar": "negotiated_dollar",
    "standard_charge|negotiated_percentage": "negotiated_percentage",
    "standard_charge|negotiated_algorithm": "negotiated_algorithm",
    "standard_charge|methodology": "methodology",
    "standard_charge|min": "min_negotiated", "standard_charge|max": "max_negotiated",
    "10th_percentile": "p10_amount", "90th_percentile": "p90_amount", "count": "allowed_count_raw",
}


def silver_from_tall(df: DataFrame) -> DataFrame:
    for src, dst in TALL_RENAMES.items():
        if src in df.columns:
            df = df.withColumnRenamed(src, dst)
    return finalize(explode_codes(df))


# ---------- CSV wide: unpivot payer|plan column groups ----------
WIDE_METRICS = {  # (prefix, suffix) -> silver column
    ("standard_charge", "negotiated_dollar"): "negotiated_dollar",
    ("standard_charge", "negotiated_percentage"): "negotiated_percentage",
    ("standard_charge", "negotiated_algorithm"): "negotiated_algorithm",
    ("standard_charge", "methodology"): "methodology",
    ("median_amount", None): "median_amount",
    ("10th_percentile", None): "p10_amount",
    ("90th_percentile", None): "p90_amount",
    ("count", None): "allowed_count_raw",
    ("additional_payer_notes", None): "additional_payer_notes",
}


def wide_payer_groups(columns: list[str]) -> dict[tuple[str, str], dict[str, str]]:
    groups: dict[tuple[str, str], dict[str, str]] = {}
    for c in columns:
        parts = c.split("|")
        if len(parts) == 4 and (parts[0], parts[3]) in WIDE_METRICS:
            key, metric = (parts[1], parts[2]), WIDE_METRICS[(parts[0], parts[3])]
        elif len(parts) == 3 and (parts[0], None) in WIDE_METRICS:
            key, metric = (parts[1], parts[2]), WIDE_METRICS[(parts[0], None)]
        else:
            continue
        groups.setdefault(key, {})[metric] = c
    return groups


def silver_from_wide(df: DataFrame) -> DataFrame:
    groups = wide_payer_groups(df.columns)
    metrics = sorted(set(WIDE_METRICS.values()))
    structs = []
    for (payer, plan), cols in groups.items():
        fields = [F.lit(payer).alias("payer_name"), F.lit(plan).alias("plan_name")]
        fields += [(F.col(f"`{cols[m]}`") if m in cols else F.lit(None).cast("string")).alias(m)
                   for m in metrics]
        structs.append(F.struct(*fields))
    payer_cols = [c for g in groups.values() for c in g.values()]
    base = df
    for src, dst in TALL_RENAMES.items():
        if src in base.columns:
            base = base.withColumnRenamed(src, dst)
    # _row is stable here because staged Parquet is read with the same partitioning both times;
    # if you change how `df` is produced, persist `base` first so both branches see the same ids.
    base = base.withColumn("_row", F.monotonically_increasing_id())
    exploded = base.withColumn("_p", F.explode(F.array(*structs))).drop(*payer_cols)
    for m in ["payer_name", "plan_name"] + metrics:
        exploded = exploded.withColumn(m, F.col(f"_p.{m}"))
    exploded = exploded.drop("_p")
    # keep only payer and plan groups where the hospital encoded a rate or allowed amount data
    has_data = (F.col("negotiated_dollar").isNotNull() | F.col("negotiated_percentage").isNotNull()
                | F.col("negotiated_algorithm").isNotNull() | F.col("median_amount").isNotNull()
                | F.col("allowed_count_raw").isNotNull())
    with_payers = exploded.where(has_data)
    # items with no payer data at all (gross or cash only) keep one row with null payer columns
    no_payers = base.drop(*payer_cols).join(with_payers.select("_row"), "_row", "left_anti")
    combined = with_payers.unionByName(no_payers, allowMissingColumns=True).drop("_row")
    return finalize(explode_codes(combined))


def spark_session(app: str = "mrf-normalize") -> SparkSession:
    return (SparkSession.builder.appName(app).master("local[*]")
            .config("spark.sql.session.timeZone", "UTC").getOrCreate())
