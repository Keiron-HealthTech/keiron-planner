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

# --- afirmación 37: las nueve claves y discovery separado ---------------------
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

# --- afirmación 13: milestone:create nunca pasa targetDate -----------------------

# Mismo mecanismo que la 23: el handler real por set_defaults, el grafo por
# alcanzable(), y STRCONSTS para mirar dentro de las constantes de módulo que el grafo
# referencia por nombre y no solo los literales inline de su propio subárbol.
MILESTONE_ROUTE = alcanzable(handler.get("milestone:create"))
require_nonempty(MILESTONE_ROUTE,
                 "[13] el grafo alcanzable desde el handler de milestone:create dio "
                 "vacío; el handler volvió a ser un stub y la afirmación probaría "
                 "cero")
MILESTONE_REFERENCED = sorted(set(n.id for nm in MILESTONE_ROUTE for n in ast.walk(FUNCS[nm])
                                 if isinstance(n, ast.Name) and n.id in STRCONSTS))
require_nonempty(MILESTONE_REFERENCED,
                 "[13] el grafo de milestone:create no referencia ninguna constante "
                 "de string del módulo, así que la mitad de la prohibición probaría "
                 "sobre el conjunto vacío")
# La cláusula positiva: sin ella, un handler que no postea nada pasaría en verde la
# prohibición de un campo que nunca pudo pasar.
if not any("projectMilestoneCreate" in STRCONSTS[nm] for nm in MILESTONE_REFERENCED):
    fail("[13] ninguna constante que el grafo de milestone:create referencia por "
         "nombre contiene projectMilestoneCreate; el handler no postea la mutation "
         "que la afirmación espera")
# El literal, en cualquier ast.Constant de string del grafo: ast.walk ya visita las
# claves de un ast.Dict como sus propios nodos Constant, así que esto cubre a la vez
# un string suelto y una clave de dict apareada, sin necesitar una segunda cláusula.
_TARGETDATE_LITERAL = sorted(set(
    nm for nm in MILESTONE_ROUTE for n in ast.walk(FUNCS[nm])
    if isinstance(n, ast.Constant) and n.value == "targetDate"))
if _TARGETDATE_LITERAL:
    fail("[13] estas funciones del grafo de milestone:create nombran el literal "
         "targetDate: %s" % _TARGETDATE_LITERAL)
# Y como subcadena de las constantes referenciadas: es lo que hace que la afirmación
# siga siendo verdad cuando el campo entre por la puerta de la constante de GraphQL,
# que es por donde entraría de verdad.
_TARGETDATE_CONST = [nm for nm in MILESTONE_REFERENCED if "targetDate" in STRCONSTS[nm]]
if _TARGETDATE_CONST:
    fail("[13] estas constantes de string que el grafo de milestone:create "
         "referencia por nombre contienen targetDate: %s" % _TARGETDATE_CONST)

# --- afirmación 59: counts.milestones es un conteo y nunca un veredicto ----------

# La raíz es la misma que la de la 53, o sea el grafo alcanzable desde el handler que
# set_defaults ata al subparser de frontier:query. El ancla no es el nombre de una
# función sino el nombre de la clave: así una salida que se mude a un helper sigue
# entrando al conjunto.
DICTS_COUNTS = [n for nm in sorted(RUTA_FRONTERA) for n in ast.walk(FUNCS[nm])
                if isinstance(n, ast.Dict)
                and any(isinstance(k, ast.Constant) and k.value == "counts"
                        for k in n.keys)]
require_nonempty(DICTS_COUNTS,
                 "[59] ningún dict literal del grafo de frontier:query lleva la clave "
                 "counts; el handler volvió a ser un stub, o la salida dejó de armarse "
                 "con literales, y toda aserción posterior sería derivada")

CLAVES_COUNTS = set(["open", "takeable", "milestones"])


def _valor_apareado(nodo, clave):
    for k, v in zip(nodo.keys, nodo.values):
        if isinstance(k, ast.Constant) and k.value == clave:
            return v
    return None


def _forma_de_conteo(nodo):
    """Un entero literal que NO es booleano, o una llamada a len. El booleano se
    excluye explícito porque en Python un True es instancia de int, así que una
    verificación por tipo que no lo excluya deja pasar milestones: True."""
    if isinstance(nodo, ast.Constant):
        return isinstance(nodo.value, int) and not isinstance(nodo.value, bool)
    return isinstance(nodo, ast.Call) and invocado(nodo.func) == "len"


for _dict in DICTS_COUNTS:
    _linea = getattr(_dict, "lineno", 0)
    _interno = _valor_apareado(_dict, "counts")
    if not isinstance(_interno, ast.Dict):
        # Falla y nunca saltea esta entrada: saltearla haría que la afirmación pruebe
        # cero sin decirlo.
        fail("[59] el valor apareado con counts en la línea %d no es un dict literal, "
             "así que sus claves no se pueden comparar" % _linea)
        continue
    # _claves_counts y no _claves: el nombre pelado pisaba la FUNCIÓN _claves de arriba
    # para todo lo que viniera después en el archivo, y el primer bloque que la volviera
    # a llamar reventaba con un TypeError en vez de fallar una afirmación.
    _claves_counts = set(k.value for k in _interno.keys
                         if isinstance(k, ast.Constant) and isinstance(k.value, str))
    if _claves_counts != CLAVES_COUNTS:
        # Igualdad de conjuntos: ninguna rama puede olvidarse la clave nueva y ninguna
        # puede agregar una cuarta.
        fail("[59] el counts de la línea %d tiene las claves %s y tiene que tener "
             "exactamente %s" % (_linea, sorted(_claves_counts),
                                 sorted(CLAVES_COUNTS)))
        continue
    if not _forma_de_conteo(_valor_apareado(_interno, "milestones")):
        fail("[59] el valor de milestones en la línea %d no es un entero literal no "
             "booleano ni una llamada a len, así que no tiene forma de conteo" % _linea)

# Sin esta mitad la afirmación pasaría con una clave estructuralmente perfecta que vale
# cero para siempre, porque la query nunca pidió la conexión.
REFERIDAS_FRONTERA = sorted(set(n.id for nm in RUTA_FRONTERA
                                for n in ast.walk(FUNCS[nm])
                                if isinstance(n, ast.Name) and n.id in STRCONSTS))
require_nonempty(REFERIDAS_FRONTERA,
                 "[59] el grafo de frontier:query no referencia ninguna constante de "
                 "string del módulo, así que su query no entra en el conjunto")
if not any("projectMilestones" in STRCONSTS[nm] for nm in REFERIDAS_FRONTERA):
    fail("[59] ninguna constante de string que el grafo de frontier:query referencia "
         "por nombre contiene projectMilestones")


# --- la ruta de escritura, raíz compartida por las nueve de este change -----------

# Misma resolución que la 23, la 53 y la 59: el handler real sale de set_defaults y el
# grafo de alcanzable(). Se define una sola vez y las nueve la citan.
RUTA_ESCRITURA = alcanzable(handler.get("map:write"))
require_nonempty(RUTA_ESCRITURA,
                 "[24] el grafo alcanzable desde el handler de map:write dio vacío; el "
                 "handler volvió a ser un stub y las nueve afirmaciones probarían cero")

ARGS_DE = {}
for _n in ast.walk(ARBOL):
    if not isinstance(_n, ast.Call):
        continue
    _f = _n.func
    if not (isinstance(_f, ast.Attribute) and isinstance(_f.value, ast.Name)):
        continue
    _op = BIND.get(_f.value.id)
    if _op is None or _f.attr != "add_argument" or not _n.args:
        continue
    if isinstance(_n.args[0], ast.Constant):
        ARGS_DE.setdefault(_op, {})[_n.args[0].value] = _n
require_nonempty(ARGS_DE.get("map:write"),
                 "[26] el subparser de map:write no declara ningún add_argument que el "
                 "extractor vea; las afirmaciones sobre sus flags probarían cero")

with open(ADAPTER, encoding="utf-8") as _fh:
    FUENTE = _fh.read()

IMPORTADOS = [a.name for n in ast.walk(ARBOL) if isinstance(n, ast.Import)
              for a in n.names]
DESDE = [n.module for n in ast.walk(ARBOL) if isinstance(n, ast.ImportFrom)]


