---
lang: es
---

# LINEAR-OPERATIONS

El contrato del adapter, al lado del script que lo implementa. Su lector es quien
mantiene `scripts/linear.py`. No es una skill: es un contrato, no una disciplina que
el modelo tenga que razonar.

La columna `Canónico` es el nombre que aparece en el código, y es la que se compara
contra los subcomandos que declara el adapter. La misma lista vive en la tabla
`Las operaciones del tracker` de `CONTEXT.md`, que la explica para el equipo; acá está
para que el adapter tenga su contrato a mano.

## Las doce operaciones

| Canónico | Qué es |
| --- | --- |
| `preflight` | Resuelve en una sola llamada de red, y sin escribir nada, todo lo que las otras once necesitan del workspace. |
| `map:create` | Adopta o crea el Project y escribe el mapa en su overview. |
| `map:read` | Solo lectura. Devuelve el contenido y una huella por encabezado. |
| `map:write` | Un read-modify-write entero adentro de una sola invocación. |
| `ticket:create` | Los tickets de decisión de una pasada, en una sola invocación, cada uno con un cuerpo que es la pregunta y nada más. |
| `ticket:block` | La relación nativa de bloqueo, en una segunda pasada. |
| `frontier:query` | Los tickets abiertos, sin bloqueantes abiertos y sin assignee. |
| `ticket:claim` | Tomar. El primer write de la sesión, y con `--release` la escritura inversa, que devuelve la toma. |
| `ticket:resolve` | Las cinco escrituras de una resolución, en una sola invocación, y con `--defer-map` solo las cuatro primeras: la quinta no se manda y la línea que le tocaba sale por stdout. |
| `ticket:rule-out` | Cierra un ticket sin resolverlo. La única destructiva. Acepta `--defer-map` con el mismo efecto. |
| `milestone:create` | Un corte demoable del colapso. Nunca lleva fecha. |
| `work:write` | Lo que produce un colapso o un aterrizaje, en una sola invocación. |

## Los códigos de salida del preflight

| Código | Constante | Falla dura | Remediación | Marca |
| --- | --- | --- | --- | --- |
| 3 | `SIN_KEY` | No hay credencial en disco, está vacía, o Linear la rechazó: un error con `AUTHENTICATION_ERROR` o `FORBIDDEN`, o con status 401 o 403. | Instalar o reinstalar la credencial corriendo `/planner-setup`. | `/planner-setup` |
| 4 | `SIN_TEAM` | El team que nombra `--team` no existe, o la credencial no lo ve. | Corregir la key del team que se le pasa a `--team`. | la key del team |
| 5 | `SIN_CERRADOS` | El team no tiene un estado `completed`, o no tiene uno `canceled`. | Revisar el workflow del team y dejarle los dos estados. | el workflow del team |
| 6 | `SIN_LABEL_MAP` | El label `map` no existe en el workspace. | Correr el preflight con `--bootstrap` la primera vez, cuando el label todavía no está. | `--bootstrap` |
| 7 | `SIN_API` | Linear devolvió un error que no es de credencial: un rate limit, un 5xx, una query rota, o la red no llegó. | Esperar un minuto y reintentar. La credencial no se toca. | `reintenta en un minuto` |

Los cinco códigos son distintos entre sí y ninguno es cero. La columna `Marca` es la
subcadena que el mensaje de esa falla emite por stderr, y se copia byte a byte: la
comparación es literal, va sin acentos para que no dependa de la codificación de la
salida, y las cinco marcas tienen que ser distintas entre sí, porque una remediación
genérica pasaría las cinco sin distinguirlas. Reformular una marca sin tocar el
mensaje, o al revés, deja el contrato y el script en desacuerdo.

