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

# El recorrido de citaciones camina DOS globs: commands/*.md y skills/*/SKILL.md. El
# segundo hace falta desde que un comando del mapa rutea a una skill y el token de cierre
# vive allá: con un solo glob, las citaciones de una skill no las ve nadie y un token que
# el contrato no declara pasa en verde.
#
# skills/_shared/ queda FUERA a propósito, y no es prolijidad: ahí vive el contrato, y si
# cosechara sus propias citaciones la igualdad se compararía contra sí misma y no
# asertaría nada. El -mindepth 2 ya lo dejaría afuera de por sí, porque el contrato no es
# un SKILL.md, y la exclusión explícita es la que sobrevive a que alguien agregue uno.
fuentes="$( { find commands -maxdepth 1 -type f -name '*.md'
              find skills -mindepth 2 -maxdepth 2 -type f -name 'SKILL.md' \
                ! -path 'skills/_shared/*'; } | sort || true)"
require_nonempty "$fuentes" "[7] el recorrido de commands/ y skills/ no matcheó ningún archivo; el lado de las citaciones daría vacío y la igualdad probaría cero"

# Solo la forma de citación, y nunca cualquier palabra en kebab-case entre backticks:
# un valor de ROUTE, un nombre de archivo y una bandera viven o van a vivir en
# commands/*.md y en skills/*/SKILL.md con esa misma pinta y ninguno es un token.
de_comandos="$(printf '%s\n' "$fuentes" \
  | xargs grep -ho '`next_recommended: [a-z0-9][a-z0-9-]*`' \
  | sed 's/^`next_recommended: //' | sed 's/`$//' | sort -u || true)"
require_nonempty "$de_comandos" "[7] ningún archivo de commands/ ni de skills/ cita un token en la forma de citación; la igualdad de conjunto vacío contra conjunto vacío pasaría sin asertar nada"

# Qué archivos citan, derivado y nunca escrito: es lo que deja ver de un vistazo que el
# recorrido nuevo llega a las skills y no solo a los comandos.
citadores="$(printf '%s\n' "$fuentes" \
  | xargs grep -l '`next_recommended: ' 2>/dev/null | sort || true)"

solo_contrato="$(comm -23 <(printf '%s\n' "$del_contrato") <(printf '%s\n' "$de_comandos") | tr '\n' ' ' || true)"
solo_comandos="$(comm -13 <(printf '%s\n' "$del_contrato") <(printf '%s\n' "$de_comandos") | tr '\n' ' ' || true)"
if [ -n "$solo_contrato" ] || [ -n "$solo_comandos" ]; then
  fail "[7] los tokens de $CONTRATO y las citaciones de commands/ y skills/ no son el mismo conjunto: solo en el contrato $solo_contrato, solo en las citaciones $solo_comandos"
fi

# --- afirmaciones 8 y 16: el recorrido de commands/ parte los ROUTE: en dos conjuntos ---

# Reusa $lista y no vuelve a extraerla: una segunda extracción sería una segunda copia
# del alcance del recorrido, y las dos podrían divergir.

# Los dos acumuladores sobreviven al while porque el heredoc lo corre en el shell actual:
# alimentado por un pipe correría en un subshell y morirían con él. Es el mismo motivo por
# el que check-language.sh alimenta su while igual.
rutean=""
no_rutean=""

