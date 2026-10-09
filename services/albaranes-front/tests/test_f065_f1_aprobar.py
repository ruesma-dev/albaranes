# tests/test_f065_f1_aprobar.py
"""F-065 · fase 1 · R20–R23: lo que se aprueba es lo que sv9 dará de alta.

- R20: no se aprueba (ficha ni listado) con filas sin cantidad o importe, y se
  dice cuáles (posición en la tabla de la ficha).
- R21: la ficha avisa (no bloquea) si la suma de las filas no cuadra con la
  de lo leído en el albarán.
- R22: la ficha sabe cuántas filas manuales descartaría revalorar.
- R23: «Traer líneas contrato» crea filas con su cantidad, válidas para sv9.

Repositorio real sobre SQLite (``f065_bbdd``), plantilla real y portal con un
servicio falso. Sin red ni BBDD.
"""
from __future__ import annotations

import re

import pytest
from domain.models.review_models import MergeDocumentUpdatePayload
from f053_sv4_bbdd import foto
from f065_bbdd import (
    DOC,
    construir,
    documento,
    ejecutar,
    fila,
    linea,
    repositorio,
    total,
)
from sqlalchemy.orm import Session


def _sin_importe(motor, vid):
    ejecutar(motor, "UPDATE albaran_line_valuations SET importe_calculado = NULL "
             "WHERE id = :v", v=vid)


# =================================================================== #
# R20 · no se aprueba con filas sin cantidad o importe
# =================================================================== #
def test_f065_r20_aprobar_del_listado_con_una_fila_sin_importe_no_aprueba():
    from domain.models.review_models import LineasIncompletasError

    motor = construir()
    _sin_importe(motor, 12)
    antes = foto(motor)

    with pytest.raises(LineasIncompletasError) as error:
        repositorio(motor).set_approved(document_id=DOC, approved=True, approved_by="ana")

    assert error.value.posiciones == [2]
    assert error.value.aviso == "Líneas sin cantidad o importe: 2" == str(error.value)
    assert foto(motor) == antes


def test_f065_r20_guardar_y_aprobar_con_filas_sin_cantidad_no_aprueba(monkeypatch):
    from domain.models.review_models import LineasIncompletasError

    motor = construir()
    ejecutar(motor, "UPDATE albaran_line_valuations SET cantidad_albaran = NULL, "
             "cantidad_convertida = NULL WHERE id = 11")
    with Session(motor) as s:
        # Una traída del contrato con la cantidad en blanco (como las de antes).
        linea(s, id=30, merge_line_id=None, line_kind="manual", matched_contrato_line_id=503,
              cantidad_albaran=None, cantidad_convertida=None, importe_calculado=None)
        s.commit()
    repo = repositorio(motor)
    monkeypatch.setattr(repo, "get_document_detail", lambda document_id: "detalle")

    with pytest.raises(LineasIncompletasError) as error:
        repo.update_document_y_transicion(
            document_id=DOC, payload=MergeDocumentUpdatePayload(approved=True, numero_albaran="Z"))

    assert error.value.aviso == "Líneas sin cantidad o importe: 1, 4"
    assert documento(motor)["approved"] in (0, False)
    assert documento(motor)["numero_albaran"] != "Z"


def test_f065_r20_la_convertida_basta_aunque_falte_la_del_albaran():
    motor = construir()
    ejecutar(motor, "UPDATE albaran_line_valuations SET cantidad_albaran = NULL "
             "WHERE id = 11")

    assert repositorio(motor).set_approved(document_id=DOC, approved=True, approved_by="ana")


def test_f065_r20_las_filas_que_la_ficha_no_pinta_no_cuentan_ni_numeran():
    """Una fila sin línea de contrato ni derivada no sale en la tabla: ni se
    puede corregir ni ocupa posición."""
    from domain.models.review_models import LineasIncompletasError

    motor = construir()
    with Session(motor) as s:
        linea(s, id=29, merge_line_id=None, line_kind="manual", importe_calculado=None)
        linea(s, id=31, merge_line_id=None, line_kind="manual", derived_contrato_line_id=601,
              importe_calculado=None)
        s.commit()

    with pytest.raises(LineasIncompletasError) as error:
        repositorio(motor).set_approved(document_id=DOC, approved=True, approved_by="ana")

    assert error.value.posiciones == [4]


