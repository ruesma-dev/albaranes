# tests/test_f048_r29_r31_motivos_revision.py
"""F-048 · R29–R31: motivos de revision de ``origen_datos`` en el merge de sv3.

Solo DOS filas de la tabla de D5 mandan a revision:

- fila 3 — el correo trae UNA obra de la lista y el papel OTRA
  (``obra.discrepancia``) ⇒ ``correo_obra_distinta_papel``;
- fila 5 — el correo trae VARIAS y el papel no casa con ninguna, o no trae
  obra (``correo_ambiguo``) ⇒ ``correo_obra_ambigua``.

Con cualquiera de los dos, ``review_required = true`` aunque la confianza
del documento sea >= 80. Ni la obra ni la confianza cambian: sv3 MARCA, no
corrige. El resto —sin bloque, ``sin_correo``, ``correo_sin_dato``,
``ia_sin_lectura_correo``, ``correo_fuera_de_lista``, ``correo_unico`` sin
discrepancia y ``correo_confirma_papel``— deja los motivos de hoy. Los
nombres son los de ``comun`` (R31), y reprocesar no los duplica.

Base: un documento con dos proveedores que coinciden, sin ningun motivo y
con confianza > 80, para que lo unico que pueda mandarlo a revision sea el
bloque.

Sin red, sin BBDD y sin LLM. Textos inventados.
"""
from __future__ import annotations

import copy
import inspect
import json

import pytest
from application.services import albaran_confidence_service
from application.services.albaran_confidence_service import AlbaranConfidenceService
from application.services.obra_enrichment_service import ObraEnrichmentService
from domain.models.extraction_models import ExtractionEnvelope
from domain.models.obra_models import ObraEnrichmentResult
from infrastructure.database.sqlalchemy_albaran_repository import (
    MOTIVO_OBRA_PREFIJO,
    anadir_motivo_revision,
    quitar_motivos_con_prefijo,
)
from ruesma_comun.contratos.origen_datos import (
    MOTIVO_REVISION_OBRA_CORREO_AMBIGUA,
    MOTIVO_REVISION_OBRA_CORREO_DISTINTA,
    MOTIVOS_REVISION_ORIGEN,
)

_META = {
    "prompt_key": "albaran_revision_fase2_es",
    "schema": "albaran_v2",
    "source_filename": "SS-4.pdf",
    "source_mime_type": "application/pdf",
    "source_sha256": "e" * 64,
    "model": "modelo-de-prueba",
    "processed_at_utc": "2026-09-24T10:00:00Z",
}
_DATA = {
    "cabecera": {
        "proveedor_nombre": "HORMIGONES DEL SUR SL", "proveedor_cif": "B12345674", "fecha": "2026-09-20",
        "numero_albaran": "SS-4", "obra_codigo": "0945", "obra_nombre": "OBRA DEMO",
    },
    "lineas": [{"concepto": "HA-25/B/20/IIa", "cantidad": 7.5, "precio": 80.0, "precio_neto": 600.0,
                "unidad_medida": "m3", "confianza_pct": 95.0}],
    "clasificacion": {"familia": "hormigon", "confianza_pct": 95.0, "motivo": "Planta de hormigon.",
                      "mixto": False, "familias_secundarias": [], "origen": "ia1"},
}


def _origen(motivo: str, *, discrepancia: bool = False, fuente: str = "papel") -> dict:
    return {
        "version": 1, "correo_presente": motivo != "sin_correo", "correo_sha256": None,
        "correo_truncado": False, "evidencia": None,
        "obra": {"fuente": fuente, "motivo": motivo, "valor_final": "0945", "valor_correo": None,
                 "candidatos_correo": [], "valor_papel": "0937" if discrepancia else "0945",
                 "discrepancia": discrepancia, "validada": True},
    }


FILA_3 = _origen("correo_unico", discrepancia=True, fuente="correo")
FILA_5 = _origen("correo_ambiguo")


def _analisis(origen: dict | None, *, con_gemini: bool = True):
    data = copy.deepcopy(_DATA)
    if origen is not None:
        data["origen_datos"] = copy.deepcopy(origen)
    crudo: dict = {"meta": dict(_META), "data": data}
    if con_gemini:
        crudo["gemini"] = {"meta": dict(_META), "data": copy.deepcopy(_DATA)}
    envelope = ExtractionEnvelope.model_validate(crudo)
    return AlbaranConfidenceService().build_merge_analysis(openai=envelope, gemini=envelope.gemini)


