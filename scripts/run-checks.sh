#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

# La lista de checks es este glob y nada más. No hay lista escrita, no hay exclusión,
# no hay guarda y no hay $0: los dos archivos que no chequean nada, _common.sh y este
# mismo, están fuera del namespace check-* por nombre. Agregar un check no toca este
# archivo ni el YAML del workflow.
shopt -s nullglob
checks=(scripts/check-*)
shopt -u nullglob

# Anti vacuidad del runner: cero checks no es verde. La guarda va antes del for porque
# bajo set -u expandir un array vacío es un error en bash 3.2.
if [ "${#checks[@]}" -eq 0 ]; then
  echo "run-checks: FAIL - el glob scripts/check-* no matcheó ningún archivo" >&2
  exit 1
fi

fallados=0
for check in "${checks[@]}"; do
  if [ ! -x "$check" ]; then
    echo "run-checks: FAIL - $check no tiene permiso de ejecución" >&2
    fallados=$((fallados + 1))
    continue
  fi
  # Subproceso, nunca source. Si se sourceara, CHECK_NAME se derivaría del $0 de este
  # archivo, todos los mensajes dirían run-checks, y el mapeo de [N] a script que la
  # afirmación 50 necesita quedaría sin sentido.
  if ! "./$check"; then
    fallados=$((fallados + 1))
  fi
done

if [ "$fallados" -ne 0 ]; then
  echo "run-checks: FAIL - $fallados de ${#checks[@]} checks fallaron" >&2
  exit 1
fi

echo "run-checks: OK - ${#checks[@]} checks en verde: ${checks[*]}"
