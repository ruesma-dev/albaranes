# tests/test_f078_aprobar.py
"""F-078 · R17, R20 · aprobar.

- R17: no se aprueba (ficha ni listado) si alguna fila a registrar SIN
  vincular (``es_linea_vinculada`` de comun) no tiene descripción: «Líneas sin
  descripción: 3, 5» (posiciones de la tabla, como F-065 R20), sin publicar el
  alta. sv9 la rechazaría con ``falta_descripcion`` (el caso de la 386).
- R20: el producto por defecto no se guarda; el que pinta sv4 es el que manda
  sv9 (misma función de comun y mismos datos) en una fila ``manual``, una
  ``reparto`` y una ``from_albaran`` sin elegido.

Repositorio real sobre SQLite (``f065_bbdd``: METALFIRE) y el portal con un
servicio falso. Sin red.
"""
from __future__ import annotations

from datetime import UTC, datetime

import pytest
from domain.models.review_models import MergeDocumentUpdatePayload
from f053_sv4_bbdd import foto
from f065_bbdd import DOC, construir, documento, ejecutar, linea, repositorio
from sqlalchemy import text
from sqlalchemy.orm import Session


def _con_descripciones(motor):
    """Las tres filas de METALFIRE como las deja F-078 (con descripción)."""
    ejecutar(motor, "UPDATE albaran_line_valuations SET descripcion_linea = 'PORTES' "
             "WHERE id = 13")


def _sin_descripcion(motor, vid=13):
    ejecutar(motor, "UPDATE albaran_line_valuations SET descripcion_linea = NULL "
             "WHERE id = :v", v=vid)


def _aprobar(motor):
    return repositorio(motor).set_approved(document_id=DOC, approved=True, approved_by="ana")


# =================================================================== #
# R17 · sin descripción no se aprueba
# =================================================================== #
def test_f078_r17_una_nueva_sin_descripcion_no_se_aprueba_y_nada_cambia():
    from domain.models.review_models import LineasIncompletasError

    motor = construir()
    _sin_descripcion(motor)                  # la 13 (Nueva, sin vincular) sin texto
    antes = foto(motor)

    with pytest.raises(LineasIncompletasError) as error:
        _aprobar(motor)

    assert error.value.sin_descripcion == [3]
    assert error.value.aviso == "Líneas sin descripción: 3" == str(error.value)
    assert foto(motor) == antes


@pytest.mark.parametrize("texto", [None, "", "   "])
def test_f078_r17_vacia_o_solo_espacios_cuenta_como_sin_descripcion(texto):
    from domain.models.review_models import LineasIncompletasError

    motor = construir()
    ejecutar(motor, "UPDATE albaran_line_valuations SET descripcion_linea = :t "
             "WHERE id = 13", t=texto)

    with pytest.raises(LineasIncompletasError):
        _aprobar(motor)


def test_f078_r17_con_descripcion_se_aprueba():
    motor = construir()
    _con_descripciones(motor)

    assert _aprobar(motor)
    assert documento(motor)["approved"] in (1, True)


def test_f078_r17_las_vinculadas_no_necesitan_descripcion():
    """11 y 12 casan con líneas del contrato de la valoración con ``sigrid_ide``:
    sv9 las manda por ``ctrpro_ide`` y la descripción es la de Sigrid."""
    motor = construir()
    _con_descripciones(motor)
    ejecutar(motor, "UPDATE albaran_line_valuations SET descripcion_linea = NULL "
             "WHERE id IN (11, 12)")

    assert _aprobar(motor)


def test_f078_r17_casada_con_una_linea_sin_sigrid_ide_es_sin_vincular():
    from domain.models.review_models import LineasIncompletasError

    motor = construir()
    _con_descripciones(motor)
    ejecutar(motor, "UPDATE albaran_contrato_lines_merge SET sigrid_ide = NULL WHERE id = 502")

    with pytest.raises(LineasIncompletasError) as error:
        _aprobar(motor)

    assert error.value.sin_descripcion == [2]


def test_f078_r17_casada_con_una_linea_de_otro_contrato_es_sin_vincular():
    from domain.models.review_models import LineasIncompletasError

    motor = construir()
    _con_descripciones(motor)
    ejecutar(motor, "UPDATE albaran_contrato_lines_merge SET codigo_contrato = 'OTRO' "
             "WHERE id = 501")

    with pytest.raises(LineasIncompletasError) as error:
        _aprobar(motor)

    assert error.value.sin_descripcion == [1]


@pytest.mark.parametrize("importe", [0.0, 1e-10, -1e-10])
def test_f078_r17_una_fila_que_no_se_registra_no_necesita_descripcion(importe):
    """Importe 0: sv9 no la manda (F-053 R13)."""
    motor = construir()
    _sin_descripcion(motor)
    ejecutar(motor, "UPDATE albaran_line_valuations SET importe_calculado = :i "
             "WHERE id = 13", i=importe)

    assert _aprobar(motor)


