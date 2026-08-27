#!/usr/bin/env python3
"""
Harness del ticket 01: por donde lee el agente el grafo de dependencias de Linear.

Sin dependencias: solo stdlib. La API key se busca, en orden, en
$LINEAR_API_KEY y en ~/.config/keiron-planner/linear.key.

Subcomandos:
  whoami                       verifica la key y muestra el workspace
  teams                        lista teams (para elegir donde va el Project descartable)
  relations <IDENT> [IDENT..]  lee relations e inverseRelations crudas
  frontier <PROJECT_ID> [LABEL]  la consulta de frontera completa, un solo round-trip
                                 (LABEL por defecto: map)
  chip <PROJECT_ID> <IDENT>    escribe un Document con la sintaxis <issue .../> y lo relee
"""
import json
import os
import pathlib
import sys
import urllib.error
import urllib.request

ENDPOINT = "https://api.linear.app/graphql"


def api_key():
    k = os.environ.get("LINEAR_API_KEY")
    if k:
        return k.strip()
    p = pathlib.Path.home() / ".config" / "keiron-planner" / "linear.key"
    if p.exists():
        return p.read_text().strip()
    sys.exit(
        "No hay API key. Coloca la key en ~/.config/keiron-planner/linear.key "
        "o ejecuta install.sh."
    )


def gql(query, variables=None):
    body = json.dumps({"query": query, "variables": variables or {}}).encode()
    req = urllib.request.Request(
        ENDPOINT,
        data=body,
        headers={"Content-Type": "application/json", "Authorization": api_key()},
    )
    try:
        with urllib.request.urlopen(req) as r:
            payload = json.load(r)
            limits = {
                h: v
                for h, v in r.headers.items()
                if "ratelimit" in h.lower() or "complexity" in h.lower()
            }
    except urllib.error.HTTPError as e:
        sys.exit(f"HTTP {e.code}: {e.read().decode()[:2000]}")
    if payload.get("errors"):
        print("=== GraphQL errors ===", file=sys.stderr)
        print(json.dumps(payload["errors"], indent=2, ensure_ascii=False), file=sys.stderr)
    if limits:
        print(f"[headers de rate limit: {limits}]", file=sys.stderr)
    return payload.get("data")


def out(d):
    print(json.dumps(d, indent=2, ensure_ascii=False))


# --- subcomandos ---------------------------------------------------------


def cmd_whoami():
    out(gql("{ viewer { id name email } organization { name urlKey } }"))


def cmd_teams():
    out(gql("{ teams(first: 50) { nodes { id key name } } }"))


def cmd_relations(idents):
    # La pregunta del ticket: una vez escrita la relacion con el MCP, por que lado
    # y con que string de `type` vuelve. En salida `type` es String, no el enum.
    q = """
    query($id: String!) {
      issue(id: $id) {
        identifier title
        state { name type }
        relations { nodes { id type relatedIssue { identifier state { type } } } }
        inverseRelations { nodes { id type issue { identifier state { type } } } }
      }
    }"""
    for i in idents:
        print(f"=== {i} ===")
        out(gql(q, {"id": i}))


