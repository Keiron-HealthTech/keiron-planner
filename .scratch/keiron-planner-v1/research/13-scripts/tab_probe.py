#!/usr/bin/env python3
"""
Harness del ticket 13: si una pestana abierta puede deshacer una escritura por API.

El 09 midio la falla directa (el plugin pisando a la persona) y la resolvio
releyendo tarde. Esto mide la falla INVERSA: los Documents de Linear son
colaborativos sobre Yjs, y un cliente con el documento abierto sostiene su
propio estado. Cuando el plugin escribe por API, ese cliente puede adoptar el
contenido nuevo o re-sincronizar empujando el suyo viejo.

El campo que decide es `Document.contentState`: el estado Yjs serializado. Esta
en la SALIDA del tipo Document pero NO en `DocumentUpdateInput`, asi que la
reconciliacion la hace el servidor. Si un `documentUpdate(content:)` mueve
`contentState`, el servidor emitio un update Yjs y un cliente conectado lo
recibe. Si no lo mueve, el cliente nunca se entera.

Sin dependencias: solo stdlib. La API key sale de $LINEAR_API_KEY o de
~/.config/keiron-planner/linear.key, igual que el resto de los harness.

Subcomandos:

  snap <doc>                 Una linea con el estado: updatedAt, updatedBy, y
                             hash y largo de content y de contentState.
  poll <doc> [seg] [cada]    Snapshots repetidos. Para mirar que le hace al
                             documento una edicion hecha a mano en la UI.
  write <doc> <tag>          Un read-modify-write por API que agrega una linea
                             marcada con <tag>. Reporta el antes y el despues.
  run <doc> <tag> [t,t,t]    write + relecturas en los segundos pedidos, todo
                             en un solo proceso para que los tiempos sean
                             reales. Es el experimento del ticket.

Todo lo que escribe queda en el Document que se pasa por argumento. Este script
no distingue: tiene que ser un sandbox.
"""
import hashlib
import json
import os
import pathlib
import sys
import time
import urllib.error
import urllib.request

ENDPOINT = "https://api.linear.app/graphql"

Q_READ = """query($id:String!){
  document(id:$id){ updatedAt updatedBy{name} content contentState }
}"""

M_WRITE = """mutation($id:String!,$c:String!){
  documentUpdate(id:$id, input:{content:$c}){
    success lastSyncId document{ updatedAt contentState }
  }
}"""


def api_key():
    k = os.environ.get("LINEAR_API_KEY")
    if k:
        return k.strip()
    p = pathlib.Path.home() / ".config" / "keiron-planner" / "linear.key"
    if p.exists():
        return p.read_text().strip()
    sys.exit("no hay API key: ni $LINEAR_API_KEY ni ~/.config/keiron-planner/linear.key")


def gql(query, variables=None):
    body = json.dumps({"query": query, "variables": variables or {}}).encode()
    req = urllib.request.Request(ENDPOINT, data=body, method="POST")
    req.add_header("Content-Type", "application/json")
    req.add_header("Authorization", api_key())
    try:
        with urllib.request.urlopen(req) as r:
            payload = json.loads(r.read())
    except urllib.error.HTTPError as e:
        payload = json.loads(e.read())
    if "errors" in payload:
        print(json.dumps(payload["errors"], indent=2, ensure_ascii=False))
        sys.exit("la query fallo")
    return payload["data"]


def h(s):
    if s is None:
        return "-"
    return hashlib.sha256(s.encode()).hexdigest()[:8]


def read(doc_id):
    d = gql(Q_READ, {"id": doc_id})["document"]
    return {
        "updatedAt": d["updatedAt"],
        "by": (d["updatedBy"] or {}).get("name", "?"),
        "content": d["content"] or "",
        "state": d["contentState"],
    }


def line(label, s, tag=None):
    mark = ""
    if tag is not None:
        mark = "  tag:%s" % ("PRESENTE" if tag in s["content"] else "*** AUSENTE ***")
    print("%-14s %s  content=%s/%-5d  state=%s/%-6d  by=%s%s"
          % (label, s["updatedAt"], h(s["content"]), len(s["content"]),
             h(s["state"]), len(s["state"] or ""), s["by"], mark))


HEAD = "%-14s %-24s %-18s %-19s %s" % ("cuando", "updatedAt", "content", "contentState", "quien")


def cmd_snap(doc_id, *_):
    print(HEAD)
    line("ahora", read(doc_id))


def cmd_poll(doc_id, secs="120", every="10", *_):
    secs, every = int(secs), int(every)
    print(HEAD)
    t0 = time.time()
    prev = None
    while True:
        el = time.time() - t0
        s = read(doc_id)
        changed = ""
        if prev:
            bits = []
            if h(s["content"]) != h(prev["content"]):
                bits.append("CONTENT CAMBIO")
            if h(s["state"]) != h(prev["state"]):
                bits.append("STATE CAMBIO")
            if s["updatedAt"] != prev["updatedAt"]:
                bits.append("updatedAt movio")
            changed = "   <-- " + ", ".join(bits) if bits else ""
        line("t+%ds" % int(el), s)
        if changed:
            print(changed)
        prev = s
        if el + every > secs:
            break
        time.sleep(every)


def compose(content, tag):
    """Agrega una linea marcada al final. Read-modify-write, como map:write."""
    stamp = time.strftime("%H:%M:%S")
    return content.rstrip("\n") + "\n\nESCRITURA DEL PLUGIN %s a las %s\n" % (tag, stamp)


def do_write(doc_id, tag):
    before = read(doc_id)
    new = compose(before["content"], tag)
    t0 = time.time()
    r = gql(M_WRITE, {"id": doc_id, "c": new})["documentUpdate"]
    ms = (time.time() - t0) * 1000
    print(HEAD)
    line("antes", before, tag)
    print("%-14s success=%s  lastSyncId=%s  %.0f ms" % ("mutation", r["success"], r["lastSyncId"], ms))
    st = r["document"]["contentState"]
    print("%-14s updatedAt=%s  state=%s/%d  (lo que devuelve la mutation)"
          % ("", r["document"]["updatedAt"], h(st), len(st or "")))
    print("%-14s el documentUpdate MOVIO contentState: %s"
          % ("", h(st) != h(before["state"])))
    return before, tag


def cmd_write(doc_id, tag="A", *_):
    before, tag = do_write(doc_id, tag)
    time.sleep(1)
    line("t+1s", read(doc_id), tag)


def cmd_run(doc_id, tag="A", ats="5,15,30,60,120,300", *_):
    ats = [int(x) for x in ats.split(",")]
    before, tag = do_write(doc_id, tag)
    t0 = time.time()
    lost_at = None
    for at in ats:
        d = at - (time.time() - t0)
        if d > 0:
            time.sleep(d)
        s = read(doc_id)
        line("t+%ds" % at, s, tag)
        if tag not in s["content"] and lost_at is None:
            lost_at = at
            print("   *** LA ESCRITURA DEL PLUGIN DESAPARECIO ***")
    print()
    if lost_at is None:
        print("VEREDICTO: la escritura sobrevivio los %d segundos completos." % ats[-1])
    else:
        print("VEREDICTO: la escritura fue deshecha en algun punto antes de t+%ds." % lost_at)


def main():
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    cmd, doc_id, rest = sys.argv[1], sys.argv[2], sys.argv[3:]
    fn = {"snap": cmd_snap, "poll": cmd_poll, "write": cmd_write, "run": cmd_run}.get(cmd)
    if not fn:
        sys.exit("subcomando desconocido: %s" % cmd)
    fn(doc_id, *rest)


if __name__ == "__main__":
    main()
