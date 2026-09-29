#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

. scripts/_common.sh

# Afirmación 55.

COMMAND_FILE=commands/map-work.md

# Las dos literales salen de la misma oración. Con la primera sola, un archivo que
# nombrara el estado en cualquier otro contexto pasaría en verde sin prohibir nada.
DONE_STATUS='status: done'
PROHIBITION='never hangs work off a milestone already marked'

# --- tercer tier: un grep sobre un archivo que falta no mira nada ---

if [ ! -f "$COMMAND_FILE" ]; then
  bail "[55] falta $COMMAND_FILE; la prohibición de aterrizar en un corte terminado se probaría sobre un archivo que no está"
fi

# --- afirmación 55: el comando nombra la prohibición de aterrizar en un corte terminado ---

# Dos fails y no un bail: una corrida tiene que poder nombrar las dos faltas.
if ! grep -qF "$DONE_STATUS" "$COMMAND_FILE"; then
  fail "[55] $COMMAND_FILE no nombra el $DONE_STATUS de un corte terminado, así que no dice sobre cuál no se aterriza"
fi

if ! grep -qF "$PROHIBITION" "$COMMAND_FILE"; then
  fail "[55] $COMMAND_FILE nombra el estado pero no la prohibición; sin ella la frase describe un corte y no prohíbe nada"
fi

report

echo "$CHECK_NAME: OK - $COMMAND_FILE nombra la prohibición de aterrizar en un corte con $DONE_STATUS"
