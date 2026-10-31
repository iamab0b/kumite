#!/usr/bin/env bash
set -euo pipefail
HOST_PYTHON="${KUMITE_HOST_PYTHON:-/mnt/c/Users/sahil/AppData/Local/Programs/Python/Python311/python.exe}"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
case "${1:-}" in
  python) shift; exec "$HOST_PYTHON" "$@" ;;
  ps) shift; exec powershell.exe -NoProfile -ExecutionPolicy Bypass -File "$@" ;;
  cmd) shift; exec cmd.exe /c "$@" ;;
  *) echo "usage: tools/host.sh python <args> | ps <script.ps1> [args] | cmd <command>" >&2; exit 64 ;;
esac
