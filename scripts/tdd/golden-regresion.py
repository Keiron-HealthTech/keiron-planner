"""Andamio de TDD, no un check del set: vive fuera del glob scripts/check-* a
proposito, y por eso run-checks.sh no lo corre. Tampoco lo corre scripts/tdd/correr.sh,
porque necesita una linea de base contra la cual comparar y esa linea es de un momento.

Para que sirve: probar que un refactor NO cambia el comportamiento, en vez de afirmarlo.
Por cada invocacion guarda el codigo de salida, stdout, stderr y la secuencia entera de
(query, variables) que viajo, con el transporte mockeado. Un refactor sin cambio de
conducta deja el JSON identico.

    /bin/bash -c '
    hogar="$(mktemp -d)"
    HOME="$hogar" XDG_CONFIG_HOME="$hogar/config" KP_ADAPTER=scripts/linear.py \
      /usr/bin/python3 scripts/tdd/golden-regresion.py /tmp/base.json capturar
    # ... el refactor ...
    HOME="$hogar" XDG_CONFIG_HOME="$hogar/config" KP_ADAPTER=scripts/linear.py \
      /usr/bin/python3 scripts/tdd/golden-regresion.py /tmp/base.json
    rm -rf "$hogar"'

Los 36 casos cubren map:write, map:create, ticket:create y ticket:block, con cinco
entradas doblemente invalidas escritas para delatar un reorden de las guardas: son las
unicas que pueden distinguirlo, porque fallan por dos motivos a la vez y solo se ve el
mensaje del que corre primero."""
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
    def __init__(self, secuencia):
        self.secuencia = list(secuencia)
        self.trafico = []

    def __call__(self, pedido, timeout=None):
        cuerpo = json.loads(pedido.data.decode("utf-8"))
        self.trafico.append([cuerpo.get("query") or "", cuerpo.get("variables") or {}])
        if len(self.trafico) > len(self.secuencia):
            raise AssertionError("transporte llamado de mas")
        elemento = self.secuencia[len(self.trafico) - 1]
        if isinstance(elemento, Exception):
            raise elemento
        return Respuesta(json.dumps(elemento).encode("utf-8"))


def correr(argv, secuencia):
    tr = Transporte(secuencia)
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
    return {"rc": rc, "stdout": so.getvalue(), "stderr": se.getvalue(),
            "trafico": tr.trafico}


DECISION_PREVIA = "- https://linear.app/keiron/issue/CRM-1: una decision previa"
DESTINO = "que el mapa exista"


def overview(previo=True):
    l = ["## " + mod.ANCLAS[0], "", DESTINO, ""]
    l += ["## " + mod.ANCLAS[1], ""]
    l += ["## " + mod.ANCLAS[2], "", DECISION_PREVIA, ""]
    l += ["## " + mod.ANCLAS[3], "", "- **Una niebla previa.** con su cuerpo",
          "  y una continuacion indentada", ""]
    l += ["## " + mod.ANCLAS[4], "", "- **Algo ruled out.** con cuerpo", ""]
    l += ["## " + mod.ANCLAS[5], ""]
    if previo:
        l += ["## " + mod.ANTES_DEL_MAPA, "", "prosa heredada que no se toca", ""]
    return "\n".join(l)


def leido(c):
    return {"data": {"project": {"content": c}}}


OK_W = {"data": {"projectUpdate": {"success": True}}}
NO_W = {"data": {"projectUpdate": {"success": False}}}
OK_C = {"data": {"projectCreate": {"success": True, "project": {
    "id": "p-nuevo", "url": "https://linear.app/keiron/project/p-nuevo"}}}}
LBL = lambda n: {"data": {"issueLabelCreate": {
    "success": True, "issueLabel": {"id": "l-" + n, "name": n}}}}
LOTE = {"data": {"issueBatchCreate": {"success": True, "issues": [
    {"id": "i-1", "identifier": "CRM-10", "title": "T1",
     "url": "https://linear.app/keiron/issue/CRM-10"},
    {"id": "i-2", "identifier": "CRM-11", "title": "T2",
     "url": "https://linear.app/keiron/issue/CRM-11"}]}}}
LOTE_NO = {"data": {"issueBatchCreate": {"success": False, "issues": []}}}
REL = {"data": {"issueRelationCreate": {"success": True, "issueRelation": {"id": "r-1"}}}}
REL_NO = {"data": {"issueRelationCreate": {"success": False, "issueRelation": None}}}

IDS = dict((n, "l-%d" % i) for i, n in enumerate(mod.LABELS))
CTX_LLENO = json.dumps({"viewer": "v1", "team": "t1", "done": "s1", "canceled": "s2",
                        "default": "s3", "discovery": "l-d", "labels": IDS})
FALTAN = dict(IDS)
FALTAN["hitl:design"] = None
FALTAN["map:no-landing"] = None
CTX_FALTAN = json.dumps({"viewer": "v1", "team": "t1", "done": "s1", "canceled": "s2",
                         "default": "s3", "discovery": None, "labels": FALTAN})

W = ["map:write", "--project", "kp"]
DEC = ["--append-decision", "https://linear.app/keiron/issue/CRM-2", "el gist nuevo"]

