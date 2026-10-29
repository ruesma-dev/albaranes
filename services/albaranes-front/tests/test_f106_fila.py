# tests/test_f106_fila.py
"""F-106 R4–R10, R16, R32 a: editar una fila recalcula lo que toca y la deja cuadrando.

Regla del humano (D1): cantidad, precio o dto ⇒ importe; importe ⇒ precio (el
dto se queda); las columnas grises (blancas del merge) nunca se tocan.

Dominio puro (``recalculo_de_fila``, el cuerpo del PATCH, el aviso de aprobar)
y repositorio real sobre SQLite (``f065_bbdd``). Sin red ni BBDD.
"""
from __future__ import annotations

import pytest
from pydantic import ValidationError


# =================================================================== #
# Dominio · recalculo_de_fila (tabla de design §4)
# =================================================================== #
@pytest.mark.parametrize(
    ("cambios", "cuadrar", "no_cuadra", "esperado"),
    [
        ({"cantidad": 48.0}, None, False, "importe"),
        ({"precio_unitario": 2.0}, None, False, "importe"),
        ({"descuento": 5.0}, None, True, "importe"),
        ({"importe": 104.16}, None, False, "precio"),
        ({"importe": 104.16, "cantidad": 48.0}, None, False, "precio"),
        ({"importe": 104.16, "descuento": 7.0}, None, False, "precio"),
        ({"codigo_partida": "01.02"}, None, True, None),
        ({}, None, True, None),
        ({}, "importe", True, "importe"),
        ({}, "precio", True, "precio"),
        ({}, "importe", False, None),
        ({}, "precio", False, None),
        ({}, "precio", None, None),
        ({"codigo_partida": "01.02"}, "precio", True, "precio"),
        # Lo tecleado manda sobre el botón.
        ({"cantidad": 48.0}, "precio", True, "importe"),
        ({"importe": 1.0}, "importe", True, "precio"),
    ],
)
def test_f106_dominio_r9_recalculo_de_fila(cambios, cuadrar, no_cuadra, esperado):
    from domain.models.review_models import recalculo_de_fila

    assert recalculo_de_fila(cambios=cambios, cuadrar=cuadrar, no_cuadra=no_cuadra) == esperado


# =================================================================== #
# Dominio · ConciliacionEditBody (R4, R7)
# =================================================================== #
def test_f106_dominio_r4_importe_con_coma_decimal():
    from domain.models.review_models import ConciliacionEditBody

    cuerpo = ConciliacionEditBody.model_validate({"importe": "1.104,16"})
    assert cuerpo.importe == pytest.approx(1104.16)
    assert cuerpo.campos() == {"importe": pytest.approx(1104.16)}


@pytest.mark.parametrize("valor", ["NaN", "Infinity", "-Infinity", "doce", float("nan"),
                                   float("inf")])
def test_f106_dominio_r4_importe_ilegible_es_422(valor):
    from domain.models.review_models import ConciliacionEditBody

    with pytest.raises(ValidationError):
        ConciliacionEditBody.model_validate({"importe": valor})


@pytest.mark.parametrize("valor", [None, "", "—"])
def test_f106_dominio_r4_importe_vacio_es_422(valor):
    from domain.models.review_models import ConciliacionEditBody

    with pytest.raises(ValidationError, match="importe"):
        ConciliacionEditBody.model_validate({"importe": valor})


@pytest.mark.parametrize("valor", ["importe", "precio"])
def test_f106_dominio_r4_cuadrar_valido_y_fuera_de_campos(valor):
    from domain.models.review_models import ConciliacionEditBody

    cuerpo = ConciliacionEditBody.model_validate({"cuadrar": valor})
    assert cuerpo.cuadrar == valor
    assert cuerpo.campos() == {}
    cuerpo = ConciliacionEditBody.model_validate({"cuadrar": valor, "cantidad": "2"})
    assert cuerpo.campos() == {"cantidad": 2.0}


