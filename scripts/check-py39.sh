#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

. scripts/_common.sh

# Afirmación 19.

adapter=scripts/linear.py
contrato=scripts/LINEAR-OPERATIONS.md

# Un solo trap EXIT en todo el archivo: un segundo reemplaza al primero bajo bash 3.2
# y le fuga el temporal en silencio, con el check en verde. La variable se inicializa
# en vacío antes del trap, para que un directorio que sobreviva nombre que fugo.
hogar=""
limpiar() { [ -n "$hogar" ] && rm -rf "$hogar"; return 0; }
trap limpiar EXIT

# --- tercer tier: sin fuente y sin intérprete no hay nada que ejecutar ---

[ -f "$adapter" ] || bail "[19] falta $adapter; las afirmaciones sobre el adapter quedan sin correr"
[ -f "$contrato" ] || bail "[19] falta $contrato; las afirmaciones sobre el adapter quedan sin correr"

py39=""
for cand in "${PY39:-}" python3.9 /usr/bin/python3; do
  [ -n "$cand" ] || continue
  v="$("$cand" -c 'import sys;print("%d.%d" % sys.version_info[:2])' 2>/dev/null || true)"
  if [ "$v" = "3.9" ]; then py39="$cand"; break; fi
done
require_nonempty "$py39" "[19] no hay ningún intérprete 3.9 en la cadena PY39, python3.9, /usr/bin/python3"