def _post_con(nodo, aguja):
    """True si el subárbol lleva un Call a _post cuyo primer argumento es el nombre de
    una constante de string del módulo cuyo valor contiene la aguja. Mira la constante
    por nombre y no el literal, porque las queries se referencian, no se inlinean."""
    for n in ast.walk(nodo):
        if not (isinstance(n, ast.Call) and invocado(n.func) == "_post" and n.args):
            continue
        a = n.args[0]
        if isinstance(a, ast.Name) and aguja in STRCONSTS.get(a.id, ""):
            return True
    return False


def _corta(st):
    """Una sentencia de primer nivel que interrumpe el flujo: la que la 24 no puede
    tener entre la lectura y la escritura. Mira si la sentencia ES un Return, un Raise o
    una llamada pelada a sys.exit, y NO si contiene uno anidado. La diferencia es
    deliberada: una guarda condicional que aborta el intento es correcta, es la forma no
    fatal del die que la Brecha de la fila ya excusaba, y es la que el reintento necesita
    para devolver un fracaso releíble en vez de matar el proceso."""
    if isinstance(st, (ast.Return, ast.Raise)):
        return True
    if isinstance(st, ast.Expr) and isinstance(st.value, ast.Call):
        f = st.value.func
        return (isinstance(f, ast.Attribute) and f.attr == "exit"
                and getattr(f.value, "id", None) == "sys")
    return False


# --- afirmación 24: la lectura y la escritura en el mismo FunctionDef -------------

LEEN = set(nm for nm in RUTA_ESCRITURA if _post_con(FUNCS[nm], "project(id:"))
ESCRIBEN = set(nm for nm in RUTA_ESCRITURA if _post_con(FUNCS[nm], "projectUpdate"))
require_nonempty(LEEN, "[24] ninguna función del grafo de map:write le pasa a _post una "
                       "constante del módulo que contenga project(id:")
require_nonempty(ESCRIBEN, "[24] ninguna función del grafo de map:write le pasa a _post "
                           "una constante del módulo que contenga projectUpdate")
AMBAS = sorted(LEEN & ESCRIBEN)
if len(AMBAS) != 1:
    fail("[24] la lectura y la escritura tienen que salir del mismo FunctionDef, y las "
         "funciones que llevan las dos son %s" % AMBAS)
else:
    _cuerpo = FUNCS[AMBAS[0]].body
    _lee = [i for i, st in enumerate(_cuerpo) if _post_con(st, "project(id:")]
    _esc = [i for i, st in enumerate(_cuerpo) if _post_con(st, "projectUpdate")]
    if not _lee or not _esc:
        fail("[24] en %s las dos sentencias de red no están en el cuerpo de primer "
             "nivel, así que su orden no se puede comparar" % AMBAS[0])
    elif _lee[0] >= _esc[0]:
        fail("[24] en %s la lectura está en la sentencia %d y la escritura en la %d, y "
             "la lectura tiene que ir primero" % (AMBAS[0], _lee[0], _esc[0]))
    else:
        if isinstance(_cuerpo[_lee[0]], ast.Return):
            fail("[24] en %s la sentencia de la lectura es un Return, así que todo lo "
                 "que sigue es código muerto y el predicado pasaría por vacuidad"
                 % AMBAS[0])
        _medio = [i for i in range(_lee[0] + 1, _esc[0]) if _corta(_cuerpo[i])]
        if _medio:
            fail("[24] en %s las sentencias %s, entre la lectura y la escritura, son un "
                 "retorno, un levantamiento o una salida de primer nivel"
                 % (AMBAS[0], _medio))

_POSTS_ESCRITURA = [n for nm in sorted(RUTA_ESCRITURA) for n in ast.walk(FUNCS[nm])
                    if isinstance(n, ast.Call) and invocado(n.func) == "_post"]
if len(_POSTS_ESCRITURA) != 2:
    fail("[24] el grafo alcanzable desde map:write llama a _post %d veces, y tiene que "
         "llamarlo exactamente dos" % len(_POSTS_ESCRITURA))

# --- afirmación 26: --expect-sections existe y su ausencia no aborta --------------

_EXPECT = ARGS_DE["map:write"].get("--expect-sections")
if _EXPECT is None:
    fail("[26] map:write no declara --expect-sections")
elif any(kw.arg == "required" and isinstance(kw.value, ast.Constant)
         and kw.value.value is True for kw in _EXPECT.keywords):
    fail("[26] --expect-sections está declarado con required=True, así que su ausencia "
         "aborta")

IFS_EXPECT = []
for _nm in sorted(RUTA_ESCRITURA):
    for _n in ast.walk(FUNCS[_nm]):
        if not (isinstance(_n, ast.If) and isinstance(_n.test, ast.Compare)):
            continue
        if not any(isinstance(c, ast.Constant) and c.value is None
                   for c in _n.test.comparators):
            continue
        if "expect" not in ast.dump(_n.test) and "esperadas" not in ast.dump(_n.test):
            continue
        IFS_EXPECT.append(_n)
require_nonempty(IFS_EXPECT,
                 "[26] ninguna rama del grafo de map:write compara las huellas "
                 "esperadas contra None, así que la afirmación probaría cero")
for _n in IFS_EXPECT:
    # La rama que se toma cuando el valor ES None: el body de un `is None`, el orelse
    # de un `is not None`.
    _rama = _n.body if isinstance(_n.test.ops[0], ast.Is) else _n.orelse
    if any(isinstance(x, ast.Call) and invocado(x.func) == "die"
           for st in _rama for x in ast.walk(st)):
        fail("[26] la rama que se toma cuando --expect-sections es None, en la línea "
             "%d, llama a die" % _n.lineno)

# --- afirmación 27: el único acceso a disco es la lectura de la credencial ---------

ABIERTOS = [n for n in ast.walk(ARBOL)
            if isinstance(n, ast.Call) and invocado(n.func) == "open"]
require_nonempty(ABIERTOS,
                 "[27] el conjunto de llamadas a open dio vacío, y eso significa que la "
                 "extracción se rompió y no que el archivo sea limpio")
if len(ABIERTOS) != 1:
    fail("[27] hay %d llamadas a open y tiene que haber exactamente una"
         % len(ABIERTOS))
_EN_KEY = [n for n in ast.walk(FUNCS["leer_key"])
           if isinstance(n, ast.Call) and invocado(n.func) == "open"] \
    if "leer_key" in FUNCS else []
if len(_EN_KEY) != len(ABIERTOS):
    fail("[27] %d de las %d llamadas a open viven fuera de leer_key"
         % (len(ABIERTOS) - len(_EN_KEY), len(ABIERTOS)))

_OS_PROHIBIDOS = ("makedirs", "mkdir", "remove", "unlink", "rename", "replace", "rmdir")
_OS_PATH_PERMITIDOS = ("isfile", "join", "expanduser")
_DISCO = []
for _n in ast.walk(ARBOL):
    if not (isinstance(_n, ast.Call) and isinstance(_n.func, ast.Attribute)):
        continue
    _base = _n.func.value
    if isinstance(_base, ast.Name) and _base.id == "os" \
            and _n.func.attr in _OS_PROHIBIDOS:
        _DISCO.append("os." + _n.func.attr)
    if isinstance(_base, ast.Name) and _base.id == "shutil":
        _DISCO.append("shutil." + _n.func.attr)
    if (isinstance(_base, ast.Attribute) and _base.attr == "path"
            and getattr(_base.value, "id", None) == "os"
            and _n.func.attr not in _OS_PATH_PERMITIDOS):
        _DISCO.append("os.path." + _n.func.attr)
if _DISCO:
    fail("[27] estas llamadas tocan el disco fuera de la lectura de la credencial: %s"
         % sorted(set(_DISCO)))
if "pathlib" in IMPORTADOS or "pathlib" in DESDE:
    fail("[27] pathlib está importado, y su superficie de disco no la ve el resto de "
         "esta afirmación")

# --- afirmación 28: un reintento por handler, y ningún mecanismo expuesto ----------

_ASIGNA_MAX = [n for n in ARBOL.body if isinstance(n, ast.Assign)
               and any(isinstance(t, ast.Name) and t.id == "MAX_INTENTOS"
                       for t in n.targets)]
if len(_ASIGNA_MAX) != 1:
    fail("[28] MAX_INTENTOS se asigna %d veces a nivel de módulo y tiene que asignarse "
         "exactamente una" % len(_ASIGNA_MAX))
    VALOR_MAX = None
