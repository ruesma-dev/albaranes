"""F-117 medición: líneas con partida fuera de la lista de su obra (SOLO LECTURA).

PG con default_transaction_read_only=on; Sigrid solo vía sigrid-api, SELECT.
Para cada lectura que hoy queda fuera de la lista, cuenta cuántas hojas de la
obra tienen su mismo «esqueleto» (E1: segmentos numéricos sin ceros y sin la
letra pegada detrás, «03A» ⇒ «3») y, aparte, cuántas comparten capítulo raíz y
último número (E2, más laxa, solo para comparar). No escribe nada.
"""
import sys, os, re, json
from collections import Counter, defaultdict
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "services", "albaranes-comun"))
from comun_ro import pg, sigrid
from ruesma_comun.sigrid.partidas import (
    SQL_PARTIDAS_POR_OBRA, ListaPartidasObra, normalizar_partida, resolver_partida_obra,
)

MOTIVOS = ("partida_fuera_de_lista", "partida_ambigua_en_obra")
RE_NUM_LETRA = re.compile(r"^(\d+)([A-Z]+)$")

SQL = """
select d.id, d.obra_codigo, d.approved, lv.line_kind, lv.review_reasons_json,
       lv.codigo_partida_albaran, lv.codigo_partida_final, lv.partida_action,
       lm.concepto, a.estado, coalesce(a.motivos_json,'') || coalesce(a.historial_json,'')
from albaran_valuations v
join albaran_documents_merge d on d.id = v.document_id
join albaran_line_valuations lv on lv.valuation_id = v.id
left join albaran_lines_merge lm on lm.id = lv.merge_line_id
left join albaran_altas_sigrid a on a.document_id = d.id
where coalesce(d.is_active, true) and d.deleted_at_utc is null
  and (lv.review_reasons_json like '%%partida_fuera_de_lista%%'
       or lv.review_reasons_json like '%%partida_ambigua_en_obra%%')
"""


def esqueleto(codigo):
    n = normalizar_partida(codigo)
    if n is None or "/" in n:
        return None
    segs = []
    for s in n.split("."):
        m = RE_NUM_LETRA.match(s)
        segs.append(m.group(1).lstrip("0") or "0" if m else s)
    return ".".join(segs)


def e2(codigo):
    n = normalizar_partida(codigo)
    if n is None or "/" in n:
        return None
    segs = n.split(".")
    if len(segs) < 2 or not re.search(r"\d+$", segs[-1]):
        return None
    return segs[0], int(re.search(r"\d+$", segs[-1]).group(0))


with pg() as c, c.cursor() as cur:
    cur.execute("SHOW transaction_read_only")
    print("transaction_read_only =", cur.fetchone()[0])
    cur.execute(SQL)
    filas = cur.fetchall()
print("líneas con motivo:", len(filas), "documentos:", len({f[0] for f in filas}))

listas = {}
for obra in sorted({(f[1] or "").strip() for f in filas if f[1]}):
    cols, rows = sigrid(SQL_PARTIDAS_POR_OBRA.replace("\\n", "\n"), [obra])
    listas[obra] = ListaPartidasObra.desde_filas(obra, cols, rows) if rows else None

res = Counter()
porcaso = []
for (doc, obra, apr, kind, rr, pa, pf, pact, concepto, alta, alta_txt) in filas:
    obra = (obra or "").strip()
    lista = listas.get(obra)
    motivo = next((m for m in MOTIVOS if m in (rr or "")), None)
    if lista is None:
        res["sin_lista"] += 1
        continue
    hoy = resolver_partida_obra(lista, pa, "ALM").motivo
    esq = esqueleto(pa)
    c1 = sorted({h.codigo for h in lista.hojas
                 if esq and esqueleto(h.codigo) == esq or esq and esqueleto(h.codigo_completo) == esq})
    k2 = e2(pa)
    c2 = sorted({h.codigo for h in lista.hojas if k2 and (e2(h.codigo_completo) == k2)})
    clave = "E1=0" if not c1 else ("E1=1" if len(c1) == 1 else "E1>=2")
    res[(motivo, hoy, clave)] += 1
    res[("alta", alta, "partida_no_encontrada" in (alta_txt or ""))] += 1
    porcaso.append((obra, pa, pf, pact, kind, apr, alta, motivo, hoy, c1, c2,
                    [(h.codigo, h.codigo_completo, (h.descripcion or "")[:28]) for h in lista.hojas if h.codigo in c1 + c2][:6],
                    (concepto or "")[:40]))

for k, v in sorted(res.items(), key=lambda x: str(x[0])):
    print(k, v)
print("\n--- por lectura (obra | leída | final | acción | kind | aprobado | alta | motivo | hoy | E1 | E2 | hojas | concepto)")
for p in sorted(porcaso, key=lambda x: (x[0], str(x[1]))):
    print(" | ".join(str(x) for x in p))
print("\nlecturas distintas por obra:", Counter(p[0] for p in porcaso))
# Muestra de cómo numera cada obra sus hojas: patrones de segmento.
pat = Counter()
for obra, l in listas.items():
    if l:
        for h in l.hojas:
            pat[re.sub(r"[A-Z]", "A", re.sub(r"\d+", "9", normalizar_partida(h.codigo_completo) or ""))] += 1
print("\npatrones de hoja (todas las obras afectadas):", pat.most_common(15))
