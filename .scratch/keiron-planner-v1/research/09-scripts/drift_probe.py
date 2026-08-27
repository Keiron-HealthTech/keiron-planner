#!/usr/bin/env python3
"""
Harness del ticket 09: la deriva entre leer y escribir el mapa, medida.

Sin dependencias: solo stdlib. La API key se busca, en orden, en
$LINEAR_API_KEY y en ~/.config/keiron-planner/linear.key, igual que probe.py
del ticket 01.

Subcomandos:

  fields      Que expone el tipo Document y que acepta DocumentUpdateInput.
              Busca cualquier senal de concurrencia que el 02 no haya visto.
  mutations   Todas las mutations cuyo nombre toca document / draft / revision.
              Re-verifica que la maquinaria de borradores siga cerrada.
  roundtrip   Escribe un markdown conocido y lo lee de vuelta. Mide si el
              round-trip normaliza, y por lo tanto si comparar contenido
              sirve como senal de deriva o produce falsos positivos.
  stamp       Mide updatedAt: granularidad, si la mutation lo devuelve, y si
              una escritura identica igual lo mueve.
  history     Mide si un documentUpdate por API deja entrada en el historial
              de versiones, y que trae esa entrada.
  cost        Complejidad real de la relectura previa a la escritura.

Todo lo que escribe queda en el Document sandbox que se pasa por argumento.
Este script no distingue: tiene que ser un sandbox.
"""
import json
import os
import pathlib
import sys
import time
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
    sys.exit("no hay API key: ni $LINEAR_API_KEY ni ~/.config/keiron-planner/linear.key")


def gql(query, variables=None, auth=True):
    """Devuelve (data, headers). Levanta si hay errors."""
    body = json.dumps({"query": query, "variables": variables or {}}).encode()
    req = urllib.request.Request(ENDPOINT, data=body, method="POST")
    req.add_header("Content-Type", "application/json")
    if auth:
        req.add_header("Authorization", api_key())
    try:
        with urllib.request.urlopen(req) as r:
            payload = json.loads(r.read())
            headers = dict(r.headers)
    except urllib.error.HTTPError as e:
        payload = json.loads(e.read())
        headers = dict(e.headers)
    if "errors" in payload:
        print(json.dumps(payload["errors"], indent=2, ensure_ascii=False))
        sys.exit("la query fallo")
    return payload.get("data"), headers


def cx(headers):
    return headers.get("x-complexity") or headers.get("X-Complexity")


# ---------------------------------------------------------------- subcomandos

def cmd_fields():
    q = """
    {
      doc: __type(name: "Document") { fields { name type { name kind ofType { name } } } }
      inp: __type(name: "DocumentUpdateInput") { inputFields { name type { name kind ofType { name } } } }
      dc:  __type(name: "DocumentContent") { fields { name type { name kind ofType { name } } } }
    }
    """
    data, _ = gql(q, auth=False)

    def render(names):
        return ", ".join(sorted(names))

    doc = [f["name"] for f in data["doc"]["fields"]]
    inp = [f["name"] for f in data["inp"]["inputFields"]]
    dc = [f["name"] for f in data["dc"]["fields"]]

    print("== Document (salida), %d campos ==" % len(doc))
    print(render(doc))
    print()
    print("== DocumentUpdateInput, %d campos ==" % len(inp))
    print(render(inp))
    print()
    print("== DocumentContent (salida), %d campos ==" % len(dc))
    print(render(dc))
    print()
    print("== senales de concurrencia buscadas en el INPUT ==")
    for needle in ("version", "etag", "expected", "lastSyncId", "ifUnmodified", "updatedAt", "contentState", "revision", "draft"):
        hits = [n for n in inp if needle.lower() in n.lower()]
        print("  %-14s -> %s" % (needle, hits or "AUSENTE"))
    print()
    print("== senales de autoria de la ultima edicion en la SALIDA ==")
    for needle in ("updatedBy", "lastEdit", "editor", "actor", "creator", "updatedAt"):
        hits = [n for n in doc if needle.lower() in n.lower()]
        print("  %-14s -> %s" % (needle, hits or "AUSENTE"))


