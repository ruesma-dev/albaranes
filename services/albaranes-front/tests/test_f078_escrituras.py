# tests/test_f078_escrituras.py
"""F-078 · R9–R16 · sv4 guarda en la fila lo que se va a ver.

- R9: el PATCH de fila toma el estado actual SOLO de la fila; lo que no tiene
  no lo completa con su línea.
- R10: cambiar la descripción la guarda en ``descripcion_linea`` en toda fila
  (Contrato o Nueva, con o sin blanca); vaciarla la deja vacía. Sustituye a
  F-065 CR1/H1 y al override de las Contrato «solo si difiere».
- R11: cambiar la unidad la guarda en ``unidad_contrato`` y, sin conversión,
  también en ``unidad_albaran`` (y en la derivada si es Nueva).
- R12–R16: «Origen ✎», «+ a Sigrid», «Traer líneas contrato» y «Dividir» dejan
  la fila con ``fila_a_guardar`` aplicada, en la misma transacción.

Repositorio real sobre SQLite (``f065_bbdd``: METALFIRE). Sin red.
"""
from __future__ import annotations

import pytest
from f065_bbdd import DOC, construir, ejecutar, fila, filas, linea, repositorio
from sqlalchemy import text
from sqlalchemy.orm import Session


def _editar(motor, vid, **campos):
    return repositorio(motor).update_line_conciliacion(
        document_id=DOC, valuation_line_id=vid, campos=campos,
    )


def _columnas(motor, vid, *columnas):
    with Session(motor) as s:
        return tuple(s.execute(
            text(f"SELECT {', '.join(columnas)} FROM albaran_line_valuations "  # noqa: S608
                 "WHERE id = :id"), {"id": vid},
        ).one())


def _derivada(motor, did):
    with Session(motor) as s:
        return dict(s.execute(
            text("SELECT descripcion_linea, unidad_medida, precio_unitario, codigo_partida, "
                 "origen FROM contrato_lines_derived WHERE id = :id"), {"id": did},
        ).mappings().one())


# =================================================================== #
# R9 · el estado actual sale solo de la fila
# =================================================================== #
def test_f078_r9_editar_la_cantidad_no_completa_la_unidad_con_la_de_su_linea():
    motor = construir()
    ejecutar(motor, "UPDATE albaran_line_valuations SET unidad_contrato = NULL WHERE id = 11")

    _editar(motor, 11, cantidad=6.0)

    assert fila(motor, 11)["unidad_contrato"] is None
    assert fila(motor, 11)["matched_contrato_line_id"] == 501


def test_f078_r9_editar_la_descripcion_no_completa_el_precio_con_el_de_su_linea():
    motor = construir()
    ejecutar(motor, "UPDATE albaran_line_valuations SET precio_unitario_final = NULL "
             "WHERE id = 11")

    _editar(motor, 11, descripcion="PUERTA EI2-60 IZQUIERDA")

    f = fila(motor, 11)
    assert f["precio_unitario_final"] is None
    assert f["matched_contrato_line_id"] == 501      # sin cambio de origen


def test_f078_r9_la_descripcion_de_su_linea_cuenta_como_cambio_si_la_fila_no_la_tiene():
    """Antes, «PUERTA CORTAFUEGOS EI2-60» era «lo que ya hay» (la de su línea) y no se
    escribía nada; ahora la fila no la tiene: se guarda."""
    motor = construir()

    _editar(motor, 11, descripcion="PUERTA CORTAFUEGOS EI2-60")

    assert fila(motor, 11)["descripcion_linea"] == "PUERTA CORTAFUEGOS EI2-60"


def test_f078_r9_la_derivada_editada_in_situ_recibe_lo_de_la_fila():
    """Nueva 13: la fila dice 55 € y su derivada 50 €; editar la cantidad deja la
    derivada con lo de la fila (el estado actual es el de la fila)."""
    motor = construir()
    ejecutar(motor, "UPDATE albaran_line_valuations SET precio_unitario_final = 55, "
             "descripcion_linea = 'PORTES A OBRA' WHERE id = 13")

    _editar(motor, 13, cantidad=2.0)

    d = _derivada(motor, 601)
    assert (d["precio_unitario"], d["descripcion_linea"]) == (55.0, "PORTES A OBRA")
    assert fila(motor, 13)["importe_calculado"] == pytest.approx(110.0)


