# PROJECT_CONTEXT.md: Healthcare Price Transparency Lakehouse

Version 1.0, written October 26, 2026. Facts, versions, and links were checked on that date. Owner: Chaz Carbis.

**How to load this file.** Put it at the repo root. Tools that read a fixed filename can use a copy or symlink named `AGENTS.md` or `CLAUDE.md`. If your model's context window is small (under about 16k tokens), always load **Part A** and paste only the Part B section the current task needs. Part A is about 1,000 words (roughly 1,500 tokens). The whole file is roughly 16k tokens, about 5k of which is the reference code appendix.

---

# PART A: QUICK CONTEXT (load every time)

## A1. Your role and rules

You are a senior data engineer pairing with Chaz on this repo. Follow these rules in every answer:

1. **Be critical, not agreeable.** Treat every claim, including Chaz's and your own, as unsupported until evidence says otherwise. If a plan has a flaw, say so first and propose the fix. No flattery, no "great question", no praise of Chaz.
2. **Mark uncertainty.** Label anything you are not sure of as `low confidence` or `unverified`. Never invent library APIs, CLI flags, config keys, or AWS behavior. If you do not know, say so and point to the doc link in Part B section B15.
3. **Give concrete, runnable output.** Prefer: a short plan, the code, a test, and the exact command to verify it. Keep prose dense. No preamble.
4. **Respect locked decisions** (A4). Do not relitigate them unless Chaz asks or new evidence breaks one; if that happens, say which decision and what evidence.
5. **Calibrate to Chaz** (A3): do not explain SQL, dbt basics, Python basics, or Snowflake. Do explain AWS IAM, Spark internals, Iceberg, Airflow, and Terraform specifics when they matter.
6. **Ask, do not guess.** If a request is ambiguous or a message looks cut off, ask one short question instead of building on an assumption.
7. **Writing style for anything Chaz will read or publish:** never use em dashes; use periods, commas, or restructured sentences. Do not end replies with a hand-back line like "let me know" or "your turn".
8. **Security:** never put secrets in code, commits, logs, or prompts. Credentials come from the AWS CLI profile or environment variables. Never commit `.env`, `*.tfstate`, or downloaded hospital files.
9. **Scope discipline:** the MVP scope in A2 is fixed. If a suggestion adds scope, label it `STRETCH` and keep it out of the current task.

## A2. The project in one paragraph

A recruiter-facing portfolio lakehouse. It downloads CMS-mandated hospital price files (machine-readable files, MRFs) for 12 Middle Tennessee hospitals, runs the official CMS validator on each, streams each file into a splittable staged format, normalizes all formats with PySpark into Apache Iceberg tables on S3 cataloged in AWS Glue, models a gold star schema with dbt on Athena, orchestrates it weekly with Airflow, provisions AWS with Terraform, tests on every PR with GitHub Actions, and serves a public Streamlit app with two pages: a cost comparison (10 shoppable procedures by hospital and payer plan) and a file quality page (CMS validator results per file). Target: hiring managers at Nashville healthcare and healthtech companies. The plan document is the source of truth for scope; this file is the source of truth for implementation detail.

**MVP is done when:** every box in the build checklist is checked, which means all 12 files flow end to end, `dbt build` passes in CI, the Streamlit app is live on a public URL, and the README, video, and resume bullets are published with real numbers.

## A3. Owner calibration

- Chaz has about 5 years of experience: Python, SQL, Snowflake, dbt, ETL and ELT pipelines, Streamlit, Node, React. Former Optum data engineer (healthcare and HIPAA context), led projects end to end.
- New to him on this project: AWS (S3, IAM, Glue, Athena), Spark, Iceberg, Airflow, Terraform, GitHub Actions OIDC.
- Time is limited and irregular (night-shift schedule). Work arrives in sessions of a few hours. Every task you help with should end in a committed, working state.

## A4. Locked decisions

| Decision | Choice | Why |
| --- | --- | --- |
| Domain | CMS hospital price transparency MRFs, Middle Tennessee | Healthcare domain matches his Optum background and Nashville employers |
| Scope | 12 files (B3), 10 procedures (B3) | Thin, complete slice |
| Cloud | AWS, account on the **Paid plan** (credits apply; Free plan accounts close after 6 months) | AWS is the most-requested cloud in postings |
| Storage | S3 + Apache Iceberg tables + AWS Glue Data Catalog | Open table format, any engine can read |
| Staging | Python streaming (ijson for JSON, pyarrow for CSV) before Spark | A CMS JSON file is one object; Spark cannot split it |
| Compute | PySpark 4.2 local (`local[*]`) inside Docker | $0 compute |
| Silver write mode | Latest-only per `source_id`, Iceberg dynamic partition overwrite | A new file version replaces that source; history via Iceberg time travel and the gold snapshot |
| Modeling | dbt-core 1.12 + dbt-athena 1.11, gold tables as Iceberg | Pay per query; dbt is already his strength |
| Orchestration | Airflow 3.3.2 via official Docker Compose, custom image | Most-requested orchestrator keyword |
| IaC | Terraform 1.17, AWS provider 6.x | Reviewable, repeatable |
| CI | GitHub Actions; AWS access via OIDC role, never static keys in CI | Visible quality signal |
| Validation | Official `@cmsgov/hpt-validator-cli` 1.12.0 | Credible, official rules |
| Serving | Streamlit Community Cloud reading an exported DuckDB file committed to the repo | Free, fast, no warehouse cost per view |
| Budget | Under $10 a month, budget alarms at $5 and $10 | Portfolio project |
| Data | Public files only, no PHI ever | Zero compliance risk |

## A5. Constraints and non-goals

- No always-on cloud compute (no EC2, EMR, MWAA, NAT gateways, RDS).
- No payer Transparency in Coverage files, no statewide coverage, no ML, no auth: all `STRETCH`.
- Downloads go to local disk, then S3; delete local copies after upload. Single files can exceed 1 GB.
- Respect source sites: one download per file per run, descriptive User-Agent, retries with backoff, no parallel hammering.

