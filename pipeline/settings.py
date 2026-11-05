"""One place for env-driven config. No paths or bucket names are hardcoded anywhere else."""
import os
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SOURCES_FILE = REPO_ROOT / "config" / "sources.yml"
WORK_DIR = Path(os.environ.get("WORK_DIR", REPO_ROOT / "data" / "work"))
AWS_REGION = os.environ.get("AWS_REGION", "us-east-1")
LAKE_BUCKET = os.environ.get("LAKE_BUCKET", "")
ATHENA_RESULTS_BUCKET = os.environ.get("ATHENA_RESULTS_BUCKET", "")
ATHENA_WORKGROUP = os.environ.get("ATHENA_WORKGROUP", "")
USER_AGENT = "price-transparency-portfolio/0.1 (+https://github.com/LilCthulu/price-transparency-lakehouse)"
