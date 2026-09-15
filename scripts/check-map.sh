#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

. scripts/_common.sh

# Afirmación 60.

adapter=scripts/linear.py

# Un solo trap EXIT en todo el archivo: un segundo reemplaza al primero bajo bash 3.2
# y le fuga el temporal en silencio, con el check en verde. Cada temporal lleva su
# propia variable inicializada en vacío antes del trap y su propio template, así que un
# directorio que sobreviva nombra cuál fugó.
hogar=""
limpiar() { [ -n "$hogar" ] && rm -rf "$hogar"; return 0; }
trap limpiar EXIT

# --- tercer tier: sin fuente y sin intérprete no hay nada que ejecutar ---

[ -f "$adapter" ] || bail "[60] falta $adapter; los desenlaces de runtime de las operaciones que escriben quedan sin correr"

py39=""
for cand in "${PY39:-}" python3.9 /usr/bin/python3; do
  [ -n "$cand" ] || continue
  v="$("$cand" -c 'import sys;print("%d.%d" % sys.version_info[:2])' 2>/dev/null || true)"
  if [ "$v" = "3.9" ]; then py39="$cand"; break; fi
done
require_nonempty "$py39" "[60] no hay ningún intérprete 3.9 en la cadena PY39, python3.9, /usr/bin/python3"

hogar="$(mktemp -d "${TMPDIR:-/tmp}/kp-map-hogar.XXXXXX")" || bail "[60] no se pudo crear el directorio temporal del hogar aislado"

# --- afirmación 60 --------------------------------------------------------------
# El seam es urllib.request.urlopen y NUNCA _post. Un harness que reasigne _post
# bypasea justamente el endurecimiento del transporte que estos casos ejercitan, que
# es la diferencia entre este script y check-py39.sh.

salida="$(HOME="$hogar" XDG_CONFIG_HOME="$hogar/config" KP_ADAPTER="$adapter" "$py39" - <<'PY' 2>&1 || true
import contextlib, difflib, importlib.util, io, json, os, socket, sys, urllib.error

sys.dont_write_bytecode = True

spec = importlib.util.spec_from_file_location("linear", os.environ["KP_ADAPTER"])
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

# La credencial se planta adentro del hogar aislado y se lee por la misma ruta que
# resuelve el adapter: sin aislar, el harness encontraría la key real de la máquina.
RUTA = os.path.join(os.environ["XDG_CONFIG_HOME"], "keiron-planner", "linear.key")
os.makedirs(os.path.dirname(RUTA), exist_ok=True)
with open(RUTA, "w") as fh:
    fh.write("lin_api_falsa\n")


def plano(texto):
    """Neutraliza los saltos en el EMISOR y no en cada aserción del consumidor: una
    línea del protocolo que se parte en dos deja a bash leyendo media línea."""
    return str(texto).replace("\r", " ").replace("\n", " ")


class Respuesta(object):
    """Lo justo que _post le pide al retorno de urlopen: context manager y read()."""

    def __init__(self, cuerpo):
        self.cuerpo = cuerpo

    def read(self):
        return self.cuerpo

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


class Transporte(object):
    """El seam. Consume una secuencia declarada por caso, donde cada elemento es una
    excepción a levantar o un payload a devolver; guarda la query y las variables que
    viajaron en cada POST, no solo el contenido. Una llamada más allá del final de la
    secuencia levanta AssertionError con un mensaje propio, y eso es lo que vuelve
    asertable el cero de un caso cuya secuencia está vacía."""

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
                "%s: el transporte se llamó %d veces y su secuencia declara %d"
                % (self.nombre, len(self.queries), len(self.secuencia)))
        elemento = self.secuencia[len(self.queries) - 1]
        if isinstance(elemento, Exception):
            raise elemento
        return Respuesta(json.dumps(elemento).encode("utf-8"))

    @property
    def llamadas(self):
        return len(self.queries)

    @property
    def contents(self):
        return [v["content"] for v in self.variables if "content" in v]


# --- las respuestas enlatadas ------------------------------------------------------

DECISION_PREVIA = "- https://linear.app/keiron/issue/CRM-1: una decision previa"
DECISION_NUEVA = ["--append-decision", "https://linear.app/keiron/issue/CRM-2",
                  "el gist nuevo"]
LINEA_NUEVA = "- https://linear.app/keiron/issue/CRM-2: el gist nuevo"
DESTINO = "que el mapa exista"