Los otros tres códigos que el adapter puede devolver no son fallas duras del preflight.
El **9** (`NO_IMPLEMENTADO`) es el de un subcomando sin cuerpo. Hoy los doce
tienen cuerpo, así que ninguno lo emite: el código y la función `cmd_stub` que lo
devuelve quedan definidos, sin ningún subcomando registrado contra ella. El
**2** lo emite `argparse`, y cubre tres casos: falta el subcomando, falta un argumento
requerido, o el subcomando no existe. El **1** queda reservado para lo que el script no
pudo decidir.

## La salida de las dos operaciones de lectura

Las dos escriben **una sola línea de JSON compacto** a stdout, sin espacios entre los
separadores y sin desactivar el escapado a ASCII, así que la línea sale en ASCII puro y
todo carácter acentuado viaja como su escape Unicode. Del otro lado, el parseo lo
deshace y devuelve la clave con su tilde, idéntica letra por letra al encabezado del
mapa, que es lo que la vuelve utilizable como ancla.

### `frontier:query`

Siete claves de primer nivel, las siete siempre presentes:

    found        bool. false cuando el Project no resolvió. Con found en false los tres
                 conteos son cero y las cuatro listas están vacías, que es la misma
                 forma que tiene un mapa ya terminado: found es lo único que los separa.
    truncated    lista de string. Subconjunto de issues, relations, inverseRelations y
                 projectMilestones, en ese orden fijo. Vacía si ninguna conexión vino
                 cortada. Cada nombre que aparece acá lleva además una línea a stderr, y
                 el código de salida sigue siendo 0 en todos los casos. Con issues
                 truncada, unlanded también queda como cota inferior; con relations
                 truncada, una decisión con más de diez relaciones puede aparecer en
                 unlanded aunque ya esté ligada a trabajo de ejecución; con
                 projectMilestones truncada, milestones también queda como cota
                 inferior además de counts.milestones, y el vecino que hace falta para
                 insertar un corte en el medio puede no estar en la lista.
    counts       objeto de tres claves enteras, open, takeable y milestones. open cuenta
                 los tickets cuyo state.id no es ninguno de los dos ids cerrados del
                 ctx. takeable cuenta los que además pasan las otras dos condiciones.
                 Con issues cortada los dos son cotas inferiores. milestones cuenta los
                 nodos de projectMilestones que trajo la respuesta, y es cota inferior
                 cuando esa conexión vino cortada.
    tickets      lista de objeto. Los abiertos tomables, createdAt ascendente.
    notTakeable  lista de objeto. Los abiertos no tomables, createdAt ascendente.
    milestones   lista de objeto, ordenada por sortOrder ascendente. Cada uno con id,
                 name, sortOrder, status, createdAt y hasIssues. Vacía cuando el
                 Project no tiene ningún milestone todavía, el mismo caso que
                 counts.milestones en cero.
    unlanded     lista de objeto. Los tickets de decisión CERRADOS cuyo label de tipo es
                 map:grilling o map:prototype, cerrados después del createdAt del
                 milestone más viejo del Project, sin ninguna relación related en
                 relations y sin el label map:no-landing. completedAt ascendente. Vacía
                 cuando no hay ninguno o cuando el Project no tiene ningún milestone
                 todavía (sin milestone no hay umbral de nacimiento, así que nada puede
                 estar sin aterrizar).

No hay campo de veredicto, con ningún nombre. Ni `verdict`, ni `stuck`, ni
`readyToCollapse`, ni un booleano equivalente: el veredicto se deriva de los tres
conteos, y lo deriva quien consume esta salida.

`milestones` tampoco es un veredicto disfrazado. Es un entero y nunca un booleano, y
dice cuántos milestones hay y jamás qué significa que los haya. Quien consume la salida
es el que decide que cero abiertos con cero milestones es una cosa y cero abiertos con
al menos uno es otra: sin el tercer conteo los dos casos son indistinguibles, que es el
bug que el ticket 06 nombró.

Una entrada de `tickets` lleva cinco claves, las cinco siempre presentes:

    identifier   string. El identificador de Linear, CRM-3401.
    title        string. El nombre del ticket.
    url          string. El enlace de Linear.
    createdAt    string. ISO 8601 en Z con milisegundos.
    labels       lista de string. Los nombres de sus labels.

