#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

. scripts/_common.sh

# Afirmaciones 14, 15, 17, 18, 20, 21, 56, 57 y 71.

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

instalador=scripts/install.sh

if [ ! -f "$instalador" ]; then
  bail "[17] falta $instalador; las afirmaciones sobre el instalador quedan sin correr"
fi

readme=README.md

if [ ! -f "$readme" ]; then
  bail "[20] falta $readme; no hay dónde buscar el snippet de instalación"
fi

if ! command -v dash > /dev/null 2>&1; then
  bail "[56] dash no está en el PATH; en macOS /bin/sh es bash 3.2 en modo posix, así que no hay otro juez de portabilidad POSIX"
fi

# Un solo trap EXIT en todo el archivo: registrar un segundo lo REEMPLAZA en vez de
# sumarlo, y el temporal del primero quedaría sin borrar en cada corrida. Medido bajo
# bash 3.2. Las dos variables arrancan vacías porque el trap se registra antes de que
# exista cualquiera de los dos directorios, y cada temporal lleva su propio template
# para que un directorio que sobreviva nombre qué fugó.
aislado=""
hogar=""
tricotomia=""
sintty=""
limpiar() {
  if [ -n "$aislado" ]; then rm -rf "$aislado"; fi
  if [ -n "$hogar" ]; then rm -rf "$hogar"; fi
  if [ -n "$tricotomia" ]; then rm -rf "$tricotomia"; fi
  if [ -n "$sintty" ]; then rm -rf "$sintty"; fi
}
trap limpiar EXIT

# --- afirmación 14: el manifiesto pasa el CLI y declara author ---

# El validador camina la raíz del plugin entera, y CLAUDE.md ahí adentro le arranca un
# warning que bajo --strict es un error. Medido: no depende del argumento, no hay flag
# que lo silencie, y lo dispara solo CLAUDE.md. Por eso la validación corre sobre una
# copia aislada del manifiesto: conserva --strict y sigue distinguiendo un campo
# desconocido. Lo que deja de mirar es el plugin tal como se despacha.
if ! aislado="$(mktemp -d "${TMPDIR:-/tmp}/kp-manifest.XXXXXX")"; then
  bail "[14] no se pudo crear el directorio temporal donde validar el manifiesto aislado"
fi
mkdir -p "$aislado/.claude-plugin"
cp "$MANIFEST" "$aislado/.claude-plugin/"

# Medido: toda la salida va por stdout y stderr queda vacío, en el caso OK y en el FAIL.
# Por eso se captura con 2>&1 y se decide por el código de salida, nunca por el texto.
if ! validacion="$(claude plugin validate --strict "$aislado" 2>&1)"; then
  fail "[14] claude plugin validate --strict no salió 0: $(printf '%s\n' "$validacion" | tail -1)"
fi

# Un solo arranque de intérprete, que imprime hechos normalizados. Los [N] se quedan en
# bash, donde la extracción estática los puede leer. Y la ruta entra por el entorno y no
# por argv: indexar argv dejaría en el archivo un corchete con un dígito adentro, que esa
# extracción no distingue de un número de afirmación.
hechos="$(KP_MANIFEST="$MANIFEST" python3 - <<'PY' || true
import json, os, sys


# El protocolo es una línea por hecho, y bash lo lee con un grep anclado que se
# queda con la primera coincidencia. Un valor con un salto de línea adentro
# inyectaría hechos que ganan por llegar antes, y una aserción saldría verde contra
# un dato fabricado. Se neutraliza acá, en el único lugar que escribe el protocolo,
# así que un hecho nuevo queda cubierto sin acordarse de nada.
def hecho(clave, valor):
    print("%s=%s" % (clave, str(valor).replace("\r", " ").replace("\n", " ")))


try:
    m = json.load(open(os.environ["KP_MANIFEST"], encoding="utf-8"))
except Exception as e:
    hecho("parse_error", e)
    sys.exit(0)
a = m.get("author")
if isinstance(a, dict):
    hecho("author_name", a.get("name") or "")
elif isinstance(a, str):
    hecho("author_name", a)
else:
    hecho("author_name", "")
d = m.get("dependencies")
if isinstance(d, list):
    hecho("deps_len", len(d))
    for i, x in enumerate(d):
        hecho("deps_%d_type" % i, type(x).__name__)
        hecho("deps_%d_value" % i, x if isinstance(x, str) else "")
else:
    hecho("deps_len", -1)
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

