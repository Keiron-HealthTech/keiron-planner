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
| `ticket:create` | Un issue del Project cuyo cuerpo es la pregunta y nada más. |
| `ticket:block` | La relación nativa de bloqueo, en una segunda pasada. |
| `frontier:query` | Los tickets abiertos, sin bloqueantes abiertos y sin assignee. |
| `ticket:claim` | Tomar. El primer write de la sesión. |
| `ticket:resolve` | Las cinco escrituras de una resolución, en una sola invocación. |
| `ticket:rule-out` | Cierra un ticket sin resolverlo. La única destructiva. |
| `milestone:create` | Un corte demoable del colapso. Nunca lleva fecha. |
| `work:write` | Lo que produce un colapso o un aterrizaje, en una sola invocación. |
