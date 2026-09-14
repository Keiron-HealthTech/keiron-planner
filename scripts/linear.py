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

# Las tres anclas que map:write edita, tomadas de ANCLAS por posición y nunca
# reescritas: una segunda copia del texto del encabezado se desincroniza en el primer
# rename, y el orden de ANCLAS ya es contrato.
ANCLA_DECISIONES = ANCLAS[2]
ANCLA_NIEBLA = ANCLAS[3]
ANCLA_FUERA = ANCLAS[4]

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


def _validar_niebla(valor):
    """Las cinco reglas de forma de una viñeta de niebla, sobre el valor que llegó por
    argumento. Devuelve el título, que es además su clave de unicidad. La guarda del
    encabezado no hace falta acá: la regla de que el valor empieza con ** ya impide que
    una viñeta de niebla pueda ser un encabezado."""
    _sin_saltos("--append-fog", valor)
    titulo = titulo_en_negrita(valor) if valor.startswith("**") else None
    if titulo is None:
        die(SIN_KEY,
            "--append-fog recibió %r, y una viñeta de niebla tiene que empezar con su "
            "título entre dobles asteriscos" % valor,
            'escribila como "**Título.** cuerpo" y volvé a correr')
    cuerpo = valor[valor.find("**", 2) + 2:]
    if cuerpo[:1] != " " or cuerpo[1:2] == " " or not cuerpo.strip():
        die(SIN_KEY,
            "--append-fog recibió %r, y después del título cerrado tiene que venir "
            "exactamente un espacio y un cuerpo no vacío" % valor,
            'escribila como "**Título.** cuerpo" y volvé a correr')
    return titulo


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
        if len(gist) > 120:
            die(SIN_KEY,
                "el gist de --append-decision tiene %s caracteres y el tope es de 120: "
                "%r" % (len(gist), gist),
                "acortá el gist; el detalle va en el comentario de resolución del "
                "ticket y el mapa nunca lo repite")
        _no_es_encabezado("--append-decision", enlace)
        _no_es_encabezado("--append-decision", gist)
        anotar(ANCLA_DECISIONES, 1, "- %s: %s" % (enlace, gist))

    for valor in args.append_fog:
        _validar_niebla(valor)
        anotar(ANCLA_NIEBLA, 1, "- %s" % valor)

    for titulo in args.remove_fog:
        _sin_saltos("--remove-fog", titulo)
        if not titulo.strip():
            die(SIN_KEY, "--remove-fog recibió un título vacío",
                "pasá el título de la viñeta, sin los asteriscos")
        anotar(ANCLA_NIEBLA, 0, titulo)

    for valor in args.append_out_of_scope:
        _sin_saltos("--append-out-of-scope", valor)
        if not valor.strip():
            die(SIN_KEY, "--append-out-of-scope recibió una línea vacía",
                "pasá la línea que querés dejar fuera de alcance")
        _no_es_encabezado("--append-out-of-scope", valor)
        anotar(ANCLA_FUERA, 1, "- %s" % valor)

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