elif not (isinstance(_ASIGNA_MAX[0].value, ast.Constant)
          and isinstance(_ASIGNA_MAX[0].value.value, int)
          and not isinstance(_ASIGNA_MAX[0].value.value, bool)):
    fail("[28] el valor de MAX_INTENTOS no es un entero literal")
    VALOR_MAX = None
else:
    VALOR_MAX = _ASIGNA_MAX[0].value.value

HANDLERS_CON_REINTENTO = ("map:write", "map:create")
_NOMBRES_HANDLER = [handler.get(op) for op in HANDLERS_CON_REINTENTO]
require_nonempty([h for h in _NOMBRES_HANDLER if h],
                 "[28] ningún handler de map:write o map:create resuelve por "
                 "set_defaults, así que la forma del reintento no se puede mirar")

_REFS_MAX = [n for n in ast.walk(ARBOL) if isinstance(n, ast.Name)
             and n.id == "MAX_INTENTOS" and isinstance(n.ctx, ast.Load)]
if len(_REFS_MAX) != 2:
    fail("[28] MAX_INTENTOS se referencia por nombre %d veces y tiene que "
         "referenciarse exactamente dos, una por handler" % len(_REFS_MAX))

_ADENTRO = 0
for _op in HANDLERS_CON_REINTENTO:
    _h = handler.get(_op)
    if _h is None or _h not in FUNCS:
        fail("[28] el handler de %s no resuelve a una función del módulo" % _op)
        continue
    _fn = FUNCS[_h]
    _fors = [n for n in ast.walk(_fn) if isinstance(n, ast.For)]
    _refs = [n for n in ast.walk(_fn) if isinstance(n, ast.Name)
             and n.id == "MAX_INTENTOS" and isinstance(n.ctx, ast.Load)]
    _ADENTRO += len(_refs)
    if len(_fors) != 1:
        fail("[28] %s tiene %d For y tiene que tener exactamente uno" % (_h, len(_fors)))
    elif len(_refs) != 1:
        fail("[28] %s referencia a MAX_INTENTOS %d veces y tiene que referenciarla una"
             % (_h, len(_refs)))
    elif not (isinstance(_fors[0].iter, ast.Call)
              and invocado(_fors[0].iter.func) == "range"
              and any(x is _refs[0]
                      for a in _fors[0].iter.args for x in ast.walk(a))):
        fail("[28] la referencia a MAX_INTENTOS de %s no es el argumento de un range en "
             "el iter de su For, así que la constante no gobierna el bucle" % _h)
    if VALOR_MAX is not None:
        _desnudos = [n for n in ast.walk(_fn) if isinstance(n, ast.Constant)
                     and isinstance(n.value, int) and not isinstance(n.value, bool)
                     and n.value == VALOR_MAX]
        if _desnudos:
            fail("[28] %s lleva %d entero literal igual al valor de MAX_INTENTOS, así "
                 "que el contador puede quedar desnudo" % (_h, len(_desnudos)))
if _ADENTRO != len(_REFS_MAX):
    fail("[28] %d referencias a MAX_INTENTOS viven fuera de los dos handlers"
         % (len(_REFS_MAX) - _ADENTRO))

# La asimetría, que es lo único de ella que el AST puede ver: el For de map:create
# cuelga del If que pregunta por args.project, y el orelse no tiene ni For ni constante.
_HC = handler.get("map:create")
if _HC in FUNCS:
    _IFS_PROJECT = [n for n in ast.walk(FUNCS[_HC]) if isinstance(n, ast.If)
                    and any(isinstance(x, ast.Attribute) and x.attr == "project"
                            for x in ast.walk(n.test))]
    require_nonempty(_IFS_PROJECT,
                     "[28] el handler de map:create no ramifica sobre el atributo "
                     "project de los args, así que su asimetría no se puede mirar")
    _bien = False
    for _if in _IFS_PROJECT:
        _en_cuerpo = [n for st in _if.body for n in ast.walk(st)
                      if isinstance(n, ast.For)]
        _en_orelse = [n for st in _if.orelse for n in ast.walk(st)
                      if isinstance(n, ast.For)]
        _max_orelse = [n for st in _if.orelse for n in ast.walk(st)
                       if isinstance(n, ast.Name) and n.id == "MAX_INTENTOS"]
        if len(_en_cuerpo) == 1 and not _en_orelse and not _max_orelse:
            _bien = True
    if not _bien:
        fail("[28] en el handler de map:create la rama que adopta tiene que llevar el "
             "único For y la rama que crea no puede llevar ni For ni referencia a "
             "MAX_INTENTOS: la asimetría del reintento no está en el árbol")

_CON_DEFAULT_FALSO = []
for _nm in sorted(RUTA_ESCRITURA):
    _a = FUNCS[_nm].args
    _conteo = sum(1 for d in _a.defaults
                  if isinstance(d, ast.Constant) and d.value is False)
    if _conteo:
        _CON_DEFAULT_FALSO.append(_nm)
if len(_CON_DEFAULT_FALSO) != 1:
    fail("[28] el booleano de idempotencia invertida tiene que ser un parámetro con "
         "default False de exactamente una función del grafo de map:write, y lo llevan "
         "%s" % _CON_DEFAULT_FALSO)

_EXPUESTOS = []
for _n in ast.walk(ARBOL):
    if not (isinstance(_n, ast.Call) and isinstance(_n.func, ast.Attribute)
            and _n.func.attr == "add_argument" and _n.args):
        continue
    if not isinstance(_n.args[0], ast.Constant):
        continue
    _lit = str(_n.args[0].value)
    if any(p in _lit for p in ("intento", "retry", "idempot")):
        _EXPUESTOS.append(_lit)
if _EXPUESTOS:
    fail("[28] estos add_argument exponen un mecanismo interno del reintento: %s"
         % _EXPUESTOS)

# --- afirmación 29: ninguna rama sobre updatedAt ----------------------------------

RAMAS = [n for n in ast.walk(ARBOL) if isinstance(n, (ast.If, ast.Compare))]
require_nonempty(RAMAS,
                 "[29] el archivo no tiene ningún If ni Compare, y una aserción de "
                 "ausencia sobre un conjunto vacío no aserta nada")
_SOBRE_UPDATED = [n for n in RAMAS
                  if "updatedAt" in ast.dump(n.test if isinstance(n, ast.If) else n)]
if _SOBRE_UPDATED:
    fail("[29] updatedAt aparece en %d If.test o Compare, y está coalescido, así que "
         "ramificar sobre él da un resultado falso" % len(_SOBRE_UPDATED))

# --- afirmación 30: ninguna query pide el estado interno del editor ---------------

_OCURRENCIAS = FUENTE.count("contentState")
if _OCURRENCIAS != 0:
    fail("[30] contentState aparece %d veces en el texto de %s, y tiene que aparecer "
         "cero: es la única de estas afirmaciones donde el archivo entero es más fuerte "
         "que la ruta, porque un comentario que lo nombra es una invitación a pedirlo"
         % (_OCURRENCIAS, ADAPTER))

# --- afirmación 31: cero verificación posterior, cero sueño -----------------------

_FLAG_VERIFY = [n for n in ast.walk(ARBOL)
                if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
                and n.func.attr == "add_argument" and n.args
                and isinstance(n.args[0], ast.Constant)
                and n.args[0].value == "--verify"]
if _FLAG_VERIFY:
    fail("[31] hay un add_argument(\"--verify\"): un --verify apagado por defecto "
         "sigue siendo código muerto de verificación posterior")
if "time" in IMPORTADOS or "time" in DESDE:
    fail("[31] time está importado")
_DORMIDAS = [n for n in ast.walk(ARBOL)
             if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
             and getattr(n.func.value, "id", None) == "time"]
if _DORMIDAS:
    fail("[31] hay %d llamadas a un atributo de time" % len(_DORMIDAS))

# La mitad acotada a RUTA_ESCRITURA: adentro de ese grafo la función que emite el
# projectUpdate es una sola, así que la extracción no es ambigua. La rama de map:create
# queda fuera a propósito, igual que en la 24, y su ausencia de relectura la mide el
# conteo de transporte de la afirmación 60.
if len(ESCRIBEN) != 1:
    fail("[31] en el grafo de map:write tiene que haber exactamente una función que "
         "emita el projectUpdate, y son %s" % sorted(ESCRIBEN))
