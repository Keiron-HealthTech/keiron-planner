---
lang: es
---

# keiron-planner

Plugin de Claude Code para planificar proyectos grandes del equipo CRM sobre
Linear. Sirve cuando todavía no se ve el camino a la solución: en vez de
planificar de una pasada, traza un mapa de decisiones sobre un Project, las
resuelve de a una y al final lo colapsa en milestones e issues de ejecución que
`/sdd-new` puede tomar.

## Instalación

El plugin vive en el marketplace de `spec-driven-dev`, que el equipo ya tiene
agregado. Desde Claude Code:

```
/plugin install keiron-planner@spec-driven-dev
```

Después, una vez por máquina:

```
/planner-setup
```

La key nunca pasa por la conversación. El script la pide sin mostrarla, y eso
necesita una terminal de verdad, que Claude Code no tiene. Por eso `/planner-setup`
no la pide: te da el comando exacto para pegar en una terminal aparte, algo como

```
sh '/Users/<usuario>/.claude/plugins/cache/spec-driven-dev/keiron-planner/<versión>/scripts/install.sh'
```

Ese comando pide tu Personal API key de Linear, la valida contra la API y la
guarda en `~/.config/keiron-planner/linear.key`. De vuelta en Claude Code,
`/planner-setup --verify` confirma que quedó bien, y `/planner-setup --remove` la
borra.

Necesita el `python3` del sistema. En un Mac sin Command Line Tools, el
instalador lo dice y pide correr `xcode-select --install`.

## Comandos

| Comando | Qué hace |
| --- | --- |
| `/map-new` | Traza el mapa sobre un Project y crea los primeros tickets. |
| `/map-work` | Resuelve un ticket de la frontera. |
| `/map-collapse` | Colapsa el mapa en milestones e issues de ejecución. |
| `/map-status` | Muestra el mapa y la frontera, sin escribir. |
| `/grill` | Grilla una idea o un plan, sin mapa de por medio. |
| `/planner-setup` | Instala o verifica la API key de Linear. |

El vocabulario del plugin está en [`CONTEXT.md`](CONTEXT.md).

## Checks

```
scripts/run-checks.sh
```

Cada afirmación que chequean está en [`scripts/CHECKS.md`](scripts/CHECKS.md).