def overview(previo=True, notas_heredada=False):
    """El fixture de base. Los encabezados salen de las constantes del módulo y no se
    tipean: un rename del ancla dejaría el harness midiendo otra cosa en silencio."""
    l = ["## " + mod.ANCLAS[0], "", DESTINO, ""]
    l += ["## " + mod.ANCLAS[1], ""]
    l += ["## " + mod.ANCLAS[2], "", DECISION_PREVIA, ""]
    l += ["## " + mod.ANCLAS[3], "", "- **Una niebla previa.** con su cuerpo",
          "  y una continuacion indentada", ""]
    l += ["## " + mod.ANCLAS[4], "", "- **Algo ruled out.** con cuerpo", ""]
    l += ["## " + mod.ANCLAS[5], ""]
    if previo:
        l += ["## " + mod.ANTES_DEL_MAPA, "", "prosa heredada que no se toca", ""]
    if notas_heredada:
        l += ["## " + mod.ANCLAS[1], "", "nota heredada", ""]
    return "\n".join(l)


def leido(contenido):
    return {"data": {"project": {"content": contenido}}}


ESCRITO_OK = {"data": {"projectUpdate": {"success": True}}}
ESCRITO_FALSO = {"data": {"projectUpdate": {"success": False}}}
CREADO_OK = {"data": {"projectCreate": {
    "success": True,
    "project": {"id": "p-nuevo", "url": "https://linear.app/keiron/project/p-nuevo"}}}}

CTX = json.dumps({"viewer": "v1", "team": "t1", "done": "s1", "canceled": "s2",
                  "default": "s3", "discovery": "l-d", "labels": {}})

ESCRIBIR = ["map:write", "--project", "kp-falso"]
CREAR = ["map:create", "--ctx", CTX, "--destino", DESTINO]

fallas = []


def chequear(caso, que, obtenido, esperado):
    if obtenido != esperado:
        fallas.append("%s / %s: obtuve %s y esperaba %s"
                      % (caso, que, plano(obtenido), plano(esperado)))


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


def json_de(caso, texto):
    try:
        return json.loads(texto)
    except ValueError:
        fallas.append("%s: stdout no parsea como JSON" % caso)
        return {}


# --- los cinco desenlaces de map:write ---------------------------------------------