@pytest.mark.parametrize("valor", ["cantidad", "IMPORTE", "", 1, None])
def test_f106_dominio_r4_cuadrar_otro_valor_es_422(valor):
    from domain.models.review_models import ConciliacionEditBody

    with pytest.raises(ValidationError):
        ConciliacionEditBody.model_validate({"cuadrar": valor})


def test_f106_dominio_r7_importe_y_precio_a_la_vez_es_422():
    from domain.models.review_models import ConciliacionEditBody

    with pytest.raises(ValidationError, match="Cambia el precio o el importe, no los dos"):
        ConciliacionEditBody.model_validate({"importe": 10, "precio_unitario": 2})


def test_f106_dominio_r4_sin_importe_ni_cuadrar_es_lo_de_hoy():
    from domain.models.review_models import ConciliacionEditBody

    cuerpo = ConciliacionEditBody.model_validate({"cantidad": "48"})
    assert cuerpo.importe is None
    assert cuerpo.cuadrar is None
    assert cuerpo.campos() == {"cantidad": 48.0}


# =================================================================== #
# Dominio · LineasIncompletasError(no_cuadran=) (R16)
# =================================================================== #
def test_f106_dominio_r16_aviso_de_lineas_que_no_cuadran():
    from domain.models.review_models import LineasIncompletasError

    error = LineasIncompletasError("doc", [], no_cuadran=[3])
    assert error.no_cuadran == [3]
    assert error.aviso == (
        "Líneas que no cuadran (cantidad × precio × (1 − dto) ≠ importe): 3"
    )
    assert str(error) == error.aviso


def test_f106_dominio_r16_aviso_junto_a_los_demas():
    from domain.models.review_models import LineasIncompletasError

    error = LineasIncompletasError("doc", [1], no_cuadran=[2, 4])
    assert error.aviso == (
        "Líneas sin cantidad o importe: 1. "
        "Líneas que no cuadran (cantidad × precio × (1 − dto) ≠ importe): 2, 4"
    )


def test_f106_dominio_r16_sin_no_cuadran_el_aviso_es_el_de_hoy():
    from domain.models.review_models import LineasIncompletasError

    error = LineasIncompletasError("doc", [1])
    assert error.no_cuadran == []
    assert error.aviso == "Líneas sin cantidad o importe: 1"


# =================================================================== #
# PATCH sobre SQLite (R5–R10, R32 a) · el albarán de CECOIS
# =================================================================== #
# Blanca 704 (gris): 10 × 11,20 −7 % = 104,16. Fila 14 Contrato (línea 504,
# 11,20 €, partida 01.04) con lo leído. ``cecois(q=48)`` deja la fila de
# producción: Q 48, P 11,2, d 7, I 104,16 ``declared_albaran`` (no cuadra).
FILA = 14


def cecois(*, q: float = 10.0, importe: float = 104.16, source: str = "declared_albaran"):
    from f065_bbdd import CONTRATO, DOC, construir, ejecutar, linea
    from sqlalchemy import text
    from sqlalchemy.orm import Session

    motor = construir()
    with Session(motor) as s:
        s.execute(text(
            "INSERT INTO albaran_contrato_lines_merge (id, contrato_id, codigo_contrato, "
            "codigo_producto, descripcion_linea, unidad_medida, precio_unitario, "
            "codigo_partida, fetched_at_utc, sigrid_ide) VALUES "
            "(504, 1, :c, 'TUB', 'TUBO PVC 110', 'UD', 11.2, '01.04', 't', 900504)"),
            {"c": CONTRATO})
        s.execute(text(
            "INSERT INTO albaran_lines_merge (id, document_id, provider_origin, "
            "line_index, concepto, cantidad, precio, precio_neto) VALUES "
            "(704, :d, 'merge', 4, 'TUBO PVC 110', 10.0, 11.2, 104.16)"),
            {"d": DOC})
        linea(s, id=FILA, merge_line_id=704, matched_contrato_line_id=504,
              precio_unitario_final=11.2, descuento_albaran_aplicado=7.0,
              cantidad_albaran=q, cantidad_convertida=q, importe_calculado=importe,
              importe_source=source, codigo_partida_final="01.04",
              descripcion_linea="TUBO PVC 110")
        s.commit()
    ejecutar(motor, "UPDATE albaran_valuations SET total_valorado = 2120 + :i "
             "WHERE id = 'f065-val-1'", i=importe)
    return motor


