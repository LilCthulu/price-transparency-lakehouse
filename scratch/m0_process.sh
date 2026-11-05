#!/bin/bash
# Waits for each M0 file to finish downloading, then runs inspect and the validator on it, one at a time.
ROOT=/c/Users/karat/claude/projects/price-transparency-lakehouse
PY="$ROOT/.venv/Scripts/python.exe"; D="$ROOT/data/m0"; N="$ROOT/notes"; mkdir -p "$N/m0"
for f in "$@"; do
  b="${f%.*}"
  while ps -ef | grep -q "[c]url.* -o $f " || { [ ! -s "$D/$f" ] && ps -ef | grep -q "[m]0_download.sh"; }; do sleep 15; done
  if [ ! -s "$D/$f" ]; then echo "MISSING $f"; continue; fi
  case "$f" in *.csv) out="$D/$b.parquet";; *) out="$D/$b.ndjson.gz";; esac
  echo "== $f $(date +%T) $(stat -c %s "$D/$f") bytes"
  "$PY" -I "$ROOT/scratch/m0_inspect.py" "$D/$f" "$out" "$N/m0/$b.json"
  ver=$("$PY" -I -c "import json,sys;print((json.load(open(sys.argv[1],encoding='utf-8')).get('meta') or {}).get('version') or '')" "$N/m0/$b.json")
  case "$ver" in 2*) v=v2.2;; *) v=v3.0;; esac
  if [ ! -s "$N/validator_$b.json" ]; then
    (cd "$D" && NODE_OPTIONS=--max-old-space-size=8192 cms-hpt-validator "$f" "$v" -o json -e 1000 > "$N/validator_$b.json") || echo "VALIDATOR FAILED rc=$? $f"
  fi
  echo "validator($v) done $(date +%T)"
done
echo ALL_DONE
ls -l "$D"
