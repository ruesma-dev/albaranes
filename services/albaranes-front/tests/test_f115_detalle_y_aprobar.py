# tests/test_f115_detalle_y_aprobar.py
"""F-115 R12, R13 · la ficha solo ofrece contratos del albarán y no se aprueba
la valoración de otro contrato.

- R12: el bloque y el desplegable de contratos listan solo los contratos del
  albarán (R1 de comun); las líneas de contrato, solo si la selección no es
  ajena. Las filas del proveedor anterior siguen en BBDD (D6), ocultas.
- R13 (D4): aprobar (ficha o listado) con la valoración vigente de un
  contrato distinto del seleccionado ⇒ 409 con el aviso, sin cambiar nada.
  Caso (h) de R22.

Repositorio real sobre SQLite (``f065_bbdd``: METALFIRE, CIF ``B12345678``,
obra ``0404``, contrato ``CTSU25/0359`` con fila legada sin CIF) y portal con
un servicio falso. Sin red ni BBDD.
"""
from __future__ import annotations

import pytest
from domain.models.review_models import MergeDocumentUpdatePayload
from f053_sv4_bbdd import foto
from f065_bbdd import CONTRATO, DOC, construir, documento, ejecutar, repositorio
from sqlalchemy import text
from sqlalchemy.orm import Session

CIF_OTRO = "A11111111"


def _con_contrato_de_otro_proveedor(motor):
    with Session(motor) as s:
        s.execute(text(
            "INSERT INTO albaran_contratos_merge (id, document_id, codigo_contrato, "
            "cif_proveedor, codigo_obra, fetched_at_utc) VALUES "
            "(2, :d, 'CTA/0001', :cif, '0404', 't'), "
            "(3, :d, 'CTX/0700', 'B12345678', '0700', 't')"),
            {"d": DOC, "cif": CIF_OTRO})
        s.execute(text(
            "INSERT INTO albaran_contrato_lines_merge (id, contrato_id, codigo_contrato, "
            "codigo_producto, descripcion_linea, unidad_medida, precio_unitario, "
            "codigo_partida, fetched_at_utc, sigrid_ide) VALUES "
            "(504, 2, 'CTA/0001', 'X', 'PUERTA DEL OTRO', 'UD', 99.0, '09.09', 't', 900504)"))
        s.commit()


def _seleccionar(motor, codigo):
    ejecutar(motor, "UPDATE albaran_documents_merge SET selected_contrato_codigo = :c "
             "WHERE id = :d", c=codigo, d=DOC)


# =================================================================== #
# R12 · la ficha
# =================================================================== #
def test_f115_r12_el_desplegable_solo_lista_los_contratos_del_albaran():
    motor = construir()
    _con_contrato_de_otro_proveedor(motor)
    _seleccionar(motor, CONTRATO)
    detalle = repositorio(motor).get_document_detail(DOC)
    assert [c.codigo_contrato for c in detalle.contratos] == [CONTRATO]
    assert {ln.codigo_contrato for ln in detalle.contrato_lines} == {CONTRATO}


def test_f115_r12_seleccion_ajena_no_carga_sus_lineas():
    motor = construir()
    _con_contrato_de_otro_proveedor(motor)
    _seleccionar(motor, "CTA/0001")
    detalle = repositorio(motor).get_document_detail(DOC)
    assert detalle.contrato_lines == []
    assert "CTA/0001" not in [c.codigo_contrato for c in detalle.contratos]


def test_f115_r12_las_filas_del_anterior_siguen_en_bbdd():
    """D6: se ocultan, no se borran."""
    motor = construir()
    _con_contrato_de_otro_proveedor(motor)
    repositorio(motor).get_document_detail(DOC)
    with Session(motor) as s:
        assert s.execute(text(
            "SELECT count(*) FROM albaran_contratos_merge WHERE document_id = :d"),
            {"d": DOC}).scalar_one() == 3


def test_f115_r12_contrato_compartido_de_otro_documento_se_filtra_igual():
    motor = construir()
    ejecutar(motor, "UPDATE albaran_contratos_merge SET document_id = 'otro', "
             "cif_proveedor = :c WHERE id = 1", c=CIF_OTRO)
    _seleccionar(motor, CONTRATO)
    detalle = repositorio(motor).get_document_detail(DOC)
    assert detalle.contratos == []
    assert detalle.contrato_lines == []


def test_f115_r12_contrato_compartido_del_mismo_proveedor_se_sigue_viendo():
    motor = construir()
    ejecutar(motor, "UPDATE albaran_contratos_merge SET document_id = 'otro', "
             "cif_proveedor = 'b-12345678', codigo_obra = '404' WHERE id = 1")
    _seleccionar(motor, CONTRATO)
    detalle = repositorio(motor).get_document_detail(DOC)
    assert [c.codigo_contrato for c in detalle.contratos] == [CONTRATO]
    assert detalle.contrato_lines