else:
    _cuerpo = FUNCS[sorted(ESCRIBEN)[0]].body
    _esc = [i for i, st in enumerate(_cuerpo) if _post_con(st, "projectUpdate")]
    _posteriores = _cuerpo[_esc[0] + 1:]
    _releen = [st for st in _posteriores
               if any(isinstance(x, ast.Call) and invocado(x.func) == "_post"
                      for x in ast.walk(st))
               or any(isinstance(x, ast.Name) and "project(id:" in STRCONSTS.get(x.id, "")
                      for x in ast.walk(st))]
    if _releen:
        fail("[31] %d sentencias posteriores al projectUpdate vuelven a llamar a _post "
             "o referencian la constante de lectura" % len(_releen))

# --- afirmación 44: el adapter no envuelve texto ----------------------------------

if "textwrap" in IMPORTADOS or "textwrap" in DESDE:
    fail("[44] textwrap está importado")
JOINS = [n for nm in sorted(RUTA_ESCRITURA) for n in ast.walk(FUNCS[nm])
         if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
         and n.func.attr == "join"]
require_nonempty(JOINS,
                 "[44] el grafo de map:write no llama a ningún join, y hay al menos uno "
                 "—el que rearma el contenido—, así que la extracción se rompió")
_CORTADAS = [n for n in JOINS for a in n.args for s in ast.walk(a)
             if isinstance(s, ast.Subscript) and isinstance(s.slice, ast.Slice)]
if _CORTADAS:
    fail("[44] %d join del grafo de map:write reciben una rebanada, que es la forma de "
         "un envoltorio de texto" % len(_CORTADAS))

# --- afirmación 45: el gist es un token propio y tiene tope de 120 ----------------

_DEC = ARGS_DE["map:write"].get("--append-decision")
if _DEC is None:
    fail("[45] map:write no declara --append-decision")
elif not any(kw.arg == "nargs" and isinstance(kw.value, ast.Constant)
             and kw.value.value == 2 for kw in _DEC.keywords):
    fail("[45] --append-decision no lleva nargs=2, así que el gist no llega como su "
         "propio token de argv y el tope no se le puede aplicar solo a él")

_CMP120 = [n for nm in sorted(RUTA_ESCRITURA) for n in ast.walk(FUNCS[nm])
           if isinstance(n, ast.Compare)
           and any(isinstance(c, ast.Constant) and not isinstance(c.value, bool)
                   and c.value == 120 for c in n.comparators)]
if len(_CMP120) != 1:
    fail("[45] en el grafo de map:write hay %d comparaciones contra el literal 120 y "
         "tiene que haber exactamente una" % len(_CMP120))
else:
    _LLEVA_DIE = False
    for _nm in sorted(RUTA_ESCRITURA):
        for _n in ast.walk(FUNCS[_nm]):
            if not isinstance(_n, ast.If):
                continue
            if not any(x is _CMP120[0] for x in ast.walk(_n.test)):
                continue
            if any(isinstance(x, ast.Call) and invocado(x.func) == "die"
                   for x in ast.walk(_n)):
                _LLEVA_DIE = True
    if not _LLEVA_DIE:
        fail("[45] la comparación contra 120 no está adentro de un If que lleve un die, "
             "así que un gist demasiado largo no sale con código no cero")

_LIT120 = [n for n in ast.walk(ARBOL) if isinstance(n, ast.Constant)
           and isinstance(n.value, int) and not isinstance(n.value, bool)
           and n.value == 120]
if len(_LIT120) != 1:
    fail("[45] el literal 120 aparece %d veces en el archivo y tiene que vivir en un "
         "solo lugar" % len(_LIT120))

# --- la ruta de ticket:create, raíz compartida por las cuatro de este change ------

# Misma resolución que la 23, la 24, la 53 y la 59: el handler real sale de
# set_defaults y el grafo de alcanzable(). Se define una sola vez y las cuatro la citan.
RUTA_TICKET = alcanzable(handler.get("ticket:create"))
require_nonempty(RUTA_TICKET,
                 "[11] el grafo alcanzable desde el handler de ticket:create dio "
                 "vacío; el handler volvió a ser un stub y las cuatro afirmaciones "
                 "probarían cero")

# Las rutas de creación de issues del archivo: las funciones que le pasan a _post una
# constante de string del módulo que contiene una de las dos mutations de creación.
CREADORAS = sorted(nm for nm in FUNCS if _post_con(FUNCS[nm], "issueCreate")
                   or _post_con(FUNCS[nm], "issueBatchCreate"))
require_nonempty(CREADORAS,
                 "[11] ninguna función le pasa a _post una constante que contenga "
                 "issueCreate ni issueBatchCreate; la afirmación probaría sobre el "
                 "conjunto vacío")


def _valores_de_clave(nombre, clave):
    """Los valores que una clave literal toma en los dicts del cuerpo de una función."""
    valores = []
    for n in ast.walk(FUNCS[nombre]):
        if not isinstance(n, ast.Dict):
            continue
        for k, v in zip(n.keys, n.values):
            if isinstance(k, ast.Constant) and k.value == clave:
                valores.append(v)
    return valores


# --- afirmación 11: toda ruta de creación de issues pasa stateId ------------------

_SIN_ESTADO = [nm for nm in CREADORAS if not _valores_de_clave(nm, "stateId")]
if _SIN_ESTADO:
    fail("[11] estas funciones emiten una creación de issues y ningún dict de su "
         "alcance lleva stateId, así que la issue nace en Triage: %s" % _SIN_ESTADO)

# --- afirmación 12: estimate en cero, y en ninguna otra ruta de creación ----------

_ESTIMATES = [v for nm in sorted(RUTA_TICKET)
              for v in _valores_de_clave(nm, "estimate")]
if len(_ESTIMATES) != 1:
    fail("[12] en el grafo de ticket:create la clave estimate aparece %d veces y "
         "tiene que aparecer exactamente una" % len(_ESTIMATES))
elif not (isinstance(_ESTIMATES[0], ast.Constant)
          and isinstance(_ESTIMATES[0].value, int)
          and not isinstance(_ESTIMATES[0].value, bool)
          and _ESTIMATES[0].value == 0):
    fail("[12] el estimate del grafo de ticket:create no es el entero literal 0; un "
         "False también compara igual a cero y no es lo mismo")

# La segunda mitad cuantifica sobre las OTRAS rutas de creación, que hoy es el conjunto
# vacío porque work:write sigue stub. El require_nonempty de arriba es sobre el conjunto
# de rutas, que sí tiene un elemento: sin él la mitad sería vacua sin que se note.
_OTRAS_CREADORAS = [nm for nm in CREADORAS if nm not in RUTA_TICKET]
_CON_ESTIMATE = [nm for nm in _OTRAS_CREADORAS if _valores_de_clave(nm, "estimate")]
if _CON_ESTIMATE:
    fail("[12] estas rutas de creación de issues que no son ticket:create pasan "
         "estimate: %s" % _CON_ESTIMATE)

# --- afirmación 38: una sola casa crea labels, y nunca crea Discovery -------------

_CREAN_LABEL = sorted(nm for nm in FUNCS if _post_con(FUNCS[nm], "issueLabelCreate"))
require_nonempty(_CREAN_LABEL,
                 "[38] ninguna función le pasa a _post una constante que contenga "
                 "issueLabelCreate; la afirmación probaría sobre el conjunto vacío")
if len(_CREAN_LABEL) != 1:
    fail("[38] issueLabelCreate tiene que salir de una sola función y sale de %s"
         % _CREAN_LABEL)
else:
    _CASA_LABEL = _CREAN_LABEL[0]
    if _CASA_LABEL not in RUTA_TICKET:
        fail("[38] la función que crea labels, %s, no es alcanzable desde el handler "
             "de ticket:create" % _CASA_LABEL)
    _OTROS_DUENOS = sorted(op for op in handler if op != "ticket:create"
                           and _CASA_LABEL in alcanzable(handler[op]))
    if _OTROS_DUENOS:
        fail("[38] la función que crea labels es alcanzable desde estos otros "
             "subcomandos: %s" % _OTROS_DUENOS)
    _NOMBRA_DISCOVERY = [n for n in ast.walk(FUNCS[_CASA_LABEL])
                         if (isinstance(n, ast.Name) and n.id == "DISCOVERY")
                         or (isinstance(n, ast.Constant) and n.value == "Discovery")]
    if _NOMBRA_DISCOVERY:
        fail("[38] la función que crea labels nombra Discovery %d veces; Discovery es "
             "del equipo, se busca y nunca se crea" % len(_NOMBRA_DISCOVERY))
    # La mitad del null: sin una comparación contra None el bucle no distingue el
    # label que falta del que ya está, y los crearía todos en cada corrida.
    if not [n for n in ast.walk(FUNCS[_CASA_LABEL]) if isinstance(n, ast.Compare)
            and any(isinstance(c, ast.Constant) and c.value is None
                    for c in n.comparators)]:
        fail("[38] la función que crea labels no compara nada contra None, así que no "
             "distingue el que falta del que ya está")

