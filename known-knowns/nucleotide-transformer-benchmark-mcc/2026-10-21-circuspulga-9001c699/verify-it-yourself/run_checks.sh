#!/bin/sh
# run from the package folder: sh verify-it-yourself/run_checks.sh
# downloads benchmark.csv (URL, space commit and sha256 in the-record-we-beat/record.md); the checker verifies the sha256
set -e
URL=https://huggingface.co/spaces/InstaDeepAI/nucleotide_transformer_benchmark/resolve/90ff8dbbf126daecf33d7c0221e2e5ff241fc354/data/benchmark.csv
TMP=$(mktemp)
curl -sfL "$URL" -o "$TMP"
python3 verify-it-yourself/check_fold_audit.py "$TMP"
rm -f "$TMP"
