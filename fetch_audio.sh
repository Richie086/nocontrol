#!/usr/bin/env bash
# Mirror all No Control tracks locally (m4a + wav + cover art) and make MP3s.
# Usage: ./fetch_audio.sh [outdir]   (needs curl, python3; ffmpeg for mp3)
set -euo pipefail
OUT="${1:-audio}"; mkdir -p "$OUT"
python3 -c 'import json;[print(t["n"],t["id"],t["title"]) for t in json.load(open("tracks.json"))]' | while read -r n id title; do
  safe=$(printf '%02d - %s' "$n" "$title" | sed 's/[^A-Za-z0-9 ._()&,-]/_/g')
  for ext in m4a wav; do
    [ -f "$OUT/$safe.$ext" ] || curl -fsSL -o "$OUT/$safe.$ext" "https://storage.googleapis.com/producer-app-public/clips/$id.$ext"
  done
  [ -f "$OUT/$safe.jpg" ] || curl -fsSL -o "$OUT/$safe.jpg" "https://storage.googleapis.com/producer-app-public/assets/$id.jpg" || true
  if command -v ffmpeg >/dev/null && [ ! -f "$OUT/$safe.mp3" ]; then
    ffmpeg -loglevel error -y -i "$OUT/$safe.wav" -codec:a libmp3lame -q:a 0 -metadata title="$title" -metadata artist="No Control" -metadata album="No Control" "$OUT/$safe.mp3"
  fi
  echo "ok: $safe"
done
