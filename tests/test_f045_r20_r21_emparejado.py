# tests/test_f045_r20_r21_emparejado.py
"""F-045 · R20 y R21: emparejar de verdad los 59 albaranes con sus ficheros.

Medición del líder sobre el material real (2026-09-15, 133 ficheros en
OneDrive): la regla de la spec —lo que va tras el último `_`— deja **24 de 59
códigos sin fichero**, porque los nombres que llegan de obra son de la forma

    ALB. C.T.C 2025-01-27  Vertedero Arecosur 188048-24385 - 0669 BLOSSOM.pdf

donde el código va EN MEDIO y no hay ni un `_`. Buscarlo como subcadena baja a
14, pero aparecen ambigüedades. Así que el emparejado es una **escalera de
estrategias**, de la más específica a la más laxa, y **la ambigüedad no se
resuelve sola: se lista**. Asignar en silencio un albarán al caso equivocado
haría que el eval comparase un papel contra el ground truth de otro, y eso no
lo detecta nadie.
"""

from __future__ import annotations

from evals.revision import albaranes

# Los 59 códigos del Excel llegan ya normalizados (sin puntos ni barras).
CODIGOS = {
    "170161": "GEN-009",
    "2115714": "FER-003",
    "202601007181": "GEN-003",
    "MC26442903": "RES-020",
    "0001167": "HOR-003",
    "24385": "RES-009",
    "24788": "RES-012",
    "24790": "RES-013",
    "030490": "RES-016",
}


def casos(*codigos):
    return {codigo: CODIGOS[codigo] for codigo in codigos}


# --- Normalizar antes de comparar: el Excel puntúa, el fichero no ---------


def test_f045_r20_el_codigo_con_puntos_de_millar_casa_con_el_fichero_sin_ellos():
    plan = albaranes.emparejar(casos("170161", "2115714"),
                               ["170161.pdf", "2115714.pdf"])
    assert plan.fallos == []
    assert {c.caso_id for c in plan.copias} == {"GEN-009", "FER-003"}


def test_f045_r20_el_codigo_con_barras_casa_igual():
    plan = albaranes.emparejar(casos("202601007181", "MC26442903"),
                               ["2026-01-007181.pdf", "MC 26-442903.pdf"])
    assert plan.fallos == []
    assert len(plan.copias) == 2


# --- El código va EN MEDIO del nombre: hace falta buscarlo ----------------


def test_f045_r20_el_codigo_en_medio_del_nombre_se_encuentra():
    nombre = "ALB. C.T.C 2025-01-27  Vertedero Arecosur 188048-24385 - 0669 BLOSSOM II.pdf"
    plan = albaranes.emparejar(casos("24385"), [nombre])
    assert [c.caso_id for c in plan.copias] == ["RES-009"]
    assert plan.copias[0].estrategia == "subcadena"


def test_f045_r20_la_coincidencia_exacta_gana_a_la_subcadena():
    """Un nombre que contiene dos códigos, pero uno de ellos ES el nombre."""
    plan = albaranes.emparejar(
        casos("24385", "24788"), ["ALB 24788 del 24385.pdf", "24385.pdf"]
    )
    por_caso = {c.caso_id: c for c in plan.copias}
    assert por_caso["RES-009"].origen == "24385.pdf"
    assert por_caso["RES-009"].estrategia == "exacto"


def test_f045_r20_un_codigo_demasiado_corto_no_se_busca_como_subcadena():
    """`117` aparecería dentro de cualquier fecha; eso no es un emparejado."""
    plan = albaranes.emparejar({"117": "RES-099"}, ["ALB 2025-01-17 obra 669.pdf"])
    assert plan.copias == []
    assert {f.tipo for f in plan.fallos} == {"codigo_sin_fila", "fila_sin_fichero"}


# --- Ceros a la izquierda --------------------------------------------------


def test_f045_r20_los_ceros_a_la_izquierda_se_contemplan_pero_en_ultimo_lugar():
    plan = albaranes.emparejar(casos("0001167"), ["1167.pdf"])
    assert [c.caso_id for c in plan.copias] == ["HOR-003"]
    assert plan.copias[0].estrategia == "sin_ceros"


def test_f045_r20_quitar_ceros_no_confunde_dos_codigos_distintos():
    """SS-0801977 y SS-0001977 difieren por dentro: el cero de en medio manda."""
    plan = albaranes.emparejar({"SS0001977": "RES-005"}, ["SS-0801977.pdf"])
    assert plan.copias == []
    assert [f.tipo for f in plan.fallos] == ["codigo_sin_fila", "fila_sin_fichero"]


# --- R21: la ambigüedad se lista, NUNCA se resuelve sola ------------------


def test_f045_r21_un_fichero_con_dos_albaranes_no_se_asigna_a_ninguno():
    """Existe de verdad: un PDF con dos albaranes de fechas distintas.

    sv1 parte los PDF multipágina (1 página = 1 albarán); partir este es
    trabajo del humano. Asignarlo a uno de los dos en silencio dejaría al otro
    sin papel y a este comparándose contra el ground truth equivocado.
    """
    nombre = "ALB. C.T.C. 2025-02-13 24788 Y 2025-02-14 24790 - 0669.pdf"
    plan = albaranes.emparejar(casos("24788", "24790"), [nombre])
    varios = [f for f in plan.fallos if f.tipo == "fichero_varios_codigos"]
    assert len(varios) == 1
    assert "24788" in varios[0].detalle and "24790" in varios[0].detalle
    assert plan.copias == []


def test_f045_r21_dos_ficheros_distintos_con_el_mismo_codigo_se_listan():
    plan = albaranes.emparejar(
        casos("24385"), ["ALB 24385 hormigon.pdf", "copia de 24385.pdf"]
    )
    duplicados = [f for f in plan.fallos if f.tipo == "codigo_duplicado"]
    assert len(duplicados) == 1
    assert "ALB 24385 hormigon.pdf" in duplicados[0].detalle
    assert plan.copias == []


def test_f045_r21_el_png_suelto_sigue_siendo_un_caso_legitimo():
    plan = albaranes.emparejar(casos("030490"), ["0669 BLOSSOM II _030490.png"])
    assert [(c.caso_id, c.destino) for c in plan.copias] == [("RES-016", "RES-016.png")]


def test_f045_r21_el_pdf_y_el_png_del_mismo_codigo_siguen_siendo_gemelos():
    plan = albaranes.emparejar(
        casos("030490"), ["ALB 030490.pdf", "0669 BLOSSOM II _030490.png"]
    )
    assert [c.caso_id for c in plan.copias] == ["RES-016", "RES-016-IMG"]


def test_f045_r21_cada_estrategia_queda_anotada_para_que_el_humano_revise():
    """Antes de renombrar hay que poder ver POR QUÉ se casó cada fichero."""
    plan = albaranes.emparejar(
        casos("170161", "24385", "0001167"),
        ["170161.pdf", "ALB del 24385 - obra 669.pdf", "1167.pdf"],
    )
    assert {c.estrategia for c in plan.copias} == {"exacto", "subcadena", "sin_ceros"}
    assert all(c.estrategia for c in plan.copias)
