#!/usr/bin/env bash
# Create a project folder: bash new.sh [--blender] <folder> [width height fps seconds bed]
#   page project (default): index.html, video.json, cues.json, audio.py, CREDITS.md, package.json + Playwright
#   --blender: scene.py, render.sh, encode.sh, video.json, cues.json, audio.py, CREDITS.md (no page, no Playwright)
# Example: bash new.sh films/paperclip-test 1920 1080 30 8 explainer
set -euo pipefail
BLENDER=0 POS=()
for a in "$@"; do case "$a" in --blender) BLENDER=1 ;; -*) echo "unknown option $a"; exit 1 ;; *) POS+=("$a") ;; esac; done
set -- ${POS[@]+"${POS[@]}"}
DIR="${1:?usage: bash new.sh [--blender] <folder> [width height fps seconds bed]}"
W="${2:-1920}"; H="${3:-1080}"; FPS="${4:-30}"; DUR="${5:-10}"; BED="${6:-explainer}"
SKILL="$(cd "$(dirname "$0")/.." && pwd)"
TPL="${SKILL}/tools/template"
if (( W % 2 || H % 2 )); then echo "width and height must be even (H.264); got ${W}x${H}"; exit 1; fi
for f in index.html scene.py cues.json; do
  if [ -e "${DIR}/${f}" ]; then echo "${DIR} already has ${f}; not overwriting"; exit 1; fi
done
mkdir -p "${DIR}"/{fonts,assets,out,check}
NAME="$(basename "${DIR}")"
fill() { sed -e "s|__W__|${W}|g" -e "s|__H__|${H}|g" -e "s|__FPS__|${FPS}|g" -e "s|__DUR__|${DUR}|g" \
             -e "s|__RECIPE__|${BED}|g" -e "s|__SKILL__|${SKILL}|g" -e "s|__NAME__|${NAME}|g" "$1" > "$2"; }
for f in cues.json audio.py; do fill "${TPL}/${f}" "${DIR}/${f}"; done
printf '# Sources and licenses\n\n| File | Source | License |\n|---|---|---|\n' > "${DIR}/CREDITS.md"
if [ "${BLENDER}" = 1 ]; then
  printf '{ "width": %s, "height": %s, "fps": %s, "duration": %s }\n' "${W}" "${H}" "${FPS}" "${DUR}" > "${DIR}/video.json"
  cp "${TPL}"/blender/{scene.py,render.sh,encode.sh} "${DIR}/"
  command -v blender >/dev/null || [ -x /Applications/Blender.app/Contents/MacOS/Blender ] || echo "no Blender yet: brew install --cask blender"
else
  fill "${TPL}/index.html" "${DIR}/index.html"
  printf '{ "width": %s, "height": %s, "fps": %s, "duration": %s, "motionBlur": { "samples": 1, "shutter": 0.5 } }\n' "${W}" "${H}" "${FPS}" "${DUR}" > "${DIR}/video.json"
  # Not `npm init`: it fails when the folder name is Chinese. "type": "module" lets Node helper scripts use import
  # (and they find their own folder with fileURLToPath(import.meta.url): a URL pathname is percent-encoded)
  printf '{ "name": "mg-film", "private": true, "type": "module" }\n' > "${DIR}/package.json"
  (cd "${DIR}" && npm i --no-audit --no-fund playwright >/dev/null 2>&1) || echo "npm i playwright failed; run it inside the folder"
  [ -d ~/Library/Caches/ms-playwright ] || [ -d ~/.cache/ms-playwright ] || echo "no Playwright browser yet: run npx playwright install chromium"
fi
[ -x ~/.venvs/mg-video/bin/python ] || echo "no Python environment for audio yet: bash ${SKILL}/tools/setup.sh"
echo "created ${DIR} ($([ "${BLENDER}" = 1 ] && echo 'Blender, ')${W}x${H} ${FPS}fps ${DUR}s, bed ${BED})"
