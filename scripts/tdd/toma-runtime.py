"""Andamio de TDD, no un check del set: vive fuera del glob scripts/check-* a
proposito, y por eso run-checks.sh no lo corre. Los cuatro desenlaces de runtime de
ticket:claim contra el transporte mockeado, escritos en rojo antes de que el subcomando
tuviera cuerpo. La fila 61 de CHECKS.md los promueve al harness de check-map.sh; hasta
entonces esta es su unica casa, y se corre con scripts/tdd/correr.sh."""
import contextlib, importlib.util, io, json, os, sys

sys.dont_write_bytecode = True

spec = importlib.util.spec_from_file_location("linear", os.environ["KP_ADAPTER"])
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

RUTA = os.path.join(os.environ["XDG_CONFIG_HOME"], "keiron-planner", "linear.key")
os.makedirs(os.path.dirname(RUTA), exist_ok=True)
with open(RUTA, "w") as fh:
    fh.write("lin_api_falsa\n")


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
            raise AssertionError("%s: el transporte se llamo %d veces y su secuencia declara %d"
                                 % (self.nombre, len(self.queries), len(self.secuencia)))
        elemento = self.secuencia[len(self.queries) - 1]
        if isinstance(elemento, Exception):
            raise elemento
        return Respuesta(json.dumps(elemento).encode("utf-8"))

    @property
    def llamadas(self):
        return len(self.queries)


CTX = json.dumps({"viewer": "v1", "team": "t1", "done": "s1", "canceled": "s2",
                  "default": "s3", "discovery": "l-d", "labels": {}})

TOMADO = {"data": {"issueUpdate": {
    "success": True,
    "issue": {"identifier": "CRM-1", "url": "https://linear.app/keiron/issue/CRM-1",
              "assignee": {"displayName": "Nombre Apellido"},
              "state": {"name": "Todo"}}}}}

SOLTADO = {"data": {"issueUpdate": {
    "success": True,
    "issue": {"identifier": "CRM-1", "url": "https://linear.app/keiron/issue/CRM-1",
              "assignee": None, "state": {"name": "Todo"}}}}}

FALLAS = []


def chequear(caso, que, obtenido, esperado):
    if obtenido != esperado:
        FALLAS.append("%s / %s: obtuve %r y esperaba %r" % (caso, que, obtenido, esperado))


def correr(nombre, argv, secuencia):
    transporte = Transporte(nombre, secuencia)
    mod.urllib.request.urlopen = transporte
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
    return rc, so.getvalue(), se.getvalue(), transporte


# caso 1: la toma feliz
n = "1-claim-feliz"
rc, out, err, tr = correr(n, ["ticket:claim", "--ctx", CTX, "--issue", "CRM-1"], [TOMADO])
chequear(n, "rc", rc, 0)
chequear(n, "llamadas al transporte", tr.llamadas, 1)
if tr.variables:
    entrada = tr.variables[0].get("input") or {}
    chequear(n, "input.assigneeId", entrada.get("assigneeId"), "v1")
    chequear(n, "sin stateId", "stateId" in entrada, False)
    chequear(n, "issue viaja como identificador", tr.variables[0].get("issue"), "CRM-1")
    chequear(n, "la query es ISSUE_UPDATE", tr.queries[0], getattr(mod, "ISSUE_UPDATE", "<no existe>"))
try:
    d = json.loads(out)
except ValueError:
    d = {}
    FALLAS.append("%s: stdout no parsea como JSON: %r" % (n, out))
chequear(n, "issue", d.get("issue"), "CRM-1")
chequear(n, "assignee", d.get("assignee"), "v1")
chequear(n, "assigneeName", d.get("assigneeName"), "Nombre Apellido")

# caso 2: la devolucion deliberada
n = "2-claim-release"
rc, out, err, tr = correr(n, ["ticket:claim", "--ctx", CTX, "--issue", "CRM-1", "--release"], [SOLTADO])
chequear(n, "rc", rc, 0)
chequear(n, "llamadas al transporte", tr.llamadas, 1)
if tr.variables:
    entrada = tr.variables[0].get("input") or {}
    chequear(n, "input.assigneeId es nulo", entrada.get("assigneeId", "AUSENTE"), None)
    chequear(n, "sin stateId", "stateId" in entrada, False)
try:
    d = json.loads(out)
except ValueError:
    d = {}
    FALLAS.append("%s: stdout no parsea como JSON: %r" % (n, out))
chequear(n, "assignee nulo", d.get("assignee", "AUSENTE"), None)
chequear(n, "assigneeName nulo", d.get("assigneeName", "AUSENTE"), None)

# caso 3: --issue vacio aborta antes de la red
n = "3-issue-vacio"
rc, out, err, tr = correr(n, ["ticket:claim", "--ctx", CTX, "--issue", "   "], [])
chequear(n, "rc", rc, mod.SIN_KEY)
chequear(n, "transporte llamado cero veces", tr.llamadas, 0)

# caso 4: viewer nulo aborta antes de la red
n = "4-viewer-nulo"
CTX_SIN_VIEWER = json.dumps({"viewer": None, "team": "t1", "done": "s1", "canceled": "s2",
                             "default": "s3", "discovery": "l-d", "labels": {}})
rc, out, err, tr = correr(n, ["ticket:claim", "--ctx", CTX_SIN_VIEWER, "--issue", "CRM-1"], [])
chequear(n, "rc", rc, mod.SIN_KEY)
chequear(n, "transporte llamado cero veces", tr.llamadas, 0)

if FALLAS:
    for f in FALLAS:
        print("FAIL - " + f)
    sys.exit(1)
print("OK - los cuatro desenlaces de ticket:claim")