# --- afirmación 20: el README tiene el snippet de instalación y nombra el setup ---

if ! grep -qF '/plugin install keiron-planner@spec-driven-dev' "$readme"; then
  fail "[20] $readme no tiene el snippet /plugin install keiron-planner@spec-driven-dev"
fi

if ! grep -qF '/planner-setup' "$readme"; then
  fail "[20] $readme no nombra /planner-setup, que es lo que la persona corre después de instalar"
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

# --- afirmación 17: el chequeo del intérprete distingue el stub de macOS ---

if ! grep -q 'python3 -V' "$instalador"; then
  fail "[17] $instalador no chequea el intérprete con python3 -V"
fi

if ! grep -q 'xcode-select --install' "$instalador"; then
  fail "[17] $instalador no nombra xcode-select --install en el mensaje del intérprete que falta"
fi

# En macOS /usr/bin/python3 existe como stub aunque las Command Line Tools no estén
# instaladas, así que la presencia del ejecutable pasa y el intérprete falla después.
# La grep corre contra el instalador y no contra este archivo, que nombra el literal en
# su patrón y en su mensaje. Y por ser de ausencia, el literal queda prohibido en todo
# el instalador, comentarios incluidos: uno que lo nombre lo pone en rojo solo.
if grep -q 'command -v python3' "$instalador"; then
  fail "[17] $instalador chequea el intérprete con command -v python3, que pasa sobre el stub de macOS"
fi

# --- afirmación 18: la key no se imprime, y su ruta está entera en una línea ---

if [ "$(grep -cF '${XDG_CONFIG_HOME:-$HOME/.config}/keiron-planner/linear.key' "$instalador" || true)" != "1" ]; then
  fail "[18] $instalador no escribe la ruta de la key entera y una sola vez en una línea"
fi

# Conteo exacto y no lista blanca por forma: cada exclusión por forma es un agujero
# futuro, y "redirigido a archivo" no distingue > "$KEY_FILE" de > /tmp/debug. Así el
# check se pone rojo cuando alguien AGREGA un uso, en vez de pasar en verde cuando
# alguien agrega un echo. Cuenta OCURRENCIAS y no líneas, y las dos razones están
# medidas: un uso pegado a una línea que ya cuenta no agrega ninguna línea y se
# escaparía, y un reformateo que parta una línea agrega una sin agregar ningún uso y
# daría rojo falso. La línea del trim ya lleva dos ocurrencias, así que el número de acá
# no es la cantidad de líneas, y es el único lugar donde vive.
ocurrencias_esperadas=8
ocurrencias="$(grep -o '_linear_key' "$instalador" | grep -c . || true)"
if [ "$ocurrencias" != "$ocurrencias_esperadas" ]; then
  fail "[18] la variable de la key aparece $ocurrencias veces en $instalador y tiene que aparecer $ocurrencias_esperadas veces; si el cambio es legítimo, este número se actualiza acá y en ningún otro lado"
fi

# --- afirmación 56: install.sh corre bajo dash ---

# Las tres partes de abajo cazan cosas distintas y ninguna contiene a las otras. Medido:
# un error de sintaxis después del case lo caza solo dash -n, porque la ejecución nunca
# llega; set -o pipefail arriba lo caza el código de salida; y unos dobles corchetes en
# la ruta de --verify NO cambian el código de salida, que sigue siendo 1, así que la
# única señal es el diagnóstico que dash escribe en stderr.
if ! parseo="$(dash -n "$instalador" 2>&1)"; then
  fail "[56] dash -n rechazó $instalador: $(printf '%s\n' "$parseo" | tail -1)"
fi

# HOME y XDG_CONFIG_HOME se SETEAN a un temporal y nunca se desasignan. Sin aislar,
# --verify encuentra la key real de la máquina y hace una llamada de red a Linear, así
# que la afirmación pasaría a depender de la red. Y desasignándolas, la expansión de la
# ruta de la key aborta bajo set -u con código 2 y no 1.
if ! hogar="$(mktemp -d "${TMPDIR:-/tmp}/kp-home.XXXXXX")"; then
  bail "[56] no se pudo crear el directorio temporal que aísla HOME"
fi