Una entrada de `notTakeable` lleva siete: esas cinco, con el mismo tipo y el mismo
significado, más estas dos, también siempre presentes:

    assignee     string o null. El displayName de quien lo tiene tomado, y null si no
                 lo tiene nadie.
    blockers     lista de objeto. Sus bloqueantes abiertos, y vacía si no tiene
                 ninguno.

Cada objeto de `blockers` lleva tres claves, las tres string y las tres siempre
presentes:

    identifier   string. El identificador del bloqueante.
    title        string. Su nombre. El identificador viaja adentro del enlace y nunca
                 en lugar del nombre: una pared de identificadores es ilegible.
    url          string. El enlace del bloqueante.

Un bloqueante cerrado no viaja: ya no bloquea, y mandarlo obligaría a repetir contra el
par de ids cerrados el mismo predicado que este comando acaba de evaluar.

Un ticket puede estar tomado **y** bloqueado a la vez, y por eso `notTakeable` es una
sola lista y no dos. Con dos listas hay que elegir en cuál cae, y el bloque que lo
pierda miente. `assignee` y `blockers` son la razón por la que ese ticket no es tomable,
y las razones se acumulan: un ticket aparece en `notTakeable` como máximo una vez, sin
importar cuántas de las dos condiciones falle.

Dos invariantes que el consumidor puede asertar gratis:

    len(tickets) == counts.takeable
    len(tickets) + len(notTakeable) == counts.open

Una entrada de `unlanded` lleva cuatro claves, las cuatro siempre presentes:

    identifier   string. El identificador de Linear del ticket de decisión.
    title        string. El nombre del ticket.
    url          string. El enlace de Linear.
    completedAt  string. ISO 8601 en Z con milisegundos: cuándo se cerró.

`unlanded` es un ticket **cerrado**, así que no repite `labels`: quien lo necesita ya sabe,
por estar en esta lista, que lleva el label de tipo `map:grilling` o `map:prototype` y no
lleva `map:no-landing`. Y no repite `createdAt`: `completedAt` es el dato que importa acá,
igual que `blockers` no repite el `state` de su bloqueante.

### `map:read`

Tres claves de primer nivel, las tres siempre presentes:

    found        bool. false cuando el Project no resolvió.
    content      string o null. El texto del overview ya normalizado por el paso 1 de
                 la regla de la huella, o null si la API lo devolvió nulo o ausente. Un
                 texto vacío se pasa tal cual y no se colapsa a null: la diferencia
                 entre "no hay overview" y "el overview está vacío" no cuesta nada
                 conservar.
    sections     objeto de seis claves, siempre las seis.

Las seis claves de `sections` son los seis encabezados canónicos sin el `## `, en este
orden, que es contrato:

    Destino
    Notas
    Decisiones hasta ahora
    Aún no especificado
    Fuera de alcance
    El colapso

Van en español porque **son** las anclas: su texto tiene que coincidir letra por letra
con el encabezado del mapa. Es la única mezcla de idiomas de las dos salidas y tiene
razón de ser.

### La regla de la huella, entera

Es lo que `map:write --expect-sections` va a tener que reproducir letra por letra, y son
dos mitades. La primera dice **qué bytes se hashean**, en seis pasos:

    1. Sobre todo el content se normalizan los fines de línea una sola vez: CRLF y CR
       solo pasan a LF. La clave content de la salida lleva el texto ya normalizado,
       así que las seis huellas son reproducibles desde content y nada más, sin conocer
       el payload crudo.
    2. Una línea es el ancla de una sección si su texto sin espacios al final es
       exactamente "## " más el encabezado. Solo se sacan los espacios del final, nunca
       los del principio: una línea indentada no matchea, para que dos líneas no puedan
       disputarse la misma ancla.
    3. El cuerpo son las líneas entre el ancla y la primera línea posterior cuyo texto
       sin espacios al final empieza con "## " o con "# ", o el final del texto. Un
       encabezado de nivel tres o más profundo pertenece al cuerpo.
    4. El encabezado mismo no entra en los bytes que se hashean. Es el ancla, ya es la
       clave del JSON, y map:write reescribe cuerpos y nunca encabezados.
    5. A cada línea del cuerpo se le sacan los espacios del final, las líneas se unen
       con LF, y al resultado se le sacan los saltos de línea del principio y del
       final. Los espacios del principio de una línea no se tocan: son el anidado de
       una viñeta y son señal.
    6. Los bytes se codifican en UTF-8, explícito. El mapa tiene tildes y eñes, y el
       default de la plataforma no es contrato.