# --- afirmación 54: lo que crea son los nueve de LABELS, map:no-landing incluido --

# El cardinal NO se escribe acá y es a propósito: su casa es la celda Afirmación de la
# fila 54, y la 37 ya ata LABELS a la tabla del glosario por igualdad de conjuntos, así
# que un décimo elemento la pone roja. Lo que esta afirmación agrega es que la función
# que crea recorra esa constante y no una copia propia, y que map:no-landing esté.
if len(_CREAN_LABEL) == 1:
    _RECORRIDAS = [n.iter.id for n in ast.walk(FUNCS[_CREAN_LABEL[0]])
                   if isinstance(n, ast.For) and isinstance(n.iter, ast.Name)]
    if "LABELS" not in _RECORRIDAS:
        fail("[54] la función que crea labels no recorre LABELS, así que el conjunto "
             "que crea es una copia que nada compara: recorre %s" % _RECORRIDAS)
elif len(_CREAN_LABEL) > 1:
    fail("[54] más de una función de %s crea labels: %s" % (ADAPTER, _CREAN_LABEL))
if "map:no-landing" not in etiquetas:
    fail("[54] map:no-landing no está en LABELS, así que ticket:create no lo crea "
         "cuando falta y un aterrizaje sin trabajo se queda sin su marcador")

# --- afirmación 41: la cadena de cinco mutations de las dos resoluciones ----------


def _alcanza_mutation(st, aguja):
    """True si la sentencia, o cualquier función del módulo que su subárbol invoque
    transitivamente, le pasa a _post una constante de string que contiene la aguja. Es la
    generalización de _post_con que la 41 necesita y la 24 no necesitaba: las dos
    sentencias de red de map:write viven literalmente en el cuerpo de _intentar_escribir,
    y en cambio las cinco escrituras de una resolución viven en helpers y no en el cuerpo
    del handler."""
    if _post_con(st, aguja):
        return True
    for n in ast.walk(st):
        if isinstance(n, ast.Call) and invocado(n.func) in FUNCS:
            for nm in alcanzable(invocado(n.func)):
                if _post_con(FUNCS[nm], aguja):
                    return True
    return False


# En el orden del contrato. La lista es la afirmación: el orden de esta secuencia es lo
# que se compara, y no un conteo de llamadas a _post.
AGUJAS_41 = ["issueBatchCreate", "issueRelationCreate", "commentCreate",
             "issueUpdate", "projectUpdate"]

for _op in ("ticket:resolve", "ticket:rule-out"):
    _h = handler.get(_op)
    require_nonempty(alcanzable(_h),
                     "[41] el grafo alcanzable desde el handler de %s dio vacío; el "
                     "subparser no resuelve a ninguna función del módulo" % _op)
    _cuerpo41 = FUNCS[_h].body
    _primeros = {}
    for _aguja in AGUJAS_41:
        _indices = [i for i, st in enumerate(_cuerpo41)
                    if _alcanza_mutation(st, _aguja)]
        require_nonempty(_indices,
                         "[41] ninguna sentencia de primer nivel de %s alcanza %s; el "
                         "handler volvió a ser un stub o perdió una de sus cinco "
                         "escrituras, y la afirmación probaría cero" % (_h, _aguja))
        _primeros[_aguja] = _indices[0]
    _sec = [_primeros[a] for a in AGUJAS_41]
    # No decreciente y no estrictamente creciente: dos escrituras pueden compartir una
    # sentencia de primer nivel, y exigir estrictez prohibiría una factorización correcta
    # sin proteger nada.
    if _sec != sorted(_sec):
        fail("[41] las cinco mutations de %s no se alcanzan en el orden del contrato: "
             "%s" % (_h, dict(zip(AGUJAS_41, _sec))))
    if not _primeros["commentCreate"] < _primeros["issueUpdate"]:
        fail("[41] en %s el comentario no se alcanza estrictamente antes que el cambio "
             "de estado, y el orden inverso deja un ticket cerrado sin respuesta" % _h)
    if not (_primeros["projectUpdate"] > _primeros["commentCreate"]
            and _primeros["projectUpdate"] > _primeros["issueUpdate"]):
        fail("[41] en %s el mapa no se alcanza estrictamente después del comentario y "
             "del estado, y el mapa va siempre último" % _h)
    _corte41 = [i for i in range(min(_sec) + 1, max(_sec)) if _corta(_cuerpo41[i])]
    if _corte41:
        fail("[41] en %s estas sentencias entre la primera y la última escritura SON un "
             "retorno, un levantamiento o una salida: %s" % (_h, _corte41))

# --- afirmación 62: la asimetría de estado y de ancla entre las dos resoluciones --


def _anclas_de(nombre):
    """Las constantes de ancla que el cuerpo de una función referencia por Name. Mira el
    cuerpo y no el grafo, y eso es lo que la fila declara: depende de que los dos
    literales sigan viviendo ahí, que es justo lo que la decisión de no parametrizar un
    helper común garantiza."""
    return set(n.id for n in ast.walk(FUNCS[nombre])
               if isinstance(n, ast.Name) and n.id.startswith("ANCLA_"))


_H_RESOLVE = handler.get("ticket:resolve")
_H_RULE_OUT = handler.get("ticket:rule-out")
if _H_RESOLVE not in FUNCS or _H_RULE_OUT not in FUNCS:
    bail("[62] los subparsers de ticket:resolve y ticket:rule-out no resuelven a dos "
         "FunctionDef del módulo; la asimetría probaría sobre el conjunto vacío")
if _H_RESOLVE == _H_RULE_OUT:
    fail("[62] los dos subcomandos resuelven al mismo handler, %s, así que no hay dos "
         "cuerpos donde vivan los literales asimétricos" % _H_RESOLVE)

_ESTADOS = {_H_RESOLVE: _claves(FUNCS[_H_RESOLVE]),
            _H_RULE_OUT: _claves(FUNCS[_H_RULE_OUT])}
_ANCLAS_H = {_H_RESOLVE: _anclas_de(_H_RESOLVE),
             _H_RULE_OUT: _anclas_de(_H_RULE_OUT)}
for _h in (_H_RESOLVE, _H_RULE_OUT):
    require_nonempty(_ESTADOS[_h],
                     "[62] el cuerpo de %s no indexa ningún payload con un literal; un "
                     "helper parametrizado dejaría la afirmación probando sobre el "
                     "conjunto vacío" % _h)
    require_nonempty(_ANCLAS_H[_h],
                     "[62] el cuerpo de %s no referencia ninguna constante de ancla; "
                     "el ancla se fue al sitio de llamada y el AST ya no la ve" % _h)

# Cuatro pertenencias y cuatro no pertenencias. Tomadas en pares para que el mensaje
# diga cuál de las dos mitades se rompió.
for _h, _propio, _ajeno in ((_H_RESOLVE, "done", "canceled"),
                            (_H_RULE_OUT, "canceled", "done")):
    if _propio not in _ESTADOS[_h]:
        fail("[62] %s no indexa el ctx con el literal %s, así que no manda el estado "
             "que le toca" % (_h, _propio))
    if _ajeno in _ESTADOS[_h]:
        fail("[62] %s nombra %s, que es el estado del otro handler" % (_h, _ajeno))
for _h, _propia, _ajena in ((_H_RESOLVE, "ANCLA_DECISIONES", "ANCLA_FUERA"),
                            (_H_RULE_OUT, "ANCLA_FUERA", "ANCLA_DECISIONES")):
    if _propia not in _ANCLAS_H[_h]:
        fail("[62] %s no escribe en %s, que es su ancla" % (_h, _propia))
    if _ajena in _ANCLAS_H[_h]:
        fail("[62] %s escribe en %s, que es el ancla del otro handler" % (_h, _ajena))