while IFS= read -r archivo; do
  if [ -z "$archivo" ]; then continue; fi
  base="${archivo##*/}"

  # Sin head, igual que la afirmación 3: quedarse con la primera de dos líneas en silencio
  # es parte de lo que esta afirmación tiene que ver.
  ruta="$(sed -n 's/^ROUTE: //p' "$archivo" || true)"
  if [ -z "$ruta" ]; then
    fail "[8] $archivo no declara ninguna línea ROUTE:"
    continue
  fi
  primera="${ruta%%$'\n'*}"
  if [ "$primera" != "$ruta" ]; then
    fail "[8] $archivo declara más de una línea ROUTE:, y la extracción tiene que ser de una sola; la primera dice '$primera'"
    continue
  fi

  case "$ruta" in
    skills/*/SKILL.md)
      rutean="${rutean}${rutean:+$'\n'}$base"
      if [ ! -f "$ruta" ]; then
        fail "[16] el ROUTE: de $archivo nombra $ruta, que no existe"
      fi
      ;;
    *)
      no_rutean="${no_rutean}${no_rutean:+$'\n'}$base"
      # Vuelve a mirar lo que la afirmación 3 ya mira para map-status.md, y a propósito: la 3
      # lo mira porque ese ROUTE: es el literal read-only, y acá se mira porque ese archivo
      # cayó del lado de los que no rutean a skill. Si una de las dos se rompe, la otra sigue.
      if [ -d "skills/${base%.md}" ]; then
        fail "[16] $archivo no rutea a ninguna skill y existe skills/${base%.md}"
      fi
      ;;
  esac
done <<EOF
$lista
EOF

# La única guarda anti vacuidad del recorrido: hasta hoy este conjunto era vacío y la
# cláusula de existencia probaba cero. El otro conjunto no la lleva porque la igualdad de
# abajo ya falla cuando queda vacío.
require_nonempty "$rutean" "[16] ningún archivo de commands/ rutea a una skill; la cláusula de existencia probaría sobre el conjunto vacío"

# El par literal es lo que la celda Afirmación de la fila dice, palabra por palabra, y no
# el cardinal, que no puede vivir en este archivo.
esperado="$(printf 'map-status.md\nplanner-setup.md\n' | sort)"
obtenido="$(printf '%s\n' "$no_rutean" | sort)"
if [ "$esperado" != "$obtenido" ]; then
  fail "[16] los archivos de commands/ que no rutean a una skill tienen que ser map-status.md y planner-setup.md, y son: $(printf '%s\n' "$obtenido" | tr '\n' ' ')"
fi

# --- afirmación 39a: el flag de bootstrap vive en un solo comando ---

# Reusa $lista por la misma regla que el recorrido de arriba: una segunda extracción sería
# una segunda copia del alcance del roster, y las dos podrían divergir.
con_bootstrap=""
while IFS= read -r archivo; do
  if [ -z "$archivo" ]; then continue; fi
  if grep -q -- "--bootstrap" "$archivo"; then
    base="${archivo##*/}"
    con_bootstrap="${con_bootstrap}${con_bootstrap:+$'\n'}$base"
  fi
done <<EOF
$lista
EOF

# Igualdad y no pertenencia, y ahí está la mitad que importa: un check que solo mirara que
# el literal está en map-new.md pasaría en verde con el flag copiado en otro comando, y la
# afirmación probaría la mitad de lo que enuncia. El nombre literal es lo que la celda
# Afirmación dice, palabra por palabra, y no el cardinal, que no puede vivir en este
# archivo. La igualdad cubre además el conjunto vacío, así que no lleva guarda propia.
esperado_flag="map-new.md"
obtenido_flag="$(printf '%s\n' "$con_bootstrap" | sort | tr '\n' ' ' || true)"
obtenido_flag="${obtenido_flag% }"
if [ "$esperado_flag" != "$obtenido_flag" ]; then
  fail "[39] el literal --bootstrap tiene que aparecer en map-new.md y en ningún otro archivo de commands/, y los que lo llevan son: ${obtenido_flag:-ninguno}"
fi

# --- afirmación 67: el prompt del subagente de research y sus dos únicas puntas ---

SUBAGENTE=skills/_shared/research-subagent.md

# No es tercer tier: que el archivo falte y que nadie lo cite son dos fallas distintas,
# y una corrida tiene que poder nombrar las dos. Cortar acá sepultaría la segunda.
if [ ! -f "$SUBAGENTE" ]; then
  fail "[67] falta $SUBAGENTE, que es el único prompt de research; las skills que lo citen apuntan a un archivo ausente"
fi

# Reusa $fuentes, el mismo recorrido de dos globs que la afirmación 7 ya arma. Una
# segunda extracción sería una segunda copia del alcance del roster, y las dos podrían
# divergir. skills/_shared/ queda afuera de ese recorrido, así que el archivo no se
# cosecha a sí mismo y la igualdad no se compara contra su propia ruta.
citan="$(printf '%s\n' "$fuentes" \
  | xargs grep -lF "$SUBAGENTE" 2>/dev/null | sort || true)"
require_nonempty "$citan" "[67] ningún archivo de commands/ ni de skills/ nombra $SUBAGENTE por su ruta; la igualdad de abajo probaría sobre el conjunto vacío"