def caso_1():
    """Éxito en el primer intento. La aserción cara es que el content difiere del
    overview original en exactamente una línea agregada."""
    n = "1-exito-primer-intento"
    base = overview()
    rc, out, err, tr = correr(n, ESCRIBIR + DECISION_NUEVA, [leido(base), ESCRITO_OK])
    chequear(n, "rc", rc, 0)
    d = json_de(n, out)
    chequear(n, "written", d.get("written"), True)
    chequear(n, "attempts", d.get("attempts"), 1)
    chequear(n, "noop", d.get("noop"), [])
    chequear(n, "llamadas al transporte", tr.llamadas, 2)
    if tr.contents:
        delta = [l for l in difflib.ndiff(base.split("\n"), tr.contents[0].split("\n"))
                 if l[:1] in ("+", "-")]
        chequear(n, "lineas de delta", len(delta), 1)
        chequear(n, "la linea agregada", delta[0] if delta else "", "+ " + LINEA_NUEVA)
        nuevas = tr.contents[0].split("\n")
        if LINEA_NUEVA in nuevas and DECISION_PREVIA in nuevas:
            chequear(n, "la decision nueva va despues de la previa",
                     nuevas.index(DECISION_PREVIA) < nuevas.index(LINEA_NUEVA), True)
        chequear(n, "la frontera sigue siendo el ultimo encabezado",
                 [l for l in nuevas if l.startswith("## ")][-1],
                 "## " + mod.ANTES_DEL_MAPA)
        chequear(n, "la prosa heredada sobrevive byte a byte y en su posicion",
                 nuevas[-2:], ["prosa heredada que no se toca", ""])
    else:
        fallas.append("%s: no viajo ningun content" % n)

    # Una sola invocación con las cuatro clases de edición. Mismo desenlace —éxito en el
    # primer intento— y es donde se ven el reparto por sección, el remove antes que el
    # append, y que el marcador de viñeta reescrito por Linear sigue matcheando.
    v = n + "-multiples-ediciones"
    conasterisco = base.replace("- **Una niebla previa.**", "* **Una niebla previa.**")
    rc, out, err, tr = correr(v, ESCRIBIR + DECISION_NUEVA + [
        "--append-fog", "**Una niebla previa.** redactada de nuevo",
        "--remove-fog", "Una niebla previa.",
        "--append-out-of-scope", "algo que queda afuera"],
        [leido(conasterisco), ESCRITO_OK])
    chequear(v, "rc", rc, 0)
    chequear(v, "llamadas al transporte", tr.llamadas, 2)
    if tr.contents:
        cuerpos = mod.cortar_secciones(tr.contents[0])
        chequear(v, "la decision aterrizo en su ancla",
                 any("CRM-2" in l for l in cuerpos[mod.ANCLAS[2]]), True)
        chequear(v, "la decision NO aterrizo en la niebla",
                 any("CRM-2" in l for l in cuerpos[mod.ANCLAS[3]]), False)
        chequear(v, "la niebla nueva aterrizo en su ancla",
                 any("redactada de nuevo" in l for l in cuerpos[mod.ANCLAS[3]]), True)
        chequear(v, "el fuera de alcance aterrizo en su ancla",
                 any("algo que queda afuera" in l for l in cuerpos[mod.ANCLAS[4]]), True)
        chequear(v, "la vineta con marcador de asterisco se borro",
                 any("con su cuerpo" in l for l in cuerpos[mod.ANCLAS[3]]), False)
        chequear(v, "y su continuacion indentada tambien",
                 any("continuacion indentada" in l for l in cuerpos[mod.ANCLAS[3]]),
                 False)
        nuevas = tr.contents[0].split("\n")
        i = nuevas.index("- algo que queda afuera")
        chequear(v, "la linea en blanco antes del encabezado siguiente sobrevive",
                 nuevas[i + 1], "")

    # remove sobre un objetivo ausente: no-op con reporte, y las demas ediciones siguen.
    a = n + "-remove-ausente-es-noop"
    rc, out, err, tr = correr(a, ESCRIBIR + DECISION_NUEVA +
                              ["--remove-fog", "No existe esta niebla."],
                              [leido(base), ESCRITO_OK])
    chequear(a, "rc", rc, 0)
    chequear(a, "el titulo viaja en noop",
             json_de(a, out).get("noop"), ["No existe esta niebla."])
    chequear(a, "la otra edicion igual se escribio", len(tr.contents), 1)

    # el gist de exactamente 120 pasa; el de 121 aborta y esta en el caso 9.
    g = n + "-gist-de-120"
    rc, out, err, tr = correr(g, ESCRIBIR + ["--append-decision",
                                             "https://linear.app/x", "g" * 120],
                              [leido(base), ESCRITO_OK])
    chequear(g, "rc", rc, 0)

    # --expect-sections: ausente no reporta deriva; con deriva reporta y escribe igual.
    s0 = n + "-sin-expect-sections"
    rc, out, err, tr = correr(s0, ESCRIBIR + DECISION_NUEVA,
                              [leido(base), ESCRITO_OK])
    chequear(s0, "ninguna linea de deriva", "se movió" in err, False)
    s1 = n + "-con-deriva"
    derivadas = dict(mod.huellas(mod.cortar_secciones(base)))
    derivadas[mod.ANCLAS[0]] = "0" * 64
    derivadas[mod.ANCLAS[1]] = "0" * 64
    rc, out, err, tr = correr(s1, ESCRIBIR + DECISION_NUEVA +
                              ["--expect-sections", json.dumps(derivadas)],
                              [leido(base), ESCRITO_OK])
    chequear(s1, "rc sigue en cero", rc, 0)
    chequear(s1, "exactamente dos lineas de deriva", err.count("se movió"), 2)
    chequear(s1, "en el orden de ANCLAS",
             err.index(mod.ANCLAS[0]) < err.index(mod.ANCLAS[1]), True)
    chequear(s1, "la escritura ocurrio igual", len(tr.contents), 1)


def caso_2():
    """projectUpdate con success false y SIN errors de nivel superior. Es el caso que
    motivó el harness: sin la puerta, se reportaría éxito sobre una escritura rechazada."""
    n = "2-success-false-sin-errors"
    rc, out, err, tr = correr(n, ESCRIBIR + DECISION_NUEVA,
                              [leido(overview()), ESCRITO_FALSO,
                               leido(overview()), ESCRITO_FALSO])
    chequear(n, "rc", rc, mod.SIN_KEY)
    chequear(n, "stdout vacio", out, "")
    chequear(n, "stderr nombra success", "success" in err, True)
    chequear(n, "llamadas al transporte", tr.llamadas, 4)


