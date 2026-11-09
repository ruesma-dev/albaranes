"""F-111 medición A y B (solo lectura)."""
import sys, os, re, json, math
from collections import Counter, defaultdict
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from comun_ro import pg

RE_CALC = re.compile(r"residuos_contenedores=(\d+) \(m3=([\d.]+) / contenedor=([\d.]+) m3\)")
RE_M3 = re.compile(r"(\d+(?:[.,]\d+)?)\s*m\s*[3³c]", re.I)

SQL = """
select d.id, d.obra_codigo, d.selected_contrato_codigo, d.approved, d.proveedor_nombre,
       lv.id, lv.line_kind, lv.review_reasons_json, lv.cantidad_convertida, lv.precio_unitario_final,
       lv.importe_calculado, lv.codigo_partida_albaran, lv.codigo_partida_final, lv.partida_action,
       lm.contexto_linea_json, lm.concepto, lv.matched_contrato_line_id
from albaran_valuations v
join albaran_documents_merge d on d.id = v.document_id
join albaran_line_valuations lv on lv.valuation_id = v.id
left join albaran_lines_merge lm on lm.id = lv.merge_line_id
where coalesce(d.is_active, true) and d.deleted_at_utc is null
"""


def sizes_contrato(cur, cache, cod):
    if cod in cache:
        return cache[cod]
    cur.execute("select descripcion_linea, precio_unitario from albaran_contrato_lines_merge where codigo_contrato=%s", (cod,))
    s = set()
    for desc, _ in cur.fetchall():
        if desc and "contenedor" in desc.lower():
            m = RE_M3.search(desc)
            if m:
                s.add(float(m.group(1).replace(",", ".")))
    cache[cod] = sorted(s)
    return cache[cod]


def nuevo(m3, sizes):
    if sizes:  # manda el contrato: el más pequeño en que cabe; si no cabe, el mayor en paquetes
        cab = [s for s in sizes if s + 1e-9 >= m3]
        if cab:
            return 1, min(cab)
        mx = max(sizes)
        return math.ceil(m3 / mx), mx
    for t in (3, 6, 9):
        if m3 <= t + 1e-9:
            return 1, t
    return math.ceil(m3 / 6), 6


with pg() as c, c.cursor() as cur:
    cur.execute(SQL)
    rows = cur.fetchall()
    cache = {}
    tot_res = 0
    calc = []
    sinpart = []
    fam = Counter()
    for r in rows:
        (doc, obra, ctr, apr, prov, lvid, kind, rr, cant, pu, imp, pa, pf, pact, ctx, concepto, mid) = r
        reasons = json.loads(rr) if rr else []
        ctxd = json.loads(ctx) if ctx else {}
        es_res = (ctxd or {}).get("tipo_familia") == "residuos" or any(str(x).startswith("residuos_") for x in reasons)
        if not es_res:
            continue
        tot_res += 1
        if kind == "from_albaran" and not (pf or "").strip():
            sinpart.append((doc, obra, apr, pa, pact, concepto))
        for x in reasons:
            m = RE_CALC.search(str(x))
            if m:
                n, m3, tam = int(m.group(1)), float(m.group(2)), float(m.group(3))
                sz = sizes_contrato(cur, cache, ctr) if ctr else []
                nn, nt = nuevo(m3, sz)
                defecto = "residuos_tamano_defecto_6m3" in reasons
                calc.append(dict(doc=doc, obra=obra, ctr=ctr, apr=apr, prov=prov, n=n, m3=m3, tam=tam, sz=sz,
                                 nn=nn, nt=nt, pu=pu, imp=imp, defecto=defecto))
    print("lineas residuos:", tot_res, "con calculo por volumen:", len(calc))
    cambian = [x for x in calc if x["nn"] != x["n"]]
    print("cambian de numero:", len(cambian), "docs:", len({x["doc"] for x in cambian}),
          "aprobados:", sum(1 for x in cambian if x["apr"]))
    print("contrato con tamanos:", Counter(bool(x["sz"]) for x in calc), "defecto6:", sum(x["defecto"] for x in calc))
    print("m3 distrib:", Counter(x["m3"] for x in calc).most_common())
    print("tam actual:", Counter(x["tam"] for x in calc))
    d_eur = sum((x["nn"] - x["n"]) * (x["pu"] or 0) for x in cambian)
    print("delta eur (mismo precio):", round(d_eur, 2))
    for x in cambian:
        print(" ", x["doc"][:8], x["obra"], x["ctr"], "apr" if x["apr"] else "-", "m3", x["m3"], "tam", x["tam"],
              "n", x["n"], "->", x["nn"], "x", x["nt"], "sz", x["sz"], "pu", x["pu"])
    print("cambia tamano sin cambiar n:", sum(1 for x in calc if x["nn"] == x["n"] and x["nt"] != x["tam"]))
    print("residuos from_albaran sin partida final:", len(sinpart), "docs", len({s[0] for s in sinpart}),
          "aprob", sum(1 for s in sinpart if s[2]))
    print("  partida_action:", Counter(s[4] for s in sinpart), "con lectura:", sum(1 for s in sinpart if (s[3] or '').strip()))
    print("  obras:", Counter(s[1] for s in sinpart))
    for s in sinpart[:15]:
        print("  ", s[0][:8], s[1], s[4], (s[5] or "")[:60])
    # partidas finales de residuos
    cur.execute(SQL)
    pf = Counter()
    obras_res = set()
    for r in cur.fetchall():
        reasons = json.loads(r[7]) if r[7] else []
        ctxd = json.loads(r[14]) if r[14] else {}
        if (ctxd or {}).get("tipo_familia") == "residuos" or any(str(x).startswith("residuos_") for x in reasons):
            pf[(r[1], r[12])] += 1
            obras_res.add(r[1])
    print("partidas finales residuos (obra, partida):", pf.most_common(40))
    print("OBRAS_RES=" + ",".join(sorted(o for o in obras_res if o)))
