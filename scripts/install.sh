#!/bin/sh
# Instalador de credenciales de keiron-planner.
#
# POSIX sh a propósito: corre en la máquina de PM y de Diseño, donde el shell de login
# no es bash. El único juez honesto de esa portabilidad es dash, porque en macOS
# /bin/sh es bash 3.2 en modo posix y traga pipefail, arrays y los dobles corchetes.
#
# Nunca imprime la key, ni entera ni en fragmentos.

set -eu

KEY_FILE="${XDG_CONFIG_HOME:-$HOME/.config}/keiron-planner/linear.key"
ENDPOINT="https://api.linear.app/graphql"

die() { printf '%s\n' "$1" >&2; exit 1; }

# Lo llaman las dos rutas que validan. Sin esta guarda, la ausencia de curl llega como
# rc 2 y el mensaje de ese código culpa a la red de algo que es una herramienta que falta.
need_curl() { command -v curl >/dev/null 2>&1 || die "Falta curl."; }

# Valida una key contra la API.
#   0  sirve. Escribe "Nombre - workspace X (slug)" en stdout.
#   1  la API la rechazó.
#   2  el script no pudo decidir: red caída, respuesta rara, falta una
#      herramienta. Este caso nunca se reporta como key inválida.
validate() {
  # El trim es una condición de la línea de abajo: la key viaja en un config de curl que
  # es una sola línea, y un espacio o un salto adentro la partiría en dos dejando un
  # pedazo de la key en la posición del nombre de opción, que es la única parte del
  # config que curl nombra cuando no la reconoce. El valor entra por heredoc, que no
  # aparece en la línea de comando de ningún proceso.
  _linear_key=$(tr -d '[:space:]' <<KEY
$1
KEY
)

  # La key va por el config que curl lee de stdin y no por -H: en argv la levanta
  # cualquier agente de EDR o MDM que registre la línea de comando de cada exec, y una
  # Personal API key de Linear no tiene alcance ni vencimiento, así que nadie se entera
  # de que hay que revocarla.
  #
  # Sin -f ni --fail, y la ausencia del flag es la decisión: una key rechazada devuelve
  # 401 con JSON válido, y curl -sS sin -f sale 0 y deja ese JSON en stdout, así que el
  # python lo lee y devuelve 1. Con -f, curl sale no cero y descarta el body: se dispara
  # el return 2 y quien tiene una key mala lee "el problema no es tu credencial".
  #
  # El stderr de curl no se captura y va derecho al del script, que es lo que prometen
  # los mensajes del rc 2 cuando dicen que el detalle está arriba. Adentro de la
  # sustitución quedaba atrapado en $_resp y el return 2 lo tiraba, y de paso ensuciaba
  # el JSON que lee el python.
  _resp=$(curl -sS --config - --max-time 20 -X POST "$ENDPOINT" \
    -H 'Content-Type: application/json' \
    -d '{"query":"{ viewer { name } organization { name urlKey } }"}' <<CONFIG
header = "Authorization: $_linear_key"
CONFIG
) || return 2

  printf '%s' "$_resp" | python3 -c '
import json, sys

raw = sys.stdin.read()
try:
    d = json.loads(raw)
except Exception:
    sys.stderr.write("La respuesta de la API no es JSON. Primeros 300 bytes:\n")
    sys.stderr.write(raw[:300] + "\n")
    sys.exit(2)

if d.get("errors"):
    msgs = [e.get("message", "sin mensaje") for e in d["errors"]]
    sys.stderr.write("La API respondió con errores: " + "; ".join(msgs)[:300] + "\n")
    sys.exit(1)

viewer = (d.get("data") or {}).get("viewer")
org = (d.get("data") or {}).get("organization") or {}
if not viewer:
    sys.stderr.write("La API no devolvió viewer.\n")
    sys.exit(1)

print(viewer.get("name", "?") + " - workspace " + org.get("name", "?") + " (" + org.get("urlKey", "?") + ")")
'
}

cmd_verify() {
  [ -f "$KEY_FILE" ] || die "No hay key guardada en $KEY_FILE. Ejecuta /planner-setup"
  need_curl
  if _who=$(validate "$(cat "$KEY_FILE")"); then
    printf 'Key válida en %s\n  %s\n' "$KEY_FILE" "$_who"
  else
    _rc=$?
    if [ "$_rc" = 2 ]; then
      die "No pude verificar la key. El problema es del script o de la red, no de la credencial. El detalle está arriba."
    fi
    die "La key en $KEY_FILE no sirve. Ejecuta /planner-setup de nuevo con una key nueva."
  fi
}

cmd_remove() {
  if [ ! -f "$KEY_FILE" ]; then
    printf 'No había key en %s\n' "$KEY_FILE"
    exit 0
  fi
  rm -f "$KEY_FILE"
  printf 'Key borrada de %s\n' "$KEY_FILE"
  printf 'Revócala también en Linear: Settings -> Security & access -> Personal API keys\n'
}