def cmd_frontier(project, label="map"):
    # Frontera = ticket abierto (state.type no completed ni canceled), sin
    # assignee, y sin ningun bloqueante abierto.
    #
    # Tamanos medidos contra el techo de complejidad de 10.000 por query, que
    # es distinto del presupuesto de 3.000.000 por hora. La complejidad se cobra
    # por lo que la query PIDE, no por lo que devuelve: este mismo shape pesa
    # igual con 5 issues que con 50.
    #
    #   pagina x anidadas -> complejidad
    #      250 x 50       -> 83.326  RECHAZADA
    #      100 x 10       ->  9.472  pasa, con 5% de aire. Muy justo.
    #       50 x 10       ->  4.737  elegido, 53% de aire
    #
    # 50 tickets de decision en un mapa ya es mucho, y 10 bloqueantes por ticket
    # tambien. Igual pedimos pageInfo: una lista de bloqueantes truncada hace
    # que un ticket bloqueado parezca tomable, y eso no puede pasar en silencio.
    q = """
    query($id: String!, $label: String!) {
      project(id: $id) {
        name
        issues(first: 50, filter: { labels: { name: { eq: $label } } }) {
          pageInfo { hasNextPage }
          nodes {
            identifier title
            state { name type }
            assignee { displayName }
            labels { nodes { name } }
            relations(first: 10) {
              pageInfo { hasNextPage }
              nodes { type relatedIssue { identifier state { type } } }
            }
            inverseRelations(first: 10) {
              pageInfo { hasNextPage }
              nodes { type issue { identifier state { type } } }
            }
          }
        }
      }
    }"""
    data = gql(q, {"id": project, "label": label})
    if not data or not data.get("project"):
        out(data)
        return

    proj = data["project"]
    nodes = proj["issues"]["nodes"]
    cerrado = ("completed", "canceled")

    truncado = []
    if proj["issues"]["pageInfo"]["hasNextPage"]:
        truncado.append("la lista de issues del Project")
    for n in nodes:
        for campo in ("relations", "inverseRelations"):
            if n[campo]["pageInfo"]["hasNextPage"]:
                truncado.append(n["identifier"] + "." + campo)

    print("Project: " + proj["name"])
    print("Tickets con label " + label + ": " + str(len(nodes)))
    print()

    frontera, bloqueados, fuera = [], [], []
    for n in nodes:
        ident, titulo = n["identifier"], n["title"]
        if n["state"]["type"] in cerrado:
            fuera.append((ident, titulo, "cerrado (" + n["state"]["name"] + ")"))
            continue
        if n["assignee"]:
            fuera.append((ident, titulo, "tomado por " + n["assignee"]["displayName"]))
            continue
        # Los bloqueantes de X son inverseRelations con type blocks: el campo
        # `issue` es el que bloquea. Medido, no supuesto.
        abiertos = [
            r["issue"]["identifier"]
            for r in n["inverseRelations"]["nodes"]
            if r["type"] == "blocks" and r["issue"]["state"]["type"] not in cerrado
        ]
        if abiertos:
            bloqueados.append((ident, titulo, "bloqueado por " + ", ".join(abiertos)))
        else:
            frontera.append((ident, titulo))

    print("FRONTERA, tomables ahora:")
    for ident, titulo in frontera or []:
        print("  " + ident + "  " + titulo)
    if not frontera:
        print("  (vacia)")
    print()
    print("Bloqueados:")
    for ident, titulo, por in bloqueados or []:
        print("  " + ident + "  " + titulo + "  -> " + por)
    if not bloqueados:
        print("  (ninguno)")
    print()
    print("Fuera de la frontera por otra razon:")
    for ident, titulo, por in fuera or []:
        print("  " + ident + "  " + titulo + "  -> " + por)
    if not fuera:
        print("  (ninguno)")

    if truncado:
        print()
        print("ATENCION: estas listas vinieron truncadas y la frontera de arriba")
        print("puede estar mal. Hay que paginar antes de confiar en ella:")
        for t in truncado:
            print("  " + t)


def cmd_chip(project_id, ident):
    issue = gql("query($id: String!){ issue(id:$id){ id identifier url } }", {"id": ident})
    if not issue or not issue.get("issue"):
        sys.exit(f"no encuentro el issue {ident}")
    iss = issue["issue"]
    content = (
        "# Test de chip\n\n"
        f"Mencion viva: <issue id=\"{iss['id']}\" href=\"{iss['url']}\">{iss['identifier']}</issue>\n\n"
        f"Control, identificador pelado: {iss['identifier']}\n\n"
        f"Control, link markdown: [{iss['identifier']}]({iss['url']})\n"
    )
    created = gql(
        """mutation($in: DocumentCreateInput!) {
             documentCreate(input: $in) { success document { id title updatedAt } } }""",
        {"in": {"title": "TEST chip 01", "content": content, "projectId": project_id}},
    )
    out(created)
    doc_id = created["documentCreate"]["document"]["id"]
    back = gql(
        "query($id: String!){ document(id:$id){ id title updatedAt content } }", {"id": doc_id}
    )
    print("\n=== content que devuelve la API, crudo ===")
    print(repr(back["document"]["content"]))
    print("\nDocument id para revisar en la UI:", doc_id)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    cmd, *rest = sys.argv[1:]
    {
        "whoami": lambda: cmd_whoami(),
        "teams": lambda: cmd_teams(),
        "relations": lambda: cmd_relations(rest),
        "frontier": lambda: cmd_frontier(*rest[:2]),
        "chip": lambda: cmd_chip(rest[0], rest[1]),
    }.get(cmd, lambda: sys.exit(__doc__))()
