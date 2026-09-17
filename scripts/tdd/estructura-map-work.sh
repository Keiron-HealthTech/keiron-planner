#!/usr/bin/env bash
# Andamio de TDD, no un check del set: vive fuera del glob scripts/check-*
# a proposito, y por eso run-checks.sh no lo corre. El contrato estructural
# de commands/map-work.md y skills/map-work/SKILL.md, escrito en rojo antes
# de que los dos archivos existieran. Se corre con scripts/tdd/correr.sh.
cd "$(dirname "$0")/../.."
fallas=0
n() { echo "FAIL - $1"; fallas=$((fallas + 1)); }

COMANDO=commands/map-work.md
SKILL=skills/map-work/SKILL.md

[ -f "$COMANDO" ] || n "no existe $COMANDO"
[ -f "$SKILL" ] || n "no existe $SKILL"
if [ "$fallas" -gt 0 ]; then echo "fallas=$fallas"; exit 1; fi

fm() { awk 'NR==1 && $0 != "---" {exit} NR==1 {next} /^---$/ {exit} {print}' "$1"; }

# --- el comando ---
claves="$(fm "$COMANDO" | grep -oE '^[a-z-]+:' | tr -d ':' | sort | tr '\n' ' ')"
[ "$claves" = "argument-hint description lang " ] || n "el frontmatter de $COMANDO declara '$claves' y tiene que declarar exactamente argument-hint, description y lang"
fm "$COMANDO" | grep -qE '^lang: en$' || n "$COMANDO no declara lang: en"
[ "$(grep -c '^ROUTE: skills/map-work/SKILL.md$' "$COMANDO")" = "1" ] || n "$COMANDO no declara exactamente un ROUTE: a skills/map-work/SKILL.md"
grep -q -- "--bootstrap" "$COMANDO" && n "$COMANDO nombra --bootstrap y la afirmación 39a lo prohíbe"
[ "$(grep -c '`next_recommended: ' "$COMANDO")" = "0" ] || n "$COMANDO cita un token, y los tokens viven en la skill"
grep -qF 'status: done' "$COMANDO" || n "$COMANDO no lleva la frase de la fila 55 sobre aterrizar en un corte con status: done"
grep -qE '^## Step ' "$COMANDO" && n "$COMANDO numera pasos y tiene que delegar sin restatearlos"

# --- la skill ---
for clave in name description license metadata lang; do
  fm "$SKILL" | grep -qE "^$clave:" || n "el frontmatter de $SKILL no declara $clave"
done
for sub in author version scope auto_invoke; do
  fm "$SKILL" | grep -qE "^  $sub:" || n "el metadata de $SKILL no declara $sub"
done
fm "$SKILL" | grep -qE '^lang: en$' || n "$SKILL no declara lang: en"
for puntero in "CONTRACT:" "TEMPLATES:" "ADAPTER:"; do
  grep -q "^$puntero" "$SKILL" || n "$SKILL no abre con el puntero $puntero"
done
for op in preflight "map:read" "frontier:query" "ticket:claim" "ticket:create" "ticket:block" "ticket:resolve" "ticket:rule-out"; do
  grep -qF "$op" "$SKILL" || n "el puntero ADAPTER de $SKILL no nombra $op"
done
for prohibida in "map:write" "map:create" "milestone:create" "work:write"; do
  grep -qF "$prohibida" "$SKILL" && n "$SKILL nombra $prohibida, que no es una de sus ocho operaciones"
done
for paso in 1 2 3 4 5 6; do
  grep -qE "^## Step $paso," "$SKILL" || n "$SKILL no lleva el paso $paso"
done
for paso in 7 8; do
  grep -qE "^## Step $paso," "$SKILL" && n "$SKILL lleva el paso $paso, que es de un corte posterior"
done
grep -q -- "--bootstrap" "$SKILL" && n "$SKILL nombra --bootstrap"
grep -qF "research-subagent.md" "$SKILL" && n "$SKILL nombra un archivo que no existe"
grep -qF "| Condition | Verdict | Token |" "$SKILL" && n "$SKILL repite la tabla del veredicto en vez de citarla"
for tok in map-new release-claim break-cycle map-collapse sdd-new; do
  grep -qF "\`next_recommended: $tok\`" "$SKILL" || n "$SKILL no cita el token $tok que sus pasos 2 y 3 emiten"
done
grep -qF '`next_recommended: map-work`' "$SKILL" && n "$SKILL se recomienda a sí misma"
grep -qF "ticket:claim --ctx" "$SKILL" || n "$SKILL no invoca ticket:claim en su paso 6"
grep -q -- "--release" "$SKILL" || n "$SKILL no nombra que el paso 6 va sin --release"

if [ "$fallas" -gt 0 ]; then echo "fallas=$fallas"; exit 1; fi
echo "OK - la estructura del comando y de la skill de /map-work"