# =================================================================== #
# R10 · la descripción, en descripcion_linea en toda fila
# =================================================================== #
def test_f078_r10_contrato_igual_que_la_de_su_linea_se_guarda():
    """Sustituye al override «solo si difiere» de F-065 R8."""
    motor = construir()
    ejecutar(motor, "UPDATE albaran_line_valuations SET descripcion_linea = 'OTRA' "
             "WHERE id = 11")

    _editar(motor, 11, descripcion="PUERTA CORTAFUEGOS EI2-60")

    f = fila(motor, 11)
    assert f["descripcion_linea"] == "PUERTA CORTAFUEGOS EI2-60"
    assert f["matched_contrato_line_id"] == 501


def test_f078_r10_nueva_con_blanca_se_guarda_en_la_fila_y_en_su_derivada():
    motor = construir()

    _editar(motor, 13, descripcion="  PORTES URGENTES  ")

    assert fila(motor, 13)["descripcion_linea"] == "PORTES URGENTES"
    assert _derivada(motor, 601)["descripcion_linea"] == "PORTES URGENTES"


def test_f078_r10_contrato_a_nueva_con_descripcion_nueva_va_a_la_fila_y_a_la_derivada():
    motor = construir()

    _editar(motor, 11, descripcion="PUERTA ESPECIAL", precio_unitario=120.0)

    f = fila(motor, 11)
    assert f["matched_contrato_line_id"] is None
    assert f["descripcion_linea"] == "PUERTA ESPECIAL"
    assert _derivada(motor, f["derived_contrato_line_id"])["descripcion_linea"] == (
        "PUERTA ESPECIAL"
    )


def test_f078_r10_contrato_a_nueva_sin_tocar_la_descripcion_conserva_la_de_la_fila():
    motor = construir()
    ejecutar(motor, "UPDATE albaran_line_valuations SET descripcion_linea = "
             "'PUERTA EI2-60 IZQUIERDA' WHERE id = 11")

    _editar(motor, 11, codigo_partida="09.09")

    f = fila(motor, 11)
    assert f["descripcion_linea"] == "PUERTA EI2-60 IZQUIERDA"
    assert _derivada(motor, f["derived_contrato_line_id"])["descripcion_linea"] == (
        "PUERTA EI2-60 IZQUIERDA"
    )


@pytest.mark.parametrize("vid", [11, 13])
def test_f078_r10_vaciarla_la_deja_vacia(vid):
    motor = construir()
    ejecutar(motor, "UPDATE albaran_line_valuations SET descripcion_linea = 'ALGO' "
             "WHERE id = :id", id=vid)

    _editar(motor, vid, descripcion=None)

    assert fila(motor, vid)["descripcion_linea"] is None


def test_f078_r10_sin_blanca_se_guarda_como_siempre():
    motor = construir()
    vid = repositorio(motor).add_standalone_valuation_line(document_id=DOC)

    _editar(motor, vid, descripcion="CARGA INCOMPLETA", cantidad=1.0, precio_unitario=12.5)

    assert fila(motor, vid)["descripcion_linea"] == "CARGA INCOMPLETA"


# =================================================================== #
# R11 · la unidad, también en unidad_albaran sin conversión
# =================================================================== #
def test_f078_r11_nueva_sin_conversion_guarda_la_unidad_en_las_dos_y_en_la_derivada():
    motor = construir()
    ejecutar(motor, "UPDATE albaran_line_valuations SET factor_conversion = 1.0 WHERE id = 13")

    _editar(motor, 13, unidad="VIAJE")

    assert _columnas(motor, 13, "unidad_contrato", "unidad_albaran") == ("VIAJE", "VIAJE")
    assert _derivada(motor, 601)["unidad_medida"] == "VIAJE"


def test_f078_r11_con_conversion_no_toca_unidad_albaran():
    """Fila 13: ``factor_conversion`` nulo (conversión desconocida)."""
    motor = construir()
    ejecutar(motor, "UPDATE albaran_line_valuations SET unidad_albaran = 'M3' WHERE id = 13")

    _editar(motor, 13, unidad="VIAJE")

    assert _columnas(motor, 13, "unidad_contrato", "unidad_albaran") == ("VIAJE", "M3")


def test_f078_r11_contrato_que_pasa_a_nueva_por_la_unidad_la_guarda_en_las_dos():
    motor = construir()

    _editar(motor, 11, unidad="PAR")

    f = fila(motor, 11)
    assert f["matched_contrato_line_id"] is None
    assert _columnas(motor, 11, "unidad_contrato", "unidad_albaran") == ("PAR", "PAR")


def test_f078_r11_sin_cambiar_la_unidad_no_se_toca_unidad_albaran():
    motor = construir()
    ejecutar(motor, "UPDATE albaran_line_valuations SET unidad_albaran = 'UDS' WHERE id = 11")

    _editar(motor, 11, cantidad=7.0)

    assert _columnas(motor, 11, "unidad_contrato", "unidad_albaran") == ("UD", "UDS")