def _patch(motor, campos=None, cuadrar=None, vid=FILA):
    from f065_bbdd import DOC, repositorio

    return repositorio(motor).update_line_conciliacion(
        document_id=DOC, valuation_line_id=vid, campos=campos or {}, cuadrar=cuadrar,
    )


def _grises(motor):
    """Las tablas que el PATCH nunca toca (R10), enteras."""
    from sqlalchemy import text
    from sqlalchemy.orm import Session

    with Session(motor) as s:
        return {
            tabla: [tuple(r) for r in s.execute(text(f"SELECT * FROM {tabla} ORDER BY 1")).all()]
            for tabla in ("albaran_lines_merge", "albaran_documents_merge",
                          "albaran_contrato_lines_merge", "albaran_contratos_merge")
        }


def _suma(motor):
    from f065_bbdd import filas

    return round(sum(f["importe_calculado"] or 0 for f in filas(motor)), 2)


def _derivada(motor, did):
    from sqlalchemy import text
    from sqlalchemy.orm import Session

    with Session(motor) as s:
        return dict(s.execute(text(
            "SELECT precio_unitario, codigo_partida, origen FROM contrato_lines_derived "
            "WHERE id = :id"), {"id": did}).mappings().one())


def _cuadra(f):
    from ruesma_comun.importes import cuadra_linea

    return cuadra_linea(f["cantidad_convertida"], f["precio_unitario_final"],
                        f["descuento_albaran_aplicado"], f["importe_calculado"])


# ------------------------------------------------------------------ R5
@pytest.mark.parametrize("source", ["declared_albaran", "calculated"])
def test_f106_r5_cantidad_mueve_el_importe_sea_cual_sea_el_origen(source):
    from f065_bbdd import fila, total

    motor = cecois(source=source)
    grises = _grises(motor)

    assert _patch(motor, {"cantidad": 48.0}) is True

    f = fila(motor, FILA)
    # C1: Q cambiada ⇒ ``calculated``, nunca el leído.
    assert (f["cantidad_convertida"], f["precio_unitario_final"],
            f["descuento_albaran_aplicado"]) == (48.0, 11.2, 7.0)
    assert f["importe_calculado"] == 499.97
    assert f["importe_source"] == "calculated"
    # R8: cambiar Q no cambia el origen.
    assert (f["matched_contrato_line_id"], f["derived_contrato_line_id"]) == (504, None)
    assert total(motor) == _suma(motor)
    assert _grises(motor) == grises
    assert _cuadra(f) is True


def test_f106_r5_dto_mueve_el_importe_y_no_cambia_el_origen():
    from f065_bbdd import fila

    motor = cecois()
    _patch(motor, {"descuento": 10.0})
    f = fila(motor, FILA)
    assert (f["importe_calculado"], f["descuento_albaran_aplicado"]) == (100.8, 10.0)
    assert f["matched_contrato_line_id"] == 504


# ------------------------------------------------------------------ R6
def test_f106_r6_importe_despeja_el_precio_y_el_dto_se_queda():
    from f065_bbdd import fila, total
    from ruesma_comun.alta_sigrid import linea_a_sigrid

    motor = cecois(q=48.0, importe=499.97, source="calculated")
    grises = _grises(motor)

    assert _patch(motor, {"importe": 104.16}) is True

    f = fila(motor, FILA)
    assert f["importe_calculado"] == 104.16
    assert f["precio_unitario_final"] == 2.333333
    assert f["descuento_albaran_aplicado"] == 7.0
    assert f["cantidad_convertida"] == 48.0
    assert f["importe_source"] == "calculated"
    # R8: un P despejado es un precio cambiado ⇒ Contrato → Nueva.
    assert f["matched_contrato_line_id"] is None
    derivada = _derivada(motor, f["derived_contrato_line_id"])
    assert (derivada["precio_unitario"], derivada["origen"]) == (2.333333, "manual_override")
    assert f["precio_unitario_agreement"] == "manual"
    # sv9 mandará 48 × 2,17 (sin vincular: Nueva).
    assert linea_a_sigrid(vinculada=False, cantidad_albaran=f["cantidad_albaran"],
                          cantidad_convertida=f["cantidad_convertida"],
                          importe=f["importe_calculado"]) == (48.0, 2.17)
    assert _cuadra(f) is True
    assert total(motor) == _suma(motor)
    assert _grises(motor) == grises