def test_f078_r17_junto_a_las_de_f065_y_desde_guardar_y_aprobar(monkeypatch):
    from domain.models.review_models import LineasIncompletasError

    motor = construir()
    _sin_descripcion(motor)
    ejecutar(motor, "UPDATE albaran_line_valuations SET importe_calculado = NULL "
             "WHERE id = 12")
    with Session(motor) as s:
        # La 386 del caso: manual, Nueva sin blanca y sin descripción.
        s.execute(text(
            "INSERT INTO contrato_lines_derived (id, created_by_valuation_id, "
            "descripcion_linea, unidad_medida, precio_unitario, origen) VALUES "
            "(639, 'f065-val-1', 'CARGA INCOMPLETA', 'M3', 12.5, 'manual_override')"))
        # F-106 R16 (fixture declarado en R31, humano 2026-10-29): P 12,5, el
        # de su derivada, para que cuadre (1 × 12,5); antes tomaba el 115 por
        # defecto de ``linea()`` y la fila no cuadraba.
        linea(s, id=386, line_kind="manual", derived_contrato_line_id=639,
              precio_unitario_final=12.5, importe_calculado=12.5,
              codigo_partida_final=None)
        s.commit()
    repo = repositorio(motor)
    monkeypatch.setattr(repo, "get_document_detail", lambda document_id: "detalle")

    with pytest.raises(LineasIncompletasError) as error:
        repo.update_document_y_transicion(
            document_id=DOC, payload=MergeDocumentUpdatePayload(approved=True))

    assert error.value.aviso == (
        "Líneas sin cantidad o importe: 2. Líneas sin descripción: 3, 4")
    assert documento(motor)["approved"] in (0, False)


def test_f078_r17_el_portal_lo_dice_al_aprobar_desde_el_listado(monkeypatch):
    from domain.models.review_models import LineasIncompletasError
    from test_f065_f1_cabecera import _cliente

    class _Servicio:
        def initialize(self):
            return True

        def approve_document(self, **_):
            raise LineasIncompletasError(DOC, [], sin_descripcion=[3, 5])

    respuesta = _cliente(monkeypatch, _Servicio()).post(
        f"/documents/{DOC}/approve", data={"redirect_query": "approved=pending"})

    assert respuesta.status_code == 303
    assert "L%C3%ADneas+sin+descripci%C3%B3n%3A+3%2C+5" in respuesta.headers["location"]


def test_f078_r17_el_portal_responde_409_al_guardar_y_aprobar(monkeypatch):
    from domain.models.review_models import LineasIncompletasError
    from test_f065_f1_cabecera import _cliente

    class _Servicio:
        def initialize(self):
            return True

        def guardar(self, **_):
            raise LineasIncompletasError(DOC, [], sin_descripcion=[3, 5])

    respuesta = _cliente(monkeypatch, _Servicio()).put(
        f"/api/documents/{DOC}", json={"approved": True})

    assert respuesta.status_code == 409
    assert respuesta.json()["detail"] == "Líneas sin descripción: 3, 5"


# =================================================================== #
# R20 · el producto por defecto: el que pinta sv4 = el que manda sv9
# =================================================================== #
def test_f078_r20_producto_pintado_es_el_de_sv9_en_manual_reparto_y_from_albaran():
    """sv9 (``validador_alta._linea_peticion``) manda, en una sin vincular,
    ``producto_efectivo(producto_sigrid, familia de su blanca, clasificación del
    documento, mapeo)``; sv4 lo pinta con ``ReviewService.productos_sigrid``. Con
    los mismos datos dan lo mismo: no hace falta guardarlo (P5)."""
    from application.services.review_service import ReviewService
    from domain.models.alta_sigrid_models import ConfigAltaSigrid
    from ruesma_comun.alta_sigrid import clasificacion_documento, producto_efectivo

    motor = construir()
    _con_descripciones(motor)
    with Session(motor) as s:
        s.execute(text("UPDATE albaran_lines_merge SET contexto_linea_json = "
                       "'{\"tipo_familia\": \"alquiler_maquinaria\"}' WHERE id = 703"))
        s.execute(text("UPDATE albaran_documents_merge SET tipologia = 'ferreteria' "
                       "WHERE id = :d"), {"d": DOC})
        s.execute(text(
            "INSERT INTO contrato_lines_derived (id, created_by_valuation_id, "
            "descripcion_linea, unidad_medida, precio_unitario, origen) VALUES "
            "(640, 'f065-val-1', 'CARGA INCOMPLETA', 'M3', 12.5, 'manual_override'), "
            "(641, 'f065-val-1', 'PUERTA EI2-90', 'UD', 115.0, 'manual_override')"))
        linea(s, id=386, line_kind="manual", derived_contrato_line_id=640,
              importe_calculado=12.5, descripcion_linea="CARGA INCOMPLETA")
        linea(s, id=387, line_kind="reparto", parent_merge_line_id=702,
              derived_contrato_line_id=641, importe_calculado=115.0,
              descripcion_linea="PUERTA EI2-90")
        s.commit()
    config = ConfigAltaSigrid(desde=datetime(2026, 10, 1, tzinfo=UTC))

    pintados = ReviewService(repositorio(motor), "revisor", None, config).productos_sigrid(
        DOC, clasificacion_documento("ferreteria", False))

    clasificacion = clasificacion_documento("ferreteria", False)   # la que lee sv9
    de_sv9 = {
        13: producto_efectivo(None, "alquiler_maquinaria", clasificacion, config.mapeo),
        386: producto_efectivo(None, None, clasificacion, config.mapeo),
        387: producto_efectivo(None, None, clasificacion, config.mapeo),
    }
    assert {vid: pintados[vid].codigo for vid in de_sv9} == de_sv9
    assert all(pintados[vid].por_defecto for vid in de_sv9)
    assert de_sv9[13] != de_sv9[386]           # la familia de la blanca cuenta
    with Session(motor) as s:
        guardados = s.execute(text(
            "SELECT producto_sigrid FROM albaran_line_valuations "
            "WHERE id IN (13, 386, 387)")).scalars().all()
    assert guardados == [None, None, None]