La segunda mitad dice **con qué se hashean y cómo se escribe el resultado**:

    7. El algoritmo es sha256 y el valor es su hexdigest completo: 64 caracteres
       hexadecimales, sin truncar nunca.
    8. La clave vale null cuando el ancla NO ESTÁ en el contenido, y por ninguna otra
       razón.
    9. Una sección presente y vacía no vale null: lleva la huella de la cadena vacía,
       que es e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855.

Los seis pasos solos serían media regla, y media regla es peor que ninguna: quien
reproduzca únicamente los bytes puede elegir otro algoritmo, truncar el hexadecimal o
colapsar la ausencia contra el vacío, y las tres cosas rompen `--expect-sections` sin
violar ninguno de los seis pasos. Confundir el paso 8 con el 9 es el bug que dejaría a
`map:write` sin poder distinguir "me borraste la sección" de "tu sección está vacía".

El paso 5 es el que vuelve la huella un detector de deriva y no uno de serialización.
El round trip de Linear no es identidad: las viñetas con guion vuelven con asterisco y
las URLs vuelven envueltas en `<>`. Una línea en blanco ganada o perdida en el borde de
una sección es churn cosmético, y una huella que se moviera con eso reportaría deriva
donde no pasó nada. Los saltos de línea interiores sí se preservan, porque agregar una
línea adentro de una sección es exactamente la señal que hay que ver.

El precio aceptado es que el paso 5 vuelve invisible un salto de línea duro de markdown,
o sea los dos espacios al final de una línea. El mapa es viñetas y líneas de una sola
línea, no prosa con saltos duros.

Un ancla duplicada hashea la primera aparición, emite un aviso por stderr nombrándola, y
el código de salida sigue siendo 0. Abortar por ancla ambigua es regla de escritura, y
le toca a `map:write`.

## La salida de las operaciones que escriben sobre un ticket

### `ticket:claim`

Una sola línea de JSON compacto, con la misma regla de separadores y de escapado a
ASCII que las dos operaciones de lectura. Tres claves de primer nivel, las tres
siempre presentes:

    issue         string. El identificador que devolvió la mutation, CRM-3401, y el
                  que se le pasó a --issue cuando la respuesta no lo trajo.
    assignee      string o null. El id del usuario que quedó asignado, que es el
                  viewer del ctx, y null después de un --release.
    assigneeName  string o null. El displayName que la mutation devolvió en el mismo
                  round trip. Viaja porque es lo único legible para una persona, y
                  aparte de assignee porque quien compone el reporte necesita el id
                  sin volver a resolverlo.

El write es uno solo, un `issueUpdate` que escribe `assigneeId` y ninguna otra clave.
No hay `--assignee`, y su ausencia es deliberada: el asignado sale de `ctx["viewer"]`
y de ningún otro lado, para que el modelo no pueda tomar en nombre de otra persona.

**La toma huérfana y la devolución deliberada son dos cosas distintas.** Una sesión
que tomó un ticket y murió deja el ticket asignado, fuera de la frontera, y nada del
plugin lo libera solo: ninguna corrida sin `--release` explícito limpia un assignee.
`--release` es la otra mitad, y es un write de una sesión viva, con una persona
mirando, para cuando el trabajo se pausa porque hace falta otro rol. Es la **única**
vía del plugin entero que deja un `assigneeId` en nulo.

