# keiron-planner

Plugin de Claude Code para planificar proyectos grandes del equipo CRM sobre
Linear. Cubre la etapa anterior a `spec-driven-dev`: cuando el camino a la
solución todavía no se ve y planificar de una pasada casa con una solución
demasiado temprano.

El plugin **todavía no existe**. Lo que hay es un mapa de decisiones, trazado
con el método que el propio plugin va a implementar.

## Retomar el trabajo

1. Leé `.scratch/keiron-planner-v1/MAP.md`. Es el mapa: destino, notas,
   decisiones tomadas, niebla y fuera de alcance. Leelo entero, es corto.
2. Elegí un ticket de la **frontera**: los de `.scratch/keiron-planner-v1/issues/`
   que no dicen `RESUELTO` y cuyo campo `Bloqueado por` dice "nada".
3. Tomalo: escribí `**Tomado por:**` en el ticket antes de trabajar.
4. Resolvelo, y **solo ese**. Nunca más de un ticket por sesión, con los de tipo
   `map:research` como única excepción.
5. Al cerrarlo: escribí la resolución en el ticket, marcalo `RESUELTO`, agregá
   una línea al índice de Decisiones del mapa, y graduá a ticket cualquier
   niebla que la resolución haya vuelto formulable.

Si el ticket es `map:grilling`, la sesión es una conversación con una persona.
El agente nunca contesta por ella.

## Vocabulario

`CONTEXT.md` es el glosario canónico y la fuente de verdad. Se actualiza en el
momento en que un término se resuelve, nunca al final. Ahí está también la regla
de idioma y la lista de términos que no usamos.

## Fuente primaria

`vendor/mattpocock-skills/` es el repo de Matt Pocock en el commit `6654f6b`,
MIT. El método del mapa sale de `skills/engineering/wayfinder/SKILL.md`. Las
tres disciplinas que este plugin adopta están en `skills/productivity/grilling/`,
`skills/engineering/domain-modeling/` y `skills/engineering/prototype/`.

## Contexto que vive fuera

- Ranking previo de las skills de Matt, con criterio distinto y alcance SDD:
  [documento en Linear](https://linear.app/keiron/document/ranking-skills-de-matt-pocock-para-el-plugin-spec-driven-dev-41ca969c664c)
- El plugin hermano: `../spec-driven-dev`. Construye lo que este planifica.
- Las decisiones de todas las sesiones están en engram, proyecto
  `keiron-planner`.