# Los doce nombres salen del contrato y no de una lista escrita acá: una lista propia
# sería una tercera copia que nadie compara contra las otras dos.
operaciones="$(awk -F'|' '
  /^## / { dentro = ($0 == "## Las doce operaciones"); next }
  dentro && /^\|/ { c=$2; gsub(/ /,"",c); if (c ~ /^`.*`$/) { gsub(/`/,"",c); print c } }
' "$contrato")"
require_nonempty "$operaciones" "[19] la tabla Las doce operaciones de $contrato dio vacío"

# --- afirmación 19 --------------------------------------------------------------

if ! "$py39" -c 'import importlib.util, sys
sys.dont_write_bytecode = True
spec = importlib.util.spec_from_file_location("linear", sys.argv[1])
spec.loader.exec_module(importlib.util.module_from_spec(spec))' "$adapter" 2>/dev/null; then
  bail "[19] $adapter no importa bajo Python 3.9"
fi

for op in $operaciones; do
  if ! "$py39" "$adapter" "$op" --help >/dev/null 2>&1; then
    fail "[19] $op --help no sale cero bajo Python 3.9"
  fi
done

# --- afirmación 58 --------------------------------------------------------------
# El ejercicio offline de los cinco desenlaces del preflight. Ni los códigos ni las
# marcas viven en este script: salen de la tabla de códigos de salida del contrato.

tabla="$(awk -F'|' '
  /^## / { dentro = ($0 == "## Los códigos de salida del preflight"); next }
  dentro && /^\|/ && $2 ~ /^ *[0-9]+ *$/ {
    cod=$2; con=$3; mar=$6;
    gsub(/^ +| +$/,"",cod); gsub(/^ +| +$/,"",con); gsub(/^ +| +$/,"",mar);
    gsub(/`/,"",con); gsub(/`/,"",mar);
    print cod "\t" con "\t" mar }
' "$contrato")"
require_nonempty "$tabla" "[58] la tabla de códigos de salida de $contrato dio vacío"

hogar="$(mktemp -d "${TMPDIR:-/tmp}/kp-py39-hogar.XXXXXX")" || bail "[58] no se pudo crear el directorio temporal del hogar aislado"

salida="$(HOME="$hogar" XDG_CONFIG_HOME="$hogar/config" KP_TABLA="$tabla" KP_ADAPTER="$adapter" "$py39" - <<'PY' 2>&1 || true
import contextlib, importlib.util, io, json, os, sys

sys.dont_write_bytecode = True

tabla = {}
for linea in os.environ["KP_TABLA"].splitlines():
    cod, con, mar = linea.split("\t")
    tabla[con] = (int(cod), mar)

spec = importlib.util.spec_from_file_location("linear", os.environ["KP_ADAPTER"])
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

# El transporte queda neutralizado en el proceso del check: cualquier ruta que llegue
# a la red revienta con un mensaje propio y sin mandar un paquete.
def _sin_red(*a, **k):
    raise AssertionError("el check tocó la red: el seam del transporte se movió")
mod.urllib.request.urlopen = _sin_red

RUTA = os.path.join(os.environ["XDG_CONFIG_HOME"], "keiron-planner", "linear.key")

def plantar():
    os.makedirs(os.path.dirname(RUTA), exist_ok=True)
    with open(RUTA, "w") as fh:
        fh.write("lin_api_falsa\n")

def borrar():
    if os.path.isfile(RUTA):
        os.remove(RUTA)

ESTADOS = [{"id": "s1", "name": "Done", "type": "completed", "position": 1},
           {"id": "s2", "name": "Canceled", "type": "canceled", "position": 2},
           {"id": "s3", "name": "Todo", "type": "unstarted", "position": 0}]

def sano(labels=None):
    nombres = mod.LABELS if labels is None else labels
    return {"data": {
        "viewer": {"id": "v1"},
        "team": {"id": "t1", "key": "CRM", "defaultIssueState": {"id": "s3"},
                 "states": {"nodes": ESTADOS}},
        "issueLabels": {"nodes": [{"id": "l-" + n, "name": n} for n in nombres]}}}

RESPUESTAS = {
    "exito": sano(),
    "credencial-rechazada": {"errors": [{"message": "Authentication required"}]},
    "sin-team": {"data": {"viewer": {"id": "v1"}, "team": None,
                          "issueLabels": {"nodes": []}}},
    "sin-cerrados": {"data": {"viewer": {"id": "v1"},
                              "team": {"id": "t1", "defaultIssueState": {"id": "s3"},
                                       "states": {"nodes": [ESTADOS[0], ESTADOS[2]]}},
                              "issueLabels": {"nodes": []}}},
    "sin-label-map": sano([n for n in mod.LABELS if n != "map"]),
}

CASOS = [
    ("exito",                "exito",         False, True,  0,    None),
    ("sin-credencial",       None,            False, False, None, "SIN_KEY"),
    ("credencial-rechazada", "credencial-rechazada", False, True, None, "SIN_KEY"),
    ("sin-team",             "sin-team",      False, True,  None, "SIN_TEAM"),
    ("sin-cerrados",         "sin-cerrados",  False, True,  None, "SIN_CERRADOS"),
    ("sin-label-map",        "sin-label-map", False, True,  None, "SIN_LABEL_MAP"),
    ("sin-map+bootstrap",    "sin-label-map", True,  True,  0,    None),
]

class Args(object):
    pass

fallas = []
marcas = [v[1] for v in tabla.values()]
if len(set(marcas)) != len(marcas):
    fallas.append("las marcas de remediación de la tabla no son distintas entre sí")

for nombre, resp, bootstrap, con_key, esperado_ok, constante in CASOS:
    plantar() if con_key else borrar()
    if resp is not None:
        mod._post = (lambda r: (lambda q, v, k: r))(RESPUESTAS[resp])
    args = Args(); args.team = "CRM"; args.bootstrap = bootstrap
    so, se = io.StringIO(), io.StringIO()
    rc = 0
    try:
        with contextlib.redirect_stdout(so), contextlib.redirect_stderr(se):
            mod.cmd_preflight(args)
    except SystemExit as exc:
        rc = exc.code if isinstance(exc.code, int) else 1
    except AssertionError as exc:
        rc = -1; se.write(str(exc))
    out, err = so.getvalue(), se.getvalue()
    if constante is None:
        esp = 0
        detalle = ""
        if rc == 0:
            try:
                d = json.loads(out)
                detalle = "claves=%d labels=%d" % (len(d), len(d.get("labels", {})))
                if len(d) != 7 or len(d.get("labels", {})) != 8:
                    fallas.append(nombre + ": el ctx no tiene siete claves y ocho labels")
            except ValueError:
                detalle = "stdout no parsea como JSON"
                fallas.append(nombre + ": stdout no parsea como JSON")
    else:
        esp, marca = tabla[constante]
        tiene = marca in err
        detalle = "stdout vacío=%s, nombra '%s'=%s" % (out == "", marca, tiene)
        if out != "":
            fallas.append(nombre + ": stdout no quedó vacío")
        if not tiene:
            fallas.append(nombre + ": el mensaje no nombra su remediación '" + marca + "'")
    if rc != esp:
        fallas.append("%s: rc=%s, esperado %s" % (nombre, rc, esp))
    print("%-22s rc=%-4s esp=%-4s %-4s %s"
          % (nombre, rc, esp, "OK" if rc == esp else "FAIL", detalle))

codigos = sorted(set(v[0] for v in tabla.values()))
print("codigos_distintos=%s" % codigos)
if len(codigos) != 4 or any(c in (0, 1, 2) for c in codigos):
    fallas.append("los códigos de la tabla no son cuatro distintos, o alguno es 0, 1 o 2")
print("fallas=%s" % (fallas if fallas else "ninguna"))
sys.exit(1 if fallas else 0)
PY
)"
if printf '%s\n' "$salida" | /usr/bin/grep -q 'fallas=ninguna'; then
  :
else
  printf '%s\n' "$salida" | sed 's/^/  /' >&2
  fail "[58] el preflight no distingue sus cinco desenlaces, o un mensaje no nombra su remediación"
fi

report

n="$(printf '%s\n' "$operaciones" | grep -c . || true)"
echo "$CHECK_NAME: OK - $adapter importa, sus $n subcomandos responden --help, y el preflight distingue sus cinco desenlaces bajo Python $("$py39" -c 'import sys;print("%d.%d.%d" % sys.version_info[:3])')"
