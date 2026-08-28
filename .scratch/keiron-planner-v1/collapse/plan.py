# -*- coding: utf-8 -*-
"""Los cinco cortes y las veintiuna issues del colapso del mapa v1.

Datos y nada más: quien escribe es collapse.py. Los cuerpos siguen la plantilla
de tres secciones con texto exacto que fijó el ticket 06.
"""

R = "https://github.com/Keiron-HealthTech/keiron-planner/blob/main/.scratch/keiron-planner-v1/research"
I = "https://github.com/Keiron-HealthTech/keiron-planner/blob/main/.scratch/keiron-planner-v1/issues"

T = {
    "01": f"[01 · El grafo de dependencias de Linear]({R}/01-grafo-dependencias-linear.md)",
    "02": f"[02 · La API de Documents]({R}/02-api-documents-linear.md)",
    "03": f"[03 · Las operaciones en Linear]({R}/03-operaciones-en-linear.md)",
    "04": f"[04 · El juguete en Linear]({R}/04-el-juguete.md)",
    "05": f"[05 · Adaptar las tres disciplinas]({I}/05-adaptar-las-tres-disciplinas.md)",
    "06": f"[06 · El colapso]({R}/06-el-colapso.md)",
    "07": f"[07 · La distribución]({R}/07-distribucion.md)",
    "08": f"[08 · Los tres comandos]({R}/08-los-tres-comandos.md)",
    "09": f"[09 · La escritura del mapa]({R}/09-la-escritura-del-mapa.md)",
    "10": f"[10 · Los checks estructurales]({R}/10-los-checks.md)",
    "11": f"[11 · El Project vivo]({R}/11-el-project-vivo.md)",
    "12": f"[12 · El aterrizaje]({R}/12-el-aterrizaje.md)",
    "13": f"[13 · La pestaña abierta]({I}/13-pestana-abierta-pisa-al-plugin.md)",
    "14": f"[14 · El preflight]({R}/14-el-preflight.md)",
}


def produjeron(*keys):
    return "Lo produjeron " + ", ".join(T[k] for k in keys[:-1]) + " y " + T[keys[-1]] + "."


MILESTONES = [
    {
        "key": "m1",
        "sortOrder": 10.0,
        "name": "El plugin se instala y lee un Project",
        "description": (
            "El tracer bullet: instalar el plugin, guardar la key y leer un Project real "
            "sin escribirle un byte. Cruza todas las capas, del marketplace a la API de "
            "Linear y de vuelta, y se demuestra contra un Project vivo del CRM porque es "
            "read-only.\n\n" + produjeron("07", "14", "03", "08", "10")
        ),
    },
    {
        "key": "m2",
        "sortOrder": 20.0,
        "name": "El mapa se traza sobre un Project",
        "description": (
            "`/map-new` de punta a punta: el destino nombrado por la persona, el mapa "
            "escrito en el overview con lo que ya estaba preservado verbatim debajo, los "
            "primeros tickets creados y la frontera dibujándose sola en la UI de Linear."
            "\n\n" + produjeron("11", "08", "05", "04", "09", "13")
        ),
    },
    {
        "key": "m3",
        "sortOrder": 30.0,
        "name": "Una decisión se resuelve en el mapa",
        "description": (
            "`/map-work`: tomar un ticket, resolverlo con la disciplina que su tipo pide, "
            "escribir el comentario de seis secciones, cerrarlo y dejar la línea en el "
            "índice. Incluye research, que es el único tipo AFK.\n\n"
            + produjeron("08", "03", "04", "05")
        ),
    },
    {
        "key": "m4",
        "sortOrder": 40.0,
        "name": "El mapa colapsa y las decisiones tardías aterrizan",
        "description": (
            "`/map-collapse` con sus dos pasadas, y el aterrizaje que le consigue trabajo "
            "de ejecución a una decisión tomada después. Termina probando la costura: "
            "`/sdd-new` corriendo sobre una issue que nació de un colapso.\n\n"
            + produjeron("06", "12")
        ),
    },
    {
        "key": "m5",
        "sortOrder": 50.0,
        "name": "El equipo instala el plugin desde el marketplace",
        "description": (
            "La versión 0.1.0 publicada, la entrada en el marketplace del plugin hermano, "
            "las cuarenta y cuatro afirmaciones vivas en verde, y alguien que no es el dev "
            "leader mapeando un proyecto real.\n\n" + produjeron("07", "10")
        ),
    },
]


def body(construir, decidido, fuera):
    """Las tres secciones con texto exacto del 06."""
    return (
        "## Qué hay que construir\n\n" + construir.strip()
        + "\n\n## Lo que ya está decidido\n\n" + decidido.strip()
        + "\n\n## Qué queda fuera\n\n" + fuera.strip() + "\n"
    )


