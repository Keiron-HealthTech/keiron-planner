#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

. scripts/_common.sh

# Afirmación 49.

if ! git rev-parse --is-inside-work-tree > /dev/null 2>&1; then
  bail "[49] esto no es un work tree de git; no hay árbol trackeado que caminar"
fi

# La fuente es lo trackeado y no lo que haya en disco, así que .gitignore se respeta sin
# reimplementarlo.
archivos="$(git ls-files '*.md' | grep -v '^vendor/' | grep -v '^\.scratch/' || true)"
require_nonempty "$archivos" "[49] la extracción de .md del árbol dio vacío; el filtro de vendor/ y .scratch/ o el glob se movieron"

while IFS= read -r f; do
  if [ -z "$f" ]; then continue; fi
  # Solo el bloque de frontmatter: un lang: en el cuerpo no cuenta, y un archivo sin
  # frontmatter da vacío.
  fm="$(awk 'NR==1 && $0 != "---" {exit} NR==1 {next} /^---$/ {exit} {print}' "$f" || true)"
  declarado="$(printf '%s\n' "$fm" | grep -E '^lang: (en|es)$' | head -1 || true)"
  if [ -z "$declarado" ]; then
    fail "[49] $f no declara lang: con valor en o es en su frontmatter"
  fi
done <<EOF
$archivos
EOF

report

n="$(printf '%s\n' "$archivos" | grep -c . || true)"
echo "$CHECK_NAME: OK - $n archivos .md del árbol declaran lang:"