def test_f065_r20_orden_de_la_ficha_base_sus_sinteticas_y_luego_las_sueltas():
    """Mismo orden que ``_load_valuation_in_session`` + ``_build_display_lines``:
    cada blanca por su ``line_index`` con sus sintéticas detrás; al final las
    huérfanas, agrupadas por padre en orden de aparición (las sueltas, de
    padre nulo, van antes que las sintéticas porque el cargador las lee
    antes)."""
    from domain.models.review_models import orden_filas_ficha

    filas = [
        {"id": 30, "merge_line_id": None, "parent_merge_line_id": None, "line_kind": "manual"},
        {"id": 13, "merge_line_id": 703, "parent_merge_line_id": None,
         "line_kind": "from_albaran"},
        {"id": 14, "merge_line_id": None, "parent_merge_line_id": 701,
         "line_kind": "synthetic_modifier"},
        {"id": 11, "merge_line_id": 701, "parent_merge_line_id": None, "line_kind": None},
        {"id": 15, "merge_line_id": None, "parent_merge_line_id": 999,
         "line_kind": "synthetic_modifier"},
        {"id": 16, "merge_line_id": None, "parent_merge_line_id": 702,
         "line_kind": "synthetic_modifier"},
        {"id": 12, "merge_line_id": 702, "parent_merge_line_id": None,
         "line_kind": "from_albaran"},
    ]

    assert [f["id"] for f in orden_filas_ficha([701, 702, 703], filas)] == [
        11, 14, 12, 16, 13, 30, 15]


def test_f065_r20_el_portal_lo_dice_al_aprobar_desde_el_listado(monkeypatch):
    from domain.models.review_models import LineasIncompletasError
    from test_f065_f1_cabecera import _cliente

    class _Servicio:
        def initialize(self):
            return True

        def approve_document(self, **_):
            raise LineasIncompletasError(DOC, [3, 5])

    respuesta = _cliente(monkeypatch, _Servicio()).post(
        f"/documents/{DOC}/approve", data={"redirect_query": "approved=pending"})

    assert respuesta.status_code == 303
    destino = respuesta.headers["location"]
    assert destino.startswith("/documents?approved=pending&")
    assert "L%C3%ADneas+sin+cantidad+o+importe%3A+3%2C+5" in destino


def test_f065_r20_el_portal_responde_409_al_guardar_y_aprobar(monkeypatch):
    from domain.models.review_models import LineasIncompletasError
    from test_f065_f1_cabecera import _cliente

    class _Servicio:
        def initialize(self):
            return True

        def guardar(self, **_):
            raise LineasIncompletasError(DOC, [3, 5])

    respuesta = _cliente(monkeypatch, _Servicio()).put(
        f"/api/documents/{DOC}", json={"approved": True})

    assert respuesta.status_code == 409
    assert respuesta.json()["detail"] == "Líneas sin cantidad o importe: 3, 5"


# =================================================================== #
# R21 · la suma de las filas frente a la de lo leído
# =================================================================== #
@pytest.mark.parametrize(("filas", "leida", "aviso"), [
    (1890.0, 2120.0, True),
    (2120.0, 2120.0, False),
    (2120.004, 2120.0, False),
    (2120.006, 2120.0, True),
    (2120.01, 2120.0, True),
    (2119.99, 2120.0, True),
    (2120.0, None, False),
    (None, 2120.0, False),
])
def test_f065_r21_dominio_aviso_suma(filas, leida, aviso):
    from domain.models.review_models import aviso_suma_importes

    texto = aviso_suma_importes(filas, leida)

    assert (texto is not None) is aviso
    if aviso:
        assert "no cuadra" in texto and "¿Aprobar igualmente?" in texto