## A6. Current status (Chaz updates this block)

```
Milestone: M1
Last finished step: 2.2 (M0, 1.4, 1.7, 2.1, 2.2 done; Terraform written and validated, not planned or applied)
Next step: 1.1 and 1.2 AWS account (needs Chaz), then 1.3 Docker Desktop plus SSO, 1.5 plan
Open questions: none. Midtown added as source 12 on 2026-11-05 (Chaz approved)
Known broken: nothing known. VUMC mixes physician fees with facility rates; M3 must separate them (see m0_findings). Local tools outside PATH: Java 21 and Terraform 1.17.1 in ~/tools; set JAVA_HOME and PYSPARK_PYTHON for pytest on Windows
```

---

# PART B: REFERENCE (load the section the task needs)

## B1. Stack and pinned versions (checked October 26, 2026)

| Component | Version | Notes |
| --- | --- | --- |
| Python | 3.13 | Airflow 3.3.2 image defaults to Python 3.13 on Debian bookworm; the reference code was verified on 3.13 |
| PySpark | 4.2.0 | Needs Java 17, 21, or 25 |
| Iceberg Spark runtime | `org.apache.iceberg:iceberg-spark-runtime-4.2_2.13:1.12.0` | Spark 4.x uses Scala 2.13 |
| Iceberg AWS bundle | `org.apache.iceberg:iceberg-aws-bundle:1.12.0` | Glue catalog and S3FileIO |
| pyiceberg | 0.12.0 | Python appends to Glue Iceberg tables (manifest, validator results) |
| pyarrow | 25.0.1 | CSV streaming to Parquet; awswrangler 3.17.1 cannot install alongside pyarrow 26 |
| ijson | 3.6.0 | Use the C backend (`yajl2_c`), it is the default when wheels install |
| requests, beautifulsoup4 | 2.34.x, 4.15.0 | Scraping and downloads |
| boto3 | 1.43.x | S3 uploads |
| awswrangler | 3.17.x | Athena query to pandas for the export step |
| dbt-core, dbt-athena | 1.12.x, 1.11.1 | Install `dbt-athena` (the `dbt-athena-community` name is also published at the same version) |
| apache-airflow | 3.3.2 | Official Compose file pinned to 3.3.2 |
| Node.js | 20 or later | Required by the CMS validator CLI |
| @cmsgov/hpt-validator-cli | 1.12.0 | Command `cms-hpt-validator` |
| Terraform, AWS provider | 1.17.0, 6.70.x | Pin `~> 6.70` |
| DuckDB, Streamlit | 2.0.x, 1.66.x | App side |
| Lint and test | ruff 0.17.x, sqlfluff 4.4.x, pytest | |

Verified pipeline `requirements.txt` (resolved together with `pip check` clean on Python 3.13, October 26, 2026; this is what goes into the `/opt/pipeline` venv):

```
pyspark==4.2.0
pyarrow==25.0.1
ijson==3.6.0
pyiceberg[glue]==0.12.0
awswrangler==3.17.1
boto3==1.43.118
requests==2.34.2
beautifulsoup4==4.15.0
duckdb==2.0.0
dbt-core==1.12.6
dbt-athena==1.11.1
pyyaml
```

Dev only: `pytest`, `ruff`, `sqlfluff`. The Streamlit app has its own small `app/requirements.txt` (`streamlit`, `duckdb`, `pandas`) because Community Cloud installs from it.
| GitHub Actions | checkout@v7, setup-python@v7, setup-node@v7, configure-aws-credentials@v6, setup-terraform@v4 | Latest major tags on October 26, 2026 |

## B2. Target repo layout

```
price-transparency-lakehouse/
  PROJECT_CONTEXT.md            # this file
  README.md
  Makefile                      # up, down, ingest, stage, normalize, build, export, test, lint
  pyproject.toml                # python deps + ruff + pytest config
  .env.example                  # AWS_PROFILE, AWS_REGION, LAKE_BUCKET, ... (no secrets)
  config/
    sources.yml                 # the 12 sources (B3), link patterns per source page
  pipeline/
    __init__.py
    settings.py                 # reads env vars, one place for bucket names and paths
    ingest.py                   # scrape links, download, hash, upload, manifest row
    validate.py                 # run cms-hpt-validator, parse JSON, results rows
    stage.py                    # CSV -> Parquet, JSON -> NDJSON.gz (reference code in appendix)
    normalize.py                # Spark readers -> silver schema (reference code in appendix)
    load_silver.py              # Spark job: read staged, normalize, write Iceberg
    export.py                   # Athena gold mart -> app/data/prices.duckdb
    iceberg_catalog.py          # pyiceberg Glue catalog helper
  tests/
    fixtures/                   # the 3 CMS v3.0.0 example files (B11)
    test_stage.py
    test_normalize.py           # the three formats must agree
    test_ingest.py              # link matching on saved HTML snapshots
  dbt/
    dbt_project.yml
    profiles.yml.example
    seeds/                      # sources.csv, procedures.csv, payer_map.csv
    models/staging/  models/marts/  snapshots/  tests/
  airflow/
    Dockerfile
    docker-compose.yaml         # from the official 3.3.2 file, image switched to build
    dags/price_transparency.py
  infra/
    main.tf  variables.tf  outputs.tf  versions.tf
  app/
    streamlit_app.py
    data/prices.duckdb          # small export, must stay under 100 MiB
  .github/workflows/ci.yml
  notes/m0_findings.md
```

## B3. Data sources

### The 12 MVP files

Vanderbilt and TriStar URLs were read from the live source pages on October 26, 2026. Ascension URLs come from a January 12, 2026 third-party index and must be confirmed on the Ascension page during M0. Never hardcode these URLs in pipeline code: `config/sources.yml` stores the source page and a link pattern, and ingest reads the current link each run.

