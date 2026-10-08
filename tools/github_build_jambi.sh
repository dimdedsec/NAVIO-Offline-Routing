#!/usr/bin/env bash
# GitHub Actions runner: prepare Jambi-area routable tiles and publishable tar.
# Deliberately narrower than all Sumatra to fit standard GitHub runner storage.
set -euo pipefail
OUT="${1:?usage: github_build_jambi.sh OUTPUT_DIR}"
mkdir -p "$OUT"
OUT="$(cd "$OUT" && pwd)"
BASE='https://download.geofabrik.de/asia/indonesia/sumatra-latest.osm.pbf'
IMAGE='ghcr.io/valhalla/valhalla:3.6.3'
echo '[NAVIO] Disk available'; df -h "$OUT"
echo '[NAVIO] Download PBF Sumatra from Geofabrik'
curl -fL --retry 3 --connect-timeout 30 "$BASE" -o "$OUT/sumatra.osm.pbf"
test -s "$OUT/sumatra.osm.pbf"
# Buffer around approximate Jambi provincial envelope, not administrative boundaries.
# DO NOT label this package as full-island coverage: bbox 100.6,-3.3,105.2,-0.1.
echo '[NAVIO] Extract Jambi bbox + road corridor buffer'
osmium extract --overwrite --strategy=complete_ways \
  --bbox=100.6,-3.3,105.2,-0.1 "$OUT/sumatra.osm.pbf" \
  -o "$OUT/region.osm.pbf"
test -s "$OUT/region.osm.pbf"
rm -f "$OUT/sumatra.osm.pbf"

echo "[NAVIO] Prepare native Valhalla tools: $IMAGE"
docker pull "$IMAGE"
echo '[NAVIO] Build tiles and indexed tar extract'
docker run --rm -v "$OUT:/work" -w /work "$IMAGE" bash -ec '
  set -euo pipefail
  mkdir -p /work/valhalla_tiles
  valhalla_build_config \
    --mjolnir-tile-dir /work/valhalla_tiles \
    --mjolnir-tile-extract /work/jambi-tiles.tar \
    --mjolnir-timezone /work/valhalla_tiles/timezones.sqlite \
    --mjolnir-admin /work/valhalla_tiles/admins.sqlite > /work/valhalla.json
  valhalla_build_timezones > /work/valhalla_tiles/timezones.sqlite
  valhalla_build_admins -c /work/valhalla.json /work/region.osm.pbf
  valhalla_build_tiles -c /work/valhalla.json /work/region.osm.pbf
  valhalla_build_extract -c /work/valhalla.json -v
'
python3 tools/check_navio_publisher.py --tar "$OUT/jambi-tiles.tar" --max-bytes 2100000000
ls -lh "$OUT/jambi-tiles.tar"
df -h "$OUT"
