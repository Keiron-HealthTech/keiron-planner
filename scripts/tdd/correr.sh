#!/usr/bin/env bash
# El punto de entrada de los andamios de TDD de este directorio. NO es un check del set:
# ni este archivo ni sus vecinos matchean el glob scripts/check-*, que es de un solo
# segmento de ruta, asi que run-checks.sh no los corre y agregar uno aca no toca el
# runner ni el workflow.
#
# Que son: las pruebas que se escribieron en rojo antes del codigo que hoy las pone en
# verde, y que todavia no tienen fila en CHECKS.md. Se conservan para que la cobertura
# no haya que reescribirla si el corte se retoma en otra sesion. La fila 61 promueve el
# andamio de runtime al harness de check-map.sh, y ese es el dia en que estos dos .py
# dejan de hacer falta.
#
# Corre bajo /bin/bash y no bajo zsh ni fish: los dos falsean el resultado, y MULTIOS lo
# hace en silencio.
set -euo pipefail

cd "$(dirname "$0")/../.."

adapter=scripts/linear.py
[ -f "$adapter" ] || { echo "correr: falta $adapter" >&2; exit 1; }

# El mismo intérprete de la cadena de la afirmación 19 que ya usan check-map.sh y
# check-adapter.py: los andamios importan linear.py como módulo y tienen que verlo con
# la misma versión que el set.
py39=""
for cand in "${PY39:-}" python3.9 /usr/bin/python3; do
  [ -n "$cand" ] || continue
  v="$("$cand" -c 'import sys;print("%d.%d" % sys.version_info[:2])' 2>/dev/null || true)"
  if [ "$v" = "3.9" ]; then py39="$cand"; break; fi
done
[ -n "$py39" ] || { echo "correr: no hay ningún intérprete 3.9 en la cadena PY39, python3.9, /usr/bin/python3" >&2; exit 1; }

# Un solo trap EXIT, igual que check-map.sh: un segundo reemplaza al primero bajo bash
# 3.2 y le fuga el temporal en silencio.
hogar=""
limpiar() { [ -n "$hogar" ] && rm -rf "$hogar"; return 0; }
trap limpiar EXIT
hogar="$(mktemp -d "${TMPDIR:-/tmp}/kp-tdd-hogar.XXXXXX")"

fallados=0
correr_py() {
  if ! HOME="$hogar" XDG_CONFIG_HOME="$hogar/config" KP_ADAPTER="$adapter" \
       "$py39" "$1"; then
    fallados=$((fallados + 1))
  fi
}

correr_py scripts/tdd/toma-runtime.py
correr_py scripts/tdd/vertical-map-work.py
correr_py scripts/tdd/resolucion-runtime.py
if ! /bin/bash scripts/tdd/estructura-map-work.sh; then
  fallados=$((fallados + 1))
fi

if [ "$fallados" -ne 0 ]; then
  echo "correr: FAIL - $fallados de 4 andamios fallaron" >&2
  exit 1
fi
echo "correr: OK - los 4 andamios de TDD en verde"
