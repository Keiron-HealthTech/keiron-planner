---
lang: es
---

# 11: cómo es de vivo un Project del CRM, medido

Hechos medidos contra el workspace `keiron` el 2026-08-27, antes de la primera
ronda de grilling del ticket 11. Personal API key, solo lectura salvo una sonda
de escritura contra el Project descartable del 04.

Harness: `11-scripts/live_project_probe.py`.

## 1. La distribución de "ya arrancó"

El team CRM tiene **32 Projects**, ocho en estado `started`. El avance de esos
ocho va de 0.02 a 0.75, o sea que no hay un punto natural donde cortar entre
"recién empezado" y "ya muy avanzado".

| Project | issues | sin empezar | en curso | listas | avance |
| --- | --- | --- | --- | --- | --- |
| Permissions V1 → V2 Overhaul | 41 | 8 | 4 | 20 | 0.66 |
| Eliminar EAV DealFields | 25 | 6 | 4 | 15 | 0.64 |
| Sidebar unificado | 23 | 17 | 6 | 0 | 0.07 |
| Plugin spec-driven-dev | 16 | 9 | 1 | 4 | 0.30 |
| IAton — Preview de negocio v2 | 15 | 2 | 8 | 4 | 0.43 |
| Editor de Plantillas WhatsApp | 14 | 13 | 1 | 0 | 0.02 |
| Amazon Connect — Multi-tenant | 13 | 5 | 0 | 7 | 0.58 |
| Onboarding Copilot — POC hackatón | 7 | 1 | 1 | 5 | 0.75 |

El volumen es chico: mediana de 15 issues, máximo 41. Ninguna paginación se
rompe con eso.

## 2. La premisa del ticket es falsa: las decisiones sí están escritas

El ticket decía "decisiones ya tomadas que nadie escribió". Medido, es al revés.
**Los ocho Projects vivos tienen `Project.content` no vacío**, entre 990 y 7.414
caracteres, y **seis de los ocho se actualizaron en los últimos siete días**.

Sus encabezados ya son el vocabulario del mapa:

| Project | encabezados de su overview |
| --- | --- |
| Sidebar unificado | Decisión de alcance · Hallazgos que definen el plan · **Fuera de alcance** · Track B |
| IAton — Preview v2 | Objetivo · Scope · **Decisiones tomadas** · Arquitectura · Riesgos |
| Eliminar EAV DealFields | Objetivo · El problema · **La decisión de arquitectura** · Plan por fases · Criterios de éxito |
| Editor de Plantillas | Objetivo · Scopes · **Estructura (4 milestones iterativos a producción)** · Fuera de alcance |
| Amazon Connect | Objetivo · Contexto · **Modelo de autenticación (decisión)** · Estructura (3 pasos iterativos) |
| Onboarding Copilot | Equipo · Alcance · Arquitectura · Precondiciones |

No es un patrón nuevo ni de estos ocho: los Projects `completed` de 2025 y 2026
tienen lo mismo, con nombres como "Decisiones Clave", "Decisión de arquitectura"
y "Fuera de alcance".

A eso se suma el cuerpo de las issues: entre 20.144 y 55.945 caracteres por
Project, y casi toda issue pasa los 500 caracteres.

**El mapa no inventa un artefacto. Formaliza uno que el equipo ya mantiene a
mano en el overview del Project.**

## 3. El Document es donde el DD se muere

Solo **3 de 32 Projects** tienen un Document colgado, y solo uno es un design
doc de verdad: `Design Doc: Permissions V1 → V2 Overhaul`, 22.842 caracteres,
443 líneas, escrito por `lleiva`.

Fue **creado el 2026-02-20 y nunca más actualizado**. Su Project arrancó el
2026-02-23 y hoy va en 0.66, seis meses después. Su encabezado sigue diciendo
`**Status:** Draft`.

El mismo Project mantiene su `Project.content` al día: última edición
2026-08-24.

O sea: en el único caso donde el equipo puso el DD en un Document y también tuvo
un overview, **el Document se congeló el día 2 y el overview siguió vivo**. Es
n=1, pero apunta en contra de la casa que el mapa eligió.

## 4. `Project.content` aguanta el markdown del mapa igual que un Document

Sonda de escritura: se mandó el `MAP.md` real (7.497 chars, 113 líneas, forma B)
a `projectUpdate(content:)` del Project descartable del 04, y se releyó.

- Vuelven **113 líneas de 113**. 7.497 a 7.532 caracteres.
- Las mismas cuatro transformaciones que midió el 04 contra un Document:
  `- ` pasa a `* ` (33 de 33 viñetas), `](url)` pasa a `](<url>)` (12 de 12
  enlaces), y el `**bold**` que cruza un corte de línea vuelve partido en cuatro
  asteriscos.
- La escritura cuesta **3 de complejidad**, contra 10.000 de techo.

`content` es escribible en `ProjectCreateInput` y en `ProjectUpdateInput`. Es el
mismo editor, con las mismas reglas: todo lo que midió el 04 se transfiere.


## 4b. El riesgo del 13 no existe: es el mismo objeto

Medido después de la ronda 1, para cerrar la condición que llevaba Q1.

`Project` tiene **`contentState`**, el estado Yjs serializado, igual que
`Document`: 44.912 bytes en el Project de sonda. **No** está en
`ProjectUpdateInput`, verificado por introspección, igual que el 13 verificó para
`DocumentUpdateInput`.

Cinco escrituras por `projectUpdate(content:)`, releyendo entre cada una:

| # | hash de `contentState` | bytes | ¿se movió? |
| --- | --- | --- | --- |
| 0 | `db75897c27e3` | 44.912 | base |
| 1 | `9c80cbf63804` | 45.256 | sí |
| 2 | `b79fceec6c45` | 45.372 | sí |
| 3 | `9a03248693f8` | 45.476 | sí |
| 4 | `ad6762e309ea` | 45.576 | sí |
| 5 | `263cc952b6a4` | 45.680 | sí |

**Cinco de cinco**, el mismo resultado que el 13 midió contra un Document.

Y el hecho que lo generaliza del todo: **el overview de un Project y un Document
son el mismo objeto**. `Project.documentContent` es de tipo `DocumentContent`, y
ese tipo tiene back-references a `document`, `project`, `issue`,
`projectMilestone` e `initiative`. En las cinco escrituras
`Project.documentContent.contentState` se movió con hash idéntico a
`Project.contentState`.

No es que el overview se comporte parecido a un Document. Es que Linear los
modela con la misma pieza. Todo lo que midió el 13 se transfiere verbatim, y la
condición que llevaba Q1 queda cerrada por mecanismo y no por analogía.

**Diferencia menor observada**: las cinco escrituras movieron `updatedAt` cada
una, a intervalos de 1,6 a 1,8 segundos, sin la coalescencia que el 09 midió
sobre Documents. No cambia nada, porque el 09 ya había prohibido ramificar sobre
`updatedAt`.

## 4c. Dos cosas que el cambio de casa sí rompe o sí acota

Medidas al cerrar, sobre lo que el 02 y el 09 daban por resuelto contra un Document.

**`Project` no tiene `updatedBy`.** `Document.updatedBy` existe; `Project.updatedBy`
no. Un Project tiene `creator`, `lead` y `members`, y ninguno dice quién tocó el
contenido la última vez. El 09 había anotado, como el primer beneficio concreto y
medible de escribir como app, que `Document.updatedBy` existe y con Personal API key
no distingue al plugin de la persona. Con el mapa en el overview ese beneficio **se
queda sin su gancho**: no hay campo que distinguir. La niebla de `actor: app` pierde
lo único medible que tenía.

**El tamaño sigue siendo irrelevante, y ahora tiene techo conocido.** Enviado a
`projectUpdate(content:)`:

| enviado | resultado |
| --- | --- |
| 50.000 chars | `success: true`, vuelven 48.521 |
| 200.000 chars | `success: true`, vuelven 194.021 |
| 500.000 chars | `Argument Validation Error`, código `INVALID_INPUT` |

El 3% que falta en los dos primeros no es truncado sino el espacio final de cada
línea que el editor limpia, consistente con las transformaciones de la sección 4.
El techo está entre 200.000 y 500.000 caracteres, y el mapa en forma B pesa 7.497.
La conclusión del 02, que el tamaño no es un blocker, se transfiere.

## 5. El equipo ya usa `DD: <proyecto>`, y es un título de issue

Seis issues llevan el label `Discovery` en toda la historia del workspace:

| Issue | título | cuerpo | Project |
| --- | --- | --- | --- |
| CRM-3010 | `DD: Mejoras Whatsapp Usuario` | 0 chars | ninguno |
| CRM-2956 | `DD: Campañas` | 0 chars | ninguno |
| CRM-2955 | `DD: Anclar Notas` | 204 chars | ninguno |
| CRM-2888 | `DISCOVERY: Amazon Connect` | 0 chars | ninguno |
| CRM-2616 | `Design Doc: Optimizar permisos al cargar tablero` | 332 chars | ninguno |
| CRM-2501 | `[CRM] Discovery Técnico - Mejoras Tableros` | 556 chars | ninguno |

Tres cosas: el título `DD: <proyecto>` que el mapa quiere para su Document **ya
existe como título de issue**; esas issues son **cáscaras vacías**, cuatro de
seis sin una sola línea de cuerpo; y **ninguna vive dentro de un Project**.

Además, dos de ellas son anteriores al Project que describen: `DD: Anclar Notas`
es del 2026-05-04 y su Project del 2026-05-12; `DISCOVERY: Amazon Connect` es del
2026-04-06 y su Project del 2026-07-17. El discovery del CRM **empieza antes de
que exista el Project**.

## 6. El label `Discovery` significa otra cosa de la que el plugin le va a dar

Hoy `Discovery` marca **una issue por proyecto**, la cáscara del DD. Seis usos en
toda la historia. `CONTEXT.md` dice que el plugin lo escribe en **todo ticket de
decisión**, que son del orden de quince por mapa. Un solo mapa multiplicaría por
tres el uso histórico del label y le cambiaría el significado a quien ya lo filtra.

## 7. Las issues de ejecución que ya viven en el Project no ensucian la frontera

Queda resuelto por construcción y no hace falta decidir nada. La query del 03
filtra por label del lado del servidor:

```graphql
issues(first: 50, filter: { labels: { some: { name: { eq: $label } } } })
```

Con `$label = "map"`, las 41 issues de Permissions son invisibles para
`frontier:query`. El tope de 50 se aplica ya filtrado, y el máximo medido de
issues por Project es 41 en total.

Lo que **no** queda cubierto es el lado de la escritura: cuando el colapso corre
sobre un Project que ya tiene issues, `issue:create` puede duplicar trabajo que ya
existe. Eso es territorio del ticket 12.

## Labels del workspace, para saber con qué convive `map`

`Bug`, `Chore`, `Discovery`, `EAV: Track A`, `EAV: Track B`, `Feature`,
`Improvement`, `Integration`, `Migrated`, `QA`, `UCC Premium`, `zz-sandbox-map`.

Los ocho labels del plugin todavía no existen. En las issues de los Projects
vivos solo se usan `Feature` (47), `Improvement` (14), `Bug` (6), `Chore` (2),
`QA` (1) y los dos de track del EAV.