def _recupera(n, boom):
    """Los casos 3 y 4: una falla de transporte en la primera llamada y el intento 2
    completo. El 4 es idéntico al 3 salvo por la excepción."""
    rc, out, err, tr = correr(n, ESCRIBIR + DECISION_NUEVA,
                              [boom, leido(overview()), ESCRITO_OK])
    chequear(n, "rc", rc, 0)
    d = json_de(n, out)
    chequear(n, "attempts", d.get("attempts"), 2)
    chequear(n, "stderr avisa del intento 1", err.count("el intento 1"), 1)
    chequear(n, "llamadas al transporte", tr.llamadas, 3)


def caso_3():
    _recupera("3-timeout-primer-intento", socket.timeout())


def caso_4():
    _recupera("4-urlerror-primer-intento",
              urllib.error.URLError("sin ruta al host"))


def caso_5():
    """La idempotencia invertida, solo en la rama del reintento, con su control."""
    n = "5-linea-ya-aplicada-en-el-reintento"
    ya = overview().replace(DECISION_PREVIA, DECISION_PREVIA + "\n" + LINEA_NUEVA)
    rc, out, err, tr = correr(n, ESCRIBIR + DECISION_NUEVA,
                              [leido(overview()), socket.timeout(),
                               leido(ya), ESCRITO_OK])
    chequear(n, "rc", rc, 0)
    d = json_de(n, out)
    chequear(n, "attempts", d.get("attempts"), 2)
    chequear(n, "stderr dice que la linea ya estaba aplicada",
             "ya estaba aplicada" in err, True)
    chequear(n, "la linea aparece una sola vez",
             tr.contents[-1].count(LINEA_NUEVA) if tr.contents else -1, 1)
    # El control, sin el cual "los duplicados siempre pasan" y "los duplicados pasan
    # solo en el reintento" son indistinguibles.
    c = n + "-CONTROL-primer-intento"
    rc, out, err, tr = correr(c, ESCRIBIR + DECISION_NUEVA, [leido(ya), ESCRITO_OK])
    chequear(c, "rc no cero", rc != 0, True)
    chequear(c, "no hubo projectUpdate", len(tr.contents), 0)

    # La familia entera de abortos posteriores a la lectura, que comparten forma con el
    # control: se leyó, se decidió no escribir, y el projectUpdate nunca salió.
    d = n + "-ABORTO-ancla-duplicada"
    doble = overview().replace("## " + mod.ANCLAS[1] + "\n",
                               "## " + mod.ANCLAS[1] + "\n\n## " + mod.ANCLAS[1] + "\n", 1)
    rc, out, err, tr = correr(d, ESCRIBIR + DECISION_NUEVA, [leido(doble), ESCRITO_OK])
    chequear(d, "rc no cero", rc != 0, True)
    chequear(d, "stderr nombra el ancla", mod.ANCLAS[1] in err, True)
    chequear(d, "no hubo projectUpdate", len(tr.contents), 0)

    f = n + "-ABORTO-ancla-ausente"
    sinfuera = overview().replace(
        "## " + mod.ANCLAS[4] + "\n\n- **Algo ruled out.** con cuerpo\n\n", "")
    rc, out, err, tr = correr(f, ESCRIBIR + ["--append-out-of-scope", "una linea"],
                              [leido(sinfuera), ESCRITO_OK])
    chequear(f, "rc no cero", rc != 0, True)
    chequear(f, "stderr nombra el ancla", mod.ANCLAS[4] in err, True)
    chequear(f, "stderr muestra el texto que iba a escribir", "una linea" in err, True)
    chequear(f, "no hubo projectUpdate", len(tr.contents), 0)

    b = n + "-ABORTO-ancla-solo-debajo-de-la-frontera"
    soloabajo = sinfuera.replace(
        "prosa heredada que no se toca\n",
        "prosa heredada que no se toca\n\n## " + mod.ANCLAS[4] + "\n\n- heredado\n")
    rc, out, err, tr = correr(b, ESCRIBIR + ["--append-out-of-scope", "una linea"],
                              [leido(soloabajo), ESCRITO_OK])
    chequear(b, "rc no cero: un ancla solo debajo de la frontera cuenta como ausente",
             rc != 0, True)
    chequear(b, "no hubo projectUpdate", len(tr.contents), 0)

    r = n + "-ABORTO-remove-que-matchea-dos"
    dosvinetas = overview().replace(
        "- **Una niebla previa.** con su cuerpo\n  y una continuacion indentada\n",
        "- **Una niebla previa.** con su cuerpo\n- **Una niebla previa.** otra vez\n")
    rc, out, err, tr = correr(r, ESCRIBIR + ["--remove-fog", "Una niebla previa."],
                              [leido(dosvinetas), ESCRITO_OK])
    chequear(r, "rc no cero", rc != 0, True)
    chequear(r, "no hubo projectUpdate", len(tr.contents), 0)