No reintenta. Es un solo campo de un solo issue, así que repetir la invocación entera
es la remediación correcta y no duplica nada.

### `ticket:resolve`

Once flags, y `--ctx`, `--project`, `--issue` y `--gist` son los cuatro requeridos:

    --ctx              el blob del preflight, opaco.
    --project          el Project cuyo overview lleva el mapa, en cualquiera de las
                       tres formas que el adapter resuelve.
    --issue            el identificador del ticket que se resuelve, CRM-3401, tal como
                       lo devolvió frontier:query y sin tipearlo de nuevo.
    --section          NOMBRE LINEA, repetible. NOMBRE es una de las seis secciones de
                       la constante SECCIONES y LINEA es una línea física de su cuerpo.
                       Las seis son obligatorias y ninguna puede quedar sin líneas.
    --gist             la línea que el mapa va a mostrar de esta decisión, con tope de
                       120 caracteres, validada por la misma función que aplica el tope
                       al --append-decision de map:write.
    --new-ticket       TITULO CUERPO LABELS, repetible. La misma forma exacta que el
                       --ticket de ticket:create.
    --block            BLOQUEANTE BLOQUEADO, repetible. Cada lado es el TÍTULO de un
                       --new-ticket de esta misma invocación, nunca un id: los ids no
                       existen hasta que la primera escritura vuelve.
    --append-fog       una viñeta de niebla nueva, con su título en negrita.
    --remove-fog       el título de una viñeta que esta resolución graduó. Tiene que
                       estar nombrado en alguna línea de --section "Niebla graduada".
    --expect-sections  el JSON de huellas que map:read emitió, para el aviso de deriva.
    --defer-map        booleano. Difiere la quinta escritura a otro conductor: las
                       cuatro primeras corren igual, la quinta no se manda, y la línea
                       que le tocaba sale por stdout en mapLine y mapArgs. Con el flag
                       puesto, --expect-sections queda sin uso y no avisa nada, porque
                       su único consumidor vive adentro de la escritura que no ocurre.

No hay `--append-decision`, y su ausencia es la decisión: el enlace de la línea del
mapa sale de `issue.url`, que la escritura 4 devuelve en su propio round trip. Así es
imposible que la línea del mapa apunte a un ticket distinto del que se acaba de cerrar,
y el modelo nunca tipea una URL.

El cuerpo del comentario cruza la CLI como líneas y nunca como markdown. El adapter lo
arma: `## <Nombre>`, línea en blanco, las líneas de esa sección unidas por salto, y una
línea en blanco entre secciones. El orden adentro de una sección es el de la línea de
comandos; el orden entre secciones lo pone `SECCIONES` y jamás el argv.

Las cinco escrituras van adentro de una sola invocación y en este orden, que el adapter
garantiza y ninguna combinación de flags reordena:

| Nº | Mutation | Cuándo |
| --- | --- | --- |
| 1 | `issueBatchCreate` | solo si hay al menos un `--new-ticket` |
| 2 | `issueRelationCreate` | solo si hay al menos un `--block` |
| 3 | `commentCreate` | siempre |
| 4 | `issueUpdate` | siempre, con `stateId` en el `done` del ctx |
| 5 | `projectUpdate` | siempre salvo con `--defer-map`, precedida de su relectura del overview |

Las dos primeras son condicionales porque un batch vacío es un round trip desperdiciado
y Linear puede rechazarlo. El comentario va antes que el estado porque una sesión que
muere entre los dos deja el ticket abierto con la respuesta ya escrita, mientras que el
orden inverso deja un ticket en Done sin respuesta, que es un agujero que nadie ve. El
mapa va último porque es el único recurso compartido entre corridas.

