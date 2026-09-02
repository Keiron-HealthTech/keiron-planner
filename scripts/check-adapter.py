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

FUNCS = dict((n.name, n) for n in ARBOL.body if isinstance(n, ast.FunctionDef))
if "cmd_preflight" not in FUNCS or "resolver_ctx" not in FUNCS:
    bail("[32] " + ADAPTER + " no define cmd_preflight y resolver_ctx; las "
         "afirmaciones sobre el adapter quedan sin correr")

# --- afirmación 33: la query aparece en un solo lugar ------------------------
asignaciones = [n for n in ARBOL.body if isinstance(n, ast.Assign)
                and any(getattr(x, "id", None) == "PREFLIGHT_QUERY"
                        for x in n.targets)]
if len(asignaciones) != 1:
    fail("[33] PREFLIGHT_QUERY se asigna %d veces a nivel módulo, y tiene que ser "
         "exactamente una" % len(asignaciones))
dentro_del_preflight = set(id(n) for n in ast.walk(FUNCS["cmd_preflight"]))
fuera = [getattr(n, "lineno", 0) for n in ast.walk(ARBOL)
         if isinstance(n, ast.Name) and n.id == "PREFLIGHT_QUERY"
         and isinstance(n.ctx, ast.Load) and id(n) not in dentro_del_preflight]
if fuera:
    fail("[33] PREFLIGHT_QUERY se referencia fuera de cmd_preflight, en las líneas "
         "%s" % fuera)


def invocado(f):
    if isinstance(f, ast.Name):
        return f.id
    if isinstance(f, ast.Attribute) and isinstance(f.value, ast.Name):
        return f.value.id + "." + f.attr
    return None


def alcanzable(raiz):
    vistos, cola = set(), [raiz]
    while cola:
        cur = cola.pop()
        if cur in vistos or cur not in FUNCS:
            continue
        vistos.add(cur)
        for n in ast.walk(FUNCS[cur]):
            if isinstance(n, ast.Call) and invocado(n.func) in FUNCS:
                cola.append(invocado(n.func))
    return vistos


RUTA = alcanzable("cmd_preflight")
require_nonempty(RUTA, "[34] el grafo alcanzable desde cmd_preflight dio vacío")

# --- afirmación 34: ninguna mutation ------------------------------------------
QUERY = (asignaciones[0].value.value
         if asignaciones and isinstance(asignaciones[0].value, ast.Constant) else "")
literales_ruta = [n.value for nm in RUTA for n in ast.walk(FUNCS[nm])
                  if isinstance(n, ast.Constant) and isinstance(n.value, str)]
sucios = [s for s in literales_ruta if "mutation" in s]
if sucios:
    fail("[34] %d literales de string del grafo alcanzable desde cmd_preflight "
         "contienen una mutation" % len(sucios))
if "mutation" in QUERY:
    fail("[34] el valor de PREFLIGHT_QUERY contiene una mutation")

BIND = {}
for _n in ast.walk(ARBOL):
    if isinstance(_n, ast.Assign) and isinstance(_n.value, ast.Call):
        _f = _n.value.func
        if isinstance(_f, ast.Attribute) and _f.attr == "add_parser" and _n.value.args:
            _a = _n.value.args[0]
            if isinstance(_a, ast.Constant) and isinstance(_a.value, str):
                for _t in _n.targets:
                    if isinstance(_t, ast.Name):
                        BIND[_t.id] = _a.value

# --- afirmación 35: los siete consumidores ------------------------------------
CONSUMIDORES = ["map:create", "ticket:create", "frontier:query", "ticket:claim",
                "ticket:resolve", "ticket:rule-out", "work:write"]
