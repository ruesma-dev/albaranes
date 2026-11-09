"""F-111 medición C: capítulo de residuos en las obras (Sigrid vía sigrid-api, lectura)."""
import sys, os, unicodedata
from collections import Counter, defaultdict
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "services", "albaranes-comun"))
from comun_ro import pg, sigrid
from ruesma_comun.sigrid.partidas import SQL_PARTIDAS_POR_OBRA


def plano(t):
    t = unicodedata.normalize("NFKD", t or "").encode("ascii", "ignore").decode().upper()
    return t


with pg() as c, c.cursor() as cur:
    cur.execute("""select distinct obra_codigo from albaran_documents_merge
                   where obra_codigo is not null and coalesce(is_active,true) and deleted_at_utc is null
                   and created_at_utc >= to_char(now() - interval '120 days','YYYY-MM-DD')""")
    obras = sorted({r[0].strip() for r in cur.fetchall() if r[0] and r[0].strip()})
print("obras con albaranes 120 d:", len(obras))

resumen = []
for obra in obras:
    try:
        cols, rows = sigrid(SQL_PARTIDAS_POR_OBRA.replace("\\\n", "\n"), [obra])
    except SystemExit:
        raise
    except Exception as e:
        print(obra, "ERROR", type(e).__name__)
        continue
    by = {r[cols.index("ide")]: dict(zip(cols, r)) for r in rows}
    padres = {n["padide"] for n in by.values() if n["padide"] not in (None, 0)}
    def nivel(n):
        k = 0; v = set()
        while n["padide"] not in (None, 0) and n["padide"] in by and n["ide"] not in v:
            v.add(n["ide"]); n = by[n["padide"]]; k += 1
        return k, n["cod"]
    def hojas_bajo(ide):
        hijos = defaultdict(list)
        for n in by.values():
            hijos[n["padide"]].append(n["ide"])
        out, pila = [], [ide]
        while pila:
            x = pila.pop()
            if x not in padres:
                out.append(by[x])
            else:
                pila.extend(hijos[x])
        return out
    nodos = [n for n in by.values() if "RESIDU" in plano(n["res"]) or "RCD" in plano(n["res"])]
    # nodos más altos (sin ancestro que también case)
    ids = {n["ide"] for n in nodos}
    def tiene_ancestro(n):
        v = set()
        while n["padide"] in by and n["ide"] not in v:
            v.add(n["ide"]); n = by[n["padide"]]
            if n["ide"] in ids:
                return True
        return False
    altos = [n for n in nodos if not tiene_ancestro(n)]
    if not altos:
        resumen.append((obra, None))
        print(obra, "SIN nodo de residuos;", len(by), "nodos")
        continue
    for n in altos:
        niv, raiz = nivel(n)
        hs = hojas_bajo(n["ide"]) if n["ide"] in padres else [n]
        resumen.append((obra, (n["cod"], niv, raiz, len(hs))))
        print(obra, "nodo", n["cod"], "|", (n["res"] or "")[:50], "| nivel", niv, "raiz", raiz,
              "| hoja" if n["ide"] not in padres else f"| {len(hs)} hojas:",
              [(h["cod"], (h["res"] or "")[:35]) for h in hs[:8]])

print("\nobras sin nodo:", sum(1 for r in resumen if r[1] is None), "de", len({r[0] for r in resumen}))
print("nodos por obra:", Counter(Counter(r[0] for r in resumen if r[1]).values()))
print("nivel:", Counter(r[1][1] for r in resumen if r[1]), "raiz:", Counter(r[1][2] for r in resumen if r[1]))
print("n hojas:", Counter(r[1][3] for r in resumen if r[1]))