Ninguna de las cinco reintenta, y la quinta llama a `_intentar_escribir` una sola vez y
sin bucle propio. `_post` traga la falla de transporte, así que ninguna rama puede
distinguir "no llegó" de "llegó y se perdió la respuesta", y las tres primeras crean
recursos que nada en el plugin sabe deshacer.

Todo abort sale con `SIN_KEY`, que es 3, y ninguno acuña un código nuevo. Lo que
distingue a cada uno es qué dice que aterrizó y cómo terminar a mano:

| Falla en | Qué quedó escrito | Remediación que imprime |
| --- | --- | --- |
| antes de la red | nada | corregir la invocación; el transporte no se llamó ni una vez |
| 1, `issueBatchCreate` | nada | volver a correr la misma invocación entera |
| 2, `issueRelationCreate` | los tickets nuevos, y cuántos bloqueos entraron | `ticket:block` con los pares que faltan, y después esta misma invocación sin `--new-ticket` ni `--block` |
| 3, `commentCreate` | los tickets y su cableado | esta misma invocación sin `--new-ticket` ni `--block` |
| 4, `issueUpdate` | los tickets, el cableado y **el comentario**; el estado en sí queda incierto, porque un timeout no distingue que el `issueUpdate` no haya llegado de que haya llegado y se perdió la respuesta | fijarse en Linear si el ticket ya cambió de estado antes de tocarlo a mano, y después correr `map:write`: repetir la invocación duplicaría el comentario. Nombra además los `--remove-fog`/`--append-fog` pendientes, para que la niebla ya validada contra el comentario no se pierda en silencio |
| 5, `projectUpdate` | todo menos la línea del mapa | **la invocación exacta de `map:write` que falta**, impresa con su `--project`, la url real, el gist y los `--remove-fog` que correspondan |

La fila 4 no tiene la misma suerte que la 5: en el punto de la falla, la url que
`--append-decision` necesita la devolvería el mismo `issueUpdate` que acaba de fallar,
así que su remediación no puede imprimir la invocación completa. `ticket:rule-out` no
carga esa restricción: `--append-out-of-scope` lleva la viñeta que ya está en el plan y
no depende de ninguna url, así que ahí la fila 4 sí imprime la invocación entera, igual
que la 5.

La última fila es la mejor remediación del archivo y es gratis: en ese punto el adapter
ya tiene el project, la url que le devolvió el `issueUpdate` y el gist. Es también la
razón por la que la quinta no reintenta. El mensaje nunca sugiere repetir
`ticket:resolve`, que recrearía los tickets nuevos y volvería a postear el comentario.

stdout, una sola línea de JSON compacto, con nueve claves siempre presentes: `issue`,
`url`, `comment` con el enlace del comentario recién escrito, `tickets` con los que se
crearon, `blocks` con los pares que quedaron cableados, `mapWritten`, `mapLine`,
`mapArgs` y `noop` con los títulos de `--remove-fog` que no matchearon ninguna viñeta.

`mapWritten` dice si la quinta escritura ocurrió de verdad en esa corrida: `true` sin el
flag, `false` con él. `mapLine` es la línea completa del mapa, con su marcador, la misma
que se habría escrito; es lo que se le muestra a una persona antes de escribir. `mapArgs`
es esa misma línea como lista de tokens de argv, lista para concatenar adentro de una
única invocación de `map:write`: lleva el `--append-decision` con su enlace y su gist,
después un `--remove-fog` por título graduado, y después un `--append-fog` por viñeta
nueva, ya sin marcador. Es lo que se ejecuta, y hacen falta las dos porque no existe
ningún flag de `map:write` que reciba una línea ya renderizada.

**Cada token de `mapArgs` llega crudo: el adapter no lo entrecomilla.** Un gist o una
viñeta de niebla los escribió una persona o un modelo, y pueden traer cualquier
carácter, incluidos los que una shell interpreta (`;`, `|`, comillas, backticks). Quien
concatena los tokens en una línea de shell tiene que entrecomillar cada uno antes de
pegarlo, sin excepción y aunque el token sea el nombre de un flag: envolverlo en
comillas simples y, si ya trae una comilla simple adentro, cerrar la comilla, escribir
`'\''` y volver a abrirla.