ISSUES = [
    # ---------------- Corte 1: el tracer bullet ----------------
    {
        "m": "m1",
        "title": "Crear el esqueleto del plugin, su manifiesto y el andamio de checks",
        "construir": """
- `.claude-plugin/plugin.json` en `0.1.0`, con `author`, `description` y `dependencies`
  con exactamente un elemento, `spec-driven-dev`, como string pelado y sin constraint.
- `LICENSE` MIT, con la atribución a Matt Pocock que `CONTEXT.md` ya declara.
- El campo `lang:` con valor `en` o `es` en el frontmatter de todo `.md` del árbol,
  `README.md` y `CONTEXT.md` incluidos, `vendor/` y `.scratch/` excluidos.
- `scripts/check-common.sh`: las raíces del árbol, el par `fail`/`report` que acumula,
  el `bail` del tercer tier y la regla anti-vacuidad. Lo sourcean los seis.
- `scripts/check-all.sh`, que saca la lista de un glob de `scripts/check-*` y nunca de
  una lista escrita.
- `scripts/CHECKS.md` con las cincuenta y cinco afirmaciones acuñadas, las cuarenta y
  cuatro vivas en estado `pendiente`, con su script, su método y su brecha.
- `.github/workflows/checks.yml`: un solo job, sobre `push` a main y `pull_request`,
  con el `npm i -g` del CLI y `actions/setup-python` en 3.9 exportado como `PY39`.
- `scripts/check-language.sh` con las afirmaciones 6 y 49, y `check-packaging.sh` con
  las 14, 15 y 21.
""",
        "decidido": """
- {T07}: el manifiesto, la dependencia declarada de verdad, la versión inicial y qué
  se publica.
- {T10}: los seis scripts y su reparto por concern, el job único y por qué no es uno
  por script, `CHECKS.md` como tabla viva, la columna de idioma en el frontmatter, y
  las reglas de acumular, no duplicar números y fallar en vacío.
""",
        "fuera": """
Los checks de lo que todavía no existe. Cada uno nace en la issue que construye lo
que chequea, y ahí su fila pasa de `pendiente` a `viva`. El `README.md` y el tag son
del corte 5.
""",
    },
    {
        "m": "m1",
        "title": "Escribir el instalador de la key y `/planner-setup`",
        "construir": """
- `scripts/install.sh`, POSIX `sh`, con los tres modos del prototipo del 01:
  interactivo, `--verify` y `--remove`.
- El chequeo del intérprete ejecutando `python3 -V` y parseando la versión, nunca con
  `command -v`, con el mensaje que nombra `xcode-select --install` para el Mac sin
  Command Line Tools.
- La validación de la credencial contra la API, trayendo `viewer` y `organization`,
  antes de guardarla.
- El guardado en `${XDG_CONFIG_HOME:-$HOME/.config}/keiron-planner/linear.key`, con el
  archivo en `0600` y el directorio en `0700`. La key no se imprime en ninguna ruta.
- `commands/planner-setup.md`, que rutea al script y no tiene skill.
- Las afirmaciones 17 y 18 en `check-packaging.sh`.
""",
        "decidido": """
- {T07}: el setup es por máquina y no por repo, su único alcance es la key, las dos
  casas descartadas, que no hay post-install hook, y que el intérprete es el `python3`
  del sistema.
- {T01}: el prototipo del instalador, del que sale la forma.
""",
        "fuera": """
Cualquier chequeo de la forma del workspace: eso es del preflight, que falla temprano
y claro. Un hook de `SessionStart` que detecte la key faltante. El snippet del
`README.md`, que es del corte 5.
""",
    },
    {
        "m": "m1",
        "title": "Escribir el preflight del adapter",
        "construir": """
- `scripts/linear.py`, stdlib pelado, compatible con Python 3.9, con el cliente GraphQL
  crudo contra `api.linear.app/graphql` y la key pelada en `Authorization`. El modelo
  no compone queries: las emite el script y lo llama por Bash.
- El subcomando `preflight`, un round-trip, que resuelve `viewer.id`, el team, el
  `completed` y el `canceled` de menor `position`, `defaultIssueState`, los ids de los
  nueve labels creando workspace-level los que falten, y el id de `Discovery` si existe,
  que se busca y nunca se crea.
- Cuatro fallas duras y solo cuatro, todas con código no cero: sin credencial, sin el
  team, sin algún estado de cerrado, y sin el label `map`.
- La salida es un blob JSON por stdout y nada más; todo lo demás va a stderr.
- `--bootstrap`, que apaga exactamente una falla y aparece solo en `/map-new`.
- `scripts/LINEAR-OPERATIONS.md`, en español, con la tabla de las doce operaciones.
- `scripts/check-adapter.py`, que lee `linear.py` con `ast`, con las afirmaciones 32 a
  38, 39a, 39b, 40 y 54, y `check-py39.sh` con la 19.
""",
        "decidido": """
- {T14}: corre una vez por conductor, y conductor es un contexto de modelo que emite
  operaciones. La salida es un blob opaco. Las cuatro fallas y `--bootstrap`.
- {T03}: el cliente único, los labels planos y workspace-level y por qué no son grupos,
  que no se cachea nada porque la fuente de verdad es Linear, y que no hay fallbacks.
- {T06}: `defaultIssueState` y el id de `Discovery`.
- {T12}: el noveno label, `map:no-landing`, que también se crea aunque el preflight no
  lo exija.
""",
        "fuera": """
Los siete subcomandos que consumen el ctx. Cada uno nace con su operación y declara
`--ctx` requerido ahí. Ninguno sabe hacer un preflight, y esa es la razón por la que
la regla se cumple por construcción.
""",
    },
    {
        "m": "m1",
        "title": "Escribir `frontier:query` y `map:read` con el predicado de frontera",
        "construir": """
- `frontier:query`: la query de un round-trip, página 50 por 10, con el filtro por
  label del lado del servidor. El tamaño de página no se toca.
- El predicado evaluado en el cliente, entero: abierto contra el par de ids cerrados
  que fijó el preflight y nunca contra `state.type`; sin assignee; y sin bloqueantes
  abiertos, leídos solo de `inverseRelations` con `type == "blocks"`.
- El orden por `createdAt` ascendente, ordenado en el cliente.
- El aviso fuerte cuando alguna de las tres conexiones vino truncada.
- La distinción entre mapa trabado y mapa listo para colapsar, que se ven igual y son
  opuestos.
- `map:read`, solo lectura, que devuelve el contenido del overview y una huella por
  cada encabezado.
- Las afirmaciones 23 y 53 en `check-adapter.py`.
""",
        "decidido": """
- {T03}: el predicado completo, que cerrado es un par de ids y no un test de tipo,
  el orden, el truncado silencioso y por qué importa, y que `Issue.sortOrder` no sirve.
- {T11}: el filtro por label deja afuera las issues de ejecución que ya viven en el
  Project, así que la frontera no se ensucia después del colapso.
- {T12}: `inverseRelations` es solo de bloqueos, y esa es la conexión que decide si un
  ticket es tomable.
""",
        "fuera": """
`map:write`, que es la otra mitad del read-modify-write y va en el corte 2 con sus
protecciones. El séptimo bloque del reporte, que es del corte 4.
""",
    },
    {
        "m": "m1",
        "title": "Escribir `/map-status` y el contrato compartido",
        "construir": """
- `skills/_shared/map-contract.md`, en inglés: el conjunto cerrado de seis tokens de
  `next_recommended`, el contrato de `$ARGUMENTS` y la tabla de tipo de ticket a
  disciplina. Son las tres cosas que más de un comando lee.
- `commands/map-status.md` con `ROUTE: read-only`, sin skill correspondiente.
- El reporte de seis bloques: destino, veredicto, frontera, tomados con su antigüedad,
  bloqueados con sus bloqueantes por nombre, y truncado. De la niebla, la cuenta de
  parches y no el texto.
- Los cuatro veredictos, con `projectMilestones` en la misma query que ya se hace.
- Los nombres son nombres: el identificador de Linear viaja adentro del enlace y nunca
  en lugar del nombre.
- Una corrida deja Linear byte a byte como estaba.
- Las afirmaciones 3 y 7 en `check-roster.sh`.
""",
        "decidido": """
- {T08}: por qué `/map-status` existe cuando en wayfinder no existe, los seis bloques,
  y que el contrato y las plantillas son tres archivos y no uno.
- {T06}: el cuarto veredicto, `colapsado`, y el sexto token, `sdd-new`.
- {T03}: frontera vacía no significa una sola cosa.
""",
        "fuera": """
El séptimo bloque, decisiones sin aterrizar, que nace con el aterrizaje en el corte 4.
Cualquier escritura: este comando no escribe en ningún modo.
""",
    },
]


