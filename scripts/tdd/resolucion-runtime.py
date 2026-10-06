"""Andamio de TDD, no un check del set: vive fuera del glob scripts/check-* a
proposito, y por eso run-checks.sh no lo corre. Los desenlaces de ticket:resolve y de
ticket:rule-out contra el transporte mockeado, escritos en rojo antes del codigo que
los pone en verde. La fila 61 de CHECKS.md los promueve al harness de check-map.sh.
Se corre con scripts/tdd/correr.sh."""
import contextlib, importlib.util, io, json, os, sys

sys.dont_write_bytecode = True

spec = importlib.util.spec_from_file_location("linear", os.environ["KP_ADAPTER"])
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

RUTA = os.path.join(os.environ["XDG_CONFIG_HOME"], "keiron-planner", "linear.key")
os.makedirs(os.path.dirname(RUTA), exist_ok=True)
with open(RUTA, "w") as fh:
    fh.write("lin_api_falsa\n")

FALLAS = []


def chequear(caso, que, obtenido, esperado):
    if obtenido != esperado:
        FALLAS.append("%s / %s: obtuve %r y esperaba %r" % (caso, que, obtenido, esperado))


class Respuesta(object):
    def __init__(self, cuerpo):
        self.cuerpo = cuerpo

    def read(self):
        return self.cuerpo

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


class Transporte(object):
    """El seam es urllib.request.urlopen y nunca _post, igual que en check-map.sh."""

    def __init__(self, nombre, secuencia):
        self.nombre = nombre
        self.secuencia = list(secuencia)
        self.queries = []
        self.variables = []

    def __call__(self, pedido, timeout=None):
        cuerpo = json.loads(pedido.data.decode("utf-8"))
        self.queries.append(cuerpo.get("query") or "")
        self.variables.append(cuerpo.get("variables") or {})
        if len(self.queries) > len(self.secuencia):
            raise AssertionError(
                "%s: el transporte se llamo %d veces y su secuencia declara %d"
                % (self.nombre, len(self.queries), len(self.secuencia)))
        elemento = self.secuencia[len(self.queries) - 1]
        if isinstance(elemento, Exception):
            raise elemento
        return Respuesta(json.dumps(elemento).encode("utf-8"))

    @property
    def llamadas(self):
        return len(self.queries)


def correr(nombre, argv, secuencia):
    tr = Transporte(nombre, secuencia)
    mod.urllib.request.urlopen = tr
    so, se = io.StringIO(), io.StringIO()
    rc = 0
    try:
        with contextlib.redirect_stdout(so), contextlib.redirect_stderr(se):
            args = mod.construir_parser().parse_args(argv)
            args.func(args)
    except SystemExit as exc:
        rc = exc.code if isinstance(exc.code, int) else 1
    except AssertionError as exc:
        rc = -1
        se.write(str(exc))
    return rc, so.getvalue(), se.getvalue(), tr


def puro(nombre, argv, fn):
    """Una funcion pura de validacion, con el transporte desarmado: cualquier llamada de
    red desde acá es un AssertionError y no un POST silencioso."""
    def explota(*a, **k):
        raise AssertionError("%s: se llamo al transporte en la validacion previa" % nombre)
    mod.urllib.request.urlopen = explota
    so, se = io.StringIO(), io.StringIO()
    rc, valor = 0, None
    try:
        with contextlib.redirect_stdout(so), contextlib.redirect_stderr(se):
            valor = fn(mod.construir_parser().parse_args(argv))
    except SystemExit as exc:
        rc = exc.code if isinstance(exc.code, int) else 1
    except AssertionError as exc:
        rc = -1
        se.write(str(exc))
    return rc, valor, se.getvalue()


SEIS = ["La decisión", "Por qué", "Lo que se cayó", "Niebla graduada",
        "Tickets nuevos", "Qué corrige o empuja"]

# --gist es requerido por el parser, asi que va en la base y los casos que lo miran
# pasan el suyo despues: argparse se queda con el ultimo de una opcion no repetible.
GIST = ["--gist", "el mapa vive en el overview del Project"]
BASE = ["ticket:resolve", "--ctx", "{}", "--project", "kp",
        "--issue", "CRM-1"] + GIST