def test_f106_r6_importe_con_cantidad_nueva():
    from f065_bbdd import fila

    motor = cecois()
    _patch(motor, {"cantidad": 48.0, "importe": 104.16})
    f = fila(motor, FILA)
    # El importe tecleado es el de hoy: con Q nueva también manda (no se descarta).
    assert (f["cantidad_convertida"], f["importe_calculado"],
            f["precio_unitario_final"]) == (48.0, 104.16, 2.333333)


def test_f106_r6_importe_con_dto_recibido():
    from f065_bbdd import fila

    motor = cecois(q=48.0, importe=499.97, source="calculated")
    _patch(motor, {"importe": 96.0, "descuento": 0.0})
    f = fila(motor, FILA)
    assert (f["importe_calculado"], f["precio_unitario_final"],
            f["descuento_albaran_aplicado"]) == (96.0, 2.0, None)


def test_f106_r6_importe_a_dos_decimales():
    from f065_bbdd import fila

    motor = cecois(q=48.0, importe=499.97, source="calculated")
    _patch(motor, {"importe": 104.164})
    assert fila(motor, FILA)["importe_calculado"] == 104.16


def test_f106_r6_importe_igual_en_fila_que_cuadra_no_escribe():
    from f065_bbdd import fila

    motor = cecois()
    antes = fila(motor, FILA)
    _patch(motor, {"importe": 104.16})
    assert fila(motor, FILA) == antes


def test_f106_r6_precio_despejado_igual_no_cambia_el_origen():
    from f065_bbdd import fila

    motor = cecois(q=48.0, importe=499.97, source="calculated")
    # 104,16 con Q 10 ⇒ 11,2: el mismo precio, sigue Contrato.
    _patch(motor, {"importe": 104.16, "cantidad": 10.0})
    f = fila(motor, FILA)
    assert (f["precio_unitario_final"], f["importe_calculado"]) == (11.2, 104.16)
    assert f["matched_contrato_line_id"] == 504


# ------------------------------------------------------------------ R7
def test_f106_r7_importe_cero_con_cantidad_cero_conserva_el_precio():
    from f065_bbdd import fila

    motor = cecois()
    _patch(motor, {"cantidad": 0.0, "importe": 0.0})
    f = fila(motor, FILA)
    assert (f["cantidad_convertida"], f["importe_calculado"],
            f["precio_unitario_final"]) == (0.0, 0.0, 11.2)
    assert f["matched_contrato_line_id"] == 504


@pytest.mark.parametrize("campos", [
    {"cantidad": 0.0, "importe": 50.0},
    {"descuento": 100.0, "importe": 50.0},
])
def test_f106_r7_importe_no_despejable_no_escribe_nada(campos):
    from f065_bbdd import fila, total
    from ruesma_comun.edicion_manual import NoDespejable

    motor = cecois()
    antes, total_antes = fila(motor, FILA), total(motor)
    with pytest.raises(NoDespejable):
        _patch(motor, campos)
    assert fila(motor, FILA) == antes
    assert total(motor) == total_antes


# ------------------------------------------------------------------ R8
def test_f106_r8_derivada_de_una_nueva_recibe_el_precio():
    from f065_bbdd import fila

    motor = cecois()
    # Fila 13: Nueva (derivada 601), 1 × 50.
    _patch(motor, {"importe": 60.0}, vid=13)
    f = fila(motor, 13)
    assert (f["precio_unitario_final"], f["importe_calculado"]) == (60.0, 60.0)
    assert f["derived_contrato_line_id"] == 601
    assert _derivada(motor, 601)["precio_unitario"] == 60.0


