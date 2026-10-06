#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

. scripts/_common.sh

# Afirmaciones 49, 6 y 83.

if ! git rev-parse --is-inside-work-tree > /dev/null 2>&1; then
  bail "[49] esto no es un work tree de git; no hay árbol trackeado que caminar"
fi

# La fuente es lo trackeado y no lo que haya en disco, así que .gitignore se respeta sin
# reimplementarlo.
# El filtro va por grep -i y no por un glob de ls-files, que es case-sensitive: un
# README.MD no lo matchea y quedaría fuera del check sin que nadie lo note.
archivos="$(git ls-files | grep -iE '\.md$' | grep -v '^vendor/' | grep -v '^\.scratch/' || true)"
require_nonempty "$archivos" "[49] la extracción de .md del árbol dio vacío; el filtro de vendor/ y .scratch/ o el glob se movieron"

# El acumulador se llena en el mismo while que ya parsea el frontmatter para la 49, así
# que el hecho de qué es un frontmatter no tiene una segunda copia. Sobrevive al while
# porque el heredoc lo corre en el shell actual: alimentado por un pipe correría en un
# subshell y el acumulador moriría con él.
ingleses=""

while IFS= read -r f; do
  if [ -z "$f" ]; then continue; fi
  # Solo el bloque de frontmatter: un lang: en el cuerpo no cuenta, y un archivo sin
  # frontmatter da vacío.
  fm="$(awk 'NR==1 && $0 != "---" {exit} NR==1 {next} /^---$/ {exit} {print}' "$f" || true)"
  declarado="$(printf '%s\n' "$fm" | grep -E '^lang: (en|es)$' | head -1 || true)"
  if [ -z "$declarado" ]; then
    fail "[49] $f no declara lang: con valor en o es en su frontmatter"
  fi
  if [ "$declarado" = "lang: en" ]; then
    ingleses="${ingleses}${ingleses:+$'\n'}$f"
  fi
done <<EOF
$archivos
EOF

# --- afirmación 6: la prosa de los archivos en inglés no lleva caracteres del español ---

# Sobre el conjunto vacío la afirmación pasaría vacuamente, así que su fuente ausente es
# tercer tier y no un verde.
require_nonempty "$ingleses" "[6] ningún .md del árbol declara lang: en; la afirmación pasaría sobre el conjunto vacío"

while IFS= read -r f; do
  if [ -z "$f" ]; then continue; fi
  # Fuera los bloques cercados y después los tramos entre backticks: un identificador en
  # español dentro de código no es prosa en español.
  prosa="$(awk '/^```/ {dentro = !dentro; next} !dentro' "$f" | sed 's/`[^`]*`//g' || true)"
  # Alternación de literales y no una clase de caracteres: bajo locale C una bracket
  # expression con estos caracteres compara BYTES y da rojo sobre cualquier carácter que
  # comparta el byte inicial 0xC3, como la cedilla o la diéresis. Medido con BSD grep, que
  # es el que este script invoca: la clase da 1 y la alternación da 0 sobre un archivo sin
  # un solo acento del español. Así la afirmación no depende del locale del runner, y no
  # hay que fijarlo.
  acentos="$(printf '%s\n' "$prosa" | grep -oE 'á|é|í|ó|ú|ñ|¿|¡|Á|É|Í|Ó|Ú|Ñ' | sort -u | tr -d '\n' || true)"
  # No se reporta número de línea: la búsqueda corre sobre la prosa ya despojada, así que
  # sus números no serían los del archivo. Los caracteres alcanzan para grepearlos.
  if [ -n "$acentos" ]; then
    fail "[6] $f declara lang: en y su prosa tiene caracteres del español: $acentos"
  fi
done <<EOF
$ingleses
EOF

# --- afirmación 83: los .md de una skill hablan el idioma de su SKILL.md ---

lang_of() {
  awk 'NR==1 && $0 != "---" {exit} NR==1 {next} /^---$/ {exit} {print}' "$1" \
    | grep -E '^lang: ' | head -1 || true
}

skills="$(printf '%s\n' "$archivos" | grep -E '^skills/[^/]+/SKILL\.md$' || true)"
require_nonempty "$skills" "[83] ningún skills/<nombre>/SKILL.md trackeado; la afirmación pasaría sobre el conjunto vacío"

hermanos=0
while IFS= read -r s; do
  if [ -z "$s" ]; then continue; fi
  dir="${s%/SKILL.md}"
  propio="$(lang_of "$s")"
  # Un enlace que el SKILL.md da a un archivo de su directorio que no existe es una rama
  # que el modelo abre y no encuentra; el enlace cuenta aunque el archivo no esté trackeado.
  enlazados="$(grep -oE '\]\([A-Za-z0-9_-]+\.md\)' "$s" | sed 's/^](//; s/)$//' | sort -u || true)"
  while IFS= read -r e; do
    if [ -z "$e" ]; then continue; fi
    if [ ! -f "$dir/$e" ]; then
      fail "[83] $s enlaza $e y $dir/$e no existe"
    fi
  done <<EOS
$enlazados
EOS
  while IFS= read -r h; do
    if [ -z "$h" ] || [ "$h" = "$s" ]; then continue; fi
    hermanos=$((hermanos + 1))
    if [ "$(lang_of "$h")" != "$propio" ]; then
      fail "[83] $h no declara el mismo $propio que $s"
    fi
  done <<EOS
$(printf '%s\n' "$archivos" | grep -E "^$dir/[^/]+\.[mM][dD]$" || true)
EOS
done <<EOF
$skills
EOF

report

n="$(printf '%s\n' "$archivos" | grep -c . || true)"
m="$(printf '%s\n' "$ingleses" | grep -c . || true)"
k="$(printf '%s\n' "$skills" | grep -c . || true)"
echo "$CHECK_NAME: OK - $n archivos .md del árbol declaran lang:, y $m en inglés sin prosa en español, y los $hermanos .md hermanos de las $k skills existen donde su SKILL.md los enlaza y declaran su mismo lang:"
