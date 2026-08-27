#!/usr/bin/env python3
"""
Ticket 08, Q5: cuanto suma traer el Document del mapa en la misma query que la
frontera. Solo lectura. Compara tres formas contra el mismo Project.

Uso: ./status_cost.py <PROJECT_ID_O_SLUG>
"""
import json, os, pathlib, sys, urllib.error, urllib.request

ENDPOINT = "https://api.linear.app/graphql"

ISSUES = """
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
"""

A = "query($id: String!, $label: String!) { project(id: $id) { name" + ISSUES + "} }"
B = ("query($id: String!, $label: String!) { project(id: $id) { name "
     "documents(first: 10) { pageInfo { hasNextPage } nodes { id title updatedAt } }" + ISSUES + "} }")
C = ("query($id: String!, $label: String!) { project(id: $id) { name "
     "documents(first: 10) { pageInfo { hasNextPage } nodes { id title content updatedAt } }" + ISSUES + "} }")


def api_key():
    k = os.environ.get("LINEAR_API_KEY")
    if k:
        return k.strip()
    p = pathlib.Path.home() / ".config" / "keiron-planner" / "linear.key"
    if p.exists():
        return p.read_text().strip()
    sys.exit("No hay API key.")


def gql(query, variables):
    req = urllib.request.Request(
        ENDPOINT,
        data=json.dumps({"query": query, "variables": variables}).encode(),
        headers={"Content-Type": "application/json", "Authorization": api_key()},
    )
    try:
        with urllib.request.urlopen(req) as r:
            payload, headers = json.load(r), dict(r.headers)
    except urllib.error.HTTPError as e:
        sys.exit(f"HTTP {e.code}: {e.read().decode()[:1500]}")
    if payload.get("errors"):
        sys.exit(json.dumps(payload["errors"], indent=2, ensure_ascii=False))
    cost = next((v for k, v in headers.items() if "complexity" in k.lower()), "?")
    return payload["data"], cost


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    pid, label = sys.argv[1], "map"
    for name, q in (("A  frontera sola", A),
                    ("B  + documents sin content", B),
                    ("C  + documents con content", C)):
        d, cost = gql(q, {"id": pid, "label": label})
        docs = d["project"].get("documents")
        extra = ""
        if docs is not None:
            extra = f"  docs={len(docs['nodes'])} truncado={docs['pageInfo']['hasNextPage']}"
        print(f"{name:32}  complejidad={cost}{extra}")


if __name__ == "__main__":
    main()