def test_f048_r31_la_base_no_tiene_motivos_y_supera_el_80():
    """Precondicion: si la base ya fuera a revision, los tests no medirian nada."""
    base = _analisis(None)

    assert base.review_reasons == []
    assert base.review_required is False
    assert base.document_confidence_pct >= 80.0


# ---------------------------------------------------------------- #
# Las dos filas que mandan a revision.
# ---------------------------------------------------------------- #
@pytest.mark.parametrize(
    ("origen", "motivo"),
    [(FILA_3, MOTIVO_REVISION_OBRA_CORREO_DISTINTA), (FILA_5, MOTIVO_REVISION_OBRA_CORREO_AMBIGUA)],
    ids=["fila3_discrepancia", "fila5_ambiguo"],
)
def test_f048_r29_r30_el_motivo_manda_a_revision_aun_con_confianza_alta(origen, motivo):
    base, analisis = _analisis(None), _analisis(origen)

    assert analisis.review_reasons == [motivo]
    assert analisis.review_required is True
    assert analisis.comparison_summary["review_reasons"] == [motivo]
    assert analisis.comparison_summary["review_required"] is True
    # sv3 marca, no corrige: ni la confianza ni la obra cambian.
    assert analisis.document_confidence_pct == base.document_confidence_pct
    assert analisis.document_confidence_pct >= 80.0
    assert analisis.merged_envelope.data.cabecera.obra_codigo == "0945"


def test_f048_r29_el_motivo_se_suma_a_los_de_hoy_sin_quitar_ninguno():
    """El caso real de hoy (un solo proveedor): los motivos que ya habia siguen."""
    sin, con = _analisis(None, con_gemini=False), _analisis(FILA_3, con_gemini=False)

    assert sin.review_reasons  # la base de un solo proveedor ya trae motivos
    assert con.review_reasons == sin.review_reasons + [MOTIVO_REVISION_OBRA_CORREO_DISTINTA]


def test_f048_r29_r30_los_dos_disparadores_son_independientes():
    """Defensivo: si llegaran a la vez, salen los dos y en orden fijo."""
    analisis = _analisis(_origen("correo_ambiguo", discrepancia=True))

    assert analisis.review_reasons == [MOTIVO_REVISION_OBRA_CORREO_DISTINTA, MOTIVO_REVISION_OBRA_CORREO_AMBIGUA]


# ---------------------------------------------------------------- #
# El resto de filas: los motivos de hoy.
# ---------------------------------------------------------------- #
@pytest.mark.parametrize(
    "origen",
    [
        None,
        _origen("sin_correo"),
        _origen("correo_sin_dato"),
        _origen("ia_sin_lectura_correo"),
        _origen("correo_fuera_de_lista"),
        _origen("correo_unico", fuente="correo"),
        _origen("correo_confirma_papel"),
    ],
    ids=["sin_bloque", "sin_correo", "correo_sin_dato", "ia_sin_lectura", "fuera_de_lista",
         "unico_sin_discrepancia", "confirma_papel"],
)
def test_f048_r31_las_demas_filas_dejan_los_motivos_de_hoy(origen):
    base, analisis = _analisis(None), _analisis(origen)

    assert analisis.review_reasons == base.review_reasons == []
    assert analisis.review_required is False
    assert analisis.document_confidence_pct == base.document_confidence_pct


# ---------------------------------------------------------------- #
# Reproceso y nombres.
# ---------------------------------------------------------------- #
@pytest.mark.parametrize("origen", [FILA_3, FILA_5], ids=["fila3", "fila5"])
def test_f048_r29_reprocesar_no_duplica_el_motivo(origen):
    """El merge recalcula los motivos en cada pasada: no los acumula."""
    primero, segundo = _analisis(origen), _analisis(origen)

    assert segundo.review_reasons == primero.review_reasons
    assert sum(m in MOTIVOS_REVISION_ORIGEN for m in segundo.review_reasons) == 1