# El código esperado es por modo y es exacto. Aceptar "no cero" dejaría pasar en verde
# justo la familia de fallas que esta afirmación busca: dash rechazando el archivo sale
# 2, un array sale 2, los paréntesis dobles salen 127, y las dos variables desasignadas
# salen 2. Y el diagnóstico no se puede pedir como "stderr vacío": die escribe por
# stderr, así que --verify sin key siempre deja texto ahí. Se busca la forma con que dash
# prefija sus diagnósticos, que ningún mensaje del instalador contiene.
for caso in "--verify:1" "--nope:1" "--remove:0"; do
  modo="${caso%%:*}"
  esperado="${caso##*:}"
  rc=0
  err="$(HOME="$hogar" XDG_CONFIG_HOME="$hogar/.config" \
    dash "$instalador" "$modo" 2>&1 >/dev/null)" || rc=$?
  if [ "$rc" -ne "$esperado" ]; then
    fail "[56] dash $instalador $modo salió $rc y tiene que salir $esperado"
  fi
  diagnostico="$(printf '%s\n' "$err" | grep -E "^$instalador: [0-9]+: " || true)"
  if [ -n "$diagnostico" ]; then
    fail "[56] dash diagnosticó $instalador en el modo $modo: $(printf '%s\n' "$diagnostico" | head -1)"
  fi
done

# --- afirmación 57: validate distingue sus tres desenlaces ---

# Los tres modos de la afirmación 56 no llegan nunca a validate, así que el contrato que
# decide qué mensaje lee la persona no lo ejercita nada. Se cierra con un curl falso al
# frente del PATH y una key plantada: las asignaciones de prefijo suman al entorno en vez
# de reemplazarlo, e install.sh invoca curl sin cualificar y sin hash, así que el
# subproceso levanta el falso. Queda offline y determinista.
#
# El precio es este stub, que es superficie que alguien mantiene. Por eso vive acá y no en
# un archivo aparte, y responde por caso en vez de imitar a curl. Lo que sí modela es lo que
# cambia el resultado: el config que recibe por stdin, y la bandera de fallo duro.
#
# Con fallo duro, curl sale 22 sobre el 401 y descarta el body, así que la rama de rechazo
# se convierte en un desenlace 2 y quien tiene una key mala lee que el problema no es su
# credencial. Se reconoce también agrupada, porque curl acepta opciones cortas juntas y
# -sSf es la forma más común de agregarla sobre una invocación que ya es -sS.
if ! tricotomia="$(mktemp -d "${TMPDIR:-/tmp}/kp-tri.XXXXXX")"; then
  bail "[57] no se pudo crear el directorio temporal donde ejercitar el contrato de validate"
fi
mkdir -p "$tricotomia/bin" "$tricotomia/.config/keiron-planner"
printf 'no-es-una-key-real\n' > "$tricotomia/.config/keiron-planner/linear.key"

cat > "$tricotomia/bin/curl" <<'CURL'
#!/bin/sh
cat > "$KP_CONFIG_VISTO"
duro=""
for a in "$@"; do
  case "$a" in
    --fail|--fail-with-body) duro=1 ;;
    --*) ;;
    -*f*) duro=1 ;;
  esac
done
case "${KP_CASO:-}" in
  valida)    printf '%s' '{"data":{"viewer":{"name":"Sonda"},"organization":{"name":"Keiron","urlKey":"keiron"}}}' ;;
  rechazada) if [ -n "$duro" ]; then exit 22; fi
             printf '%s' '{"errors":[{"message":"Authentication required, not authenticated"}]}' ;;
  caida)     printf 'curl: (6) Could not resolve host: api.linear.app\n' >&2; exit 6 ;;
esac
CURL
chmod +x "$tricotomia/bin/curl"

# La marca es lo que discrimina, y no el código: rechazada y caída salen las dos 1, porque
# die sale 1 siempre. Que un desenlace 2 nunca se reporte como key inválida es la cláusula
# del contrato, y la única forma de verla es el texto que la persona lee.
for caso in "valida:0:Key válida en" "rechazada:1:no sirve" "caida:1:no de la credencial"; do
  modo="${caso%%:*}"
  resto="${caso#*:}"
  esperado="${resto%%:*}"
  marca="${resto#*:}"
  rc=0
  dicho="$(KP_CASO="$modo" KP_CONFIG_VISTO="$tricotomia/visto" \
    PATH="$tricotomia/bin:$PATH" HOME="$tricotomia" \
    XDG_CONFIG_HOME="$tricotomia/.config" dash "$instalador" --verify 2>&1)" || rc=$?
  if [ "$rc" -ne "$esperado" ]; then
    fail "[57] con la respuesta $modo, $instalador --verify salió $rc y tiene que salir $esperado"
  fi
  if ! printf '%s\n' "$dicho" | grep -qF "$marca"; then
    fail "[57] con la respuesta $modo, el mensaje de $instalador no dice \"$marca\": $(printf '%s\n' "$dicho" | tail -1)"
  fi