def secciones(**cambios):
    """Los seis --section completos, con la seccion que se quiera pisar o borrar."""
    cuerpos = dict((n, ["linea de " + n]) for n in SEIS)
    cuerpos.update(cambios)
    argv = []
    for n in SEIS:
        for l in cuerpos[n]:
            argv += ["--section", n, l]
    return argv


# --- la constante y su orden ------------------------------------------------------

chequear("SECCIONES", "las seis en orden", list(getattr(mod, "SECCIONES", [])), SEIS)
chequear("COMMENT_CREATE", "postea commentCreate",
         "commentCreate" in getattr(mod, "COMMENT_CREATE", ""), True)
chequear("COMMENT_CREATE", "no cita ningun enum",
         'type: "' in getattr(mod, "COMMENT_CREATE", ""), False)

# --- el render de las seis secciones ----------------------------------------------

n = "render-las-seis"
rc, cuerpo, err = puro(n, BASE + secciones(), mod._cuerpo_de_secciones)
chequear(n, "rc", rc, 0)
esperado = "\n\n".join("## %s\n\nlinea de %s" % (s, s) for s in SEIS)
chequear(n, "el cuerpo renderizado", cuerpo, esperado)

n = "render-orden-de-secciones-no-es-el-de-argv"
invertido = []
for s in reversed(SEIS):
    invertido += ["--section", s, "linea de " + s]
rc, cuerpo, err = puro(n, BASE + invertido, mod._cuerpo_de_secciones)
chequear(n, "rc", rc, 0)
chequear(n, "el orden lo pone SECCIONES y no el argv", cuerpo, esperado)

n = "render-varias-lineas-en-orden-de-argv"
rc, cuerpo, err = puro(n, BASE + secciones(**{"Por qué": ["primera", "segunda"]}),
                       mod._cuerpo_de_secciones)
chequear(n, "rc", rc, 0)
chequear(n, "las lineas de una seccion van en el orden de la linea de comandos",
         "## Por qué\n\nprimera\nsegunda" in (cuerpo or ""), True)

# --- las cuatro guardas previas a la red ------------------------------------------

n = "seccion-fuera-de-las-seis"
rc, cuerpo, err = puro(n, BASE + secciones() + ["--section", "Otra cosa", "x"],
                       mod._cuerpo_de_secciones)
chequear(n, "rc", rc, mod.SIN_KEY)
chequear(n, "nombra las seis en la remediacion",
         all(s in err for s in SEIS), True)

n = "seccion-sin-ninguna-linea"
rc, cuerpo, err = puro(n, BASE + secciones(**{"Niebla graduada": []}),
                       mod._cuerpo_de_secciones)
chequear(n, "rc", rc, mod.SIN_KEY)
chequear(n, "nombra cual falta", "Niebla graduada" in err, True)

n = "linea-con-salto"
rc, cuerpo, err = puro(n, BASE + secciones(**{"Por qué": ["con\nsalto"]}),
                       mod._cuerpo_de_secciones)
chequear(n, "rc", rc, mod.SIN_KEY)
chequear(n, "es la guarda de los saltos", "salto de línea" in err, True)

n = "linea-que-es-encabezado"
rc, cuerpo, err = puro(n, BASE + secciones(**{"Por qué": ["## Una septima"]}),
                       mod._cuerpo_de_secciones)
chequear(n, "rc", rc, mod.SIN_KEY)
chequear(n, "es la guarda del encabezado", "encabezado" in err, True)

# --- el gist, la niebla y su guarda de consistencia --------------------------------

NIEBLA_OK = {"Niebla graduada": ["se graduó Los reportes del equipo clínico."]}


def resolucion(argv):
    return puro("x", BASE + argv, mod._resolucion_de)


n = "gist-feliz"
rc, valor, err = puro(n, BASE + secciones() + GIST, mod._resolucion_de)
chequear(n, "rc", rc, 0)
chequear(n, "el gist viaja entero", (valor or {}).get("gist"), GIST[1])

n = "gist-de-121"
rc, valor, err = puro(n, BASE + secciones() + ["--gist", "g" * 121], mod._resolucion_de)
chequear(n, "rc", rc, mod.SIN_KEY)
chequear(n, "es la guarda compartida del tope", "el tope es de 120" in err, True)