# ------------------------------------------------------------------ R9
def test_f106_r9_cuadrar_importe_sobre_la_fila_de_produccion():
    from f065_bbdd import fila, total

    motor = cecois(q=48.0)
    assert _cuadra(fila(motor, FILA)) is False

    assert _patch(motor, cuadrar="importe") is True

    f = fila(motor, FILA)
    assert (f["importe_calculado"], f["precio_unitario_final"]) == (499.97, 11.2)
    assert f["importe_source"] == "calculated"
    assert f["matched_contrato_line_id"] == 504
    assert total(motor) == _suma(motor)


def test_f106_r9_cuadrar_precio_sobre_la_fila_de_produccion():
    from f065_bbdd import fila

    motor = cecois(q=48.0)
    grises = _grises(motor)

    _patch(motor, cuadrar="precio")

    f = fila(motor, FILA)
    assert (f["importe_calculado"], f["precio_unitario_final"]) == (104.16, 2.333333)
    assert f["importe_source"] == "calculated"
    assert f["matched_contrato_line_id"] is None
    assert _cuadra(f) is True
    assert _grises(motor) == grises


@pytest.mark.parametrize("cuadrar", ["importe", "precio"])
def test_f106_r9_cuadrar_sobre_una_que_cuadra_no_escribe(cuadrar):
    from f065_bbdd import fila

    motor = cecois()
    antes = fila(motor, FILA)
    _patch(motor, cuadrar=cuadrar)
    assert fila(motor, FILA) == antes


def test_f106_r9_cuadrar_sobre_una_no_comparable_no_escribe():
    from f065_bbdd import ejecutar, fila

    motor = cecois()
    ejecutar(motor, "UPDATE albaran_line_valuations SET precio_unitario_final = NULL "
             "WHERE id = :v", v=FILA)
    antes = fila(motor, FILA)
    _patch(motor, cuadrar="importe")
    assert fila(motor, FILA) == antes


def test_f106_r9_cuadrar_precio_sin_divisor_es_no_despejable():
    from f065_bbdd import ejecutar, fila
    from ruesma_comun.edicion_manual import NoDespejable

    motor = cecois()
    ejecutar(motor, "UPDATE albaran_line_valuations SET cantidad_convertida = 0, "
             "cantidad_albaran = 0 WHERE id = :v", v=FILA)
    antes = fila(motor, FILA)
    with pytest.raises(NoDespejable):
        _patch(motor, cuadrar="precio")
    assert fila(motor, FILA) == antes


def test_f106_r9_c2_partida_sobre_la_fila_de_produccion_sigue_sin_cuadrar():
    # C2: lo que dejó AC26/30435. Una edición que no toca Q, P ni d no cuadra
    # la fila (ni la reetiqueta): la ficha la pinta en rojo y no se aprueba.
    from f065_bbdd import fila

    motor = cecois(q=48.0)
    _patch(motor, {"codigo_partida": "01.09"})
    f = fila(motor, FILA)
    assert (f["importe_calculado"], f["precio_unitario_final"]) == (104.16, 11.2)
    assert f["importe_source"] == "declared_albaran"
    assert _cuadra(f) is False


# ------------------------------------------------------------------ R10
def test_f106_r10_borde_de_r6_cantidad_grande_cuadra():
    from f065_bbdd import ejecutar, fila

    motor = cecois()
    ejecutar(motor, "UPDATE albaran_line_valuations SET descuento_albaran_aplicado = NULL "
             "WHERE id = :v", v=FILA)
    _patch(motor, {"cantidad": 40000.0, "importe": 12345.67})
    f = fila(motor, FILA)
    assert f["precio_unitario_final"] == 0.308642
    assert _cuadra(f) is True