done

# El config por stdin es lo que hoy transporta la credencial, y una sola comparación
# establece las tres cosas que lo hacen seguro: que es una línea sola, que el token de
# opción es la constante, y que la key llega entera. Si se partiera, curl leería un pedazo
# de la credencial como nombre de opción, que es la única parte del config que nombra
# cuando no la reconoce.
if [ "$(cat "$tricotomia/visto" 2>/dev/null || true)" != 'header = "Authorization: no-es-una-key-real"' ]; then
  fail "[57] el config que $instalador le pasa a curl no es la línea que declara: $(cat "$tricotomia/visto" 2>/dev/null | tr '\n' ' ' || true)"
fi

# Cuarto caso, y va afuera del bucle porque no perturba la respuesta sino el intérprete.
# El falso modela el stub de macOS: existe, no reporta versión y falla. Sin la guarda, el
# pipe de validate sale 127, que no es ninguno de los tres desenlaces, y el mensaje culpa a
# la credencial. El bin del curl falso queda igual adelante, así que el caso sigue offline
# aunque alguien mueva la guarda después de la validación.
mkdir -p "$tricotomia/sin-python3"
cat > "$tricotomia/sin-python3/python3" <<'PY3'
#!/bin/sh
echo "xcrun: error: invalid active developer path" >&2
exit 1
PY3
chmod +x "$tricotomia/sin-python3/python3"
rc=0
dicho="$(KP_CASO=valida KP_CONFIG_VISTO="$tricotomia/visto" \
  PATH="$tricotomia/sin-python3:$tricotomia/bin:$PATH" HOME="$tricotomia" \
  XDG_CONFIG_HOME="$tricotomia/.config" dash "$instalador" --verify 2>&1)" || rc=$?
if [ "$rc" -ne 1 ]; then
  fail "[57] sin un python3 que funcione, $instalador --verify salió $rc y tiene que salir 1"
fi
if ! printf '%s\n' "$dicho" | grep -qF 'No hay un python3 que funcione'; then
  fail "[57] sin un python3 que funcione, $instalador --verify culpa a la credencial: $(printf '%s\n' "$dicho" | tail -1)"
fi

# --- afirmación 71: sin TTY, el instalador da un comando que se puede pegar ---

# /planner-setup corre siempre dentro de Claude Code, que nunca le da TTY al script. Un
# mensaje que mande a correr /planner-setup en una terminal no tiene salida, así que lo
# único que sirve es la ruta absoluta del propio script. Se invoca con la ruta relativa
# a propósito: es la forma en que un $0 sin resolver se escaparía al mensaje.
if ! sintty="$(mktemp -d "${TMPDIR:-/tmp}/kp-notty.XXXXXX")"; then
  bail "[71] no se pudo crear el directorio temporal que aísla HOME"
fi
rc=0
dicho="$(HOME="$sintty" XDG_CONFIG_HOME="$sintty/.config" \
  dash "$instalador" < /dev/null 2>&1)" || rc=$?
if [ "$rc" -ne 1 ]; then
  fail "[71] sin TTY, $instalador salió $rc y tiene que salir 1"
fi
comando="sh '$(pwd -P)/$instalador'"
if ! printf '%s\n' "$dicho" | grep -qF "$comando"; then
  fail "[71] sin TTY, el mensaje de $instalador no trae el comando $comando para pegar en una terminal"
fi
if printf '%s\n' "$dicho" | grep -qE 'ejecuta /planner-setup (ahí|en)'; then
  fail "[71] sin TTY, el mensaje de $instalador manda a correr /planner-setup en una terminal, donde no existe"
fi

report

echo "$CHECK_NAME: OK - manifiesto válido con author, dependencies en un string pelado, el README trae el snippet de instalación y nombra /planner-setup, nada trackeado matchea *.key, y el instalador chequea el intérprete, guarda la key en su ruta sin imprimirla, corre bajo dash sin diagnóstico, y su validación manda la credencial en una línea de config, distingue los tres desenlaces, no culpa a la credencial de una herramienta que falta, y sin TTY da la ruta absoluta del script para pegar en una terminal"