n = "gist-de-120"
rc, valor, err = puro(n, BASE + secciones() + ["--gist", "g" * 120], mod._resolucion_de)
chequear(n, "rc", rc, 0)

n = "gist-vacio"
rc, valor, err = puro(n, BASE + secciones() + ["--gist", "   "], mod._resolucion_de)
chequear(n, "rc", rc, mod.SIN_KEY)

n = "gist-con-salto"
rc, valor, err = puro(n, BASE + secciones() + ["--gist", "con\nsalto"], mod._resolucion_de)
chequear(n, "rc", rc, mod.SIN_KEY)

n = "gist-que-es-encabezado"
rc, valor, err = puro(n, BASE + secciones() + ["--gist", "## Destino"], mod._resolucion_de)
chequear(n, "rc", rc, mod.SIN_KEY)

n = "remove-fog-nombrado-en-la-seccion"
rc, valor, err = puro(n, BASE + secciones(**NIEBLA_OK) + GIST +
                      ["--remove-fog", "Los reportes del equipo clínico."],
                      mod._resolucion_de)
chequear(n, "rc", rc, 0)
chequear(n, "el titulo graduado viaja",
         (valor or {}).get("graduadas"), ["Los reportes del equipo clínico."])

n = "remove-fog-sin-mencion-en-la-seccion"
rc, valor, err = puro(n, BASE + secciones() + GIST +
                      ["--remove-fog", "Los reportes del equipo clínico."],
                      mod._resolucion_de)
chequear(n, "rc", rc, mod.SIN_KEY)
chequear(n, "nombra el titulo que no aparece",
         "Los reportes del equipo clínico." in err, True)
chequear(n, "nombra la seccion que lo tendria que nombrar",
         "Niebla graduada" in err, True)

n = "append-fog-sin-titulo-en-negrita"
rc, valor, err = puro(n, BASE + secciones() + GIST +
                      ["--append-fog", "sin titulo en negrita"], mod._resolucion_de)
chequear(n, "rc", rc, mod.SIN_KEY)

n = "append-fog-con-titulo"
rc, valor, err = puro(n, BASE + secciones() + GIST +
                      ["--append-fog", "**Una niebla nueva.** con su cuerpo"],
                      mod._resolucion_de)
chequear(n, "rc", rc, 0)
chequear(n, "la vineta llega renderizada con su marcador",
         (valor or {}).get("niebla"), ["- **Una niebla nueva.** con su cuerpo"])

n = "issue-vacio"
rc, valor, err = puro(n, ["ticket:resolve", "--ctx", "{}", "--project", "kp",
                          "--issue", "  "] + secciones() + GIST, mod._resolucion_de)
chequear(n, "rc", rc, mod.SIN_KEY)

n = "ctx-roto"
rc, valor, err = puro(n, ["ticket:resolve", "--ctx", "{no json", "--project", "kp",
                          "--issue", "CRM-1"] + secciones() + GIST, mod._resolucion_de)
chequear(n, "rc", rc, mod.SIN_KEY)

# --- los tickets nuevos y su cableado por titulo -----------------------------------

T1 = ["--new-ticket", "Una pregunta nueva", "El cuerpo es la pregunta", "map:grilling"]
T2 = ["--new-ticket", "Otra pregunta", "Su cuerpo", ""]

n = "new-ticket-feliz"
rc, valor, err = puro(n, BASE + secciones() + T1 + T2, mod._resolucion_de)
chequear(n, "rc", rc, 0)
chequear(n, "los tickets llegan validados y en orden",
         (valor or {}).get("tickets"),
         [("Una pregunta nueva", "El cuerpo es la pregunta", ["map:grilling"]),
          ("Otra pregunta", "Su cuerpo", [])])

n = "new-ticket-dos-tipos"
rc, valor, err = puro(n, BASE + secciones() +
                      ["--new-ticket", "T", "C", "map:grilling,map:task"],
                      mod._resolucion_de)
chequear(n, "rc", rc, mod.SIN_KEY)
chequear(n, "es la guarda de los dos tipos", "más de un tipo" in err, True)
chequear(n, "el mensaje nombra el flag que se escribió", "--new-ticket" in err, True)