def cmd_mutations():
    q = """{ __type(name: "Mutation") { fields { name args { name type { kind name ofType { name } } } } } }"""
    data, _ = gql(q, auth=False)
    names = [f["name"] for f in data["__type"]["fields"]]
    for needle in ("document", "draft", "revision", "checkpoint"):
        hits = sorted(n for n in names if needle in n.lower())
        print("== mutations que contienen %r: %d ==" % (needle, len(hits)))
        for h in hits:
            print("   ", h)
        print()


ROUNDTRIP_MD = """# DD: sandbox 09

## Decisiones hasta ahora

- [01: algo](https://linear.app/keiron/issue/CRM-1): una linea con tildes, ñ y
  ~62 endpoints, y un `codigo inline`.
- [02: otra](https://linear.app/keiron/issue/CRM-2): y esta usa comillas "dobles".

## Aún no especificado

- **Una niebla en negrita.** Con cuerpo.

## Fuera de alcance

- Nada.
"""


def cmd_roundtrip(doc_id):
    marker = "<!-- probe %d -->" % int(time.time())
    sent = ROUNDTRIP_MD + "\n" + marker + "\n"
    m = """
    mutation($id: String!, $c: String!) {
      documentUpdate(id: $id, input: {content: $c}) {
        success
        lastSyncId
        document { id updatedAt }
      }
    }
    """
    data, h = gql(m, {"id": doc_id, "c": sent})
    print("documentUpdate success=%s complejidad=%s" % (data["documentUpdate"]["success"], cx(h)))
    print("updatedAt devuelto por la mutation: %s" % data["documentUpdate"]["document"]["updatedAt"])
    print()

    q = """query($id: String!) { document(id: $id) { id updatedAt content } }"""
    data2, h2 = gql(q, {"id": doc_id})
    got = data2["document"]["content"]
    print("relectura complejidad=%s updatedAt=%s" % (cx(h2), data2["document"]["updatedAt"]))
    print()
    print("== identidad byte a byte del round-trip ==")
    print("enviado: %d bytes | recibido: %d bytes | identico: %s"
          % (len(sent.encode()), len(got.encode()), sent == got))
    if sent != got:
        import difflib
        d = list(difflib.unified_diff(sent.splitlines(), got.splitlines(),
                                      "enviado", "recibido", lineterm="", n=1))
        print("\n".join(d) if d else "(difieren solo en whitespace de borde)")
    print()
    print("== ¿sobrevive el marcador HTML? ==")
    print("marcador %r presente en la relectura: %s" % (marker, marker in got))


