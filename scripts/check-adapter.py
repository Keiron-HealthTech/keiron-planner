#!/usr/bin/env python3
"""Afirmaciones de AST sobre scripts/linear.py. Corre bajo 3.9: se re-exec al
intérprete de la cadena de la afirmación 19 si el que lo arrancó no lo es."""
import os
import subprocess
import sys

# Antes de cualquier import local: una corrida de un check no deja bytecode en el árbol.
sys.dont_write_bytecode = True

# La marca la pone el padre y la lee el hijo: es lo que distingue un re-exec que no
# aterrizó de un primer arranque, y corta el bucle.
MARCA = "KP_CHECK_ADAPTER_REEXEC"
CADENA = "PY39, python3.9, /usr/bin/python3"


def _es39(ruta):
    try:
        salida = subprocess.check_output(
            [ruta, "-c", "import sys;print('%d.%d' % sys.version_info[:2])"],
            stderr=subprocess.DEVNULL).decode().strip()
    except Exception:
        return False
    return salida == "3.9"


def _reexec():
    if sys.version_info[:2] == (3, 9):
        return
    if os.environ.get(MARCA):
        sys.stderr.write("check-adapter: FAIL - "
                         "[32] el re-exec no aterrizó en 3.9\n")
        sys.exit(1)
    candidatos = []
    if os.environ.get("PY39"):
        candidatos.append(os.environ["PY39"])
    candidatos.append("python3.9")
    candidatos.append("/usr/bin/python3")
    for cand in candidatos:
        if _es39(cand):
            os.environ[MARCA] = "1"
            # execvp y no execv: el segundo candidato es un nombre pelado y hay que
            # buscarlo en el PATH. El argumento del script va absoluto porque después
            # de esto viene un chdir.
            aqui = os.path.abspath(__file__)
            os.execvp(cand, [cand, aqui] + sys.argv[1:])
    sys.stderr.write("check-adapter: FAIL - "
                     "[32] no hay ningún intérprete 3.9 en la cadena " + CADENA +
                     "; las afirmaciones sobre linear.py quedan sin correr\n")
    sys.exit(1)


_reexec()
# Sin sys.path.insert: sys.path[0] ya es el directorio del script, absoluto, y
# sobrevive al chdir. El chdir va antes del import local para que toda ruta de este
# archivo sea relativa a la raíz del repo y no al cwd de quien lo invocó.
os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

import ast  # noqa: E402  después del re-exec: el ast que importa es el de 3.9
from _common import fail, report, bail, require_nonempty, CHECK_NAME  # noqa: E402

ADAPTER = "scripts/linear.py"
CONTRATO = "scripts/LINEAR-OPERATIONS.md"
GLOSARIO = "CONTEXT.md"


def tabla(ruta, encabezado):
    """Primera celda en backticks de cada fila bajo un encabezado de nivel dos."""
    filas = []
    dentro = False
    with open(ruta, encoding="utf-8") as fh:
        for linea in fh:
            if linea.startswith("## "):
                dentro = linea.rstrip("\n") == encabezado
                continue
            if not dentro or not linea.startswith("|"):
                continue
            celdas = linea.split("|")
            if len(celdas) < 3:
                continue
            primera = celdas[1].strip()
            if len(primera) > 2 and primera[0] == "`" and primera[-1] == "`":
                filas.append(primera[1:-1])
    return filas


for _ruta in (ADAPTER, CONTRATO, GLOSARIO):
    if not os.path.isfile(_ruta):
        bail("[32] falta " + _ruta +
             "; las afirmaciones sobre el adapter quedan sin correr")
try:
    with open(ADAPTER, encoding="utf-8") as _fh:
        ARBOL = ast.parse(_fh.read())
except SyntaxError as _exc:
    bail("[32] " + ADAPTER + " no parsea: " + str(_exc))

# --- afirmación 32 ----------------------------------------------------------
literales = []
no_literales = 0
for nodo in ast.walk(ARBOL):
    if not isinstance(nodo, ast.Call):
        continue
    f = nodo.func
    if not (isinstance(f, ast.Attribute) and f.attr == "add_parser"):
        continue
    if not nodo.args:
        no_literales += 1
        continue
    primero = nodo.args[0]
    if isinstance(primero, ast.Constant) and isinstance(primero.value, str):
        literales.append(primero.value)
    else:
        no_literales += 1

del_contrato = tabla(CONTRATO, "## Las doce operaciones")
del_glosario = tabla(GLOSARIO, "## Las operaciones del tracker")

require_nonempty(literales, "[32] el conjunto de add_parser del AST dio vacío")
require_nonempty(del_contrato,
                 "[32] la tabla Las doce operaciones de " + CONTRATO + " dio vacío")
require_nonempty(del_glosario,
                 "[32] la tabla Las operaciones del tracker de " + GLOSARIO +
                 " dio vacío")

if no_literales:
    fail("[32] hay %d add_parser cuyo primer argumento no es un literal de string; "
         "un bucle vacía el conjunto en silencio" % no_literales)
if set(literales) != set(del_contrato):
    fail("[32] los add_parser y la tabla de " + CONTRATO + " no son el mismo "
         "conjunto: solo en el código %s, solo en la tabla %s"
         % (sorted(set(literales) - set(del_contrato)),
            sorted(set(del_contrato) - set(literales))))
if set(del_contrato) != set(del_glosario):
    fail("[32] la tabla de " + CONTRATO + " y la de " + GLOSARIO + " no son el "
         "mismo conjunto: %s" % sorted(set(del_contrato) ^ set(del_glosario)))

report()
print("%s: OK - los %d subcomandos de %s son los de %s y los de %s, bajo Python "
      "%d.%d.%d" % (CHECK_NAME, len(literales), ADAPTER, CONTRATO, GLOSARIO,
                    sys.version_info[0], sys.version_info[1], sys.version_info[2]))