ISSUES += [
    # ---------------- Corte 2: el mapa se traza ----------------
    {
        "m": "m2",
        "title": "Escribir `map:create` y `map:write`",
        "construir": """
- `map:create`: adopta el Project si le pasan uno y lo crea si no, y escribe el mapa en
  `Project.content`. Las secciones del mapa van arriba; lo que ya estaba se preserva
  **verbatim** debajo, bajo `Antes del mapa`. Nunca borra ni reescribe prosa que
  escribió una persona, y nunca reordena.
- `map:write`: un read-modify-write entero adentro de una sola invocación. Recibe la
  edición como argumentos semánticos y nunca markdown, y relee justo antes de escribir
  para que la ventana sean milisegundos y no la sesión.
- Acepta `--expect-sections`, y su ausencia no aborta.
- Exactamente un reintento, con su contador en un solo lugar y sin exponerlo como flag.
- Ninguna ruta compara `updatedAt` para decidir si escribir, ninguna pide
  `contentState`, ninguna verifica después de escribir y ninguna duerme.
- Ninguna ruta lee ni escribe un archivo de estado del contenido del mapa.
- El flag que agrega una decisión recibe el gist como argumento propio y rechaza más de
  120 caracteres con código no cero. El adapter no envuelve texto.
- Las afirmaciones 24, 26 a 31, 44 y 45 en `check-adapter.py`.
""",
        "decidido": """
- {T11}: el mapa es el overview del Project y no un Document, `Antes del mapa`, y que
  `Project` y `Document` son la misma pieza para Linear.
- {T09}: no se detecta el conflicto, se evita; releer justo antes de escribir baja la
  ventana a 332 ms; y nada de estado en disco.
- {T13}: la escritura mueve el estado Yjs, así que una pestaña abierta no deja rama que
  un cliente pueda ganar.
- {T04}: el índice es una línea por decisión y el gist tiene tope de 120 caracteres.
- {T02}: el tamaño no es blocker, y las transformaciones que el editor aplica en la
  primera escritura son punto fijo.
""",
        "fuera": """
Llenar `## El colapso`, que lo hace `/map-collapse` una sola vez. Cualquier
verificación posterior a la escritura: está prohibida a propósito.
""",
    },
    {
        "m": "m2",
        "title": "Escribir las plantillas del mapa",
        "construir": """
- `skills/_shared/map-templates.md`, en español, porque lo que genera lo lee una
  persona en Linear.
- Los seis encabezados del DD con texto exacto, que son contrato: el plugin ancla por
  título y nunca por posición, y si falta alguno falla fuerte en vez de escribir en el
  lugar equivocado.
- Las seis secciones del comentario de resolución, en orden, con `## Lo que se cayó`
  tercera, entre `## Por qué` y `## Niebla graduada`. Las vacías lo dicen.
- Las tres secciones del cuerpo de la issue de ejecución.
- Ninguna plantilla ni ningún comando contiene `<details>` ni `<summary>`.
- La entrada de `Decisiones hasta ahora` ocupa una línea física.
- `scripts/check-templates.sh` con las afirmaciones 9, 25, 42, 43 y 46.
""",
        "decidido": """
- {T04}: la forma del índice medida contra el juguete, las seis secciones del comentario
  y el tope del gist, y que `<details>` no sobrevive.
- {T08}: los encabezados son contrato, las Notas no otorgan permisos, y la sección de
  niebla graduada es obligatoria porque un paso omitido no falla solo.
- {T06}: el sexto encabezado, `## El colapso`, y las tres secciones del cuerpo de la
  issue de ejecución.
""",
        "fuera": """
Todo lo que va en inglés: eso es `map-contract.md`, que es otro archivo a propósito.
Meter una plantilla en español adentro del contrato en inglés es la clase de archivo
que se pudre.
""",
    },
    {
        "m": "m2",
        "title": "Escribir `ticket:create` y `ticket:block`",
        "construir": """
- `ticket:create`: un issue del Project cuyo cuerpo es la pregunta y nada más. El tipo,
  el modo, el bloqueo y la toma viven en campos nativos del tracker.
- Pasa `stateId` explícito, porque con `triageEnabled` una issue creada por API cae en
  Triage y no en el `defaultIssueState`. Pasa `estimate: 0`, porque un ticket de
  decisión no es entrega y no puede pesar en la vara con la que se mide la entrega.
- Los labels: `map`, el de tipo, el `hitl:<rol>` si corresponde, y `Discovery` cuando
  existe en el workspace, salteado en silencio cuando no.
- Es el único que crea los labels del plugin que falten, los nueve, aunque no los use
  todos, y nunca crea `Discovery`.
- Rechaza dos labels `map:<tipo>` en la misma issue con código no cero.
- `ticket:block`: la relación nativa, con el bloqueante siempre del lado `issue`,
  escrita en una segunda pasada porque los tickets tienen que existir para referenciarse.
- Las afirmaciones 11, 12, 38, 47 y 54 en `check-adapter.py`.
""",
        "decidido": """
- {T03}: el cuerpo es la pregunta y nada más, los campos nativos, la dirección del
  bloqueo y la segunda pasada, y que la creación de labels vive en un solo lugar.
- {T06}: `stateId` explícito contra Triage, `estimate: 0` y el label `Discovery`, los
  tres medidos contra el team CRM.
- {T10}: la exclusividad de tipo se chequea en el adapter y no contra Linear.
""",
        "fuera": """
Estirar la operación con un flag para que también cree issues de ejecución: anula la
invariante del cuerpo y rompe el check que cuenta subcomandos. Cablear bloqueos entre
issues de ejecución, que no se hace nunca.
""",
    },
    {
        "m": "m2",
        "title": "Keironizar grilling, domain-modeling y prototype, y abrir `/grill`",
        "construir": """
- Las tres skills bajo `skills/`, en inglés, model-invoked, con el frontmatter de SDD:
  `name`, `description`, `license`, y `metadata` con `author`, `version`, `scope` y
  `auto_invoke`. Cada una con su línea de atribución MIT.
- En prototype: el agente construye variantes y **nunca elige**. Un ticket
  `map:prototype` con una sola variante, o sin una elección dicha por la persona, no se
  resuelve, y la sección `La decisión` tiene que nombrar quién eligió.
- En grilling: se queda 1 a 1 y no aprende roles. Una pregunta que el interlocutor de
  turno no puede contestar sale como ticket con su `hitl:pm` o `hitl:design`.
- En domain-modeling: lee el puntero al repo central de dominio desde el `CLAUDE.md`
  del repo, procede en silencio cuando falta, y nunca sugiere crearlo.
- `commands/grill.md`, la única puerta user-invoked de las tres.
""",
        "decidido": """
- {T05}: las cuatro respuestas del ticket. El glosario canónico vive en un repo central
  alcanzado por un puntero de una línea; el multi-rol sale como ticket y no entra en la
  skill; las tres son model-invoked con `/grill` como única puerta; y van en inglés con
  el frontmatter de SDD para que importarlas después sea copiar un archivo.
- {T08}: los dos agujeros de wayfinder que acá se cierran, el de las Notas que otorgan
  permisos y el del prototipo donde el agente elige.
""",
        "fuera": """
Poblar el repo central de dominio: es trabajo del equipo y el plugin ni lo crea ni lo
puebla. El Tier B de Matt, triage, to-questionnaire, handoff y research como skills
propias, que está en Fuera de alcance del mapa.
""",
    },
    {
        "m": "m2",
        "title": "Escribir `/map-new` de punta a punta",
        "construir": """
- `commands/map-new.md` y `skills/map-new/SKILL.md`, con los ocho pasos.
- El destino lo nombra la persona, siempre, y el plugin nunca lo propone.
- La frontera se mapea breadth-first, a lo ancho y no a lo hondo, y **no hay corte**:
  sin niebla el mapa se crea igual y nace con Decisiones escritas, cero tickets y
  veredicto `map-collapse`.
- Sobre un Project que ya arrancó, muestra lo que encontró y pide confirmación una vez.
  Nunca se niega y nunca reescribe prosa ajena.
- `ticket:create` para todo lo que se pueda enunciar con precisión ahora, y
  `ticket:block` en una segunda pasada.
- `map:write` una sola vez, y `frontier:query` al cerrar: relee en vez de reportar de
  memoria.
- `--bootstrap` aparece en este comando y en ningún otro de `commands/`.
- Las afirmaciones 39a y la parte de la 8+16 que este comando cierra.
""",
        "decidido": """
- {T08}: los ocho pasos, el corte de wayfinder que se saca y por qué, y que
  `frontier:query` cierra este comando además de abrir `/map-work`.
- {T11}: la confirmación única sobre un Project vivo, el destino nombrado por la
  persona, y `Antes del mapa` como lugar de las decisiones heredadas.
- {T14}: `--bootstrap` y su alcance de exactamente una falla.
""",
        "fuera": """
Disparar los subagentes de research, que es el paso 6 y va en el corte 3. Los tickets
`map:research` se crean acá y quedan esperando en la frontera, que es un estado
legítimo y visible.
""",
    },

    # ---------------- Corte 3: una decisión se resuelve ----------------
    {
        "m": "m3",
        "title": "Escribir `ticket:claim`, `ticket:resolve` y `ticket:rule-out`",
        "construir": """
- `ticket:claim`: el primer write de la sesión, antes de cualquier trabajo. No se
  libera sola, ni siquiera cuando la sesión muere: eso lo reporta `/map-status`.
- `ticket:resolve`: cinco escrituras adentro de una sola invocación y en este orden.
  Los tickets nuevos, su cableado, el comentario de resolución, el estado, y el mapa
  siempre último. El orden lo garantiza el adapter y nunca el modelo.
- `ticket:rule-out`: la única operación destructiva. Misma secuencia, con el `canceled`
  del preflight, y la línea a `Fuera de alcance` y nunca a `Decisiones hasta ahora`.
- La afirmación 41 en `check-adapter.py`: las cinco escrituras en la misma función, sin
  punto de retorno entre ellas.
""",
        "decidido": """
- {T03}: la toma huérfana no se libera sola y por qué, la respuesta va como comentario
  para que la pregunta quede inmutable, y el orden que deja estado recuperable.
- {T08}: son cinco escrituras y no tres, y esta es la única operación que se parte
  entre procesos cuando la conduce un subagente de research.
- {T04}: las seis secciones del comentario, con `Lo que se cayó` tercera.
""",
        "fuera": """
El aterrizaje, que es un paso de `/map-work` y no de esta operación, y va en el corte 4.
Una segunda operación destructiva: el mapa tiene una sola a propósito.
""",
    },
    {
        "m": "m3",
        "title": "Escribir `/map-work` hasta el paso 8",
        "construir": """
- `commands/map-work.md` y su skill, con los pasos 1 a 8.
- El veredicto antes de elegir nada, y sin tomar en los dos casos que paran: mapa
  trabado emite `break-cycle`, mapa listo emite `map-collapse`, mapa colapsado emite
  `sdd-new`. Con al menos un ticket abierto trabaja normal y no mira milestones.
- La elección del ticket: el que nombró el argumento, o el primero de la frontera en
  `createdAt` ascendente. Sin argumento pregunta y para, y nunca adivina ni busca.
- El chequeo de rol **antes** de tomar. Si el label no es `hitl:dev`, pregunta si quien
  está del otro lado es ese rol o puede hablar por él, y se niega si no. Va antes del
  claim porque tomar y después negarse deja una toma huérfana.
- La tabla de disciplinas por tipo, cada fila con la regla que no se negocia.
- La graduación de niebla, con la sección obligatoria que dice `ninguna` cuando no
  graduó nada.
- La rama de la pregunta de otro rol: si la respuesta hace falta, crea el ticket, lo
  cablea como bloqueante, **suelta la toma** y para.
- Nunca más de un ticket por sesión, y research es la única excepción.
""",
        "decidido": """
- {T08}: los pasos, el chequeo de rol antes de tomar, la rama de otro rol con su
  devolución deliberada de la toma, y por qué la niebla graduada lleva negativo
  explícito.
- {T05}: el multi-rol sale como ticket y la ronda sigue sin esa pregunta.
- {T03}: el orden de la frontera y el predicado que decide qué es tomable.
- {T06}: el cuarto veredicto en el paso 3.
""",
        "fuera": """
Los pasos 9 y 10, el aterrizaje y el reporte de cierre que lo reporta, que van en el
corte 4.
""",
    },
    {
        "m": "m3",
        "title": "Cerrar research: el subagente, su Document y el reparto de escrituras",
        "construir": """
- `skills/_shared/research-subagent.md`, en inglés, el prompt que invocan `/map-new` y
  `/map-work` por igual. Es el mismo mecanismo desde dos lados, no dos mecanismos.
- La variante de `map:create` que usa solo su segunda mitad: el Document
  `RESEARCH: <título del ticket>` colgado del mismo Project. No es una operación nueva.
- El reparto de escrituras: cada subagente corre **su propio preflight** y escribe su
  Document, su comentario y su cambio de estado, que son recursos suyos. El mapa, que
  es el único recurso compartido, lo escribe solo el padre, una vez, con todas las
  líneas juntas.
- El paso 6 de `/map-new`, y el manejo desde `/map-work` de todos los `map:research` de
  la frontera en paralelo. Si el argumento nombra uno, agarra ese solo.
""",
        "decidido": """
- {T08}: no hay rama descartable de research porque el polyrepo obliga a elegir repo, no
  hay skill de research propia, la concurrencia de los subagentes baja las escrituras
  del mapa de N a 1, y el preflight es uno por proceso que emite operaciones.
- {T14}: conductor es un contexto de modelo que emite operaciones; un subagente es uno,
  un subcomando no.
""",
        "fuera": """
Una skill de research propia del plugin: el Tier B completo está en Fuera de alcance
del mapa y ese límite no se corre. Pasarle al subagente los ids ya resueltos por el
padre, que es acoplamiento a cambio de nada.
""",
    },
]


