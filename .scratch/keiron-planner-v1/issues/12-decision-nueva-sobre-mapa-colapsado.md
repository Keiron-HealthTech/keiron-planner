# 12: Qué hace el plugin cuando aparece una decisión nueva sobre un mapa ya colapsado

**Tipo:** `map:grilling` · **Modo:** HITL (`hitl:dev`)
**Bloqueado por:** nada. Tomable ahora.
**Origen:** graduado desde la niebla al resolver el [06](06-que-hace-map-collapse.md).

## Pregunta

El colapso es un evento único. Corre con la frontera vacía, escribe milestones e
issues de ejecución, y una segunda corrida se niega.

Pero durante la construcción aparece una pregunta que el mapa no vio. Alguien
crea el ticket de decisión, `/map-work` lo resuelve, y la decisión entra al índice
del mapa. No hay colapso que la lleve a ejecución.

Para la v1 esto ya tiene respuesta, y es "a mano": quien resuelve ese ticket crea
la issue de ejecución él mismo. La pregunta es qué hacemos cuando pase seguido.

Preguntas que cuelgan de esta:

- Si `/map-collapse` gana un modo incremental, o si es otro comando.
- Cómo se deduplica contra los milestones y las issues que ya existen, que es la
  mitad del costo de un modo incremental.
- En qué milestone cae una decisión posterior al colapso. Puede que en ninguno de
  los que existen, y entonces el colapso incremental también corta.
- Si el mapa se puede "descolapsar", o si un mapa colapsado que se reabre mucho es
  la señal de que el destino estaba mal trazado y lo que hace falta es un mapa
  nuevo.

## Hecho cuando

Está decidido si existe el colapso incremental, y si existe, cuál es su
precondición y cómo deduplica.