n = "new-ticket-label-ajeno"
rc, valor, err = puro(n, BASE + secciones() + ["--new-ticket", "T", "C", "map"],
                      mod._resolucion_de)
chequear(n, "rc", rc, mod.SIN_KEY)

n = "new-ticket-titulo-vacio"
rc, valor, err = puro(n, BASE + secciones() + ["--new-ticket", "  ", "C", ""],
                      mod._resolucion_de)
chequear(n, "rc", rc, mod.SIN_KEY)

n = "block-por-titulo"
rc, valor, err = puro(n, BASE + secciones() + T1 + T2 +
                      ["--block", "Una pregunta nueva", "Otra pregunta"],
                      mod._resolucion_de)
chequear(n, "rc", rc, 0)
chequear(n, "el par viaja por titulo y nunca por id",
         (valor or {}).get("pares"), [("Una pregunta nueva", "Otra pregunta")])

n = "block-titulo-inexistente"
rc, valor, err = puro(n, BASE + secciones() + T1 +
                      ["--block", "Un título que no declaré", "Una pregunta nueva"],
                      mod._resolucion_de)
chequear(n, "rc", rc, mod.SIN_KEY)
chequear(n, "nombra el titulo que no matchea",
         "Un título que no declaré" in err, True)
chequear(n, "nombra los declarados", "Una pregunta nueva" in err, True)

n = "block-titulo-ambiguo"
rc, valor, err = puro(n, BASE + secciones() + T1 +
                      ["--new-ticket", "Una pregunta nueva", "Otro cuerpo", ""] +
                      ["--block", "Una pregunta nueva", "Una pregunta nueva"],
                      mod._resolucion_de)
chequear(n, "rc", rc, mod.SIN_KEY)

n = "block-consigo-mismo"
rc, valor, err = puro(n, BASE + secciones() + T1 +
                      ["--block", "Una pregunta nueva", "Una pregunta nueva"],
                      mod._resolucion_de)
chequear(n, "rc", rc, mod.SIN_KEY)

n = "block-duplicado"
rc, valor, err = puro(n, BASE + secciones() + T1 + T2 +
                      ["--block", "Una pregunta nueva", "Otra pregunta",
                       "--block", "Una pregunta nueva", "Otra pregunta"],
                      mod._resolucion_de)
chequear(n, "rc", rc, mod.SIN_KEY)

n = "block-reciproco"
rc, valor, err = puro(n, BASE + secciones() + T1 + T2 +
                      ["--block", "Una pregunta nueva", "Otra pregunta",
                       "--block", "Otra pregunta", "Una pregunta nueva"],
                      mod._resolucion_de)
chequear(n, "rc", rc, mod.SIN_KEY)

n = "block-contra-el-ticket-que-se-cierra"
rc, valor, err = puro(n, BASE + secciones() + T1 +
                      ["--block", "Una pregunta nueva", "CRM-1"], mod._resolucion_de)
chequear(n, "rc", rc, mod.SIN_KEY)

n = "sin-ticket-ni-block-es-legitimo"
rc, valor, err = puro(n, BASE + secciones(), mod._resolucion_de)
chequear(n, "rc", rc, 0)
chequear(n, "cero tickets", (valor or {}).get("tickets"), [])
chequear(n, "cero pares", (valor or {}).get("pares"), [])

# --- la puerta de commentCreate ---------------------------------------------------

n = "comentar-exito"
mod.urllib.request.urlopen = Transporte(n, [{"data": {"commentCreate": {
    "success": True, "comment": {"id": "c-1", "url": "https://linear.app/c/1"}}}}])
ok, detalle, url = mod._comentar("CRM-1", "## x\n\ny", "k")
chequear(n, "ok", ok, True)
chequear(n, "url", url, "https://linear.app/c/1")

n = "comentar-success-false-sin-errors"
mod.urllib.request.urlopen = Transporte(
    n, [{"data": {"commentCreate": {"success": False, "comment": None}}}])
ok, detalle, url = mod._comentar("CRM-1", "x", "k")
chequear(n, "ok", ok, False)
chequear(n, "el detalle nombra success", "success" in detalle, True)


