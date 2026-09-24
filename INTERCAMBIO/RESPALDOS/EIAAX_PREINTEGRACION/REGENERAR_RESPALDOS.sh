#!/usr/bin/env bash
# Regenera respaldos verificables V1/V2 sin secretos (git archive).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
OUT="$(cd "$(dirname "$0")" && pwd)"
TS="$(date -u +%Y%m%dT%H%M%SZ)"
V1_SHA="e8cb853a2c447fd5e136a0907e44d68ce2c8cf81"
V2_SHA="dc1e6cda8d3de6695d9a052a2a13afdb5f431077"

cd "$ROOT"
git fetch origin "$V1_SHA" "$V2_SHA" fase2-candidato-final-certificado

V1_FILE="$OUT/EIAAX_V1_e8cb853_${TS}.tar.gz"
V2_FILE="$OUT/EIAAX_V2_dc1e6cd_${TS}.tar.gz"

git archive --format=tar.gz --prefix=EIAAX_V1_e8cb853/ "$V1_SHA" -o "$V1_FILE"
git archive --format=tar.gz --prefix=EIAAX_V2_dc1e6cd/ "$V2_SHA" -o "$V2_FILE"

echo "V1: $V1_FILE"
sha256sum "$V1_FILE"
echo "V2: $V2_FILE"
sha256sum "$V2_FILE"