def test_f065_r21_dominio_aviso_suma_con_las_dos_cifras():
    from domain.models.review_models import aviso_suma_importes

    assert aviso_suma_importes(1890.0, 2120.0) == (
        "La suma de las líneas (1.890,00 €) no cuadra con la del albarán "
        "(2.120,00 €). ¿Aprobar igualmente?"
    )


def _detalle(motor):
    from infrastructure.database.orm_models import AlbaranDocumentMergeOrm

    repo = repositorio(motor)
    with Session(motor) as s:
        doc = s.get(AlbaranDocumentMergeOrm, DOC)
        _ = doc.lines
        valoracion = repo._load_valuation_in_session(session=s, document_id=DOC)
        mapa = repo._load_conciliation_map_in_session(session=s, valuation=valoracion)
        return repo._build_merge_detail(
            merge_doc=doc, available_views=[], provider_snapshots=[], contratos=[],
            selected_contrato_codigo=None, valuation=valoracion,
            conciliation_by_valuation_line_id=mapa,
        )


def test_f065_r21_la_ficha_lleva_las_dos_sumas_y_el_aviso():
    motor = construir()
    ejecutar(motor, "UPDATE albaran_line_valuations SET importe_calculado = 690 WHERE id = 11")

    detalle = _detalle(motor)

    assert detalle.suma_filas == pytest.approx(690 + 1150 + 50)
    assert detalle.suma_leida == pytest.approx(2120.0)
    assert "1.890,00 €" in detalle.aviso_suma


def test_f065_r21_sin_importes_leidos_no_hay_aviso():
    motor = construir()
    ejecutar(motor, "UPDATE albaran_lines_merge SET precio_neto = NULL")

    detalle = _detalle(motor)

    assert detalle.suma_leida is None and detalle.aviso_suma is None


def test_f065_r21_plantilla_el_boton_de_aprobar_lleva_el_aviso(
    render_detalle, documento_detalle, linea_valorada, fila_detalle,
):
    doc = documento_detalle(lineas_valoracion=[linea_valorada()], display=[fila_detalle()])
    html = render_detalle(doc.model_copy(update={"suma_filas": 1.0, "suma_leida": 2.0}))

    boton = re.search(r'<button[^>]*id="approve-btn"[^>]*>', html).group(0)
    assert 'data-aviso-suma="La suma de las líneas (1,00 €)' in boton


# =================================================================== #
# R22 · cuántas filas manuales descartaría revalorar
# =================================================================== #
def test_f065_r22_la_ficha_cuenta_las_filas_manuales():
    motor = construir()
    assert _detalle(motor).n_filas_manuales == 0

    ejecutar(motor, "UPDATE albaran_line_valuations SET bloqueada = 1 WHERE id = 11")
    ejecutar(motor, "UPDATE albaran_line_valuations SET partida_action = 'almacen_elegido' "
             "WHERE id = 12")
    ejecutar(motor, "UPDATE contrato_lines_derived SET origen = 'manual_override' "
             "WHERE id = 601")

    assert _detalle(motor).n_filas_manuales == 3


def test_f065_r22_el_json_de_la_ficha_lo_lleva():
    """El JS lo lee del JSON incrustado (``window.__documentData``)."""
    detalle = _detalle(construir())

    assert "n_filas_manuales" in detalle.model_dump()


# =================================================================== #
# R23 · traer líneas de contrato con su cantidad
# =================================================================== #
def test_f065_r23_traer_crea_filas_contrato_validas_para_sv9():
    motor = construir()

    creadas = repositorio(motor).add_valuation_lines_from_contrato(
        document_id=DOC, lineas=[(503, 5.0), (501, 2.0)])

    assert len(creadas) == 2
    f = fila(motor, creadas[0])
    assert f["matched_contrato_line_id"] == 503
    assert (f["cantidad_albaran"], f["cantidad_convertida"], f["factor_conversion"]) == (
        5.0, 5.0, 1.0)
    assert f["importe_calculado"] == pytest.approx(575.0)
    assert f["precio_unitario_final"] == pytest.approx(115.0)
    assert f["codigo_partida_final"] == "01.03"
    assert f["unidad_contrato"] == "UD"
    assert f["line_kind"] == "manual" and f["merge_line_id"] is None
    assert total(motor) == pytest.approx(2120 + 575 + 230)


