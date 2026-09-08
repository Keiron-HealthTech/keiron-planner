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
import re  # noqa: E402
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


def tabla_codigos(ruta):
    """Código y constante de cada fila de la tabla de códigos de salida."""
    filas, dentro = [], False
    with open(ruta, encoding="utf-8") as fh:
        for linea in fh:
            if linea.startswith("## "):
                dentro = linea.rstrip("\n") == "## Los códigos de salida del preflight"
                continue
            if not dentro or not linea.startswith("|"):
                continue
            celdas = [c.strip() for c in linea.split("|")]
            if len(celdas) != 7 or not celdas[1].isdigit():
                continue
            filas.append((int(celdas[1]), celdas[2].strip("`")))
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
referencias = [n for n in ast.walk(ARBOL)
               if isinstance(n, ast.Name) and n.id == "PREFLIGHT_QUERY"
               and isinstance(n.ctx, ast.Load)]
fuera = [getattr(n, "lineno", 0) for n in referencias
         if id(n) not in dentro_del_preflight]
dentro = [n for n in referencias if id(n) in dentro_del_preflight]
if fuera:
    fail("[33] PREFLIGHT_QUERY se referencia fuera de cmd_preflight, en las líneas "
         "%s" % fuera)
if not dentro:
    fail("[33] PREFLIGHT_QUERY no se referencia desde cmd_preflight; nada asegura "
         "que _post reciba la constante")


def invocado(f):
    if isinstance(f, ast.Name):
        return f.id
    if isinstance(f, ast.Attribute) and isinstance(f.value, ast.Name):
        return f.value.id + "." + f.attr
    return None


def _fold_cadena(nodo):
    """Repliega un BinOp de + entre literales de string, que ast.parse no resuelve
    por su cuenta (la adyacente "a" "b" sí llega repliegada como un solo Constant).
    a + b + c parsea left-leaning, y la recursión baja por ese lado."""
    if isinstance(nodo, ast.Constant) and isinstance(nodo.value, str):
        return nodo.value
    if isinstance(nodo, ast.BinOp) and isinstance(nodo.op, ast.Add):
        izquierda = _fold_cadena(nodo.left)
        derecha = _fold_cadena(nodo.right)
        if izquierda is not None and derecha is not None:
            return izquierda + derecha
    return None


def _literales_de(nodos):
    """Todo literal de string de un iterable de nodos AST, incluido el que un BinOp
    arma por concatenación. Comparte método entre las afirmaciones 23 y 34, así que
    una mutation partida en dos con + no se cuela por ninguna de las dos rutas."""
    valores = []
    for n in nodos:
        if isinstance(n, ast.Constant) and isinstance(n.value, str):
            valores.append(n.value)
        elif isinstance(n, ast.BinOp):
            plegado = _fold_cadena(n)
            if plegado is not None:
                valores.append(plegado)
    return valores


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
QUERY = (_fold_cadena(asignaciones[0].value) or "") if asignaciones else ""
literales_ruta = [s for nm in RUTA for s in _literales_de(ast.walk(FUNCS[nm]))]
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

# --- afirmación 40: cuatro códigos distintos -----------------------------------
con_sys_exit = sorted(set(nm for nm, fn in FUNCS.items() for n in ast.walk(fn)
                          if isinstance(n, ast.Call)
                          and invocado(n.func) == "sys.exit"))
if con_sys_exit != ["die"]:
    fail("[40] sys.exit aparece en %s, y tiene que aparecer solo en die"
         % (con_sys_exit or "ninguna función"))
otras = [n for n in ast.walk(ARBOL)
         if (isinstance(n, ast.Call) and invocado(n.func) in ("os._exit", "exit"))
         or (isinstance(n, ast.Raise) and isinstance(n.exc, ast.Call)
             and invocado(n.exc.func) == "SystemExit")]
if otras:
    fail("[40] hay %d salidas por una vía que no es die: os._exit, exit() o raise "
         "SystemExit" % len(otras))
llamadas_die = [n for nm in RUTA for n in ast.walk(FUNCS[nm])
                if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
                and n.func.id == "die"]
require_nonempty(llamadas_die, "[40] no hay ninguna llamada a die alcanzable desde "
                               "cmd_preflight")
codigos, opacos = {}, 0
for n in llamadas_die:
    if len(n.args) != 3:
        opacos += 1
        continue
    a = n.args[0]
    if isinstance(a, ast.Constant) and isinstance(a.value, int):
        codigos[a.value] = "(literal)"
    elif isinstance(a, ast.Name) and a.id in CONSTS:
        codigos[CONSTS[a.id]] = a.id
    else:
        opacos += 1
if opacos:
    fail("[40] %d llamadas a die tienen un código que no resuelve a un entero, o no "
         "llevan los tres argumentos" % opacos)
if len(codigos) != 4:
    fail("[40] las fallas duras alcanzables tienen %d códigos distintos y tienen "
         "que tener cuatro: %s" % (len(codigos), sorted(codigos)))
malos = [c for c in codigos if c in (0, 1, 2)]
if malos:
    fail("[40] estos códigos de falla dura colisionan con los reservados: %s" % malos)
del_contrato_codigos = {}
for fila in tabla_codigos(CONTRATO):
    del_contrato_codigos[fila[0]] = fila[1]
require_nonempty(del_contrato_codigos, "[40] la tabla de códigos de salida de " +
                 CONTRATO + " dio vacía")
if codigos != del_contrato_codigos:
    fail("[40] el mapa de códigos del AST %s no es el de %s %s"
         % (sorted(codigos.items()), CONTRATO,
            sorted(del_contrato_codigos.items())))
