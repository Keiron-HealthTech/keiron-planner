# 11: Qué hace `/map-new` sobre un Project que ya arrancó

**Tipo:** `map:grilling` · **Modo:** HITL (`hitl:dev`) · **RESUELTO** el 2026-08-28
**Bloqueado por:** nada.
**Tomado por:** Luis Felipe Jaña (`hitl:dev`), sesión del 2026-08-27.
**Origen:** graduado desde la niebla al resolver el [08](08-los-dos-modos-keironizados.md).

## Pregunta

El 03 decidió que `map:create` adopta el Project si le pasan uno, porque en el
CRM los Projects los suele abrir PM antes de que el dev leader se meta. El 08
decidió que `/map-new` crea siempre el DD, sin el corte de wayfinder. Los dos
juntos significan que `/map-new` va a correr sobre Projects vivos, con trabajo
adentro y decisiones ya tomadas que nadie escribió.

## Por qué graduó de la niebla

El parche decía "proyectos del CRM que ya arrancaron sin mapa: si se les puede
poner uno encima a mitad de camino, y qué pasa con lo ya decidido". Era difuso
porque no estaba claro que `/map-new` fuera a tocar un Project ajeno. Ahora lo
es, y el caso pasó de hipotético a ser el camino más probable en el CRM de hoy.

## Preguntas que cuelgan de esta

- Qué pasa con las issues de ejecución que ya viven en ese Project. Comparten
  Project con los tickets de decisión, y lo único que los separa es el label
  `map`. Si eso alcanza, o si hace falta algo más.
- Qué pasa con las decisiones ya tomadas y no escritas. Si el mapa nace con
  Decisiones hasta ahora vacío y miente, o si hay un paso de recuperación.
- Si el trabajo ya hecho recorta el destino, y quién lo dice.
- Si un mapa puesto a mitad de camino se distingue de uno trazado desde cero, o
  si no vale la pena distinguirlos.

## Hecho cuando

Está escrito qué hace `/map-new` cuando el Project que adopta ya tiene issues, y
resuelto qué pasa con las decisiones tomadas antes del mapa.

---

# Resolución

Dos rondas de grilling, once preguntas, frontera del árbol vacía. Las once se
confirmaron tal como venían recomendadas.
Deliverable: [`research/11-el-project-vivo.md`](../research/11-el-project-vivo.md).
Harness: [`research/11-scripts/live_project_probe.py`](../research/11-scripts/live_project_probe.py).

## La decisión

**El mapa se muda: es el overview del Project, `Project.content`, y no un Document
aparte.** Eso es lo que hace `/map-new` sobre un Project que ya arrancó, porque
después de la mudanza casi no hay nada que hacer: las decisiones ya estaban ahí.

Seis piezas:

1. **`map:create` escribe `Project.content` y no crea Document.** El mapa no tiene
   título propio; el nombre del Project es su nombre.
2. **Nunca reescribe prosa humana, y es absoluto.** Las secciones del mapa van
   arriba, y lo que ya estaba se preserva **verbatim** debajo, bajo un solo
   encabezado, **Antes del mapa**. No se mapea `Objetivo` a Destino ni nada
   parecido: mapear es mover, y mover es reescribir.
3. **Nunca se niega.** Cuando el Project ya tiene issues, muestra lo que encontró
   (issues, overview, Document si hay) y pide confirmación una vez. No hay umbral,
   porque el avance de los ocho Projects vivos va de 0.02 a 0.75 sin punto natural
   de corte.
4. **Las decisiones heredadas no entran al índice.** Viven en Antes del mapa, sin
   enlace y sin gist, porque no tienen ticket detrás. El invariante del índice
   queda intacto. Para promover una, se abre un ticket de decisión y se resuelve:
   el camino normal, cero mecanismo nuevo, y de paso la decisión hereda la
   conversación que nunca tuvo.
5. **El destino lo nombra la persona, siempre.** El agente no propone destino ni
   recorte: pone delante lo que encontró y la persona nombra con eso a la vista. Un
   agente que propone destino sobre un Project al 66% propone "terminar lo que
   falta", que es un plan y no un destino.
6. **Que un Project ya tenga mapa lo dicen las secciones del mapa**, que es la
   huella por encabezado que `map:read` ya devuelve. Ni marcador, ni label de
   Project.

Y dos cosas que se dejan como estaban: el label `Discovery` **sigue yendo en todo
ticket de decisión**, y un mapa puesto a mitad de camino se distingue con **una
línea en Notas** que dice qué adoptó y cuándo.

## Por qué

Porque el overview está en la portada del Project y por eso se mantiene, y un
Document está a un clic y por eso se muere. Eso no es una intuición sobre diseño de
producto, está medido en el workspace: los **ocho** Projects vivos del CRM tienen
overview no vacío, entre 990 y 7.414 caracteres, y **seis de los ocho se
actualizaron en los últimos siete días**. El único design doc que vive en un
Document, `Design Doc: Permissions V1 → V2 Overhaul`, 22.842 caracteres, fue creado
el 2026-02-20 y **nunca más actualizado**; todavía dice `Status: Draft`. Su Project
arrancó tres días después y hoy va en 0.66. El mismo Project mantiene su overview al
día.

Y porque los encabezados de esos overviews ya son el vocabulario del mapa:
`Decisiones tomadas`, `La decisión de arquitectura`, `Decisión de alcance`, `Fuera de
alcance`, `Estructura (4 milestones iterativos a producción)`. El patrón viene de
2025 y sigue en los Projects cerrados. **El mapa no inventa un artefacto: formaliza
uno que el equipo ya mantiene a mano.** Poner el mapa en un Document era pedirle al
equipo que abandone el lugar donde ya escribe para irse al lugar donde ya se le murió
un DD.

