#!/usr/bin/env bash
# render_text.sh <variant> <base_cut.mp4> <out.mp4>
# แปะตัวหนังสือจาก text/<variant>.ass ลงบน base cut
set -euo pipefail
V="${1:?variant (A|B|C)}"; BASE="${2:?base_cut.mp4}"; OUT="${3:?out.mp4}"
HERE="$(cd "$(dirname "$0")/.." && pwd)"
ffmpeg -v error -i "$BASE" -vf "ass=$HERE/text/$V.ass" \
  -c:v libx264 -preset slow -crf 19 -pix_fmt yuv420p -movflags +faststart -an \
  "$OUT" -y
echo "wrote $OUT"
