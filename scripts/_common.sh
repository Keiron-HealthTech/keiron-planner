# shellcheck shell=bash
# Contrato compartido por todos los scripts de check. Se sourcea, nunca se ejecuta.
# No lleva shebang y no lleva bit de ejecución a propósito: no está en el namespace
# check-* y no entra al glob de run-checks.sh.
#
# Su gemelo en Python es scripts/_common.py, que nace con check-adapter.py. Las dos
# copias tienen las mismas cuatro funciones y la misma forma de mensaje. Lo que las
# ata es la afirmación 50, que compara los [N] de todos los scripts sin importar el
# lenguaje.

# El piso del dialecto es bash 3.2, que es lo que resuelve env bash en la máquina del
# dev leader. Quedan prohibidos mapfile, readarray, declare -A, ${var^^} y &>>.
#
# Y queda prohibido pinear LC_ALL=C. Sería lo obvio para que el orden del glob fuera
# idéntico en toda máquina, pero rompe el método de la afirmación 6, que es una clase
# de caracteres acentuados: bajo locale C una bracket expression con esos caracteres
# deja de funcionar por bytes. El orden del glob no necesita pinearse, porque los
# nombres de los checks difieren solo en letras ASCII minúsculas y toda collation
# coincide en el orden de esas.
set -euo pipefail

# Las raíces del árbol. Solo lo que existe hoy o nace en esta issue. Cada raíz nueva
# la agrega la issue que crea el directorio.
MANIFEST=.claude-plugin/plugin.json
SCRIPTS=scripts
CHECKS_MD=scripts/CHECKS.md

# El nombre del check sale del archivo que sourcea, no de un literal por script.
# Así el nombre del mensaje no se puede separar del nombre del archivo, y el mapeo de
# [N] a script que la afirmación 50 necesita no puede mentir.
# Depende de que run-checks.sh ejecute cada check como subproceso: si lo sourceara,
# esto diría run-checks.
CHECK_NAME="${0##*/}"
CHECK_NAME="${CHECK_NAME%.sh}"
CHECK_NAME="${CHECK_NAME%.py}"

# Las fallas se acumulan en vez de salir en la primera: una corrida nombra todo lo
# que está roto, que es lo que hace observable una mutación deliberada de una línea
# aunque otra aserción ya esté fallando.
FAILURES=""

# fail "[N] qué está roto y dónde"
# El [N] va embebido en el string, nunca como argumento aparte: es lo que hace que la
# afirmación 50 pueda extraerlo con la misma expresión de un .sh y de un .py.
fail() {
  FAILURES="${FAILURES}${FAILURES:+$'\n'}$1"
}

# report
# Si hay fallas, imprime todas por stderr y sale 1. Si no hay, vuelve y el check
# imprime su propia línea de OK. Nunca se llama adentro de una sustitución de
# comandos ni de un pipe: su exit tiene que ser el del script.
report() {
  if [ -n "$FAILURES" ]; then
    echo "$CHECK_NAME: FAIL - $(printf '%s\n' "$FAILURES" | head -1)" >&2
    printf '%s\n' "$FAILURES" | tail -n +2 | sed 's/^/  also: /' >&2
    exit 1
  fi
}

# bail "[N] falta la fuente"
# El tercer tier. Se llama cuando falta el archivo o la herramienta que el check
# mira, porque veinte fallas derivadas de una fuente ausente son ruido. Sale 1
# siempre: se lo llama justo cuando FAILURES no puede quedar vacío.
bail() {
  fail "$1"
  report
}

# require_nonempty "$extraccion" "[N] la extracción dio vacío"
# La regla anti vacuidad, como helper y no como convención: un check cuya extracción
# da vacío falla, nunca pasa. Es tercer tier, porque una extracción vacía significa
# que la fuente se movió y toda aserción posterior sobre ese conjunto es derivada.
# Cuando una aserción quiera acumular en vez de cortar, no usa este helper: usa la
# forma con fail.
require_nonempty() {
  if [ -z "$1" ]; then
    bail "$2"
  fi
}