ISSUES += [
    # ---------------- Corte 4: el colapso y el aterrizaje ----------------
    {
        "m": "m4",
        "title": "Escribir `milestone:create` y `work:write`",
        "construir": """
- `milestone:create`: un corte demoable, **sin `targetDate` nunca**, porque un milestone
  no es un corte temporal y sin fecha `overdue` es inalcanzable. `sortOrder` explícito y
  distinto de cero, porque el cero es lo único que Linear recalcula y lo manda al final.
  Las anclas salen de lo que devuelve la API.
- `work:write`, en una sola invocación y con tres desenlaces posibles: las issues de
  ejecución en una llamada atómica con `issueBatchCreate`, las relaciones `related`
  hacia el ticket de decisión, y el label `map:no-landing` cuando no hubo trabajo.
- Con la lista de issues vacía **no** se llama a `issueBatchCreate`: la API la rechaza
  con `arrayNotEmpty`.
- La relación va con el ticket de decisión del lado `issueId` y la issue de ejecución
  del lado `relatedIssueId`, al revés que `ticket:block` y a propósito, para que no caiga
  en `inverseRelations` y no compita con los bloqueos por el tope de paginación.
- Ninguna issue de ejecución lleva label `map` ni `Discovery`, ninguna lleva `estimate`,
  todas llevan `stateId` explícito, y todas nacen con su corte puesto.
- Las afirmaciones 13, 48, 51 y 52 en `check-adapter.py`.
""",
        "decidido": """
- {T06}: las dos operaciones nuevas y por qué no son variantes de `ticket:create`, el
  batch atómico, sin `estimate` y el costo que eso tiene, y que no se cablea ningún
  bloqueo entre issues de ejecución.
- {T12}: el renombre a `work:write` y por qué, la guarda de la lista vacía, la dirección
  de la relación con su medición del tope de complejidad, y el `sortOrder` corregido.
""",
        "fuera": """
Mover issues de corte, borrar milestones, o cualquier semántica de merge entre dos
colapsos: la idempotencia es por rechazo y no por merge. Ligar las decisiones anteriores
al colapso, que costaría M round-trips y una tercera ventana de falla.
""",
    },
    {
        "m": "m4",
        "title": "Escribir `/map-collapse` con sus dos pasadas",
        "construir": """
- `commands/map-collapse.md` y `skills/map-collapse/SKILL.md`, con los nueve pasos.
- La precondición: cero tickets de decisión abiertos y cero milestones.
- El rechazo de la segunda corrida, partido en dos: con milestones y cero issues de
  ejecución es un colapso que murió a la mitad, lo dice y ofrece retomar desde el paso 5;
  con issues adentro se niega duro.
- Primera pasada, los cortes: el agente propone, la persona aprueba o redibuja, y nada
  se escribe. El primero es siempre el tracer bullet y **se grillea**, porque es la
  única pieza del colapso que las decisiones no contienen.
- Segunda pasada, las issues, que no arranca hasta que los cortes estén aprobados.
- La `description` del milestone nombra las decisiones que produjeron ese corte, por
  nombre y con enlace. Esa es toda la trazabilidad, y va ahí y no en cada issue.
- `## El colapso` se llena una sola vez, con los milestones por nombre y enlace.
- El reporte de cierre nombra la primera issue del primer corte con su URL y emite
  `sdd-new` pelado.
""",
        "decidido": """
- {T06}: el procedimiento entero, que es HITL y evento único, las dos pasadas y por qué
  no se mezclan, la secuencia N+2, el colapso a medias, y la idempotencia por rechazo.
""",
        "fuera": """
El colapso incremental y el descolapso, que no existen. Escribir artefactos de SDD en
ningún repo: el traspaso ocurre en `/sdd-new`. Tocar cualquier campo del Project, que es
ciclo de vida de PM.
""",
    },
    {
        "m": "m4",
        "title": "Agregar el aterrizaje a `/map-work` y el séptimo bloque a `/map-status`",
        "construir": """
- Los pasos 9 y 10 de `/map-work`. El aterrizaje corre después de `ticket:resolve`, solo
  si el Project tiene al menos un milestone y solo en sesiones HITL de `map:grilling` o
  `map:prototype`.
- Los tres desenlaces: issues nuevas, ligar a una issue de ejecución que ya existe, o
  nada, y el tercero se marca con `map:no-landing`.
- El corte donde aterriza: uno existente, o uno nuevo insertado con un `sortOrder`
  estrictamente entre los de sus dos vecinos. **Nunca un corte con `status: done`**, que
  se lee antes de escribir y no se relee para verificar, porque es denormalizado.
- Cuando todos los cortes están terminados y llega una decisión que pide corte, el corte
  nace igual y el comando lo dice en voz alta: esto reabre el proyecto y puede ser la
  señal de que el destino estaba mal trazado.
- El séptimo bloque de `/map-status`, decisiones sin aterrizar, por nombre y con su
  antigüedad desde `completedAt`, con el predicado completo del 12.
- La afirmación 55.
""",
        "decidido": """
- {T12}: el aterrizaje entero. Por qué vive en `/map-work` y no en `/map-collapse`, los
  tres desenlaces y por qué el del medio es el más común, el noveno label, el predicado
  del reporte, y el aterrizaje a medias que se acepta y se nombra.
""",
        "fuera": """
Cambiar el trabajo de ejecución que una decisión tardía deja mal: está en Fuera de
alcance del mapa y no gradúa. Un séptimo token o un quinto veredicto. Que `/map-work`
sobre un mapa colapsado sin tickets abiertos ofrezca retomar aterrizajes pendientes, que
es el colapso incremental entrando por la ventana.
""",
    },
    {
        "m": "m4",
        "title": "Probar la costura con `/sdd-new`",
        "construir": """
- Correr `/sdd-new` sobre una issue de ejecución nacida de un colapso, de punta a punta,
  y dejar escrito qué pasó.
- Verificar tres cosas. Que el orchestrator de SDD trae la issue con las herramientas de
  Linear y le pasa el contexto a `sdd-explore`, que es la puerta que ya existe. Que el
  discovery loop arranca sin volver a litigar lo que la sección `Lo que ya está decidido`
  enlaza. Y que el cuerpo de tres secciones alcanza sin tener forma de proposal, que es
  justamente lo que lo haría saltear el pensamiento que existe para hacer.
- Si algo no cierra, el arreglo es de la plantilla del cuerpo de la issue, de este lado
  de la costura.
""",
        "decidido": """
- {T06}: el traspaso ocurre en `/sdd-new` y no en `/sdd-apply`, la puerta ya existe y
  nadie la usa, y el cuerpo no es un proposal a propósito.
- {T07}: la dirección de la dependencia. SDD construye, el planner planifica.
""",
        "fuera": """
Cambiar cualquier archivo del repo de `spec-driven-dev`: la PR del corte 5 toca el
marketplace y su README, y nada más. Escribir `openspec/changes/` desde este plugin.
""",
    },

    # ---------------- Corte 5: el equipo lo instala ----------------
    {
        "m": "m5",
        "title": "Cerrar las cuarenta y cuatro afirmaciones vivas",
        "construir": """
- Repasar `scripts/CHECKS.md` entero y pasar a `viva` toda fila cuyo check ya exista.
  Es donde se nota si algo se construyó sin chequearse.
- Cerrar la brecha medida de la afirmación 14: `claude plugin validate --strict` deja
  pasar limpio un `SKILL.md` sin `name:`. Se cierra desde `check-roster.sh`, que ya
  camina `skills/`, y sale casi gratis.
- Hacer valer la afirmación 50: los números marcados `viva` y los `[N]` que emiten los
  seis scripts son el mismo conjunto.
- CI en verde, con el job único corriendo `check-all.sh`.
""",
        "decidido": """
- {T10}: la tabla de las cincuenta y cinco acuñadas con su script y su método, los seis
  scripts, que cada check nace con lo que chequea, las reglas de acumular y de no
  escribir dos veces un número, y qué brecha se acepta en cada fila.
""",
        "fuera": """
Las seis brechas que solo cierra un test de comportamiento del adapter: siguen en niebla
y no se cierran acá. Un `check-linear.sh` que pegue contra la API, descartado porque mete
una credencial en CI.
""",
    },
    {
        "m": "m5",
        "title": "Escribir el README y publicar la versión 0.1.0",
        "construir": """
- `README.md`, con `lang: es`, el snippet de instalación
  `/plugin install keiron-planner@spec-driven-dev`, y `/planner-setup` nombrado.
- El tag, creado con `claude plugin tag --push`, que deriva `keiron-planner--v0.1.0` de
  la versión del manifiesto sin necesitar una entrada de marketplace alrededor.
- La afirmación 20 en `check-packaging.sh`.
""",
        "decidido": """
- {T07}: la convención de tags, la versión inicial `0.1.0` y por qué dice la verdad, el
  orden de publicación con el tag antes que la PR, y que el `README.md` va en español
  porque su lector es una persona del equipo y el repo es internal.
""",
        "fuera": """
La entrada del marketplace, que va después y en otro repo. Decidir cómo se actualiza el
plugin: el auto-update ya viaja con la configuración del marketplace del hermano y no hay
nada que decidir hasta que alguien se queje.
""",
    },
    {
        "m": "m5",
        "title": "Abrir la PR al marketplace de `spec-driven-dev`",
        "construir": """
- Una PR al repo hermano, una sola vez, con dos cosas y nada más. La entrada en
  `.claude-plugin/marketplace.json`, apuntando a `Keiron-HealthTech/keiron-planner` por
  `source: github`, **sin `version` y sin `ref`**. Y una línea en su `README.md` diciendo
  que ese marketplace hospeda dos plugins, con el snippet de instalación del planner.
- Va después del tag y nunca antes: una entrada viva apuntando a un repo sin
  `.claude-plugin/` no reserva un lugar, publica una falla.
""",
        "decidido": """
- {T07}: por qué entra al marketplace ajeno y no a uno propio, que sin `version` cada
  release nuestro no pide una PR allá, el alcance exacto de la PR, y que **no** toca la
  skill `using-sdd`, porque hacerlo invierte la dirección de la dependencia.
""",
        "fuera": """
Un marketplace nuevo de la organización, descartado porque obliga a todo el equipo a
agregar uno que ya tiene puesto. Los tags de SDD, que están fuera de la convención y son
problema del repo hermano.
""",
    },
    {
        "m": "m5",
        "title": "Correr el plugin sobre el primer proyecto real del CRM",
        "construir": """
- Instalar desde el marketplace en una máquina que **no** sea la del dev leader, correr
  `/planner-setup`, y mapear un proyecto de verdad de punta a punta hasta el colapso.
- Es lo que verifica el supuesto que el 07 dejó abierto y no pudo medir: que
  `source: github` alcanza un repo `INTERNAL` con las credenciales de git de quien
  instala. Si pidiera un token, el arreglo es una línea, cambiar `source: github` por
  `source: url` con la URL `.git` completa, que usa el credential helper.
- Dejar escrito qué se rompió, si se rompió algo.
""",
        "decidido": """
- {T07}: el supuesto y su arreglo de una línea, que el intérprete es el `python3` del
  sistema para que nadie tenga que instalar nada, y el caso del Mac sin Command Line
  Tools que el instalador nombra en su mensaje.
""",
        "fuera": """
Publicar el plugin fuera de Keiron, que está en Fuera de alcance del mapa. Soportar
Linux más allá de que el mensaje de error quede fuera de lugar sin ser dañino.
""",
    },
]


def render(text):
    """Reemplaza los punteros {TNN} por el enlace al documento que decidió."""
    out = text
    for k, v in T.items():
        out = out.replace("{T" + k + "}", v)
    return out


def issue_body(issue):
    return render(body(issue["construir"], issue["decidido"], issue["fuera"]))