| source_id | Hospital (other locations in file) | Format | Current direct link | M0 |
| --- | --- | --- | --- | --- |
| vumc_main | Vanderbilt University Medical Center | CSV, tall or wide unknown | https://finance.vumc.org/assets/pub/pt/352528741_vanderbilt-university-medical-center_standardcharges.csv | yes |
| vumc_wilson | Vanderbilt Wilson County Hospital | CSV | https://finance.vumc.org/assets/pub/pt/352528741-1306889597_vanderbilt-university-medical-center_standardcharges.csv | |
| vumc_clarksville | Vanderbilt Clarksville Hospital | JSON | https://finance.vumc.org/assets/pub/pt/203500835_vanderbilt-clarksville-hospital_standardcharges.json | yes |
| tristar_centennial | TriStar Centennial (Parthenon Pavilion, Women's, Children's, Bellevue ER, Spring Hill ER) | JSON | see TriStar note | yes |
| tristar_skyline | TriStar Skyline (East Nashville ER) | JSON | see TriStar note | |
| tristar_southern_hills | TriStar Southern Hills (Century Farms ER, Nolensville ER) | JSON | see TriStar note | |
| tristar_summit | TriStar Summit (Mt. Juliet ER) | JSON | see TriStar note | |
| tristar_stonecrest | TriStar StoneCrest | JSON | see TriStar note | |
| tristar_hendersonville | TriStar Hendersonville (Portland ER) | JSON | see TriStar note | |
| ascension_west | Ascension Saint Thomas West (Midtown has its own file, see ascension_midtown) | Tall CSV (v3.0.0 on 2026-11-05) | https://healthcare.ascension.org/-/media/project/ascension/healthcare/price-transparency-files/tn-csv/620347580-1629025648_saint-thomas-west-hospital_standardcharges.csv | yes |
| ascension_midtown | Ascension Saint Thomas Midtown | Tall CSV (v3.0.0 on 2026-11-05) | https://healthcare.ascension.org/-/media/project/ascension/healthcare/price-transparency-files/tn-csv/620347580-1780778969_saint-thomas-west-hospital_standardcharges.csv | yes |
| ascension_rutherford | Ascension Saint Thomas Rutherford | Tall CSV (v3.0.0 on 2026-11-05) | https://healthcare.ascension.org/-/media/project/ascension/healthcare/price-transparency-files/tn-csv/620475842_saint-thomas-rutherford-hospital_standardcharges.csv | |

**TriStar note.** All six files live in one Azure blob container. URL form:
`https://stctrprodsnsvc00455826e6.blob.core.windows.net/pt-final-posting-files/<FILE>?si=dpx-pt-json-access-policy&spr=https&sv=2026-02-06&sr=c&sig=<scraped-at-runtime>`
where `<FILE>` is one of: `62-1113737_TRISTAR-CENTENNIAL-MEDICAL-CENTER_standardcharges.json`, `62-1560757_TRISTAR-SKYLINE-MEDICAL-CENTER_standardcharges.json`, `62-1113737_TRISTAR-SOUTHERN-HILLS-MEDICAL-CENTER_standardcharges.json`, `62-1113737_TRISTAR-SUMMIT-MEDICAL-CENTER_standardcharges.json`, `62-1113737_TRISTAR-STONECREST-MEDICAL-CENTER_standardcharges.json`, `62-1321255_TRISTAR-HENDERSONVILLE-MEDICAL-CENTER_standardcharges.json`. The token belongs to a stored access policy and did not change between October 21 and 26, 2026; still scrape it fresh each run.

**Source pages (what ingest scrapes):**
- Vanderbilt: https://www.vumc.org/pricetransparency/home (anchor tags linking to `finance.vumc.org/assets/pub/pt/`; match on the link label, for example "Vanderbilt Clarksville Hospital - Machine Readable")
- TriStar: https://www.tristarhealth.com/patient-resources/patient-financial-resources/pricing-transparency-cms-required-file-of-standard-charges (anchors containing `pt-final-posting-files/`; match on the file name, for example `TRISTAR-CENTENNIAL-MEDICAL-CENTER`)
- Ascension: https://healthcare.ascension.org/price-transparency (page structure unverified; expect anchors containing `tn-csv/`; match on the link label for West, Midtown, and Rutherford, because West and Midtown share a file name stem). Some Ascension files have been published as `.zip`.

**Midtown.** Its file says `hospital_name` Saint Thomas West and carries West's type 2 NPI (1629025648); only `location_name` says Midtown. Never key or label a hospital from those fields. Use `source_id` and the display name in `config/sources.yml`.

**Keys:** file names follow `<EIN>_<name>_standardcharges`, but TriStar reuses EIN 62-1113737 for five hospitals. `source_id` is the only hospital key in the pipeline. Locations inside a file go to a bridge table.

### The 10 procedures (all on CMS's list of 70 shoppable services)

| code | code_type | Service |
| --- | --- | --- |
| 70553 | CPT | MRI brain before and after contrast |
| 74177 | CPT | CT abdomen and pelvis with contrast |
| 76700 | CPT | Ultrasound of abdomen |
| 77067 | CPT | Screening mammography, both breasts |
| 45378 | CPT | Diagnostic colonoscopy |
| 43235 | CPT | Diagnostic upper GI endoscopy |
| 66984 | CPT | Cataract removal with lens insertion |
| 29881 | CPT | Knee arthroscopy, removal of one cartilage |
| 80053 | CPT | Comprehensive metabolic panel |
| 470 | MS-DRG | Major lower-extremity joint replacement without MCC |

Hospitals may encode 470 as `0470` or `00470`, and may label it `DRG` or `MS-DRG`. Normalize: strip leading zeros on DRG-family codes before matching; match MS-DRG 470 against code types `MS-DRG` and `DRG`. Some hospitals may also publish HCPCS equivalents or only revenue codes for an item: those items will not match and must be counted on the quality page, not silently dropped.

## B4. CMS file format reference (template v3.0.0)

Source: CMS data dictionaries at https://github.com/CMSgov/hospital-price-transparency (CSV: `documentation/CSV/README.md`, JSON: `documentation/JSON/README.md`, changes: `documentation/UPDATE_GUIDE.md`). v3.0 took effect January 1, 2026; CMS enforcement began April 1, 2026. Real files may still be v2.2.

