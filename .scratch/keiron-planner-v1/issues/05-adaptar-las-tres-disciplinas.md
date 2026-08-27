# 05: Cómo se adaptan grilling, domain-modeling y prototype al vivir acá

**Tipo:** `map:grilling` · **Modo:** HITL (`hitl:dev`)
**Estado:** RESUELTO (2026-08-26)
**Bloqueado por:** nada.
**Tomado por:** ljana (sesion del 2026-08-26).

## Pregunta

Al decidir que la propiedad sigue a la necesidad, estas tres pasaron a vivir en
este plugin. Son de Matt y están en inglés, pensadas para un dev solo. ¿Qué
cambia al keironizarlas?

Preguntas que cuelgan de esta:

- Qué se traduce y qué se deja en inglés, aplicando la regla de idioma del
  glosario.
- Cuáles son model-invoked y cuáles user-invoked. Matt tiene grilling
  model-invoked con `grill-me` como puerta de entrada user-invoked.
- Qué le agrega la realidad multi-rol: grilling asume un humano, y en discovery
  hay PM, Diseño y dev leader.
- Cómo quedan escritas para que SDD las pueda importar después sin reescribirlas.
- Si domain-modeling escribe en `CONTEXT.md` del repo destino o en otro lado,
  dado que este plugin planifica trabajo que ocurre en otros repos.

## Hecho cuando

**Corrección al criterio original.** Lo había escrito como "las tres skills
existen en el repo", que es un entregable y no una decisión. Wayfinder pide
decisiones, no entregables: escribir las skills es ejecución y ocurre después
del colapso. El criterio correcto es que las cuatro preguntas estén resueltas,
y lo están.

## Resolución

### 1. El glosario del dominio vive en un repo central

El CRM es polyrepo: once repos activos, ninguno con `CONTEXT.md` ni `docs/adr/`,
y los proyectos cruzan repos por defecto. Los dos layouts de Matt, un
`CONTEXT.md` en la raíz o un `CONTEXT-MAP.md` dentro del mismo repo, no cubren
este caso.

El glosario canónico vive en **un repo central de dominio**, y cada repo del CRM
lo alcanza con un puntero de una línea en su `CLAUDE.md`. Los términos
compartidos (deal, flow, role, workspace, corporation, template) tienen una sola
definición; los términos propios de un repo se agregan en su sección.

Descartadas: uno por repo, porque el vocabulario compartido se duplicaría y
derivaría, y un glosario que deriva es peor que ninguno porque le miente al
agente con autoridad. Dentro de `keiron-planner`, porque acopla el glosario del
dominio a la herramienta que hoy lo mantiene. Un Document de Linear, porque no
se versiona ni pasa por PR.

**El plugin no crea ni puebla ese repo.** Siguiendo la regla de CRM-3308, si el
glosario no existe la skill procede en silencio y no sugiere crearlo. Poblarlo
es trabajo del equipo, no del plugin.

### 2. El multi-rol no entra en grilling: sale como ticket

Grilling se queda 1 a 1 y no aprende roles. Una pregunta que el interlocutor de
turno no puede contestar **se convierte en un ticket HITL** con su label
`hitl:pm` o `hitl:design`, y la ronda sigue sin ella.

Es el mismo mecanismo que la niebla que gradúa, con el eje corrido de cuándo a
quién. Grilling son 28 líneas y su valor está en ser chica: meterle un modelo de
roles adentro la hincha y complica la importación futura a SDD.

**Consecuencia que toca otros tickets**: grilling pasa a necesitar crear
tickets, así que deja de ser una skill pura de conversación y toca el adapter.
Anotado en el ticket 08.

### 3. Invocación

Las tres son model-invoked. Se llega a ellas desde `/map-new` y `/map-work`.

Una sola puerta user-invoked: **`/grill`**, porque grillear suelto sin mapa de
por medio es útil por sí solo y es la skill más usada del repo de Matt. Cuesta
siete líneas.

### 4. Idioma y forma

Las skills se escriben **en inglés**, con el frontmatter de SDD: `name`,
`description`, `license`, y `metadata` con `author`, `version`, `scope` y
`auto_invoke`. Lo que las skills escriben, o sea el mapa, los tickets y las
resoluciones, va en español neutro.

Traducir la prosa de las tres referencias es riesgo sin ganancia. Y con el
frontmatter alineado, el día que SDD las importe es copiar un archivo. Esto
también resuelve la quinta sub-pregunta del ticket.

### Atribución

Las tres vienen de mattpocock/skills, MIT, Copyright 2026 Matt Pocock. Cada
skill keironizada lleva su línea.