# --- los tres desenlaces de map:create ---------------------------------------------

def caso_6():
    """Adoptar un overview de prosa previa, preservándola byte a byte bajo la frontera."""
    n = "6-adoptar-preservando-la-prosa"
    previo = "prosa previa del Project\n\nun segundo parrafo\n"
    rc, out, err, tr = correr(n, CREAR + ["--project", "kp-1"],
                              [leido(previo), ESCRITO_OK])
    chequear(n, "rc", rc, 0)
    d = json_de(n, out)
    chequear(n, "created", d.get("created"), False)
    chequear(n, "url", d.get("url"), None)
    chequear(n, "tres claves y ninguna mas", sorted(d), ["created", "project", "url"])
    chequear(n, "llamadas al transporte", tr.llamadas, 2)
    if tr.contents:
        nuevas = tr.contents[0].split("\n")
        encabezados = [l for l in nuevas if l.startswith("## ")]
        chequear(n, "los seis en el orden de ANCLAS y la frontera ultima",
                 encabezados,
                 ["## " + a for a in mod.ANCLAS] + ["## " + mod.ANTES_DEL_MAPA])
        chequear(n, "el destino esta bajo su ancla",
                 nuevas[nuevas.index("## " + mod.ANCLAS[0]) + 2], DESTINO)
        corte = nuevas.index("## " + mod.ANTES_DEL_MAPA)
        chequear(n, "la prosa previa entera, verbatim y en su orden, bajo la frontera",
                 nuevas[corte + 2:], previo.split("\n"))
    else:
        fallas.append("%s: no viajo ningun content" % n)

    # Un overview vacío no hace nacer la frontera: sin prosa previa no hay nada que
    # preservar, y el documento queda con seis encabezados y ninguno más.
    v = n + "-overview-vacio"
    rc, out, err, tr = correr(v, CREAR + ["--project", "kp-1"],
                              [leido(""), ESCRITO_OK])
    chequear(v, "rc", rc, 0)
    chequear(v, "seis encabezados y ninguno mas",
             len([l for l in tr.contents[0].split("\n") if l.startswith("## ")])
             if tr.contents else -1, 6)

    # Las DOS condiciones de la guarda de adopción, por separado.
    s6 = n + "-GUARDA-las-seis-anclas"
    rc, out, err, tr = correr(s6, CREAR + ["--project", "kp-1"],
                              [leido("\n".join(mod.esqueleto("otro destino", []))),
                               ESCRITO_OK])
    chequear(s6, "rc no cero", rc != 0, True)
    chequear(s6, "no hubo projectUpdate", len(tr.contents), 0)
    f6 = n + "-GUARDA-frontera-con-rangos-vacio"
    rc, out, err, tr = correr(f6, CREAR + ["--project", "kp-1"],
                              [leido("## " + mod.ANTES_DEL_MAPA + "\nheredado\n"),
                               ESCRITO_OK])
    chequear(f6, "rc no cero: la frontera sola alcanza, con rangos vacio",
             rc != 0, True)
    chequear(f6, "no hubo projectUpdate", len(tr.contents), 0)

    # El reintento de la adopción, acotado por _ya_es_este_mapa: si el intento 1 aterrizó
    # y se perdió la respuesta, el 2 reconoce su propio mapa y NO vuelve a escribir.
    p6 = n + "-reintento-reconoce-su-propio-mapa"
    propio = "\n".join(mod.esqueleto(DESTINO, []))
    rc, out, err, tr = correr(p6, CREAR + ["--project", "kp-1"],
                              [leido("prosa\n"), socket.timeout(),
                               leido(propio), ESCRITO_OK])
    chequear(p6, "rc", rc, 0)
    chequear(p6, "tres llamadas", tr.llamadas, 3)
    chequear(p6, "no hubo un SEGUNDO projectUpdate", len(tr.contents), 1)
    a6 = n + "-reintento-sobre-un-mapa-AJENO-aborta"
    ajeno = "\n".join(mod.esqueleto("OTRO destino distinto", []))
    rc, out, err, tr = correr(a6, CREAR + ["--project", "kp-1"],
                              [leido("prosa\n"), socket.timeout(),
                               leido(ajeno), ESCRITO_OK])
    chequear(a6, "rc no cero", rc != 0, True)
    chequear(a6, "no hubo un SEGUNDO projectUpdate", len(tr.contents), 1)


