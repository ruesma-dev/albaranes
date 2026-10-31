# tests/test_f115_guardar_retira_contrato.py
"""F-115 R9–R11, R18, R19 · el guardado no reenvía el contrato del proveedor anterior.

- R9: si el PUT trae un ``selected_contrato_codigo`` que no es del albarán con
  el CIF y la obra de ese mismo PUT (R1 de comun), se guarda NULL y el origen
  NULL (sustituye a la aceptación por «contrato compartido» sin mirar el
  proveedor).
- R10: se quita de las notas la línea de auto-selección de ese código.
- R11: el aviso de guardado dice que se quitó el contrato y que se busca y se
  revalora.
- R18: aprobado o con alta bloqueante, 409 como hoy, sin tocar nada.
- R19: el mismo CIF con otro formato no retira ni relanza.

Casos (g) e (i) de R22. Sin red: SQLite en memoria con el ORM de sv4.
"""
from __future__ import annotations

from typing import Any

import pytest
from f053_sv4_bbdd import _VALORACION, DDL_ALTAS, Fabrica, _merge, poner_alta
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

DOC = "f115-doc-0000-0000-000000000001"
CIF_A, CIF_B, OBRA = "A11111111", "B22222222", "0404"
NOTA_AUTO_A = (
    "[AVISO] Contrato CTA/0001 elegido AUTOMATICAMENTE entre 2 candidatos "
    "(criterio deterministico por familia/palabras). Verificar que es el correcto."
)
OTRA_NOTA = "[NOTA] Hablado con la obra."


def _motor(*, aprobado: bool = False, filas_contrato=None, con_altas: bool = False):
    from infrastructure.database.orm_models import Base

    motor = create_engine("sqlite://")
    Base.metadata.create_all(motor)
    if filas_contrato is None:
        filas_contrato = [(DOC, "CTA/0001", CIF_A, OBRA)]
    with Session(motor) as s:
        for sentencia in _VALORACION:
            s.execute(text(sentencia))
        if con_altas:
            s.execute(text(DDL_ALTAS))
        _merge(s, DOC, proveedor_cif=CIF_A, obra_codigo=OBRA, approved=aprobado,
               selected_contrato_codigo="CTA/0001", selected_contrato_origen="auto_multiple",
               review_notes=f"{OTRA_NOTA}\n{NOTA_AUTO_A}")
        _merge(s, "f115-otro", proveedor_cif=CIF_B, obra_codigo=OBRA)
        for i, (doc, codigo, cif, obra) in enumerate(filas_contrato, start=1):
            s.execute(text(
                "INSERT INTO albaran_contratos_merge (id, document_id, codigo_contrato, "
                "cif_proveedor, codigo_obra, fetched_at_utc) VALUES (:i, :d, :c, :cif, :o, 't')"),
                {"i": i, "d": doc, "c": codigo, "cif": cif, "o": obra})
        s.commit()
    return motor


def _repo(motor):
    from infrastructure.database.review_repository import AlbaranReviewRepository

    repo = AlbaranReviewRepository(Fabrica(motor))  # type: ignore[arg-type]
    repo.initialize = lambda: True  # type: ignore[method-assign]
    repo._undo_table_ready = True  # type: ignore[attr-defined]
    return repo


def _guardar(motor, **campos: Any):
    from domain.models.review_models import MergeDocumentUpdatePayload

    datos = {"proveedor_cif": CIF_B, "obra_codigo": OBRA, "selected_contrato_codigo": "CTA/0001",
             "review_notes": f"{OTRA_NOTA}\n{NOTA_AUTO_A}"}
    datos.update(campos)
    detalle, _ = _repo(motor).update_document_y_transicion(
        document_id=DOC, payload=MergeDocumentUpdatePayload(**datos),
    )
    return detalle


def _merge_bd(motor) -> dict[str, Any]:
    with Session(motor) as s:
        return dict(s.execute(text(
            "SELECT proveedor_cif, obra_codigo, selected_contrato_codigo, "
            "selected_contrato_origen, review_notes, approved FROM albaran_documents_merge "
            "WHERE id = :d"), {"d": DOC}).mappings().one())


# ------------------------------------------------------------------ #
# R9, R10 · caso (g)
# ------------------------------------------------------------------ #
def test_f115_r9_g_put_con_el_codigo_de_a_y_el_cif_de_b_guarda_nulo():
    motor = _motor()
    detalle = _guardar(motor)
    fila = _merge_bd(motor)
    assert fila["proveedor_cif"] == CIF_B
    assert (fila["selected_contrato_codigo"], fila["selected_contrato_origen"]) == (None, None)
    assert detalle.selected_contrato_codigo is None
    assert detalle.contrato_retirado == "CTA/0001"


