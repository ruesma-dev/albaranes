# tests/test_f048_r35_vista_modelo.py
"""F-048 · R32–R35 (modelo de vista): sv4 LEE ``origen_datos`` y no escribe nada.

sv3 guarda el bloque dentro del ``raw_extraction_json`` del merge, que la
ficha ya carga. ``DocumentDetailPayload`` lo expone con tres propiedades:

- ``origen_datos``: el bloque parseado con el modelo de ``comun``. JSON
  roto, ausente, que no es un objeto, sin ``data`` o sin bloque, o un bloque
  que no valida ⇒ ``None``, y la ficha abre igual que hoy (R35).
- ``avisos_origen_datos``: lo que ve el revisor. Discrepancia ⇒ el campo,
  el codigo del correo y el del papel (R32); ``correo_ambiguo``,
  ``correo_confirma_papel`` y ``correo_fuera_de_lista`` ⇒ los candidatos del
  correo (R33). El resto de motivos no pinta nada.
- ``origen_en_duda``: ``True`` si ``review_reasons`` trae alguno de
  ``MOTIVOS_REVISION_ORIGEN`` de ``comun`` (R34). Sale de los motivos que
  sello sv3, no se recalcula aqui.

Solo en la vista MERGE, como la clasificacion de F-043: la vista por
proveedor es la extraccion cruda.

Sin red, sin BBDD y sin LLM. Codigos inventados.
"""
from __future__ import annotations

import inspect
import json
from pathlib import Path

import pytest
from ruesma_comun.contratos import MOTIVOS_REVISION_ORIGEN, OrigenDatos
from ruesma_comun.contratos.origen_datos import (
    MOTIVO_REVISION_OBRA_CORREO_AMBIGUA,
    MOTIVO_REVISION_OBRA_CORREO_DISTINTA,
)

RAIZ = Path(__file__).resolve().parents[1]


def _origen(motivo: str, *, final="0945", correo=None, candidatos=(), papel="0945", discrepancia=False,
            fuente="papel", validada=True) -> dict:
    return {
        "version": 1, "correo_presente": motivo != "sin_correo", "correo_sha256": "f" * 64,
        "correo_truncado": False, "evidencia": "la 945",
        "obra": {"fuente": fuente, "motivo": motivo, "valor_final": final, "valor_correo": correo,
                 "candidatos_correo": list(candidatos), "valor_papel": papel,
                 "discrepancia": discrepancia, "validada": validada},
    }


DISCREPANCIA = _origen("correo_unico", correo="0945", candidatos=["0945"], papel="0937", discrepancia=True,
                       fuente="correo")
AMBIGUO = _origen("correo_ambiguo", final="0937", candidatos=["0945", "0320"], papel="0937")
CONFIRMA = _origen("correo_confirma_papel", candidatos=["0945", "0320"], papel="09-45")
FUERA = _origen("correo_fuera_de_lista", candidatos=["PED-555"], validada=False)


def _raw(origen: dict | None) -> str:
    data: dict = {"cabecera": {"obra_codigo": "0945"}, "lineas": []}
    if origen is not None:
        data["origen_datos"] = origen
    return json.dumps({"meta": {}, "data": data, "debug": {}}, ensure_ascii=False)


def _payload(raw: str | None, motivos: list[str] | None = None, **campos):
    from domain.models.review_models import DocumentDetailPayload

    base = {
        "id": "f048-doc-0001",
        "source_filename": "SS-1.pdf",
        "provider_origin": "merge",
        "model_name": "—",
        "created_at_utc": "2026-09-24T10:00:00Z",
        "raw_extraction_json": raw,
        "review_reasons_json": json.dumps(motivos) if motivos is not None else None,
    }
    base.update(campos)
    return DocumentDetailPayload(**base)


# ---------------------------------------------------------------- #
# origen_datos
# ---------------------------------------------------------------- #
def test_f048_r35_el_payload_parsea_el_bloque_con_el_modelo_de_comun():
    documento = _payload(_raw(DISCREPANCIA))

    assert isinstance(documento.origen_datos, OrigenDatos)
    assert documento.origen_datos.model_dump(mode="json") == DISCREPANCIA


