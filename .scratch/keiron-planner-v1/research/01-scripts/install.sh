#!/bin/sh
# Instalador de credenciales de keiron-planner.
#
# POSIX sh a propósito: tiene que correr igual en fish, zsh y bash, porque no lo
# ejecuta solo un dev. Pide la API key de Linear, la valida contra la API antes
# de guardarla, y la deja en un archivo con permisos 0600 fuera de todo repo.
#
# Uso:
#   ./install.sh            interactivo: pide la key, la valida y la guarda
#   ./install.sh --verify   no pide nada: dice si la key guardada sirve
#   ./install.sh --remove   borra la key guardada
#
# Nunca imprime la key, ni entera ni en fragmentos.

set -eu

CONFIG_DIR="${XDG_CONFIG_HOME:-$HOME/.config}/keiron-planner"
KEY_FILE="$CONFIG_DIR/linear.key"
ENDPOINT="https://api.linear.app/graphql"

die() { printf '%s\n' "$1" >&2; exit 1; }

# Valida una key contra la API.
#   0  sirve. Escribe "Nombre - workspace X (slug)" en stdout.
#   1  la API la rechazó.
#   2  el script no pudo decidir: red caída, respuesta rara, falta una
#      herramienta. Este caso nunca se reporta como key inválida.
validate() {
  _key="$1"
  _resp=$(curl -sS --max-time 20 -X POST "$ENDPOINT" \
    -H 'Content-Type: application/json' \
    -H "Authorization: $_key" \
    -d '{"query":"{ viewer { name } organization { name urlKey } }"}' 2>&1) || return 2

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
  [ -f "$KEY_FILE" ] || die "No hay key guardada en $KEY_FILE. Ejecuta ./install.sh"
  if _who=$(validate "$(cat "$KEY_FILE")"); then
    printf 'Key válida en %s\n  %s\n' "$KEY_FILE" "$_who"
  else
    _rc=$?
    if [ "$_rc" = 2 ]; then
      die "No pude verificar la key. El problema es del script o de la red, no de la credencial. El detalle está arriba."
    fi
    die "La key en $KEY_FILE no sirve. Ejecuta ./install.sh de nuevo con una key nueva."
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
  command -v curl >/dev/null 2>&1 || die "Falta curl."
  command -v python3 >/dev/null 2>&1 || die "Falta python3."

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

  # Sin terminal no hay forma de apagar el eco, y una key tipeada con eco queda
  # en el scrollback y en cualquier transcript que esté grabando.
  if [ ! -t 0 ]; then
    die "Necesito una terminal de verdad para pedir la key sin mostrarla.

Este script se está ejecutando sin TTY, por ejemplo desde un pipe, un hook o un
agente. Abre una terminal y ejecútalo ahí:

  $0

No guardé nada."
  fi

  printf 'Pega la key y presiona Enter. No se va a ver mientras escribes: '
  _stty_saved=$(stty -g)
  trap 'stty "$_stty_saved" 2>/dev/null || true' EXIT INT TERM
  stty -echo
  IFS= read -r _key
  stty "$_stty_saved"
  trap - EXIT INT TERM
  printf '\n'

  # Quitar espacios de los costados, que es el error más común al pegar.
  _key=$(printf '%s' "$_key" | tr -d '[:space:]')
  [ -n "$_key" ] || die "No pegaste nada."

  printf 'Validando contra Linear...\n'
  if _who=$(validate "$_key"); then
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

No guardé nada. Genera una nueva y ejecuta ./install.sh otra vez."
  fi

  mkdir -p "$CONFIG_DIR"
  chmod 700 "$CONFIG_DIR"
  # umask antes de crear, para que el archivo nunca exista con permisos abiertos
  # ni por un instante.
  _umask_saved=$(umask)
  umask 077
  printf '%s\n' "$_key" > "$KEY_FILE"
  umask "$_umask_saved"
  chmod 600 "$KEY_FILE"

  printf '\nGuardada en %s con permisos %s\n' "$KEY_FILE" "$(ls -l "$KEY_FILE" | cut -c1-10)"
  printf 'Para revisarla en cualquier momento: ./install.sh --verify\n'
}

case "${1:-}" in
  --verify) cmd_verify ;;
  --remove) cmd_remove ;;
  "")       cmd_install ;;
  *)        die "Uso: ./install.sh [--verify|--remove]" ;;
esac
