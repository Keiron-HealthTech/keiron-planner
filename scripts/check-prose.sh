#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

. scripts/_common.sh

# Afirmaciones 55 y 79.

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

# --- tercer tier: un grep sobre un archivo que falta no mira nada ---

if [ ! -f "$COMMAND_FILE" ]; then
  bail "[55] falta $COMMAND_FILE; la prohibición de aterrizar en un corte terminado se probaría sobre un archivo que no está"
fi

if [ ! -f "$COLLAPSE_SKILL" ]; then
  bail "[79] falta $COLLAPSE_SKILL; la negativa por una entrega de diseño abierta se probaría sobre un archivo que no está"
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

report

echo "$CHECK_NAME: OK - $COMMAND_FILE nombra la prohibición de aterrizar en un corte con $DONE_STATUS, y el paso 3 de $COLLAPSE_SKILL lee $DELIVERIES_KEY en la tercera de sus negativas, con nueve pasos"
