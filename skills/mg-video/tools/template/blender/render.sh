#!/usr/bin/env bash
# Render frames with Blender in the background (nohup), so a tool timeout can't kill a long render.
#   bash render.sh                  every frame, final settings → out/frames/f0001.png …   (log: out/render.log)
#   bash render.sh 61-120           a range or list of frames (1,31,61-65); Blender frame f shows t = (f - 1) / fps
#   bash render.sh resume           continue after a crash or a kill: frames already in the folder are skipped
#   bash render.sh test [frames]    20 frames spread over the film (or the ones listed), 50 %, 16 samples → out/test/
#   bash render.sh preview          40 %, 8 samples, no motion blur → out/preview/, encoded to check/预览.mp4
#   overrides: SCALE=10 SAMPLES=8 MB=0 OUT=out/x BLENDER=/path/to/blender   FG=1 stays in the foreground
# Stop: kill the pid it prints. Then: bash encode.sh. One GPU-heavy render at a time on a shared machine.
set -euo pipefail
cd "$(dirname "$0")"
mkdir -p out
if [ "${FG:-0}" != 1 ]; then
  FG=1 nohup bash "$0" "$@" >> out/render.log 2>&1 &
  echo "rendering in the background, pid $! — follow: tail -f out/render.log   stop: kill $!"
  exit 0
fi
BLENDER=${BLENDER:-$(command -v blender || echo /Applications/Blender.app/Contents/MacOS/Blender)}
MODE=final RANGE='' RESUME=0
for a in "$@"; do
  case "$a" in
    final|test|preview) MODE=$a ;;
    resume) RESUME=1 ;;
    [0-9]*) RANGE=$a ;;
    *) echo "unknown argument: $a (see the top of render.sh)"; exit 1 ;;
  esac
done
case $MODE in
  final)   P=${SCALE:-100} S=${SAMPLES:-28} M=${MB:-1} O=${OUT:-out/frames} ;;
  test)    P=${SCALE:-50}  S=${SAMPLES:-16} M=${MB:-1} O=${OUT:-out/test}; RANGE=${RANGE:-test} ;;
  preview) P=${SCALE:-40}  S=${SAMPLES:-8}  M=${MB:-0} O=${OUT:-out/preview} ;;
esac
echo "== $(date '+%F %T') $MODE: frames ${RANGE:-all}, $P %, $S samples, motion blur $M → $O (resume $RESUME)"
trap 'kill $BPID 2>/dev/null' TERM INT
"$BLENDER" -b --factory-startup -P scene.py -- ${RANGE:+--frames "$RANGE"} --scale "$P" --samples "$S" --mb "$M" --out "$O" --resume "$RESUME" &
BPID=$!
wait $BPID
if [ "$MODE" = preview ]; then bash encode.sh "$O" check/预览.mp4; fi
