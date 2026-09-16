#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

. scripts/_common.sh

# Afirmaciones 9, 25, 42, 43 y 46.

PLANTILLAS=skills/_shared/map-templates.md
ADAPTER=scripts/linear.py

# --- tercer tier: sin la fuente no hay ninguna plantilla que mirar ---

if [ ! -f "$PLANTILLAS" ]; then
  bail "[9] falta $PLANTILLAS; las cinco afirmaciones sobre las plantillas quedan sin correr"
fi

if [ ! -f "$ADAPTER" ]; then
  bail "[9] falta $ADAPTER; sin él no hay contra qué comparar las anclas del DD"
fi

# El cuerpo de la plantilla que vive bajo un encabezado, y nada más que eso: solo lo
# que está adentro de la PRIMERA cerca que sigue al encabezado. La separación es
# obligatoria y no prolijidad: sin ella los "## " del archivo y los "## " de las
# plantillas serían indistinguibles. Es el mismo idioma con el que check-language.sh
# despoja bloques cercados. La igualdad exacta del encabezado, y no un prefijo, es lo
# que hace que renombrarlo dé vacío y corte por tercer tier en vez de medir otra cosa.
bloque() {
  awk -v enc="$1" '
    $0 == enc { f = 1; next }
    !f { next }
    c == 0 && /^## / { exit }
    /^```/ { c++; if (c == 2) exit; next }
    c == 1 { print }
  ' "$PLANTILLAS"
}

# Vacío cuando las dos secuencias son idénticas, y si no un texto que las nombra a las
# dos. No lleva el número de la afirmación: el [N] va embebido en el string del fail, y
# cada llamador escribe el suyo.
diferencia() {
  if [ "$1" = "$2" ]; then
    printf ''
  else
    printf 'obtenida "%s", esperada "%s"' \
      "$(printf '%s\n' "$1" | tr '\n' '/')" "$(printf '%s\n' "$2" | tr '\n' '/')"
  fi
}

# --- afirmación 9: los seis encabezados del DD y las tres secciones de ejecución ---

# La primera mitad compara contra el adapter y no contra una copia: los seis
# encabezados salen de la constante que los escribe, acotada al bloque de su
# asignación. Un reformateo de ANCLAS da vacío y corta por tercer tier, así que se
# rompe fuerte y nunca en verde.
anclas="$(awk '
  /^ANCLAS = \[/ { dentro = 1 }
  dentro {
    resto = $0
    while (match(resto, /"[^"]*"/)) {
      print substr(resto, RSTART + 1, RLENGTH - 2)
      resto = substr(resto, RSTART + RLENGTH)
    }
    if (index($0, "]")) exit
  }
' "$ADAPTER" || true)"
require_nonempty "$anclas" "[9] la constante ANCLAS de $ADAPTER dio vacía; la extracción se rompió y la comparación probaría cero"

dd="$(bloque "## El DD" | sed -n 's/^## //p' || true)"
require_nonempty "$dd" "[9] el bloque del DD de $PLANTILLAS dio vacío; su encabezado se renombró o su cerca se movió"

d="$(diferencia "$dd" "$anclas")"
if [ -n "$d" ]; then
  fail "[9] la secuencia de encabezados del bloque del DD de $PLANTILLAS no es la de ANCLAS en $ADAPTER: $d"
fi

if printf '%s\n' "$dd" | grep -q '^Antes del mapa$'; then
  fail "[9] el bloque del DD de $PLANTILLAS nombra Antes del mapa, que no es un ancla de lectura sino la zona inerte debajo de la frontera"
fi

# La segunda mitad no tiene otra casa en el árbol, así que la secuencia esperada se
# escribe acá con su número al lado, igual que la 37 escribe el conjunto de las claves
# del ctx adentro de check-adapter.py.
EJECUCION="$(printf '%s\n' \
  "Qué hay que construir" \
  "Lo que ya está decidido" \
  "Qué queda fuera")"

ejecucion="$(bloque "## El cuerpo de una issue de ejecución" | sed -n 's/^## //p' || true)"
require_nonempty "$ejecucion" "[9] el bloque del cuerpo de una issue de ejecución de $PLANTILLAS dio vacío"

d="$(diferencia "$ejecucion" "$EJECUCION")"
if [ -n "$d" ]; then
  fail "[9] las secciones del cuerpo de una issue de ejecución de $PLANTILLAS no son las tres del research 06: $d"
fi

# --- afirmación 43: las seis del comentario de resolución, en secuencia ordenada ---

# Secuencia y no conjunto: la posición es parte de la afirmación, y "Lo que se cayó"
# tercera es lo que la fila nombra. Única casa, así que se escribe acá.
RESOLUCION="$(printf '%s\n' \
  "La decisión" \
  "Por qué" \
  "Lo que se cayó" \
  "Niebla graduada" \
  "Tickets nuevos" \
  "Qué corrige o empuja")"

resolucion="$(bloque "## El comentario de resolución" | sed -n 's/^## //p' || true)"
require_nonempty "$resolucion" "[43] el bloque del comentario de resolución de $PLANTILLAS dio vacío"

d="$(diferencia "$resolucion" "$RESOLUCION")"
if [ -n "$d" ]; then
  fail "[43] las secciones del comentario de resolución de $PLANTILLAS no son las seis en su orden: $d"
fi

# --- afirmación 42: una decisión ocupa una línea física ---

decisiones="$(bloque "## Decisiones hasta ahora (ejemplo)" || true)"
require_nonempty "$decisiones" "[42] el bloque de ejemplo de Decisiones hasta ahora de $PLANTILLAS dio vacío"

n_vinetas="$(printf '%s\n' "$decisiones" | grep -c '^- ' || true)"
if [ "$n_vinetas" -eq 0 ]; then
  fail "[42] el bloque de ejemplo de Decisiones hasta ahora de $PLANTILLAS no tiene ninguna viñeta"
fi

# Una viñeta partida en dos deja una segunda línea que no empieza con el marcador, y
# eso es exactamente lo que esta mitad ve: la primera sola no distingue una viñeta
# envuelta de una entera.
continuaciones="$(printf '%s\n' "$decisiones" | grep -v '^- ' | grep -c '[^[:space:]]' || true)"
if [ "$continuaciones" -ne 0 ]; then
  fail "[42] el bloque de ejemplo de Decisiones hasta ahora de $PLANTILLAS tiene $continuaciones línea con texto que no empieza una viñeta, así que alguna ocupa más de una línea física"
fi

# --- afirmación 25: los títulos de niebla no se repiten, y el archivo dice por qué ---

FRASE="es la clave única de una viñeta de niebla"

niebla="$(bloque "## La niebla (ejemplo)" || true)"
require_nonempty "$niebla" "[25] el bloque de ejemplo de niebla de $PLANTILLAS dio vacío"

titulos="$(printf '%s\n' "$niebla" | sed -n 's/^- \(\*\*[^*]*\*\*\).*/\1/p' || true)"
require_nonempty "$titulos" "[25] ninguna viñeta del bloque de niebla de $PLANTILLAS empieza con un título entre dobles asteriscos"

n_titulos="$(printf '%s\n' "$titulos" | grep -c . || true)"
if [ "$n_titulos" -lt 2 ]; then
  fail "[25] el bloque de niebla de $PLANTILLAS tiene $n_titulos viñeta con título, y con menos de dos la unicidad no aserta nada"
fi

repetidos="$(printf '%s\n' "$titulos" | sort | uniq -d | tr '\n' ' ' || true)"
if [ -n "$repetidos" ]; then
  fail "[25] estos títulos de niebla aparecen más de una vez en el bloque de $PLANTILLAS, y el título es la clave: $repetidos"
fi

if ! grep -qF "$FRASE" "$PLANTILLAS"; then
  fail "[25] $PLANTILLAS no dice que el título $FRASE, así que la unicidad de arriba sería una coincidencia y no una regla"
fi

# --- afirmación 46: ni las plantillas ni los comandos llevan bloques colapsables ---

comandos="$(find commands -maxdepth 1 -type f -name '*.md' | sort || true)"
require_nonempty "$comandos" "[46] el glob de commands/ no matcheó ningún archivo; la mitad de los comandos probaría sobre el conjunto vacío"

# El heredoc corre el while en el shell actual: alimentado por un pipe correría en un
# subshell y el acumulador moriría con él.
colapsables=""
while IFS= read -r archivo; do
  if [ -z "$archivo" ]; then continue; fi
  if grep -qiE '<details>|<summary>' "$archivo"; then
    colapsables="${colapsables}${colapsables:+ }$archivo"
  fi
done <<EOF
$PLANTILLAS
$comandos
EOF

if [ -n "$colapsables" ]; then
  fail "[46] estos archivos llevan <details> o <summary>, y el índice colapsable se comía dos tercios del documento con diez entradas: $colapsables"
fi

report

# Cardinales derivados y no escritos, igual que los de check-language y check-roster.
n_anclas="$(printf '%s\n' "$anclas" | grep -c . || true)"
n_resolucion="$(printf '%s\n' "$resolucion" | grep -c . || true)"
n_comandos="$(printf '%s\n' "$comandos" | grep -c . || true)"
echo "$CHECK_NAME: OK - $PLANTILLAS lleva las $n_anclas anclas del DD que escribe $ADAPTER, las secciones del cuerpo de ejecución y las $n_resolucion del comentario de resolución en su orden, una decisión por línea física y $n_titulos títulos de niebla distintos, y ni las plantillas ni los $n_comandos archivos de commands/ llevan bloques colapsables"
