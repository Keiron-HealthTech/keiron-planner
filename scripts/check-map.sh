#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

. scripts/_common.sh

# Afirmación 60.

adapter=scripts/linear.py

# Un solo trap EXIT en todo el archivo: un segundo reemplaza al primero bajo bash 3.2
# y le fuga el temporal en silencio, con el check en verde. Cada temporal lleva su
# propia variable inicializada en vacío antes del trap y su propio template, así que un
# directorio que sobreviva nombra cuál fugó.
hogar=""
limpiar() { [ -n "$hogar" ] && rm -rf "$hogar"; return 0; }
trap limpiar EXIT

# --- tercer tier: sin fuente y sin intérprete no hay nada que ejecutar ---

[ -f "$adapter" ] || bail "[60] falta $adapter; los desenlaces de runtime de las operaciones que escriben quedan sin correr"

py39=""
for cand in "${PY39:-}" python3.9 /usr/bin/python3; do
  [ -n "$cand" ] || continue
  v="$("$cand" -c 'import sys;print("%d.%d" % sys.version_info[:2])' 2>/dev/null || true)"
  if [ "$v" = "3.9" ]; then py39="$cand"; break; fi
done
require_nonempty "$py39" "[60] no hay ningún intérprete 3.9 en la cadena PY39, python3.9, /usr/bin/python3"

hogar="$(mktemp -d "${TMPDIR:-/tmp}/kp-map-hogar.XXXXXX")" || bail "[60] no se pudo crear el directorio temporal del hogar aislado"

# --- afirmación 60 --------------------------------------------------------------
# El seam es urllib.request.urlopen y NUNCA _post. Un harness que reasigne _post
# bypasea justamente el endurecimiento del transporte que estos casos ejercitan, que
# es la diferencia entre este script y check-py39.sh.

salida="$(HOME="$hogar" XDG_CONFIG_HOME="$hogar/config" KP_ADAPTER="$adapter" "$py39" - <<'PY' 2>&1 || true
import contextlib, importlib.util, io, json, os, sys, urllib.error

sys.dont_write_bytecode = True

spec = importlib.util.spec_from_file_location("linear", os.environ["KP_ADAPTER"])
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

# La credencial se planta adentro del hogar aislado y se lee por la misma ruta que
# resuelve el adapter: sin aislar, el harness encontraría la key real de la máquina.
RUTA = os.path.join(os.environ["XDG_CONFIG_HOME"], "keiron-planner", "linear.key")
os.makedirs(os.path.dirname(RUTA), exist_ok=True)
with open(RUTA, "w") as fh:
    fh.write("lin_api_falsa\n")


def plano(texto):
    """Neutraliza los saltos en el EMISOR y no en cada aserción del consumidor: una
    línea del protocolo que se parte en dos deja a bash leyendo media línea."""
    return str(texto).replace("\r", " ").replace("\n", " ")


class Respuesta(object):
    """Lo justo que _post le pide al retorno de urlopen: context manager y read()."""

    def __init__(self, cuerpo):
        self.cuerpo = cuerpo

    def read(self):
        return self.cuerpo

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


class Transporte(object):
    """El seam. Consume una secuencia declarada por caso, donde cada elemento es una
    excepción a levantar o un cuerpo de respuesta en bytes; cuenta las llamadas y
    guarda la query y las variables que viajaron, para que un caso pueda asertar
    sobre lo que se mandó y no solo sobre lo que volvió. Una llamada más allá del
    final de la secuencia levanta AssertionError, y eso es lo que vuelve asertable el
    cero de un caso que no debe tocar la red."""

    def __init__(self, nombre, secuencia):
        self.nombre = nombre
        self.secuencia = list(secuencia)
        self.llamadas = []

    def __call__(self, pedido, timeout=None):
        cuerpo = json.loads(pedido.data.decode("utf-8"))
        self.llamadas.append((cuerpo.get("query"), cuerpo.get("variables")))
        if len(self.llamadas) > len(self.secuencia):
            raise AssertionError(
                "%s: el transporte se llamó %d veces y su secuencia declara %d"
                % (self.nombre, len(self.llamadas), len(self.secuencia)))
        elemento = self.secuencia[len(self.llamadas) - 1]
        if isinstance(elemento, Exception):
            raise elemento
        return Respuesta(elemento)


CASOS = [
    ("urlerror-primer-intento",
     [urllib.error.URLError("sin ruta al host")],
     1),
]

fallas = []

for nombre, secuencia, esperadas in CASOS:
    transporte = Transporte(nombre, secuencia)
    mod.urllib.request.urlopen = transporte
    devuelto = None
    escapo = ""
    so, se = io.StringIO(), io.StringIO()
    try:
        with contextlib.redirect_stdout(so), contextlib.redirect_stderr(se):
            devuelto = mod._post(mod.MAP_READ_QUERY, {"project": "kp-falso"},
                                 mod.leer_key())
    except BaseException as exc:
        escapo = "%s: %s" % (type(exc).__name__, exc)

    if escapo:
        fallas.append("%s: la falla de transporte se escapó como %s en vez de "
                      "volver como errors" % (nombre, escapo))
    elif not isinstance(devuelto, dict) or sorted(devuelto) != ["errors"]:
        fallas.append("%s: el retorno es %s y tenía que ser un dict con la sola "
                      "clave errors" % (nombre, plano(devuelto)))
    else:
        errores = devuelto["errors"]
        if not isinstance(errores, list) or not errores:
            fallas.append("%s: errors es %s y tenía que ser una lista no vacía"
                          % (nombre, plano(errores)))
        elif "message" not in errores[0]:
            fallas.append("%s: el primer error es %s y no lleva message"
                          % (nombre, plano(errores[0])))

    if len(transporte.llamadas) != esperadas:
        fallas.append("%s: el transporte se llamó %d veces y el caso declara %d"
                      % (nombre, len(transporte.llamadas), esperadas))

    print("%-26s transporte=%-3d esperadas=%-3d %s"
          % (nombre, len(transporte.llamadas), esperadas,
             plano(escapo or devuelto)))

print("casos=%d" % len(CASOS))
print("fallas=%s" % (plano(fallas) if fallas else "ninguna"))
sys.exit(1 if fallas else 0)
PY
)"

if printf '%s\n' "$salida" | /usr/bin/grep -q 'fallas=ninguna'; then
  :
else
  printf '%s\n' "$salida" | sed 's/^/  /' >&2
  fail "[60] las operaciones que escriben no distinguen sus desenlaces de runtime con el transporte mockeado"
fi

report

# El cardinal sale de la corrida y no de una palabra escrita a mano: un conteo tipeado
# acá sería una segunda casa que nadie compara contra la primera.
casos="$(printf '%s\n' "$salida" | sed -n 's/^casos=//p')"
require_nonempty "$casos" "[60] la corrida no emitió su cardinal de casos, así que el protocolo entre el intérprete y bash se movió"
plural=""
[ "$casos" = 1 ] || plural="s"
echo "$CHECK_NAME: OK - $adapter distingue $casos desenlace$plural de runtime con el transporte mockeado, sin red y sin credencial real, bajo Python $("$py39" -c 'import sys;print("%d.%d.%d" % sys.version_info[:3])')"
