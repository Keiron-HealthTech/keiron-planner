# 02: Qué permite y qué limita la API de Documents de Linear

**Tipo:** `map:research` · **Modo:** AFK
**Estado:** RESUELTO (2026-08-26)
**Bloqueado por:** nada. Tomable ahora.

## Pregunta

El mapa vive como un Document de Linear titulado `DD: <proyecto>` y se reescribe
en cada sesión, porque Decisiones hasta ahora crece y la niebla se vacía. ¿La
API de Documents aguanta ese uso?

## Qué hay que averiguar, contra fuentes primarias

- Si hay límite de tamaño en el contenido de un Document, y cuál.
- Si se puede editar por parches (el MCP expone `patch` en `save_issue`; hay que
  confirmar si `save_document` lo expone también) o si toda edición reescribe el
  documento entero.
- Si un Document soporta enlaces a issues que se rendericen como referencias
  vivas en la UI, que es lo que hace legible el índice de decisiones.
- Límites de rate relevantes para una sesión que escribe varias veces.

## Hecho cuando

Existe un markdown citado en el repo, con cada afirmación apuntando a la fuente
primaria que la sostiene, y una conclusión de una línea sobre si el Document
sirve como casa del mapa o hay que buscar otra.


## Resolución

Reporte completo con fuentes: [`research/02-api-documents-linear.md`](../research/02-api-documents-linear.md)

**El Document sirve como casa del mapa. No hay blocker.**

- **Tamaño**: no hay límite declarado en el schema. El único techo verificado es
  de transporte, 10 MiB por request HTTP, tres órdenes de magnitud por encima de
  lo que pesa un mapa.
- **Parches**: la API GraphQL solo acepta el contenido entero. `documentUpdate`
  no tiene ningún campo `patch` y el schema tampoco, en 51k líneas de SDL. El
  MCP sí expone `patch` con las seis operaciones, pero es azúcar que hace
  read-modify-write por debajo. Conviene usarlo igual: ahorra tokens y acota el
  daño de un error del modelo.
- **Rate limits**: irrelevantes. Un `documentUpdate` cuesta unos 3 puntos de
  complejidad contra un presupuesto de 2.500 requests por hora. Con una
  advertencia: la doc oficial se contradice a sí misma y los headers reales no
  coinciden con lo documentado, así que el límite se lee en runtime.
- **Enlaces vivos**: verificado en negativo. Un `CRM-123` pelado vuelve como
  texto plano, no como chip. La mención viva se serializa como
  `<issue id="..." href="...">CRM-123</issue>`. **Resuelto por el ticket 01 el
  2026-08-26: la API no la parsea.** Escrita con `href`, el pipeline de markdown
  autolinkea la URL adentro del valor del atributo y lo corrompe; sin `href`
  tampoco. El índice de decisiones usa link markdown común.

**Corrección al hallazgo de rate limits de este ticket.** Dije que eran
irrelevantes. Es cierto para el presupuesto por hora y **falso para el límite por
query**, que existe y es de 10.000 de complejidad. No lo vi porque una lectura sin
autenticar no lo pega: hay que mandar una query cara y que la API la rechace. El
ticket 01 lo midió y eso fija el tamaño de página de la consulta de frontera.

**El riesgo real no era ninguno de los que anticipé.** No hay control de
concurrencia: `DocumentUpdateInput` no tiene versión, etag ni `expectedUpdatedAt`,
y los Documents son colaborativos en tiempo real sobre Yjs. Gana el último que
escribe. Eso graduó a ticket propio, el 09.

**Nota de segundo orden que afecta el uso de `patch`**: el markdown es una
representación derivada del Yjs canónico, así que el round-trip no es
byte-idéntico. Se observaron tildes escapadas y URLs envueltas. Las anclas de
`patch` se toman de lo que devuelve la API, nunca de lo que el plugin creyó
escribir.