def caso_7():
    """Crear cuesta un solo round trip, y su query no pide de vuelta lo que no debe."""
    n = "7-crear-en-un-solo-post"
    rc, out, err, tr = correr(n, CREAR + ["--name", "Un proyecto"], [CREADO_OK])
    chequear(n, "rc", rc, 0)
    chequear(n, "UNA sola llamada al transporte", tr.llamadas, 1)
    q = tr.queries[0] if tr.queries else ""
    chequear(n, "la query contiene projectCreate", "projectCreate" in q, True)
    chequear(n, "la query NO contiene projectUpdate", "projectUpdate" in q, False)
    chequear(n, "la query no pide el estado interno del editor",
             "content" + "State" in q, False)
    d = json_de(n, out)
    chequear(n, "created", d.get("created"), True)
    chequear(n, "project", d.get("project"), "p-nuevo")
    chequear(n, "url", d.get("url"),
             "https://linear.app/keiron/project/p-nuevo")

    # LA ASIMETRÍA. El caso mide que crear cuesta un solo POST, y acá se mide del lado
    # donde eso importa: cuando falla. Un segundo POST dejaría dos Projects hermanos con
    # el mismo nombre, y el plugin no tiene ninguna operación para deshacerlo. Se prueba
    # con las dos formas de falla, porque _post convierte la excepción en errors.
    for etiqueta, boom in (("timeout", socket.timeout()),
                           ("errors", {"errors": [{"message": "se cayo"}]})):
        a = n + "-ASIMETRIA-la-creacion-no-reintenta-" + etiqueta
        rc, out, err, tr = correr(a, CREAR + ["--name", "Un proyecto"],
                                  [boom, CREADO_OK])
        chequear(a, "rc no cero", rc != 0, True)
        chequear(a, "UNA sola llamada: no hubo un segundo projectCreate",
                 tr.llamadas, 1)
        chequear(a, "stdout vacio", out, "")
        chequear(a, "el mensaje dice que NO SE SABE", "NO SE SABE" in err, True)
        chequear(a, "nombra el --name que busco", "Un proyecto" in err, True)
        chequear(a, "pide mirar Linear antes de volver a correr", "Linear" in err, True)
        chequear(a, "NO afirma que el Project no se creo",
                 "no se creó" in err or "no se creo" in err, False)
        chequear(a, "no le echa la culpa a la credencial",
                 "credencial" in err or "/planner-setup" in err, False)


def caso_8():
    """La regresión de la frontera, y el más importante de los nueve: el map:write
    posterior corre sobre el content REAL que este map:create produjo, y no sobre un
    overview tipeado. Si fuera tipeado mediría la forma que el autor del harness CREE
    que map:create produce, que es lo que el defecto original demostró que no se puede
    asumir."""
    n = "8-adoptar-con-notas-y-escribir-despues"
    previo = "## " + mod.ANCLAS[1] + "\nnota heredada\n\nprosa suelta\n"
    rc, out, err, tr = correr(n, CREAR + ["--project", "kp-1"],
                              [leido(previo), ESCRITO_OK])
    chequear(n, "el map:create sale en cero", rc, 0)
    if not tr.contents:
        fallas.append("%s: el map:create no escribio nada" % n)
        return
    producido = tr.contents[0]
    chequear(n, "el ancla heredada aparece dos veces en el content producido",
             producido.count("## " + mod.ANCLAS[1]), 2)
    m = n + "-map-write-posterior"
    rc, out, err, tr = correr(m, ESCRIBIR + DECISION_NUEVA,
                              [leido(producido), ESCRITO_OK])
    chequear(m, "rc", rc, 0)
    chequear(m, "escribio", len(tr.contents), 1)
    chequear(m, "stderr NO dice que un ancla aparece mas de una vez",
             "aparece más de una vez" in err, False)
    if tr.contents:
        chequear(m, "la decision nueva aterrizo",
                 LINEA_NUEVA in tr.contents[0].split("\n"), True)


