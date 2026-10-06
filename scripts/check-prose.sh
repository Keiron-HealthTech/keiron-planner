#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

. scripts/_common.sh

# Afirmaciones 55, 79, 81 y 82.

COMMAND_FILE=commands/map-work.md
COLLAPSE_SKILL=skills/map-collapse/SKILL.md

# Las dos literales salen de la misma oración. Con la primera sola, un archivo que
# nombrara el estado en cualquier otro contexto pasaría en verde sin prohibir nada.
DONE_STATUS='status: done'
PROHIBITION='never hangs work off a milestone already marked'

# El encabezado entero y no "three refusals" suelto: una frase en otro paso que dijera
# lo mismo dejaría el paso 3 con dos negativas y el check en verde.
REFUSALS_HEADING='## Step 3, the verdict, and the three refusals'
DELIVERIES_KEY='`designDeliveries`'

MAP_WORK_SKILL=skills/map-work/SKILL.md
DELIVERY_FLAG='--design-delivery'
DELIVERY_TITLE='`Diseño terminado: <the view>`'
HAND_CLOSE='closes it by hand in Linear, and no command closes it'

PROTOTYPE_SKILL=skills/prototype/SKILL.md
PROPOSAL_FILE=skills/prototype/PROPOSAL.md
LABEL_RULE='The label decides before the question does'
NOBODY_ASKED='nobody is asked'
PROPOSAL_LINK='[PROPOSAL.md](PROPOSAL.md)'
PROPOSAL_ROW='| Written proposal |'
ONE_PROPOSAL='One proposal is the default'
SEVERAL_APPROACHES='two or three approaches when the decision spans several views or `Diseño` asks for them'
NO_TWO_VARIANTS='The minimum of two variants does not apply'
LIVE_LINK='lives in Claude Design, behind its live link, and the agent never builds variants there'

# --- tercer tier: un grep sobre un archivo que falta no mira nada ---

if [ ! -f "$COMMAND_FILE" ]; then
  bail "[55] falta $COMMAND_FILE; la prohibición de aterrizar en un corte terminado se probaría sobre un archivo que no está"
fi

if [ ! -f "$COLLAPSE_SKILL" ]; then
  bail "[79] falta $COLLAPSE_SKILL; la negativa por una entrega de diseño abierta se probaría sobre un archivo que no está"
fi

if [ ! -f "$MAP_WORK_SKILL" ]; then
  bail "[81] falta $MAP_WORK_SKILL; el paso de la entrega de diseño se probaría sobre un archivo que no está"
fi

if [ ! -f "$PROTOTYPE_SKILL" ]; then
  bail "[82] falta $PROTOTYPE_SKILL; la rama de Diseño se probaría sobre un archivo que no está"
fi

if [ ! -f "$PROPOSAL_FILE" ]; then
  bail "[82] falta $PROPOSAL_FILE; un ticket de Diseño no tiene rama de propuesta escrita y cae en las de código"
fi

# --- afirmación 55: el comando nombra la prohibición de aterrizar en un corte terminado ---

# Dos fails y no un bail: una corrida tiene que poder nombrar las dos faltas.
if ! grep -qF "$DONE_STATUS" "$COMMAND_FILE"; then
  fail "[55] $COMMAND_FILE no nombra el $DONE_STATUS de un corte terminado, así que no dice sobre cuál no se aterriza"
fi

if ! grep -qF "$PROHIBITION" "$COMMAND_FILE"; then
  fail "[55] $COMMAND_FILE nombra el estado pero no la prohibición; sin ella la frase describe un corte y no prohíbe nada"
fi

# --- afirmación 79: /map-collapse se niega con una entrega de diseño abierta ---

steps="$(grep -c '^## Step [0-9]' "$COLLAPSE_SKILL" || true)"
if [ "$steps" != 9 ]; then
  fail "[79] $COLLAPSE_SKILL tiene $steps pasos y tiene que tener nueve: la tercera negativa vive adentro del paso 3 y no agrega uno"
fi

if ! grep -qxF "$REFUSALS_HEADING" "$COLLAPSE_SKILL"; then
  fail "[79] el paso 3 de $COLLAPSE_SKILL no se llama \"the three refusals\", así que la negativa por una entrega abierta no está donde se deriva el veredicto"