Las dos vienen siempre, con el flag y sin él, y con el mismo valor: la línea se calcula
una sola vez, antes de la bifurcación, así que lo que se imprime y lo que se escribe no
son dos construcciones que puedan divergir sino una con dos destinos. Ni `--project` ni
`--expect-sections` viajan en `mapArgs`: son del conductor que escribe el mapa, que ya
los tiene de primera mano.

### `ticket:rule-out`

La misma superficie que `ticket:resolve` salvo una fila, y esa fila es la operación:

    --out-of-scope   la viñeta entera de Fuera de alcance, con su título en negrita,
                     validada por _validar_vineta, la misma que valida las viñetas de
                     niebla de map:write. Requerida.

**No acepta `--gist`, y la asimetría es el punto.** El flag no está declarado, así que
pasarlo no es un argumento ignorado sino un error de invocación de `argparse`, con
código 2. La línea de esta operación va a `## Fuera de alcance` y nunca a
`## Decisiones hasta ahora`, y la recíproca es igual de fuerte: `ticket:resolve` no
acepta `--append-out-of-scope`.

Los otros diez flags son los mismos, `--new-ticket`, `--block` y `--defer-map`
incluidos. Sus dos
primeras escrituras casi siempre están vacías, pero casi siempre no es siempre, y darle
la misma forma cuesta cero: sacar un ticket de alcance puede abrir preguntas nuevas.

Las cinco escrituras van en el mismo orden y con las mismas condiciones que las de
`ticket:resolve`, y las seis fallas dicen lo mismo con tres diferencias: la escritura 4
manda el `canceled` del ctx en vez del `done`; la remediación de la escritura 4, a
diferencia de la de `ticket:resolve`, sí imprime la invocación entera de `map:write`,
porque `--append-out-of-scope` no depende de ninguna url; y la remediación de la
escritura 5 imprime un `map:write --append-out-of-scope` en vez de un
`--append-decision`.

Es la **única operación destructiva del adapter**: cierra un ticket sin resolverlo. El
comentario se escribe igual, con sus seis secciones, así que la decisión de sacarlo de
alcance queda auditable en el ticket aunque el ticket quede cancelado.

stdout, la misma forma que `ticket:resolve`, con las mismas nueve claves. Con
`--defer-map`, `mapLine` es la viñeta entera con su marcador y `mapArgs` empieza con
`--append-out-of-scope`: la línea de esta operación va a `## Fuera de alcance` también
cuando el mapa lo escribe otro conductor.

## La salida de las operaciones que escriben sobre el colapso

### `milestone:create`

Una sola línea de JSON compacto, con la misma regla de separadores y de escapado a
ASCII que las demás. Tres claves de primer nivel, las tres siempre presentes:

    id         string. El id que devolvió la mutation.
    name       string. El nombre que devolvió la mutation, igual al que se pasó.
    sortOrder  number. El sortOrder que devolvió la mutation, y NUNCA el que se pidió:
               es la regla de las anclas. Con `--sort-order` en cero la mutation
               falla del lado del adapter antes de tocar la red, así que el valor que
               vuelve siempre coincide con el pedido salvo por redondeo del lado de
               la API.

El write es un solo `projectMilestoneCreate`, sin `targetDate` en ninguna rama: es lo
que sostiene la afirmación 13. `status` no se pide de vuelta: es derivado, tiene lag,
y quien lo necesita lo lee por `frontier:query` antes de escribir, nunca después.

No reintenta: `_post` traga la falla de transporte y no distingue "no llegó" de
"llegó y se perdió la respuesta", y el plugin no tiene ninguna operación para borrar
un milestone.

### `work:write`

