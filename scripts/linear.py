#!/usr/bin/env python3
"""El adapter de Linear. El contrato de las doce operaciones y de los códigos de
salida vive en scripts/LINEAR-OPERATIONS.md."""
import argparse
import hashlib
import json
import os
import socket
import sys
import urllib.error
import urllib.request

ENDPOINT = "https://api.linear.app/graphql"

# Los ocho del ctx. Su segunda copia es la tabla Tipos de ticket de CONTEXT.md.
LABELS = ["map", "map:research", "map:prototype", "map:grilling", "map:task",
          "hitl:pm", "hitl:design", "hitl:dev"]

# Aparte de LABELS a propósito: Discovery es del equipo, se busca y nunca se crea.
DISCOVERY = "Discovery"

# El nombre del label del mapa, no su id: el ctx que cierra /map-new todavía dice
# map: null porque el label nació después del preflight. Constante y no argumento,
# para que no se pueda pasar el equivocado.
LABEL_MAPA = "map"

# Los seis encabezados del mapa, sin el "## ". El orden es contrato: el dict de
# sections se arma iterando esta lista, así que dos corridas sobre el mismo mapa
# emiten la misma línea.
ANCLAS = ["Destino", "Notas", "Decisiones hasta ahora", "Aún no especificado",
          "Fuera de alcance", "El colapso"]

# El séptimo encabezado, y a propósito FUERA de ANCLAS: no es un ancla de lectura, no
# lleva huella, y cortar_secciones tiene que seguir sin devolverle un cuerpo. Vive acá,
# junto a la otra lista que la primitiva de rangos mira, y no con quien escribe el
# esqueleto, porque desde que corta el recorrido la primitiva es su consumidora.
ANTES_DEL_MAPA = "Antes del mapa"

SIN_KEY = 3
SIN_TEAM = 4
SIN_CERRADOS = 5
SIN_LABEL_MAP = 6
NO_IMPLEMENTADO = 9


def die(codigo, mensaje, remediacion):
    """El único terminador del archivo: el único sys.exit vive acá. El tercer
    argumento no lleva default, así que olvidarlo es un TypeError y no una omisión."""
    print("linear.py: %s\n  remediación: %s" % (mensaje, remediacion), file=sys.stderr)
    sys.exit(codigo)


def ruta_key():
    # or, no el default de .get: con la variable seteada y vacía, .get devuelve una
    # ruta relativa al cwd y el instalador cae al default. Solo or coincide con los
    # tres casos de ${XDG_CONFIG_HOME:-$HOME/.config}.
    base = os.environ.get("XDG_CONFIG_HOME") or os.path.join(
        os.path.expanduser("~"), ".config")
    return os.path.join(base, "keiron-planner", "linear.key")


def leer_key():
    ruta = ruta_key()
    if not os.path.isfile(ruta):
        die(SIN_KEY, "no hay credencial de Linear en %s" % ruta,
            "corre /planner-setup")
    with open(ruta, encoding="utf-8") as fh:
        key = fh.read().strip()
    if not key:
        die(SIN_KEY, "la credencial guardada en %s está vacía" % ruta,
            "corre /planner-setup")
    return key


# Un solo POST, tres campos raíz, cero project y cero document. El preflight es de
# solo lectura y no emite ninguna mutation. La afirmación que lo asegura camina los
# nodos del AST y no el texto del archivo, así que este comentario es inofensivo.
PREFLIGHT_QUERY = """
query($team: String!, $labels: [String!]!) {
  viewer { id displayName }
  team(id: $team) {
    id key name
    defaultIssueState { id name }
    states(first: 50) { nodes { id name type position } }
  }
  issueLabels(first: 250, filter: { name: { in: $labels } }) {
    nodes { id name team { id } }
  }
}
"""


# Los tamaños de página van adentro del string y nunca en una constante: así la
# query y la medición de complejidad que la aprobó no pueden divergir. relations
# viaja sin nodes a propósito: el predicado no la lee, y no pedirla deja el payload
# incapaz de entregar un bloqueante por la conexión equivocada.
FRONTIER_QUERY = """
query($project: String!, $label: String!) {
  project(id: $project) {
    issues(first: 50, filter: { labels: { some: { name: { eq: $label } } } }) {
      pageInfo { hasNextPage }
      nodes {
        identifier
        title
        url
        createdAt
        state { id name }
        assignee { displayName }
        labels { nodes { name } }
        relations(first: 10) {
          pageInfo { hasNextPage }
        }
        inverseRelations(first: 10) {
          pageInfo { hasNextPage }
          nodes { type issue { identifier title url state { id } } }
        }
      }
    }
    projectMilestones(first: 10) {
      pageInfo { hasNextPage }
      nodes { id }
    }
  }
}
"""