def cmd_stamp(doc_id):
    q = """query($id: String!) { document(id: $id) { updatedAt content } }"""
    data0, _ = gql(q, {"id": doc_id})
    before, content = data0["document"]["updatedAt"], data0["document"]["content"]
    print("updatedAt inicial: %s" % before)
    print("granularidad del string: %s" % ("milisegundos" if "." in before else "SEGUNDOS"))
    print()

    print("== escritura IDENTICA (mismo content) ==")
    m = """
    mutation($id: String!, $c: String!) {
      documentUpdate(id: $id, input: {content: $c}) { success document { updatedAt } }
    }
    """
    data1, _ = gql(m, {"id": doc_id, "c": content})
    same_write = data1["documentUpdate"]["document"]["updatedAt"]
    print("updatedAt tras reescribir lo mismo: %s" % same_write)
    print("¿lo movio?: %s" % (same_write != before))
    print()

    time.sleep(2)
    print("== escritura DISTINTA ==")
    data2, _ = gql(m, {"id": doc_id, "c": content + "\n<!-- stamp -->\n"})
    diff_write = data2["documentUpdate"]["document"]["updatedAt"]
    print("updatedAt tras cambiar el contenido: %s" % diff_write)
    print("¿lo movio?: %s" % (diff_write != same_write))
    print()

    print("== ¿la mutation devuelve el MISMO updatedAt que una relectura inmediata? ==")
    data3, _ = gql(q, {"id": doc_id})
    reread = data3["document"]["updatedAt"]
    print("mutation dijo: %s" % diff_write)
    print("relectura dice: %s" % reread)
    print("coinciden: %s  (si coinciden, el plugin puede encadenar sin releer)" % (diff_write == reread))
    print()

    print("== ¿tocar solo el titulo mueve updatedAt? ==")
    qt = """query($id: String!) { document(id: $id) { title } }"""
    dt, _ = gql(qt, {"id": doc_id})
    title = dt["document"]["title"]
    mt = """
    mutation($id: String!, $t: String!) {
      documentUpdate(id: $id, input: {title: $t}) { success document { updatedAt } }
    }
    """
    time.sleep(2)
    dt2, _ = gql(mt, {"id": doc_id, "t": title})
    print("updatedAt tras re-escribir el mismo titulo: %s" % dt2["documentUpdate"]["document"]["updatedAt"])
    print("¿lo movio?: %s" % (dt2["documentUpdate"]["document"]["updatedAt"] != reread))


def cmd_history(doc_id):
    q = """
    query($id: String!) {
      documentContentHistory(id: $id) {
        history {
          id
          createdAt
          contentDataSnapshotAt
          actorIds
        }
      }
    }
    """
    data, h = gql(q, {"id": doc_id})
    hist = data["documentContentHistory"]["history"]
    print("entradas de historial: %d (complejidad=%s)" % (len(hist), cx(h)))
    for e in hist[-8:]:
        print("  %s  snapshot=%s  actores=%s" % (e["createdAt"], e["contentDataSnapshotAt"], e["actorIds"]))
    print()
    print("== ¿trae el contenido del snapshot? ==")
    q2 = """
    query($id: String!) {
      documentContentHistory(id: $id) { history { id contentData } }
    }
    """
    try:
        d2, h2 = gql(q2, {"id": doc_id})
        entries = d2["documentContentHistory"]["history"]
        last = entries[-1] if entries else None
        print("contentData del ultimo: %s" % ("presente, %d chars" % len(json.dumps(last["contentData"])) if last and last.get("contentData") else "vacio/ausente"))
        print("complejidad de traer contentData: %s" % cx(h2))
    except SystemExit:
        print("contentData no consultable por esta via")


def cmd_cost(doc_id):
    print("== costo de la relectura previa a escribir ==")
    for label, q in [
        ("solo updatedAt", "query($id: String!) { document(id: $id) { updatedAt } }"),
        ("updatedAt + content", "query($id: String!) { document(id: $id) { id updatedAt content } }"),
        ("el paquete completo", "query($id: String!) { document(id: $id) { id title updatedAt content creator { id } } }"),
    ]:
        _, h = gql(q, {"id": doc_id})
        print("  %-22s complejidad=%s" % (label, cx(h)))
    print()
    print("== presupuesto restante de esta key ==")
    _, h = gql("{ viewer { id } }")
    for k in sorted(h):
        if k.lower().startswith("x-ratelimit") or k.lower() == "x-complexity":
            print("  %s: %s" % (k, h[k]))


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    cmd = sys.argv[1]
    rest = sys.argv[2:]
    if cmd == "fields":
        cmd_fields()
    elif cmd == "mutations":
        cmd_mutations()
    elif cmd in ("roundtrip", "stamp", "history", "cost"):
        if not rest:
            sys.exit("uso: %s <document-id>" % cmd)
        {"roundtrip": cmd_roundtrip, "stamp": cmd_stamp,
         "history": cmd_history, "cost": cmd_cost}[cmd](rest[0])
    else:
        sys.exit("subcomando desconocido: %s" % cmd)


if __name__ == "__main__":
    main()