# --- las cinco escrituras de cmd_ticket_resolve -----------------------------------

NIEBLA_TITULO = "Los reportes del equipo clínico."
DECISION_PREVIA = "- https://linear.app/keiron/issue/CRM-0: una decision previa"


def overview():
    l = ["## " + mod.ANCLAS[0], "", "que el mapa exista", ""]
    l += ["## " + mod.ANCLAS[1], ""]
    l += ["## " + mod.ANCLAS[2], "", DECISION_PREVIA, ""]
    l += ["## " + mod.ANCLAS[3], "", "- **%s** todavia no se puede enunciar"
          % NIEBLA_TITULO, ""]
    l += ["## " + mod.ANCLAS[4], ""]
    l += ["## " + mod.ANCLAS[5], ""]
    l += ["## " + mod.ANTES_DEL_MAPA, "", "prosa heredada que no se toca", ""]
    return "\n".join(l)


IDS = dict((n, "l-%d" % i) for i, n in enumerate(mod.LABELS))
CTX = json.dumps({"viewer": "v1", "team": "t1", "done": "s-done",
                  "canceled": "s-canc", "default": "s-todo", "discovery": "l-d",
                  "labels": IDS})
SIN_DESIGN = dict(IDS)
SIN_DESIGN["hitl:design"] = None
CTX_SIN_DESIGN = json.dumps({"viewer": "v1", "team": "t1", "done": "s-done",
                             "canceled": "s-canc", "default": "s-todo",
                             "discovery": None, "labels": SIN_DESIGN})

LOTE = {"data": {"issueBatchCreate": {"success": True, "issues": [
    {"id": "i-1", "identifier": "CRM-10", "title": "Una pregunta nueva",
     "url": "https://linear.app/keiron/issue/CRM-10"},
    {"id": "i-2", "identifier": "CRM-11", "title": "Otra pregunta",
     "url": "https://linear.app/keiron/issue/CRM-11"}]}}}
RELACION = {"data": {"issueRelationCreate": {"success": True,
                                             "issueRelation": {"id": "r-1"}}}}
COMENTARIO = {"data": {"commentCreate": {"success": True, "comment": {
    "id": "c-1", "url": "https://linear.app/keiron/issue/CRM-1#comment-c-1"}}}}
COMENTARIO_NO = {"data": {"commentCreate": {"success": False, "comment": None}}}
URL_CERRADO = "https://linear.app/keiron/issue/CRM-1"
ESTADO = {"data": {"issueUpdate": {"success": True, "issue": {
    "identifier": "CRM-1", "url": URL_CERRADO, "assignee": {"displayName": "Dev"},
    "state": {"name": "Done"}}}}}
LEIDO = {"data": {"project": {"content": overview()}}}
ESCRITO = {"data": {"projectUpdate": {"success": True}}}
ESCRITO_NO = {"data": {"projectUpdate": {"success": False}}}

GRADUA = {"Niebla graduada": ["se graduó %s" % NIEBLA_TITULO]}
RESOLVER = ["ticket:resolve", "--ctx", CTX, "--project", "kp", "--issue", "CRM-1"]
EL_GIST = ["--gist", "el mapa vive en el overview del Project"]

n = "resolve-feliz-seis-posts"
rc, out, err, tr = correr(
    n, RESOLVER + secciones(**GRADUA) + EL_GIST + T1 + T2 +
    ["--block", "Una pregunta nueva", "Otra pregunta",
     "--remove-fog", NIEBLA_TITULO],
    [LOTE, RELACION, COMENTARIO, ESTADO, LEIDO, ESCRITO])
chequear(n, "rc", rc, 0)
chequear(n, "seis POSTs", tr.llamadas, 6)
orden = ["issueBatchCreate", "issueRelationCreate", "commentCreate", "issueUpdate",
         "project(id:", "projectUpdate"]
for i, aguja in enumerate(orden):
    chequear(n, "el POST %d lleva %s" % (i + 1, aguja),
             aguja in (tr.queries[i] if i < len(tr.queries) else ""), True)