# Un solo campo raíz, y es el markdown. El estado interno del editor de Linear no
# se pide en ninguna parte de este archivo: no es contrato y escribirlo de vuelta
# corrompe el documento.
MAP_READ_QUERY = """
query($project: String!) {
  project(id: $project) {
    content
  }
}
"""


def _post(query, variables, key):
    """La ÚNICA función que toca la red. El check de runtime la rebindea desde
    afuera para ejercitar los desenlaces del preflight sin red y sin credencial."""
    cuerpo = json.dumps({"query": query, "variables": variables}).encode("utf-8")
    pedido = urllib.request.Request(ENDPOINT, data=cuerpo, method="POST")
    pedido.add_header("Content-Type", "application/json")
    pedido.add_header("Authorization", key)
    try:
        with urllib.request.urlopen(pedido, timeout=30) as respuesta:
            return json.loads(respuesta.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        try:
            return json.loads(exc.read().decode("utf-8"))
        except ValueError:
            return {"errors": [{"message": "HTTP %s" % exc.code}]}
    # HTTPError va arriba porque es subclase de URLError: invertir el orden se come la
    # rama que ya existía. Y socket.timeout va aparte porque bajo 3.9 no deriva de
    # URLError, así que la cláusula de arriba no lo atrapa.
    except urllib.error.URLError as exc:
        return {"errors": [{"message": "no se pudo alcanzar %s: %s"
                                       % (ENDPOINT, exc.reason)}]}
    except socket.timeout:
        return {"errors": [{"message": "%s no respondió a tiempo" % ENDPOINT}]}


def resolver_ctx(payload, bootstrap, team):
    """Pura: de la respuesta al ctx. Tres de las cuatro fallas duras viven acá."""
    if payload.get("errors"):
        die(SIN_KEY, "la API de Linear rechazó la credencial guardada",
            "corre /planner-setup de nuevo con una key nueva")
    datos = payload.get("data") or {}
    equipo = datos.get("team")
    if not equipo:
        die(SIN_TEAM, "el team %s no existe o la credencial no lo ve" % team,
            "revisa la key del team y los permisos de la credencial")
    estados = (equipo.get("states") or {}).get("nodes") or []
    cerrados = sorted([e for e in estados if e.get("type") == "completed"],
                       key=lambda e: e.get("position") or 0)
    cancelados = sorted([e for e in estados if e.get("type") == "canceled"],
                         key=lambda e: e.get("position") or 0)
    if not cerrados or not cancelados:
        die(SIN_CERRADOS,
            "el team %s no tiene ningún estado de tipo completed, o ninguno de "
            "tipo canceled" % team,
            "crea los estados que faltan en el workflow del team")
    encontrados = {}
    for nodo in ((datos.get("issueLabels") or {}).get("nodes") or []):
        encontrados[nodo.get("name")] = nodo.get("id")
    labels = {}
    for nombre in LABELS:
        labels[nombre] = encontrados.get(nombre)
    if labels["map"] is None and not bootstrap:
        die(SIN_LABEL_MAP, "el label map no existe en el workspace",
            "corre /map-new, que pasa --bootstrap al preflight")
    faltantes = [n for n in LABELS if labels[n] is None]
    if faltantes:
        print("aviso: faltan labels, los crea el primer ticket:create: %s"
              % ", ".join(faltantes), file=sys.stderr)
    return {
        "viewer": (datos.get("viewer") or {}).get("id"),
        "team": equipo.get("id"),
        "done": cerrados[0].get("id"),
        "canceled": cancelados[0].get("id"),
        "default": (equipo.get("defaultIssueState") or {}).get("id"),
        "labels": labels,
        "discovery": encontrados.get(DISCOVERY),
    }


def cmd_preflight(args):
    key = leer_key()
    payload = _post(PREFLIGHT_QUERY,
                     {"team": args.team, "labels": LABELS + [DISCOVERY]}, key)
    ctx = resolver_ctx(payload, args.bootstrap, args.team)
    print(json.dumps(ctx, separators=(",", ":")))


def resolver_datos(payload):
    """La puerta compartida de las dos operaciones de lectura. Un data.project nulo
    no es falla dura: el llamador lo emite como found: false y sale en cero."""
    errores = payload.get("errors")
    if errores:
        # Una entrada puede no traer message, o no ser un dict: HTTPError sintetiza
        # la suya con un solo campo, pero el shape real de Linear no está prometido.
        textos = []
        for error in errores:
            mensaje = error.get("message") if isinstance(error, dict) else None
            textos.append(str(mensaje) if mensaje is not None else str(error))
        die(SIN_KEY,
            "la API de Linear devolvió un error para esta consulta: %s"
            % "; ".join(textos),
            "revisa el mensaje de arriba; si nombra la credencial corre "
            "/planner-setup de nuevo con una key nueva, si no, puede ser un "
            "límite temporal o un problema de la consulta")
    return (payload.get("data") or {}).get("project")


def es_frontera_del_mapa(linea):
    """True si la línea es el encabezado que cierra el mapa. Un solo sitio de
    definición porque tiene dos consumidores: rangos_de_anclas, para saber dónde dejar
    de mirar, y la guarda de adopción de map:create, para saber que este Project ya
    pasó por acá."""
    return linea.rstrip() == "## " + ANTES_DEL_MAPA


def normalizar(texto):
    """El array de líneas sobre el que trabajan la lectura y la escritura. Es función
    y no una línea repetida porque tiene dos consumidores: cortar_secciones y el paso
    uno del read-modify-write."""
    return texto.replace("\r\n", "\n").replace("\r", "\n").split("\n")


def rangos_de_anclas(lineas):
    """La única función que parsea encabezados de ancla. Pura: no imprime y no termina.
    Devuelve (rangos, duplicadas). rangos es {ancla: (i_inicio, i_fin)} sobre el array
    original, con i_inicio la línea siguiente al encabezado de su PRIMERA aparición e
    i_fin la primera línea que vuelve a ser un encabezado de nivel uno o dos, o el fin
    del recorrido. duplicadas son las anclas cuyo encabezado aparece más de una vez, en
    orden de documento y una sola vez cada una. El recorrido TERMINA en el encabezado
    de la frontera: el mapa se acaba ahí y lo de abajo es zona inerte. Solo rstrip al
    buscar el ancla y nunca lstrip, para que una línea indentada no se dispute la
    sección con la de verdad."""
    fin = len(lineas)
    for indice, linea in enumerate(lineas):
        if es_frontera_del_mapa(linea):
            fin = indice
            break
    encabezados = dict(("## " + ancla, ancla) for ancla in ANCLAS)
    primera = {}
    duplicadas = []
    for indice in range(fin):
        ancla = encabezados.get(lineas[indice].rstrip())
        if ancla is None:
            continue
        if ancla not in primera:
            primera[ancla] = indice
        elif ancla not in duplicadas:
            duplicadas.append(ancla)
    rangos = {}
    for ancla in primera:
        inicio = primera[ancla]
        corte = fin
        for indice in range(inicio + 1, fin):
            limpia = lineas[indice].rstrip()
            # Un encabezado de nivel tres o más profundo no matchea ninguno de los dos
            # prefijos, así que pertenece al cuerpo.
            if limpia.startswith("## ") or limpia.startswith("# "):
                corte = indice
                break
        rangos[ancla] = (inicio + 1, corte)
    return rangos, duplicadas


def cortar_secciones(texto):
    """Pura salvo por el aviso: del overview a los seis cuerpos. El aviso de ancla
    duplicada vive acá y no en la primitiva porque avisar y seguir es regla de LECTURA:
    la primitiva reporta el hecho y cada llamador elige su política."""
    lineas = normalizar(texto)
    rangos, duplicadas = rangos_de_anclas(lineas)
    for ancla in duplicadas:
        # Se hashea la primera aparición y map:read sale en cero igual: abortar
        # por ancla ambigua es regla de escritura, no de lectura.
        print("aviso: el ancla %s aparece más de una vez: se hashea la "
              "primera" % ancla, file=sys.stderr)
    cuerpos = dict((ancla, None) for ancla in ANCLAS)
    for ancla in ANCLAS:
        if ancla in rangos:
            inicio, corte = rangos[ancla]
            cuerpos[ancla] = lineas[inicio:corte]
    return cuerpos


def huellas(cuerpos):
    """La otra mitad de la regla que map:write va a tener que reproducir: sha256
    completo, sin truncar. None es que falta el ancla y nunca que la sección esté
    vacía, que lleva la huella de la cadena vacía. Los espacios del principio de una
    línea no se tocan: son el anidado de una viñeta y son señal."""
    salida = {}
    for ancla in ANCLAS:
        lineas = cuerpos.get(ancla)
        if lineas is None:
            salida[ancla] = None
            continue
        cuerpo = "\n".join(linea.rstrip() for linea in lineas).strip("\n")
        salida[ancla] = hashlib.sha256(cuerpo.encode("utf-8")).hexdigest()
    return salida


def bloqueantes_abiertos(nodo, cerrados):
    """La única función que nombra inverseRelations e issue a la vez: los bloqueos
    salen de ahí y nunca de relations. Devuelve la lista, y la lista vacía es el
    'sin bloqueantes abiertos' de la tercera condición del predicado."""
    abiertos = []
    for rel in ((nodo.get("inverseRelations") or {}).get("nodes") or []):
        if rel.get("type") != "blocks":
            continue
        bloqueante = rel.get("issue") or {}
        if (bloqueante.get("state") or {}).get("id") in cerrados:
            continue
        abiertos.append({"identifier": bloqueante.get("identifier"),
                         "title": bloqueante.get("title"),
                         "url": bloqueante.get("url")})
    return abiertos


def clasificar_frontera(nodos, cerrados):
    """Las tres condiciones, el orden y el reparto en las dos listas, en un solo
    recorrido. cerrados es el par de ids del ctx: nunca state.type, porque el team
    tiene dos estados canceled y uno de ellos se llama Blocked."""
    tomables, no_tomables = [], []
    for nodo in sorted(nodos, key=lambda n: (n.get("createdAt") or "",
                                             n.get("identifier") or "")):
        if (nodo.get("state") or {}).get("id") in cerrados:
            continue
        asignado = (nodo.get("assignee") or {}).get("displayName")
        bloqueantes = bloqueantes_abiertos(nodo, cerrados)
        entrada = {
            "identifier": nodo.get("identifier"),
            "title": nodo.get("title"),
            "url": nodo.get("url"),
            "createdAt": nodo.get("createdAt"),
            "labels": [etiqueta.get("name") for etiqueta
                       in ((nodo.get("labels") or {}).get("nodes") or [])],
        }
        if asignado is None and not bloqueantes:
            tomables.append(entrada)
            continue
        entrada["assignee"] = asignado
        entrada["blockers"] = bloqueantes
        no_tomables.append(entrada)
    return tomables, no_tomables


def truncadas(proyecto):
    """Los nombres de las conexiones cortadas, en el orden fijo del contrato. Nombra
    relations e inverseRelations pero nunca issue, así que no lee un bloqueante."""
    conexion = proyecto.get("issues") or {}
    nodos = conexion.get("nodes") or []
    cortadas = []
    if (conexion.get("pageInfo") or {}).get("hasNextPage"):
        cortadas.append("issues")
    if any(((n.get("relations") or {}).get("pageInfo") or {}).get("hasNextPage")
           for n in nodos):
        cortadas.append("relations")
    if any(((n.get("inverseRelations") or {}).get("pageInfo") or {}).get("hasNextPage")
           for n in nodos):
        cortadas.append("inverseRelations")
    hitos = proyecto.get("projectMilestones") or {}
    if (hitos.get("pageInfo") or {}).get("hasNextPage"):
        cortadas.append("projectMilestones")
    return cortadas


def cmd_map_read(args):
    key = leer_key()
    payload = _post(MAP_READ_QUERY, {"project": args.project}, key)
    proyecto = resolver_datos(payload)
    crudo = None if proyecto is None else proyecto.get("content")
    if crudo is None:
        # Un Project que no resolvió y un Project sin overview llevan la misma forma
        # vacía, y found es lo único que los separa. Un "" no se colapsa a null: la
        # diferencia entre "no hay overview" y "el overview está vacío" no cuesta
        # nada conservar.
        salida = {"found": proyecto is not None, "content": None,
                  "sections": dict((ancla, None) for ancla in ANCLAS)}
    else:
        # El paso 1 de la regla de la huella, una sola vez y sobre todo el texto:
        # content sale ya normalizado, así que las seis huellas se reproducen desde
        # content y nada más, sin conocer el payload crudo.
        texto = crudo.replace("\r\n", "\n").replace("\r", "\n")
        salida = {"found": True, "content": texto,
                  "sections": huellas(cortar_secciones(texto))}
    print(json.dumps(salida, separators=(",", ":")))


def cmd_frontier_query(args):
    ctx = json.loads(args.ctx)
    cerrados = {ctx["done"], ctx["canceled"]}
    key = leer_key()
    payload = _post(FRONTIER_QUERY,
                    {"project": args.project, "label": LABEL_MAPA}, key)
    proyecto = resolver_datos(payload)
    if proyecto is None:
        # found es lo único que separa un --project que no resolvió de un mapa ya
        # colapsado: los dos llevan los conteos en cero y las dos listas vacías.
        salida = {"found": False, "truncated": [],
                  "counts": {"open": 0, "takeable": 0, "milestones": 0},
                  "tickets": [], "notTakeable": []}
    else:
        cortadas = truncadas(proyecto)
        # Cada conexión cortada miente distinto: decirle a quien perdió relations
        # que un ticket bloqueado puede parecer tomable sería falso.
        consecuencias = {
            "issues": "los dos conteos son cotas inferiores y falta frontera",
            "relations": "no afecta la frontera: el predicado no lee esta conexión",
            "inverseRelations": "un ticket bloqueado puede parecer tomable, y la "
                                "lista de bloqueantes de una entrada puede venir "
                                "incompleta",
            # No es "ninguna": el veredicto sobrevive porque solo necesita cero
            # contra más de cero, y una página cortada trajo al menos un nodo. Lo
            # que sí queda mal es el número.
            "projectMilestones": "el veredicto no cambia, porque solo distingue "
                                 "cero de más de cero, pero counts.milestones "
                                 "queda como cota inferior",
        }
        for nombre in cortadas:
            print("aviso: %s vino truncada: %s" % (nombre, consecuencias[nombre]),
                  file=sys.stderr)
        tomables, no_tomables = clasificar_frontera(
            (proyecto.get("issues") or {}).get("nodes") or [], cerrados)
        nodos_hitos = (proyecto.get("projectMilestones") or {}).get("nodes") or []
        salida = {"found": True, "truncated": cortadas,
                  "counts": {"open": len(tomables) + len(no_tomables),
                             "takeable": len(tomables),
                             "milestones": len(nodos_hitos)},
                  "tickets": tomables, "notTakeable": no_tomables}
    print(json.dumps(salida, separators=(",", ":")))


def cmd_stub(args):
    die(NO_IMPLEMENTADO,
        "el subcomando %s todavía no está implementado" % args.operacion,
        "espera al corte que lo construye")


def construir_parser():
    parser = argparse.ArgumentParser(prog="linear.py")
    # required=True: sin él, un adapter invocado sin subcomando sale 1 o 0 en vez de 2.
    subs = parser.add_subparsers(dest="operacion", required=True)

    # Los doce se declaran explícitos, sin bucle: con un bucle el AST ve un solo
    # literal y las afirmaciones sobre el conjunto de subcomandos se vuelven vacuas.
    p_preflight = subs.add_parser("preflight")
    p_preflight.add_argument("--team", required=True)
    p_preflight.add_argument("--bootstrap", action="store_true")
    p_preflight.set_defaults(func=cmd_preflight)

    p_map_create = subs.add_parser("map:create")
    p_map_create.add_argument("--ctx", required=True)
    p_map_create.set_defaults(func=cmd_stub)

    p_map_read = subs.add_parser("map:read")
    p_map_read.add_argument("--project", required=True)
    p_map_read.set_defaults(func=cmd_map_read)

    p_map_write = subs.add_parser("map:write")
    p_map_write.set_defaults(func=cmd_stub)

    p_ticket_create = subs.add_parser("ticket:create")
    p_ticket_create.add_argument("--ctx", required=True)
    p_ticket_create.set_defaults(func=cmd_stub)

    p_ticket_block = subs.add_parser("ticket:block")
    p_ticket_block.set_defaults(func=cmd_stub)

    p_frontier_query = subs.add_parser("frontier:query")
    p_frontier_query.add_argument("--ctx", required=True)
    p_frontier_query.add_argument("--project", required=True)
    p_frontier_query.set_defaults(func=cmd_frontier_query)

    p_ticket_claim = subs.add_parser("ticket:claim")
    p_ticket_claim.add_argument("--ctx", required=True)
    p_ticket_claim.set_defaults(func=cmd_stub)

    p_ticket_resolve = subs.add_parser("ticket:resolve")
    p_ticket_resolve.add_argument("--ctx", required=True)
    p_ticket_resolve.set_defaults(func=cmd_stub)

    p_ticket_rule_out = subs.add_parser("ticket:rule-out")
    p_ticket_rule_out.add_argument("--ctx", required=True)
    p_ticket_rule_out.set_defaults(func=cmd_stub)

    p_milestone_create = subs.add_parser("milestone:create")
    p_milestone_create.set_defaults(func=cmd_stub)

    p_work_write = subs.add_parser("work:write")
    p_work_write.add_argument("--ctx", required=True)
    p_work_write.set_defaults(func=cmd_stub)

    return parser


def main(argv):
    args = construir_parser().parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main(sys.argv[1:])