CASOS = [
    ("write-exito", W + DEC, [leido(overview()), OK_W]),
    ("write-multiple", W + DEC + [
        "--append-fog", "**Una niebla previa.** redactada de nuevo",
        "--remove-fog", "Una niebla previa.",
        "--append-out-of-scope", "**Algo que queda afuera.** con su cuerpo"],
     [leido(overview()), OK_W]),
    ("write-remove-ausente", W + DEC + ["--remove-fog", "No existe."],
     [leido(overview()), OK_W]),
    ("write-gist-120", W + ["--append-decision", "https://x", "g" * 120],
     [leido(overview()), OK_W]),
    ("write-gist-121", W + ["--append-decision", "https://x", "g" * 121], []),
    ("write-gist-vacio", W + ["--append-decision", "https://x", ""],
     [leido(overview()), OK_W]),
    ("write-gist-encabezado", W + ["--append-decision", "https://x", "## Destino"], []),
    ("write-enlace-con-espacio", W + ["--append-decision", "ht tp://x", "g"], []),
    ("write-sin-ediciones", W, []),
    # Entradas doblemente invalidas: son las unicas que pueden delatar un reorden de
    # las guardas de --append-decision, porque cada una falla por dos motivos a la vez y
    # solo se ve el mensaje del que corre primero.
    ("write-gist-salto-y-enlace-vacio",
     W + ["--append-decision", "", "un gist\ncon salto"], []),
    ("write-gist-salto-y-enlace-con-espacio",
     W + ["--append-decision", "ht tp://x", "un gist\ncon salto"], []),
    ("write-los-dos-encabezado",
     W + ["--append-decision", "## Destino", "## Notas"], []),
    ("write-gist-121-y-enlace-encabezado",
     W + ["--append-decision", "## Destino", "g" * 121], []),
    ("write-gist-121-y-gist-encabezado",
     W + ["--append-decision", "https://x", "## " + "g" * 121], []),
    ("write-success-false", W + DEC,
     [leido(overview()), NO_W, leido(overview()), NO_W]),
    ("write-expect", W + DEC + ["--expect-sections", json.dumps(
        {mod.ANCLAS[0]: "0" * 64})], [leido(overview()), OK_W]),
    ("write-fog-sin-titulo", W + ["--append-fog", "sin titulo en negrita"], []),
    ("write-oos-sin-titulo", W + ["--append-out-of-scope", "sin titulo"], []),
    ("create-adoptar", ["map:create", "--ctx", CTX_LLENO, "--destino", DESTINO,
                        "--project", "kp"], [leido("prosa previa"), OK_W]),
    ("create-nombre", ["map:create", "--ctx", CTX_LLENO, "--destino", DESTINO,
                       "--name", "El proyecto"], [OK_C]),
    ("create-destino-frontera", ["map:create", "--ctx", CTX_LLENO, "--destino",
                                 "## " + mod.ANTES_DEL_MAPA, "--name", "X"], []),
    ("ticket-happy", ["ticket:create", "--ctx", CTX_LLENO, "--project", "kp",
                      "--ticket", "T1", "C1", "map:grilling,hitl:pm",
                      "--ticket", "T2", "C2", ""], [LOTE]),
    ("ticket-labels-faltantes", ["ticket:create", "--ctx", CTX_FALTAN, "--project",
                                 "kp", "--ticket", "T1", "C1", "map:grilling"],
     [LBL("hitl:design"), LBL("map:no-landing"), LOTE]),
    ("ticket-dos-tipos", ["ticket:create", "--ctx", CTX_LLENO, "--project", "kp",
                          "--ticket", "T1", "C1", "map:grilling,map:task"], []),
    ("ticket-label-ajeno", ["ticket:create", "--ctx", CTX_LLENO, "--project", "kp",
                            "--ticket", "T1", "C1", "map"], []),
    ("ticket-vacio", ["ticket:create", "--ctx", CTX_LLENO, "--project", "kp",
                      "--ticket", "", "C1", ""], []),
    ("ticket-sin-ticket", ["ticket:create", "--ctx", CTX_LLENO, "--project", "kp"], []),
    ("ticket-ctx-roto", ["ticket:create", "--ctx", "{no json", "--project", "kp",
                         "--ticket", "T", "C", ""], []),
    ("ticket-lote-falla", ["ticket:create", "--ctx", CTX_LLENO, "--project", "kp",
                           "--ticket", "T1", "C1", ""], [LOTE_NO]),
    ("block-happy", ["ticket:block", "--block", "A", "B", "--block", "B", "C"],
     [REL, REL]),
    ("block-reciproco", ["ticket:block", "--block", "A", "B", "--block", "B", "A"], []),
    ("block-duplicado", ["ticket:block", "--block", "A", "B", "--block", "A", "B"], []),
    ("block-consigo", ["ticket:block", "--block", "A", "A"], []),
    ("block-vacio", ["ticket:block"], []),
    ("block-id-vacio", ["ticket:block", "--block", " ", "B"], []),
    ("block-falla-segundo", ["ticket:block", "--block", "A", "B", "--block", "B", "C"],
     [REL, REL_NO]),
]

salida = {}
for nombre, argv, sec in CASOS:
    salida[nombre] = correr(argv, sec)

destino = sys.argv[1]
if len(sys.argv) > 2 and sys.argv[2] == "capturar":
    with open(destino, "w") as fh:
        json.dump(salida, fh, indent=1, sort_keys=True)
    print("capturado: %d casos" % len(salida))
    sys.exit(0)

with open(destino) as fh:
    base = json.load(fh)
difs = []
for nombre in sorted(set(list(base) + list(salida))):
    if base.get(nombre) != salida.get(nombre):
        difs.append(nombre)
if difs:
    for nombre in difs:
        print("DIFIERE - " + nombre)
        print("  antes:  " + json.dumps(base.get(nombre), sort_keys=True)[:400])
        print("  ahora:  " + json.dumps(salida.get(nombre), sort_keys=True)[:400])
    sys.exit(1)
print("IDENTICO - los %d casos producen el mismo codigo, stdout, stderr y trafico"
      % len(salida))
