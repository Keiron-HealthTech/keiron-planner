#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

. scripts/_common.sh

# Afirmaciones 60, 47, 61, 66, 73, 74 y 75.

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

# Dos acumuladores y no uno: este harness lleva los desenlaces de dos afirmaciones, y
# un [N] que no distinga cuál falló manda a leer el script equivocado. La afirmación en
# curso la fija el bucle del final, así que ningún caso puede anotar en el balde ajeno.
FALLAS = {"60": [], "47": [], "61": [], "66": [], "73": [], "74": [], "75": []}
AFIRMACION = ["60"]


def anotar(texto):
    FALLAS[AFIRMACION[0]].append(texto)


def chequear(caso, que, obtenido, esperado):
    if obtenido != esperado:
        anotar("%s / %s: obtuve %s y esperaba %s"
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
        anotar("%s: stdout no parsea como JSON" % caso)
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
        anotar("%s: no viajo ningun content" % n)

    # Una sola invocación con las cuatro clases de edición. Mismo desenlace —éxito en el
    # primer intento— y es donde se ven el reparto por sección, el remove antes que el
    # append, y que el marcador de viñeta reescrito por Linear sigue matcheando.
    v = n + "-multiples-ediciones"
    conasterisco = base.replace("- **Una niebla previa.**", "* **Una niebla previa.**")
    rc, out, err, tr = correr(v, ESCRIBIR + DECISION_NUEVA + [
        "--append-fog", "**Una niebla previa.** redactada de nuevo",
        "--remove-fog", "Una niebla previa.",
        "--append-out-of-scope", "**Algo que queda afuera.** con su cuerpo"],
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
                 any("Algo que queda afuera." in l for l in cuerpos[mod.ANCLAS[4]]),
                 True)
        chequear(v, "la vineta con marcador de asterisco se borro",
                 any("con su cuerpo" in l for l in cuerpos[mod.ANCLAS[3]]), False)
        chequear(v, "y su continuacion indentada tambien",
                 any("continuacion indentada" in l for l in cuerpos[mod.ANCLAS[3]]),
                 False)
        nuevas = tr.contents[0].split("\n")
        i = nuevas.index("- **Algo que queda afuera.** con su cuerpo")
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
    rc, out, err, tr = correr(f, ESCRIBIR + ["--append-out-of-scope", "**Una linea.** con su cuerpo"],
                              [leido(sinfuera), ESCRITO_OK])
    chequear(f, "rc no cero", rc != 0, True)
    chequear(f, "stderr nombra el ancla", mod.ANCLAS[4] in err, True)
    chequear(f, "stderr muestra el texto que iba a escribir", "Una linea." in err,
             True)
    chequear(f, "no hubo projectUpdate", len(tr.contents), 0)

    b = n + "-ABORTO-ancla-solo-debajo-de-la-frontera"
    soloabajo = sinfuera.replace(
        "prosa heredada que no se toca\n",
        "prosa heredada que no se toca\n\n## " + mod.ANCLAS[4] + "\n\n- heredado\n")
    rc, out, err, tr = correr(b, ESCRIBIR + ["--append-out-of-scope", "**Una linea.** con su cuerpo"],
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
        anotar("%s: no viajo ningun content" % n)

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
        anotar("%s: el map:create no escribio nada" % n)
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
        # Sin título en negrita la clave de unicidad de fuera de alcance dependía de
        # cómo se hubiera escrito la línea, y era el único de los tres flags así.
        ("append-out-of-scope-sin-titulo-en-negrita",
         ESCRIBIR + ["--append-out-of-scope", "texto suelto sin negrita"],
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


# --- los tres desenlaces de ticket:create que cierran la brecha de la 47 ------------
# La fila decía "prueba que el código está, no que rechace bien", y un AST no puede
# cerrar eso: hace falta runtime. El bloque no es nuevo, es éste, porque la naturaleza
# del método —runtime con el transporte mockeado— ya tiene casa y un bloque se paga
# solo cuando el método cambia de naturaleza.

LABELS_RESUELTOS = dict((n, "l-" + n) for n in mod.LABELS)
CTX_TICKET = json.dumps({"viewer": "v1", "team": "t1", "done": "s1", "canceled": "s2",
                         "default": "s3", "discovery": "l-d",
                         "labels": LABELS_RESUELTOS})
CREAR_TICKET = ["ticket:create", "--ctx", CTX_TICKET, "--project", "p-1"]
TICKETS_OK = {"data": {"issueBatchCreate": {
    "success": True,
    "issues": [{"id": "i-1", "identifier": "CRM-10", "title": "la pregunta",
                "url": "https://linear.app/keiron/issue/CRM-10"}]}}}


def _label_ids(transporte):
    """Los labelIds de la primera entrada que viajó al issueBatchCreate."""
    if not transporte.variables:
        return None
    issues = transporte.variables[0].get("issues") or []
    return issues[0].get("labelIds") if issues else None


def caso_10():
    """Dos tipos a la vez, rechazados ANTES del primer POST. Vale por el cero y no por
    el código de salida: un rc no cero lo daría igual una implementación que valida
    después de leer, y ésa ya gastó un round trip sobre una invocación que nunca iba a
    poder escribir. La secuencia va vacía, así que cualquier llamada revienta."""
    n = "10-dos-tipos-rechazados-antes-de-la-red"
    argv = CREAR_TICKET + ["--ticket", "la pregunta", "el cuerpo",
                           "map:research,map:grilling"]
    rc, out, err, tr = correr(n, argv, [])
    chequear(n, "rc", rc, mod.SIN_KEY)
    chequear(n, "stdout vacio", out, "")
    chequear(n, "stderr nombra el primer tipo", "map:research" in err, True)
    chequear(n, "stderr nombra el segundo tipo", "map:grilling" in err, True)
    chequear(n, "TRANSPORTE LLAMADO CERO VECES", tr.llamadas, 0)

    # La familia que comparte desenlace: todo lo que _tickets_de rompe antes de la red.
    otros = [
        ("sin-ningun-ticket", CREAR_TICKET),
        ("titulo-vacio", CREAR_TICKET + ["--ticket", "   ", "el cuerpo", ""]),
        ("cuerpo-vacio", CREAR_TICKET + ["--ticket", "la pregunta", "   ", ""]),
        ("titulo-con-salto", CREAR_TICKET + ["--ticket", "con\nsalto", "cuerpo", ""]),
        ("label-que-no-es-tipo-ni-rol",
         CREAR_TICKET + ["--ticket", "la pregunta", "el cuerpo", "map"]),
        ("map-no-landing-no-se-pide",
         CREAR_TICKET + ["--ticket", "la pregunta", "el cuerpo", "map:no-landing"]),
        ("ctx-que-no-parsea",
         ["ticket:create", "--ctx", "{no es json", "--project", "p-1",
          "--ticket", "la pregunta", "el cuerpo", ""]),
    ]
    for etiqueta, argv in otros:
        o = n + "-" + etiqueta
        rc, out, err, tr = correr(o, argv, [])
        chequear(o, "rc", rc, mod.SIN_KEY)
        chequear(o, "stdout vacio", out, "")
        chequear(o, "TRANSPORTE LLAMADO CERO VECES", tr.llamadas, 0)


def caso_11():
    """El control con UN solo tipo. Sin él, "rechaza siempre" y "rechaza bien" son
    indistinguibles, que es la misma lección del control obligatorio del caso 5."""
    n = "11-un-solo-tipo-se-crea"
    argv = CREAR_TICKET + ["--ticket", "la pregunta", "el cuerpo",
                           "map:grilling,hitl:pm"]
    rc, out, err, tr = correr(n, argv, [TICKETS_OK])
    chequear(n, "rc", rc, 0)
    chequear(n, "UNA sola llamada: el ctx ya trae los nueve ids", tr.llamadas, 1)
    q = tr.queries[0] if tr.queries else ""
    chequear(n, "la query contiene issueBatchCreate", "issueBatchCreate" in q, True)
    ids = _label_ids(tr)
    chequear(n, "el labelIds lleva map", "l-map" in (ids or []), True)
    chequear(n, "y el tipo declarado", "l-map:grilling" in (ids or []), True)
    chequear(n, "y el rol declarado", "l-hitl:pm" in (ids or []), True)
    chequear(n, "y Discovery, que existe en este workspace",
             "l-d" in (ids or []), True)
    chequear(n, "y NINGUN otro tipo",
             [t for t in mod.TIPOS if t != "map:grilling"
              and ("l-" + t) in (ids or [])], [])
    d = json_de(n, out)
    chequear(n, "el identifier del ticket creado",
             [t.get("identifier") for t in d.get("tickets") or []], ["CRM-10"])
    chequear(n, "createdLabels vacio: no faltaba ninguno", d.get("createdLabels"), [])


def caso_12():
    """Cero tipos es legítimo y es la señal de AFK, no un error. El otro control: sin
    él, una guarda escrita como "exactamente uno" pasaría el caso 10 y el 11 y estaría
    rechazando algo que el glosario declara válido."""
    n = "12-cero-tipos-es-AFK-y-no-un-error"
    argv = CREAR_TICKET + ["--ticket", "la pregunta", "el cuerpo", ""]
    rc, out, err, tr = correr(n, argv, [TICKETS_OK])
    chequear(n, "rc", rc, 0)
    chequear(n, "UNA sola llamada", tr.llamadas, 1)
    ids = _label_ids(tr)
    chequear(n, "el labelIds lleva map", "l-map" in (ids or []), True)
    chequear(n, "y NINGUN tipo",
             [t for t in mod.TIPOS if ("l-" + t) in (ids or [])], [])


# --- el desenlace de ticket:block que cierra la brecha del enum citado -------------
# El defecto real fue exactamente esto: la query de issueRelationCreate llevaba el
# enum citado, type: "blocks", y GraphQL rechaza ese documento por validación antes de
# escribir nada. Ni el AST ni este mismo harness lo agarraban antes: el AST no tiene
# esquema contra el cual validar un enum, y un transporte mockeado que solo mira el rc
# acepta cualquier texto de query. Este caso lee la query real que sale al POST.

TICKET_BLOCK = ["ticket:block"]
RELACION_OK = {"data": {"issueRelationCreate": {"success": True,
                                                "issueRelation": {"id": "r-1"}}}}


def caso_13():
    """El enum sin comillas y la orientación issueId/relatedIssueId, más la guarda que
    los protege: el par recíproco aborta con el transporte en cero. Los tres son el
    defecto real: la query citada no habría validado nunca contra el esquema, y una
    orientación invertida haría que un ticket bloqueado se leyera como tomable, porque
    bloqueantes_abiertos lee el bloqueante del lado issueId a través de
    inverseRelations."""
    n = "13-ticket-block-query-real-y-orientacion"
    rc, out, err, tr = correr(n, TICKET_BLOCK + ["--block", "CRM-1", "CRM-2"],
                              [RELACION_OK])
    chequear(n, "rc", rc, 0)
    chequear(n, "UNA sola llamada al transporte", tr.llamadas, 1)
    q = tr.queries[0] if tr.queries else ""
    chequear(n, "la query contiene issueRelationCreate", "issueRelationCreate" in q,
             True)
    chequear(n, "el enum va sin comillas", "type: blocks" in q, True)
    chequear(n, "el enum NUNCA va citado", 'type: "blocks"' in q, False)
    chequear(n, "issueId mapea a la variable del bloqueante",
             "issueId: $bloqueante" in q, True)
    chequear(n, "relatedIssueId mapea a la variable del bloqueado",
             "relatedIssueId: $bloqueado" in q, True)
    variables = tr.variables[0] if tr.variables else {}
    chequear(n, "el bloqueante viajo con el id que se paso primero",
             variables.get("bloqueante"), "CRM-1")
    chequear(n, "el bloqueado viajo con el id que se paso segundo",
             variables.get("bloqueado"), "CRM-2")
    d = json_de(n, out)
    chequear(n, "el stdout preserva la orientacion",
             d.get("blocks"), [{"blocker": "CRM-1", "blocked": "CRM-2"}])

    # Sin esta guarda, --block A B seguido de --block B A escribe dos
    # issueRelationCreate independientes y dos tickets se bloquean mutuamente para
    # siempre. La secuencia va vacía, así que cualquier llamada al transporte revienta
    # con un mensaje que nombra el caso: eso es lo que hace asertable el cero.
    r = n + "-CONTROL-par-reciproco-aborta-antes-de-la-red"
    rc, out, err, tr = correr(r, TICKET_BLOCK + ["--block", "CRM-1", "CRM-2",
                                                 "--block", "CRM-2", "CRM-1"], [])
    chequear(r, "rc", rc, mod.SIN_KEY)
    chequear(r, "stdout vacio", out, "")
    chequear(r, "TRANSPORTE LLAMADO CERO VECES", tr.llamadas, 0)



# --- los once desenlaces de las tres operaciones que cierran un ticket -------------
# Mismo aparato que la 60 y la 47, en el mismo harness: el seam es
# mod.urllib.request.urlopen y nunca mod._post, así que el endurecimiento del transporte
# corre de verdad. Lo que estos once agregan sobre el AST es todo lo que el AST no puede
# ver: el ORDEN real en que salen las queries, el markdown que el adapter renderiza, el
# content que viaja al mapa, y el cero del transporte en las abortadas antes de la red.

SEIS = list(mod.SECCIONES)
GRADUADA = "Una niebla previa."
# CRM-5 y no CRM-1: el overview del fixture ya lleva una linea de decision con la url
# de CRM-1, y resolver ese mismo ticket dejaria una asercion de "no se colo ninguna
# linea nueva" midiendo la linea vieja en vez de la que este caso vigila.
RESOLVER = ["ticket:resolve", "--ctx", CTX_TICKET, "--project", "p-1",
            "--issue", "CRM-5"]
FUERA = ["ticket:rule-out", "--ctx", CTX_TICKET, "--project", "p-1",
         "--issue", "CRM-5"]
GIST = ["--gist", "el mapa vive en el overview del Project"]
VINETA_FUERA = "**Los reportes del equipo clinico.** quedaron mas alla del destino"
NUEVOS = ["--new-ticket", "Una pregunta nueva", "El cuerpo es la pregunta",
          "map:grilling",
          "--new-ticket", "Otra pregunta", "Su cuerpo", ""]
CABLE = ["--block", "Una pregunta nueva", "Otra pregunta"]
URL_CERRADO = "https://linear.app/keiron/issue/CRM-5"


def secciones(**cambios):
    """Los seis --section completos, con la sección que se quiera pisar o vaciar. Las
    seis son obligatorias, así que el caso de la sección vacía se arma borrando una."""
    cuerpos = dict((n, ["linea de " + n]) for n in SEIS)
    cuerpos.update(cambios)
    argv = []
    for n in SEIS:
        for l in cuerpos[n]:
            argv += ["--section", n, l]
    return argv


URL_TOMADO = "https://linear.app/keiron/issue/CRM-1"
TOMADO = {"data": {"issueUpdate": {"success": True, "issue": {
    "identifier": "CRM-1", "url": URL_TOMADO,
    "assignee": {"displayName": "Dev Leader"}, "state": {"name": "Todo"}}}}}
SOLTADO = {"data": {"issueUpdate": {"success": True, "issue": {
    "identifier": "CRM-1", "url": URL_TOMADO, "assignee": None,
    "state": {"name": "Todo"}}}}}
CERRADO = {"data": {"issueUpdate": {"success": True, "issue": {
    "identifier": "CRM-5", "url": URL_CERRADO, "assignee": None,
    "state": {"name": "Done"}}}}}
CANCELADO = {"data": {"issueUpdate": {"success": True, "issue": {
    "identifier": "CRM-5", "url": URL_CERRADO, "assignee": None,
    "state": {"name": "Canceled"}}}}}
NUEVOS_OK = {"data": {"issueBatchCreate": {"success": True, "issues": [
    {"id": "i-1", "identifier": "CRM-10", "title": "Una pregunta nueva",
     "url": "https://linear.app/keiron/issue/CRM-10"},
    {"id": "i-2", "identifier": "CRM-11", "title": "Otra pregunta",
     "url": "https://linear.app/keiron/issue/CRM-11"}]}}}
COMENTADO = {"data": {"commentCreate": {"success": True, "comment": {
    "id": "c-1", "url": URL_CERRADO + "#comment-c-1"}}}}
COMENTADO_FALSO = {"data": {"commentCreate": {"success": False, "comment": None}}}
CIERRE_FALSO = {"data": {"issueUpdate": {"success": False, "issue": None}}}


def caso_14():
    """La toma: un solo write, y escribe assigneeId y ninguna otra clave."""
    n = "14-ticket-claim-toma"
    rc, out, err, tr = correr(n, ["ticket:claim", "--ctx", CTX_TICKET,
                                  "--issue", "CRM-1"], [TOMADO])
    chequear(n, "rc", rc, 0)
    chequear(n, "UNA sola llamada al transporte", tr.llamadas, 1)
    entrada = (tr.variables[0] if tr.variables else {}).get("input") or {}
    chequear(n, "input.assigneeId es el viewer del ctx", entrada.get("assigneeId"), "v1")
    chequear(n, "sin la clave stateId", "stateId" in entrada, False)
    chequear(n, "el issue viaja por su identificador",
             (tr.variables[0] if tr.variables else {}).get("issue"), "CRM-1")
    d = json_de(n, out)
    chequear(n, "stdout issue", d.get("issue"), "CRM-1")
    chequear(n, "stdout assignee", d.get("assignee"), "v1")
    chequear(n, "stdout assigneeName", d.get("assigneeName"), "Dev Leader")

    # Las dos guardas previas: sin ticket y sin viewer, las dos con el transporte en cero.
    for sufijo, argv in (
            ("issue-vacio", ["ticket:claim", "--ctx", CTX_TICKET, "--issue", "  "]),
            ("viewer-nulo", ["ticket:claim", "--ctx", json.dumps(
                {"viewer": None, "team": "t1", "done": "s1", "canceled": "s2",
                 "default": "s3", "discovery": None, "labels": LABELS_RESUELTOS}),
                "--issue", "CRM-1"])):
        g = n + "-CONTROL-" + sufijo
        rc, out, err, tr = correr(g, argv, [])
        chequear(g, "rc", rc, mod.SIN_KEY)
        chequear(g, "TRANSPORTE LLAMADO CERO VECES", tr.llamadas, 0)


def caso_15():
    """La devolución deliberada. Que sea la ÚNICA ruta del archivo que deja un
    assigneeId nulo lo prueba la afirmación 63 por AST, y acá no se copia: este caso
    prueba lo que el AST no ve, que el null viaja de verdad en el input del POST."""
    n = "15-ticket-claim-release"
    rc, out, err, tr = correr(n, ["ticket:claim", "--ctx", CTX_TICKET,
                                  "--issue", "CRM-1", "--release"], [SOLTADO])
    chequear(n, "rc", rc, 0)
    chequear(n, "UNA sola llamada al transporte", tr.llamadas, 1)
    entrada = (tr.variables[0] if tr.variables else {}).get("input") or {}
    chequear(n, "input.assigneeId viajo NULO", entrada.get("assigneeId", "AUSENTE"),
             None)
    chequear(n, "la clave esta presente y no ausente", "assigneeId" in entrada, True)
    chequear(n, "sin la clave stateId", "stateId" in entrada, False)
    d = json_de(n, out)
    chequear(n, "stdout assignee nulo", d.get("assignee", "AUSENTE"), None)
    chequear(n, "stdout assigneeName nulo", d.get("assigneeName", "AUSENTE"), None)


def caso_16():
    """La resolución entera: seis POSTs en el orden del contrato, el markdown que el
    adapter renderiza, y el content que viaja al mapa con la url que devolvió el propio
    issueUpdate. Es el caso que el AST no puede cubrir: el orden real y el texto."""
    n = "16-ticket-resolve-seis-posts-en-orden"
    base = overview()
    rc, out, err, tr = correr(
        n, RESOLVER + secciones(**{SEIS[3]: ["se graduo " + GRADUADA]}) + GIST +
        NUEVOS + CABLE + ["--remove-fog", GRADUADA],
        [NUEVOS_OK, RELACION_OK, COMENTADO, CERRADO, leido(base), ESCRITO_OK])
    chequear(n, "rc", rc, 0)
    chequear(n, "SEIS llamadas al transporte", tr.llamadas, 6)
    esperado = ["issueBatchCreate", "issueRelationCreate", "commentCreate",
                "issueUpdate", "project(id:", "projectUpdate"]
    for i, aguja in enumerate(esperado):
        chequear(n, "el POST %d lleva %s" % (i + 1, aguja),
                 aguja in (tr.queries[i] if i < len(tr.queries) else ""), True)
    if tr.llamadas != 6:
        return
    cuerpo = tr.variables[2].get("body") or ""
    chequear(n, "el comentario lleva los seis encabezados en el orden de SECCIONES",
             [l[3:] for l in cuerpo.split("\n") if l.startswith("## ")], SEIS)
    chequear(n, "y ninguno de mas", cuerpo.count("## "), 6)
    chequear(n, "el comentario va al issue por su identificador",
             tr.variables[2].get("issue"), "CRM-5")
    entrada = tr.variables[3].get("input") or {}
    chequear(n, "input.stateId es el done del ctx", entrada.get("stateId"), "s1")
    chequear(n, "y no lleva assigneeId", "assigneeId" in entrada, False)
    contenido = tr.variables[5].get("content") or ""
    cuerpos = mod.cortar_secciones(contenido)
    linea = "- %s: %s" % (URL_CERRADO, GIST[1])
    chequear(n, "el mapa gano la linea con la url que devolvio el issueUpdate",
             linea in cuerpos[mod.ANCLA_DECISIONES], True)
    chequear(n, "la decision previa sobrevive",
             DECISION_PREVIA in cuerpos[mod.ANCLA_DECISIONES], True)
    chequear(n, "el mapa perdio la vineta graduada",
             any(GRADUADA in l for l in cuerpos[mod.ANCLA_NIEBLA]), False)
    chequear(n, "y su continuacion indentada tambien",
             any("continuacion indentada" in l for l in cuerpos[mod.ANCLA_NIEBLA]),
             False)
    chequear(n, "la prosa heredada bajo la frontera sobrevive",
             contenido.split("\n")[-2:], ["prosa heredada que no se toca", ""])
    d = json_de(n, out)
    chequear(n, "stdout nombra los dos tickets nuevos", len(d.get("tickets") or []), 2)
    chequear(n, "stdout nombra el par cableado",
             d.get("blocks"), [{"blocker": "i-1", "blocked": "i-2"}])


def caso_17():
    """Sin --new-ticket: CUATRO POSTs exactos. La guarda del batch vacío, que es la
    misma razón por la que la fila 51 se la pide a work:write."""
    n = "17-ticket-resolve-sin-tickets-nuevos"
    rc, out, err, tr = correr(n, RESOLVER + secciones() + GIST,
                              [COMENTADO, CERRADO, leido(overview()), ESCRITO_OK])
    chequear(n, "rc", rc, 0)
    chequear(n, "CUATRO llamadas al transporte", tr.llamadas, 4)
    for prohibida in ("issueBatchCreate", "issueRelationCreate", "issueLabelCreate"):
        chequear(n, "ninguna query lleva " + prohibida,
                 [q for q in tr.queries if prohibida in q], [])


def caso_18():
    """Una de las seis secciones sin ninguna línea: aborta ANTES de la red, nombrando
    cuál falta. Es lo que vuelve mecánicamente imposible saltearse la graduación de
    niebla sin decirlo, porque el negativo hay que escribirlo a mano."""
    n = "18-seccion-vacia-aborta-antes-de-la-red"
    rc, out, err, tr = correr(n, RESOLVER + secciones(**{SEIS[3]: []}) + GIST, [])
    chequear(n, "rc", rc, mod.SIN_KEY)
    chequear(n, "stdout vacio", out, "")
    chequear(n, "stderr nombra la seccion que falta", SEIS[3] in err, True)
    chequear(n, "TRANSPORTE LLAMADO CERO VECES", tr.llamadas, 0)


def caso_19():
    """El comentario rechazado con success false y SIN errors de nivel superior: TRES
    POSTs, y el mensaje dice qué quedó escrito. Sin la puerta de tres casos esto se
    reportaría como éxito sobre un comentario que Linear no escribió."""
    n = "19-comentario-rechazado"
    rc, out, err, tr = correr(n, RESOLVER + secciones() + GIST + NUEVOS + CABLE,
                              [NUEVOS_OK, RELACION_OK, COMENTADO_FALSO])
    chequear(n, "rc", rc, mod.SIN_KEY)
    chequear(n, "stdout vacio", out, "")
    chequear(n, "TRES llamadas al transporte", tr.llamadas, 3)
    chequear(n, "stderr nombra success", "success" in err, True)
    chequear(n, "stderr dice que los tickets ya quedaron escritos",
             "tickets nuevos" in err, True)


def caso_20():
    """La quinta escritura falla: SEIS POSTs, y la remediación imprime la invocación de
    map:write que falta, con el mismo project, la url real y el gist. Es la mejor
    remediación del archivo y es la razón por la que la quinta no reintenta."""
    n = "20-el-mapa-falla-e-imprime-el-map-write"
    rc, out, err, tr = correr(
        n, RESOLVER + secciones(**{SEIS[3]: ["se graduo " + GRADUADA]}) + GIST +
        NUEVOS + CABLE + ["--remove-fog", GRADUADA],
        [NUEVOS_OK, RELACION_OK, COMENTADO, CERRADO, leido(overview()),
         ESCRITO_FALSO])
    chequear(n, "rc", rc, mod.SIN_KEY)
    chequear(n, "SEIS llamadas al transporte", tr.llamadas, 6)
    chequear(n, "stderr imprime una invocacion de map:write", "map:write" in err, True)
    chequear(n, "con el mismo --project", "--project p-1" in err, True)
    chequear(n, "con la url real que devolvio el issueUpdate", URL_CERRADO in err, True)
    chequear(n, "con el gist real", GIST[1] in err, True)
    chequear(n, "y con el titulo graduado", GRADUADA in err, True)
    chequear(n, "NUNCA sugiere repetir ticket:resolve", "ticket:resolve" in err, False)
    chequear(n, "y dice que el comentario y el estado ya aterrizaron",
             "comentario" in err and "Done" in err, True)


def caso_21():
    """Fuera de alcance: el estado cancelado, la viñeta bajo su propia ancla, y
    Decisiones hasta ahora byte a byte como estaba. La asimetría es la operación."""
    n = "21-ticket-rule-out"
    base = overview()
    rc, out, err, tr = correr(n, FUERA + secciones() +
                              ["--out-of-scope", VINETA_FUERA],
                              [COMENTADO, CANCELADO, leido(base), ESCRITO_OK])
    chequear(n, "rc", rc, 0)
    chequear(n, "CUATRO llamadas al transporte", tr.llamadas, 4)
    if tr.llamadas != 4:
        return
    chequear(n, "input.stateId es el canceled del ctx",
             (tr.variables[1].get("input") or {}).get("stateId"), "s2")
    contenido = tr.variables[3].get("content") or ""
    cuerpos = mod.cortar_secciones(contenido)
    chequear(n, "la vineta aterrizo bajo Fuera de alcance",
             ("- " + VINETA_FUERA) in cuerpos[mod.ANCLA_FUERA], True)
    chequear(n, "Decisiones hasta ahora quedo BYTE A BYTE como estaba",
             cuerpos[mod.ANCLA_DECISIONES],
             mod.cortar_secciones(base)[mod.ANCLA_DECISIONES])
    chequear(n, "y no se colo ninguna linea de decision",
             any(URL_CERRADO in l for l in cuerpos[mod.ANCLA_DECISIONES]), False)

    # La asimetría del otro lado: --gist no está declarado, así que argparse lo rechaza.
    g = n + "-CONTROL-no-acepta-gist"
    rc, out, err, tr = correr(g, FUERA + secciones() +
                              ["--out-of-scope", VINETA_FUERA, "--gist", "x"], [])
    chequear(g, "rc del error de argparse", rc, 2)
    chequear(g, "TRANSPORTE LLAMADO CERO VECES", tr.llamadas, 0)


def caso_22():
    """El enum, otra vez, y por la ruta nueva. La 60 ya lo mide desde ticket:block; acá
    se mide que el cableado de una resolución REUSE esa constante en vez de reescribirla,
    que es exactamente por donde el defecto de 60329ef volvería a entrar."""
    n = "22-el-enum-reusado-desde-la-resolucion"
    rc, out, err, tr = correr(
        n, RESOLVER + secciones() + GIST + NUEVOS + CABLE,
        [NUEVOS_OK, RELACION_OK, COMENTADO, CERRADO, leido(overview()), ESCRITO_OK])
    chequear(n, "rc", rc, 0)
    q = tr.queries[1] if len(tr.queries) > 1 else ""
    chequear(n, "la query de la relacion es la constante del modulo, BYTE A BYTE",
             q, mod.ISSUE_RELATION_CREATE)
    chequear(n, "lleva el enum sin comillas", "type: blocks" in q, True)
    chequear(n, "y NUNCA cita un enum", 'type: "' in q, False)


def caso_23():
    """Las dos consistencias que se rompen antes de la red: un --remove-fog que la
    sección Niebla graduada no nombra, y un --block que nombra un título que ningún
    --new-ticket declaró. Las dos por el handler entero y no por la función pura, que es
    lo que prueba que la validación corre antes del primer POST y no después."""
    n = "23-titulos-que-no-matchean-abortan-antes-de-la-red"
    rc, out, err, tr = correr(
        n, RESOLVER + secciones() + GIST + ["--remove-fog", GRADUADA], [])
    chequear(n, "rc", rc, mod.SIN_KEY)
    chequear(n, "stdout vacio", out, "")
    chequear(n, "stderr nombra el titulo que la seccion no menciona",
             GRADUADA in err, True)
    chequear(n, "stderr nombra la seccion que lo tendria que nombrar",
             SEIS[3] in err, True)
    chequear(n, "TRANSPORTE LLAMADO CERO VECES", tr.llamadas, 0)

    b = n + "-CONTROL-block-con-titulo-inexistente"
    rc, out, err, tr = correr(
        b, RESOLVER + secciones() + GIST + NUEVOS +
        ["--block", "Un titulo que no declare", "Otra pregunta"], [])
    chequear(b, "rc", rc, mod.SIN_KEY)
    chequear(b, "stdout vacio", out, "")
    chequear(b, "stderr nombra el titulo que no matchea",
             "Un titulo que no declare" in err, True)
    chequear(b, "stderr nombra los declarados", "Una pregunta nueva" in err, True)
    chequear(b, "TRANSPORTE LLAMADO CERO VECES", tr.llamadas, 0)

    # Y el mismo desenlace por la otra punta, ticket:rule-out.
    r = n + "-CONTROL-por-la-ruta-de-rule-out"
    rc, out, err, tr = correr(
        r, FUERA + secciones() + ["--out-of-scope", VINETA_FUERA,
                                  "--remove-fog", GRADUADA], [])
    chequear(r, "rc", rc, mod.SIN_KEY)
    chequear(r, "TRANSPORTE LLAMADO CERO VECES", tr.llamadas, 0)


def caso_24():
    """La cuarta escritura falla, antes de llegar a la quinta: CUATRO POSTs, sin afirmar
    que el estado no cambio (un timeout no distingue eso de que haya cambiado y se haya
    perdido la respuesta), y nombrando los flags de niebla pendientes, porque a esta
    altura todavia no hay url para imprimir la invocacion entera de map:write. Mismo
    desenlace que el caso 20 mide para la quinta escritura, ahora para la cuarta."""
    n = "24-el-issueupdate-falla-antes-del-mapa"
    rc, out, err, tr = correr(
        n, RESOLVER + secciones(**{SEIS[3]: ["se graduo " + GRADUADA]}) + GIST +
        NUEVOS + CABLE + ["--remove-fog", GRADUADA,
                          "--append-fog",
                          "**Una niebla nueva.** que abre esta resolucion"],
        [NUEVOS_OK, RELACION_OK, COMENTADO, CIERRE_FALSO])
    chequear(n, "rc", rc, mod.SIN_KEY)
    chequear(n, "CUATRO llamadas al transporte", tr.llamadas, 4)
    chequear(n, "stderr NO afirma que el estado no cambio",
             "no se pudo cambiar" in err, False)
    chequear(n, "stderr admite que puede haber cambiado igual",
             "puede que" in err, True)
    chequear(n, "stderr nombra el remove-fog pendiente",
             "--remove-fog" in err and GRADUADA in err, True)
    chequear(n, "stderr nombra el append-fog pendiente",
             "--append-fog" in err and "Una niebla nueva." in err, True)
    chequear(n, "y dice que el comentario ya esta escrito", "comentario" in err, True)
    chequear(n, "NUNCA sugiere repetir ticket:resolve", "ticket:resolve" in err, False)


# Lo que la corrida diferida imprimió, para que los casos que la comparan lo hagan
# contra una salida del programa y nunca contra un formato escrito acá. Un check que
# escribiera la línea esperada estaría verificando su propia copia, que es exactamente
# la copia número tres que este cambio existe para no agregar.
DIFERIDO = {}


def caso_25():
    """--defer-map: las cuatro escrituras del ticket y ninguna del mapa, con la línea y
    los mapArgs impresos en el stdout de siempre. Es la mitad que el AST no puede ver:
    que ninguna query alcance el mapa de verdad, y no solo que haya un Return escrito
    arriba de la sentencia que lo escribe."""
    n = "25-ticket-resolve-defer-map-feliz"
    rc, out, err, tr = correr(
        n, RESOLVER + secciones() + GIST + NUEVOS + CABLE + ["--defer-map"],
        [NUEVOS_OK, RELACION_OK, COMENTADO, CERRADO])
    chequear(n, "rc", rc, 0)
    chequear(n, "stderr vacio", err, "")
    chequear(n, "CUATRO llamadas al transporte", tr.llamadas, 4)
    for prohibida in ("project(id:", "projectUpdate"):
        chequear(n, "ninguna query lleva " + prohibida,
                 [q for q in tr.queries if prohibida in q], [])
    d = json_de(n, out)
    chequear(n, "mapWritten es false", d.get("mapWritten"), False)
    chequear(n, "mapLine no viene vacia", bool(d.get("mapLine")), True)
    chequear(n, "mapArgs empieza con --append-decision",
             (d.get("mapArgs") or [])[:1], ["--append-decision"])
    DIFERIDO["resolve"] = d


def caso_26():
    """La MISMA argv del caso 25 sin el flag: seis POSTs, y la línea que la corrida
    diferida imprimió está byte a byte adentro del content que viajó al projectUpdate.
    Es la pata que vuelve no tautológica a toda la fila, porque compara dos salidas del
    programa: una cadena que un proceso imprimió por stdout contra los bytes que otro
    proceso mandó por el transporte. El check nunca escribe el formato de la línea."""
    n = "26-la-misma-argv-sin-el-flag-escribe-lo-que-la-otra-imprimio"
    d = DIFERIDO.get("resolve") or {}
    if not d.get("mapLine"):
        anotar("%s: el caso 25 no dejo ninguna mapLine, asi que no hay contra que "
               "comparar y esta pata no puede pasar en verde" % n)
        return
    rc, out, err, tr = correr(
        n, RESOLVER + secciones() + GIST + NUEVOS + CABLE,
        [NUEVOS_OK, RELACION_OK, COMENTADO, CERRADO, leido(overview()), ESCRITO_OK])
    chequear(n, "rc", rc, 0)
    chequear(n, "SEIS llamadas al transporte", tr.llamadas, 6)
    if tr.llamadas != 6:
        return
    cuerpos = mod.cortar_secciones(tr.variables[5].get("content") or "")
    chequear(n, "la linea diferida esta BYTE A BYTE bajo Decisiones hasta ahora",
             d["mapLine"] in cuerpos[mod.ANCLA_DECISIONES], True)
    e = json_de(n, out)
    chequear(n, "la corrida escrita imprime la MISMA mapLine",
             e.get("mapLine"), d["mapLine"])
    chequear(n, "y los MISMOS mapArgs", e.get("mapArgs"), d.get("mapArgs"))
    chequear(n, "con mapWritten en true", e.get("mapWritten"), True)


def caso_27():
    """La tercera punta, desde el cable: map:write con los mapArgs que la corrida
    diferida devolvió deja bajo el ancla la MISMA línea que esa corrida imprimió. Es la
    casa única del formato asertada desde el transporte y no desde el AST, y es el
    camino exacto que recorre el padre cuando un subagente le devuelve su bloque."""
    n = "27-map-write-con-los-mapargs-del-diferido"
    d = DIFERIDO.get("resolve") or {}
    if not d.get("mapArgs"):
        anotar("%s: el caso 25 no dejo ningunos mapArgs que pasarle a map:write" % n)
        return
    rc, out, err, tr = correr(n, ["map:write", "--project", "p-1"] +
                              list(d["mapArgs"]), [leido(overview()), ESCRITO_OK])
    chequear(n, "rc", rc, 0)
    chequear(n, "DOS llamadas al transporte", tr.llamadas, 2)
    if tr.llamadas != 2:
        return
    cuerpos = mod.cortar_secciones(tr.variables[1].get("content") or "")
    chequear(n, "la linea que el mapa gana es la que el diferido imprimio",
             d["mapLine"] in cuerpos[mod.ANCLA_DECISIONES], True)
    chequear(n, "la decision previa sobrevive",
             DECISION_PREVIA in cuerpos[mod.ANCLA_DECISIONES], True)


def caso_28():
    """ticket:rule-out --defer-map contra su corrida hermana sin el flag: cuatro POSTs
    contra seis, mapArgs que empieza con --append-out-of-scope, y la viñeta diferida
    byte a byte bajo Fuera de alcance y NUNCA bajo Decisiones. La asimetría de las dos
    operaciones también viaja en el reparto."""
    n = "28-ticket-rule-out-defer-map"
    argv = FUERA + secciones() + ["--out-of-scope", VINETA_FUERA] + NUEVOS + CABLE
    rc, out, err, tr = correr(n, argv + ["--defer-map"],
                              [NUEVOS_OK, RELACION_OK, COMENTADO, CANCELADO])
    chequear(n, "rc", rc, 0)
    chequear(n, "stderr vacio", err, "")
    chequear(n, "CUATRO llamadas al transporte", tr.llamadas, 4)
    for prohibida in ("project(id:", "projectUpdate"):
        chequear(n, "ninguna query lleva " + prohibida,
                 [q for q in tr.queries if prohibida in q], [])
    d = json_de(n, out)
    chequear(n, "mapWritten es false", d.get("mapWritten"), False)
    chequear(n, "mapArgs empieza con --append-out-of-scope",
             (d.get("mapArgs") or [])[:1], ["--append-out-of-scope"])
    if not d.get("mapLine"):
        anotar("%s: la corrida diferida no imprimio ninguna mapLine" % n)
        return

    h = n + "-HERMANA-sin-el-flag"
    rc, out, err, tr = correr(h, argv, [NUEVOS_OK, RELACION_OK, COMENTADO, CANCELADO,
                                        leido(overview()), ESCRITO_OK])
    chequear(h, "rc", rc, 0)
    chequear(h, "SEIS llamadas al transporte", tr.llamadas, 6)
    if tr.llamadas != 6:
        return
    cuerpos = mod.cortar_secciones(tr.variables[5].get("content") or "")
    chequear(h, "la vineta diferida esta BYTE A BYTE bajo Fuera de alcance",
             d["mapLine"] in cuerpos[mod.ANCLA_FUERA], True)
    chequear(h, "y NUNCA bajo Decisiones hasta ahora",
             d["mapLine"] in cuerpos[mod.ANCLA_DECISIONES], False)


def caso_29():
    """La niebla viaja en mapArgs y no se pierde en silencio: los tres grupos de flags
    en el orden fijado, el --append-fog SIN su marcador, y ni --project ni
    --expect-sections adentro. Y la guarda de _niebla_de sigue abortando antes de la
    red, con el transporte en cero, cuando la sección que cuenta la graduación no
    nombra el título: el flag no aflojó ninguna validación previa."""
    n = "29-defer-map-con-niebla-graduada-y-nueva"
    nueva = "**Una niebla nueva.** que abre esta resolucion"
    rc, out, err, tr = correr(
        n, RESOLVER + secciones(**{SEIS[3]: ["se graduo " + GRADUADA]}) + GIST +
        ["--remove-fog", GRADUADA, "--append-fog", nueva, "--defer-map"],
        [COMENTADO, CERRADO])
    chequear(n, "rc", rc, 0)
    chequear(n, "DOS llamadas al transporte", tr.llamadas, 2)
    d = json_de(n, out)
    args = d.get("mapArgs") or []
    chequear(n, "mapArgs lleva los tres grupos en el orden del contrato",
             [a for a in args if a.startswith("--")],
             ["--append-decision", "--remove-fog", "--append-fog"])
    chequear(n, "el --remove-fog lleva el titulo exacto",
             args[args.index("--remove-fog") + 1] if "--remove-fog" in args else None,
             GRADUADA)
    chequear(n, "el --append-fog viaja SIN marcador",
             args[args.index("--append-fog") + 1] if "--append-fog" in args else None,
             nueva)
    for prohibido in ("--project", "--expect-sections"):
        chequear(n, "mapArgs NO lleva " + prohibido, prohibido in args, False)

    g = n + "-CONTROL-graduada-que-la-seccion-no-nombra"
    rc, out, err, tr = correr(
        g, RESOLVER + secciones() + GIST + ["--remove-fog", GRADUADA, "--defer-map"],
        [])
    chequear(g, "rc", rc, mod.SIN_KEY)
    chequear(g, "stdout vacio", out, "")
    chequear(g, "stderr nombra el titulo que la seccion no menciona",
             GRADUADA in err, True)
    chequear(g, "TRANSPORTE LLAMADO CERO VECES", tr.llamadas, 0)


def caso_30():
    """El comentario rechazado con success false y el flag puesto: código no cero,
    stdout VACÍO y stderr nombrando lo que ya aterrizó. Es el caso que sostiene la regla
    con la que el padre decide si un retorno sirve: stdout con contenido implica éxito,
    stdout vacío implica falla, y con --defer-map esa regla no se afloja."""
    n = "30-defer-map-con-el-comentario-rechazado"
    rc, out, err, tr = correr(
        n, RESOLVER + secciones() + GIST + NUEVOS + CABLE + ["--defer-map"],
        [NUEVOS_OK, RELACION_OK, COMENTADO_FALSO])
    chequear(n, "rc", rc, mod.SIN_KEY)
    chequear(n, "stdout vacio", out, "")
    chequear(n, "TRES llamadas al transporte", tr.llamadas, 3)
    chequear(n, "stderr nombra success", "success" in err, True)
    chequear(n, "stderr dice que los tickets ya quedaron escritos",
             "tickets nuevos" in err, True)


# --- los desenlaces de --project con un issue ------------------------------------
# Estos pasan por main y no por args.func: la resolución del issue vive en main, y un
# caso que llamara al handler directo probaría el handler sin la resolución.

URL_ISSUE = "https://linear.app/keiron/issue/CRM-7/el-slug-del-ticket"


def issue_resuelto(labels=("map", "map:grilling"), project="p-del-issue"):
    return {"data": {"issue": {
        "identifier": "CRM-7",
        "project": {"id": project} if project else None,
        "labels": {"nodes": [{"name": n} for n in labels]}}}}


def correr_main(nombre, argv, secuencia):
    transporte = Transporte(nombre, secuencia)
    mod.urllib.request.urlopen = transporte
    so, se = io.StringIO(), io.StringIO()
    rc = 0
    try:
        with contextlib.redirect_stdout(so), contextlib.redirect_stderr(se):
            mod.main(argv)
    except SystemExit as exc:
        rc = exc.code if isinstance(exc.code, int) else 1
    except AssertionError as exc:
        rc = -1
        se.write(str(exc))
    return rc, so.getvalue(), se.getvalue(), transporte


def caso_31():
    """La URL de un ticket en map:read: un POST al issue con el identificador sacado de
    la URL, y la lectura del mapa sobre el Project de ese issue."""
    n = "31-map-read-con-la-url-de-un-ticket"
    rc, out, err, tr = correr_main(n, ["map:read", "--project", URL_ISSUE],
                                   [issue_resuelto(), leido(overview())])
    chequear(n, "rc", rc, 0)
    chequear(n, "DOS llamadas al transporte", tr.llamadas, 2)
    chequear(n, "la primera query es la del issue",
             tr.queries[0] if tr.queries else "", mod.ISSUE_PROJECT_QUERY)
    chequear(n, "el identificador sale de la URL",
             (tr.variables[0] if tr.variables else {}).get("issue"), "CRM-7")
    chequear(n, "la lectura usa el Project del issue",
             (tr.variables[1] if len(tr.variables) > 1 else {}).get("project"),
             "p-del-issue")
    chequear(n, "found", json_de(n, out).get("found"), True)


def caso_32():
    """El identificador pelado en frontier:query, la otra lectura del contrato."""
    n = "32-frontier-query-con-el-identificador"
    vacio = {"data": {"project": {
        "issues": {"pageInfo": {"hasNextPage": False}, "nodes": []},
        "projectMilestones": {"pageInfo": {"hasNextPage": False}, "nodes": []}}}}
    rc, out, err, tr = correr_main(
        n, ["frontier:query", "--ctx", CTX, "--project", "CRM-7"],
        [issue_resuelto(), vacio])
    chequear(n, "rc", rc, 0)
    chequear(n, "DOS llamadas al transporte", tr.llamadas, 2)
    chequear(n, "la frontera usa el Project del issue",
             (tr.variables[1] if len(tr.variables) > 1 else {}).get("project"),
             "p-del-issue")


URL_PROJECT = "https://linear.app/keiron/project/campanas-a06fa7500fde"
PROJECT_RESUELTO = {"data": {"project": {"id": "p-de-la-url"}}}


def caso_33():
    """La URL de un Project se resuelve a su id con un POST antes de leer, y la
    lectura viaja sobre el id devuelto. Un slug cuyo slugId termina solo en dígitos
    viaja tal cual y sin round trip de más."""
    n = "33-url-de-project-se-resuelve"
    rc, out, err, tr = correr_main(n, ["map:read", "--project", URL_PROJECT],
                                   [PROJECT_RESUELTO, leido(overview())])
    chequear(n, "rc", rc, 0)
    chequear(n, "DOS llamadas al transporte", tr.llamadas, 2)
    chequear(n, "la primera query es la del Project",
             tr.queries[0] if tr.queries else "",
             getattr(mod, "PROJECT_ID_QUERY", "falta PROJECT_ID_QUERY"))
    chequear(n, "la variable es el slug",
             (tr.variables[0] if tr.variables else {}).get("project"),
             "campanas-a06fa7500fde")
    chequear(n, "la lectura usa el id devuelto",
             (tr.variables[1] if len(tr.variables) > 1 else {}).get("project"),
             "p-de-la-url")

    n = "33-url-de-project-con-overview-manda-el-mismo-slug"
    rc, out, err, tr = correr_main(
        n, ["map:read", "--project", URL_PROJECT + "/overview"],
        [PROJECT_RESUELTO, leido(overview())])
    chequear(n, "rc", rc, 0)
    chequear(n, "la variable es el slug sin /overview",
             (tr.variables[0] if tr.variables else {}).get("project"),
             "campanas-a06fa7500fde")

    n, valor = "33-slug-terminado-en-digitos", "campanas-123456789012"
    rc, out, err, tr = correr_main(n, ["map:read", "--project", valor],
                                   [leido(overview())])
    chequear(n, "rc", rc, 0)
    chequear(n, "UNA llamada al transporte", tr.llamadas, 1)
    chequear(n, "el valor viaja tal cual",
             (tr.variables[0] if tr.variables else {}).get("project"), valor)


def caso_34():
    """Los tres rechazos con NO_ES_DEL_MAPA, cada uno después de un solo POST y sin
    leer el mapa: sin el label map, sin Project, y un issue que no existe."""
    no_existe = {"errors": [{"message": "Entity not found: Issue",
                             "extensions": {"code": "INPUT_ERROR", "statusCode": 400}}],
                 "data": None}
    for n, respuesta, aguja in (
            ("34-issue-sin-label-map", issue_resuelto(labels=("Improvement",)),
             "label map"),
            ("34-issue-sin-project", issue_resuelto(project=None), "ningún Project"),
            ("34-issue-que-no-existe", no_existe, "no existe")):
        rc, out, err, tr = correr_main(n, ["map:read", "--project", URL_ISSUE],
                                       [respuesta])
        chequear(n, "rc", rc, mod.NO_ES_DEL_MAPA)
        chequear(n, "stdout vacio", out, "")
        chequear(n, "UNA llamada al transporte", tr.llamadas, 1)
        chequear(n, "stderr explica el rechazo", aguja in err, True)


def caso_35():
    """Un error que no es de existencia no se disfraza de rechazo: la credencial sale
    con SIN_KEY y un rate limit con SIN_API."""
    for n, respuesta, esperado in (
            ("35-credencial-rechazada",
             {"errors": [{"message": "Authentication required",
                          "extensions": {"code": "AUTHENTICATION_ERROR"}}]},
             mod.SIN_KEY),
            ("35-rate-limit",
             {"errors": [{"message": "Rate limit exceeded",
                          "extensions": {"code": "RATELIMITED"}}]},
             mod.SIN_API)):
        rc, out, err, tr = correr_main(n, ["map:read", "--project", "CRM-7"],
                                       [respuesta])
        chequear(n, "rc", rc, esperado)
        chequear(n, "UNA llamada al transporte", tr.llamadas, 1)


def caso_47():
    """Un Project que no existe sale con NO_ES_DEL_MAPA después de un solo POST y sin
    leer el mapa; la credencial rechazada sigue saliendo con SIN_KEY."""
    no_existe = {"errors": [{"message": "Entity not found: Project",
                             "extensions": {"code": "INPUT_ERROR", "statusCode": 400}}],
                 "data": None}
    for n, respuesta, esperado in (
            ("47-project-que-no-existe", no_existe, mod.NO_ES_DEL_MAPA),
            ("47-project-nulo", {"data": {"project": None}}, mod.NO_ES_DEL_MAPA),
            ("47-project-con-credencial-rechazada",
             {"errors": [{"message": "Authentication required",
                          "extensions": {"code": "AUTHENTICATION_ERROR"}}]},
             mod.SIN_KEY)):
        rc, out, err, tr = correr_main(n, ["map:read", "--project", URL_PROJECT],
                                       [respuesta])
        chequear(n, "rc", rc, esperado)
        chequear(n, "stdout vacio", out, "")
        chequear(n, "UNA llamada al transporte", tr.llamadas, 1)
        if esperado == mod.NO_ES_DEL_MAPA:
            chequear(n, "stderr explica el rechazo", "no existe" in err, True)


def caso_48():
    """milestone:create con la URL de un Project manda el id resuelto como projectId,
    nunca la URL."""
    n = "48-milestone-create-con-la-url-de-un-project"
    creado = {"data": {"projectMilestoneCreate": {"success": True, "projectMilestone": {
        "id": "m1", "name": "Corte", "sortOrder": 1.0}}}}
    rc, out, err, tr = correr_main(
        n, ["milestone:create", "--project", URL_PROJECT, "--name", "Corte",
            "--description", "el primer corte", "--sort-order", "1"],
        [PROJECT_RESUELTO, creado])
    chequear(n, "rc", rc, 0)
    chequear(n, "DOS llamadas al transporte", tr.llamadas, 2)
    chequear(n, "projectId es el id resuelto",
             (tr.variables[1] if len(tr.variables) > 1 else {}).get("project"),
             "p-de-la-url")


def caso_36():
    """map:create no resuelve el issue: adopta un Project que todavía no tiene mapa, y
    su --project viaja tal cual a la primera lectura."""
    n = "36-map-create-no-resuelve-el-issue"
    rc, out, err, tr = correr_main(n, CREAR + ["--project", "CRM-7"],
                                   [{"data": {"project": None}}])
    chequear(n, "la primera query no es la del issue",
             (tr.queries[0] if tr.queries else "") != mod.ISSUE_PROJECT_QUERY, True)
    chequear(n, "el valor viaja tal cual",
             (tr.variables[0] if tr.variables else {}).get("project"), "CRM-7")


# --- las correcciones del mapa desde una resolución -------------------------------
# Graduar niebla a Fuera de alcance, reemplazar una viñeta de Fuera de alcance y corregir
# el Destino. Los dos últimos ensayan sus ediciones contra una lectura del mapa antes de
# la primera escritura, así que un título que no existe aborta sin escribir nada.

MUDADA = "**La niebla mudada.** quedo fuera del destino"
CORREGIDA = "**Algo corregido.** con cuerpo nuevo"
DESTINO_NUEVO = "que el mapa exista solo por correo"
GRADUAR = ["--graduate-out-of-scope", GRADUADA, MUDADA]
REEMPLAZAR = ["--replace-out-of-scope", "Algo ruled out.", CORREGIDA]
CORREGIR = ["--amend-destination", DESTINO_NUEVO]
CON_GUARDAS = secciones(**{SEIS[3]: ["se graduo " + GRADUADA],
                           SEIS[5]: ["corrige el Destino y Algo ruled out."]})


def caso_37():
    """Graduar a Fuera de alcance: la niebla se va y la viñeta entra en la misma
    escritura, con cuatro POSTs como cualquier resolución sin tickets nuevos."""
    n = "37-graduar-niebla-a-fuera-de-alcance"
    rc, out, err, tr = correr(n, RESOLVER + CON_GUARDAS + GIST + GRADUAR,
                              [COMENTADO, CERRADO, leido(overview()), ESCRITO_OK])
    chequear(n, "rc", rc, 0)
    chequear(n, "CUATRO llamadas al transporte", tr.llamadas, 4)
    contenidos = tr.contents
    chequear(n, "UNA sola escritura del mapa", len(contenidos), 1)
    cuerpos = mod.cortar_secciones(contenidos[0] if contenidos else "")
    chequear(n, "la niebla perdio el parche",
             any(GRADUADA in l for l in cuerpos.get(mod.ANCLA_NIEBLA) or []), False)
    chequear(n, "Fuera de alcance gano la vineta",
             "- " + MUDADA in (cuerpos.get(mod.ANCLA_FUERA) or []), True)
    chequear(n, "la vineta previa de Fuera de alcance sobrevive",
             "- **Algo ruled out.** con cuerpo" in (cuerpos.get(mod.ANCLA_FUERA) or []),
             True)
    flags = json_de(n, out).get("mapArgs") or []
    chequear(n, "mapArgs lleva el parche como --remove-fog",
             "--remove-fog" in flags and GRADUADA in flags, True)
    chequear(n, "y la vineta como --append-out-of-scope",
             "--append-out-of-scope" in flags and MUDADA in flags, True)

    r = n + "-CONTROL-sin-la-linea-de-niebla-graduada-aborta-antes-de-la-red"
    rc, out, err, tr = correr(r, RESOLVER + secciones() + GIST + GRADUAR, [])
    chequear(r, "rc", rc, mod.SIN_KEY)
    chequear(r, "stderr nombra el titulo", GRADUADA in err, True)
    chequear(r, "TRANSPORTE LLAMADO CERO VECES", tr.llamadas, 0)


def caso_38():
    """Reemplazar una viñeta de Fuera de alcance: un ensayo de lectura antes de la
    primera escritura, y la viñeta nueva en el mismo lugar que la vieja."""
    n = "38-reemplazar-fuera-de-alcance"
    # Con una segunda viñeta abajo, reemplazar en el lugar y agregar al final dejan de
    # producir el mismo cuerpo.
    base = overview().replace("- **Algo ruled out.** con cuerpo",
                              "- **Algo ruled out.** con cuerpo\n- **Otra cosa.** sigue")
    rc, out, err, tr = correr(
        n, RESOLVER + CON_GUARDAS + GIST + REEMPLAZAR,
        [leido(base), COMENTADO, CERRADO, leido(base), ESCRITO_OK])
    chequear(n, "rc", rc, 0)
    chequear(n, "CINCO llamadas al transporte", tr.llamadas, 5)
    chequear(n, "el primer POST es una lectura y no escribe",
             "mutation" in (tr.queries[0] if tr.queries else "mutation"), False)
    fuera = mod.cortar_secciones(tr.contents[0] if tr.contents else "").get(
        mod.ANCLA_FUERA) or []
    chequear(n, "Fuera de alcance queda con la vineta nueva en el lugar de la vieja",
             [l for l in fuera if l.strip()], ["- " + CORREGIDA, "- **Otra cosa.** sigue"])


def caso_39():
    """Un reemplazo con un título que no existe aborta después del ensayo y antes de
    escribir nada: una sola llamada, y es la lectura."""
    n = "39-reemplazo-sin-el-titulo-aborta-sin-escribir"
    rc, out, err, tr = correr(
        n, RESOLVER + CON_GUARDAS + GIST +
        ["--replace-out-of-scope", "No existe.", CORREGIDA], [leido(overview())])
    chequear(n, "rc", rc, mod.SIN_KEY)
    chequear(n, "stdout vacio", out, "")
    chequear(n, "UNA llamada al transporte", tr.llamadas, 1)
    chequear(n, "y no escribe", "mutation" in (tr.queries[0] if tr.queries else ""),
             False)
    chequear(n, "stderr nombra el titulo", "No existe." in err, True)


def caso_40():
    """Corregir el Destino exige que Qué corrige o empuja lo nombre, y sin esa línea
    aborta antes del primer POST."""
    n = "40-corregir-destino-sin-nombrarlo-aborta-antes-de-la-red"
    rc, out, err, tr = correr(n, RESOLVER + secciones() + GIST + CORREGIR, [])
    chequear(n, "rc", rc, mod.SIN_KEY)
    chequear(n, "stderr nombra la seccion", SEIS[5] in err, True)
    chequear(n, "TRANSPORTE LLAMADO CERO VECES", tr.llamadas, 0)


def caso_41():
    """Corregir el Destino: el cuerpo entero de la sección queda en la línea nueva."""
    n = "41-corregir-destino"
    rc, out, err, tr = correr(
        n, RESOLVER + CON_GUARDAS + GIST + CORREGIR,
        [leido(overview()), COMENTADO, CERRADO, leido(overview()), ESCRITO_OK])
    chequear(n, "rc", rc, 0)
    chequear(n, "CINCO llamadas al transporte", tr.llamadas, 5)
    destino = mod.cortar_secciones(tr.contents[0] if tr.contents else "").get(
        mod.ANCLAS[0]) or []
    chequear(n, "el Destino es la linea nueva y nada mas",
             [l for l in destino if l.strip()], [DESTINO_NUEVO])
    flags = json_de(n, out).get("mapArgs") or []
    chequear(n, "mapArgs lleva --amend-destination",
             flags[-2:], ["--amend-destination", DESTINO_NUEVO])


def caso_42():
    """Los tres flags juntos con --defer-map, y los mapArgs que devuelve corridos por
    map:write: el mapa que queda es byte a byte el de la misma resolución sin el flag,
    así que las dos puntas salen de una sola construcción."""
    n = "42-defer-map-y-map-write-reproducen-la-resolucion"
    argv = RESOLVER + CON_GUARDAS + GIST + GRADUAR + REEMPLAZAR + CORREGIR
    rc, out, err, directa = correr(
        n, argv, [leido(overview()), COMENTADO, CERRADO, leido(overview()), ESCRITO_OK])
    chequear(n, "rc sin el flag", rc, 0)
    rc, out, err, tr = correr(n, argv + ["--defer-map"],
                              [leido(overview()), COMENTADO, CERRADO])
    chequear(n, "rc con el flag", rc, 0)
    flags = json_de(n, out).get("mapArgs") or []
    if not flags or not directa.contents:
        anotar("%s: una de las dos corridas no dejo nada que comparar" % n)
        return
    rc, out, err, escrito = correr(n, ESCRIBIR + flags,
                                   [leido(overview()), ESCRITO_OK])
    chequear(n, "rc de map:write", rc, 0)
    chequear(n, "map:write deja el mismo mapa que la resolucion directa",
             escrito.contents[0] if escrito.contents else "", directa.contents[0])


def caso_43():
    """Sin ninguno de los tres flags no hay ensayo: la resolución gasta los mismos
    cuatro POSTs que antes."""
    n = "43-sin-los-flags-nuevos-no-hay-ensayo"
    rc, out, err, tr = correr(n, RESOLVER + secciones() + GIST,
                              [COMENTADO, CERRADO, leido(overview()), ESCRITO_OK])
    chequear(n, "rc", rc, 0)
    chequear(n, "CUATRO llamadas al transporte", tr.llamadas, 4)
    chequear(n, "el primer POST es el comentario",
             "commentCreate" in (tr.queries[0] if tr.queries else ""), True)


# --- las entregas de diseño abiertas en frontier:query ---------------------------

FRONTERA = ["frontier:query", "--ctx", CTX, "--project", "kp-falso"]


def entrega(identifier, state, created, assignee=None):
    return {"identifier": identifier, "title": "Diseño terminado: " + identifier,
            "url": "https://linear.app/keiron/issue/" + identifier,
            "createdAt": created, "state": {"id": state},
            "assignee": {"displayName": assignee} if assignee else None}


def frontera_con(entregas, cortada=False):
    return {"data": {"project": {
        "issues": {"pageInfo": {"hasNextPage": False}, "nodes": []},
        "designDeliveries": {"pageInfo": {"hasNextPage": cortada}, "nodes": entregas},
        "projectMilestones": {"pageInfo": {"hasNextPage": False}, "nodes": []}}}}


def caso_44():
    """Dos entregas abiertas y una cerrada: viajan las abiertas, en createdAt
    ascendente y con sus cuatro claves, y los conteos no las ven."""
    n = "44-frontier-query-con-entregas-abiertas"
    rc, out, err, tr = correr(n, FRONTERA, [frontera_con([
        entrega("CRM-12", "s3", "2026-10-02T00:00:00.000Z", "Ana"),
        entrega("CRM-11", "s1", "2026-10-01T00:00:00.000Z"),
        entrega("CRM-10", "s3", "2026-10-01T00:00:00.000Z")])])
    chequear(n, "rc", rc, 0)
    chequear(n, "UNA llamada al transporte", tr.llamadas, 1)
    chequear(n, "la query pide designDeliveries",
             "designDeliveries" in (tr.queries[0] if tr.queries else ""), True)
    chequear(n, "la variable delivery es LABELS[9]",
             (tr.variables[0] if tr.variables else {}).get("delivery"),
             (mod.LABELS[9:10] or ["LABELS sin décimo elemento"])[0])
    salida = json_de(n, out)
    chequear(n, "designDeliveries", salida.get("designDeliveries"), [
        {"identifier": "CRM-10", "title": "Diseño terminado: CRM-10",
         "url": "https://linear.app/keiron/issue/CRM-10", "assignee": None},
        {"identifier": "CRM-12", "title": "Diseño terminado: CRM-12",
         "url": "https://linear.app/keiron/issue/CRM-12", "assignee": "Ana"}])
    chequear(n, "counts no cuenta las entregas", salida.get("counts"),
             {"open": 0, "takeable": 0, "milestones": 0})
    chequear(n, "truncated", salida.get("truncated"), [])


def caso_45():
    """Un Project que no resolvió: la clave viaja igual, vacía."""
    n = "45-frontier-query-sin-project"
    rc, out, err, tr = correr(n, FRONTERA, [{"data": {"project": None}}])
    chequear(n, "rc", rc, 0)
    salida = json_de(n, out)
    chequear(n, "found", salida.get("found"), False)
    chequear(n, "designDeliveries vacía", salida.get("designDeliveries"), [])


def caso_46():
    """Solo entregas cerradas y la conexión cortada: la lista vacía no prueba nada, y
    truncated lo dice."""
    n = "46-frontier-query-con-las-entregas-cortadas"
    rc, out, err, tr = correr(n, FRONTERA, [frontera_con(
        [entrega("CRM-11", "s2", "2026-10-01T00:00:00.000Z")], cortada=True)])
    chequear(n, "rc", rc, 0)
    salida = json_de(n, out)
    chequear(n, "la entrega cerrada no viaja", salida.get("designDeliveries"), [])
    chequear(n, "truncated", salida.get("truncated"), ["designDeliveries"])
    chequear(n, "stderr avisa del corte", "designDeliveries" in err, True)

CASOS =[("60", caso_1), ("60", caso_2), ("60", caso_3), ("60", caso_4),
         ("60", caso_5), ("60", caso_6), ("60", caso_7), ("60", caso_8),
         ("60", caso_9), ("47", caso_10), ("47", caso_11), ("47", caso_12),
         ("60", caso_13), ("61", caso_14), ("61", caso_15), ("61", caso_16),
         ("61", caso_17), ("61", caso_18), ("61", caso_19), ("61", caso_20),
         ("61", caso_21), ("61", caso_22), ("61", caso_23), ("61", caso_24),
         ("66", caso_25), ("66", caso_26), ("66", caso_27), ("66", caso_28),
         ("66", caso_29), ("66", caso_30), ("73", caso_31), ("73", caso_32),
         ("73", caso_33), ("73", caso_34), ("73", caso_35), ("73", caso_36),
         ("73", caso_47), ("73", caso_48),
         ("74", caso_37), ("74", caso_38), ("74", caso_39), ("74", caso_40),
         ("74", caso_41), ("74", caso_42), ("74", caso_43),
         ("75", caso_44), ("75", caso_45), ("75", caso_46)]
for _afirmacion, _caso in CASOS:
    AFIRMACION[0] = _afirmacion
    _caso()

for _afirmacion in ("60", "47", "61", "66", "73", "74", "75"):
    print("casos%s=%d" % (_afirmacion,
                          len([c for c in CASOS if c[0] == _afirmacion])))
    print("fallas%s=%s" % (_afirmacion, plano(FALLAS[_afirmacion])
                           if FALLAS[_afirmacion] else "ninguna"))
sys.exit(1 if [b for b in FALLAS.values() if b] else 0)
PY
)"

# La corrida entera se vuelca una sola vez, y solo si algo falló: el balde que falló lo
# nombra el [N] de abajo. Cada fail lleva su número embebido en el string y escrito a
# mano, nunca interpolado: un "[$var]" no lo extrae la afirmación 50.
#
# El volcado va detrás de una línea que empieza con el nombre del check, y no pelado: el
# volcado sale por stderr ANTES que report, así que sin esa línea la primera de stderr es
# una línea del protocolo del harness y el lector no sabe qué check abrió el archivo.
if printf '%s\n' "$salida" | /usr/bin/grep -q 'fallas60=ninguna' \
   && printf '%s\n' "$salida" | /usr/bin/grep -q 'fallas47=ninguna' \
   && printf '%s\n' "$salida" | /usr/bin/grep -q 'fallas61=ninguna' \
   && printf '%s\n' "$salida" | /usr/bin/grep -q 'fallas66=ninguna' \
   && printf '%s\n' "$salida" | /usr/bin/grep -q 'fallas73=ninguna' \
   && printf '%s\n' "$salida" | /usr/bin/grep -q 'fallas74=ninguna' \
   && printf '%s\n' "$salida" | /usr/bin/grep -q 'fallas75=ninguna'; then
  :
else
  echo "$CHECK_NAME: la corrida del harness dijo:" >&2
  printf '%s\n' "$salida" | sed 's/^/  /' >&2
fi

if ! printf '%s\n' "$salida" | /usr/bin/grep -q 'fallas60=ninguna'; then
  fail "[60] las operaciones que escriben no distinguen sus desenlaces de runtime con el transporte mockeado"
fi

if ! printf '%s\n' "$salida" | /usr/bin/grep -q 'fallas47=ninguna'; then
  fail "[47] ticket:create no rechaza dos labels de tipo antes de tocar la red, o rechaza de más: cero tipos es AFK y uno solo se crea"
fi

if ! printf '%s\n' "$salida" | /usr/bin/grep -q 'fallas61=ninguna'; then
  fail "[61] ticket:claim, ticket:resolve y ticket:rule-out no distinguen sus desenlaces de runtime con el transporte mockeado, o las cinco escrituras de una resolución no viajan en el orden del contrato"
fi

if ! printf '%s\n' "$salida" | /usr/bin/grep -q 'fallas66=ninguna'; then
  fail "[66] con --defer-map las dos resoluciones no distinguen sus desenlaces de runtime con el transporte mockeado, o alguna query sigue alcanzando el mapa"
fi

if ! printf '%s\n' "$salida" | /usr/bin/grep -q 'fallas73=ninguna'; then
  fail "[73] --project no resuelve el Project de un ticket de decisión pasado por URL o identificador ni el id de un Project pasado por URL, o resuelve lo que no es un issue ni la URL de un Project, o no rechaza el que no es del mapa o el Project que no existe"
fi

if ! printf '%s\n' "$salida" | /usr/bin/grep -q 'fallas74=ninguna'; then
  fail "[74] ticket:resolve no gradúa niebla a Fuera de alcance, no reemplaza una viñeta de Fuera de alcance o no corrige el Destino como dice el contrato, o alguno escribe antes de abortar"
fi

if ! printf '%s\n' "$salida" | /usr/bin/grep -q 'fallas75=ninguna'; then
  fail "[75] frontier:query no emite designDeliveries en sus dos ramas, deja pasar una entrega cerrada, no manda LABELS[9] en la query o no nombra designDeliveries en truncated cuando esa conexión viene cortada"
fi

report

# Los cardinales salen de la corrida y no de una palabra escrita a mano: un conteo
# tipeado acá sería una segunda casa que nadie compara contra la primera.
casos="$(printf '%s\n' "$salida" | sed -n 's/^casos60=//p')"
require_nonempty "$casos" "[60] la corrida no emitió su cardinal de casos, así que el protocolo entre el intérprete y bash se movió"
casos47="$(printf '%s\n' "$salida" | sed -n 's/^casos47=//p')"
require_nonempty "$casos47" "[47] la corrida no emitió su cardinal de casos, así que el protocolo entre el intérprete y bash se movió"
casos61="$(printf '%s\n' "$salida" | sed -n 's/^casos61=//p')"
require_nonempty "$casos61" "[61] la corrida no emitió su cardinal de casos, así que el protocolo entre el intérprete y bash se movió"
casos66="$(printf '%s\n' "$salida" | sed -n 's/^casos66=//p')"
require_nonempty "$casos66" "[66] la corrida no emitió su cardinal de casos, así que el protocolo entre el intérprete y bash se movió"
casos73="$(printf '%s\n' "$salida" | sed -n 's/^casos73=//p')"
require_nonempty "$casos73" "[73] la corrida no emitió su cardinal de casos, así que el protocolo entre el intérprete y bash se movió"
casos74="$(printf '%s\n' "$salida" | sed -n 's/^casos74=//p')"
require_nonempty "$casos74" "[74] la corrida no emitió su cardinal de casos, así que el protocolo entre el intérprete y bash se movió"
casos75="$(printf '%s\n' "$salida" | sed -n 's/^casos75=//p')"
require_nonempty "$casos75" "[75] la corrida no emitió su cardinal de casos, así que el protocolo entre el intérprete y bash se movió"
plural=""
[ "$casos" = 1 ] || plural="s"
echo "$CHECK_NAME: OK - $adapter distingue $casos desenlace$plural de runtime de las operaciones que escriben el mapa y de ticket:block, y $casos47 de ticket:create, y $casos61 de las tres operaciones que cierran un ticket, y $casos66 del reparto de la escritura del mapa con --defer-map, y $casos73 de --project con un ticket o un Project, y $casos74 de las correcciones del mapa desde una resolución, y $casos75 de las entregas de diseño abiertas en frontier:query, con el transporte mockeado, sin red y sin credencial real, bajo Python $("$py39" -c 'import sys;print("%d.%d.%d" % sys.version_info[:3])')"
