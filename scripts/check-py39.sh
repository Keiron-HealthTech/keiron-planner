#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

. scripts/_common.sh

# Afirmación 19.

adapter=scripts/linear.py
contrato=scripts/LINEAR-OPERATIONS.md

# --- tercer tier: sin fuente y sin intérprete no hay nada que ejecutar ---

[ -f "$adapter" ] || bail "[19] falta $adapter; las afirmaciones sobre el adapter quedan sin correr"
[ -f "$contrato" ] || bail "[19] falta $contrato; las afirmaciones sobre el adapter quedan sin correr"

py39=""
for cand in "${PY39:-}" python3.9 /usr/bin/python3; do
  [ -n "$cand" ] || continue
  v="$("$cand" -c 'import sys;print("%d.%d" % sys.version_info[:2])' 2>/dev/null || true)"
  if [ "$v" = "3.9" ]; then py39="$cand"; break; fi
done
require_nonempty "$py39" "[19] no hay ningún intérprete 3.9 en la cadena PY39, python3.9, /usr/bin/python3"

# Los doce nombres salen del contrato y no de una lista escrita acá: una lista propia
# sería una tercera copia que nadie compara contra las otras dos.
operaciones="$(awk -F'|' '
  /^## / { dentro = ($0 == "## Las doce operaciones"); next }
  dentro && /^\|/ { c=$2; gsub(/ /,"",c); if (c ~ /^`.*`$/) { gsub(/`/,"",c); print c } }
' "$contrato")"
require_nonempty "$operaciones" "[19] la tabla Las doce operaciones de $contrato dio vacío"

# --- afirmación 19 --------------------------------------------------------------

if ! "$py39" -c 'import importlib.util, sys
sys.dont_write_bytecode = True
spec = importlib.util.spec_from_file_location("linear", sys.argv[1])
spec.loader.exec_module(importlib.util.module_from_spec(spec))' "$adapter" 2>/dev/null; then
  bail "[19] $adapter no importa bajo Python 3.9"
fi

for op in $operaciones; do
  if ! "$py39" "$adapter" "$op" --help >/dev/null 2>&1; then
    fail "[19] $op --help no sale cero bajo Python 3.9"
  fi
done

report

n="$(printf '%s\n' "$operaciones" | grep -c . || true)"
echo "$CHECK_NAME: OK - $adapter importa y sus $n subcomandos responden --help bajo Python $("$py39" -c 'import sys;print("%d.%d.%d" % sys.version_info[:3])')"