### CSV (tall and wide)

- **Row 1:** file-level headers. **Row 2:** their values. **Row 3:** item headers. **Row 4 onward:** data.
- Row 1 headers: `hospital_name`, `last_updated_on`, `version`, `location_name`, `hospital_address`, `type_2_npi`, `license_number|<STATE>` (state lives in the header, for example `license_number|TN`), `attester_name`, and one header whose text **is** the full attestation statement (starts with "To the best of its knowledge and belief"); its row 2 value is `true` or `false`. Optional: `financial_aid_policy`, `general_contract_provisions`.
- Multi-value fields (`location_name`, `hospital_address`, `type_2_npi`) are pipe-separated, possibly with spaces: `0000000001 | 0000000002`.
- `last_updated_on` is ISO `YYYY-MM-DD`, but `M/D/YYYY` and `MM/DD/YYYY` are also accepted (the CMS example uses `4/1/2026`).
- Headers are case-insensitive and may have spaces around pipes (the CMS tall example uses `code | 1 | type`). Normalize: trim each pipe part, lowercase keywords, keep payer and plan names as written.
- Item columns, tall: `description`, `code|i`, `code|i|type` (i = 1..n), `setting`, `drug_unit_of_measurement`, `drug_type_of_measurement`, `standard_charge|gross`, `standard_charge|discounted_cash`, `payer_name`, `plan_name`, `modifiers`, `standard_charge|negotiated_dollar`, `standard_charge|negotiated_percentage`, `standard_charge|negotiated_algorithm`, `median_amount`, `10th_percentile`, `90th_percentile`, `count`, `standard_charge|min`, `standard_charge|max`, `standard_charge|methodology`, `additional_generic_notes`. Optional `billing_class`.
- Wide differs: no `payer_name` or `plan_name` columns. Nine columns per payer and plan: `standard_charge|<payer>|<plan>|negotiated_dollar`, `...|negotiated_percentage`, `...|negotiated_algorithm`, `...|methodology`, `median_amount|<payer>|<plan>`, `10th_percentile|<payer>|<plan>`, `90th_percentile|<payer>|<plan>`, `count|<payer>|<plan>`, `additional_payer_notes|<payer>|<plan>`. Many plans means thousands of columns.
- v2.x differences: `hospital_location` instead of `location_name`; an affirmation statement instead of attestation; no `type_2_npi` or `attester_name`; `estimated_amount` (tall) or `estimated_amount|<payer>|<plan>` (wide) instead of median and percentiles.

### JSON

- One root object. Keys: `hospital_name`, `last_updated_on`, `version`, `location_name` (array), `hospital_address` (array), `license_information` {`license_number`, `state`}, `attestation` {`attestation`, `confirm_attestation`, `attester_name`}, `type_2_npi` (array), optional `general_contract_provisions` (array of objects in the CMS example), `standard_charge_information` (array, the big one), `modifier_information` (array).
- Each `standard_charge_information` item: `description`, optional `drug_information` {`unit`, `type`}, `code_information` [ {`code`, `type`} ], `standard_charges` [ {`setting`, `gross_charge`, `discounted_cash`, `minimum`, `maximum`, `modifier_code` (array), `additional_generic_notes`, `payers_information` [ {`payer_name`, `plan_name`, `standard_charge_dollar`, `standard_charge_percentage`, `standard_charge_algorithm`, `methodology`, `median_amount`, `10th_percentile`, `90th_percentile`, `count`, `additional_payer_notes`} ] } ].
- Not JSON Lines. Spark's JSON reader with `multiLine=true` treats each file as one record, so a 1 GB file lands in one task. That is why staging exists.
- The CMS example file is `examples/JSON/v3_json_format_example.json` (the JSON README links a different, capitalized name that does not exist).

### Enums and value rules

- `setting`: `inpatient`, `outpatient`, `both`.
- `methodology`: `case rate`, `fee schedule`, `percent of total billed charges`, `per diem`, `other` (other requires an explanation in notes).
- Code types: CPT, NDC, HCPCS, RC, ICD, DRG, MS-DRG, R-DRG, S-DRG, APS-DRG, AP-DRG, APR-DRG, APC, LOCAL, EAPG, HIPPS, CDT, CDM, TRIS-DRG, CMG, MS-LTC-DRG.
- Drug type of measurement: GR, ME, ML, UN, F2, EA, GM.
- `count` is a **string**: `"0"`, `"1 through 10"`, or a whole number of 11 or more with no thousands separator. Parse to `allowed_count_low` and `allowed_count_high`.
- Median and percentile allowed amounts are required **only** when the rate is a percentage or algorithm (and the count is not 0). Expect them to be null for most dollar rates.
- Numerics must be positive; a value of 0 or a negative is a CMS deficiency. Real files may include `$` or `,`: strip them before casting and count it on the quality page.
- `standard_charge|min` and `|max` (JSON `minimum`, `maximum`) are required whenever any negotiated dollar exists.

## B5. Pipeline stage specs

Every stage is idempotent and can be rerun for one `source_id`.

### 1. Ingest (`pipeline/ingest.py`)
1. Load `config/sources.yml`. For each source: GET the source page, parse anchors with BeautifulSoup, select the one link matching the source's pattern. Zero or multiple matches is an error recorded in the manifest, not a crash of the whole run.
2. Stream the file to local disk (`requests` with `stream=True`, 8 MB chunks, connect and read timeouts, retry with backoff on 429 and 5xx). Compute SHA-256 while streaming.
3. If `.zip` or `.gz`, decompress and hash the inner file; record both.
4. Compare the hash with the latest manifest row for that source. If unchanged, record `changed=false` and stop for that source.
5. If changed, upload to `s3://<lake-bucket>/raw/source_id=<id>/fetched_date=<YYYY-MM-DD>/<original filename>` and append a manifest row.
6. Keep the local copy under `data/raw/<source_id>/` until Stage and Validate finish for that file; a final `cleanup` task deletes it. Stage and Validate read the local copy, falling back to S3 if it is missing.
- Manifest table `bronze.file_manifest` (Iceberg, appended with pyiceberg): `source_id string, source_page_url string, file_url string (store without query string), file_name string, sha256 string, bytes bigint, format string (csv|json), fetched_at timestamp, changed boolean, s3_key string, error string`.
- Never store the TriStar token in the manifest; strip query strings.