# =================================================================== #
# R12 · «Origen ✎»
# =================================================================== #
def _reapuntar(motor, vid, **opciones):
    return repositorio(motor).set_line_conciliacion(
        document_id=DOC, valuation_line_id=vid, **opciones,
    )


def test_f078_r12_a_una_linea_de_contrato_trae_su_descripcion_y_su_unidad():
    """Antes la descripción quedaba a NULL a propósito y la ficha pintaba la de la
    línea; sv9 mandaba el concepto leído."""
    motor = construir()

    _reapuntar(motor, 12, mode="contract_line", matched_contrato_line_id=503)

    assert _columnas(motor, 12, "matched_contrato_line_id", "descripcion_linea",
                     "unidad_contrato", "unidad_albaran") == (
        503, "PUERTA CORTAFUEGOS EI2-120", "UD", "UD")


def test_f078_r12_si_su_linea_no_tiene_descripcion_conserva_la_que_tenia():
    motor = construir()
    ejecutar(motor, "UPDATE albaran_contrato_lines_merge SET descripcion_linea = '  ' "
             "WHERE id = 503")
    ejecutar(motor, "UPDATE albaran_line_valuations SET descripcion_linea = 'PUERTA "
             "EI2-90 HOJA' WHERE id = 12")

    _reapuntar(motor, 12, mode="contract_line", matched_contrato_line_id=503)

    assert fila(motor, 12)["descripcion_linea"] == "PUERTA EI2-90 HOJA"


def test_f078_r12_a_nueva_con_blanca_guarda_la_descripcion_que_se_veia():
    """Sustituye a F-065 H1 («con blanca sin editar no fija descripción»)."""
    motor = construir()

    _reapuntar(motor, 11, mode="nueva")

    f = fila(motor, 11)
    assert f["derived_contrato_line_id"] is not None
    assert f["descripcion_linea"] == "PUERTA CORTAFUEGOS EI2-60"
    assert _columnas(motor, 11, "unidad_contrato", "unidad_albaran") == ("UD", "UD")


def test_f078_r12_a_nueva_con_descripcion_tecleada_la_guarda():
    motor = construir()

    _reapuntar(motor, 11, mode="nueva", descripcion="PUERTA ESPECIAL")

    assert fila(motor, 11)["descripcion_linea"] == "PUERTA ESPECIAL"


# =================================================================== #
# R13 · «+ a Sigrid» (y «Copiar sin casar → Nueva»)
# =================================================================== #
def _blanca_sin_valorar(motor):
    ejecutar(motor, "INSERT INTO albaran_lines_merge (id, document_id, provider_origin, "
             "line_index, concepto, cantidad, precio, precio_neto, unidad_medida, "
             "codigo_imputacion) VALUES (704, :d, 'merge', 4, ' TORNILLOS M8 ', 2.0, "
             "10.0, 20.0, 'CAJA', '05.01')", d=DOC)


def _fila_de_blanca(motor, merge_line_id):
    with Session(motor) as s:
        return s.execute(text(
            "SELECT id FROM albaran_line_valuations WHERE merge_line_id = :m"),
            {"m": merge_line_id}).scalar_one()


def test_f078_r13_contrato_nace_con_concepto_unidad_y_cantidades():
    motor = construir()
    _blanca_sin_valorar(motor)

    assert repositorio(motor).add_conciliacion_for_merge_line(
        document_id=DOC, merge_line_id=704, mode="contract_line",
        matched_contrato_line_id=503) is True

    vid = _fila_de_blanca(motor, 704)
    assert _columnas(motor, vid, "descripcion_linea", "unidad_contrato", "unidad_albaran",
                     "cantidad_albaran", "cantidad_convertida") == (
        "TORNILLOS M8", "UD", "UD", 2.0, 2.0)


def test_f078_r13_nueva_nace_con_la_unidad_de_la_blanca_tambien_en_la_derivada():
    motor = construir()
    _blanca_sin_valorar(motor)

    repositorio(motor).add_conciliacion_for_merge_line(
        document_id=DOC, merge_line_id=704, mode="nueva")

    vid = _fila_de_blanca(motor, 704)
    f = fila(motor, vid)
    assert _columnas(motor, vid, "descripcion_linea", "unidad_contrato", "unidad_albaran",
                     "cantidad_convertida") == ("TORNILLOS M8", "CAJA", "CAJA", 2.0)
    d = _derivada(motor, f["derived_contrato_line_id"])
    assert (d["descripcion_linea"].strip(), d["unidad_medida"]) == ("TORNILLOS M8", "CAJA")