if tr.llamadas == 6:
    cuerpo = tr.variables[2].get("body") or ""
    chequear(n, "el comentario lleva los seis encabezados en el orden de SECCIONES",
             [l[3:] for l in cuerpo.split("\n") if l.startswith("## ")], SEIS)
    chequear(n, "input.stateId es el done del ctx",
             (tr.variables[3].get("input") or {}).get("stateId"), "s-done")
    contenido = tr.variables[5].get("content") or ""
    chequear(n, "el mapa gano la linea con la url que devolvio el issueUpdate",
             ("- [CRM-1](<%s>): %s" % (URL_CERRADO, EL_GIST[1])) in contenido, True)
    chequear(n, "la decision previa sobrevive", DECISION_PREVIA in contenido, True)
    chequear(n, "el mapa perdio la vineta graduada",
             NIEBLA_TITULO in contenido, False)
    chequear(n, "la prosa heredada sobrevive",
             "prosa heredada que no se toca" in contenido, True)
    # El enum, otra vez: la query de la relacion es la constante y nada mas.
    chequear(n, "la query de la relacion es la constante, byte a byte",
             tr.queries[1], mod.ISSUE_RELATION_CREATE)
    chequear(n, "lleva el enum sin comillas", "type: blocks" in tr.queries[1], True)
    chequear(n, "y no lo cita", 'type: "' in tr.queries[1], False)
    d = json.loads(out)
    chequear(n, "stdout nombra el ticket cerrado", d.get("issue"), "CRM-1")
    chequear(n, "stdout nombra los dos tickets nuevos", len(d.get("tickets") or []), 2)

n = "resolve-sin-new-ticket-cuatro-posts"
rc, out, err, tr = correr(n, RESOLVER + secciones() + EL_GIST,
                          [COMENTARIO, ESTADO, LEIDO, ESCRITO])
chequear(n, "rc", rc, 0)
chequear(n, "cuatro POSTs exactos", tr.llamadas, 4)
chequear(n, "ningun issueBatchCreate",
         [q for q in tr.queries if "issueBatchCreate" in q], [])
chequear(n, "ningun issueRelationCreate",
         [q for q in tr.queries if "issueRelationCreate" in q], [])
chequear(n, "ningun issueLabelCreate",
         [q for q in tr.queries if "issueLabelCreate" in q], [])

TITULO_ENTREGA = "Diseño terminado: la vista de campañas"
URL_ENTREGA = "https://linear.app/keiron/issue/CRM-12"
LEIDO_CON_DISENO = {"data": {"issue": {
    "identifier": "CRM-1", "project": {"id": "kp"},
    "labels": {"nodes": [{"name": "map"}, {"name": "hitl:design"}]}}}}
LOTE_CON_ENTREGA = {"data": {"issueBatchCreate": {"success": True, "issues": [
    {"id": "i-12", "identifier": "CRM-12", "title": TITULO_ENTREGA,
     "url": URL_ENTREGA}]}}}

n = "resolve-con-entrega-de-diseno"
rc, out, err, tr = correr(
    n, RESOLVER + secciones() + EL_GIST +
    ["--design-delivery", TITULO_ENTREGA, "Decisión: CRM-1\n\n## Para qué es la vista\nx"],
    [LEIDO_CON_DISENO, LOTE_CON_ENTREGA, COMENTARIO, ESTADO, LEIDO, ESCRITO])
chequear(n, "rc", rc, 0)
chequear(n, "seis POSTs: la lectura y las cinco escrituras", tr.llamadas, 6)
if tr.llamadas == 6:
    chequear(n, "la primera es la lectura previa", tr.queries[0],
             mod.ISSUE_PROJECT_QUERY)
    chequear(n, "la entrega viaja en el issueBatchCreate",
             "issueBatchCreate" in tr.queries[1], True)
    entrada = (tr.variables[1].get("issues") or [{}])[0]
    chequear(n, "la entrega no lleva map, asi que la frontera no la ve",
             IDS["map"] in (entrada.get("labelIds") or []), False)
    chequear(n, "la entrega lleva hitl:design y map:design-delivery",
             entrada.get("labelIds"), [IDS["hitl:design"], IDS["map:design-delivery"]])
    cuerpo = tr.variables[2].get("body") or ""
    chequear(n, "el comentario nombra la entrega en Tickets nuevos",
             ("Entrega de diseño: [CRM-12](<%s>)" % URL_ENTREGA)
             in cuerpo.split("## Tickets nuevos")[-1].split("## Qué corrige")[0], True)
    d = json.loads(out)
    chequear(n, "designDelivery", (d.get("designDelivery") or {}).get("identifier"),
             "CRM-12")
    chequear(n, "tickets no la cuenta", d.get("tickets"), [])

