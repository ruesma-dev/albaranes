"""F-117 medición 2 (SOLO LECTURA): qué estrategias resolverían cada lectura fuera de lista.

- E1d (direccional): la lectura NO lleva letra pegada a un número; la hoja SÍ
  («03A»), y quitándosela (y los ceros) coinciden.
- SUF: la lectura normalizada es el final, por segmentos completos, de una hoja.
- NODO: la lectura es un código NO hoja de la obra; cuántas hojas cuelgan de él.
- COLISIONES: en todas las obras con albaranes en 120 días, cuántos esqueletos
  E1d tienen 2 o más hojas con letra (CI.03A.8 y CI.03P.8 a la vez).
"""
import sys, os, re
from collections import Counter, defaultdict
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "services", "albaranes-comun"))
from comun_ro import pg, sigrid
from ruesma_comun.sigrid.partidas import (
    SQL_PARTIDAS_POR_OBRA, ListaPartidasObra, codigo_completo, normalizar_partida, resolver_partida_obra,
)

RE_NL = re.compile(r"^(\d+)([A-Z]+)$")


def segs(c):
    n = normalizar_partida(c)
    return None if n is None or "/" in n else n.split(".")


def tiene_letra(ss):
    return any(RE_NL.match(s) for s in ss)


def esq(ss):
    return ".".join((RE_NL.match(s).group(1).lstrip("0") or "0") if RE_NL.match(s) else s for s in ss)


def e1d(lista, lectura):
    ss = segs(lectura)
    if not ss or tiene_letra(ss):
        return []
    k = ".".join(ss)
    out = set()
    for h in lista.hojas:
        for f in (h.codigo, h.codigo_completo):
            hs = segs(f)
            if hs and tiene_letra(hs) and esq(hs) == k:
                out.add(h.codigo)
    return sorted(out)


def suf(lista, lectura):
    ss = segs(lectura)
    if not ss or len(ss) < 2:
        return []
    out = set()
    for h in lista.hojas:
        for f in (h.codigo, h.codigo_completo):
            hs = segs(f)
            if hs and len(hs) > len(ss) and hs[-len(ss):] == ss:
                out.add(h.codigo)
    return sorted(out)


def arbol(cols, rows):
    by = {r[cols.index("ide")]: dict(zip(cols, r)) for r in rows}
    hijos = defaultdict(list)
    for n in by.values():
        hijos[n["padide"]].append(n["ide"])
    return by, hijos


def nodo(by, hijos, lectura):
    k = normalizar_partida(lectura)
    out = []
    for n in by.values():
        raiz, v = n, set()
        while raiz["padide"] in by and raiz["ide"] not in v:
            v.add(raiz["ide"]); raiz = by[raiz["padide"]]
        formas = {normalizar_partida(n["cod"]), normalizar_partida(codigo_completo(raiz["cod"], n["cod"])) if n["cod"] else None}
        if n["cod"] and k in formas and hijos.get(n["ide"]):
            pila = list(hijos[n["ide"]])
            while pila:
                x = pila.pop()
                if hijos.get(x):
                    pila.extend(hijos[x])
                elif by[x]["cod"]:
                    out.append((by[x]["cod"], (by[x]["res"] or "")[:26]))
    return out


with pg() as c, c.cursor() as cur:
    cur.execute("SHOW transaction_read_only")
    assert cur.fetchone()[0] == "on"
    cur.execute("""select d.obra_codigo, lv.codigo_partida_albaran, lv.codigo_partida_final, lm.concepto
        from albaran_valuations v join albaran_documents_merge d on d.id = v.document_id
        join albaran_line_valuations lv on lv.valuation_id = v.id
        left join albaran_lines_merge lm on lm.id = lv.merge_line_id
        where coalesce(d.is_active, true) and d.deleted_at_utc is null
          and lv.review_reasons_json like '%%partida_fuera_de_lista%%'""")
    filas = cur.fetchall()
    cur.execute("""select distinct obra_codigo from albaran_documents_merge
        where obra_codigo is not null and coalesce(is_active,true) and deleted_at_utc is null
          and created_at_utc >= to_char(now() - interval '120 days','YYYY-MM-DD')""")
    obras120 = sorted({r[0].strip() for r in cur.fetchall() if r[0] and r[0].strip()})

datos = {}
for obra in sorted(set(obras120) | {(f[0] or "").strip() for f in filas if f[0]}):
    cols, rows = sigrid(SQL_PARTIDAS_POR_OBRA.replace("\\n", "\n"), [obra])
    if rows:
        datos[obra] = (ListaPartidasObra.desde_filas(obra, cols, rows), *arbol(cols, rows))

print("--- lecturas fuera de lista hoy (obra | leída | final | E1d | SUF | NODO(n hojas, muestra) | concepto)")
cuenta = Counter()
vistos = Counter()
for obra, pa, pf, concepto in filas:
    obra = (obra or "").strip()
    if obra not in datos:
        continue
    lista, by, hijos = datos[obra]
    if resolver_partida_obra(lista, pa, "ALM").motivo != "fuera_de_lista":
        cuenta["hoy_ya_casa"] += 1
        continue
    a, b, n = e1d(lista, pa), suf(lista, pa), nodo(by, hijos, pa)
    cuenta[("E1d", min(len(a), 2))] += 1
    cuenta[("SUF", min(len(b), 2))] += 1
    cuenta[("NODO", "0" if not n else ("1" if len(n) == 1 else ("2-5" if len(n) <= 5 else ">5")))] += 1
    vistos[(obra, pa, pf, tuple(a), tuple(b[:4]), len(n), tuple(n[:4]), (concepto or "")[:30])] += 1
for k, v in sorted(vistos.items()):
    print(v, "x", " | ".join(str(x) for x in k))
print()
for k, v in sorted(cuenta.items(), key=lambda x: str(x[0])):
    print(k, v)

print("\n--- colisiones E1d en", len(obras120), "obras con albaranes en 120 días")
tot_claves = col = 0
obras_con_letra = 0
ejemplos = []
for obra in obras120:
    if obra not in datos:
        continue
    lista = datos[obra][0]
    g = defaultdict(set)
    for h in lista.hojas:
        hs = segs(h.codigo_completo)
        if hs and tiene_letra(hs):
            g[esq(hs)].add(h.codigo)
    if g:
        obras_con_letra += 1
    planas = {normalizar_partida(h.codigo_completo) for h in lista.hojas} | {normalizar_partida(h.codigo) for h in lista.hojas}
    for k, cods in g.items():
        tot_claves += 1
        if len(cods) >= 2:
            col += 1
            if len(ejemplos) < 12:
                ejemplos.append((obra, k, sorted(cods)[:4]))
        if k in planas:
            cuenta["esqueleto_choca_con_hoja_plana"] += 1
print("obras con hojas con letra:", obras_con_letra, "| esqueletos:", tot_claves, "| con >=2 hojas:", col)
print("esqueleto que ya es otra hoja sin letra (la normalización de hoy ganaría):", cuenta["esqueleto_choca_con_hoja_plana"])
print("ejemplos de colisión:", ejemplos)
