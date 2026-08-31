#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

. scripts/_common.sh

# Afirmaciones 14, 15 y 21. Las 17, 18 y 20 no nacen acá: hablan de install.sh y de
# README.md, que no existen. Nacen con ellos.

# --- tercer tier: sin fuente y sin herramientas no hay nada que chequear ---

if [ ! -f "$MANIFEST" ]; then
  bail "[14] falta $MANIFEST; no hay manifiesto que validar"
fi

if ! command -v claude > /dev/null 2>&1; then
  bail "[14] claude no está en el PATH; el CLI ausente es un error honesto y no un caso a soportar"
fi

if ! command -v python3 > /dev/null 2>&1; then
  bail "[15] python3 no está en el PATH; no hay con qué leer el manifiesto"
fi

if ! git rev-parse --is-inside-work-tree > /dev/null 2>&1; then
  bail "[21] esto no es un work tree de git; no hay árbol trackeado que revisar"
fi

# --- afirmación 14: el manifiesto pasa el CLI y declara author ---

# El validador camina la raíz del plugin entera, y CLAUDE.md ahí adentro le arranca un
# warning que bajo --strict es un error: el runtime no carga ese archivo como contexto
# del plugin. Medido: el warning no depende del argumento, no hay flag que lo silencie,
# y lo dispara solo CLAUDE.md. Así que la validación corre sobre una copia aislada del
# manifiesto, que es exactamente el sujeto de esta afirmación, y conserva --strict.
# Medido: la copia aislada sale 0 y sigue distinguiendo, un campo desconocido la
# devuelve en 1.
#
# Lo que esta forma deja de mirar es el plugin tal como se despacha. El día que exista
# skills/, validarlo es de otra afirmación y de otro check.
aislado=""
limpiar_aislado() {
  if [ -n "$aislado" ]; then
    rm -rf "$aislado"
  fi
}
trap limpiar_aislado EXIT

if ! aislado="$(mktemp -d "${TMPDIR:-/tmp}/kp-manifest.XXXXXX")"; then
  bail "[14] no se pudo crear el directorio temporal donde validar el manifiesto aislado"
fi
mkdir -p "$aislado/.claude-plugin"
cp "$MANIFEST" "$aislado/.claude-plugin/"

# Medido: la salida va entera por stdout y stderr queda vacío, en el caso OK y en el
# FAIL. Así que se captura con 2>&1 y se decide por el código de salida, nunca por el
# texto. Medido también que sale 0 con HOME vacío y sin credencial, que es lo que hace
# que esta aserción corra igual en CI.
if ! validacion="$(claude plugin validate --strict "$aislado" 2>&1)"; then
  fail "[14] claude plugin validate --strict no salió 0: $(printf '%s\n' "$validacion" | tail -1)"
fi

# Un solo arranque de intérprete que imprime hechos normalizados. Los [N] se quedan en
# bash, donde la afirmación 50 los puede leer.
#
# La ruta entra por el entorno y no como argumento posicional. Indexar argv dejaría un
# corchete con el dígito uno adentro, y la afirmación 50 extrae los [N] con una
# expresión que no distingue un índice de Python de un número de afirmación. La
# afirmación 1 existe, así que eso no fallaría por contabilidad: mapearía la afirmación
# 1 a este script en silencio.
hechos="$(KP_MANIFEST="$MANIFEST" python3 - <<'PY' || true
import json, os, sys
try:
    m = json.load(open(os.environ["KP_MANIFEST"], encoding="utf-8"))
except Exception as e:
    print("parse_error=%s" % e)
    sys.exit(0)
a = m.get("author")
if isinstance(a, dict):
    print("author_name=%s" % (a.get("name") or ""))
elif isinstance(a, str):
    print("author_name=%s" % a)
else:
    print("author_name=")
d = m.get("dependencies")
if isinstance(d, list):
    print("deps_len=%d" % len(d))
    for i, x in enumerate(d):
        print("deps_%d_type=%s" % (i, type(x).__name__))
        print("deps_%d_value=%s" % (i, x if isinstance(x, str) else ""))
else:
    print("deps_len=-1")
PY
)"
require_nonempty "$hechos" "[14] la lectura de $MANIFEST con python3 no devolvió ningún hecho; el lector se rompió"

dato() { # clave
  printf '%s\n' "$hechos" | grep "^$1=" | head -1 | sed "s/^$1=//" || true
}

if [ -n "$(dato parse_error)" ]; then
  bail "[14] $MANIFEST no parsea como JSON: $(dato parse_error)"
fi

if [ -z "$(dato author_name)" ]; then
  fail "[14] $MANIFEST no declara author con un name no vacío"
fi

# --- afirmación 15: dependencies con exactamente un elemento, string pelado ---
# El uno y el literal spec-driven-dev se hardcodean sin culpa: es la única copia, y la
# primera vive en código y no en una tabla.

if [ "$(dato deps_len)" != "1" ]; then
  fail "[15] $MANIFEST declara dependencies con largo $(dato deps_len); tiene que ser exactamente uno"
else
  if [ "$(dato deps_0_type)" != "str" ]; then
    fail "[15] el único elemento de dependencies es $(dato deps_0_type) y tiene que ser string pelado, sin constraint de versión"
  fi
  if [ "$(dato deps_0_value)" != "spec-driven-dev" ]; then
    fail "[15] el único elemento de dependencies es '$(dato deps_0_value)' y tiene que ser 'spec-driven-dev'"
  fi
fi

# --- afirmación 21: ninguna key trackeada, y .gitignore la cubre ---
# Sobre todo lo trackeado, vendor/ y .scratch/ incluidos.

keys="$(git ls-files '*.key' || true)"
if [ -n "$keys" ]; then
  fail "[21] hay archivos *.key trackeados: $(printf '%s\n' "$keys" | tr '\n' ' ')"
fi

# La ruta de prueba no necesita existir: git check-ignore resuelve el patrón.
if ! git check-ignore -q sonda-de-prueba.key; then
  fail "[21] .gitignore no cubre *.key"
fi

report

echo "$CHECK_NAME: OK - manifiesto válido con author, dependencies en un string pelado, y nada trackeado matchea *.key"
