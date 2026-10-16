#!/usr/bin/env bash
# Python environment for audio (mgsound) and the check scripts, in ~/.venvs/mg-video, plus a check of the toolchain.
#   bash setup.sh           create or update the environment (once), then check
#   bash setup.sh --check   only check: installs nothing (exit 1 if something required is missing)
set -euo pipefail
SKILL="$(cd "$(dirname "$0")/.." && pwd)"
VENV=${MG_VENV:-~/.venvs/mg-video}
CHECK=0; [ "${1:-}" = --check ] && CHECK=1
FAIL=0
bad() { echo "  FAIL  $*"; FAIL=1; }
recent() { "$1" -c 'import sys; sys.exit(sys.version_info < (3, 11))' 2>/dev/null; }   # numpy 2.4 needs Python ≥ 3.11
ver() { "$1" -c 'import sys; print("%d.%d" % sys.version_info[:2])' 2>/dev/null || echo none; }
UV_HINT='install uv: HOMEBREW_NO_AUTO_UPDATE=1 brew install uv (plain `brew install` can hang for minutes in auto-update)'

# Python: fail before installing anything when the environment can't be built
if [ -x "${VENV}/bin/python" ]; then
  recent "${VENV}/bin/python" && echo "  ok    ${VENV} (Python $(ver "${VENV}/bin/python"))" \
    || bad "${VENV} has Python $(ver "${VENV}/bin/python"); numpy 2.4 needs ≥ 3.11: rm -rf ${VENV}, ${UV_HINT}, rerun"
elif command -v uv >/dev/null; then echo "  todo  create ${VENV} with uv (Python 3.13)"
elif recent python3; then echo "  todo  create ${VENV} with python3 $(ver python3)"
else bad "no uv, and python3 is $(ver python3) (numpy 2.4 needs ≥ 3.11): ${UV_HINT}"; fi
if [ "${CHECK}" = 0 ] && [ "${FAIL}" = 0 ]; then
  if [ ! -x "${VENV}/bin/python" ]; then
    mkdir -p "$(dirname "${VENV}")"
    if command -v uv >/dev/null; then uv venv -p 3.13 "${VENV}"; else python3 -m venv "${VENV}"; fi
  fi
  if command -v uv >/dev/null; then VIRTUAL_ENV="${VENV}" uv pip install -r "${SKILL}/requirements.txt"
  else "${VENV}/bin/pip" install -r "${SKILL}/requirements.txt"; fi
fi
if [ -x "${VENV}/bin/python" ]; then
  "${VENV}/bin/python" -c "import numpy, scipy, soundfile, pyloudnorm, PIL" 2>/dev/null && echo "  ok    audio and check packages import" \
    || { [ "${CHECK}" = 1 ] && echo "  todo  install requirements.txt into ${VENV}" || bad "packages don't import in ${VENV}"; }
fi

# The rest of the toolchain (checked only)
if command -v ffmpeg >/dev/null; then
  V=$(ffmpeg -hide_banner -version | sed -n '1s/^ffmpeg version \([^ ]*\).*/\1/p'); MAJ=${V%%.*}
  case "${MAJ}" in
    ''|*[!0-9]*) echo "  warn  ffmpeg ${V}: version not recognised (tools are tested on 9.x)" ;;
    *) if [ "${MAJ}" -lt 7 ]; then echo "  warn  ffmpeg ${V}: tools are tested on 9.x; before 7 (the -vsync era) -fps_mode and setparams colour tags may be missing"
       else echo "  ok    ffmpeg ${V}"; fi ;;
  esac
  ffmpeg -hide_banner -filters 2>/dev/null | grep -q ' drawtext ' || echo "  note  this ffmpeg has no drawtext filter (no tool here needs it)"
else bad "no ffmpeg: brew install ffmpeg"; fi
command -v node >/dev/null && echo "  ok    node $(node --version)" || bad "no node: brew install node"
{ ls -d ~/Library/Caches/ms-playwright/chromium* || ls -d ~/.cache/ms-playwright/chromium*; } >/dev/null 2>&1 && echo "  ok    Playwright Chromium" \
  || echo "  todo  npx playwright install chromium (in a project folder)"
command -v blender >/dev/null || [ -x /Applications/Blender.app/Contents/MacOS/Blender ] && echo "  ok    Blender (3D card)" \
  || echo "  note  no Blender; only the 3D card needs it: brew install --cask blender"
[ "${FAIL}" = 0 ] && echo "$([ "${CHECK}" = 1 ] && echo 'check done' || echo 'environment ready')" || echo "fix the FAIL lines above"
exit "${FAIL}"
