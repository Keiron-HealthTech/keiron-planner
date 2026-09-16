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
| `ticket:claim` | Tomar. El primer write de la sesión. |
| `ticket:resolve` | Las cinco escrituras de una resolución, en una sola invocación. |
| `ticket:rule-out` | Cierra un ticket sin resolverlo. La única destructiva. |
| `milestone:create` | Un corte demoable del colapso. Nunca lleva fecha. |
| `work:write` | Lo que produce un colapso o un aterrizaje, en una sola invocación. |

## Los códigos de salida del preflight

| Código | Constante | Falla dura | Remediación | Marca |
| --- | --- | --- | --- | --- |
| 3 | `SIN_KEY` | No hay credencial en disco, está vacía, o Linear la rechazó. | Instalar o reinstalar la credencial corriendo `/planner-setup`. | `/planner-setup` |
| 4 | `SIN_TEAM` | El team que nombra `--team` no existe, o la credencial no lo ve. | Corregir la key del team que se le pasa a `--team`. | la key del team |
| 5 | `SIN_CERRADOS` | El team no tiene un estado `completed`, o no tiene uno `canceled`. | Revisar el workflow del team y dejarle los dos estados. | el workflow del team |
| 6 | `SIN_LABEL_MAP` | El label `map` no existe en el workspace. | Correr el preflight con `--bootstrap` la primera vez, cuando el label todavía no está. | `--bootstrap` |

Los cuatro códigos son distintos entre sí y ninguno es cero. La columna `Marca` es la
subcadena que el mensaje de esa falla emite por stderr, y se copia byte a byte: la
comparación es literal, va sin acentos para que no dependa de la codificación de la
salida, y las cuatro marcas tienen que ser distintas entre sí, porque una remediación
genérica pasaría las cuatro sin distinguirlas. Reformular una marca sin tocar el
mensaje, o al revés, deja el contrato y el script en desacuerdo.

Los otros tres códigos que el adapter puede devolver no son fallas duras del preflight.
El **9** es el de los stubs, los siete subcomandos que todavía no tienen cuerpo. El
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

Cinco claves de primer nivel, las cinco siempre presentes:

    found        bool. false cuando el Project no resolvió. Con found en false los tres
                 conteos son cero y las dos listas están vacías, que es la misma forma
                 que tiene un mapa ya terminado: found es lo único que los separa.
    truncated    lista de string. Subconjunto de issues, relations, inverseRelations y
                 projectMilestones, en ese orden fijo. Vacía si ninguna conexión vino
                 cortada. Cada nombre que aparece acá lleva además una línea a stderr, y
                 el código de salida sigue siendo 0 en todos los casos.
    counts       objeto de tres claves enteras, open, takeable y milestones. open cuenta
                 los tickets cuyo state.id no es ninguno de los dos ids cerrados del
                 ctx. takeable cuenta los que además pasan las otras dos condiciones.
                 Con issues cortada los dos son cotas inferiores. milestones cuenta los
                 nodos de projectMilestones que trajo la respuesta, y es cota inferior
                 cuando esa conexión vino cortada.
    tickets      lista de objeto. Los abiertos tomables, createdAt ascendente.
    notTakeable  lista de objeto. Los abiertos no tomables, createdAt ascendente.

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
