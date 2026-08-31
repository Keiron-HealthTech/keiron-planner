# shellcheck shell=bash
# Contrato compartido por los scripts de check. Se sourcea, nunca se ejecuta: no lleva
# shebang ni bit de ejecución, así que queda fuera del namespace check-* y no entra al
# glob de run-checks.sh. Su gemelo en Python replica estas cuatro funciones y la misma
# forma de mensaje.

# El piso del dialecto es bash 3.2. Quedan prohibidos mapfile, readarray, declare -A,
# ${var^^} y &>>. Y queda prohibido LC_ALL=C: rompe los métodos que son clases de
# caracteres acentuados, porque bajo locale C una bracket expression con esos caracteres
# deja de funcionar por bytes.
set -euo pipefail

# Solo raíces que existen. Una constante que apunta a algo ausente es una fuente que
# ningún check mira, así que la regla anti vacuidad no la protege.
MANIFEST=.claude-plugin/plugin.json
SCRIPTS=scripts
CHECKS_MD=scripts/CHECKS.md

# Derivado del archivo que sourcea, para que el nombre del mensaje no se pueda separar
# del nombre del archivo. Depende de que run-checks.sh ejecute cada check como
# subproceso: si lo sourceara, esto diría run-checks.
CHECK_NAME="${0##*/}"
CHECK_NAME="${CHECK_NAME%.sh}"
CHECK_NAME="${CHECK_NAME%.py}"

# Las fallas se acumulan en vez de salir en la primera, así que una corrida nombra todo
# lo que está roto y no solo lo primero.
FAILURES=""

# El [N] va embebido en el string, nunca como argumento aparte: es lo que permite
# extraerlo con la misma expresión de un .sh y de un .py.
fail() {
  FAILURES="${FAILURES}${FAILURES:+$'\n'}$1"
}

# Nunca se llama adentro de una sustitución de comandos ni de un pipe: su exit tiene que
# ser el del script.
report() {
  if [ -n "$FAILURES" ]; then
    echo "$CHECK_NAME: FAIL - $(printf '%s\n' "$FAILURES" | head -1)" >&2
    printf '%s\n' "$FAILURES" | tail -n +2 | sed 's/^/  also: /' >&2
    exit 1
  fi
}

# El tercer tier: reporta y sale ahí mismo, porque las fallas derivadas de una fuente
# ausente sepultan el mensaje que importa. FAILURES nunca queda vacío acá: se la llama
# justo cuando falta algo.
bail() {
  fail "$1"
  report
}

# La regla anti vacuidad como función y no como convención, para que se pueda chequear
# que todos la usen. Es tercer tier: una extracción vacía significa que la fuente se
# movió, y toda aserción posterior sobre ese conjunto es derivada. Una aserción que
# quiera acumular en vez de cortar usa fail.
require_nonempty() {
  if [ -z "$1" ]; then
    bail "$2"
  fi
}
