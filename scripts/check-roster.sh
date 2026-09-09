#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

. scripts/_common.sh

# Afirmaciones 3 y 7.

COMANDO=commands/map-status.md
CONTRATO=skills/_shared/map-contract.md

# El encabezado que acota la extracción del lado del contrato, y es un literal
# compartido con el archivo: si allá se renombra, acá la extracción da vacío y
# require_nonempty corta. Va sin backticks porque un backtick adentro de comillas
# dobles es sustitución de comando, y sin el cardinal porque el cardinal no puede
# vivir en este archivo.
ENCABEZADO="## The closed set of next_recommended tokens"

# --- tercer tier: sin las dos fuentes no hay nada que comparar ---

if [ ! -f "$COMANDO" ]; then
  bail "[3] falta $COMANDO; las afirmaciones sobre el roster de comandos quedan sin correr"
fi

if [ ! -f "$CONTRATO" ]; then
  bail "[7] falta $CONTRATO; las fallas derivadas de una fuente ausente sepultan el mensaje que importa"
fi

# --- afirmación 3: el ROUTE del comando de solo lectura, y la skill que no existe ---

# La misma extracción que ya usa la spec de packaging, y a propósito SIN head: quedarse
# con la primera de dos líneas en silencio es exactamente lo que esta afirmación tiene
# que ver, y es donde este check es más estricto que el del plugin hermano.
declarado="$(sed -n 's/^ROUTE: //p' "$COMANDO" || true)"
require_nonempty "$declarado" "[3] $COMANDO no declara ninguna línea ROUTE:"

primera="${declarado%%$'\n'*}"
if [ "$primera" != "$declarado" ]; then
  fail "[3] $COMANDO declara más de una línea ROUTE:, y la extracción tiene que ser de una sola; la primera dice '$primera'"
elif [ "$declarado" != "read-only" ]; then
  fail "[3] el ROUTE: de $COMANDO dice '$declarado' y tiene que decir read-only"
fi

if [ -d skills/map-status ]; then
  fail "[3] existe el directorio skills/map-status; un comando de solo lectura no conduce ninguna disciplina, así que no tiene skill"
fi

# --- afirmación 7: los tokens del contrato son los que citan los comandos ---

# Va primero porque las dos extracciones de abajo dependen de que el glob matchee: con
# el glob vacío, grep recibiría el patrón literal y moriría con un mensaje que no dice
# nada de la afirmación.
lista="$(find commands -maxdepth 1 -type f -name '*.md' | sort || true)"
require_nonempty "$lista" "[7] el glob de commands/ no matcheó ningún archivo; el lado de los comandos daría vacío y la igualdad probaría cero"

# El helper tabla(ruta, encabezado) de check-adapter.py, portado a awk. El alcance por
# encabezado es obligatorio y no prolijidad: el contrato lleva una segunda tabla, la de
# tipo de ticket a disciplina, cuyas primeras celdas también van entre backticks, y sin
# el alcance esos nombres entrarían al conjunto y la igualdad fallaría siempre.
del_contrato="$(awk -v enc="$ENCABEZADO" '
  /^## / { dentro = ($0 == enc); next }
  !dentro { next }
  /^\|/ {
    n = split($0, celdas, "|")
    if (n < 3) next
    p = celdas[2]
    gsub(/^[ \t]+/, "", p)
    gsub(/[ \t]+$/, "", p)
    if (length(p) > 2 && substr(p, 1, 1) == "`" && substr(p, length(p), 1) == "`") {
      print substr(p, 2, length(p) - 2)
    }
  }
' "$CONTRATO" | sort -u || true)"
require_nonempty "$del_contrato" "[7] la tabla de tokens de $CONTRATO bajo su encabezado dio vacío; el encabezado se renombró o la tabla se quedó sin filas"

# Solo la forma de citación, y nunca cualquier palabra en kebab-case entre backticks:
# un valor de ROUTE, un nombre de archivo y una bandera viven o van a vivir en
# commands/*.md con esa misma pinta y ninguno es un token.
de_comandos="$(grep -ho '`next_recommended: [a-z0-9][a-z0-9-]*`' commands/*.md \
  | sed 's/^`next_recommended: //' | sed 's/`$//' | sort -u || true)"
require_nonempty "$de_comandos" "[7] ningún archivo de commands/ cita un token en la forma de citación; la igualdad de conjunto vacío contra conjunto vacío pasaría sin asertar nada"

solo_contrato="$(comm -23 <(printf '%s\n' "$del_contrato") <(printf '%s\n' "$de_comandos") | tr '\n' ' ' || true)"
solo_comandos="$(comm -13 <(printf '%s\n' "$del_contrato") <(printf '%s\n' "$de_comandos") | tr '\n' ' ' || true)"
if [ -n "$solo_contrato" ] || [ -n "$solo_comandos" ]; then
  fail "[7] los tokens de $CONTRATO y las citaciones de commands/ no son el mismo conjunto: solo en el contrato $solo_contrato, solo en los comandos $solo_comandos"
fi

report

# Conteos derivados y no escritos, igual que los que imprime check-language: el cardinal
# del conjunto no vive en este archivo, se calcula acá y se muestra.
tokens="$(printf '%s\n' "$del_contrato" | grep -c . || true)"
archivos="$(printf '%s\n' "$lista" | grep -c . || true)"
echo "$CHECK_NAME: OK - el ROUTE: de $COMANDO es read-only y no tiene skill, y los $tokens tokens de $CONTRATO son exactamente los que citan los $archivos archivos de commands/"