cmd_install() {
  need_curl

  # Se ejecuta python3 -V en vez de resolver la ruta del ejecutable: en macOS
  # /usr/bin/python3 existe como stub aunque las Command Line Tools no estén instaladas,
  # así que la presencia del ejecutable pasa el chequeo y el intérprete falla después. Un
  # solo case decide los dos fracasos, el ejecutable ausente y el stub que no reporta
  # versión.
  _pyv=$(python3 -V 2>&1) || true
  case "$_pyv" in
    "Python 3."*) : ;;
    *) die "No hay un python3 que funcione: python3 -V dijo \"$_pyv\".

En macOS /usr/bin/python3 existe aunque las Command Line Tools no estén instaladas, y
ahí es donde falla. Instálalas con:

  xcode-select --install

No guardé nada." ;;
  esac

  # Sin terminal no hay forma de apagar el eco, y una key tipeada con eco queda en el
  # scrollback y en cualquier transcript que esté grabando. La guarda va antes de la
  # primera pregunta y no antes de la última: sin TTY, un read choca con EOF y bajo
  # set -e mata el script en el acto, dejando el prompt colgado sin explicación y sin
  # decir que no hay TTY, que es la condición de la que depende quien lo invoca.
  if [ ! -t 0 ]; then
    die "Necesito una terminal de verdad para pedir la key sin mostrarla.

Este script se está ejecutando sin TTY, por ejemplo desde un pipe, un hook o un
agente. Abre una terminal y ejecuta /planner-setup ahí.

No guardé nada."
  fi

  if [ -f "$KEY_FILE" ] && _who=$(validate "$(cat "$KEY_FILE")" 2>/dev/null); then
    printf 'Ya hay una key válida en %s\n  %s\n\n' "$KEY_FILE" "$_who"
    printf '¿Quieres reemplazarla? [s/N] '
    read -r _ans
    case "$_ans" in
      s|S|si|Si|SI|y|Y|yes) : ;;
      *) printf 'Sin cambios.\n'; exit 0 ;;
    esac
  fi

  cat <<'HELP'

Necesito una Personal API key de Linear.

  1. Abre Linear y ve a Settings -> Security & access
  2. En "Personal API keys", toca "New API key"
  3. Ponle un nombre que se entienda, por ejemplo "keiron-planner"
  4. Cópiala. Linear la muestra una sola vez.

La key queda solo en tu máquina, en un archivo que solo tú puedes leer.
No se sube a ningún repo y no se comparte con nadie.

HELP

  printf 'Pega la key y presiona Enter. No se va a ver mientras escribes: '
  _stty_saved=$(stty -g)
  trap 'stty "$_stty_saved" 2>/dev/null || true' EXIT INT TERM
  stty -echo
  IFS= read -r _linear_key
  stty "$_stty_saved"
  trap - EXIT INT TERM
  printf '\n'

  # Quitar espacios de los costados, que es el error más común al pegar.
  _linear_key=$(printf '%s' "$_linear_key" | tr -d '[:space:]')
  [ -n "$_linear_key" ] || die "No pegaste nada."

  printf 'Validando contra Linear...\n'
  if _who=$(validate "$_linear_key"); then
    printf 'La key sirve.\n  %s\n' "$_who"
  else
    _rc=$?
    if [ "$_rc" = 2 ]; then
      die "No pude validar la key, y el problema no es la credencial.

Se cayó el script o la red. El detalle está arriba de este mensaje.
No guardé nada. La key que pegaste puede estar perfecta."
    fi
    die "La API rechazó la key.

Casi siempre es una de estas tres:
  - la copiaste incompleta
  - la key es de otro workspace
  - la revocaste y Linear ya no la conoce

No guardé nada. Genera una nueva y ejecuta /planner-setup otra vez."
  fi

  mkdir -p "${KEY_FILE%/*}"
  chmod 700 "${KEY_FILE%/*}"
  # umask antes de crear, para que el archivo nunca exista con permisos abiertos ni por
  # un instante. Es más fuerte que el chmod 600 posterior, que se queda de todos modos
  # para el caso del archivo que ya existía.
  _umask_saved=$(umask)
  umask 077
  printf '%s\n' "$_linear_key" > "$KEY_FILE"
  umask "$_umask_saved"
  chmod 600 "$KEY_FILE"

  printf '\nGuardada en %s con permisos %s\n' "$KEY_FILE" "$(ls -l "$KEY_FILE" | cut -c1-10)"
  printf 'Para revisarla en cualquier momento: /planner-setup --verify\n'
}

case "${1:-}" in
  --verify) cmd_verify ;;
  --remove) cmd_remove ;;
  "")       cmd_install ;;
  *)        die "Uso: /planner-setup [--verify|--remove]" ;;
esac