# --- el desenlace de validación previa ----------------------------------------------

def caso_9():
    """La guarda del encabezado sobre --destino, que es donde muerde de verdad: el
    esqueleto lo escribe crudo bajo su ancla, así que ahí el valor ES la línea. La
    aserción que importa es el CERO y no el código de salida: un rc no cero lo daría
    igual una implementación que valida después de leer, y ésa ya gastó un round trip
    sobre un argumento que nunca iba a poder escribir. La secuencia va vacía, así que
    cualquier llamada revienta con un mensaje que nombra el caso."""
    n = "9-encabezado-rechazado-antes-de-la-red"
    argv = ["map:create", "--ctx", CTX, "--destino", "## " + mod.ANTES_DEL_MAPA,
            "--project", "kp-1"]
    rc, out, err, tr = correr(n, argv, [])
    chequear(n, "rc", rc, mod.SIN_KEY)
    chequear(n, "stdout vacio", out, "")
    chequear(n, "stderr nombra el flag", "--destino" in err, True)
    chequear(n, "stderr dice que no puede ser un encabezado",
             "encabezado" in err, True)
    chequear(n, "TRANSPORTE LLAMADO CERO VECES", tr.llamadas, 0)

    # La familia entera de abortos con el transporte en cero. Todos son el mismo
    # desenlace —la validación corre antes del primer POST— y el cero es la aserción que
    # los separa de una implementación que valida después de leer.
    otros = [
        ("destino-nivel-uno",
         ["map:create", "--ctx", CTX, "--destino", "# Cualquier cosa",
          "--project", "kp-1"], mod.SIN_KEY),
        ("destino-con-salto",
         ["map:create", "--ctx", CTX, "--destino", "con\nsalto",
          "--project", "kp-1"], mod.SIN_KEY),
        ("gist-de-121",
         ESCRIBIR + ["--append-decision", "https://linear.app/x", "g" * 121],
         mod.SIN_KEY),
        ("sin-ninguna-edicion", ESCRIBIR, mod.SIN_KEY),
        ("append-out-of-scope-que-es-encabezado",
         ESCRIBIR + ["--append-out-of-scope", "## " + mod.ANTES_DEL_MAPA],
         mod.SIN_KEY),
        ("expect-sections-que-no-parsea",
         ESCRIBIR + DECISION_NUEVA + ["--expect-sections", "{no es json"],
         mod.SIN_KEY),
        ("los-dos-origenes-juntos",
         CREAR + ["--project", "kp-1", "--name", "otro"], 2),
        ("ningun-origen", CREAR, 2),
    ]
    for etiqueta, argv, esperado in otros:
        o = n + "-" + etiqueta
        rc, out, err, tr = correr(o, argv, [])
        chequear(o, "rc", rc, esperado)
        chequear(o, "TRANSPORTE LLAMADO CERO VECES", tr.llamadas, 0)


CASOS = [caso_1, caso_2, caso_3, caso_4, caso_5, caso_6, caso_7, caso_8, caso_9]
for _caso in CASOS:
    _caso()

print("casos=%d" % len(CASOS))
print("fallas=%s" % (plano(fallas) if fallas else "ninguna"))
sys.exit(1 if fallas else 0)
PY
)"

if printf '%s\n' "$salida" | /usr/bin/grep -q 'fallas=ninguna'; then
  :
else
  printf '%s\n' "$salida" | sed 's/^/  /' >&2
  fail "[60] las operaciones que escriben no distinguen sus desenlaces de runtime con el transporte mockeado"
fi

report

# El cardinal sale de la corrida y no de una palabra escrita a mano: un conteo tipeado
# acá sería una segunda casa que nadie compara contra la primera.
casos="$(printf '%s\n' "$salida" | sed -n 's/^casos=//p')"
require_nonempty "$casos" "[60] la corrida no emitió su cardinal de casos, así que el protocolo entre el intérprete y bash se movió"
plural=""
[ "$casos" = 1 ] || plural="s"
echo "$CHECK_NAME: OK - $adapter distingue $casos desenlace$plural de runtime con el transporte mockeado, sin red y sin credencial real, bajo Python $("$py39" -c 'import sys;print("%d.%d.%d" % sys.version_info[:3])')"
