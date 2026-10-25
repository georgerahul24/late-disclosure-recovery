#!/usr/bin/env bash
# Generate the Synthea population used for all reported experiments.
# Runs on a compute node (inside the holder job):
#   srun --jobid=<hold> --overlap -c 16 --mem=32G bash cluster/run_synthea.sh
#
# Pinned for reproducibility: Synthea release, seed, population size, state.
# Writes CSV exports to node scratch ($SCR/synthea/out-<seed>/csv) and a provenance file
# data/synthea/PROVENANCE.txt (committed) with versions and sha256 sums.
set -euo pipefail
cd "$(dirname "$0")/.."
SYNTHEA_VERSION=${SYNTHEA_VERSION:-v3.3.0}
POP=${POP:-6000}
SEED=${SEED:-20261026}
CSEED=${CSEED:-20261026}
STATE=${STATE:-Massachusetts}
SCR=${SCR:-/ssd_scratch/gr/lma}
mkdir -p "$SCR/synthea" data/synthea

# 1. JDK 17 (Eclipse Temurin), node-local
if [ ! -x "$SCR/jdk/bin/java" ]; then
  curl -fsSL "https://api.adoptium.net/v3/binary/latest/17/ga/linux/x64/jdk/hotspot/normal/eclipse" -o "$SCR/jdk.tgz"
  mkdir -p "$SCR/jdk" && tar -xzf "$SCR/jdk.tgz" -C "$SCR/jdk" --strip-components=1 && rm "$SCR/jdk.tgz"
fi
JAVA="$SCR/jdk/bin/java"
"$JAVA" -version 2>&1 | head -1

# 2. Synthea jar (pinned release; falls back to master build only if missing)
JAR="$SCR/synthea/synthea-$SYNTHEA_VERSION.jar"
if [ ! -s "$JAR" ]; then
  curl -fsSL "https://github.com/synthetichealth/synthea/releases/download/$SYNTHEA_VERSION/synthea-with-dependencies.jar" -o "$JAR" \
  || { SYNTHEA_VERSION=master-branch-latest; JAR="$SCR/synthea/synthea-$SYNTHEA_VERSION.jar";
       curl -fsSL "https://github.com/synthetichealth/synthea/releases/download/master-branch-latest/synthea-with-dependencies.jar" -o "$JAR"; }
fi

# 3. Generate (CSV only, full history, alive and dead kept; we filter later)
OUT="$SCR/synthea/out-$SEED"
rm -rf "$OUT"
cd "$SCR/synthea"
"$JAVA" -Xmx24g -jar "$JAR" -p "$POP" -s "$SEED" -cs "$CSEED" \
  --exporter.baseDirectory "$OUT" \
  --exporter.fhir.export false --exporter.fhir.transaction_bundle false \
  --exporter.hospital.fhir.export false --exporter.practitioner.fhir.export false \
  --exporter.csv.export true --exporter.years_of_history 0 \
  "$STATE" > "$OUT.log" 2>&1
cd - >/dev/null
tail -5 "$OUT.log"

# Raw CSVs stay on node scratch (home quota is tiny). The converter
# (scripts/synthea_to_records.py) reads them from here.
ln -sfn "$OUT/csv" "$SCR/synthea/latest-csv"
{
  echo "generated: $(date -Iseconds) on $(hostname)"
  echo "synthea_release: $SYNTHEA_VERSION"
  echo "synthea_jar_sha256: $(sha256sum "$JAR" | cut -d' ' -f1)"
  echo "java: $("$JAVA" -version 2>&1 | head -1)"
  echo "args: -p $POP -s $SEED -cs $CSEED $STATE, csv export, years_of_history=0"
  echo "summary: $(grep -E 'Records: total' "$OUT.log" || tail -1 "$OUT.log")"
  echo "raw_csv_dir: $OUT/csv (node $(hostname), not in git)"
  for f in "$OUT"/csv/{patients,medications,conditions,encounters,observations}.csv; do echo "$(basename "$f"): $(wc -l < "$f") lines sha256=$(sha256sum "$f" | cut -d' ' -f1)"; done
} > data/synthea/PROVENANCE.txt
cat data/synthea/PROVENANCE.txt
