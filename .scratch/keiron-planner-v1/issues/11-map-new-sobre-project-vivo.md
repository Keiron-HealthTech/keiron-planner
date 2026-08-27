# 11: Qué hace `/map-new` sobre un Project que ya arrancó

**Tipo:** `map:grilling` · **Modo:** HITL (`hitl:dev`)
**Bloqueado por:** nada. Tomable ahora.
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
