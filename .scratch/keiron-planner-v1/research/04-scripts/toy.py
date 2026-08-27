#!/usr/bin/env python3
"""
Harness del ticket 04: el mapa de juguete en un Document de Linear.

Sin dependencias: solo stdlib. La API key se busca en $LINEAR_API_KEY y en
~/.config/keiron-planner/linear.key, igual que el harness del ticket 01.

Subcomandos:
  probe                 escribe la sonda de markdown y la relee, mostrando el diff
  put <TITLE> <FILE>    crea o actualiza un Document del sandbox con el archivo dado
  get <DOC_ID>          imprime el content tal como lo devuelve la API
  list                  lista los Documents del Project descartable
"""
import difflib
import json
import pathlib
import os
import sys
import urllib.request

ENDPOINT = "https://api.linear.app/graphql"
PROJECT = "400e790e-67c1-4eb0-8f4b-af388fc514a1"  # ZZ SANDBOX keiron-planner 01


def api_key():
    k = os.environ.get("LINEAR_API_KEY")
    if k:
        return k.strip()
    p = pathlib.Path.home() / ".config" / "keiron-planner" / "linear.key"
    if p.exists():
        return p.read_text().strip()
    sys.exit("No hay API key.")


def gql(query, variables=None):
    req = urllib.request.Request(
        ENDPOINT,
        data=json.dumps({"query": query, "variables": variables or {}}).encode(),
        headers={"Content-Type": "application/json", "Authorization": api_key()},
    )
    with urllib.request.urlopen(req) as f:
        out = json.loads(f.read())
    if "errors" in out:
        sys.exit(json.dumps(out["errors"], indent=1))
    return out["data"]


def docs():
    q = """query($p: String!) { project(id: $p) {
        documents(first: 50) { nodes { id title slugId url updatedAt } } } }"""
    return gql(q, {"p": PROJECT})["project"]["documents"]["nodes"]


def put(title, content):
    existing = {d["title"]: d for d in docs()}
    if title in existing:
        did = existing[title]["id"]
        q = """mutation($id: String!, $c: String!) {
            documentUpdate(id: $id, input: { content: $c })
            { success document { id url updatedAt } } }"""
        d = gql(q, {"id": did, "c": content})["documentUpdate"]["document"]
    else:
        q = """mutation($t: String!, $c: String!, $p: String!) {
            documentCreate(input: { title: $t, content: $c, projectId: $p })
            { success document { id url updatedAt } } }"""
        d = gql(q, {"t": title, "c": content, "p": PROJECT})["documentCreate"]["document"]
    return d


def get(doc_id):
    q = """query($id: String!) { document(id: $id) { id title url content } }"""
    return gql(q, {"id": doc_id})["document"]


PROBE = """# ZZ SONDA de markdown, ticket 04

Que sobrevive al pipeline Yjs de Linear y que no. Todo lo de abajo se escribio
por API y se releyo por API.

## 1. details / summary de HTML

<details>
<summary>Una decision plegada</summary>

El cuerpo de la decision, que en el mapa real ocupa doce lineas.

</details>

## 2. Toggle con el guion y el signo mayor

> Una decision plegada con quote
> El cuerpo de la decision.

## 3. Vineta anidada a dos niveles

- Decision en una linea, la que se ve siempre.
  - El detalle, indentado, que es lo que hoy ocupa doce lineas.
    - Un tercer nivel, para ver si sobrevive.

## 4. Tabla

| Ticket | La decision en una linea | Que se cayo |
| --- | --- | --- |
| 14 | Una vez por conductor | "falla ocho veces" era falso |
| 13 | No puede pisarlo | ninguna |

## 5. Encabezado de nivel 3 como ancla de una decision

### 14: Si el preflight corre por invocacion o por sesion

Una vez por conductor.

## 6. Checkbox

- [ ] sin resolver
- [x] resuelto

## 7. Separador y cita

---

> Cita simple.

## 8. Link markdown y URL pelada

[CRM-3346](https://linear.app/keiron/issue/CRM-3346)

https://linear.app/keiron/issue/CRM-3346

## 9. Codigo inline y bloque

Inline: `map:write`

```
un bloque de codigo
```
"""


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    cmd = sys.argv[1]
    if cmd == "list":
        for d in docs():
            print("%s  %-50s %s" % (d["id"], d["title"], d["url"]))
    elif cmd == "probe":
        d = put("ZZ SONDA markdown 04", PROBE)
        print("escrito:", d["url"])
        back = get(d["id"])["content"]
        print("\n--- diff escrito -> leido ---")
        for line in difflib.unified_diff(
            PROBE.splitlines(), back.splitlines(),
            fromfile="escrito", tofile="leido", lineterm="", n=1
        ):
            print(line)
        print("\n--- leido, crudo ---")
        print(back)
    elif cmd == "put":
        content = pathlib.Path(sys.argv[3]).read_text()
        d = put(sys.argv[2], content)
        print("%s  %s  %d chars" % (d["id"], d["url"], len(content)))
    elif cmd == "get":
        print(get(sys.argv[2])["content"])
    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    main()
