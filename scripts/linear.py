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

# Los nueve del ctx. Su segunda copia es la tabla Tipos de ticket de CONTEXT.md.
# El orden es contrato: TIPOS y HITL salen de acá por posición.
LABELS = ["map", "map:research", "map:prototype", "map:grilling", "map:task",
          "hitl:pm", "hitl:design", "hitl:dev", "map:no-landing"]

# Aparte de LABELS a propósito: Discovery es del equipo, se busca y nunca se crea.
DISCOVERY = "Discovery"

# Los cuatro tipos y los tres roles, tomados de LABELS por posición y nunca reescritos:
# una segunda copia de esos nombres se desincroniza en el primer rename, y el orden de
# LABELS ya es contrato. El primero de la lista, map, no es un tipo, y el noveno,
# map:no-landing, lo aplica work:write y nunca un ticket de decisión.
TIPOS = LABELS[1:5]
HITL = LABELS[5:8]

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

# Las tres anclas que map:write edita, tomadas de ANCLAS por posición y nunca
# reescritas: una segunda copia del texto del encabezado se desincroniza en el primer
# rename, y el orden de ANCLAS ya es contrato.
ANCLA_DECISIONES = ANCLAS[2]
ANCLA_NIEBLA = ANCLAS[3]
ANCLA_FUERA = ANCLAS[4]

# Las seis secciones del comentario de resolución, sin el "## ", en su orden de
# contrato. Misma regla que ANCLAS: el orden ES contrato, el render itera esta lista y
# nunca el argv, y su segunda copia es el bloque de El comentario de resolución de
# map-templates.md, que la afirmación 43 compara contra esta constante.
SECCIONES = ["La decisión", "Por qué", "Lo que se cayó", "Niebla graduada",
             "Tickets nuevos", "Qué corrige o empuja"]

SIN_KEY = 3
SIN_TEAM = 4
SIN_CERRADOS = 5
SIN_LABEL_MAP = 6
NO_IMPLEMENTADO = 9

# El tope de intentos del read-modify-write, y NO un código de salida: va en su propio
# bloque para que nadie lo lea como el quinto. Es el único literal del contador en todo
# el archivo, y el handler que reintenta lo referencia por nombre en el iter de su For.
MAX_INTENTOS = 2


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


# No pide project { content } de vuelta: releer lo que se acaba de escribir es
# verificación posterior a la escritura, y está prohibida. Y tampoco pide el estado
# interno del editor de Linear, que no se nombra en ninguna parte de este archivo: no es
# contrato, y escribirlo de vuelta corrompe el documento.
PROJECT_UPDATE = """
mutation($project: String!, $content: String!) {
  projectUpdate(id: $project, input: { content: $content }) {
    success
  }
}
"""


# Pide success y el id y la url del Project recién nacido, y eso NO es verificación
# posterior a la escritura: es el payload de la propia mutation, en el mismo round trip,
# y es el único camino para que quien la invoque sepa qué Project acaba de nacer. No pide
# content de vuelta ni el estado interno del editor. Que el contenido viaje en el mismo
# POST es lo que hace que crear cueste uno solo, y también lo que vuelve ambigua su falla.
PROJECT_CREATE = """
mutation($team: String!, $name: String!, $content: String!) {
  projectCreate(input: { teamId: $team, name: $name, content: $content }) {
    success
    project { id url }
  }
}
"""


ISSUE_LABEL_CREATE = """
mutation($nombre: String!) {
  issueLabelCreate(input: { name: $nombre }) {
    success
    issueLabel { id name }
  }
}
"""

ISSUE_BATCH_CREATE = """
mutation($issues: [IssueCreateInput!]!) {
  issueBatchCreate(input: { issues: $issues }) {
    success
    issues { id identifier title url }
  }
}
"""

# El nombre de las variables es lo que hace legible la orientación en el sitio de
# llamada, y es deliberado: un issueId: $a se puede leer mal, un issueId: $bloqueante
# no. El bloqueante SIEMPRE del lado issue.
ISSUE_RELATION_CREATE = """
mutation($bloqueante: String!, $bloqueado: String!) {
  issueRelationCreate(input: {
    type: blocks, issueId: $bloqueante, relatedIssueId: $bloqueado
  }) {
    success
    issueRelation { id }
  }
}
"""

# La respuesta va como comentario y nunca en el cuerpo del ticket: la pregunta queda
# inmutable y auditable, y la respuesta gana autor y timestamp gratis. Pide id y url de
# vuelta, y eso NO es verificación posterior a la escritura: es el payload de la propia
# mutation, en el mismo round trip, y es lo único que deja reportar dónde quedó. Sus dos
# campos son un identificador y texto, así que no lleva ningún enum.
COMMENT_CREATE = """
mutation($issue: String!, $body: String!) {
  commentCreate(input: { issueId: $issue, body: $body }) {
    success
    comment { id url }
  }
}
"""