# El estado se manda por su id del ctx y nunca se decide comparando contra el type de
# Linear: esa lectura es del preflight y de nadie más.
for _h in (_H_RESOLVE, _H_RULE_OUT):
    if "type" in _ESTADOS[_h]:
        fail("[62] %s nombra el campo type de un estado; el id del estado sale del ctx "
             "y ninguna de las dos rutas lo redecide" % _h)

# --- afirmación 63: la toma escribe assigneeId y ninguna otra clave --------------

_CLAIM = handler.get("ticket:claim")
if _CLAIM not in FUNCS:
    bail("[63] el subparser de ticket:claim no resuelve a ningún FunctionDef del "
         "módulo; el handler volvió a ser un stub y la afirmación probaría cero")

# Los dicts que alimentan el input de la mutation, tomados del sitio de llamada: viven
# como literales en el cuerpo del handler por decisión de diseño, y eso es lo que los
# vuelve legibles sin seguir argumentos. El dict que el handler imprime por stdout NO
# entra, y esa exclusión es la afirmación: lo que se escribe en Linear y lo que se
# reporta son dos cosas, y solo la primera es el input de un issueUpdate.
_INPUTS_CLAIM = [a for n in ast.walk(FUNCS[_CLAIM])
                 if isinstance(n, ast.Call) and invocado(n.func) == "_cambiar_estado"
                 for a in n.args if isinstance(a, ast.Dict)]
require_nonempty(_INPUTS_CLAIM,
                 "[63] ningún dict literal del cuerpo de %s llega como argumento de "
                 "_cambiar_estado; el input se arma en otro lado y la afirmación "
                 "probaría sobre el conjunto vacío" % _CLAIM)

for _d in _INPUTS_CLAIM:
    _claves_input = set(k.value for k in _d.keys
                        if isinstance(k, ast.Constant) and isinstance(k.value, str))
    if _claves_input != set(["assigneeId"]) or len(_d.keys) != 1:
        fail("[63] un input de %s lleva las claves %s y tiene que llevar assigneeId y "
             "ninguna otra" % (_CLAIM, sorted(_claves_input)))
        continue
    _valor = _d.values[0]
    if isinstance(_valor, ast.Constant) and _valor.value is None:
        continue
    # La mitad que impide que el asignado venga de un argumento: el valor no nulo es
    # una indexación del ctx con el literal viewer, y nada más que eso.
    if not (isinstance(_valor, ast.Subscript)
            and isinstance(_valor.value, ast.Name) and _valor.value.id != "args"
            and isinstance(_valor.slice, ast.Constant)
            and _valor.slice.value == "viewer"):
        fail("[63] el assigneeId no nulo de %s no sale de indexar el ctx con el "
             "literal viewer" % _CLAIM)

require_nonempty(ARGS_DE.get("ticket:claim"),
                 "[63] el subparser de ticket:claim no declara ningún add_argument que "
                 "el extractor vea; la guarda del flag de asignado probaría cero")
_FLAGS_ASIGNADO = sorted(f for f in ARGS_DE["ticket:claim"] if "assignee" in f)
if _FLAGS_ASIGNADO:
    fail("[63] el subparser de ticket:claim declara flags de asignado: %s; el asignado "
         "sale del ctx y de ningún otro lado" % _FLAGS_ASIGNADO)

if [n for n in ast.walk(FUNCS[_CLAIM])
        if isinstance(n, ast.Constant) and n.value == "stateId"]:
    fail("[63] %s nombra stateId, y la toma no cambia el estado de nada" % _CLAIM)

# El null del assigneeId es la única vía del plugin que limpia una toma, así que una
# segunda casa que lo escriba es una devolución que nadie ve. Reusa _valores_de_clave,
# que ya lee los valores de una clave literal en los dicts del cuerpo de una función.
_OTROS_NULOS = sorted(nm for nm in FUNCS if nm != _CLAIM
                      and any(isinstance(v, ast.Constant) and v.value is None
                              for v in _valores_de_clave(nm, "assigneeId")))
if _OTROS_NULOS:
    fail("[63] estas funciones aparean assigneeId con None fuera de %s: %s"
         % (_CLAIM, _OTROS_NULOS))

# --- afirmación 64: --defer-map gobierna una sola condición por handler ----------

# Mismo mecanismo que la 39b, generalizado de un subparser a dos. El BIND no ve un
# add_argument sobre un grupo mutuamente excluyente, y por eso el flag tiene prohibido
# vivir ahí: adentro de un grupo esta afirmación probaría sobre el conjunto vacío.
_ADD_DEFER = [n for n in ast.walk(ARBOL) if isinstance(n, ast.Call)
              and isinstance(n.func, ast.Attribute)
              and n.func.attr == "add_argument"
              and n.args and isinstance(n.args[0], ast.Constant)
              and n.args[0].value == "--defer-map"]
if len(_ADD_DEFER) != 2:
    fail("[64] hay %d declaraciones de --defer-map y tiene que haber dos, una por "
         "resolución" % len(_ADD_DEFER))
else:
    _SOBRE_DEFER = sorted(set(BIND.get(getattr(n.func.value, "id", ""), "?")
                              for n in _ADD_DEFER))
    if _SOBRE_DEFER != ["ticket:resolve", "ticket:rule-out"]:
        fail("[64] --defer-map se declara sobre %s y tiene que declararse sobre "
             "ticket:resolve y ticket:rule-out, y sobre ningún otro subcomando"
             % _SOBRE_DEFER)
    for _n64 in _ADD_DEFER:
        _kws64 = dict((k.arg, k.value) for k in _n64.keywords)
        _accion64 = _kws64.get("action")
        if not (isinstance(_accion64, ast.Constant)
                and _accion64.value == "store_true"):
            fail("[64] una declaración de --defer-map no lleva action=store_true, así "
                 "que el flag no es el booleano puro que la rama supone")
        _propios64 = sorted(k for k in ("required", "dest") if k in _kws64)
        if _propios64:
            fail("[64] una declaración de --defer-map lleva %s, y el flag es un "
                 "booleano puro sin ninguno de los dos" % _propios64)

for _op64 in ("ticket:resolve", "ticket:rule-out"):
    _h64 = handler.get(_op64)
    if _h64 not in FUNCS:
        fail("[64] el subparser de %s no resuelve a ningún FunctionDef del módulo; el "
             "handler volvió a ser un stub y la afirmación probaría cero" % _op64)
        continue
    _ifs64 = [n for n in ast.walk(FUNCS[_h64]) if isinstance(n, ast.If)
              and any(isinstance(x, ast.Attribute) and x.attr == "defer_map"
                      for x in ast.walk(n.test))]
    if len(_ifs64) != 1:
        fail("[64] el valor de --defer-map gobierna %d condiciones del cuerpo de %s, y "
             "tiene que gobernar exactamente una" % (len(_ifs64), _h64))
        continue
    _rama64 = _ifs64[0]
    if not any(isinstance(st, ast.Return) for st in _rama64.body):
        fail("[64] la condición de --defer-map de %s no lleva un Return de primer "
             "nivel, así que no corta antes de la escritura del mapa" % _h64)
    if _alcanza_mutation(_rama64, "projectUpdate"):
        fail("[64] la condición de --defer-map de %s alcanza projectUpdate, que es "
             "exactamente la escritura que la rama existe para saltear" % _h64)

# --- afirmación 65: la casa única del formato de la línea y del marcador ---------

# Mismo mecanismo que la 45, que ya exige que el literal 120 aparezca una sola vez en
# todo el archivo, portado a dos literales de string. Cada fila lleva el literal, la
# función que tiene que ser su única casa, y las puntas que tienen que llamarla por
# Name en vez de armar la cadena por su cuenta.
CASAS_65 = [("- %s: %s", "_linea_de_decision",
             ["_ediciones_de", "cmd_ticket_resolve"]),
            ("- %s", "_linea_de_vineta",
             ["_niebla_de", "_ediciones_de", "cmd_ticket_rule_out"])]