def test_f115_r10_g_quita_solo_la_nota_de_auto_seleccion_de_ese_codigo():
    motor = _motor()
    otra_auto = "[AVISO] Contrato CTZ/0009 elegido AUTOMATICAMENTE entre 3 candidatos."
    _guardar(motor, review_notes=f"{OTRA_NOTA}\n{NOTA_AUTO_A}\n{otra_auto}")
    assert _merge_bd(motor)["review_notes"] == f"{OTRA_NOTA}\n{otra_auto}"


def test_f115_r9_cambio_de_obra_con_el_mismo_proveedor_tambien_retira():
    """R15/D2: se conserva el proveedor; el contrato era de la obra anterior."""
    motor = _motor()
    detalle = _guardar(motor, proveedor_cif=CIF_A, obra_codigo="0700")
    fila = _merge_bd(motor)
    assert (fila["proveedor_cif"], fila["obra_codigo"]) == (CIF_A, "0700")
    assert fila["selected_contrato_codigo"] is None
    assert detalle.contrato_retirado == "CTA/0001"


def test_f115_r9_contrato_compartido_de_otro_documento_y_de_otro_proveedor_se_retira():
    motor = _motor(filas_contrato=[("f115-otro", "CTA/0001", CIF_A, OBRA)])
    _guardar(motor)
    assert _merge_bd(motor)["selected_contrato_codigo"] is None


def test_f115_r9_contrato_compartido_del_mismo_proveedor_se_acepta_como_hoy():
    motor = _motor(filas_contrato=[("f115-otro", "CTB/0001", CIF_B, OBRA)])
    detalle = _guardar(motor, selected_contrato_codigo="CTB/0001")
    assert _merge_bd(motor)["selected_contrato_codigo"] == "CTB/0001"
    assert detalle.contrato_retirado is None


def test_f115_r9_contrato_del_documento_y_del_albaran_se_conserva_con_su_origen():
    motor = _motor()
    detalle = _guardar(motor, proveedor_cif=CIF_A)
    fila = _merge_bd(motor)
    assert (fila["selected_contrato_codigo"], fila["selected_contrato_origen"]) == (
        "CTA/0001", "auto_multiple")
    assert NOTA_AUTO_A in fila["review_notes"]
    assert detalle.contrato_retirado is None


def test_f115_r9_f_fila_legada_sin_cif_no_descalifica():
    motor = _motor(filas_contrato=[(DOC, "CTA/0001", None, OBRA)])
    _guardar(motor)
    assert _merge_bd(motor)["selected_contrato_codigo"] == "CTA/0001"


def test_f115_r9_codigo_sin_ninguna_fila_se_descarta_como_hoy_sin_decir_retirado():
    motor = _motor(filas_contrato=[])
    detalle = _guardar(motor)
    assert _merge_bd(motor)["selected_contrato_codigo"] is None
    assert detalle.contrato_retirado is None


# ------------------------------------------------------------------ #
# R19 · mismo CIF con otro formato · caso (e)
# ------------------------------------------------------------------ #
@pytest.mark.parametrize("cif", ["a-11111111", " a 11111111 ", "ESA11111111"])
def test_f115_r19_e_mismo_cif_con_otro_formato_no_retira(cif):
    motor = _motor()
    detalle = _guardar(motor, proveedor_cif=cif)
    assert _merge_bd(motor)["selected_contrato_codigo"] == "CTA/0001"
    assert detalle.contrato_retirado is None


@pytest.mark.parametrize("cif", ["a-11111111", "ESA11111111", " a 11111111 "])
def test_f115_r19_mismo_cif_con_otro_formato_no_relanza_la_busqueda(cif):
    from application.services.busqueda_contratos import debe_relanzar_busqueda, estado_busqueda
    from domain.models.review_models import BUSQUEDA_ENCONTRADOS, RastroBusquedaContratos

    rastro = RastroBusquedaContratos(cif=CIF_A, obra=OBRA, resultado=BUSQUEDA_ENCONTRADOS,
                                     at_utc="2026-10-30T10:00:00+00:00")
    assert not debe_relanzar_busqueda(estado_busqueda(cif, OBRA, rastro))
    assert debe_relanzar_busqueda(estado_busqueda(CIF_B, OBRA, rastro))