# Una sola constante para las tres escrituras que cambian un campo de un issue que ya
# existe: la toma, la devolución de la toma y el estado. El input viaja entero como
# variable porque es el mismo campo de la API en los tres casos, y dos constantes serían
# dos copias de una forma. Quien construye el input es cada handler, con su propio dict
# literal, así que el AST sigue viendo qué clave escribe cada uno sin seguir argumentos.
# Pedir issue de vuelta NO es verificación posterior a la escritura: es el payload de la
# propia mutation, en el mismo round trip, y es lo único que deja reportar dónde quedó.
# Ningún argumento de acá es un enum de GraphQL: los cuatro campos que se escriben son
# identificadores o texto, así que el defecto del enum entrecomillado no tiene dónde
# ocurrir. El único enum del archivo sigue viviendo en ISSUE_RELATION_CREATE.
ISSUE_UPDATE = """
mutation($issue: String!, $input: IssueUpdateInput!) {
  issueUpdate(id: $issue, input: $input) {
    success
    issue { identifier url assignee { displayName } state { name } }
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


def _sin_marcador(linea):
    """La línea sin su marcador de viñeta ni su indentación. El despojo no es cosmética:
    el serializador de Linear reescribe el guion como asterisco al guardar, así que un
    matcher anclado en el guion dejaría de encontrar sus propias viñetas después de la
    primera escritura."""
    resto = linea.strip()
    if len(resto) > 1 and resto[0] in ("-", "*", "+") and resto[1] == " ":
        resto = resto[1:].lstrip(" ")
    return resto


def titulo_en_negrita(linea):
    """El título de una viñeta de niebla, o None. Es la subcadena entre el primer par de
    ** de la línea, verbatim, con su punto final si lo tiene: es la misma cadena que
    --remove-fog recibe como argumento, así que las dos mitades no pueden divergir. Que
    el cierre se busque desde el índice dos es lo que garantiza que el título no
    contenga otro par de asteriscos."""
    resto = _sin_marcador(linea)
    if not resto.startswith("**"):
        return None
    cierre = resto.find("**", 2)
    if cierre < 0:
        return None
    return resto[2:cierre] or None


def _es_continuacion(linea):
    """Una línea que pertenece a la viñeta de arriba: no vacía, indentada, y que no
    arranca una viñeta nueva."""
    if not linea.strip() or not linea.startswith(" "):
        return False
    marca = linea.strip()
    return not (len(marca) > 1 and marca[0] in ("-", "*", "+") and marca[1] == " ")


def _clave_de_unicidad(linea):
    """Con qué se compara si una línea ya está. El título en negrita cuando la línea lo
    tiene, porque una viñeta con el mismo título es la misma entrada aunque el cuerpo
    haya cambiado, y la línea despojada de su marcador cuando no lo tiene, que es el
    caso de una decisión."""
    return titulo_en_negrita(linea) or _sin_marcador(linea)


def _sin_saltos(etiqueta, valor):
    """Un valor de una sola línea física. El adapter no envuelve texto, así que un salto
    adentro de un argumento produciría markdown que nadie escribió."""
    if "\n" in valor or "\r" in valor:
        die(SIN_KEY,
            "%s recibió un valor con un salto de línea y tiene que ser una sola "
            "línea: %r" % (etiqueta, valor),
            "sacá el salto de línea del argumento y volvé a correr")


def _no_es_encabezado(etiqueta, valor):
    """La guarda de la frontera. Mira el VALOR que llegó por argumento y no la línea
    renderizada: la línea lleva el marcador de viñeta adelante, así que nunca empezaría
    con una almohadilla y la guarda no mordería nunca. Un valor que es un encabezado de
    nivel uno o dos parte en dos la sección donde cae, y si además es el de la frontera
    corta el mapa entero de ahí para abajo en toda lectura futura."""
    limpio = valor.rstrip()
    if limpio.startswith("## ") or limpio.startswith("# "):
        die(SIN_KEY,
            "%s recibió %r, y una línea del mapa no puede ser un encabezado"
            % (etiqueta, valor),
            "sacale las almohadillas del principio y volvé a correr")


def _validar_vineta(etiqueta, valor):
    """Las cinco reglas de forma de una viñeta con título en negrita, sobre el valor que
    llegó por argumento. La comparten los dos flags que agregan una viñeta, y la etiqueta
    es un parámetro para que el mensaje nombre el flag que la persona escribió. Devuelve
    el título, que es además su clave de unicidad. La guarda del encabezado no hace falta
    acá: la regla de que el valor empieza con ** ya impide que la viñeta sea un
    encabezado."""
    _sin_saltos(etiqueta, valor)
    titulo = titulo_en_negrita(valor) if valor.startswith("**") else None
    if titulo is None:
        die(SIN_KEY,
            "%s recibió %r, y la viñeta tiene que empezar con su título entre dobles "
            "asteriscos" % (etiqueta, valor),
            'escribila como "**Título.** cuerpo" y volvé a correr')
    cuerpo = valor[valor.find("**", 2) + 2:]
    if cuerpo[:1] != " " or cuerpo[1:2] == " " or not cuerpo.strip():
        die(SIN_KEY,
            "%s recibió %r, y después del título cerrado tiene que venir exactamente "
            "un espacio y un cuerpo no vacío" % (etiqueta, valor),
            'escribila como "**Título.** cuerpo" y volvé a correr')
    return titulo


def _validar_gist(etiqueta, gist):
    """El tope de 120 caracteres del gist, y la ÚNICA casa del literal en todo el
    archivo. La comparten el --append-decision de map:write y el --gist de la resolución,
    y la etiqueta es un parámetro para que el mensaje nombre el flag que la persona
    escribió, igual que en _validar_vineta.

    Cubre el tope y nada más. Las otras dos guardas del valor, _sin_saltos y
    _no_es_encabezado, las aplica cada llamador por su cuenta: en map:write se intercalan
    con las del enlace, que viaja en el mismo flag, y meterlas acá adentro cambiaría qué
    mensaje ve una invocación que falla por dos motivos a la vez."""
    if len(gist) > 120:
        die(SIN_KEY,
            "el gist de %s tiene %s caracteres y el tope es de 120: %r"
            % (etiqueta, len(gist), gist),
            "acortá el gist; el detalle va en el comentario de resolución del "
            "ticket y el mapa nunca lo repite")


def _linea_de_decision(enlace, gist):
    """La ÚNICA casa del formato de una línea de Decisiones hasta ahora: marcador,
    enlace, dos puntos y gist. La comparten las tres puntas que la necesitan, el
    --append-decision de map:write, la quinta escritura de ticket:resolve y la impresión
    que la reemplaza con --defer-map, así que ninguna la escribe a mano y no pueden
    divergir. Misma regla que _validar_gist, que es la única casa del literal 120."""
    return "- %s: %s" % (enlace, gist)


def _linea_de_vineta(valor):
    """La ÚNICA casa del marcador de una viñeta del mapa, la de niebla y la de Fuera de
    alcance. Recibe el valor ya validado por _validar_vineta y solo le pone el
    marcador."""
    return "- %s" % valor


def _cuerpo_de_secciones(args):
    """El markdown del comentario de resolución, armado por el adapter y nunca por el
    modelo. Valida antes de renderizar: acá se rompe todo lo que se pueda romper sin
    haber tocado la red. La comparten las dos operaciones que cierran un ticket.

    El orden ADENTRO de una sección es el de la línea de comandos. El orden ENTRE
    secciones lo pone SECCIONES y nunca el argv, así que dos invocaciones con las mismas
    líneas en otro orden de flags producen el mismo comentario.

    Las seis son obligatorias y ninguna puede venir sin líneas, y esa es la regla que
    vuelve mecánicamente imposible saltearse la graduación de niebla en silencio: la
    sección tiene que existir, así que el negativo hay que escribirlo a mano. El adapter
    no puede juzgar si el contenido es correcto, pero sí puede negarse a escribir un
    comentario con una sección vacía, y eso convierte un olvido mudo en una salida no
    cero."""
    lineas = {}
    for nombre, linea in args.section:
        if nombre not in SECCIONES:
            die(SIN_KEY,
                "--section recibió %r, que no es ninguna de las seis secciones del "
                "comentario de resolución" % nombre,
                "las seis son, en este orden: %s" % ", ".join(SECCIONES))
        # Las dos guardas reusadas verbatim. La segunda es la que impide forjar una
        # séptima sección desde adentro del cuerpo de otra.
        _sin_saltos("--section", linea)
        _no_es_encabezado("--section", linea)
        lineas.setdefault(nombre, []).append(linea)
    faltantes = [n for n in SECCIONES if not lineas.get(n)]
    if faltantes:
        die(SIN_KEY,
            "estas secciones del comentario no recibieron ninguna línea: %s"
            % ", ".join(faltantes),
            "pasá al menos un --section por cada una de las seis; cuando no hay nada "
            "que nombrar, la línea lo dice explícito, por ejemplo ninguna")
    return "\n\n".join("## %s\n\n%s" % (nombre, "\n".join(lineas[nombre]))
                       for nombre in SECCIONES)


def _validar_ticket(etiqueta, titulo, cuerpo, etiquetas):
    """Las cuatro guardas de un ticket de decisión nuevo, sobre los tres valores que
    llegaron por argumento. La comparten el --ticket de ticket:create y el --new-ticket
    de las dos operaciones que cierran un ticket, y la etiqueta es un parámetro para que
    el mensaje nombre el flag que la persona escribió, igual que en _validar_vineta.
    Devuelve (titulo, cuerpo, nombres)."""
    _sin_saltos(etiqueta, titulo)
    _sin_saltos(etiqueta, cuerpo)
    if not titulo.strip() or not cuerpo.strip():
        die(SIN_KEY,
            "%s recibió un título o un cuerpo vacío: %r" % (etiqueta, titulo),
            "el título es la pregunta en prosa y el cuerpo es esa pregunta y nada "
            "más; ninguno de los dos puede ir vacío")
    nombres = [n for n in etiquetas.split(",") if n]
    ajenos = [n for n in nombres if n not in TIPOS + HITL]
    if ajenos:
        die(SIN_KEY,
            "%s %r recibió labels que no son ni un tipo ni un rol: %s"
            % (etiqueta, titulo, ", ".join(ajenos)),
            "pasá a lo sumo un tipo de %s y los roles de %s; map y map:no-landing "
            "no se piden acá" % (", ".join(TIPOS), ", ".join(HITL)))
    del_tipo = [n for n in nombres if n in TIPOS]
    if len(del_tipo) > 1:
        die(SIN_KEY,
            "%s %r lleva más de un tipo a la vez y un ticket tiene a lo "
            "sumo uno: %s" % (etiqueta, titulo, ", ".join(del_tipo)),
            "dejá un solo tipo, o ninguno si el ticket es AFK, y volvé a correr")
    return (titulo, cuerpo, nombres)


def _validar_par(etiqueta, sustantivo, pares, bloqueante, bloqueado):
    """Las tres guardas de un par de bloqueo, contra los pares que ya pasaron por acá en
    esta misma invocación. La comparten el --block de ticket:block, donde los dos lados
    son ids, y el de las dos operaciones que cierran un ticket, donde son títulos: el
    sustantivo es un parámetro para que el mensaje diga cuál de los dos recibió.

    Un par cuyos dos lados son iguales aborta, y eso no es celo: un ticket que se bloquea
    a sí mismo no vuelve a ser tomable nunca, y no hay ninguna operación en el plugin
    para deshacerlo. El mismo criterio corre contra un --block exacto repetido y contra
    su recíproco, porque las dos formas terminan en dos issueRelationCreate
    independientes y ningún guard de más abajo las nota.

    Esto NO es un detector de ciclos: A→B, B→C y C→A en la misma corrida pasa entero,
    porque cada par se compara solo contra los que ya vinieron antes y no contra la
    cadena completa. Tampoco cubre B bloqueado por A escrito en una invocación aparte de
    la que trajo A bloqueado por B: acá nunca se leen las relaciones que ya existen en
    Linear, así que ese caso cruzado de invocaciones no tiene cómo detectarse acá."""
    if bloqueante == bloqueado:
        die(SIN_KEY,
            "%s recibió el mismo %s de los dos lados: %r"
            % (etiqueta, sustantivo, bloqueante),
            "un ticket que se bloquea a sí mismo no vuelve a ser tomable, y no hay "
            "operación en el plugin para deshacerlo")
    if (bloqueante, bloqueado) in pares:
        die(SIN_KEY,
            "%s repitió el mismo par dos veces: %r bloqueado por %r" %
            (etiqueta, bloqueado, bloqueante),
            "sacá el %s duplicado, escribir la misma relación dos veces no "
            "aporta nada" % etiqueta)
    if (bloqueado, bloqueante) in pares:
        die(SIN_KEY,
            "%s recibió %r bloqueado por %r y también %r bloqueado por %r "
            "en la misma corrida"
            % (etiqueta, bloqueado, bloqueante, bloqueante, bloqueado),
            "elegí un solo sentido: dos tickets bloqueándose mutuamente no vuelven "
            "a ser tomables nunca")


def _cableado_de(args, tickets):
    """Los pares de --block resueltos contra los títulos de los --new-ticket de ESTA
    misma invocación, y nunca contra un id: los ids no existen hasta que la primera
    escritura vuelve. Los dos lados tienen que ser tickets nuevos, así que cablear el
    ticket que se está cerrando no matchea y aborta: ese ticket queda en Done en la
    escritura siguiente, y la rama que sí necesita bloquearlo es la de otro rol, que no
    pasa por esta operación. Devuelve los pares de títulos, en el orden de argv."""
    titulos = [titulo for titulo, _, _ in tickets]
    pares = []
    for bloqueante, bloqueado in args.block:
        for lado in (bloqueante, bloqueado):
            cuantos = titulos.count(lado)
            if cuantos != 1:
                die(SIN_KEY,
                    "--block nombra %r, y entre los --new-ticket de esta invocación "
                    "ese título aparece %s veces" % (lado, cuantos),
                    "los dos lados de un --block tienen que ser el título exacto de un "
                    "--new-ticket de esta misma invocación, y de uno solo; los "
                    "declarados son: %s" % (", ".join(titulos) or "ninguno"))
        _validar_par("--block", "título", pares, bloqueante, bloqueado)
        pares.append((bloqueante, bloqueado))
    return pares


def _issue_de(args):
    """El identificador del ticket sobre el que se opera, validado. Lo comparten las tres
    operaciones que escriben sobre un ticket ya existente."""
    _sin_saltos("--issue", args.issue)
    if not args.issue.strip():
        die(SIN_KEY, "--issue llegó vacío o con espacios solos: %r" % args.issue,
            "pasá el identificador del ticket, CRM-123, tal como lo devolvió "
            "frontier:query")
    return args.issue


def _ctx_de(args):
    """El blob del preflight parseado. Su única falla es que no parsee: el blob es opaco
    y quien lo edita a mano ya rompió el contrato."""
    try:
        return json.loads(args.ctx)
    except ValueError:
        die(SIN_KEY, "--ctx no parsea como JSON: %r" % args.ctx,
            "pasá el blob que emitió el preflight, sin editarlo")


def _niebla_de(args):
    """Las viñetas de niebla que se abren y los títulos que se gradúan, ya validados, más
    la guarda de consistencia contra la sección que los cuenta. Devuelve (niebla,
    graduadas), con niebla ya renderizada con su marcador.

    La guarda es la mitad decidible de la regla: todo título que esta resolución saca del
    mapa tiene que estar nombrado en alguna línea de la sección que lo cuenta. La inversa,
    que la sección no nombre un parche que no se removió, NO es decidible acá, porque la
    sección es prosa y un título puede nombrarse justamente para decir que NO se graduó.
    Queda declarada como brecha, con la misma honestidad con que la afirmación 25 declara
    la suya."""
    niebla = []
    for valor in args.append_fog:
        _validar_vineta("--append-fog", valor)
        niebla.append(_linea_de_vineta(valor))
    graduadas = []
    for titulo in args.remove_fog:
        _sin_saltos("--remove-fog", titulo)
        if not titulo.strip():
            die(SIN_KEY, "--remove-fog recibió un título vacío",
                "pasá el título de la viñeta, sin los asteriscos")
        graduadas.append(titulo)
    # Por posición y nunca reescrito, igual que ANCLA_DECISIONES sale de ANCLAS: el
    # orden de SECCIONES ya es contrato y una segunda copia del texto se desincroniza en
    # el primer rename.
    contadas = [linea for nombre, linea in args.section if nombre == SECCIONES[3]]
    mudas = [t for t in graduadas if not any(t in linea for linea in contadas)]
    if mudas:
        die(SIN_KEY,
            "estos títulos se gradúan del mapa y no los nombra ninguna línea de la "
            "sección %s del comentario: %s" % (SECCIONES[3], ", ".join(mudas)),
            "nombralos en esa sección, o sacá el --remove-fog: una niebla que se va del "
            "mapa sin que el comentario diga por qué no deja rastro de la graduación")
    return niebla, graduadas


def _resolucion_de(args):
    """Todo lo que ticket:resolve puede romper sin un round trip, roto acá y en un solo
    lugar, antes del primer POST. Mismo orden que ticket:create y ticket:block ya usan:
    la función pura primero, después leer_key, y recién entonces la red."""
    ctx = _ctx_de(args)
    issue = _issue_de(args)
    cuerpo = _cuerpo_de_secciones(args)
    _sin_saltos("--gist", args.gist)
    if not args.gist.strip():
        die(SIN_KEY, "--gist llegó vacío o con espacios solos: %r" % args.gist,
            "el gist es la línea que el mapa va a mostrar de esta decisión, así que "
            "tiene que decir algo")
    _validar_gist("--gist", args.gist)
    _no_es_encabezado("--gist", args.gist)
    niebla, graduadas = _niebla_de(args)
    tickets = [_validar_ticket("--new-ticket", t, c, e) for t, c, e in args.new_ticket]
    return {"ctx": ctx, "issue": issue, "cuerpo": cuerpo, "gist": args.gist,
            "niebla": niebla, "graduadas": graduadas,
            "tickets": tickets, "pares": _cableado_de(args, tickets),
            "esperadas": _esperadas_de(args)}


def _fuera_de_alcance_de(args):
    """La función pura de ticket:rule-out. Espeja a _resolucion_de en todo lo que las dos
    operaciones comparten, y difiere en una sola fila: en vez de un gist recibe la viñeta
    entera de Fuera de alcance, con su título en negrita, validada por _validar_vineta
    reusada verbatim. Acá no existe --gist, y esa ausencia es la asimetría: la línea de
    esta operación va a Fuera de alcance y nunca a Decisiones."""
    ctx = _ctx_de(args)
    issue = _issue_de(args)
    cuerpo = _cuerpo_de_secciones(args)
    _validar_vineta("--out-of-scope", args.out_of_scope)
    niebla, graduadas = _niebla_de(args)
    tickets = [_validar_ticket("--new-ticket", t, c, e) for t, c, e in args.new_ticket]
    return {"ctx": ctx, "issue": issue, "cuerpo": cuerpo,
            "vineta": args.out_of_scope,
            "niebla": niebla, "graduadas": graduadas,
            "tickets": tickets, "pares": _cableado_de(args, tickets),
            "esperadas": _esperadas_de(args)}


def _ediciones_de(args):
    """Las ediciones agrupadas por ancla, ya validadas: acá se rompe todo lo que se pueda
    romper sin haber tocado la red, que es lo que hace que una invocación mal formada no
    gaste un round trip. Devuelve {ancla: (removes, appends)}, con el orden de la línea
    de comandos preservado adentro de cada lista."""
    ediciones = {}

    def anotar(ancla, indice, dato):
        ediciones.setdefault(ancla, ([], []))[indice].append(dato)

    for enlace, gist in args.append_decision:
        _sin_saltos("--append-decision", enlace)
        _sin_saltos("--append-decision", gist)
        if not enlace or any(c.isspace() for c in enlace):
            die(SIN_KEY,
                "el enlace de --append-decision está vacío o tiene espacios: %r"
                % enlace,
                "pasá la URL del ticket como un solo token, sin espacios")
        _validar_gist("--append-decision", gist)
        _no_es_encabezado("--append-decision", enlace)
        _no_es_encabezado("--append-decision", gist)
        anotar(ANCLA_DECISIONES, 1, _linea_de_decision(enlace, gist))

    for valor in args.append_fog:
        _validar_vineta("--append-fog", valor)
        anotar(ANCLA_NIEBLA, 1, _linea_de_vineta(valor))

    for titulo in args.remove_fog:
        _sin_saltos("--remove-fog", titulo)
        if not titulo.strip():
            die(SIN_KEY, "--remove-fog recibió un título vacío",
                "pasá el título de la viñeta, sin los asteriscos")
        anotar(ANCLA_NIEBLA, 0, titulo)

    for valor in args.append_out_of_scope:
        # La misma guarda que la niebla, y es lo que vuelve determinista la clave de
        # unicidad de esta sección: sin título en negrita la clave era la línea entera,
        # así que la idempotencia funcionaba o no según cómo la persona hubiera escrito
        # el texto. Era el único de los tres flags con esa dependencia silenciosa.
        _validar_vineta("--append-out-of-scope", valor)
        anotar(ANCLA_FUERA, 1, _linea_de_vineta(valor))

    if not ediciones:
        die(SIN_KEY,
            "map:write no recibió ninguna edición, y escribir cero ediciones es un "
            "error de invocación y no un no-op silencioso",
            "pasá al menos uno de --append-decision, --append-fog, --remove-fog o "
            "--append-out-of-scope")
    return ediciones


def _esperadas_de(args):
    """Las huellas que el llamador declaró, o None cuando --expect-sections no vino. El
    único die de esta rama vive adentro de la comparación contra None, que es lo que
    hace que la ausencia del flag no pueda producir una salida no cero."""
    if args.expect_sections is None:
        return None
    try:
        return json.loads(args.expect_sections)
    except ValueError:
        die(SIN_KEY,
            "--expect-sections no parsea como JSON: %r" % args.expect_sections,
            "pasá el JSON que map:read emitió en su clave sections, sin editarlo")


def _sin_la_vineta(cuerpo, titulo):
    """El cuerpo sin la viñeta de ese título, y cuántas se borraron. Se lleva la viñeta
    entera y no solo su primera línea: una viñeta de niebla real ocupa varias líneas
    físicas."""
    salida = []
    borradas = 0
    indice = 0
    while indice < len(cuerpo):
        if titulo_en_negrita(cuerpo[indice]) != titulo:
            salida.append(cuerpo[indice])
            indice += 1
            continue
        borradas += 1
        indice += 1
        while indice < len(cuerpo) and _es_continuacion(cuerpo[indice]):
            indice += 1
    return salida, borradas


def _con_la_linea(cuerpo, linea, reintento):
    """El cuerpo con la línea agregada después de su última línea no vacía, así que la
    línea en blanco que separa la sección del encabezado siguiente se conserva. Una línea
    que ya está es abort duro, porque agregarla de nuevo la contaría dos veces; en la
    rama del reintento se invierte a no-op con reporte, y esa es la única excepción."""
    clave = _clave_de_unicidad(linea)
    if any(_clave_de_unicidad(vieja) == clave for vieja in cuerpo):
        if not reintento:
            die(SIN_KEY,
                "esta línea ya está en el mapa y agregarla nuevo la contaría dos "
                "veces: %s" % linea,
                "sacá esa edición de la invocación, o leé el mapa antes de escribir")
        print("aviso: la línea ya estaba aplicada, así que este intento no la "
              "repite: %s" % linea, file=sys.stderr)
        return cuerpo
    ultima = 0
    for indice, texto in enumerate(cuerpo):
        if texto.strip():
            ultima = indice + 1
    return cuerpo[:ultima] + [linea] + cuerpo[ultima:]


def aplicar_ediciones(lineas, ediciones, reintento=False):
    """Aplica las ediciones sección por sección sobre el array original y devuelve
    (nuevas, noop). Todo lo que queda fuera de los rangos editados sobrevive byte a byte
    y en su posición, la zona inerte de abajo de la frontera incluida. reintento invierte
    la idempotencia de append: en la rama del reintento, 'esta línea ya está' pasa de
    abort duro a no-op con reporte. Lo pone el script y nunca un argumento, así que la
    excepción no se puede invocar desde afuera."""
    rangos, duplicadas = rangos_de_anclas(lineas)
    if duplicadas:
        die(SIN_KEY,
            "estas anclas aparecen más de una vez en el overview y una escritura no "
            "puede elegir cuál: %s" % ", ".join(duplicadas),
            "dejá una sola aparición de cada encabezado y volvé a correr")
    for ancla in ANCLAS:
        if ancla not in ediciones or ancla in rangos:
            continue
        removes, appends = ediciones[ancla]
        die(SIN_KEY,
            "el overview no tiene el encabezado %s, así que no hay dónde escribir "
            "esto: %s" % (ancla, "; ".join(removes + appends)),
            "agregá ese encabezado al overview, o trazá el mapa con map:create; "
            "map:write nunca escribe al final del documento como reemplazo")
    noop = []
    nuevas = list(lineas)
    # Descendente por índice de inicio: un splice corre los índices de todo lo que está
    # más abajo, así que las secciones que faltan tienen que estar más arriba.
    for ancla in sorted(ediciones, key=lambda a: rangos[a][0], reverse=True):
        inicio, corte = rangos[ancla]
        removes, appends = ediciones[ancla]
        cuerpo = list(lineas[inicio:corte])
        # Los remove antes que los append: es lo que le da sentido a graduar una niebla
        # y abrir otra con el mismo título en una sola invocación.
        for titulo in removes:
            cuerpo, borradas = _sin_la_vineta(cuerpo, titulo)
            if borradas > 1:
                die(SIN_KEY,
                    "el título %s matchea %s viñetas y una escritura no puede elegir "
                    "cuál borrar" % (titulo, borradas),
                    "dejá una sola viñeta con ese título y volvé a correr")
            if borradas == 0:
                noop.append(titulo)
                print("aviso: no hay ninguna viñeta titulada %s, así que no se borró "
                      "nada" % titulo, file=sys.stderr)
        for linea in appends:
            cuerpo = _con_la_linea(cuerpo, linea, reintento)
        nuevas[inicio:corte] = cuerpo
    return nuevas, noop


def _errores_de(payload):
    """Los mensajes de error de una respuesta, o la lista vacía. NO muere: la ruta de
    escritura necesita decidir si reintenta, y resolver_datos no le sirve porque muere.
    Duplica a propósito el extractor de resolver_datos, que este change tiene prohibido
    tocar para que resolver_ctx lo siga tratando igual."""
    textos = []
    for error in (payload.get("errors") or []):
        mensaje = error.get("message") if isinstance(error, dict) else None
        textos.append(str(mensaje) if mensaje is not None else str(error))
    return textos


def _resolver_escritura(payload):
    """La única puerta de projectUpdate. Un projectUpdate rechazado puede venir con
    success: false y SIN errors de nivel superior, así que mirar solo errors reportaría
    éxito sobre una escritura que Linear rechazó. Devuelve (ok, detalle)."""
    errores = _errores_de(payload)
    if errores:
        return (False, "; ".join(errores))
    datos = (payload.get("data") or {}).get("projectUpdate") or {}
    # is not True y no un not pelado: la clave ausente y el false explícito son los dos
    # casos que importan, y los dos caen del lado del fracaso.
    if datos.get("success") is not True:
        return (False, "projectUpdate devolvió success=%s" % datos.get("success"))
    return (True, "")


def _reportar_deriva(texto, esperadas):
    """El único uso de --expect-sections: nombra por stderr las anclas cuya huella se
    movió desde la lectura del llamador. Nunca aborta y nunca cambia el código de salida,
    porque la escritura ya se re-deriva del texto recién leído: la deriva es información
    para la persona y no un motivo para no escribir. Reusa huellas y cortar_secciones sin
    tocarlas, así que las dos puntas comparan lo mismo."""
    ahora = huellas(cortar_secciones(texto))
    for ancla in ANCLAS:
        if ancla in esperadas and esperadas[ancla] != ahora[ancla]:
            print("aviso: la sección %s se movió desde tu lectura" % ancla,
                  file=sys.stderr)


def _intentar_escribir(project, ediciones, esperadas, reintento, key):
    """Un intento entero del read-modify-write: relee tarde, re-deriva y escribe. Las dos
    sentencias de red viven en esta función y en ninguna otra del grafo de map:write, y
    el bucle vive en el handler: con el bucle acá, el salto del reintento se metería entre
    las dos. Devuelve (ok, detalle) y NUNCA termina el proceso por una falla de
    transporte, para que el llamador pueda reintentar."""
    lectura = _post(MAP_READ_QUERY, {"project": project}, key)
    errores = _errores_de(lectura)
    if errores:
        return (False, "; ".join(errores))
    proyecto = (lectura.get("data") or {}).get("project")
    if proyecto is None:
        die(SIN_KEY,
            "el Project %s no resolvió, así que no hay overview que reescribir"
            % project,
            "revisá el identificador que le pasaste a --project")
    texto = proyecto.get("content") or ""
    if esperadas is not None:
        _reportar_deriva(texto, esperadas)
    nuevas, noop = aplicar_ediciones(normalizar(texto), ediciones, reintento)
    escritura = _post(PROJECT_UPDATE,
                      {"project": project, "content": "\n".join(nuevas)}, key)
    ok, detalle = _resolver_escritura(escritura)
    return (ok, detalle if not ok else noop)


def esqueleto(destino, previo):
    """El mapa recién nacido: los seis encabezados en el orden de contrato de ANCLAS,
    Destino con el texto que la persona dictó, y el array de líneas del overview que ya
    estaba preservado VERBATIM al final, bajo la frontera. Nunca lo reescribe ni lo
    reordena. La frontera va ÚLTIMA y eso es un requisito del parser y no una preferencia
    de lectura: la primitiva corta el recorrido ahí, así que ponerla antes dejaría a los
    seis encabezados en la zona inerte."""
    lineas = ["## " + ANCLAS[0], "", destino, ""]
    for ancla in ANCLAS[1:]:
        lineas.extend(["## " + ancla, ""])
    if any(linea.strip() for linea in previo):
        lineas.extend(["## " + ANTES_DEL_MAPA, ""])
        lineas.extend(previo)
    return lineas


def _destino_de(args):
    """El destino ya validado: acá se rompe todo lo que se pueda romper sin haber tocado
    la red. Es LA exposición de la guarda del encabezado, porque el esqueleto lo escribe
    crudo bajo su ancla y sin marcador de viñeta: al revés de los appends de map:write,
    acá el valor ES la línea, y un encabezado metido por este argumento corta el mapa
    entero para toda lectura futura."""
    _sin_saltos("--destino", args.destino)
    if not args.destino.strip():
        die(SIN_KEY, "--destino recibió un texto vacío",
            "pasá la frase que nombra a dónde va este mapa")
    _no_es_encabezado("--destino", args.destino)
    return args.destino


def _resolver_creacion(payload):
    """La puerta de projectCreate. La misma regla que _resolver_escritura —errors
    primero, después 'is not True'— sobre la otra clave del payload, y además saca el id
    y la url del mismo round trip. Es una función aparte y no un parámetro de
    _resolver_escritura para no reabrir su cuerpo ni su clave. Devuelve
    (ok, detalle, proyecto)."""
    errores = _errores_de(payload)
    if errores:
        return (False, "; ".join(errores), {})
    datos = (payload.get("data") or {}).get("projectCreate") or {}
    if datos.get("success") is not True:
        return (False, "projectCreate devolvió success=%s" % datos.get("success"), {})
    return (True, "", datos.get("project") or {})


def tiene_las_seis(rangos):
    """True si el overview lleva las seis anclas, que es la forma que esqueleto produce.
    Un solo sitio de definición porque tiene dos consumidores que TIENEN que coincidir:
    la guarda de adopción, que decide si este Project ya tiene un mapa, y
    _ya_es_este_mapa, que decide si ese mapa es el que este intento iba a escribir. Las
    dos nociones vivieron separadas y no coincidían —una contaba cualquier ancla suelta
    como un mapa y la otra exigía las seis, a tres líneas de distancia—, así que ahora
    viven juntas y no pueden volver a divergir."""
    return sorted(rangos) == sorted(ANCLAS)


def _ya_es_este_mapa(rangos, lineas, destino):
    """True si el overview que acabamos de releer es exactamente el mapa que este intento
    iba a escribir: las seis anclas presentes y el cuerpo de Destino, sin líneas vacías,
    igual al destino recibido. Es la guarda que acota la inversión de idempotencia del
    reintento de la adopción a 'mi escritura anterior aterrizó' y no a 'hay un mapa':
    entre los dos intentos alguien pudo escribir OTRO mapa, y ese no es el nuestro."""
    if not tiene_las_seis(rangos):
        return False
    inicio, corte = rangos[ANCLAS[0]]
    return [l for l in lineas[inicio:corte] if l.strip()] == [destino]


def _intentar_adoptar(project, destino, reintento, key):
    """Un intento entero de la adopción: relee tarde, decide y escribe. Devuelve
    (ok, detalle) y NUNCA termina el proceso por una falla de transporte, para que el
    llamador pueda reintentar. Sí termina, y con razón, cuando el Project no resuelve o
    cuando ya tiene un mapa que no es el nuestro: eso no lo arregla reintentar."""
    lectura = _post(MAP_READ_QUERY, {"project": project}, key)
    errores = _errores_de(lectura)
    if errores:
        return (False, "; ".join(errores))
    proyecto = (lectura.get("data") or {}).get("project")
    if proyecto is None:
        die(SIN_KEY,
            "el Project %s no resolvió, así que no hay overview que adoptar" % project,
            "revisá el identificador que le pasaste a --project")
    lineas = normalizar(proyecto.get("content") or "")
    rangos, _duplicadas = rangos_de_anclas(lineas)
    # "Ya tiene mapa" es la frontera presente —seña inequívoca de que este plugin ya
    # escribió acá— o las seis anclas juntas, que es la forma que esqueleto produce. Un
    # subconjunto suelto NO es un mapa: un encabezado con el nombre de un ancla en la
    # prosa de un Project real es del todo plausible, y negarse a adoptarlo sería pedirle
    # a la persona que renombre su propia prosa. Las dos condiciones juntas cubren el
    # documento entero pese al corte de la primitiva: si la frontera está, la segunda
    # aborta y no hace falta mirar debajo; si no está, no hay corte y la primera ve todo.
    if tiene_las_seis(rangos) or any(es_frontera_del_mapa(l) for l in lineas):
        if reintento and _ya_es_este_mapa(rangos, lineas, destino):
            return (True, "")
        die(SIN_KEY,
            "el Project %s ya tiene un mapa: encontré %s"
            % (project, ", ".join(sorted(rangos)) or ANTES_DEL_MAPA),
            "si querés trazar otro mapa, usá otro Project; si querés editar este, "
            "es map:write y no map:create")
    escritura = _post(PROJECT_UPDATE,
                      {"project": project,
                       "content": "\n".join(esqueleto(destino, lineas))}, key)
    return _resolver_escritura(escritura)


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


def _tickets_de(args):
    """El ctx parseado y los tickets ya validados: acá se rompe todo lo que se pueda
    romper sin haber tocado la red, que es lo que hace que una invocación mal formada
    no gaste un round trip. Devuelve (ctx, tickets) con cada ticket como
    (titulo, cuerpo, nombres) y el orden de la línea de comandos preservado.

    La guarda del encabezado NO se aplica acá, y es deliberado: su propósito declarado
    es la línea del mapa, y el cuerpo de una issue no es una línea del mapa."""
    ctx = _ctx_de(args)
    if not args.ticket:
        die(SIN_KEY,
            "ticket:create no recibió ningún --ticket, y crear cero tickets es un "
            "error de invocación y no un no-op silencioso",
            "pasá al menos un --ticket con su título, su cuerpo y sus labels")
    return ctx, [_validar_ticket("--ticket", t, c, e) for t, c, e in args.ticket]


def _resolver_label(payload):
    """La puerta de issueLabelCreate: la misma regla de tres casos que
    _resolver_escritura y _resolver_creacion, sobre su propia clave del payload.
    Devuelve (ok, detalle, etiqueta)."""
    errores = _errores_de(payload)
    if errores:
        return (False, "; ".join(errores), {})
    datos = (payload.get("data") or {}).get("issueLabelCreate") or {}
    if datos.get("success") is not True:
        return (False, "issueLabelCreate devolvió success=%s" % datos.get("success"),
                {})
    return (True, "", datos.get("issueLabel") or {})


def _resolver_tickets(payload):
    """La puerta de issueBatchCreate, con la misma regla de tres casos y sobre la otra
    clave del payload. Es una función aparte y no un parámetro de las otras dos, que es
    la decisión que ya se tomó para _resolver_creacion. Devuelve (ok, detalle,
    issues)."""
    errores = _errores_de(payload)
    if errores:
        return (False, "; ".join(errores), [])
    datos = (payload.get("data") or {}).get("issueBatchCreate") or {}
    if datos.get("success") is not True:
        return (False, "issueBatchCreate devolvió success=%s" % datos.get("success"),
                [])
    return (True, "", datos.get("issues") or [])


def _crear_labels_faltantes(ctx, key):
    """La ÚNICA casa que crea labels en todo el archivo, y por eso el recorrido es de
    LABELS y no de una lista propia. teamId va omitido a propósito: los labels del
    plugin son workspace-level y planos, nunca label groups, porque un grupo no se
    puede aplicar a un issue y partiría el nombre canónico map:research en la UI.

    Discovery no puede caer acá y eso es gratis de verificar: vive fuera de LABELS y
    fuera de ctx["labels"], y esa forma es lo que vuelve chequeable la prohibición de
    crearlo. Devuelve (labels, creados)."""
    labels = dict(ctx.get("labels") or {})
    creados = []
    for nombre in LABELS:
        if labels.get(nombre) is not None:
            continue
        ok, detalle, etiqueta = _resolver_label(
            _post(ISSUE_LABEL_CREATE, {"nombre": nombre}, key))
        if not ok:
            die(SIN_KEY,
                "el label %s no se pudo crear: %s. Labels que SÍ quedaron creados en "
                "esta corrida: %s" % (nombre, detalle, ", ".join(creados) or "ninguno"),
                "corré el preflight de nuevo ANTES de reintentar: el ctx que tenés ya "
                "no describe el workspace")
        labels[nombre] = etiqueta.get("id")
        creados.append(nombre)
    return labels, creados


def _crear_tickets(ctx, project, labels, tickets, key):
    """La escritura del lote de tickets de decisión, en una sola llamada atómica. Recibe
    el dict de labels YA resuelto y NO crea ninguno: la única casa que crea labels sigue
    siendo _crear_labels_faltantes, y quien la llama sigue siendo solo cmd_ticket_create.
    Cortar acá es lo que deja que las operaciones de resolución reusen esta escritura sin
    convertirse en una segunda creadora de labels. Devuelve (ok, detalle, issues)."""
    # Discovery se usa cuando está y se saltea en silencio cuando no. Nunca se crea.
    comunes = [labels[LABEL_MAPA]]
    if ctx.get("discovery") is not None:
        comunes.append(ctx["discovery"])
    entradas = []
    for titulo, cuerpo, nombres in tickets:
        # stateId explícito: sin él la issue nace en Triage. estimate en cero: un
        # ticket de decisión no se estima.
        entradas.append({"teamId": ctx["team"], "projectId": project,
                         "title": titulo, "description": cuerpo,
                         "stateId": ctx["default"], "estimate": 0,
                         "labelIds": comunes + [labels[n] for n in nombres]})
    return _resolver_tickets(_post(ISSUE_BATCH_CREATE, {"issues": entradas}, key))


def _bloqueos_de(args):
    """Los pares ya validados: acá se rompe todo lo que se pueda romper sin haber
    tocado la red. Un par cuyos dos ids son iguales aborta, y eso no es celo: un ticket
    que se bloquea a sí mismo no vuelve a ser tomable nunca, y no hay ninguna operación
    en el plugin para deshacerlo.

    El mismo criterio corre contra los pares que ya pasaron por acá en esta misma
    invocación: un --block exacto repetido, o su recíproco (A bloqueado por B junto
    con B bloqueado por A), también abortan. Esas tres guardas viven en _validar_par,
    compartidas con las dos operaciones que cierran un ticket, y ahí está escrito lo que
    NO cubren."""
    if not args.block:
        die(SIN_KEY,
            "ticket:block no recibió ningún --block, y escribir cero relaciones es un "
            "error de invocación y no un no-op silencioso",
            "pasá al menos un --block con el id del bloqueante y el del bloqueado")
    pares = []
    for bloqueante, bloqueado in args.block:
        _sin_saltos("--block", bloqueante)
        _sin_saltos("--block", bloqueado)
        if not bloqueante.strip() or not bloqueado.strip():
            die(SIN_KEY,
                "--block recibió un id vacío: %r y %r" % (bloqueante, bloqueado),
                "pasá los dos ids, el del bloqueante primero y el del bloqueado "
                "después")
        _validar_par("--block", "id", pares, bloqueante, bloqueado)
        pares.append((bloqueante, bloqueado))
    return pares


def _resolver_relaciones(payload):
    """La puerta de issueRelationCreate, con la misma regla de tres casos que las otras
    tres. Devuelve (ok, detalle)."""
    errores = _errores_de(payload)
    if errores:
        return (False, "; ".join(errores))
    datos = (payload.get("data") or {}).get("issueRelationCreate") or {}
    if datos.get("success") is not True:
        return (False,
                "issueRelationCreate devolvió success=%s" % datos.get("success"))
    return (True, "")


def _bloquear_pares(pares, key):
    """El cableado de una pasada de bloqueos, compartido por ticket:block y por las dos
    operaciones de resolución. El bloqueante siempre del lado issue, y esta orientación
    es el espejo exacto de la lectura de la frontera, que saca el bloqueante de
    inverseRelations.issue. Si esta punta escribiera invertido, un ticket bloqueado
    aparecería como tomable.

    No reintenta, por la misma razón que ticket:create: _post traga la falla de
    transporte y una relación repetida no se puede deshacer desde acá. Corta en el
    primer par que no confirma y NO termina el proceso: devuelve (ok, detalle, escritos)
    con los pares que sí entraron, porque cada llamador tiene su propia remediación y la
    de una resolución a medias no es la de un ticket:block suelto.

    La constante que postea es ISSUE_RELATION_CREATE, referenciada por nombre. Ningún
    llamador reescribe su enum: type: blocks va sin comillas adentro del cuerpo de la
    mutation, y una segunda copia de ese literal es exactamente por donde el defecto que
    dejó a ticket:block inservible al nacer volvería a entrar."""
    escritos = []
    for bloqueante, bloqueado in pares:
        ok, detalle = _resolver_relaciones(
            _post(ISSUE_RELATION_CREATE,
                  {"bloqueante": bloqueante, "bloqueado": bloqueado}, key))
        if not ok:
            return (False,
                    "el bloqueo de %s por %s no confirmó: %s"
                    % (bloqueado, bloqueante, detalle), escritos)
        escritos.append((bloqueante, bloqueado))
    return (True, "", escritos)


def _comentar(issue, cuerpo, key):
    """La ÚNICA puerta de commentCreate: escribe y resuelve, con la misma regla de tres
    casos que las otras cuatro. Un commentCreate con success en false y sin errors de
    nivel superior es un fracaso y no un éxito silencioso. Devuelve (ok, detalle, url),
    con la url del comentario recién escrito, que la mutation devuelve en el mismo round
    trip."""
    payload = _post(COMMENT_CREATE, {"issue": issue, "body": cuerpo}, key)
    errores = _errores_de(payload)
    if errores:
        return (False, "; ".join(errores), "")
    datos = (payload.get("data") or {}).get("commentCreate") or {}
    if datos.get("success") is not True:
        return (False, "commentCreate devolvió success=%s" % datos.get("success"), "")
    return (True, "", (datos.get("comment") or {}).get("url") or "")


def _cambiar_estado(issue, input_, key):
    """La ÚNICA puerta de issueUpdate: escribe y resuelve, con la misma regla de tres
    casos que las otras cuatro puertas. El input llega armado desde el handler y no se
    arma acá, y esa es la decisión: cada handler escribe su propio dict literal, que es
    lo que deja ver desde afuera qué clave de la issue toca. Devuelve (ok, detalle,
    issue), con issue el payload que la mutation devolvió en el mismo round trip."""
    payload = _post(ISSUE_UPDATE, {"issue": issue, "input": input_}, key)
    errores = _errores_de(payload)
    if errores:
        return (False, "; ".join(errores), {})
    datos = (payload.get("data") or {}).get("issueUpdate") or {}
    if datos.get("success") is not True:
        return (False, "issueUpdate devolvió success=%s" % datos.get("success"), {})
    return (True, "", datos.get("issue") or {})


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


def cmd_map_create(args):
    destino = _destino_de(args)      # valida la línea única antes de tocar la red
    key = leer_key()
    # La asimetría, y es deliberada: adoptar relee en cada intento, así que repetirlo es
    # seguro porque la guarda de arriba re-evalúa sobre la relectura. Crear es un POST
    # único cuyo fracaso de transporte no distingue "no llegó" de "llegó y se perdió la
    # respuesta", así que reintentarlo puede dejar dos Projects hermanos con el mismo
    # nombre, y el plugin no tiene ninguna operación para deshacerlo.
    if args.project:
        detalle = ""
        for intento in range(MAX_INTENTOS):
            ok, detalle = _intentar_adoptar(args.project, destino, intento > 0, key)
            if ok:
                print(json.dumps({"created": False, "project": args.project,
                                  "url": None}, separators=(",", ":")))
                return
            print("aviso: el intento %s falló: %s" % (intento + 1, detalle),
                  file=sys.stderr)
        die(SIN_KEY,
            "no se pudo adoptar el Project %s; el último intento dijo: %s"
            % (args.project, detalle),
            "volvé a correr el mismo comando: adoptar es seguro de repetir, porque una "
            "segunda corrida sobre un Project que ya tiene mapa aborta sin escribir")
    else:
        # json.loads y no resolver_ctx: esa función transforma la respuesta del
        # preflight en el ctx y lleva adentro tres de las cuatro fallas duras, así que
        # llamarla acá le daría a map:create códigos de salida que D6 le prohíbe. El ctx
        # ya viene resuelto en el blob, igual que lo consume frontier:query.
        equipo = json.loads(args.ctx)["team"]
        creacion = _post(PROJECT_CREATE,
                         {"team": equipo, "name": args.name,
                          "content": "\n".join(esqueleto(destino, []))}, key)
        ok, detalle, proyecto = _resolver_creacion(creacion)
        if not ok:
            die(SIN_KEY,
                "el projectCreate de %s no confirmó y NO SE SABE si el Project quedó "
                "hecho: %s" % (args.name, detalle),
                "abrí Linear y buscá un Project llamado %s ANTES de volver a correr: "
                "si aparece, seguí con map:create --project sobre él; si no aparece, "
                "volvé a correr este mismo comando. Esta rama no reintenta sola "
                "justamente para no dejarte dos Projects con el mismo nombre"
                % args.name)
        print(json.dumps({"created": True, "project": proyecto.get("id"),
                          "url": proyecto.get("url")}, separators=(",", ":")))


def cmd_map_write(args):
    ediciones = _ediciones_de(args)      # valida todo antes de tocar la red
    esperadas = _esperadas_de(args)      # None cuando --expect-sections no vino
    key = leer_key()
    detalle = ""
    for intento in range(MAX_INTENTOS):
        ok, detalle = _intentar_escribir(args.project, ediciones, esperadas,
                                         intento > 0, key)
        if ok:
            print(json.dumps({"written": True, "attempts": intento + 1,
                              "noop": detalle}, separators=(",", ":")))
            return
        print("aviso: el intento %s falló: %s" % (intento + 1, detalle),
              file=sys.stderr)
    die(SIN_KEY,
        "no se pudo escribir el mapa; el último intento dijo: %s" % detalle,
        "mirá el mensaje de arriba y volvé a correr el comando")


def cmd_ticket_create(args):
    ctx, tickets = _tickets_de(args)     # valida todo antes de tocar la red
    key = leer_key()
    # Los labels que faltan se crean UNA vez por corrida, y por eso la invocación crea
    # todos los tickets de la pasada: el preflight corre una vez por conductor y el ctx
    # es inmutable, así que una segunda invocación leería los mismos null y volvería a
    # crearlos. No reintenta: _post traga la falla de transporte, así que ninguna rama
    # puede distinguir "no llegó" de "llegó y se perdió la respuesta", y un
    # issueBatchCreate repetido deja N tickets hermanos que nada sabe deshacer.
    labels, creados = _crear_labels_faltantes(ctx, key)
    ok, detalle, issues = _crear_tickets(ctx, args.project, labels, tickets, key)
    if not ok:
        die(SIN_KEY,
            "el issueBatchCreate no confirmó: %s. Labels que SÍ quedaron creados en "
            "esta corrida: %s" % (detalle, ", ".join(creados) or "ninguno"),
            "corré el preflight de nuevo ANTES de reintentar: el ctx que tenés ya no "
            "describe el workspace, porque esos labels ahora existen")
    print(json.dumps(
        {"tickets": [{"identifier": i.get("identifier"), "id": i.get("id"),
                      "title": i.get("title"), "url": i.get("url")} for i in issues],
         "createdLabels": creados}, separators=(",", ":")))


def cmd_ticket_block(args):
    pares = _bloqueos_de(args)      # valida todo antes de tocar la red
    key = leer_key()
    ok, detalle, escritos = _bloquear_pares(pares, key)
    if not ok:
        die(SIN_KEY,
            "%s. Bloqueos que SÍ quedaron escritos en esta corrida: %s"
            % (detalle,
               ", ".join("%s bloquea a %s" % par for par in escritos) or "ninguno"),
            "volvé a correr solo los pares que faltan: esta rama no reintenta "
            "sola, y repetir un par que ya entró duplicaría la relación")
    print(json.dumps(
        {"blocks": [{"blocker": b, "blocked": d} for b, d in escritos]},
        separators=(",", ":")))


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


def cmd_ticket_claim(args):
    # Primero todo lo que se puede romper sin un round trip, después la key, después la
    # red: el mismo orden que ya usan ticket:create, ticket:block y map:write.
    try:
        ctx = json.loads(args.ctx)
    except ValueError:
        die(SIN_KEY, "--ctx no parsea como JSON: %r" % args.ctx,
            "pasá el blob que emitió el preflight, sin editarlo")
    _sin_saltos("--issue", args.issue)
    if not args.issue.strip():
        die(SIN_KEY, "--issue llegó vacío o con espacios solos: %r" % args.issue,
            "pasá el identificador del ticket, CRM-123, tal como lo devolvió "
            "frontier:query")
    if ctx.get("viewer") is None:
        die(SIN_KEY,
            "el preflight no resolvió el viewer, así que la toma no tiene a quién "
            "asignarse",
            "corré el preflight de nuevo: el ctx que tenés no dice quién sos")
    key = leer_key()
    # El asignado sale del ctx y de ningún otro lado, y por eso no hay un --assignee:
    # un flag dejaría tomar en nombre de otra persona, que es justo lo que la toma
    # existe para impedir. --release es la misma escritura con el valor inverso, y no
    # una operación decimotercera: las doce ya están fijas.
    if args.release:
        ok, detalle, issue = _cambiar_estado(args.issue, {"assigneeId": None}, key)
    else:
        ok, detalle, issue = _cambiar_estado(args.issue,
                                             {"assigneeId": ctx["viewer"]}, key)
    if not ok:
        die(SIN_KEY,
            "la %s de %s no confirmó: %s"
            % ("devolución" if args.release else "toma", args.issue, detalle),
            "volvé a correr la misma invocación: esta operación escribe un solo campo "
            "y repetirla no duplica nada")
    asignado = issue.get("assignee") or {}
    print(json.dumps({"issue": issue.get("identifier") or args.issue,
                      "assignee": None if args.release else ctx["viewer"],
                      "assigneeName": asignado.get("displayName")},
                     separators=(",", ":")))


def _citar(token):
    """Un token de una invocación que un mensaje de remediación imprime, listo para
    copiar y pegar en una shell. Solo entrecomilla lo que lo necesita, para que la línea
    siga siendo legible."""
    if token and not any(c in token for c in " \"'\\$`"):
        return token
    return "'" + token.replace("'", "'\\''") + "'"


def cmd_ticket_resolve(args):
    plan = _resolucion_de(args)      # valida todo antes de tocar la red
    ctx = plan["ctx"]
    labels = ctx.get("labels") or {}
    # ticket:resolve NO crea labels, y ese corte es lo que mantiene verde la afirmación
    # 38: _crear_labels_faltantes sigue teniendo un solo llamador, cmd_ticket_create. El
    # estado que esta guarda rechaza no ocurre en el camino normal, porque implica un
    # workspace que nunca corrió ticket:create, o sea un mapa con cero tickets, y ese
    # mapa tiene la frontera vacía: /map-work para en el veredicto y nunca llega acá.
    faltan = sorted(set(n for n in [LABEL_MAPA] +
                        [n for _, _, nombres in plan["tickets"] for n in nombres]
                        if labels.get(n) is None)) if plan["tickets"] else []
    if faltan:
        die(SIN_KEY,
            "estos labels que los --new-ticket necesitan vinieron en null en el ctx: "
            "%s" % ", ".join(faltan),
            "corré /map-new en este workspace: es quien crea los labels del plugin "
            "cuando faltan, y esta operación nunca los crea por su cuenta")
    key = leer_key()
    issues, escritos = [], []
    if plan["tickets"]:
        ok, detalle, issues = _crear_tickets(ctx, args.project, labels,
                                             plan["tickets"], key)
        if not ok:
            die(SIN_KEY,
                "el issueBatchCreate no confirmó: %s. No quedó escrito nada de esta "
                "resolución: ni los tickets nuevos, ni el cableado, ni el comentario, "
                "ni el estado, ni el mapa" % detalle,
                "volvé a correr la misma invocación entera: como no aterrizó nada, "
                "repetirla no duplica nada")
    if plan["pares"]:
        # Los títulos se resuelven a ids recién acá, con lo que devolvió la escritura 1.
        por_titulo = dict((i.get("title"), i.get("id")) for i in issues)
        ok, detalle, escritos = _bloquear_pares(
            [(por_titulo.get(a), por_titulo.get(b)) for a, b in plan["pares"]], key)
        if not ok:
            die(SIN_KEY,
                "%s. Los tickets nuevos ya quedaron escritos, y de los bloqueos "
                "entraron %s" % (detalle, len(escritos)),
                "corré ticket:block solo con los pares que faltan, y después esta "
                "misma invocación sin --new-ticket ni --block: el comentario, el "
                "estado y el mapa todavía no se escribieron")
    ok, detalle, comentario = _comentar(plan["issue"], plan["cuerpo"], key)
    if not ok:
        die(SIN_KEY,
            "el comentario de resolución no se pudo escribir: %s. Los tickets nuevos y "
            "su cableado ya quedaron escritos" % detalle,
            "volvé a correr esta misma invocación sin --new-ticket ni --block: el "
            "estado y el mapa todavía no se escribieron")
    ok, detalle, issue = _cambiar_estado(plan["issue"], {"stateId": ctx["done"]}, key)
    if not ok:
        # _post traga la falla de transporte, así que un timeout acá no distingue "el
        # issueUpdate no llegó" de "llegó y se perdió la respuesta": el estado puede
        # haber cambiado igual. Nombrar los --remove-fog/--append-fog pendientes es lo
        # único posible en este punto, porque la url que --append-decision necesita
        # todavía no existe: la devuelve el mismo issueUpdate que acaba de fallar.
        pendiente = []
        for titulo in plan["graduadas"]:
            pendiente += ["--remove-fog", titulo]
        for vineta in plan["niebla"]:
            pendiente += ["--append-fog", vineta[2:]]
        niebla = (" Sumale estos flags de niebla al map:write de más abajo, que si no "
                  "se pierden para siempre: %s."
                  % " ".join(_citar(t) for t in pendiente)) if pendiente else ""
        die(SIN_KEY,
            "el estado no se pudo confirmar: %s. Puede que el ticket ya esté en Done y "
            "puede que no: un timeout no distingue las dos. El comentario de "
            "resolución YA está escrito en el ticket, así que repetir esta invocación "
            "lo duplicaría.%s" % (detalle, niebla),
            "fijate en Linear si el ticket ya quedó en Done antes de tocarlo; si no, "
            "cerralo a mano. Después corré map:write --project %s --append-decision "
            "con la url del ticket y el gist, para dejar la línea en el mapa"
            % _citar(args.project))
    url = issue.get("url") or ""
    # La línea y los flags se arman antes de la bifurcación, así que lo que se imprime
    # y lo que se escribe es el mismo valor: una construcción y dos destinos, y no dos
    # construcciones que puedan divergir. Ni --project ni --expect-sections viajan en
    # mapArgs: el primero es uno solo para toda la invocación del llamador, y el
    # segundo es la huella de una lectura del mapa que esta operación nunca hizo.
    linea = _linea_de_decision(url, plan["gist"])
    flags = ["--append-decision", url, plan["gist"]]
    for titulo in plan["graduadas"]:
        flags += ["--remove-fog", titulo]
    for vineta in plan["niebla"]:
        flags += ["--append-fog", vineta[2:]]
    salida = {"issue": issue.get("identifier") or plan["issue"], "url": url,
              "comment": comentario,
              "tickets": [{"identifier": i.get("identifier"), "id": i.get("id"),
                           "title": i.get("title"), "url": i.get("url")}
                          for i in issues],
              "blocks": [{"blocker": b, "blocked": d} for b, d in escritos],
              "mapWritten": not args.defer_map, "mapLine": linea, "mapArgs": flags,
              "noop": []}
    if args.defer_map:
        # Las cuatro escrituras del ticket ya aterrizaron; la quinta, que es la única
        # sobre el recurso compartido, la hace quien despachó esta invocación con los
        # mapArgs de acá. El noop viene vacío porque ningún intento de escritura corrió
        # y por lo tanto ninguno pudo detectar una línea ya aplicada.
        print(json.dumps(salida, separators=(",", ":")))
        return
    ediciones = {ANCLA_DECISIONES: ([], [linea])}
    if plan["graduadas"] or plan["niebla"]:
        ediciones[ANCLA_NIEBLA] = (plan["graduadas"], plan["niebla"])
    # Un solo intento y sin bucle propio: MAX_INTENTOS gobierna el reintento de
    # map:write y de map:create, y una tercera referencia lo desparramaría. Acá no hace
    # falta, porque una falla en la quinta no pierde nada y se recupera con el comando
    # exacto que el mensaje de abajo imprime.
    ok, detalle = _intentar_escribir(args.project, ediciones, plan["esperadas"],
                                     False, key)
    if not ok:
        faltante = ["map:write", "--project", args.project,
                    "--append-decision", url, plan["gist"]]
        for titulo in plan["graduadas"]:
            faltante += ["--remove-fog", titulo]
        for vineta in plan["niebla"]:
            faltante += ["--append-fog", vineta[2:]]
        die(SIN_KEY,
            "la línea del mapa no se pudo escribir: %s. Todo lo demás ya aterrizó: los "
            "tickets nuevos, su cableado, el comentario y el ticket en Done" % detalle,
            "corré exactamente esto para terminar a mano, y nada más: linear.py %s"
            % " ".join(_citar(t) for t in faltante))
    salida["noop"] = detalle
    print(json.dumps(salida, separators=(",", ":")))


def cmd_ticket_rule_out(args):
    # Una función aparte de cmd_ticket_resolve, y no una parametrizada por estado y por
    # ancla. Las dos no comparten destino ni valor, y comparten menos que eso: no
    # comparten FORMA. Una decisión es un enlace más gist con tope; una entrada de Fuera
    # de alcance es una viñeta con título en negrita que es además su clave única. Un
    # helper parametrizado tendría que ramificar por forma adentro, y ahí ya no es un
    # helper; además dejaría los dos literales asimétricos en el sitio de llamada, donde
    # el AST de este repo deliberadamente no los sigue.
    plan = _fuera_de_alcance_de(args)   # valida todo antes de tocar la red
    ctx = plan["ctx"]
    labels = ctx.get("labels") or {}
    faltan = sorted(set(n for n in [LABEL_MAPA] +
                        [n for _, _, nombres in plan["tickets"] for n in nombres]
                        if labels.get(n) is None)) if plan["tickets"] else []
    if faltan:
        die(SIN_KEY,
            "estos labels que los --new-ticket necesitan vinieron en null en el ctx: "
            "%s" % ", ".join(faltan),
            "corré /map-new en este workspace: es quien crea los labels del plugin "
            "cuando faltan, y esta operación nunca los crea por su cuenta")
    key = leer_key()
    issues, escritos = [], []
    if plan["tickets"]:
        ok, detalle, issues = _crear_tickets(ctx, args.project, labels,
                                             plan["tickets"], key)
        if not ok:
            die(SIN_KEY,
                "el issueBatchCreate no confirmó: %s. No quedó escrito nada de este "
                "fuera de alcance: ni los tickets nuevos, ni el cableado, ni el "
                "comentario, ni el estado, ni el mapa" % detalle,
                "volvé a correr la misma invocación entera: como no aterrizó nada, "
                "repetirla no duplica nada")
    if plan["pares"]:
        por_titulo = dict((i.get("title"), i.get("id")) for i in issues)
        ok, detalle, escritos = _bloquear_pares(
            [(por_titulo.get(a), por_titulo.get(b)) for a, b in plan["pares"]], key)
        if not ok:
            die(SIN_KEY,
                "%s. Los tickets nuevos ya quedaron escritos, y de los bloqueos "
                "entraron %s" % (detalle, len(escritos)),
                "corré ticket:block solo con los pares que faltan, y después esta "
                "misma invocación sin --new-ticket ni --block: el comentario, el "
                "estado y el mapa todavía no se escribieron")
    ok, detalle, comentario = _comentar(plan["issue"], plan["cuerpo"], key)
    if not ok:
        die(SIN_KEY,
            "el comentario no se pudo escribir: %s. Los tickets nuevos y su cableado ya "
            "quedaron escritos" % detalle,
            "volvé a correr esta misma invocación sin --new-ticket ni --block: el "
            "estado y el mapa todavía no se escribieron")
    ok, detalle, issue = _cambiar_estado(plan["issue"],
                                         {"stateId": ctx["canceled"]}, key)
    if not ok:
        # A diferencia de la resolución, acá la remediación SÍ puede imprimir la
        # invocación exacta: --append-out-of-scope lleva la viñeta que ya está en plan,
        # y no una url que solo devolvería el issueUpdate que acaba de fallar.
        faltante = ["map:write", "--project", args.project,
                    "--append-out-of-scope", plan["vineta"]]
        for titulo in plan["graduadas"]:
            faltante += ["--remove-fog", titulo]
        for vineta in plan["niebla"]:
            faltante += ["--append-fog", vineta[2:]]
        die(SIN_KEY,
            "el estado no se pudo confirmar: %s. Puede que el ticket ya esté cancelado "
            "y puede que no: un timeout no distingue las dos. El comentario YA está "
            "escrito en el ticket, así que repetir esta invocación lo duplicaría"
            % detalle,
            "fijate en Linear si el ticket ya quedó cancelado antes de tocarlo; si no, "
            "cancelalo a mano. Después corré exactamente esto para dejar la línea en "
            "el mapa: linear.py %s" % " ".join(_citar(t) for t in faltante))
    # Misma forma que en cmd_ticket_resolve y con sus literales propios, escrita dos
    # veces a propósito: un helper compartido se llevaría ANCLA_FUERA al sitio de
    # llamada y la afirmación 62 dejaría de ver la asimetría de los dos handlers.
    linea = _linea_de_vineta(plan["vineta"])
    flags = ["--append-out-of-scope", plan["vineta"]]
    for titulo in plan["graduadas"]:
        flags += ["--remove-fog", titulo]
    for vineta in plan["niebla"]:
        flags += ["--append-fog", vineta[2:]]
    salida = {"issue": issue.get("identifier") or plan["issue"],
              "url": issue.get("url") or "", "comment": comentario,
              "tickets": [{"identifier": i.get("identifier"), "id": i.get("id"),
                           "title": i.get("title"), "url": i.get("url")}
                          for i in issues],
              "blocks": [{"blocker": b, "blocked": d} for b, d in escritos],
              "mapWritten": not args.defer_map, "mapLine": linea, "mapArgs": flags,
              "noop": []}
    if args.defer_map:
        print(json.dumps(salida, separators=(",", ":")))
        return
    ediciones = {ANCLA_FUERA: ([], [linea])}
    if plan["graduadas"] or plan["niebla"]:
        ediciones[ANCLA_NIEBLA] = (plan["graduadas"], plan["niebla"])
    ok, detalle = _intentar_escribir(args.project, ediciones, plan["esperadas"],
                                     False, key)
    if not ok:
        faltante = ["map:write", "--project", args.project,
                    "--append-out-of-scope", plan["vineta"]]
        for titulo in plan["graduadas"]:
            faltante += ["--remove-fog", titulo]
        for vineta in plan["niebla"]:
            faltante += ["--append-fog", vineta[2:]]
        die(SIN_KEY,
            "la línea del mapa no se pudo escribir: %s. Todo lo demás ya aterrizó: los "
            "tickets nuevos, su cableado, el comentario y el ticket cancelado" % detalle,
            "corré exactamente esto para terminar a mano, y nada más: linear.py %s"
            % " ".join(_citar(t) for t in faltante))
    salida["noop"] = detalle
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

    # Los dos flags del grupo mutuamente excluyente son INVISIBLES para el extractor de
    # check-adapter.py, que solo ata variables asignadas desde add_parser: ninguna
    # afirmación puede depender de --project ni de --name. El --ctx sí cuelga directo del
    # subparser, así que la afirmación de los siete consumidores lo sigue viendo.
    p_map_create = subs.add_parser("map:create")
    p_map_create.add_argument("--ctx", required=True)
    p_map_create.add_argument("--destino", required=True)
    _origen_del_project = p_map_create.add_mutually_exclusive_group(required=True)
    _origen_del_project.add_argument("--project")
    _origen_del_project.add_argument("--name")
    p_map_create.set_defaults(func=cmd_map_create)

    p_map_read = subs.add_parser("map:read")
    p_map_read.add_argument("--project", required=True)
    p_map_read.set_defaults(func=cmd_map_read)

    # Sin --ctx a propósito: map:write es una de las cuatro operaciones que no lo
    # consumen. El gist va como su propio token de argv y nunca empaquetado con el
    # enlace, que es lo que permite aplicarle el tope al gist solo.
    p_map_write = subs.add_parser("map:write")
    p_map_write.add_argument("--project", required=True)
    p_map_write.add_argument("--append-decision", nargs=2, action="append",
                             default=[], metavar=("ENLACE", "GIST"))
    p_map_write.add_argument("--append-fog", action="append", default=[],
                             metavar="VINETA")
    p_map_write.add_argument("--remove-fog", action="append", default=[],
                             metavar="TITULO")
    p_map_write.add_argument("--append-out-of-scope", action="append", default=[],
                             metavar="LINEA")
    p_map_write.add_argument("--expect-sections")
    p_map_write.set_defaults(func=cmd_map_write)

    # --ticket copia la forma de --append-decision: nargs fijo, repetible y con el
    # default explícito. Repetible por la misma razón por la que map:write tiene sus
    # cuatro flags repetibles: la pasada entera entra en una sola invocación. LABELS es
    # una lista separada por comas, y cero labels se pasa como "".
    p_ticket_create = subs.add_parser("ticket:create")
    p_ticket_create.add_argument("--ctx", required=True)
    p_ticket_create.add_argument("--project", required=True)
    p_ticket_create.add_argument("--ticket", nargs=3, action="append", default=[],
                                 metavar=("TITULO", "CUERPO", "LABELS"))
    p_ticket_create.set_defaults(func=cmd_ticket_create)

    # Sin --ctx a propósito: ticket:block es una de las cuatro operaciones que no lo
    # consumen. Sus dos operandos son ids de tickets creados en la misma corrida, y
    # pasar ids adentro de una corrida es el mecanismo declarado. Repetible por la
    # misma razón que --ticket: la segunda pasada entera entra en una invocación.
    p_ticket_block = subs.add_parser("ticket:block")
    p_ticket_block.add_argument("--block", nargs=2, action="append", default=[],
                                metavar=("BLOQUEANTE", "BLOQUEADO"))
    p_ticket_block.set_defaults(func=cmd_ticket_block)

    p_frontier_query = subs.add_parser("frontier:query")
    p_frontier_query.add_argument("--ctx", required=True)
    p_frontier_query.add_argument("--project", required=True)
    p_frontier_query.set_defaults(func=cmd_frontier_query)

    # --issue y no --ticket: --ticket ya existe en ticket:create con nargs=3, y reusar
    # el mismo nombre con otra aridad entre subcomandos es una trampa de lectura. No es
    # repetible porque una sesión toma un ticket, y no hay --assignee a propósito.
    p_ticket_claim = subs.add_parser("ticket:claim")
    p_ticket_claim.add_argument("--ctx", required=True)
    p_ticket_claim.add_argument("--issue", required=True, metavar="IDENTIFICADOR")
    p_ticket_claim.add_argument("--release", action="store_true")
    p_ticket_claim.set_defaults(func=cmd_ticket_claim)

    # --section NOMBRE LINEA, repetible: el cuerpo del comentario cruza la CLI como
    # líneas físicas y nunca como markdown. _sin_saltos ya mata cualquier valor con un
    # salto, y un --body-file pediría un segundo open() que la afirmación 27 prohíbe.
    p_ticket_resolve = subs.add_parser("ticket:resolve")
    p_ticket_resolve.add_argument("--ctx", required=True)
    p_ticket_resolve.add_argument("--project", required=True)
    p_ticket_resolve.add_argument("--issue", required=True, metavar="IDENTIFICADOR")
    p_ticket_resolve.add_argument("--section", nargs=2, action="append", default=[],
                                  metavar=("NOMBRE", "LINEA"))
    # Sin --append-decision: el enlace de la línea del mapa sale del payload de la
    # propia escritura del estado, en el mismo round trip, así que no hay forma de que
    # la línea apunte a un ticket distinto del que se acaba de cerrar.
    p_ticket_resolve.add_argument("--gist", required=True)
    # Misma forma exacta que el --ticket de ticket:create, y el cableado se nombra por
    # título de un --new-ticket de esta misma invocación: los ids no existen hasta que
    # la primera escritura vuelve.
    p_ticket_resolve.add_argument("--new-ticket", nargs=3, action="append", default=[],
                                  metavar=("TITULO", "CUERPO", "LABELS"))
    p_ticket_resolve.add_argument("--block", nargs=2, action="append", default=[],
                                  metavar=("BLOQUEANTE", "BLOQUEADO"))
    p_ticket_resolve.add_argument("--append-fog", action="append", default=[],
                                  metavar="VINETA")
    p_ticket_resolve.add_argument("--remove-fog", action="append", default=[],
                                  metavar="TITULO")
    p_ticket_resolve.add_argument("--expect-sections")
    # Directo del subparser y NUNCA adentro de un grupo mutuamente excluyente: ahí el
    # extractor de check-adapter.py no lo vería y la afirmación 64 probaría sobre el
    # conjunto vacío, que es el mismo motivo por el que --project y --name de
    # map:create no pueden sostener ninguna.
    p_ticket_resolve.add_argument("--defer-map", action="store_true")
    p_ticket_resolve.set_defaults(func=cmd_ticket_resolve)

    # La misma superficie que ticket:resolve salvo una fila: acá va --out-of-scope y NO
    # existe --gist. La asimetría es el punto, y argparse la hace dura: un --gist sobre
    # ticket:rule-out no es un flag ignorado, es un error de invocación.
    p_ticket_rule_out = subs.add_parser("ticket:rule-out")
    p_ticket_rule_out.add_argument("--ctx", required=True)
    p_ticket_rule_out.add_argument("--project", required=True)
    p_ticket_rule_out.add_argument("--issue", required=True, metavar="IDENTIFICADOR")
    p_ticket_rule_out.add_argument("--section", nargs=2, action="append", default=[],
                                   metavar=("NOMBRE", "LINEA"))
    p_ticket_rule_out.add_argument("--out-of-scope", required=True, metavar="VINETA")
    p_ticket_rule_out.add_argument("--new-ticket", nargs=3, action="append", default=[],
                                   metavar=("TITULO", "CUERPO", "LABELS"))
    p_ticket_rule_out.add_argument("--block", nargs=2, action="append", default=[],
                                   metavar=("BLOQUEANTE", "BLOQUEADO"))
    p_ticket_rule_out.add_argument("--append-fog", action="append", default=[],
                                   metavar="VINETA")
    p_ticket_rule_out.add_argument("--remove-fog", action="append", default=[],
                                   metavar="TITULO")
    p_ticket_rule_out.add_argument("--expect-sections")
    p_ticket_rule_out.add_argument("--defer-map", action="store_true")
    p_ticket_rule_out.set_defaults(func=cmd_ticket_rule_out)

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