# =================================================================== #
# R13 · aprobar con la valoración de otro contrato · caso (h)
# =================================================================== #
def test_f115_r13_h_guardar_y_aprobar_con_valoracion_de_a_y_seleccion_nula_409():
    from domain.models.alta_sigrid_models import ValoracionDeOtroContratoError

    motor = construir()
    antes = foto(motor)
    with pytest.raises(ValoracionDeOtroContratoError) as error:
        repositorio(motor).update_document_y_transicion(
            document_id=DOC, payload=MergeDocumentUpdatePayload(approved=True, numero_albaran="Z"),
        )
    assert error.value.aviso == (
        f"La valoración es del contrato {CONTRATO} y el albarán tiene ningún contrato: "
        "espera a que termine la valoración o pulsa Revalorar"
    )
    assert str(error.value) == error.value.aviso
    assert foto(motor) == antes
    assert documento(motor)["numero_albaran"] != "Z"


def test_f115_r13_aprobar_del_listado_con_otro_contrato_409_sin_cambiar_nada():
    from domain.models.alta_sigrid_models import ValoracionDeOtroContratoError

    motor = construir()
    _con_contrato_de_otro_proveedor(motor)
    _seleccionar(motor, "CTA/0001")
    antes = foto(motor)
    with pytest.raises(ValoracionDeOtroContratoError) as error:
        repositorio(motor).set_approved(document_id=DOC, approved=True, approved_by="ana")
    assert "el albarán tiene CTA/0001" in error.value.aviso
    assert foto(motor) == antes


def test_f115_r13_mismo_contrato_recortado_aprueba():
    motor = construir()
    _seleccionar(motor, CONTRATO)
    ejecutar(motor, "UPDATE albaran_valuations SET contrato_codigo = :c WHERE document_id = :d",
             c=f" {CONTRATO} ", d=DOC)
    assert repositorio(motor).set_approved(document_id=DOC, approved=True, approved_by="ana")
    assert documento(motor)["approved"] in (1, True)


def test_f115_r13_valoracion_sin_contrato_y_sin_seleccion_aprueba():
    motor = construir()
    ejecutar(motor, "UPDATE albaran_valuations SET contrato_codigo = NULL WHERE document_id = :d",
             d=DOC)
    _seleccionar(motor, None)
    # Sin contrato, las filas necesitan su descripción para aprobarse (F-078 R17).
    ejecutar(motor, "UPDATE albaran_line_valuations SET descripcion_linea = 'PUERTA'")
    assert repositorio(motor).set_approved(document_id=DOC, approved=True, approved_by="ana")


def test_f115_r13_valoracion_sin_contrato_y_con_seleccion_409():
    from domain.models.alta_sigrid_models import ValoracionDeOtroContratoError

    motor = construir()
    _seleccionar(motor, CONTRATO)
    ejecutar(motor, "UPDATE albaran_valuations SET contrato_codigo = '' WHERE document_id = :d",
             d=DOC)
    ejecutar(motor, "UPDATE albaran_line_valuations SET descripcion_linea = 'PUERTA'")
    with pytest.raises(ValoracionDeOtroContratoError) as error:
        repositorio(motor).set_approved(document_id=DOC, approved=True, approved_by="ana")
    assert error.value.aviso.startswith("La valoración es sin contrato y el albarán tiene")


def test_f115_r13_guardar_y_aprobar_con_el_mismo_contrato_aprueba():
    motor = construir()
    _seleccionar(motor, CONTRATO)
    _, paso = repositorio(motor).update_document_y_transicion(
        document_id=DOC,
        payload=MergeDocumentUpdatePayload(
            approved=True, selected_contrato_codigo=CONTRATO,
            proveedor_cif="B12345678", obra_codigo="0404",
            # (F-108 R11) La ficha manda su fecha y su número.
            fecha="2026-10-08", numero_albaran="A-1",
        ),
    )
    assert paso is True


def test_f115_r13_guardar_sin_aprobar_no_lo_mira():
    motor = construir()
    detalle, paso = repositorio(motor).update_document_y_transicion(
        document_id=DOC, payload=MergeDocumentUpdatePayload(numero_albaran="Z"),
    )
    assert paso is False
    assert documento(motor)["numero_albaran"] == "Z"


def test_f115_r13_el_portal_responde_409_al_guardar_y_aprobar(monkeypatch):
    from domain.models.alta_sigrid_models import ValoracionDeOtroContratoError
    from test_f065_f1_cabecera import _cliente

    class _Servicio:
        def initialize(self):
            return True

        def guardar(self, **_):
            raise ValoracionDeOtroContratoError(DOC, "CTA/0001", None)

    respuesta = _cliente(monkeypatch, _Servicio()).put(
        f"/api/documents/{DOC}", json={"approved": True})
    assert respuesta.status_code == 409
    assert respuesta.json()["detail"].startswith("La valoración es del contrato CTA/0001")


def test_f115_r13_el_portal_lo_dice_al_aprobar_desde_el_listado(monkeypatch):
    from domain.models.alta_sigrid_models import ValoracionDeOtroContratoError
    from test_f065_f1_cabecera import _cliente

    class _Servicio:
        def initialize(self):
            return True

        def approve_document(self, **_):
            raise ValoracionDeOtroContratoError(DOC, "CTA/0001", "CTB/0002")

    respuesta = _cliente(monkeypatch, _Servicio()).post(
        f"/documents/{DOC}/approve", data={"redirect_query": "approved=pending"})
    assert respuesta.status_code == 303
    assert "CTB%2F0002" in respuesta.headers["location"]