def test_f048_r31_los_nombres_se_importan_de_comun_no_se_copian():
    fuente = inspect.getsource(albaran_confidence_service)

    assert MOTIVO_REVISION_OBRA_CORREO_DISTINTA not in fuente
    assert MOTIVO_REVISION_OBRA_CORREO_AMBIGUA not in fuente
    assert "correo_ambiguo" not in fuente


# ---------------------------------------------------------------- #
# CR-D1 · la red de obra de F-002 no borra los motivos del origen.
#
# ``retirar_revision_obra`` corre justo despues de ``save()`` cuando la obra
# del merge existe en Sigrid y quita los motivos que empiezan por
# ``MOTIVO_OBRA_PREFIJO``. La red no se toca (design §6): son los nombres de
# ``comun`` los que no pueden caer bajo ese prefijo.
# ---------------------------------------------------------------- #
class _RepoRedObra:
    """Doble del puerto ``ObraMergeRepository`` con la columna de motivos.

    ``retirar_revision_obra`` hace lo MISMO que el repositorio SQLAlchemy
    (``sqlalchemy_albaran_repository.py``), sin la sesion: aplica la funcion
    pura ``quitar_motivos_con_prefijo`` con ``MOTIVO_OBRA_PREFIJO``.
    """

    def __init__(self, *, obra_codigo: str, review_reasons_json: str | None) -> None:
        self._obra_codigo = obra_codigo
        self.review_reasons_json = review_reasons_json
        self.retiradas = 0

    def get_merge_obra_codigo(self, *, document_id):
        return self._obra_codigo

    def update_merge_obra_fields(self, *, document_id, obra_nombre, obra_direccion):
        pass

    def descartar_obra_no_valida(self, *, document_id, codigo_leido, motivo):
        raise AssertionError("la obra existe: la red no debe descartarla")

    def retirar_revision_obra(self, *, document_id):
        self.retiradas += 1
        self.review_reasons_json = quitar_motivos_con_prefijo(self.review_reasons_json, MOTIVO_OBRA_PREFIJO)


class _SigridObraExiste:
    def fetch_obra_by_codigo(self, *, codigo_obra_normalizado):
        return ObraEnrichmentResult(
            codigo_obra=codigo_obra_normalizado, nombre_obra="OBRA DEMO", direccion_linea1="CALLE FALSA 1",
            direccion_linea2=None, codigo_postal="50001", municipio="ZARAGOZA", provincia="ZARAGOZA",
        )


@pytest.mark.parametrize(
    ("origen", "motivo"),
    [(FILA_3, MOTIVO_REVISION_OBRA_CORREO_DISTINTA), (FILA_5, MOTIVO_REVISION_OBRA_CORREO_AMBIGUA)],
    ids=["fila3_discrepancia", "fila5_ambiguo"],
)
def test_f048_cr_d1_la_red_de_obra_conserva_el_motivo_del_origen(origen, motivo):
    """Merge con obra valida + motivo del origen + un motivo de obra viejo:
    tras la red, el de obra se va (la red actuo) y el del origen se queda."""
    analisis = _analisis(origen)
    assert analisis.review_reasons == [motivo]
    # La columna como la deja ``save()``, con un motivo de obra de una pasada anterior.
    columna = anadir_motivo_revision(
        json.dumps(analisis.review_reasons, ensure_ascii=False, indent=2), "obra_inexistente:0937",
    )
    repo = _RepoRedObra(obra_codigo=analisis.merged_envelope.data.cabecera.obra_codigo, review_reasons_json=columna)

    ObraEnrichmentService(client=_SigridObraExiste(), repository=repo).enrich_merge_document(merge_document_id="m-1")

    assert repo.retiradas == 1
    assert json.loads(repo.review_reasons_json) == [motivo]


@pytest.mark.parametrize("motivo", MOTIVOS_REVISION_ORIGEN)
def test_f048_cr_d1_ningun_motivo_del_origen_cae_bajo_el_prefijo_de_la_red(motivo):
    columna = json.dumps([motivo])

    assert not motivo.startswith(MOTIVO_OBRA_PREFIJO)
    assert quitar_motivos_con_prefijo(columna, MOTIVO_OBRA_PREFIJO) == json.dumps([motivo], indent=2)
