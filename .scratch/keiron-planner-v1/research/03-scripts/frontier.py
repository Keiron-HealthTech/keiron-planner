#!/usr/bin/env python3
"""
Harness del ticket 03: la consulta de frontera con el predicado corregido.

Corrige al ticket 01, que definia cerrado como state.type in (completed, canceled).
Contra el team CRM eso esta mal: el team tiene DOS estados de tipo canceled, y uno
de ellos es "Blocked", que es semanticamente lo mas abierto que hay.

Cerrado es exactamente los dos estados que el plugin escribe, resueltos a id por
el preflight.

Sin dependencias: solo stdlib. La key se busca en $LINEAR_API_KEY y en
~/.config/keiron-planner/linear.key.

Uso:
  ./frontier.py preflight <TEAM_KEY>
  ./frontier.py frontier <PROJECT_ID_O_SLUG> <LABEL> [TEAM_KEY]
"""
import json
import os
import pathlib
import sys
import urllib.error
import urllib.request

ENDPOINT = "https://api.linear.app/graphql"

LABELS = [
    "map", "map:research", "map:prototype", "map:grilling", "map:task",
    "hitl:pm", "hitl:design", "hitl:dev",
]

PREFLIGHT = """
query($team: String!, $labels: [String!]!) {
  viewer { id displayName }
  team(id: $team) {
    id key name
    states(first: 50) { nodes { id name type position } }
  }
  issueLabels(first: 250, filter: { name: { in: $labels } }) {
    nodes { id name team { id } }
  }
}
"""

FRONTIER = """
query($id: String!, $label: String!) {
  project(id: $id) {
    name
    issues(first: 50, filter: { labels: { some: { name: { eq: $label } } } }) {
      pageInfo { hasNextPage }
      nodes {
        identifier title createdAt
        state { id name type }
        assignee { displayName }
        labels { nodes { name } }
        relations(first: 10) {
          pageInfo { hasNextPage }
          nodes { type relatedIssue { identifier state { id } } }
        }
        inverseRelations(first: 10) {
          pageInfo { hasNextPage }
          nodes { type issue { identifier state { id } } }
        }
      }
    }
  }
}
"""


def api_key():
    k = os.environ.get("LINEAR_API_KEY")
    if k:
        return k.strip()
    p = pathlib.Path.home() / ".config" / "keiron-planner" / "linear.key"
    if p.exists():
        return p.read_text().strip()
    sys.exit("No hay API key. Corre install.sh del ticket 01.")


def gql(query, variables=None):
    req = urllib.request.Request(
        ENDPOINT,
        data=json.dumps({"query": query, "variables": variables or {}}).encode(),
        headers={"Content-Type": "application/json", "Authorization": api_key()},
    )
    try:
        with urllib.request.urlopen(req) as r:
            payload = json.load(r)
            headers = dict(r.headers)
    except urllib.error.HTTPError as e:
        sys.exit(f"HTTP {e.code}: {e.read().decode()[:2000]}")
    if payload.get("errors"):
        sys.exit(json.dumps(payload["errors"], indent=2, ensure_ascii=False))
    cost = [v for k, v in headers.items() if "complexity" in k.lower()]
    if cost:
        print(f"[complejidad: {cost[0]}]", file=sys.stderr)
    return payload["data"]


def preflight(team_key):
    """Resuelve viewer, los dos ids de estado y los ids de label. No guarda nada."""
    d = gql(PREFLIGHT, {"team": team_key, "labels": LABELS})
    states = d["team"]["states"]["nodes"]
    done = sorted([s for s in states if s["type"] == "completed"], key=lambda s: s["position"])
    canceled = sorted([s for s in states if s["type"] == "canceled"], key=lambda s: s["position"])
    if not done or not canceled:
        sys.exit(f"El team {team_key} no tiene estado completed o canceled. Sin fallback.")
    existing = {n["name"]: n["id"] for n in d["issueLabels"]["nodes"]}
    return {
        "viewer": d["viewer"],
        "team_id": d["team"]["id"],
        "resolved": done[0],
        "out_of_scope": canceled[0],
        "closed": {done[0]["id"], canceled[0]["id"]},
        "labels": existing,
        "missing_labels": [n for n in LABELS if n not in existing],
        # los estados que el test por tipo habria contado como cerrados y no lo son
        "trampas": [s for s in states
                    if s["type"] in ("completed", "canceled")
                    and s["id"] not in {done[0]["id"], canceled[0]["id"]}],
    }


def blockers(node):
    return [r["issue"] for r in node["inverseRelations"]["nodes"] if r["type"] == "blocks"]


def frontier(project, label, closed):
    conn = gql(FRONTIER, {"id": project, "label": label})["project"]["issues"]
    if conn["pageInfo"]["hasNextPage"]:
        print("!! TRUNCADO: el mapa tiene mas de 50 tickets", file=sys.stderr)
    nodes = sorted(conn["nodes"], key=lambda n: n["createdAt"])  # createdAt ascendente, en el cliente
    takeable, blocked, other = [], [], []
    for n in nodes:
        if n["relations"]["pageInfo"]["hasNextPage"] or n["inverseRelations"]["pageInfo"]["hasNextPage"]:
            print(f"!! TRUNCADO en las relaciones de {n['identifier']}", file=sys.stderr)
        if n["state"]["id"] in closed:
            other.append((n, f"cerrado ({n['state']['name']})"))
        elif n["assignee"]:
            other.append((n, f"tomado por {n['assignee']['displayName']}"))
        else:
            open_blockers = [b for b in blockers(n) if b["state"]["id"] not in closed]
            (blocked if open_blockers else takeable).append(
                (n, open_blockers) if open_blockers else n
            )
    return nodes, takeable, blocked, other


def main():
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    cmd = sys.argv[1]
    if cmd == "preflight":
        pre = preflight(sys.argv[2])
        print(f"viewer:            {pre['viewer']['displayName']}")
        print(f"resuelto:          {pre['resolved']['name']}")
        print(f"fuera de alcance:  {pre['out_of_scope']['name']}")
        print(f"labels que faltan: {pre['missing_labels'] or 'ninguno'}")
        if pre["trampas"]:
            print(f"TRAMPAS, cerrados por tipo pero abiertos de verdad: "
                  f"{[s['name'] for s in pre['trampas']]}")
        return
    if cmd == "frontier":
        project, label = sys.argv[2], sys.argv[3]
        team = sys.argv[4] if len(sys.argv) > 4 else "CRM"
        pre = preflight(team)
        nodes, takeable, blocked, other = frontier(project, label, pre["closed"])
        print("\nFRONTERA, tomables ahora:")
        for n in takeable:
            print(f"  {n['identifier']}  {n['title'][:60]}")
        print("\nBloqueados:")
        for n, ab in blocked:
            print(f"  {n['identifier']}  {n['title'][:44]} -> {[b['identifier'] for b in ab]}")
        print("\nFuera de la frontera por otra razon:")
        for n, why in other:
            print(f"  {n['identifier']}  {n['title'][:44]} -> {why}")
        open_tickets = [n for n in nodes if n["state"]["id"] not in pre["closed"]]
        print()
        if not open_tickets:
            print("=> mapa listo para colapsar")
        elif not takeable:
            print("=> MAPA TRABADO: hay tickets abiertos y la frontera esta vacia. Buscar un ciclo.")
        else:
            print(f"=> en curso: {len(takeable)} tomables, {len(open_tickets)} abiertos")
        return
    sys.exit(__doc__)


if __name__ == "__main__":
    main()