El costo se midió antes de proponerlo, y es más bajo de lo que parecía. El 04
sobrevive entero, porque su veredicto es sobre la forma del índice y no sobre la
casa. El 10 no dependía del Document más que en tres afirmaciones. Y el riesgo que
parecía serio, el del 13, no existe: es el mismo objeto.

## Lo que se cayó

**La premisa de este ticket.** Decía "decisiones ya tomadas que nadie escribió", y
sobre eso colgaba la mitad de sus preguntas. Medido, es al revés: están escritas,
están frescas, y están en el overview del Project más 20.144 a 55.945 caracteres de
cuerpos de issue. El ticket temía un mapa naciendo con el índice vacío y mintiendo.
El problema real era el opuesto, un mapa naciendo al lado de 7.414 caracteres de
decisiones vivas y ofreciéndose como reemplazo.

**Y con ella, una decisión de encuadre que doce tickets resueltos daban por firme**,
la de que el mapa es un Document colgado del Project. No la derribó un argumento sino
un conteo: 3 Documents en 32 Projects, contra 32 overviews.

**El riesgo que el 13 dejó abierto para cualquier otra casa: no existe.** `Project`
tiene `contentState`, el estado Yjs serializado, no está en `ProjectUpdateInput`, y
`projectUpdate(content:)` lo mueve en **5 de 5** escrituras. Y lo que lo cierra del
todo: `Project.documentContent` es de tipo `DocumentContent`, un tipo con
back-references a `document`, `project`, `issue`, `projectMilestone` e `initiative`,
y en las cinco escrituras se movió con hash idéntico a `Project.contentState`. El
overview de un Project y un Document **son la misma pieza**. Linear no los modela
parecido, los modela con el mismo objeto. Todo lo que midió el 13 se transfiere
verbatim, y el 04 con él.

**Una contradicción de `CONTEXT.md`, de paso.** La fila de Resolution decía que Lo
que se cayó es la **sexta** sección. El 04, que la creó, la puso **tercera**, y el 10
la escribió tercera. Corregida.

## Niebla graduada

Ninguna nueva. Pero **la niebla de `actor: app` perdió lo único medible que tenía**:
el 09 había anotado que `Document.updatedBy` existe y que con Personal API key no
distingue al plugin de la persona. **`Project` no tiene `updatedBy`.** Tiene
`creator`, `lead` y `members`, y ninguno dice quién tocó el contenido. El beneficio
concreto de escribir como app se queda sin gancho, y la niebla vuelve a ser solo la
pregunta por el disparador. Se anotó en el mapa.

Y **una niebla se encogió sin que nadie la tocara**: "un espejo del glosario en
Linear, para PM y Diseño". Con el mapa en la portada del Project, PM y Diseño lo ven
sin que nadie les avise. No la cierra, porque el glosario no es el mapa, pero le saca
la mitad que era de visibilidad.

## Tickets nuevos

Ninguno. Todo lo que la mudanza ponía en duda se midió en la misma sesión: el estado
Yjs, el round-trip de markdown, el techo de tamaño y `updatedBy`.

## Qué corrige o empuja

**Al 02**, la mitad de su alcance. Sus quince menciones al Document siguen siendo
ciertas sobre Documents, y el mapa ya no vive en uno. Lo que se transfiere está
medido: el round-trip de markdown es idéntico, y el tamaño sigue sin ser blocker con
techo entre 200.000 y 500.000 caracteres (`Argument Validation Error` a los 500.000).
Lo que no se transfiere son sus llamadas concretas.

**Al 09**, las llamadas y nada de la estrategia. Releer tarde y re-derivar sigue
siendo correcto y sigue siendo necesario, incluida la quinta fase del 13 que corre al
revés: el plugin puede destruir trabajo de una persona. Lo que cambia es
`document(id:)` por `project(id:)` y `documentUpdate` por `projectUpdate`. La ventana
de 332 ms hay que volver a medirla, aunque la escritura cuesta 3 de complejidad
contra el techo de 10.000. Y su nota sobre `Document.updatedBy` se retira: el campo
no existe en Project.

**Al 13**, el mecanismo se confirma y el objeto se amplía. Su conclusión no era sobre
Documents, era sobre `DocumentContent`, y resulta que el overview de un Project es
uno. Sus dos decisiones aguantan sin cambio: no se agrega verificación posterior a la
escritura, y `contentState` no entra al contrato.

**Al 10**, tres afirmaciones se reescriben y ninguna se retira ni se agrega. La **24**
y la **31** cambian `document(id:)` y `documentUpdate` por `project(id:)` y
`projectUpdate`. La **40** pierde la mitad de su cláusula: el `preflight` sigue sin
tener que consultar el Project, pero ya no hay Document que verificar que no aparezca.

**Al 06 y al 12, nada.** El colapso escribe milestones e issues de ejecución en el
Project, y eso no lo toca la casa del mapa. La duplicación al colapsar sobre un
Project que ya tiene issues sigue siendo del 12.

**A `frontier:query`, nada, y se revisó.** Las issues de ejecución que ya viven en el
Project no ensucian la frontera, y no hacía falta decidirlo: la query del 03 filtra
por label del lado del servidor, así que las 41 issues de Permissions son invisibles.
El tope de 50 se aplica ya filtrado, y el máximo medido de issues por Project es 41.

**Al `DD: <proyecto>` que el equipo ya usa como título de issue**, nada, y a propósito.
Hay seis en toda la historia, cuatro con el cuerpo vacío, ninguna dentro de un
Project, y dos anteriores al Project que describen. Emparejarlas por título es
coincidencia difusa para adoptar cáscaras vacías. El plugin las ignora.