@pytest.mark.parametrize("cantidad", [None, 0.0])
def test_f065_r23_sin_cantidad_o_con_cero_no_se_trae_nada(cantidad):
    motor = construir()
    antes = foto(motor)

    with pytest.raises(ValueError):
        repositorio(motor).add_valuation_lines_from_contrato(
            document_id=DOC, lineas=[(503, 5.0), (501, cantidad)])

    assert foto(motor) == antes


def test_f065_r23_una_linea_de_otro_contrato_se_ignora():
    motor = construir()
    ejecutar(motor, "INSERT INTO albaran_contratos_merge (id, document_id, codigo_contrato, "
             "fetched_at_utc) VALUES (2, 'f065-doc-0000-0000-000000000999', 'OTRO', 't')")
    ejecutar(motor, "INSERT INTO albaran_contrato_lines_merge (id, contrato_id, "
             "codigo_contrato, precio_unitario, fetched_at_utc) VALUES (900, 2, 'OTRO', 1, 't')")

    assert repositorio(motor).add_valuation_lines_from_contrato(
        document_id=DOC, lineas=[(900, 1.0)]) == []


class _ServicioTraer:
    def __init__(self):
        self.lineas = None

    def initialize(self):
        return True

    def add_valuation_lines_from_contrato(self, *, document_id, lineas):
        self.lineas = lineas
        return len(lineas)


@pytest.mark.parametrize("cuerpo", [
    {"contrato_line_ids": [503]},
    {"lineas": [{"contrato_line_id": 503}]},
    {"lineas": [{"contrato_line_id": 503, "cantidad": 0}]},
    {"lineas": [{"contrato_line_id": 503, "cantidad": "abc"}]},
    {"lineas": []},
])
def test_f065_r23_el_portal_exige_la_cantidad(monkeypatch, cuerpo):
    from test_f065_f1_cabecera import _cliente

    servicio = _ServicioTraer()

    respuesta = _cliente(monkeypatch, servicio).post(
        f"/api/documents/{DOC}/lines/from-contrato", json=cuerpo)

    assert respuesta.status_code == 422
    assert servicio.lineas is None


def test_f065_r23_el_portal_pasa_cada_linea_con_su_cantidad(monkeypatch):
    from test_f065_f1_cabecera import _cliente

    servicio = _ServicioTraer()

    respuesta = _cliente(monkeypatch, servicio).post(
        f"/api/documents/{DOC}/lines/from-contrato",
        json={"lineas": [{"contrato_line_id": 503, "cantidad": "5,5"},
                         {"contrato_line_id": "501", "cantidad": 2}]})

    assert respuesta.status_code == 200, respuesta.text
    assert respuesta.json()["created"] == 2
    assert servicio.lineas == [(503, 5.5), (501, 2.0)]


def test_f065_r23_el_servicio_deja_deshacer_lo_traido():
    import json

    from application.services.review_service import ReviewService
    from sqlalchemy import text

    motor = construir()

    creadas = ReviewService(repositorio(motor), "ana").add_valuation_lines_from_contrato(
        document_id=DOC, lineas=[(503, 5.0)])

    assert creadas == 1
    with Session(motor) as s:
        (payload,) = s.execute(text(
            "SELECT payload FROM undo_log WHERE document_id = :d"), {"d": DOC}).scalars().all()
    entrada = json.loads(payload)
    assert [d["table"] for d in entrada["delete_created"]] == ["albaran_line_valuations"]
    assert [r["table"] for r in entrada["restore"]] == ["albaran_valuations"]
    assert entrada["restore"][0]["values"]["total_valorado"] == 2120.0


def test_f065_r22_sin_valoracion_no_hay_filas_manuales():
    from domain.models.review_models import DocumentDetailPayload

    detalle = DocumentDetailPayload(
        id="x", source_filename="x.pdf", provider_origin="merge", model_name="m",
        created_at_utc="2026-10-09",
    )

    assert detalle.n_filas_manuales == 0
    assert detalle.suma_filas is None and detalle.suma_leida is None