def test_f106_r10_no_publica_ni_escribe_los_originales():
    import inspect

    import infrastructure.database.review_repository as modulo

    codigo = inspect.getsource(modulo.AlbaranReviewRepository.update_line_conciliacion)
    assert "publish" not in codigo and "queue" not in codigo.lower()
    for tabla in ("albaran_lines_merge", "albaran_documents_merge"):
        assert f"UPDATE {tabla}" not in codigo and f"INSERT INTO {tabla}" not in codigo


# ------------------------------------------------------------------ deshacer
def _deshacer(motor):
    """Lo que hace ``undo_last`` (que usa ``FOR UPDATE``, PostgreSQL), con los
    métodos reales de restaurar (como ``test_f065_f3_dividir``)."""
    import json

    from f065_bbdd import DOC, repositorio
    from sqlalchemy import text
    from sqlalchemy.orm import Session

    repo = repositorio(motor)
    with Session(motor) as s:
        (payload,) = s.execute(text(
            "SELECT payload FROM undo_log WHERE document_id = :d AND undone = 0"),
            {"d": DOC}).scalars().all()
        entrada = json.loads(payload)
        for item in entrada.get("delete_created", []):
            s.execute(text(f"DELETE FROM {item['table']} WHERE id = :id"), {"id": item["id"]})
        for snap in entrada.get("reinsert", []):
            repo._undo_apply_reinsert(s, snap)
        for snap in entrada["restore"]:
            repo._undo_apply_restore(s, snap)
        s.execute(text("DELETE FROM undo_log"))
        s.commit()
    return entrada


def test_f106_deshacer_devuelve_precio_importe_y_origen():
    from application.services.review_service import ReviewService
    from f065_bbdd import DOC, fila, repositorio, total

    motor = cecois(q=48.0)
    antes, total_antes = fila(motor, FILA), total(motor)
    servicio = ReviewService(repositorio(motor), "ana")

    assert servicio.update_line_conciliacion(
        document_id=DOC, valuation_line_id=FILA, campos={}, cuadrar="precio") is True
    assert fila(motor, FILA)["precio_unitario_final"] == 2.333333

    _deshacer(motor)

    assert fila(motor, FILA) == antes
    assert total(motor) == total_antes


# ------------------------------------------------------------------ R32 a
def test_f106_r32a_cecois_por_el_patch():
    from f065_bbdd import fila
    from ruesma_comun.alta_sigrid import linea_a_sigrid

    motor = cecois()
    grises = _grises(motor)

    _patch(motor, {"cantidad": 48.0})
    f = fila(motor, FILA)
    assert (f["importe_calculado"], f["importe_source"]) == (499.97, "calculated")

    _patch(motor, {"importe": 104.16})
    f = fila(motor, FILA)
    assert (f["precio_unitario_final"], f["importe_calculado"]) == (2.333333, 104.16)
    assert f["matched_contrato_line_id"] is None  # Nueva
    assert linea_a_sigrid(vinculada=False, cantidad_albaran=f["cantidad_albaran"],
                          cantidad_convertida=f["cantidad_convertida"],
                          importe=f["importe_calculado"]) == (48.0, 2.17)
    assert _grises(motor) == grises


# =================================================================== #
# app.py · 422 de R4 y R7; ``cuadrar`` llega al servicio
# =================================================================== #
class _Servicio:
    def __init__(self, error=None):
        self.llamadas = []
        self._error = error

    def initialize(self):
        return True

    def update_line_conciliacion(self, **kwargs):
        self.llamadas.append(kwargs)
        if self._error is not None:
            raise self._error
        return True


def _cliente(monkeypatch, servicio):
    from config.settings import Settings
    from fastapi.testclient import TestClient
    from interface_adapters.web import app as modulo_app

    monkeypatch.setattr(modulo_app, "SessionFactory", lambda **_: object())
    monkeypatch.setattr(modulo_app, "AlbaranReviewRepository", lambda *_: object())
    monkeypatch.setattr(modulo_app, "WorkflowRunsPurger", lambda *_: object())
    monkeypatch.setattr(modulo_app, "ReviewService", lambda *_: servicio)
    ajustes = Settings.model_construct(pg_password="x", pg_admin_password="x")
    return TestClient(modulo_app.build_app(ajustes), follow_redirects=False)