# ------------------------------------------------------------------ #
# R18 · aprobado o con alta bloqueante · caso (i)
# ------------------------------------------------------------------ #
def test_f115_r18_i_aprobado_409_sin_tocar_nada():
    from domain.models.review_models import AlbaranAprobadoError

    motor = _motor(aprobado=True)
    antes = _merge_bd(motor)
    with pytest.raises(AlbaranAprobadoError):
        _guardar(motor)
    assert _merge_bd(motor) == antes


@pytest.mark.parametrize("estado", ["en_curso", "incierto", "registrado"])
def test_f115_r18_alta_bloqueante_409_sin_tocar_nada(estado):
    from domain.models.alta_sigrid_models import AlbaranBloqueadoError

    motor = _motor(con_altas=True)
    poner_alta(motor, estado, document_id=DOC)
    antes = _merge_bd(motor)
    with pytest.raises(AlbaranBloqueadoError):
        _guardar(motor)
    assert _merge_bd(motor) == antes


# ------------------------------------------------------------------ #
# R11 · el aviso del guardado
# ------------------------------------------------------------------ #
def _outcome(status: str, message: str = "m"):
    from domain.models.contrato_refetch_models import ContratoRefetchOutcome

    return ContratoRefetchOutcome(status=status, count=0, selected_contrato_codigo=None,
                                  message=message, cif=None, obra_codigo=None)


def test_f115_r11_aviso_proveedor_cambiado_con_busqueda_encolada():
    from application.services.busqueda_contratos import aviso_de_guardado

    assert aviso_de_guardado(
        aprobado=False, busqueda=_outcome("queued"), contrato_retirado="CTA/0001",
        cambio="proveedor",
    ) == (
        "Documento guardado. Proveedor cambiado: se ha quitado el contrato CTA/0001 y se "
        "buscan los contratos del nuevo proveedor; después se vuelve a valorar",
        True,
    )


def test_f115_r11_aviso_obra_cambiada_conserva_el_proveedor():
    from application.services.busqueda_contratos import aviso_de_guardado

    mensaje, buscando = aviso_de_guardado(
        aprobado=False, busqueda=_outcome("queued"), contrato_retirado="CTA/0001",
        cambio="obra",
    )
    assert mensaje == (
        "Documento guardado. Obra cambiada: se ha quitado el contrato CTA/0001 y se buscan "
        "los contratos del mismo proveedor en la nueva obra; después se vuelve a valorar"
    )
    assert buscando is True


def test_f115_r11_aviso_con_busqueda_local_anade_su_mensaje():
    from application.services.busqueda_contratos import aviso_de_guardado

    mensaje, buscando = aviso_de_guardado(
        aprobado=False, busqueda=_outcome("found_single", "1 contrato encontrado."),
        contrato_retirado="CTA/0001", cambio="proveedor",
    )
    assert mensaje.endswith("después se vuelve a valorar. 1 contrato encontrado.")
    assert buscando is False


def test_f115_r11_sin_retirada_el_aviso_es_el_de_siempre():
    from application.services.busqueda_contratos import aviso_de_guardado

    assert aviso_de_guardado(aprobado=False, busqueda=_outcome("queued"),
                             contrato_retirado=None, cambio="proveedor") == (
        "Documento guardado. Buscando contratos con el CIF y la obra guardados…", True)


def test_f115_r11_el_servicio_dice_que_contrato_se_retiro_y_que_cambio():
    from application.services.review_service import ReviewService
    from domain.models.review_models import MergeDocumentUpdatePayload

    class _Refetch:
        def __init__(self):
            self.llamadas = []

        def refetch(self, *, document_id):
            self.llamadas.append(document_id)
            return _outcome("queued")

    motor = _motor()
    with Session(motor) as s:  # rastro de la búsqueda con el proveedor A
        s.execute(text(
            "UPDATE albaran_documents_merge SET contratos_busqueda_cif = :c, "
            "contratos_busqueda_obra = :o, contratos_busqueda_resultado = 'encontrados', "
            "contratos_busqueda_at_utc = '2026-10-30T10:00:00+00:00' WHERE id = :d"),
            {"c": CIF_A, "o": OBRA, "d": DOC})
        s.commit()
    refetch = _Refetch()
    resultado = ReviewService(_repo(motor), default_reviewer="revisor").guardar(
        document_id=DOC,
        payload=MergeDocumentUpdatePayload(proveedor_cif=CIF_B, obra_codigo=OBRA,
                                           selected_contrato_codigo="CTA/0001"),
        refetch_client=refetch,
    )
    assert refetch.llamadas == [DOC]
    assert resultado.contrato_retirado == "CTA/0001"
    assert resultado.cambio == "proveedor"