ctx_req, handler = {}, {}
for n in ast.walk(ARBOL):
    if not isinstance(n, ast.Call):
        continue
    f = n.func
    if not (isinstance(f, ast.Attribute) and isinstance(f.value, ast.Name)):
        continue
    op = BIND.get(f.value.id)
    if op is None:
        continue
    if (f.attr == "add_argument" and n.args
            and isinstance(n.args[0], ast.Constant) and n.args[0].value == "--ctx"):
        ctx_req[op] = any(kw.arg == "required" and isinstance(kw.value, ast.Constant)
                          and kw.value.value is True for kw in n.keywords)
    if f.attr == "set_defaults":
        for kw in n.keywords:
            if kw.arg == "func" and isinstance(kw.value, ast.Name):
                handler[op] = kw.value.id
resueltos = [op for op in CONSUMIDORES if op in handler]
require_nonempty(ctx_req, "[35] el conjunto de subcomandos que declaran --ctx dio vacío")
require_nonempty(resueltos, "[35] el conjunto de handlers de los consumidores dio vacío")
if sorted(k for k, v in ctx_req.items() if v) != sorted(CONSUMIDORES):
    fail("[35] los subcomandos con --ctx requerido no son los siete consumidores: %s"
         % sorted(k for k, v in ctx_req.items() if v))
sin_req = sorted(k for k, v in ctx_req.items() if not v)
if sin_req:
    fail("[35] estos declaran --ctx sin required=True: %s" % sin_req)
for op in resueltos:
    h = handler[op]
    if any(isinstance(x, ast.Name) and x.id == "PREFLIGHT_QUERY"
           for nm in alcanzable(h) for x in ast.walk(FUNCS[nm])):
        fail("[35] el consumidor %s resuelve un ctx por su cuenta, vía %s" % (op, h))

# --- afirmación 36: un solo print a stdout ------------------------------------
a_stdout = []
for nm in sorted(RUTA):
    for n in ast.walk(FUNCS[nm]):
        if isinstance(n, ast.Call) and invocado(n.func) == "print":
            if not any(kw.arg == "file" and isinstance(kw.value, ast.Attribute)
                       and kw.value.attr == "stderr"
                       and isinstance(kw.value.value, ast.Name)
                       and kw.value.value.id == "sys" for kw in n.keywords):
                a_stdout.append((nm, n))
if len(a_stdout) != 1:
    fail("[36] hay %d print a stdout en el grafo del preflight, y tiene que haber "
         "exactamente uno" % len(a_stdout))
else:
    nm, n = a_stdout[0]
    if nm != "cmd_preflight":
        fail("[36] el único print a stdout vive en %s y no en cmd_preflight" % nm)
    if not (n.args and isinstance(n.args[0], ast.Call)
            and invocado(n.args[0].func) == "json.dumps"):
        fail("[36] el argumento del único print a stdout no es un json.dumps")

# --- afirmación 37: las ocho claves y discovery separado ----------------------
etiquetas = []
for n in ARBOL.body:
    if isinstance(n, ast.Assign) and any(getattr(x, "id", None) == "LABELS"
                                         for x in n.targets):
        etiquetas = [e.value for e in n.value.elts
                     if isinstance(e, ast.Constant) and isinstance(e.value, str)]
tipos = tabla(GLOSARIO, "## Tipos de ticket")
require_nonempty(etiquetas, "[37] la constante LABELS del adapter dio vacía")
require_nonempty(tipos, "[37] la tabla Tipos de ticket de " + GLOSARIO + " dio vacía")
if set(etiquetas) != set(tipos):
    fail("[37] LABELS y la tabla Tipos de ticket no son el mismo conjunto: solo en "
         "el código %s, solo en la tabla %s" % (sorted(set(etiquetas) - set(tipos)),
                                                sorted(set(tipos) - set(etiquetas))))
retornos = [n for n in ast.walk(FUNCS["resolver_ctx"])
            if isinstance(n, ast.Return) and isinstance(n.value, ast.Dict)]
if len(retornos) != 1:
    fail("[37] resolver_ctx tiene %d return con un dict, y tiene que tener uno"
         % len(retornos))