n = "resolve-label-nulo-muere-antes-de-la-red"
rc, out, err, tr = correr(
    n, ["ticket:resolve", "--ctx", CTX_SIN_DESIGN, "--project", "kp",
        "--issue", "CRM-1"] + secciones() + EL_GIST +
    ["--new-ticket", "Una pregunta de diseño", "Su cuerpo", "hitl:design"], [])
chequear(n, "rc", rc, mod.SIN_KEY)
chequear(n, "transporte llamado cero veces", tr.llamadas, 0)
chequear(n, "nombra el label que falta", "hitl:design" in err, True)
chequear(n, "manda a map-new", "map-new" in err, True)

n = "resolve-comentario-rechazado"
rc, out, err, tr = correr(
    n, RESOLVER + secciones() + EL_GIST + T1 +
    [], [LOTE, COMENTARIO_NO])
chequear(n, "rc", rc, mod.SIN_KEY)
chequear(n, "dos POSTs", tr.llamadas, 2)
chequear(n, "dice que los tickets ya quedaron escritos",
         "tickets nuevos" in err, True)

n = "resolve-mapa-rechazado"
rc, out, err, tr = correr(
    n, RESOLVER + secciones() + EL_GIST,
    [COMENTARIO, ESTADO, LEIDO, ESCRITO_NO])
chequear(n, "rc", rc, mod.SIN_KEY)
chequear(n, "cuatro POSTs", tr.llamadas, 4)
chequear(n, "stderr imprime la invocacion de map:write",
         "map:write" in err, True)
chequear(n, "con el mismo project", "--project kp" in err, True)
chequear(n, "con el gist real", EL_GIST[1] in err, True)
chequear(n, "con la url real", URL_CERRADO in err, True)
chequear(n, "y no sugiere repetir ticket:resolve",
         "ticket:resolve" in err, False)


# --- ticket:rule-out y sus dos literales asimetricos ------------------------------

VINETA = "**Los reportes del equipo clínico.** quedaron más allá del destino"
FUERA = ["ticket:rule-out", "--ctx", CTX, "--project", "kp", "--issue", "CRM-1"]
ESTADO_CANC = {"data": {"issueUpdate": {"success": True, "issue": {
    "identifier": "CRM-1", "url": URL_CERRADO, "assignee": None,
    "state": {"name": "Canceled"}}}}}

n = "rule-out-feliz"
rc, out, err, tr = correr(n, FUERA + secciones() + ["--out-of-scope", VINETA],
                          [COMENTARIO, ESTADO_CANC, LEIDO, ESCRITO])
chequear(n, "rc", rc, 0)
chequear(n, "cuatro POSTs", tr.llamadas, 4)
if tr.llamadas == 4:
    chequear(n, "input.stateId es el canceled del ctx",
             (tr.variables[1].get("input") or {}).get("stateId"), "s-canc")
    contenido = tr.variables[3].get("content") or ""
    cuerpos = mod.cortar_secciones(contenido)
    chequear(n, "la vineta aterrizo en Fuera de alcance",
             any(VINETA in l for l in cuerpos[mod.ANCLA_FUERA]), True)
    chequear(n, "Decisiones hasta ahora quedo byte a byte igual",
             cuerpos[mod.ANCLA_DECISIONES],
             mod.cortar_secciones(overview())[mod.ANCLA_DECISIONES])
    chequear(n, "y no se colo ninguna linea de decision",
             any("CRM-1" in l for l in cuerpos[mod.ANCLA_DECISIONES]), False)

n = "rule-out-no-acepta-gist"
rc, out, err, tr = correr(n, FUERA + secciones() + ["--out-of-scope", VINETA,
                                                    "--gist", "un gist"], [])