@pytest.mark.parametrize(
    "raw",
    [
        None,
        "",
        "{ roto",
        "[1, 2]",
        json.dumps({"meta": {}}),
        json.dumps({"data": "no es un objeto"}),
        _raw(None),
        json.dumps({"data": {"origen_datos": "no es un objeto"}}),
        json.dumps({"data": {"origen_datos": {"obra": {"motivo": "inventado"}}}}),
    ],
    ids=["nulo", "vacio", "json_roto", "no_es_objeto", "sin_data", "data_no_objeto", "sin_bloque",
         "bloque_no_objeto", "bloque_que_no_valida"],
)
def test_f048_r35_json_roto_ausente_o_sin_bloque_da_none_y_ningun_aviso(raw):
    documento = _payload(raw)

    assert documento.origen_datos is None
    assert documento.avisos_origen_datos == []
    assert documento.origen_en_duda is False


def test_f048_r35_la_vista_de_un_proveedor_no_lo_ensena():
    """Como la clasificacion (F-043): se ensena en el MERGE."""
    documento = _payload(_raw(DISCREPANCIA), view_mode="openai", provider_origin="openai")

    assert documento.origen_datos is None
    assert documento.avisos_origen_datos == []


# ---------------------------------------------------------------- #
# avisos_origen_datos
# ---------------------------------------------------------------- #
def test_f048_r32_la_discrepancia_dice_el_campo_y_las_dos_lecturas():
    (aviso,) = _payload(_raw(DISCREPANCIA)).avisos_origen_datos

    assert aviso == (
        "Obra: el correo dice 0945 y el papel dice 0937. "
        "Se ha usado la del correo."
    )


@pytest.mark.parametrize(
    ("origen", "esperado"),
    [
        (AMBIGUO, ("Obra: el correo cita varias obras (0945, 0320) y ninguna es la del papel (0937). "
                   "Se ha dejado la del papel.")),
        (CONFIRMA, ("Obra: el correo cita varias obras (0945, 0320) y una es la del papel "
                    "(el papel dice 09-45; en la lista de obras, 0945). Se ha usado 0945.")),
        (FUERA, ("Obra: el correo cita PED-555, que no está en la lista de obras de Sigrid. "
                 "Se ha usado la lectura del papel.")),
    ],
    ids=["ambiguo", "confirma_papel", "fuera_de_lista"],
)
def test_f048_r33_los_candidatos_del_correo_salen_con_su_motivo(origen, esperado):
    assert _payload(_raw(origen)).avisos_origen_datos == [esperado]


@pytest.mark.parametrize(("papel", "final"), [("945", "0945"), ("09-45", "0945")], ids=["sin_cero", "con_guion"])
def test_f048_cr_d3_confirma_papel_cita_la_lectura_del_papel_y_la_de_la_lista(papel, final):
    """Menor 3 de la review del bloque D: desde CR-C5 la cabecera lleva la forma
    de la lista; el aviso cita las dos lecturas para que no parezcan dos obras."""
    confirma = _origen("correo_confirma_papel", final=final, candidatos=[final, "0320"], papel=papel)

    assert _payload(_raw(confirma)).avisos_origen_datos == [
        f"Obra: el correo cita varias obras ({final}, 0320) y una es la del papel "
        f"(el papel dice {papel}; en la lista de obras, {final}). Se ha usado {final}."
    ]


def test_f048_cr_d3_confirma_papel_con_la_misma_forma_cita_una_sola_vez():
    confirma = _origen("correo_confirma_papel", candidatos=["0945", "0320"], papel="0945")

    assert _payload(_raw(confirma)).avisos_origen_datos == [
        "Obra: el correo cita varias obras (0945, 0320) y una es la del papel (0945). Se ha usado esa."
    ]


def test_f048_cr_d2_varios_codigos_fuera_de_lista_concuerdan_en_plural():
    """Menor 2 de la review del bloque D: «que no están», no «que no está»."""
    fuera = _origen("correo_fuera_de_lista", candidatos=["PED-555", "600123"], validada=False)

    assert _payload(_raw(fuera)).avisos_origen_datos == [
        "Obra: el correo cita PED-555, 600123, que no están en la lista de obras de Sigrid. "
        "Se ha usado la lectura del papel."
    ]