fi

# El rango es el cuerpo del paso 3, del encabezado al del paso 4: la clave nombrada en
# otro paso no frena el colapso antes de la primera escritura.
step3="$(sed -n '/^## Step 3,/,/^## Step 4,/p' "$COLLAPSE_SKILL")"
if ! printf '%s\n' "$step3" | grep -qF "$DELIVERIES_KEY"; then
  fail "[79] el paso 3 de $COLLAPSE_SKILL no lee $DELIVERIES_KEY, así que una entrega de diseño abierta no frena el colapso"
fi

# --- afirmación 81: /map-work pasa la entrega de diseño y la nombra en el reporte ---

# Los dos rangos se acotan en el encabezado siguiente: el flag nombrado en otro paso no
# llega a la invocación de ticket:resolve, y la entrega nombrada en otro paso no llega al
# reporte.
step8="$(sed -n '/^## Step 8,/,/^## Step 9,/p' "$MAP_WORK_SKILL")"
for literal in "$DELIVERY_FLAG" "$DELIVERY_TITLE"; do
  if ! printf '%s
' "$step8" | grep -qF -- "$literal"; then
    fail "[81] el paso 8 de $MAP_WORK_SKILL no nombra $literal, así que una resolución de Diseño cierra sin su entrega"
  fi
done
step10="$(sed -n '/^## Step 10,/,$p' "$MAP_WORK_SKILL")"
if ! printf '%s
' "$step10" | grep -qF "design delivery"; then
  fail "[81] el paso 10 de $MAP_WORK_SKILL no nombra la entrega de diseño en el reporte"
fi
if ! printf '%s
' "$step10" | grep -qF "$HAND_CLOSE"; then
  fail "[81] el paso 10 de $MAP_WORK_SKILL no dice que Diseño cierra la entrega a mano y que ningún comando la cierra"
fi

# --- afirmación 82: con hitl:design, prototype conversa hasta una propuesta escrita ---

# El rango es la sección que elige la rama: la regla del label escrita en otra sección
# llegaría tarde, después de la pregunta que decide entre las ramas de código.
pick="$(sed -n '/^## Pick a branch$/,/^## Rules/p' "$PROTOTYPE_SKILL")"
for literal in '`hitl:design`' "$PROPOSAL_LINK" "$LABEL_RULE" "$NOBODY_ASKED"; do
  if ! printf '%s\n' "$pick" | grep -qF -- "$literal"; then
    fail "[82] la sección que elige la rama en $PROTOTYPE_SKILL no nombra $literal, así que un ticket de Diseño llega a la pregunta por código"
  fi
done
if ! grep -qF -- "$PROPOSAL_ROW" "$PROTOTYPE_SKILL"; then
  fail "[82] la tabla de elecciones de $PROTOTYPE_SKILL no tiene la fila de la propuesta escrita, así que la regla de dos variantes la alcanza"
fi

for part in '`Para qué es la vista`' '`Qué debe tener`' '`Qué considerar`' '`Qué queda abierto`'; do
  if ! grep -qF -- "$part" "$PROPOSAL_FILE"; then
    fail "[82] $PROPOSAL_FILE no nombra la parte $part de la propuesta"
  fi
done
for literal in "$ONE_PROPOSAL" "$SEVERAL_APPROACHES" "$NO_TWO_VARIANTS" "$LIVE_LINK"; do
  if ! grep -qF -- "$literal" "$PROPOSAL_FILE"; then
    fail "[82] $PROPOSAL_FILE no dice: $literal"
  fi
done

report

echo "$CHECK_NAME: OK - $COMMAND_FILE nombra la prohibición de aterrizar en un corte con $DONE_STATUS, y el paso 3 de $COLLAPSE_SKILL lee $DELIVERIES_KEY en la tercera de sus negativas, con nueve pasos, y el paso 8 de $MAP_WORK_SKILL pasa $DELIVERY_FLAG y su paso 10 nombra la entrega que Diseño cierra a mano, y con hitl:design $PROTOTYPE_SKILL lleva a $PROPOSAL_FILE sin preguntar, con sus cuatro partes y una propuesta por defecto"