else:
    claves, no_lit = [], 0
    for k in retornos[0].value.keys:
        if isinstance(k, ast.Constant) and isinstance(k.value, str):
            claves.append(k.value)
        else:
            no_lit += 1
    if no_lit:
        fail("[37] el dict del ctx tiene %d claves que no son literales" % no_lit)
    # única copia del conjunto, así que se escribe acá con su número al lado
    if set(claves) != set(["viewer", "team", "done", "canceled", "default", "labels",
                           "discovery"]):
        fail("[37] las claves de primer nivel del ctx son %s" % sorted(claves))
    valor_discovery = None
    for k, v in zip(retornos[0].value.keys, retornos[0].value.values):
        if isinstance(k, ast.Constant) and k.value == "discovery":
            valor_discovery = v
    refs = [n for n in ast.walk(FUNCS["resolver_ctx"])
            if isinstance(n, ast.Name) and n.id == "DISCOVERY"]
    en_valor = ([n for n in ast.walk(valor_discovery)
                 if isinstance(n, ast.Name) and n.id == "DISCOVERY"]
                if valor_discovery is not None else [])
    if len(refs) != 1 or len(en_valor) != 1:
        fail("[37] DISCOVERY se referencia %d veces en resolver_ctx y %d de ellas "
             "en el valor de la clave discovery; tiene que ser una y una"
             % (len(refs), len(en_valor)))
if "Discovery" in etiquetas:
    fail("[37] Discovery aparece adentro de LABELS, y va como campo separado")

CONSTS = {}
for _n in ARBOL.body:
    if (isinstance(_n, ast.Assign) and isinstance(_n.value, ast.Constant)
            and isinstance(_n.value.value, int)
            and not isinstance(_n.value.value, bool)):
        for _t in _n.targets:
            if isinstance(_t, ast.Name):
                CONSTS[_t.id] = _n.value.value

# --- afirmación 39b: el flag apaga exactamente una falla ----------------------
add_boot = [n for n in ast.walk(ARBOL) if isinstance(n, ast.Call)
            and isinstance(n.func, ast.Attribute) and n.func.attr == "add_argument"
            and n.args and isinstance(n.args[0], ast.Constant)
            and n.args[0].value == "--bootstrap"]
if len(add_boot) != 1:
    fail("[39] hay %d add_argument(--bootstrap) y tiene que haber uno" % len(add_boot))
else:
    sobre = BIND.get(getattr(add_boot[0].func.value, "id", ""), "?")
    if sobre != "preflight":
        fail("[39] --bootstrap se declara sobre el subparser %s y no sobre preflight"
             % sobre)
condiciones = []
for nm in sorted(RUTA):
    for n in ast.walk(FUNCS[nm]):
        if isinstance(n, ast.If) and any(
                (isinstance(x, ast.Name) and x.id == "bootstrap")
                or (isinstance(x, ast.Attribute) and x.attr == "bootstrap")
                for x in ast.walk(n.test)):
            condiciones.append((nm, n))
if len(condiciones) != 1:
    fail("[39] el valor de --bootstrap participa en %d condiciones del grafo del "
         "preflight, y tiene que participar en una" % len(condiciones))
else:
    nm, n = condiciones[0]
    codigos_de_la_guarda = set()
    for c in ast.walk(n):
        if (isinstance(c, ast.Call) and isinstance(c.func, ast.Name)
                and c.func.id == "die"):
            a = c.args[0] if c.args else None
            if isinstance(a, ast.Name) and a.id in CONSTS:
                codigos_de_la_guarda.add(CONSTS[a.id])
            elif isinstance(a, ast.Constant) and isinstance(a.value, int):
                codigos_de_la_guarda.add(a.value)
    if codigos_de_la_guarda != set([CONSTS.get("SIN_LABEL_MAP")]):
        fail("[39] la única condición sobre --bootstrap alcanza los códigos %s, y "
             "tiene que alcanzar solo el de SIN_LABEL_MAP"
             % sorted(codigos_de_la_guarda))

report()
print("%s: OK - los %d subcomandos de %s son los de %s y los de %s, bajo Python "
      "%d.%d.%d" % (CHECK_NAME, len(literales), ADAPTER, CONTRATO, GLOSARIO,
                    sys.version_info[0], sys.version_info[1], sys.version_info[2]))