### 2. Stage (`pipeline/stage.py`, reference code in the appendix; runs right after Ingest)
- CSV: read rows 1 to 3 with Python's `csv` module (metadata and headers), normalize headers, then stream rows 4 onward with `pyarrow.csv.open_csv(skip_rows=3, column_names=..., newlines_in_values=True)` with every column typed as string, writing Parquet batch by batch. Detect layout: wide if any header matches `standard_charge|<a>|<b>|<metric>`.
- JSON: stream `standard_charge_information.item` with `ijson.items(..., use_float=True)` into gzipped NDJSON, one item per line; stream `modifier_information.item` into a second file; collect top-level metadata in one `ijson.parse` pass that skips the two big arrays.
- Output: `s3://<lake-bucket>/staged/source_id=<id>/sha256=<hash>/{items.ndjson.gz|data.parquet, modifiers.ndjson.gz, meta.json}`. Staged files expire after 30 days by lifecycle rule; they can be rebuilt from raw.
- Fail loudly on duplicate normalized headers.

### 3. Validate (`pipeline/validate.py`, runs after Stage because it needs the template version from `meta.json`)
- Command: `cms-hpt-validator <file> v3.0 -o json -e 1000`. Use `v2.2` when the file's `version` field starts with `2`.
- **The CLI exits 0 even when the file is invalid.** Read the JSON `valid` field.
- Output shape (verified): `{file, validatorVersion, dataDictionaryVersion, timestamp, valid, errorCount, alertCount, errors: [{path, message, columnName, value, allowedValues}], alerts: [...]}`. `path` is a cell like `F4` for CSV.
- `errorCount` is capped by `-e`. Store `error_limit_hit = errorCount >= limit`.
- Large files with many errors can exhaust Node memory; lower `-e` if that happens.
- Results table `bronze.validator_results` (Iceberg via pyiceberg): `source_id, sha256, validated_at, data_dictionary_version, valid, error_count, alert_count, error_limit_hit, message, column_name, cell_path, value` (one row per error or alert, plus one summary row with null message when valid).

