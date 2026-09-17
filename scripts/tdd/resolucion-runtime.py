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

BASE = ["ticket:resolve", "--ctx", "{}", "--project", "kp", "--issue", "CRM-1"]


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

if FALLAS:
    for f in FALLAS:
        print("FAIL - " + f)
    sys.exit(1)
print("OK - las secciones, su render y la puerta del comentario")
