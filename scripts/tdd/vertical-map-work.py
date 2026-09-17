"""Andamio de TDD, no un check del set: vive fuera del glob scripts/check-* a
proposito. La rebanada vertical de /map-work hasta el paso 6, preflight, map:read,
frontier:query y ticket:claim, contra el transporte mockeado. Prueba que ninguna lectura
escribe y que la toma es la primera y la unica escritura de la sesion. Se corre con
scripts/tdd/correr.sh."""
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


QUERIES = []


class Transporte(object):
    def __init__(self, secuencia):
        self.secuencia = list(secuencia)
        self.n = 0

    def __call__(self, pedido, timeout=None):
        cuerpo = json.loads(pedido.data.decode("utf-8"))
        QUERIES.append((cuerpo.get("query") or "", cuerpo.get("variables") or {}))
        if self.n >= len(self.secuencia):
            raise AssertionError("el transporte se llamo de mas")
        elemento = self.secuencia[self.n]
        self.n += 1
        return Respuesta(json.dumps(elemento).encode("utf-8"))


PREFLIGHT = {"data": {
    "viewer": {"id": "u-123", "displayName": "Dev Leader"},
    "team": {"id": "t-1", "key": "CRM", "name": "CRM",
             "defaultIssueState": {"id": "s-todo", "name": "Todo"},
             "states": {"nodes": [
                 {"id": "s-todo", "name": "Todo", "type": "unstarted", "position": 0},
                 {"id": "s-done", "name": "Done", "type": "completed", "position": 1},
                 {"id": "s-canc", "name": "Canceled", "type": "canceled", "position": 2}]}},
    "issueLabels": {"nodes": [{"id": "l-%d" % i, "name": n, "team": None}
                              for i, n in enumerate(mod.LABELS + [mod.DISCOVERY])]}}}

MAPA = "\n".join(["## " + a + "\n" for a in mod.ANCLAS])
LEIDO = {"data": {"project": {"content": MAPA}}}

FRONTERA = {"data": {"project": {
    "issues": {"pageInfo": {"hasNextPage": False}, "nodes": [{
        "identifier": "CRM-3401", "title": "Una pregunta sin responder",
        "url": "https://linear.app/keiron/issue/CRM-3401",
        "createdAt": "2026-09-16T12:00:00.000Z",
        "state": {"id": "s-todo", "name": "Todo"},
        "assignee": None,
        "labels": {"nodes": [{"name": "map"}, {"name": "map:grilling"}]},
        "relations": {"pageInfo": {"hasNextPage": False}},
        "inverseRelations": {"pageInfo": {"hasNextPage": False}, "nodes": []}}]},
    "projectMilestones": {"pageInfo": {"hasNextPage": False}, "nodes": []}}}}

TOMADO = {"data": {"issueUpdate": {
    "success": True,
    "issue": {"identifier": "CRM-3401",
              "url": "https://linear.app/keiron/issue/CRM-3401",
              "assignee": {"displayName": "Dev Leader"},
              "state": {"name": "Todo"}}}}}

FALLAS = []


def chequear(que, obtenido, esperado):
    if obtenido != esperado:
        FALLAS.append("%s: obtuve %r y esperaba %r" % (que, obtenido, esperado))


def correr(argv, secuencia):
    mod.urllib.request.urlopen = Transporte(secuencia)
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
    return rc, so.getvalue(), se.getvalue()


PROJECT = "https://linear.app/keiron/project/el-mapa"

# paso 1
rc, ctx, err = correr(["preflight", "--team", "CRM"], [PREFLIGHT])
chequear("paso 1 rc", rc, 0)
ctx = ctx.strip()

# paso 2
rc, leido, err = correr(["map:read", "--project", PROJECT], [LEIDO])
chequear("paso 2 map:read rc", rc, 0)
chequear("las seis anclas estan",
         sum(1 for v in json.loads(leido)["sections"].values() if v is not None), 6)

rc, frontera, err = correr(
    ["frontier:query", "--ctx", ctx, "--project", PROJECT], [FRONTERA])
chequear("paso 2 frontier:query rc", rc, 0)
f = json.loads(frontera)
chequear("counts.takeable", f["counts"]["takeable"], 1)
chequear("counts.open", f["counts"]["open"], 1)
chequear("counts.milestones", f["counts"]["milestones"], 0)

# paso 3: el veredicto sale de esos conteos, y con un tomable es en curso y sigue.
chequear("el veredicto continua", f["counts"]["takeable"] > 0, True)

# paso 4: el primero de tickets, verbatim.
elegido = f["tickets"][0]["identifier"]
chequear("el elegido", elegido, "CRM-3401")

# paso 5: sin hitl:pm ni hitl:design el chequeo de rol no dispara.
roles = [l for l in f["tickets"][0]["labels"] if l in ("hitl:pm", "hitl:design")]
chequear("el chequeo de rol no dispara", roles, [])

# hasta aca ninguna escritura
antes = len(QUERIES)
chequear("tres lecturas antes del paso 6", antes, 3)
chequear("ninguna lectura lleva una mutation",
         [q for q, _ in QUERIES if "mutation" in q], [])

# paso 6: la toma
rc, salida, err = correr(
    ["ticket:claim", "--ctx", ctx, "--issue", elegido], [TOMADO])
chequear("paso 6 rc", rc, 0)
chequear("un solo POST mas", len(QUERIES) - antes, 1)
q, v = QUERIES[-1]
chequear("la query del paso 6 es ISSUE_UPDATE", q, mod.ISSUE_UPDATE)
chequear("es la unica mutation de la sesion",
         len([1 for qq, _ in QUERIES if "mutation" in qq]), 1)
chequear("issue viaja verbatim", v.get("issue"), "CRM-3401")
chequear("input.assigneeId es el viewer del ctx",
         (v.get("input") or {}).get("assigneeId"), json.loads(ctx)["viewer"])
chequear("sin stateId", "stateId" in (v.get("input") or {}), False)
d = json.loads(salida)
chequear("stdout issue", d.get("issue"), "CRM-3401")
chequear("stdout assignee", d.get("assignee"), "u-123")
chequear("stdout assigneeName", d.get("assigneeName"), "Dev Leader")

if FALLAS:
    for f_ in FALLAS:
        print("FAIL - " + f_)
    sys.exit(1)
print("OK - la rebanada vertical de /map-work llega al paso 6 con una sola escritura")
print("     stdout del paso 6: " + salida.strip())
