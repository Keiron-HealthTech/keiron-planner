#!/usr/bin/env python3
"""
Harness del ticket 11: que hace /map-new sobre un Project que ya arranco.

El 03 decidio que `map:create` adopta el Project si le pasan uno. El 08 decidio
que `/map-new` crea siempre el DD. Juntos: /map-new va a correr sobre Projects
vivos. Lo que falta medir es COMO son de vivos los Projects del CRM hoy, y que
rastro dejan las decisiones que ya se tomaron sin escribirse.

Solo lee. No muta nada.

La API key sale de $LINEAR_API_KEY o de ~/.config/keiron-planner/linear.key.

Subcomandos:
  projects    Inventario de Projects del team CRM: issues por estado, docs
              colgados, fechas. Es la distribucion de "ya arranco".
  docs        Todos los Documents del workspace, con su Project y su titulo.
              Mide si la convencion `DD: <proyecto>` ya existe en la practica
              y si un Project aguanta mas de un Document.
  discovery   Las issues con label Discovery en Projects vivos. Son el rastro
              mas probable de una decision ya tomada y no escrita.
  labels      Que labels existen hoy en el workspace, para ver con que
              convive el label `map`.
"""
import json, os, sys, urllib.request, pathlib

API = "https://api.linear.app/graphql"

def key():
    k = os.environ.get("LINEAR_API_KEY")
    if k: return k.strip()
    p = pathlib.Path.home() / ".config/keiron-planner/linear.key"
    return p.read_text().strip()

def gql(query, variables=None):
    body = json.dumps({"query": query, "variables": variables or {}}).encode()
    req = urllib.request.Request(API, data=body, headers={
        "Content-Type": "application/json", "Authorization": key()})
    with urllib.request.urlopen(req) as r:
        cost = r.headers.get("X-Complexity")
        out = json.loads(r.read())
    if "errors" in out:
        print(json.dumps(out["errors"], indent=2)); sys.exit(1)
    return out["data"], cost

def projects():
    q = """
    query {
      teams(first: 10) { nodes { id key name
        projects(first: 50) { nodes {
          id name slugId createdAt startedAt state
          issues(first: 250) { nodes { identifier createdAt
            state { name type } labels { nodes { name } } assignee { displayName } } }
          documents(first: 20) { nodes { id title createdAt } }
        } } } }
    }"""
    data, cost = gql(q)
    print(f"complejidad: {cost}\n")
    for t in data["teams"]["nodes"]:
        print(f"=== TEAM {t['key']} · {t['name']} ===")
        ps = t["projects"]["nodes"]
        print(f"{len(ps)} projects\n")
        for p in sorted(ps, key=lambda x: -len(x["issues"]["nodes"])):
            iss = p["issues"]["nodes"]
            by_type = {}
            for i in iss:
                by_type[i["state"]["type"]] = by_type.get(i["state"]["type"], 0) + 1
            labs = {}
            for i in iss:
                for l in i["labels"]["nodes"]:
                    labs[l["name"]] = labs.get(l["name"], 0) + 1
            docs = p["documents"]["nodes"]
            print(f"  {p['name'][:58]:60s} state={p['state']:12s} issues={len(iss):3d}")
            print(f"      creado={p['createdAt'][:10]} arrancado={(p['startedAt'] or '-')[:10]}  por estado={by_type}")
            print(f"      docs={len(docs)}: {[d['title'][:40] for d in docs]}")
            if labs: print(f"      labels={dict(sorted(labs.items(), key=lambda x:-x[1])[:8])}")
            print()

def docs():
    q = """
    query { documents(first: 100) { nodes {
      id title createdAt updatedAt
      project { name } creator { displayName } } } }"""
    data, cost = gql(q)
    print(f"complejidad: {cost}\n")
    ds = data["documents"]["nodes"]
    print(f"{len(ds)} documents en el workspace\n")
    byproj = {}
    for d in ds:
        pn = d["project"]["name"] if d.get("project") else "(sin project)"
        byproj.setdefault(pn, []).append(d)
    for pn, group in sorted(byproj.items(), key=lambda x: -len(x[1])):
        print(f"  {pn[:55]:57s} {len(group)} doc(s)")
        for d in group:
            print(f"      · {d['title'][:60]:62s} {d['createdAt'][:10]} por {d['creator']['displayName'] if d.get('creator') else '?'}")
        print()

def discovery():
    q = """
    query { issues(first: 100, filter: { labels: { some: { name: { eq: "Discovery" } } } }) {
      nodes { identifier title createdAt state { name type }
        project { name } labels { nodes { name } } } } }"""
    data, cost = gql(q)
    print(f"complejidad: {cost}\n")
    ns = data["issues"]["nodes"]
    print(f"{len(ns)} issues con label Discovery\n")
    for i in ns:
        pn = i["project"]["name"] if i.get("project") else "(sin project)"
        print(f"  {i['identifier']:10s} {i['state']['type']:12s} {i['createdAt'][:10]}  {pn[:30]:32s} {i['title'][:60]}")

def labels():
    q = """query { issueLabels(first: 100) { nodes { name description } } }"""
    data, cost = gql(q)
    print(f"complejidad: {cost}\n")
    ns = data["issueLabels"]["nodes"]
    print(f"{len(ns)} labels\n")
    for l in sorted(ns, key=lambda x: x["name"]):
        print(f"  {l['name'][:34]:36s} {(l.get('description') or '')[:60]}")

if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "projects"
    {"projects": projects, "docs": docs, "discovery": discovery, "labels": labels}[cmd]()
