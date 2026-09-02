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
El **9** es el de los stubs, los once subcomandos que todavía no tienen cuerpo. El
**2** lo emite `argparse`, y cubre tres casos: falta el subcomando, falta un argumento
requerido, o el subcomando no existe. El **1** queda reservado para lo que el script no
pudo decidir.