raiz = re.findall(r"^  (\w+)[\s({]", QUERY, re.M)
require_nonempty(raiz, "[40] no se pudo leer ningún campo raíz de PREFLIGHT_QUERY")
prohibidos = [c for c in raiz if c in ("project", "document")]
if prohibidos:
    fail("[40] la query del preflight consulta %s" % prohibidos)

# --- afirmación 53: los bloqueos salen solo de inverseRelations ----------------


def _claves(nodo):
    """Todo nombre con el que un subárbol indexa un payload, en las tres formas
    que el adapter usa. Con atributos solos el conjunto daría vacío: la respuesta
    de _post es un dict y se indexa con corchetes o con .get."""
    nombres = set()
    for n in ast.walk(nodo):
        if isinstance(n, ast.Subscript):
            # En 3.9 el slice de un índice simple ES el Constant: no hay ast.Index
            # en el medio, y por eso este check se re-exec a 3.9 antes de tocar ast.
            if isinstance(n.slice, ast.Constant) and isinstance(n.slice.value, str):
                nombres.add(n.slice.value)
        elif isinstance(n, ast.Attribute):
            nombres.add(n.attr)
        elif (isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
              and n.func.attr == "get" and n.args
              and isinstance(n.args[0], ast.Constant)
              and isinstance(n.args[0].value, str)):
            nombres.add(n.args[0].value)
    return nombres


RUTA_FRONTERA = alcanzable(handler.get("frontier:query"))
require_nonempty(RUTA_FRONTERA,
                 "[53] el grafo alcanzable desde el handler de frontier:query dio "
                 "vacío")
CLAVES = dict((nm, _claves(FUNCS[nm])) for nm in RUTA_FRONTERA)
# Leer un bloqueante es sintáctico y no depende de ningún nombre de función: es
# nombrar inverseRelations e issue a la vez. El escaneo de truncado nombra las dos
# conexiones pero no issue, así que su relations es legal y queda afuera.
PREDICADO = sorted(nm for nm, claves in CLAVES.items()
                   if "inverseRelations" in claves and "issue" in claves)
require_nonempty(PREDICADO,
                 "[53] ninguna función alcanzable desde frontier:query lee un "
                 "bloqueante: ninguna nombra inverseRelations e issue a la vez")
mezcladas = sorted(nm for nm in PREDICADO
                   if "relations" in CLAVES[nm] or "relatedIssue" in CLAVES[nm])
if mezcladas:
    fail("[53] estas funciones leen un bloqueante y además nombran relations o "
         "relatedIssue: %s" % mezcladas)
con_related = sorted(nm for nm, claves in CLAVES.items()
                     if "relatedIssue" in claves)
if con_related:
    fail("[53] relatedIssue solo lo trae relations.nodes, y estas funciones del "
         "grafo de frontier:query lo nombran: %s" % con_related)

# --- afirmación 23: ninguna mutation en la ruta de map:read --------------------
STRCONSTS = {}
for _n in ARBOL.body:
    if not isinstance(_n, ast.Assign):
        continue
    if isinstance(_n.value, ast.Constant) and isinstance(_n.value.value, str):
        _valor_str = _n.value.value
    elif isinstance(_n.value, ast.BinOp):
        # Misma _fold_cadena de las afirmaciones 23 y 34: una constante de módulo
        # armada con + no queda afuera del conjunto solo por no ser un Constant.
        _valor_str = _fold_cadena(_n.value)
    else:
        _valor_str = None
    if _valor_str is None:
        continue
    for _t in _n.targets:
        if isinstance(_t, ast.Name):
            STRCONSTS[_t.id] = _valor_str

RUTA_MAP = alcanzable(handler.get("map:read"))
require_nonempty(RUTA_MAP,
                 "[23] el grafo alcanzable desde el handler de map:read dio vacío")
# Va antes de las guardas de vacuidad porque es la que caza el stub sin ambigüedad:
# cmd_stub sí tiene literales propios, pero llama a _post cero veces. Exigir
# exactamente una caza además un segundo round trip, que ninguna vacuidad vería.
posts = [n for nm in sorted(RUTA_MAP) for n in ast.walk(FUNCS[nm])
         if isinstance(n, ast.Call) and invocado(n.func) == "_post"]
if len(posts) != 1:
    fail("[23] el grafo alcanzable desde map:read llama a _post %d veces, y tiene "
         "que llamarlo exactamente una" % len(posts))
LITERALES_MAP = [s for nm in sorted(RUTA_MAP) for s in _literales_de(ast.walk(FUNCS[nm]))]
require_nonempty(LITERALES_MAP,
                 "[23] el conjunto de literales de string del grafo de map:read dio "
                 "vacío")
# La query no es un literal del subárbol: se referencia por nombre. Sin este cuarto
# conjunto la afirmación probaría cero justo sobre el texto que importa.
REFERIDAS = sorted(set(n.id for nm in RUTA_MAP for n in ast.walk(FUNCS[nm])
                       if isinstance(n, ast.Name) and n.id in STRCONSTS))
require_nonempty(REFERIDAS,
                 "[23] el grafo de map:read no referencia ninguna constante de "
                 "string del módulo, así que su query no entra en el conjunto")
sucios_map = [s for s in LITERALES_MAP + [STRCONSTS[nm] for nm in REFERIDAS]
              if "mutation" in s]
if sucios_map:
    fail("[23] %d cadenas alcanzables desde map:read, contando el valor de las "
         "constantes de string que el grafo referencia por nombre, contienen una "
         "mutation" % len(sucios_map))


report()
print("%s: OK - las diez afirmaciones de AST sobre %s cierran, bajo Python "
      "%d.%d.%d" % (CHECK_NAME, ADAPTER,
                    sys.version_info[0], sys.version_info[1], sys.version_info[2]))