# =================================================================== #
# R14 · «Traer líneas contrato»
# =================================================================== #
def test_f078_r14_traer_lineas_nacen_con_unidad_albaran():
    motor = construir()

    (vid,) = repositorio(motor).add_valuation_lines_from_contrato(
        document_id=DOC, lineas=[(503, 5.0)])

    assert _columnas(motor, vid, "descripcion_linea", "unidad_contrato", "unidad_albaran",
                     "cantidad_convertida") == ("PUERTA CORTAFUEGOS EI2-120", "UD", "UD", 5.0)


# =================================================================== #
# R15 · «Dividir»
# =================================================================== #
def _dividir(motor, vid, *pares):
    from domain.models.review_models import ParteDivision

    return repositorio(motor).dividir_linea(
        document_id=DOC, valuation_line_id=vid,
        partes=[ParteDivision(cantidad=q, codigo_partida=p) for q, p in pares],
    )


def test_f078_r15_la_original_y_las_partes_quedan_con_su_descripcion_y_unidades():
    motor = construir()

    hecha = _dividir(motor, 11, (3.0, "01.01"), (5.0, "01.01"))

    for vid in (11, *hecha.partes):
        assert _columnas(motor, vid, "descripcion_linea", "unidad_contrato",
                         "unidad_albaran") == ("PUERTA CORTAFUEGOS EI2-60", "UD", "UD"), vid


def test_f078_r15_la_original_que_pasa_a_nueva_guarda_la_descripcion_que_se_veia():
    """Sustituye a F-065 R32 («con blanca y sin descripción fijada: nula»)."""
    motor = construir()

    _dividir(motor, 12, (4.0, "01.03"), (6.0, "01.02"))

    f = fila(motor, 12)
    assert f["matched_contrato_line_id"] is None
    assert f["descripcion_linea"] == "PUERTA CORTAFUEGOS EI2-90"


def test_f078_r15_nueva_con_blanca_divide_con_el_concepto_del_papel():
    """P1 = (b): la Nueva 13 (blanca «PORTES»), sin descripción propia y con una
    derivada que dice otra cosa, se reparte con el concepto del papel."""
    motor = construir()
    ejecutar(motor, "UPDATE contrato_lines_derived SET descripcion_linea = 'TRANSPORTE' "
             "WHERE id = 601")
    ejecutar(motor, "UPDATE albaran_line_valuations SET descripcion_linea = NULL "
             "WHERE id = 13")

    (p2,) = _dividir(motor, 13, (0.5, "03.01"), (0.5, "03.01")).partes

    assert fila(motor, 13)["descripcion_linea"] == "PORTES"
    assert fila(motor, p2)["descripcion_linea"] == "PORTES"


# =================================================================== #
# R16 · toda vía que crea o reapunta deja la fila con fila_a_guardar aplicada
# =================================================================== #
def _pendiente(motor, vid):
    """Lo que ``fila_a_guardar`` cambiaría en la fila tal como quedó."""
    from ruesma_comun.linea_valorada import CamposFila, LineaDeLaFila, cambios_a_guardar

    with Session(motor) as s:
        r = s.execute(text(
            "SELECT lv.descripcion_linea, lv.unidad_contrato, lv.unidad_albaran, "
            "lv.precio_unitario_final, lv.cantidad_albaran, lv.cantidad_convertida, "
            "lv.factor_conversion, cl.id AS cl_id, cl.descripcion_linea AS cl_d, "
            "cl.unidad_medida AS cl_u, cl.precio_unitario AS cl_p, d.id AS d_id, "
            "d.descripcion_linea AS d_d, d.unidad_medida AS d_u, d.precio_unitario AS d_p, "
            "l.concepto FROM albaran_line_valuations lv "
            "LEFT JOIN albaran_contrato_lines_merge cl ON cl.id = lv.matched_contrato_line_id "
            "LEFT JOIN contrato_lines_derived d ON d.id = lv.derived_contrato_line_id "
            "LEFT JOIN albaran_lines_merge l ON l.id = lv.merge_line_id WHERE lv.id = :id"),
            {"id": vid}).mappings().one()
    if r["cl_id"] is not None:
        linea = LineaDeLaFila(True, r["cl_d"], r["cl_u"], r["cl_p"])
    elif r["d_id"] is not None:
        linea = LineaDeLaFila(False, r["d_d"], r["d_u"], r["d_p"])
    else:
        linea = None
    campos = CamposFila(**{c: r[c] for c in (
        "descripcion_linea", "unidad_contrato", "unidad_albaran", "precio_unitario_final",
        "cantidad_albaran", "cantidad_convertida", "factor_conversion")})
    return cambios_a_guardar(campos, linea, r["concepto"])