for _lit65, _casa65, _puntas65 in CASAS_65:
    _nodos65 = [n for n in ast.walk(ARBOL) if isinstance(n, ast.Constant)
                and isinstance(n.value, str) and n.value == _lit65]
    if len(_nodos65) != 1:
        fail("[65] el literal %r aparece %d veces en %s y tiene que aparecer una sola "
             "vez, adentro de %s" % (_lit65, len(_nodos65), ADAPTER, _casa65))
        continue
    # Identidad de nodo y no valor: es lo que ata el literal a la función que lo
    # contiene sin volver a buscarlo por texto.
    _duenos65 = sorted(nm for nm in FUNCS
                       if any(x is _nodos65[0] for x in ast.walk(FUNCS[nm])))
    if _duenos65 != [_casa65]:
        fail("[65] el literal %r vive en %s y su única casa tiene que ser %s"
             % (_lit65, _duenos65, _casa65))
        continue
    if not [n for n in ast.walk(FUNCS[_casa65]) if isinstance(n, ast.Return)
            and any(x is _nodos65[0] for x in ast.walk(n))]:
        fail("[65] %s no devuelve el literal %r, así que no es la casa que arma la "
             "cadena sino un sitio que la nombra de paso" % (_casa65, _lit65))
    _llaman65 = sorted(nm for nm in FUNCS
                       if any(isinstance(n, ast.Call) and invocado(n.func) == _casa65
                              for n in ast.walk(FUNCS[nm])))
    require_nonempty(_llaman65,
                     "[65] ninguna función de %s llama a %s por Name; la casa única "
                     "quedó sin puntas y la afirmación probaría sobre el conjunto "
                     "vacío" % (ADAPTER, _casa65))
    _faltan65 = [nm for nm in _puntas65 if nm not in _llaman65]
    if _faltan65:
        fail("[65] estas puntas no llaman a %s, así que arman la cadena por su cuenta: "
             "%s" % (_casa65, _faltan65))

# --- la ruta de work:write, raíz compartida por las tres de este change ------------

# Mismo mecanismo que la 23 y la 13: el handler real por set_defaults, el grafo por
# alcanzable(). Se define una sola vez y las tres afirmaciones de abajo la citan.
WORK_ROUTE = alcanzable(handler.get("work:write"))
require_nonempty(WORK_ROUTE,
                 "[51] el grafo alcanzable desde el handler de work:write dio vacío; "
                 "el handler volvió a ser un stub y las tres afirmaciones probarían "
                 "cero")

# --- afirmación 48: ninguna ruta de work:write agrega el label map ---------------

_WORK_CREATORS = sorted(nm for nm in WORK_ROUTE
                        if _post_con(FUNCS[nm], "issueBatchCreate"))
require_nonempty(_WORK_CREATORS,
                 "[48] ninguna función del grafo de work:write le pasa a _post una "
                 "constante que contenga issueBatchCreate; la afirmación probaría "
                 "sobre el conjunto vacío")
_WITH_LABEL_IDS = [nm for nm in _WORK_CREATORS if _valores_de_clave(nm, "labelIds")]
if _WITH_LABEL_IDS:
    fail("[48] estas rutas de creación de issues de ejecución construyen labelIds: "
         "%s" % _WITH_LABEL_IDS)
_NAME_MAP_LABEL = [nm for nm in sorted(WORK_ROUTE)
                   if any((isinstance(n, ast.Name) and n.id == "LABEL_MAPA")
                          or (isinstance(n, ast.Constant) and n.value == "map")
                          for n in ast.walk(FUNCS[nm]))]
if _NAME_MAP_LABEL:
    fail("[48] estas funciones del grafo de work:write nombran el label del mapa: "
         "%s" % _NAME_MAP_LABEL)

# --- afirmación 51: con la lista vacía no se llama a issueBatchCreate ------------

_WORK_HANDLER = handler.get("work:write")
_WORK_BODY = FUNCS[_WORK_HANDLER].body
_WORK_STATEMENT_INDEXES = [i for i, st in enumerate(_WORK_BODY)
                           if _alcanza_mutation(st, "issueBatchCreate")]
require_nonempty(_WORK_STATEMENT_INDEXES,
                 "[51] ninguna sentencia de primer nivel de %s alcanza "
                 "issueBatchCreate; el handler volvió a ser un stub o perdió su "
                 "escritura" % _WORK_HANDLER)
_UNGUARDED = [i for i in _WORK_STATEMENT_INDEXES
             if not isinstance(_WORK_BODY[i], ast.If)]
if _UNGUARDED:
    fail("[51] en %s las sentencias %s alcanzan issueBatchCreate y NO son un If, así "
         "que la llamada no está adentro de ninguna guarda"
         % (_WORK_HANDLER, _UNGUARDED))
for _i51 in _WORK_STATEMENT_INDEXES:
    if isinstance(_WORK_BODY[_i51], ast.If):
        _test51 = _WORK_BODY[_i51].test
        _guards_issues = any(
            (isinstance(n, ast.Subscript) and isinstance(n.slice, ast.Constant)
             and n.slice.value == "issues")
            or (isinstance(n, ast.Attribute) and n.attr == "issue"
                and isinstance(n.value, ast.Name) and n.value.id == "args")
            for n in ast.walk(_test51))
        if not _guards_issues:
            fail("[51] en %s la guarda de la sentencia %d no nombra la lista de "
                 "issues, ni como plan[\"issues\"] ni como args.issue, así que "
                 "guarda otra cosa" % (_WORK_HANDLER, _i51))

# --- afirmación 52: el ticket de decisión del lado issueId -----------------------

# Precedente: la 65 por atar un literal a su única casa, y la 53 por partir un
# conjunto de funciones en dos por lo que nombran.
_RELATED_CONSTS = sorted(nm for nm, value in STRCONSTS.items()
                         if "issueRelationCreate" in value
                         and "type: related" in value)
require_nonempty(_RELATED_CONSTS,
                 "[52] ninguna constante de string del módulo contiene "
                 "issueRelationCreate con type: related; la afirmación probaría "
                 "sobre el conjunto vacío")
if len(_RELATED_CONSTS) != 1:
    fail("[52] estas constantes contienen issueRelationCreate con type: related, y "
         "tiene que ser una sola: %s" % _RELATED_CONSTS)
else:
    _RELATED_CONST = _RELATED_CONSTS[0]
    # Espacios colapsados: el mismo criterio que la 65 aplicaría si mirara texto en
    # vez de identidad de nodo, acá hace falta porque la mutation es multilínea.
    _RELATED_TEXT = " ".join(STRCONSTS[_RELATED_CONST].split())
    if "issueId: $decision" not in _RELATED_TEXT:
        fail("[52] %s no aparea issueId con $decision; el ticket de decisión tiene "
             "que ir del lado issueId" % _RELATED_CONST)
    if "relatedIssueId: $trabajo" not in _RELATED_TEXT:
        fail("[52] %s no aparea relatedIssueId con $trabajo; la issue de ejecución "
             "tiene que ir del lado relatedIssueId" % _RELATED_CONST)
    _RELATED_CALLS = [n for nm in sorted(WORK_ROUTE) for n in ast.walk(FUNCS[nm])
                      if isinstance(n, ast.Call) and invocado(n.func) == "_post"
                      and n.args and isinstance(n.args[0], ast.Name)
                      and n.args[0].id == _RELATED_CONST]
    require_nonempty(_RELATED_CALLS,
                     "[52] ningún _post del grafo de work:write pasa %s como primer "
                     "argumento; la afirmación probaría sobre el conjunto vacío"
                     % _RELATED_CONST)
    for _n52 in _RELATED_CALLS:
        _dict52 = _n52.args[1] if len(_n52.args) > 1 else None
        _keys52 = sorted(k.value for k in
                         (_dict52.keys if isinstance(_dict52, ast.Dict) else [])
                         if isinstance(k, ast.Constant))
        if _keys52 != ["decision", "trabajo"]:
            fail("[52] un _post de %s pasa las claves %s, y tienen que ser "
                 "exactamente decision y trabajo" % (_RELATED_CONST, _keys52))
    _BLOCKS_IN_WORK_ROUTE = [nm for nm in sorted(WORK_ROUTE)
                            if _post_con(FUNCS[nm], "type: blocks")]
    if _BLOCKS_IN_WORK_ROUTE:
        fail("[52] estas funciones del grafo de work:write postean una constante "
             "con type: blocks: %s" % _BLOCKS_IN_WORK_ROUTE)
    _RELATED_ELSEWHERE = sorted(
        nm for _op52 in ("ticket:block", "ticket:resolve", "ticket:rule-out")
        for nm in alcanzable(handler.get(_op52))
        if _post_con(FUNCS[nm], "type: related"))
    if _RELATED_ELSEWHERE:
        fail("[52] estas funciones de ticket:block/resolve/rule-out postean una "
             "constante con type: related: %s" % _RELATED_ELSEWHERE)