RUTA = "/api/documents/DOC/lines/14/conciliacion/campos"


def test_f106_r4_app_pasa_importe_y_cuadrar_al_servicio(monkeypatch):
    servicio = _Servicio()
    cliente = _cliente(monkeypatch, servicio)

    r = cliente.patch(RUTA, json={"importe": "104,16"})
    assert r.status_code == 200, r.text
    assert servicio.llamadas[0]["campos"] == {"importe": 104.16}
    assert "cuadrar" not in servicio.llamadas[0]

    r = cliente.patch(RUTA, json={"cuadrar": "precio"})
    assert r.status_code == 200, r.text
    assert servicio.llamadas[1]["campos"] == {}
    assert servicio.llamadas[1]["cuadrar"] == "precio"


@pytest.mark.parametrize("cuerpo", [
    {"cuadrar": "todo"}, {"importe": "NaN"}, {"importe": None},
    {"importe": 10, "precio_unitario": 2},
])
def test_f106_r4_r7_app_422_sin_llamar_al_servicio(monkeypatch, cuerpo):
    servicio = _Servicio()
    r = _cliente(monkeypatch, servicio).patch(RUTA, json=cuerpo)
    assert r.status_code == 422
    assert servicio.llamadas == []


def test_f106_r7_app_no_despejable_es_422_con_el_texto(monkeypatch):
    from ruesma_comun.edicion_manual import NoDespejable

    servicio = _Servicio(error=NoDespejable())
    r = _cliente(monkeypatch, servicio).patch(RUTA, json={"importe": 50})
    assert r.status_code == 422
    assert r.json()["detail"] == (
        "No se puede calcular el precio con cantidad 0 o descuento del 100 %: "
        "cambia la cantidad, el descuento o el precio"
    )


# =================================================================== #
# T9 · R-8: residuos (F-036) cuadran con la cantidad convertida
# =================================================================== #
def test_f106_r_8_residuos_de_f036_cuadran_con_la_convertida():
    # SS-0000589: 6 m3 declarados, 1 contenedor a 120 = 120 (F-036 D1).
    from ruesma_comun.importes import cuadra_linea
    from test_f036_r1_r8_conversion_no_reproducible import LINEA_RESIDUOS as L

    assert cuadra_linea(L["cantidad_convertida"], L["pu"], L["dto"], L["importe"]) is True
    # Con la del albarán no cuadraría (6 × 120 = 720): por eso Q es la convertida.
    assert cuadra_linea(L["cantidad_albaran"], L["pu"], L["dto"], L["importe"]) is False


def test_f106_r_8_editar_un_residuo_lo_deja_cuadrando_y_conserva_la_del_albaran():
    from f065_bbdd import fila, linea, motor_con_valoracion, repositorio
    from sqlalchemy.orm import Session

    motor = motor_con_valoracion(document_id="f106-doc-res", valuation_id="f106-val-res",
                                 total=120.0)
    with Session(motor) as s:
        from sqlalchemy import text

        s.execute(text(
            "INSERT INTO contrato_lines_derived (id, created_by_valuation_id, "
            "descripcion_linea, unidad_medida, precio_unitario, codigo_partida, origen) "
            "VALUES (5900, 'f106-val-res', 'CONTENEDOR', 'UD', 120, '01.01', "
            "'nueva_no_match')"))
        linea(s, id=900, valuation_id="f106-val-res", derived_contrato_line_id=5900,
              precio_unitario_final=120.0, factor_conversion=None, cantidad_albaran=6.0,
              cantidad_convertida=1.0, importe_calculado=120.0)
        s.commit()

    repositorio(motor).update_line_conciliacion(
        document_id="f106-doc-res", valuation_line_id=900, campos={"importe": 300.0})

    f = fila(motor, 900)
    assert (f["cantidad_albaran"], f["cantidad_convertida"]) == (6.0, 1.0)
    assert (f["precio_unitario_final"], f["importe_calculado"]) == (300.0, 300.0)
    assert _cuadra(f) is True