### 4. Normalize and load silver (`pipeline/normalize.py`, `pipeline/load_silver.py`)
- Read staged data for changed sources only. Use the reader matching `meta.format` and `layout`: `silver_from_json`, `silver_from_tall`, or `silver_from_wide` (appendix).
- Add `source_id`, `sha256`, `mrf_last_updated_on`, `template_version`, `loaded_at`.
- Write `glue.silver.standard_charges` with dynamic partition overwrite on `source_id` (only that source's partition is replaced). Write `glue.silver.mrf_file_meta` the same way.
- Create Iceberg tables with `TBLPROPERTIES ('format-version'='2')` so Athena can read them (Athena support for v3 tables is unverified).
- Spark session config (unverified end to end; Maven was unreachable from the prototyping sandbox):

```python
spark = (SparkSession.builder.master("local[*]")
  .config("spark.jars.packages",
          "org.apache.iceberg:iceberg-spark-runtime-4.2_2.13:1.12.0,"
          "org.apache.iceberg:iceberg-aws-bundle:1.12.0")
  .config("spark.sql.extensions", "org.apache.iceberg.spark.extensions.IcebergSparkSessionExtensions")
  .config("spark.sql.catalog.glue", "org.apache.iceberg.spark.SparkCatalog")
  .config("spark.sql.catalog.glue.type", "glue")
  .config("spark.sql.catalog.glue.warehouse", f"s3://{LAKE_BUCKET}/warehouse/")
  .config("spark.sql.catalog.glue.io-impl", "org.apache.iceberg.aws.s3.S3FileIO")
  .config("spark.sql.sources.partitionOverwriteMode", "dynamic")
  .config("spark.driver.memory", "4g")
  .getOrCreate())
from pyspark.sql import functions as F
table = "glue.silver.standard_charges"
if not spark.catalog.tableExists(table):
    (df.writeTo(table).using("iceberg").partitionedBy(F.col("source_id"))
       .tableProperty("format-version", "2").create())
else:
    df.writeTo(table).overwritePartitions()   # replaces only the source_id partitions present in df
```
- `spark.jars.packages` downloads the two Iceberg jars from Maven Central on first run and caches them under `~/.ivy2`; in Docker, mount or bake that cache so every task does not re-download.
- The Iceberg docs pattern this follows is in `docs/docs/aws.md` of the apache/iceberg repo (Spark 3.5 example there; swap to the 4.2_2.13 runtime).
- AWS credentials reach Spark through the default provider chain (`AWS_PROFILE` or env vars mounted into the container).

### 5. Gold with dbt on Athena (`dbt/`)
- Profile: `type: athena`, `s3_staging_dir: s3://<athena-results-bucket>/dbt/`, `region_name`, `database: awsdatacatalog`, `schema: gold`, `work_group: <workgroup>`, threads 4.
- Sources: `silver.standard_charges`, `silver.mrf_file_meta`, `bronze.file_manifest`, `bronze.validator_results` (declare freshness on `file_manifest.fetched_at`).
- Every gold model: `materialized='table'` or `'incremental'`, `table_type='iceberg'`. Incremental uses `incremental_strategy='merge'` and `unique_key='rate_key'`. Glue-backed Iceberg tables need a unique S3 location per table; keep dbt-athena's default naming or set `s3_data_naming` so locations never collide.
- Athena does not support table constraints. Contracts (`contract: {enforced: true}`) check column names and types; not-null, unique, and relationships are data tests.
- Snapshots work on Iceberg in dbt-athena (confirmed in adapter source: `iceberg_snapshot_merge_sql`).
- Seeds: `sources.csv` (source_id, display_name, system, city), `procedures.csv` (code, code_type, label), `payer_map.csv` (raw_payer_name, raw_plan_name, payer_normalized, plan_normalized).
- Models: see B7.

### 6. Export (`pipeline/export.py`)
- `awswrangler.athena.read_sql_query("select * from gold.mart_procedure_prices", database="gold", workgroup=..., ctas_approach=False)` (the default CTAS approach creates temporary tables, which needs extra Glue permissions) and the same for `mart_file_quality`, then write both tables into `app/data/prices.duckdb` with the duckdb Python API. Assert the file is under 50 MiB (GitHub warns at 50 MiB and blocks at 100 MiB).
- Publishing the app update is a manual commit and push in the MVP.

### 7. Streamlit app (`app/streamlit_app.py`)
- Page 1, Cost comparison: pick a procedure, see one row per hospital location group and payer plan with negotiated dollar, gross, cash, min, max, methodology; show percentage or algorithm and percentiles only where present; a chart of negotiated dollars by hospital. State the file date for each hospital and the CMS caveat that rates are not patient out-of-pocket cost.
- Page 2, File quality: per source, valid or not, error counts by column, template version, file date, how many of the 10 procedures matched, and the share of payer names mapped.
- Community Cloud limits: about 2.7 GB memory, apps sleep after 12 hours without traffic.

## B6. Silver schemas

`silver.standard_charges` (partitioned by `source_id`). Grain: one row per item, code, setting, modifiers, payer, plan, methodology. Items with no payer rows keep one row with null payer columns.

| Column | Type | Notes |
| --- | --- | --- |
| source_id | string | partition |
| sha256 | string | file version |
| description | string | |
| code | string | DRG-family codes stripped of leading zeros |
| code_type | string | uppercased |
| modifiers | string | pipe-joined |
| setting | string | lowercased |
| drug_unit_of_measurement | double | |
| drug_type_of_measurement | string | |
| gross_charge | double | |
| discounted_cash | double | |
| payer_name | string | raw, as encoded |
| plan_name | string | raw, as encoded |
| negotiated_dollar | double | |
| negotiated_percentage | double | 70.5 means 70.5 percent |
| negotiated_algorithm | string | |
| methodology | string | lowercased |
| median_amount, p10_amount, p90_amount | double | only for percentage or algorithm rates |
| allowed_count_raw | string | as encoded |
| allowed_count_low, allowed_count_high | int | "1 through 10" gives 1 and 10 |
| min_negotiated, max_negotiated | double | |
| additional_generic_notes, additional_payer_notes | string | |
| mrf_last_updated_on | date | parse ISO and M/D/YYYY |
| template_version | string | |
| loaded_at | timestamp | |

`silver.mrf_file_meta` (partitioned by `source_id`): `source_id, sha256, hospital_name, template_version, mrf_last_updated_on, location_names array<string>, hospital_addresses array<string>, type_2_npis array<string>, license_state, license_number, attester_name, attestation_confirmed boolean, layout string (json|tall|wide), item_rows bigint, loaded_at`.

## B7. Gold models

| Model | Grain | Key columns |
| --- | --- | --- |
| `dim_source_file` | source_id | display_name, system, city, latest sha256, template_version, file date |
| `bridge_source_location` | source_id + location_name | location_name, address, position |
| `dim_payer_plan` | payer_plan_key | payer_normalized, plan_normalized, raw names array |
| `dim_procedure` | code + code_type | label |
| `fct_negotiated_rate` | rate_key = hash(source_id, description, code, code_type, setting, modifiers, payer_name, plan_name, methodology) | all measures from silver, filtered to the 10 codes |
| `fct_file_quality` | source_id + sha256 + rule | rule, passed, detail; rules from validator results plus pipeline checks (procedures matched, payer names unmapped, numeric cleanups) |
| `snap_negotiated_rate` | rate_key, SCD2 | dbt snapshot, strategy `check` on the measure columns |
| `mart_procedure_prices` | one row per fact row, denormalized | what the app reads |
| `mart_file_quality` | one row per source per rule | what the app reads |

Tests: contracts on all gold models; unique and not_null on every key; relationships from fact to each dim; accepted_values on setting, methodology, code_type; custom: `negotiated_dollar > 0` where not null; `p10_amount <= median_amount <= p90_amount` where all present; percentage or algorithm rows have `allowed_count_raw`; `payer_map` covers every raw payer name (warn first, then error once the map is complete).

## B8. Infrastructure (Terraform, `infra/`)

Resources (region `us-east-1` unless Chaz picks another):
- `aws_s3_bucket` lake bucket with `aws_s3_bucket_public_access_block` (all true), server-side encryption (SSE-S3), and `aws_s3_bucket_lifecycle_configuration`: `raw/` to a cheaper storage class after 60 days, `staged/` expires after 30 days.
- `aws_s3_bucket` for Athena query results, lifecycle expiry 7 days.
- `aws_glue_catalog_database`: `bronze`, `silver`, `gold`.
- `aws_athena_workgroup` with result location, `enforce_workgroup_configuration = true`, engine version 3, and `bytes_scanned_cutoff_per_query` set (for example 10 GB).
- `aws_budgets_budget` monthly cost budget with email notifications at $5 actual and $10 actual (and a forecast alert).
- `aws_iam_openid_connect_provider` for `token.actions.githubusercontent.com` and an `aws_iam_role` trusted only for `repo:<owner>/<repo>:*`, with least-privilege access to the lake bucket, results bucket, Glue databases, and the workgroup.
- Local development credentials: prefer an AWS CLI SSO profile; if using an IAM user, scope its policy to the same resources and never commit keys.
- State: local `terraform.tfstate`, gitignored and backed up. Moving to an S3 backend is optional; check the current Terraform S3 backend docs for locking options before doing it.

## B9. Airflow (`airflow/`)

- Start from `curl -LfO 'https://airflow.apache.org/docs/apache-airflow/3.3.2/docker-compose.yaml'`, then `mkdir -p ./dags ./logs ./plugins ./config`, set `AIRFLOW_UID` in `.env`, `docker compose up airflow-init`, `docker compose up`. UI at http://localhost:8080 (default login airflow / airflow). Docker needs at least 4 GB memory, about 8 GB recommended. The Compose setup is for development only.
- Build a custom image instead of `_PIP_ADDITIONAL_REQUIREMENTS` (uncomment `build: .` in the Compose file). Sketch (unverified build; verify in M1):

```dockerfile
FROM node:22-bookworm-slim AS validator
RUN npm install -g @cmsgov/hpt-validator-cli@1.12.0

FROM apache/airflow:3.3.2
USER root
RUN apt-get update \
 && apt-get install -y --no-install-recommends openjdk-17-jre-headless \
 && rm -rf /var/lib/apt/lists/*
COPY --from=validator /usr/local/bin/node /usr/local/bin/node
COPY --from=validator /usr/local/lib/node_modules /usr/local/lib/node_modules
RUN printf '#!/bin/sh\nexec node /usr/local/lib/node_modules/@cmsgov/hpt-validator-cli/dist/index.js "$@"\n' \
      > /usr/local/bin/cms-hpt-validator && chmod +x /usr/local/bin/cms-hpt-validator
USER airflow
# Pipeline deps live in their own venv so they never fight Airflow's pinned constraints
# (pyarrow, boto3, and dbt versions commonly conflict with them).
COPY requirements.txt /requirements.txt
RUN python -m venv /opt/pipeline && /opt/pipeline/bin/pip install --no-cache-dir -r /requirements.txt
```
  The base image is Debian bookworm, whose packaged Node.js is too old for the validator, which is why Node is copied from the official Node image. Set `JAVA_HOME` if Spark cannot find Java.
- Mount the repo (at `/opt/repo`) into the containers and mount `~/.aws` for credentials, not read-only, because AWS SSO writes refreshed tokens to its cache; set `AWS_PROFILE` in the Compose environment and run `aws sso login` before a session of DAG runs.
- Every pipeline step runs as a BashOperator calling the venv: for example `/opt/pipeline/bin/python -m pipeline.ingest --source-id {{ params.source_id }}` and `/opt/pipeline/bin/dbt build --project-dir /opt/repo/dbt --target prod`. Airflow's own environment imports nothing from the pipeline.
- DAG `price_transparency`, schedule `@weekly`, `catchup=False`, `max_active_runs=1`. Tasks: `ingest` (dynamic task mapping over the 12 source_ids) >> `stage` (mapped, changed files only) >> `validate` (mapped) >> `load_silver` (one Spark job for all changed sources) >> `dbt_build` >> `export` >> `cleanup`. Unchanged sources short-circuit after ingest.
- Retries: 2 with 5 minute delay on network tasks; none on dbt.

## B10. CI (`.github/workflows/ci.yml`)

- On pull_request and push to main:
  - Job `lint-test` (no AWS): set up Python, install deps, `ruff check`, `pytest` (uses the CMS example fixtures, starts local Spark), `sqlfluff lint dbt/models` with the Athena dialect, `dbt parse`.
  - Job `dbt-build` (needs `lint-test`): `permissions: id-token: write, contents: read`; `aws-actions/configure-aws-credentials@v6` with `role-to-assume` from Terraform output; `dbt build --target ci` into a `gold_ci` schema. Keep it cheap: CI builds against the same silver tables; models filter to the 10 codes so scans stay small.
- Java is preinstalled on GitHub's Ubuntu runners; set up Java 17 explicitly if Spark tests fail.

## B11. Testing strategy

- Fixtures: the three official CMS v3.0.0 examples, copied into `tests/fixtures/`:
  - https://raw.githubusercontent.com/CMSgov/hospital-price-transparency/master/examples/CSV/Tall%20Format%20Examples/V3.0.0_Tall_CSV_Format_Example.csv
  - https://raw.githubusercontent.com/CMSgov/hospital-price-transparency/master/examples/CSV/Wide%20Format%20Examples/V3.0.0_Wide_CSV_Format_Example.csv
  - https://raw.githubusercontent.com/CMSgov/hospital-price-transparency/master/examples/JSON/v3_json_format_example.json
- The core test: all three formats encode the same hospital, so all three readers must produce identical silver rows (verified: 53 rows each, 13 with a median allowed amount).
- Add small hand-made fixtures for edge cases as they appear in real files: v2.2 headers, `$` in numerics, zero-padded DRG codes, `1 through 10` counts, duplicate headers, BOM at file start, a zipped file.
- Ingest tests run against saved HTML snapshots of the three source pages (never live network in CI).
- dbt: data tests plus a few dbt unit tests on the payer mapping and code normalization logic.

## B12. Code conventions

- Python 3.12+, type hints, `ruff` defaults plus import sorting, line length 110, `logging` not `print`, f-strings.
- Config from env vars via `pipeline/settings.py`; no paths or bucket names hardcoded elsewhere.
- Functions small and pure where possible; Spark transforms take and return DataFrames so they are testable without AWS.
- Every CLI entry point takes `--source-id` to run one source.
- Commit early: one milestone step per commit, message in imperative mood.

## B13. Gotchas (read before debugging)

1. Spark cannot split a CMS JSON file. Never `spark.read.json(..., multiLine=True)` on a raw MRF; read the staged NDJSON.
2. CSV metadata rows 1 and 2 break any reader that assumes the header is row 1.
3. Header text varies in spacing and case; payer and plan names inside wide headers must keep their case.
4. The attestation header is a full paragraph of text; match it by prefix.
5. `count` is a string. "1 through 10" is valid.
6. Percentiles exist only for percentage or algorithm rates. Nulls elsewhere are correct, not a bug.
7. EIN is not unique per hospital (TriStar). Use `source_id`.
8. One file can cover several locations (Centennial covers six). Location rows go to the bridge, not the fact.
9. DRG codes may be zero-padded; code type may be `DRG` instead of `MS-DRG`.
10. The validator exits 0 on invalid files. Read `valid`.
11. Wide files can have thousands of columns. Build the unpivot programmatically (appendix) and expect long Spark plan analysis; test on the widest real file early.
12. `monotonically_increasing_id` in the wide reader is only stable if the input is read the same way in both branches; persist the DataFrame if you change the input.
13. Athena reads Iceberg format v2 tables; create tables with `format-version=2`.
14. Glue-backed Iceberg tables need unique S3 locations per table.
15. GitHub blocks files over 100 MiB; never commit raw or staged data, only the small DuckDB export.
16. Streamlit Community Cloud apps sleep after 12 hours idle; the README must stand on its own with a screenshot and video.
17. Ascension URLs in B3 are from January 2026 and unverified; confirm in M0.
18. The CMS JSON README links an example filename that does not exist; the real file is `v3_json_format_example.json`.
19. Do not `pip install` pipeline packages into Airflow's environment; use the `/opt/pipeline` venv (B9).
20. `dbt parse` and `sqlfluff` in CI need a profile; commit a `ci` profile with placeholder values for the no-AWS job and use sqlfluff's jinja templater (dialect `athena`) so linting never connects.
21. Code 470 also appears as a revenue code (`RC`) and a local `TRIS-DRG`. Always filter 470 on code type `MS-DRG` or `DRG` (found in M0).
22. CPT codes may be typed `HCPCS`; VUMC labels 80053 only that way. Accept both for the nine CPT codes (found in M0).
23. JSON nests `attester_name` under `attestation`; CSV has it at the top level (found in M0).

## B14. Milestones and definition of done

- **M0, validate the data:** download the four M0 files (vumc_main, vumc_clarksville, tristar_centennial, ascension_west), run the validator, record in `notes/m0_findings.md`: format, layout, size, template version, v3.0 fields present, validator result, distinct payer names (first 50), whether Midtown appears in the ascension_west `location_name`, whether the 10 codes appear and how they are coded. Gate: Spark still justified, scope still realistic.
- **M1, foundation:** repo scaffold, Terraform applied (all B8 resources), CI green on lint and tests with fixtures, Airflow image builds and the UI loads.
- **M2, ingest and normalize:** all 12 sources fetched, validated, staged, loaded to silver; rerun with no upstream change skips everything; silver counts compared against the Trilliant index (cross-check only). Gate: first shareable artifact.
- **M3, model and test:** dbt gold models, seeds, snapshot, tests, docs; `dbt build` green in CI through OIDC.
- **M4, orchestrate and serve:** one Airflow DAG run end to end; Streamlit app live on a public URL.
- **M5, package:** README in the order from the plan, architecture diagram, 2-minute video, LinkedIn post, resume bullets with real numbers.

## B15. Links

- CMS data dictionary repo: https://github.com/CMSgov/hospital-price-transparency
- CSV dictionary: https://github.com/CMSgov/hospital-price-transparency/blob/master/documentation/CSV/README.md
- JSON dictionary: https://github.com/CMSgov/hospital-price-transparency/blob/master/documentation/JSON/README.md
- v2.2 to v3.0 changes: https://github.com/CMSgov/hospital-price-transparency/blob/master/documentation/UPDATE_GUIDE.md
- CMS validator CLI: https://github.com/cmsgov/hpt-validator-cli
- CMS HPT tools (web validator, TXT generator): https://cmsgov.github.io/hpt-tool/
- CMS 70 shoppable services list (Becker's summary): https://www.beckershospitalreview.com/finance/the-70-cms-mandated-services-hospitals-must-post-online-next-year/
- Iceberg AWS integration (Glue catalog, S3FileIO): https://iceberg.apache.org/docs/latest/aws/
- Spark JSON data source (multiLine behavior): https://spark.apache.org/docs/3.4.1/sql-data-sources-json.html
- pyiceberg Glue catalog reference: https://py.iceberg.apache.org/reference/pyiceberg/catalog/glue
- dbt Iceberg on AWS (dbt-athena): https://docs.getdbt.com/docs/build/iceberg/adapters/aws-iceberg-support
- Airflow 3.3.2 Docker Compose guide: https://airflow.apache.org/docs/apache-airflow/stable/howto/docker-compose/index.html
- Streamlit Community Cloud limits: https://docs.streamlit.io/deploy/streamlit-community-cloud/manage-your-app
- GitHub large file limits: https://docs.github.com/en/repositories/working-with-files/managing-large-files/about-large-files-on-github
- Trilliant MRF index (row-count cross-check only): https://oria-data.trillianthealth.com/hospital/ascension_saint_thomas_west-9408a

---

# APPENDIX: Reference implementation (verified)

These three files were run on October 26, 2026 with Python 3.13, PySpark 4.2.0 (Java 21), and ijson 3.6.0 against the three CMS v3.0.0 example files, once with pyarrow 26.0.0 and again with the pinned requirements in B1 (pyarrow 25.0.1). All tests passed: the tall CSV, wide CSV, and JSON readers produced identical silver rows. They have **not** been run on a real hospital file yet, and they do not include the Iceberg write. Treat them as the starting point for `pipeline/stage.py`, `pipeline/normalize.py`, and `tests/test_normalize.py`; real files will surface edge cases (B11) that need new tests.

## A. `pipeline/stage.py`

```python
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
```

## B. `pipeline/normalize.py`

```python
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
```

## C. `tests/test_normalize.py`

Set `CMS_EXAMPLES` to the folder holding the three fixtures, or edit the paths to `tests/fixtures/`.

```python
"""The three CMS v3.0.0 example files encode the same hospital; all three readers must agree."""
import os
import pytest
from stage import stage_csv, stage_json, normalize_header
from normalize import spark_session, silver_from_json, silver_from_tall, silver_from_wide

E = os.environ.get("CMS_EXAMPLES", "/tmp/hpt/examples")
TALL = f"{E}/CSV/Tall Format Examples/V3.0.0_Tall_CSV_Format_Example.csv"
WIDE = f"{E}/CSV/Wide Format Examples/V3.0.0_Wide_CSV_Format_Example.csv"
JSON = f"{E}/JSON/v3_json_format_example.json"

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
```