def test_f078_r16_cada_via_deja_la_fila_materializada():
    motor = construir()
    _blanca_sin_valorar(motor)
    repo = repositorio(motor)
    ejecutar(motor, "UPDATE albaran_line_valuations SET factor_conversion = 1.0, "
             "unidad_albaran = NULL, cantidad_convertida = NULL WHERE id = 13")

    tocadas = []
    repo.set_line_conciliacion(document_id=DOC, valuation_line_id=12, mode="contract_line",
                               matched_contrato_line_id=503)
    tocadas.append(12)
    repo.set_line_conciliacion(document_id=DOC, valuation_line_id=13, mode="nueva")
    tocadas.append(13)
    repo.add_conciliacion_for_merge_line(document_id=DOC, merge_line_id=704, mode="nueva")
    tocadas.append(_fila_de_blanca(motor, 704))
    tocadas += repo.add_valuation_lines_from_contrato(document_id=DOC, lineas=[(501, 2.0)])
    tocadas += [11, *_dividir(motor, 11, (2.0, "01.01"), (6.0, "07.07")).partes]

    assert {vid: _pendiente(motor, vid) for vid in tocadas} == {vid: {} for vid in tocadas}


def test_f078_r16_anadir_linea_nace_vacia_y_asi_se_ve():
    motor = construir()

    vid = repositorio(motor).add_standalone_valuation_line(document_id=DOC)

    assert _columnas(motor, vid, "descripcion_linea", "unidad_contrato", "unidad_albaran",
                     "precio_unitario_final") == (None, None, None, None)


def test_f078_r16_el_patch_no_materializa_lo_vaciado():
    motor = construir()
    ejecutar(motor, "UPDATE albaran_line_valuations SET descripcion_linea = 'X' WHERE id = 11")

    _editar(motor, 11, descripcion=None)

    assert fila(motor, 11)["descripcion_linea"] is None


# =================================================================== #
# T10 · el helper decide Contrato / Nueva como la ficha
# =================================================================== #
def _materializar(motor, vid):
    repo = repositorio(motor)
    with Session(motor) as s:
        repo._materializar_fila_in_session(s, vid)
        s.commit()


def test_f078_r16_materializar_una_contrato_sin_descripcion_toma_la_de_su_linea():
    """Fila 11 (Contrato, blanca «PUERTA EI2-60»): la de su línea, no el papel."""
    motor = construir()

    _materializar(motor, 11)

    assert fila(motor, 11)["descripcion_linea"] == "PUERTA CORTAFUEGOS EI2-60"


def test_f078_r16_materializar_una_nueva_con_blanca_sin_descripcion_toma_el_papel():
    """Fila 13 (Nueva, blanca «PORTES»), derivada «TRANSPORTE»: el papel (P1 = (b))."""
    motor = construir()
    ejecutar(motor, "UPDATE contrato_lines_derived SET descripcion_linea = 'TRANSPORTE' "
             "WHERE id = 601")
    ejecutar(motor, "UPDATE albaran_line_valuations SET descripcion_linea = NULL "
             "WHERE id = 13")

    _materializar(motor, 13)

    assert fila(motor, 13)["descripcion_linea"] == "PORTES"


def test_f078_r16_materializar_una_fila_que_no_existe_no_hace_nada():
    motor = construir()

    _materializar(motor, 999)

    assert [f["id"] for f in filas(motor)] == [11, 12, 13]


def test_f078_r16_materializar_una_manual_sin_blanca_toma_su_derivada():
    """La 386 del caso: manual, sin blanca, derivada «CARGA INCOMPLETA» en M3."""
    motor = construir()
    ejecutar(motor, "INSERT INTO contrato_lines_derived (id, created_by_valuation_id, "
             "descripcion_linea, unidad_medida, precio_unitario, origen) VALUES "
             "(639, 'f065-val-1', 'CARGA INCOMPLETA', 'M3', 12.5, 'manual_override')")
    with Session(motor) as s:
        linea(s, id=386, line_kind="manual", derived_contrato_line_id=639,
              unidad_contrato=None, precio_unitario_final=None, importe_calculado=12.5)
        s.commit()

    _materializar(motor, 386)

    assert _columnas(motor, 386, "descripcion_linea", "unidad_contrato", "unidad_albaran",
                     "precio_unitario_final") == ("CARGA INCOMPLETA", "M3", "M3", 12.5)