def test_f048_r33_sin_papel_el_aviso_lo_dice():
    ambiguo = _origen("correo_ambiguo", final=None, candidatos=["0945", "0320"], papel=None)

    (aviso,) = _payload(_raw(ambiguo)).avisos_origen_datos

    assert aviso == (
        "Obra: el correo cita varias obras (0945, 0320) y el papel no trae obra. "
        "Se ha dejado sin obra."
    )


@pytest.mark.parametrize(
    "origen",
    [
        _origen("sin_correo"),
        _origen("correo_sin_dato"),
        _origen("ia_sin_lectura_correo"),
        _origen("correo_unico", correo="0945", candidatos=["0945"], fuente="correo"),
    ],
    ids=["sin_correo", "sin_dato", "ia_sin_lectura", "unico_sin_discrepancia"],
)
def test_f048_r33_el_resto_de_motivos_no_pinta_aviso(origen):
    documento = _payload(_raw(origen))

    assert documento.origen_datos is not None
    assert documento.avisos_origen_datos == []


# ---------------------------------------------------------------- #
# origen_en_duda
# ---------------------------------------------------------------- #
@pytest.mark.parametrize("motivo", MOTIVOS_REVISION_ORIGEN)
def test_f048_r34_un_motivo_de_origen_pone_el_aviso_en_duda(motivo):
    assert _payload(_raw(AMBIGUO), [motivo]).origen_en_duda is True


def test_f048_r34_otros_motivos_no_lo_ponen_en_duda():
    documento = _payload(_raw(DISCREPANCIA), ["single_provider_openai", "clasificacion_mixta"])

    assert documento.origen_en_duda is False


def test_f048_r34_la_duda_sale_de_los_motivos_de_sv3_no_del_bloque():
    """Discrepancia en el bloque pero sin motivo sellado: no se recalcula aqui."""
    assert _payload(_raw(DISCREPANCIA), []).origen_en_duda is False
    assert _payload(_raw(None), [MOTIVO_REVISION_OBRA_CORREO_DISTINTA]).origen_en_duda is True


# ---------------------------------------------------------------- #
# sv4 no escribe ni copia nombres (R31, R35)
# ---------------------------------------------------------------- #
def test_f048_r31_sv4_no_copia_los_nombres_de_los_motivos():
    from domain.models import review_models

    fuente = inspect.getsource(review_models)
    for motivo in (MOTIVO_REVISION_OBRA_CORREO_DISTINTA, MOTIVO_REVISION_OBRA_CORREO_AMBIGUA):
        assert motivo not in fuente


def test_f048_r35_sv4_no_escribe_origen_datos():
    """Ni DDL, ni ``review_notes``, ni motivos: el repositorio no lo nombra."""
    repositorio = (RAIZ / "infrastructure" / "database" / "review_repository.py").read_text(encoding="utf-8")

    assert "origen_datos" not in repositorio
    for motivo in MOTIVOS_REVISION_ORIGEN:
        assert motivo not in repositorio


def test_f048_r35_el_lector_del_merge_lleva_el_bloque_a_la_ficha(repositorio):
    """De la fila del merge a la ficha, sin BBDD: el lector ya pasaba el JSON."""
    from infrastructure.database.orm_models import AlbaranDocumentMergeOrm

    merge = AlbaranDocumentMergeOrm(
        id="f048-doc-0001", provider_origin="merge", source_filename="SS-1.pdf",
        source_mime_type="application/pdf", source_sha256="0" * 64, prompt_key="p",
        schema_name="documento_albaran", model_name="m", raw_extraction_json=_raw(DISCREPANCIA),
        review_reasons_json=json.dumps([MOTIVO_REVISION_OBRA_CORREO_DISTINTA]),
        created_at_utc="2026-09-24T10:00:00Z", approved=False,
    )

    detalle = repositorio._build_merge_detail(
        merge_doc=merge, available_views=["merge"], provider_snapshots=[], contratos=[],
        selected_contrato_codigo=None,
    )

    assert detalle.origen_datos is not None
    assert detalle.origen_en_duda is True
    assert len(detalle.avisos_origen_datos) == 1