# --- afirmación 69: map:write escribe bajo El colapso solo por --append-collapse -

# Precedente: la 64 por declarar un flag y resolver sobre qué subparsers se declara, la
# 65 por atar un nombre a su único sitio por identidad de nodo y por contar un literal
# por igualdad, y la 62 por los dos handlers de resolución.
_COLLAPSE_FLAG = ARGS_DE["map:write"].get("--append-collapse")
require_nonempty(_COLLAPSE_FLAG,
                 "[69] map:write no declara --append-collapse; la afirmación probaría "
                 "sobre el conjunto vacío")

# Cláusula 1: el flag es repetible y vive solo en map:write.
_collapse_kws = dict((kw.arg, kw.value) for kw in _COLLAPSE_FLAG.keywords)
_collapse_action = _collapse_kws.get("action")
if not (isinstance(_collapse_action, ast.Constant)
        and _collapse_action.value == "append"):
    fail("[69] --append-collapse no lleva action=\"append\", así que el colapso no "
         "podría escribir todos sus cortes en una sola invocación")
_COLLAPSE_DECLS = [n for n in ast.walk(ARBOL) if isinstance(n, ast.Call)
                   and isinstance(n.func, ast.Attribute)
                   and n.func.attr == "add_argument"
                   and n.args and isinstance(n.args[0], ast.Constant)
                   and n.args[0].value == "--append-collapse"]
_collapse_parsers = sorted(set(BIND.get(getattr(n.func.value, "id", ""), "?")
                               for n in _COLLAPSE_DECLS))
if _collapse_parsers != ["map:write"]:
    fail("[69] --append-collapse se declara sobre %s y tiene que declararse solo "
         "sobre map:write" % _collapse_parsers)

# Cláusula 2: el ancla sale de ANCLAS por posición y el encabezado no se reescribe.
_COLLAPSE_ASSIGNS = [n for n in ARBOL.body if isinstance(n, ast.Assign)
                     and any(isinstance(t, ast.Name) and t.id == "COLLAPSE_ANCHOR"
                             for t in n.targets)]
if len(_COLLAPSE_ASSIGNS) != 1:
    fail("[69] hay %d asignaciones de módulo a COLLAPSE_ANCHOR y tiene que haber una "
         "sola" % len(_COLLAPSE_ASSIGNS))
else:
    _collapse_value = _COLLAPSE_ASSIGNS[0].value
    _collapse_index = (_collapse_value.slice
                       if isinstance(_collapse_value, ast.Subscript) else None)
    if not (isinstance(_collapse_value, ast.Subscript)
            and isinstance(_collapse_value.value, ast.Name)
            and _collapse_value.value.id == "ANCLAS"
            and isinstance(_collapse_index, ast.Constant)
            and _collapse_index.value == 5):
        fail("[69] COLLAPSE_ANCHOR no se asigna como ANCLAS[5]; el ancla tiene que "
             "salir de la lista por posición")
_ANCHORS_LISTS = [n.value for n in ARBOL.body if isinstance(n, ast.Assign)
                  and any(isinstance(t, ast.Name) and t.id == "ANCLAS"
                          for t in n.targets)
                  and isinstance(n.value, ast.List)]
if len(_ANCHORS_LISTS) != 1 or len(_ANCHORS_LISTS[0].elts) != 6:
    fail("[69] ANCLAS no es un solo literal de lista de seis elementos")
else:
    _sixth_anchor = _ANCHORS_LISTS[0].elts[5]
    if not (isinstance(_sixth_anchor, ast.Constant)
            and _sixth_anchor.value == "El colapso"):
        fail("[69] el sexto elemento de ANCLAS no es la constante \"El colapso\"")
_COLLAPSE_HEADINGS = [n for n in ast.walk(ARBOL) if isinstance(n, ast.Constant)
                      and n.value == "El colapso"]
if len(_COLLAPSE_HEADINGS) != 1:
    fail("[69] la cadena \"El colapso\" aparece en %d constantes de %s y tiene que "
         "aparecer en una sola, la de ANCLAS" % (len(_COLLAPSE_HEADINGS), ADAPTER))

# Cláusula 3: un solo sitio de escritura, atado al flag y a las dos casas únicas.
_COLLAPSE_SITES = [n for nm in sorted(RUTA_ESCRITURA) for n in ast.walk(FUNCS[nm])
                   if isinstance(n, ast.Name) and n.id == "COLLAPSE_ANCHOR"
                   and isinstance(n.ctx, ast.Load)]
require_nonempty(_COLLAPSE_SITES,
                 "[69] ninguna función del grafo de map:write carga COLLAPSE_ANCHOR; "
                 "las cláusulas del sitio y de las resoluciones probarían sobre el "
                 "conjunto vacío")
_COLLAPSE_LOADS = [n for n in ast.walk(ARBOL) if isinstance(n, ast.Name)
                   and n.id == "COLLAPSE_ANCHOR" and isinstance(n.ctx, ast.Load)]
if len(_COLLAPSE_LOADS) != 1:
    fail("[69] COLLAPSE_ANCHOR se carga %d veces en %s y tiene que cargarse una sola, "
         "en el sitio de escritura del flag" % (len(_COLLAPSE_LOADS), ADAPTER))
elif "_ediciones_de" not in RUTA_ESCRITURA:
    fail("[69] _ediciones_de no está en el grafo de map:write, así que el sitio de "
         "escritura del colapso no es alcanzable desde el handler")
else:
    _COLLAPSE_CALLS = [n for n in ast.walk(FUNCS["_ediciones_de"])
                       if isinstance(n, ast.Call) and invocado(n.func) == "anotar"
                       and n.args and n.args[0] is _COLLAPSE_LOADS[0]]
    _COLLAPSE_LOOPS = [loop for loop in ast.walk(FUNCS["_ediciones_de"])
                       if isinstance(loop, ast.For)
                       and isinstance(loop.iter, ast.Attribute)
                       and loop.iter.attr == "append_collapse"
                       and isinstance(loop.iter.value, ast.Name)
                       and loop.iter.value.id == "args"
                       and any(c is _COLLAPSE_CALLS[0] for c in ast.walk(loop))
                       ] if _COLLAPSE_CALLS else []
    if not _COLLAPSE_CALLS:
        fail("[69] la carga de COLLAPSE_ANCHOR no está en _ediciones_de como primer "
             "argumento de una llamada a anotar")
    elif not _COLLAPSE_LOOPS:
        fail("[69] la llamada a anotar con COLLAPSE_ANCHOR no está dentro de un for "
             "sobre args.append_collapse")
    else:
        for _collapse_house in ("_validar_vineta", "_linea_de_vineta"):
            if not any(isinstance(n, ast.Call) and invocado(n.func) == _collapse_house
                       for n in ast.walk(_COLLAPSE_LOOPS[0])):
                fail("[69] el for sobre args.append_collapse no llama a %s por Name"
                     % _collapse_house)

# Cláusula 4: ninguna resolución alcanza la edición del colapso. Se camina el grafo
# alcanzable y no _ANCLAS_H, que solo junta los Name con prefijo ANCLA_ y dejaría la
# cláusula pasando siempre.
_RESOLUTION_GRAPH = alcanzable(_H_RESOLVE) | alcanzable(_H_RULE_OUT)
require_nonempty(_RESOLUTION_GRAPH,
                 "[69] el grafo alcanzable desde las dos resoluciones dio vacío; la "
                 "cláusula probaría sobre el conjunto vacío")
if "_ediciones_de" in _RESOLUTION_GRAPH:
    fail("[69] una resolución alcanza _ediciones_de, que es la edición de map:write")
_RESOLUTION_HITS = sorted(
    nm for nm in _RESOLUTION_GRAPH
    if any(isinstance(n, ast.Name) and n.id == "COLLAPSE_ANCHOR"
           for n in ast.walk(FUNCS[nm])))
if _RESOLUTION_HITS:
    fail("[69] estas funciones alcanzables desde una resolución nombran "
         "COLLAPSE_ANCHOR: %s" % _RESOLUTION_HITS)

report()
print("%s: OK - las treinta y tres afirmaciones de AST sobre %s cierran, bajo Python "
      "%d.%d.%d" % (CHECK_NAME, ADAPTER,
                    sys.version_info[0], sys.version_info[1], sys.version_info[2]))