Una sola línea de JSON compacto, con la misma regla de separadores y de escapado a
ASCII que las demás. Tres claves de primer nivel, las tres siempre presentes:

    issues      lista de objeto. Las issues de ejecución que se crearon en esta
                corrida, vacía cuando la invocación no traía ningún `--issue`. Cada
                una lleva cuatro claves, las cuatro siempre presentes: identifier, id,
                title y url, la misma forma que `tickets` de `ticket:resolve`.
    related     lista de objeto. Las relaciones `related` que confirmaron, en el
                orden en que entraron, vacía cuando la invocación no traía ningún
                `--relate`. Cada una lleva dos claves: decision, el ticket de decisión,
                e issue, el id de la issue de ejecución del otro lado, ya resuelto
                (sea que `--relate` lo haya nombrado por índice o por id existente).
    noLanding   string o null. El identificador que recibió el label
                `map:no-landing`, y null en los otros dos desenlaces.

Las tres siempre presentes y nunca omitidas: los tres desenlaces tienen la misma forma
y se distinguen por el contenido.

Las tres escrituras van adentro de una sola invocación y en este orden, que el adapter
garantiza y ninguna combinación de flags reordena:

| Nº | Mutation | Cuándo |
| --- | --- | --- |
| 1 | `issueBatchCreate` | solo si hay al menos un `--issue` |
| 2 | `issueRelationCreate` con `type: related` | solo si hay al menos un `--relate` |
| 3 | `issueAddLabel` | solo con `--no-landing` |

Las dos primeras son condicionales por la misma razón que en `ticket:resolve`: la API
rechaza un `issueBatchCreate` con la lista vacía. Las relaciones van después de las
issues porque necesitan los ids que devuelve la primera escritura; el label va último
porque es el único desenlace que convive con cero de las otras dos.

Las issues de ejecución que crea no llevan `estimate` ni ningún `labelIds`: no son
tickets de decisión, así que no llevan el label `map`, y `frontier:query` sigue
funcionando igual después de que aterrizan. Toda `issueRelationCreate` que emite pone
el ticket de decisión del lado `issueId`, al revés que `ticket:block`, para que la
relación caiga en `relations` y no en `inverseRelations`.

No reintenta ninguna de las tres. `_post` traga la falla de transporte, así que
ninguna rama puede distinguir "no llegó" de "llegó y se perdió la respuesta", y
repetir la invocación entera solo es seguro cuando nada quedó escrito: con parte de la
secuencia ya confirmada, la remediación que cada falla imprime dice exactamente qué
repetir y qué no.

### map:write bajo el colapso

`map:write` escribe bajo `## El colapso` con `--append-collapse VINETA`. El flag es
repetible y lleva un solo valor por ocurrencia, así que la pasada entera entra en una
sola invocación: el colapso escribe todos sus cortes juntos, y el aterrizaje escribe
uno. Solo `map:write` lo declara; `ticket:resolve` y `ticket:rule-out` no lo tienen.

La línea que agrega es una viñeta con título en negrita:

    **<nombre del corte>.** <una frase que dice qué demuestra ese corte>

Sin enlace, porque un milestone no expone `url`: los cortes van por nombre. El adapter
no compone texto propio. Valida el valor con las mismas cinco reglas de forma que
`--append-fog` y `--append-out-of-scope` y lo renderiza con el mismo marcador, así que
las tres secciones de viñetas escriben la misma clase de línea.

El título en negrita es la clave de unicidad. Un corte cuyo nombre ya está en la
sección aborta la invocación, y en el segundo intento de un `map:write` que ya escribió
esa línea la repetición pasa a no-op con reporte y no duplica nada.

La sección sale de la lista de encabezados por posición, la sexta, y el adapter nunca
reescribe su texto. Un overview sin el encabezado `## El colapso` aborta sin escribir y
sin agregar la línea al final del documento. `--expect-sections` cubre la sección igual
que las otras cinco y sigue siendo opcional: la deriva de su huella se avisa por
stderr y nunca aborta. El envelope de stdout no cambia: `written`, `attempts` y `noop`.
