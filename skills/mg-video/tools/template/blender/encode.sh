#!/usr/bin/env bash
# PNG frames + out/audio.wav → 成片.mp4 (H.264 CRF 16, yuv420p, bt709 tags, AAC 256k 48 kHz).
#   bash encode.sh                              out/frames → 成片.mp4
#   bash encode.sh out/preview check/预览.mp4     another folder / file
# Every frame f0001.png … must be there: ffmpeg silently stops at the first gap.
set -euo pipefail
cd "$(dirname "$0")"
IN=${1:-out/frames} OUT=${2:-成片.mp4}
num() { sed -n "s/.*\"$1\"[^0-9.]*\([0-9.]*\).*/\1/p" video.json | head -n 1; }
FPS=$(num fps) N=$(awk -v d="$(num duration)" -v f="$(num fps)" 'BEGIN { printf "%d", d * f + 0.5 }')
missing=0 first=''
for ((f = 1; f <= N; f++)); do
  [ -f "$(printf '%s/f%04d.png' "$IN" "$f")" ] || { missing=$((missing + 1)); [ -n "$first" ] || first=$f; }
done
if [ "$missing" -gt 0 ]; then echo "$IN is missing $missing of $N frames (first: f$(printf %04d "$first").png): bash render.sh resume"; exit 1; fi
AUDIO=(-an)
[ -f out/audio.wav ] && AUDIO=(-i out/audio.wav -map 0:v:0 -map 1:a:0 -af apad -t "$(awk -v n="$N" -v f="$FPS" 'BEGIN { printf "%.6f", n / f }')" -c:a aac -b:a 256k -ar 48000)
# ffmpeg 9 takes colour tags from the frames (PNG: sRGB transfer) and ignores -color_trc; setparams stamps bt709 on all three
ffmpeg -hide_banner -loglevel error -y -framerate "$FPS" -start_number 1 -i "$IN/f%04d.png" "${AUDIO[@]}" -frames:v "$N" \
  -vf "scale=trunc(iw/2)*2:trunc(ih/2)*2:out_color_matrix=bt709:out_range=tv,format=yuv420p,setparams=color_primaries=bt709:color_trc=bt709:colorspace=bt709:range=tv" \
  -c:v libx264 -preset slow -crf 16 -movflags +faststart "$OUT"
echo "$OUT: $N frames at $FPS fps$([ -f out/audio.wav ] && echo ', with out/audio.wav')"
