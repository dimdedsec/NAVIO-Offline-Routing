#!/usr/bin/env bash
# Test a real driving route against the freshly built tiles (not just tar headers).
set -euo pipefail
OUT="${1:?usage: github_smoke_route.sh OUTPUT_DIR}"
OUT="$(cd "$OUT" && pwd)"
IMAGE='ghcr.io/valhalla/valhalla:3.6.3'
NAME="navio-jambi-smoke-${GITHUB_RUN_ID:-local}-$$"
trap 'docker logs "$NAME" --tail 30 2>/dev/null || true; docker rm -f "$NAME" >/dev/null 2>&1 || true' EXIT
# Avoid publishing graph if service cannot load the tiles.
docker run --detach --name "$NAME" -p 127.0.0.1:8002:8002 \
  -v "$OUT:/work:ro" -w /work "$IMAGE" valhalla_service /work/valhalla.json 1
# Near Jambi City; final test must also be on Android / motor.
PAYLOAD='{"locations":[{"lat":-1.6098,"lon":103.6131},{"lat":-1.6207,"lon":103.5956}],"costing":"auto","directions_options":{"units":"kilometers"}}'
for i in $(seq 1 30); do
  if curl -fsS --connect-timeout 2 --max-time 20 \
      -H 'Content-Type: application/json' \
      -d "$PAYLOAD" http://127.0.0.1:8002/route \
      -o "$OUT/smoke-route.json"; then
    if python3 - "$OUT/smoke-route.json" <<'PY'
import json,sys
try:
    result=json.load(open(sys.argv[1]))
    trip=result['trip']
    legs=trip['legs']
    assert legs and legs[0].get('shape')
    assert legs[0].get('maneuvers')
    assert trip['summary']['length'] > 0
    print('PASS: Valhalla returned a Jambi route, geometry and maneuvers')
except Exception as exc:
    print('Not yet a valid route:', exc)
    sys.exit(1)
PY
    then
      exit 0
    fi
  fi
  echo "[NAVIO] Waiting for usable local Valhalla engine ($i/30)"
  sleep 4
done
echo '[NAVIO] FAIL: engine cannot return a valid Jambi route; release NOT published.' >&2
exit 1