chequear(n, "rc", rc, 2)
chequear(n, "transporte llamado cero veces", tr.llamadas, 0)

n = "rule-out-exige-out-of-scope"
rc, out, err, tr = correr(n, FUERA + secciones(), [])
chequear(n, "rc", rc, 2)

n = "rule-out-vineta-sin-titulo"
rc, out, err, tr = correr(n, FUERA + secciones() +
                          ["--out-of-scope", "sin titulo en negrita"], [])
chequear(n, "rc", rc, mod.SIN_KEY)
chequear(n, "transporte llamado cero veces", tr.llamadas, 0)

n = "rule-out-con-tickets-nuevos"
rc, out, err, tr = correr(n, FUERA + secciones() + ["--out-of-scope", VINETA] + T1 + T2 +
                          ["--block", "Una pregunta nueva", "Otra pregunta"],
                          [LOTE, RELACION, COMENTARIO, ESTADO_CANC, LEIDO, ESCRITO])
chequear(n, "rc", rc, 0)
chequear(n, "seis POSTs, la misma forma que resolve", tr.llamadas, 6)
if tr.llamadas == 6:
    chequear(n, "la query de la relacion sigue siendo la constante",
             tr.queries[1], mod.ISSUE_RELATION_CREATE)

n = "rule-out-mapa-rechazado"
rc, out, err, tr = correr(n, FUERA + secciones() + ["--out-of-scope", VINETA],
                          [COMENTARIO, ESTADO_CANC, LEIDO, ESCRITO_NO])
chequear(n, "rc", rc, mod.SIN_KEY)
chequear(n, "imprime map:write con --append-out-of-scope",
         "--append-out-of-scope" in err, True)
chequear(n, "y nunca --append-decision", "--append-decision" in err, False)

# Los dos handlers son dos funciones de nivel superior y no una parametrizada.
import ast as _ast
_arbol = _ast.parse(open(os.environ["KP_ADAPTER"]).read())
_nombres = [x.name for x in _arbol.body if isinstance(x, _ast.FunctionDef)]
chequear("asimetria", "cmd_ticket_resolve existe", "cmd_ticket_resolve" in _nombres, True)
chequear("asimetria", "cmd_ticket_rule_out existe", "cmd_ticket_rule_out" in _nombres, True)
# El snippet de verificacion de la delta spec busca un nombre que empiece con
# _resolver_ticket, y eso da un FALSO POSITIVO contra el arbol vivo: _resolver_tickets
# es la puerta de issueBatchCreate y existe desde CRM-3400. La propiedad real es que
# ninguno de los dos handlers delegue su estado ni su ancla, asi que se mide asi.
_cuerpos = dict((x.name, x) for x in _arbol.body if isinstance(x, _ast.FunctionDef))


def _llama(quien, a_quien):
    return any(isinstance(nd, _ast.Call) and getattr(nd.func, "id", None) == a_quien
               for nd in _ast.walk(_cuerpos[quien]))


def _nombra(quien, constante):
    return any(isinstance(nd, _ast.Name) and nd.id == constante
               for nd in _ast.walk(_cuerpos[quien]))


chequear("asimetria", "resolve no delega en rule-out",
         _llama("cmd_ticket_resolve", "cmd_ticket_rule_out"), False)
chequear("asimetria", "rule-out no delega en resolve",
         _llama("cmd_ticket_rule_out", "cmd_ticket_resolve"), False)
chequear("asimetria", "resolve escribe en su propia ancla",
         _nombra("cmd_ticket_resolve", "ANCLA_DECISIONES"), True)
chequear("asimetria", "y no en la del otro",
         _nombra("cmd_ticket_resolve", "ANCLA_FUERA"), False)
chequear("asimetria", "rule-out escribe en su propia ancla",
         _nombra("cmd_ticket_rule_out", "ANCLA_FUERA"), True)
chequear("asimetria", "y no en la del otro",
         _nombra("cmd_ticket_rule_out", "ANCLA_DECISIONES"), False)

if FALLAS:
    for f in FALLAS:
        print("FAIL - " + f)
    sys.exit(1)
print("OK - ticket:resolve y ticket:rule-out: guardas, escrituras y asimetria")