# Igualdad y no pertenencia, por el mismo motivo que la 39a: un check que solo mirara
# que las dos skills lo nombran pasaría en verde con una tercera punta copiándolo sin
# pedir permiso, y la afirmación probaría la mitad de lo que enuncia.
esperado_subagente="$(printf 'skills/map-new/SKILL.md\nskills/map-work/SKILL.md\n' | sort)"
if [ "$citan" != "$esperado_subagente" ]; then
  fail "[67] a $SUBAGENTE lo tienen que nombrar skills/map-new/SKILL.md y skills/map-work/SKILL.md, y lo nombran: $(printf '%s\n' "$citan" | tr '\n' ' ')"
fi

# --- afirmación 70: cada skill declara un name: igual a su directorio ---

# Reusa $fuentes por la misma regla que la 67: una segunda extracción sería una segunda
# copia del alcance del roster, y las dos podrían divergir.
skills_md="$(printf '%s\n' "$fuentes" | grep '^skills/' || true)"
require_nonempty "$skills_md" "[70] el recorrido de skills/ no matcheó ningún SKILL.md; la comparación de name: con el directorio probaría sobre el conjunto vacío"

while IFS= read -r f; do
  if [ -z "$f" ]; then continue; fi
  dir="${f#skills/}"
  dir="${dir%/SKILL.md}"
  if [ "$(head -1 "$f")" != "---" ]; then
    fail "[70] $f no abre con un frontmatter"
    continue
  fi
  # Sin esta guarda, la extracción de abajo leería el cuerpo entero y un name: del cuerpo
  # contaría como si fuera del frontmatter.
  if ! awk 'NR > 1 && $0 == "---" { c = 1; exit } END { exit !c }' "$f"; then
    fail "[70] $f abre un frontmatter y nunca lo cierra"
    continue
  fi
  frontmatter="$(awk 'NR==1 && $0 != "---" {exit} NR==1 {next} /^---$/ {exit} {print}' "$f")"
  lineas="$(printf '%s\n' "$frontmatter" | grep '^name:' || true)"
  if [ -z "$lineas" ]; then
    fail "[70] $f no declara name: en su frontmatter"
    continue
  fi
  if [ "${lineas%%$'\n'*}" != "$lineas" ]; then
    fail "[70] $f declara más de una línea name:"
    continue
  fi
  valor="$(printf '%s\n' "${lineas#name:}" | sed 's/^[[:space:]]*//; s/[[:space:]]*$//')"
  case "$valor" in
    \"*\") valor="${valor#\"}"; valor="${valor%\"}" ;;
    \'*\') valor="${valor#\'}"; valor="${valor%\'}" ;;
  esac
  if [ -z "$valor" ]; then
    fail "[70] $f declara name: vacío"
    continue
  fi
  if [ "$valor" != "$dir" ]; then
    fail "[70] $f declara name: '$valor' y su directorio es $dir"
  fi
done <<EOF
$skills_md
EOF

report

# Conteos derivados y no escritos, igual que los que imprime check-language: el cardinal
# del conjunto no vive en este archivo, se calcula acá y se muestra.
tokens="$(printf '%s\n' "$del_contrato" | grep -c . || true)"
archivos="$(printf '%s\n' "$fuentes" | grep -c . || true)"
ruteadores="$(printf '%s\n' "$rutean" | grep -c . || true)"
quienes="$(printf '%s\n' "$citadores" | tr '\n' ' ')"
quienes="${quienes% }"
subagentistas="$(printf '%s\n' "$citan" | tr '\n' ' ')"
subagentistas="${subagentistas% }"
skills_ok="$(printf '%s\n' "$skills_md" | grep -c . || true)"
echo "$CHECK_NAME: OK - el ROUTE: de $COMANDO es read-only y no tiene skill, los $tokens tokens de $CONTRATO son exactamente los que citan los $archivos archivos de commands/ y skills/, y quienes citan son $quienes, el ROUTE: de cada archivo de commands/ que rutea a una skill apunta a una que existe, $ruteadores en total, el flag de bootstrap vive solo en $esperado_flag, a $SUBAGENTE lo nombran por su ruta exactamente $subagentistas, y las $skills_ok skills de skills/ declaran un name: igual a su directorio"
