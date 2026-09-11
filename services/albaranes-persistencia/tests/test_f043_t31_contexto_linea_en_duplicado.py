# tests/test_f043_t31_contexto_linea_en_duplicado.py
"""F-043 · T31 — el re-proceso pierde el ``contexto_linea`` de la LINEA.

Segundo defecto REAL del mismo sitio, medido el 2026-09-11 contra el
pipeline local con LLM de verdad (albaran SS-0003967, document_id
``1dc06154-00ce-4c80-9de3-7a41cc0a08c3``):

- sv2 clasifico el DOCUMENTO (residuos / 100 / ia2) y ademas IA2 emitio
  el contexto de la UNICA linea, con los tres campos que abren la
  maquinaria de residuos de sv6: ``tipo_familia``, ``codigo_ler`` y
  ``volumen_m3``. Esta literal en el envelope que quedo en Azurite
  (``envelopes/1dc06154-..._phase_1.json``).
- sv3 escribio las seis columnas ``tipologia*`` —eso ya lo arreglo
  ``test_f043_t31_clasificacion_en_duplicado.py``— pero dejo
  ``albaran_lines_merge.contexto_linea_json`` a NULL: la fila de la
  linea seguia siendo la del 2026-08-19.
- Consecuencia medida en sv6: la clasificacion SI abrio las puertas de
  familia (la valoracion trae la razon ``residuos_sin_volumen_m3``, que
  solo se alcanza dentro de la puerta de residuos), pero sin
  ``volumen_m3`` no se pueden contar contenedores y sin ``codigo_ler``
  no hay incremento que inyectar: **720,00 EUR = 6 m3 x 120** en UNA
  linea, en vez de 120 + 90 en dos.

Causa: la misma rama de DUPLICADO de ``PersistAlbaranPipeline.run``.
``repository.save()`` —la unica escritura de ``contexto_linea_json``,
dentro de ``_build_lines``— no corre cuando el PDF ya estaba
persistido. El arreglo de esta manana solo cubrio la clasificacion del
DOCUMENTO; el contexto de las LINEAS seguia perdiendose.

Por que ningun test lo veia: los de residuos de sv5/sv6 construyen la
linea con su ``contexto_linea`` ya puesto (``f036_escenarios_residuos``,
``test_f043_r26_ss0003967``) y los de sv3 atacan ``_build_lines`` por
separado. Nadie recorria ``run()`` mirando la LINEA.

Sin red, sin BBDD, sin LLM.
"""
from __future__ import annotations

import hashlib

import pytest
from ruesma_comun.contratos.contexto_linea import ContextoLinea

from application.pipelines.persist_albaran_pipeline import (
    PersistAlbaranPipeline,
    PersistAlbaranRequest,
)
from domain.models.persistence_models import ExistingDocument

_PDF = b"%PDF-1.4 SS-0003967"
_SHA256 = hashlib.sha256(_PDF).hexdigest()
_MERGE_ID = "1dc06154-00ce-4c80-9de3-7a41cc0a08c3"

#: El ``contexto_linea`` REAL que IA2 emitio el 2026-09-11 para la unica
#: linea de SS-0003967, copiado del envelope de Azurite sin retocar. Los
#: tres campos que importan aguas abajo:
#:   - ``tipo_familia`` -> rama 1 de ``familia_efectiva`` (sv6);
#:   - ``volumen_m3``   -> ``calcular_contenedores_residuos`` (1 ud);
#:   - ``codigo_ler``   -> la sintetica ``INCREMENTO LER 170604`` (90 EUR).
#: El mismo diccionario se usa en el otro extremo de la cadena, en
#: ``services/albaran-valoracion-persist/tests/
#: test_f043_t31_cadena_merge_a_puertas.py``.
CONTEXTO_LINEA_REAL = {
    "tipo_familia": "residuos",
    "rol_linea": "base",
    "descripcion_extendida": None,
    "notas_tiempo": None,
    "ref_linea_base": None,
    "codigo_ler": "170604",
    "volumen_m3": 6.0,
    "peso_toneladas": 0.18,
    "contenedores": None,
    "contenedores_entregados": None,
    "contenedores_retirados": None,
    "carga_incompleta": None,
    "m3_no_transportados": None,
    "exceso_declarado_min": None,
}

_CLASIFICACION = {
    "familia": "residuos",
    "confianza_pct": 100.0,
    "motivo": "Gestor autorizado de RCD, LER 170604 y contenedores.",
    "mixto": False,
    "familias_secundarias": [],
    "origen": "ia2",
}


def _envelope(*, con_contexto: bool = True) -> dict:
    """El envelope FINAL de sv2 tal como lo recibe el worker de sv3."""
    linea: dict = {
        "codigo": "170604",
        "concepto": "Mat. Aislamiento",
        "cantidad": 6.0,
        "confianza_pct": 95.0,
    }
    if con_contexto:
        linea["contexto_linea"] = dict(CONTEXTO_LINEA_REAL)
    return {
        "meta": {
            "prompt_key": "albaran_revision_fase2_residuos",
            "schema": "albaran_v2",
            "source_filename": "SALMEDINA_0003967.pdf",
            "source_mime_type": "application/pdf",
            "source_sha256": _SHA256,
            "model": "gpt-5.2",
            "processed_at_utc": "2026-09-11T08:55:12+00:00",
        },
        "data": {
            "cabecera": {
                "proveedor_nombre": "SALMEDINA",
                "proveedor_cif": "B82899550",
                "numero_albaran": "SS-0003967",
                "fecha": "2024-07-10",
            },
            "lineas": [linea],
            "clasificacion": dict(_CLASIFICACION),
        },
        "debug": {"phase_1": {}},
    }


class RepoDuplicadoFake:
    """Repositorio que ya tiene el documento (misma huella del PDF)."""

    def __init__(self, *, falla_escritura: bool = False) -> None:
        self.falla_escritura = falla_escritura
        self.contextos: list[tuple[str, list]] = []

    def initialize(self) -> None:
        return None

    def get_by_sha256(self, source_sha256: str) -> ExistingDocument:
        return ExistingDocument(
            document_id=_MERGE_ID,
            source_sha256=source_sha256,
            sharepoint_url=None,
            stored_lines=1,
        )

    def save(self, **_kwargs):  # pragma: no cover — el duplicado no guarda
        raise AssertionError("La rama de duplicado no debe llamar a save().")

    def update_merge_clasificacion(self, *, document_id, clasificacion):
        return True

    def update_merge_lineas_contexto(self, *, document_id, lineas):
        if self.falla_escritura:
            raise RuntimeError("UPDATE roto")
        self.contextos.append((document_id, list(lineas)))
        return len(lineas)

    def get_merge_cif_and_obra(self, *, document_id: str):
        return "B82899550", "0687"

    def get_selected_contrato_codigo(self, *, document_id: str):
        return "CTSU24/0228"

    def has_selected_contrato_with_lines(self, *, document_id: str):
        return True, "CTSU24/0228"


def _pipeline(repo, *, valuation_trigger=None) -> PersistAlbaranPipeline:
    return PersistAlbaranPipeline(
        repository=repo,
        document_storage=object(),
        normalizer=object(),
        valuation_trigger=valuation_trigger,
    )


def _run(repo, envelope: dict, *, valuation_trigger=None):
    return _pipeline(repo, valuation_trigger=valuation_trigger).run(
        PersistAlbaranRequest(
            filename="SALMEDINA_0003967.pdf",
            mime_type="application/pdf",
            file_bytes=_PDF,
            extraction_envelope=envelope,
            context={},
        )
    )


# ------------------------------------------------------------------ #
# El defecto: un documento ya persistido pierde el contexto de linea.
# ------------------------------------------------------------------ #

def test_f043_t31_el_duplicado_persiste_el_contexto_de_las_lineas():
    """El caso SS-0003967 exacto: re-proceso de un PDF ya conocido."""
    repo = RepoDuplicadoFake()

    resultado = _run(repo, _envelope())

    assert resultado.duplicate is True
    assert len(repo.contextos) == 1
    document_id, lineas = repo.contextos[0]
    assert document_id == _MERGE_ID
    assert len(lineas) == 1
    assert lineas[0].contexto_linea is not None


def test_f043_t31_el_contexto_trae_los_tres_campos_que_usan_las_puertas():
    """Los tres campos que consume la maquinaria de residuos de sv6.

    Este es el contrato de la entrega, no un detalle del test: sv5 lee
    ``albaran_lines_merge.contexto_linea_json``, lo valida contra ESTE
    mismo ``ContextoLinea`` de ``ruesma_comun`` y lo mete en el sobre.
    Si alguno de los tres se cae por el camino, sv6 abre la puerta de
    residuos y no puede hacer nada con ella: son los 720,00 EUR
    medidos el 2026-09-11.
    """
    repo = RepoDuplicadoFake()

    _run(repo, _envelope())

    ctx = repo.contextos[0][1][0].contexto_linea
    # Lo que llega tiene que revalidar contra el contrato compartido.
    ctx = ContextoLinea.model_validate(ctx.model_dump())
    assert ctx.tipo_familia == "residuos"   # rama 1 de familia_efectiva
    assert ctx.codigo_ler == "170604"       # sintetica del incremento
    assert ctx.volumen_m3 == pytest.approx(6.0)  # nº de contenedores


def test_f043_t31_basta_con_que_UNA_linea_traiga_contexto():
    """Un albaran mixto: la linea 2 no es de familia compleja y llega sin
    contexto. Eso no puede impedir que se escriba el de la linea 1."""
    envelope = _envelope()
    envelope["data"]["lineas"].append(
        {"codigo": "ZZ", "concepto": "Otra cosa", "cantidad": 1.0},
    )
    repo = RepoDuplicadoFake()

    _run(repo, envelope)

    lineas = repo.contextos[0][1]
    assert len(lineas) == 2
    assert lineas[0].contexto_linea is not None
    assert lineas[1].contexto_linea is None


def test_f043_t31_lo_escribe_antes_de_disparar_la_valoracion():
    """Orden obligatorio: sv6 valora leyendo el merge. Escribir el
    contexto DESPUES del trigger es una carrera que sv6 pierde."""
    orden: list[str] = []

    class RepoOrdenado(RepoDuplicadoFake):
        def update_merge_lineas_contexto(self, *, document_id, lineas):
            orden.append("contexto")
            return super().update_merge_lineas_contexto(
                document_id=document_id, lineas=lineas,
            )

    class TriggerEspia:
        def trigger_async(self, **_kwargs) -> bool:
            orden.append("valoracion")
            return True

        def trigger_sync(self, **_kwargs):  # pragma: no cover
            raise AssertionError("el duplicado dispara en async")

    _run(RepoOrdenado(), _envelope(), valuation_trigger=TriggerEspia())

    assert orden.index("contexto") < orden.index("valoracion")


# ------------------------------------------------------------------ #
# R27 — un envelope SIN contexto se comporta exactamente como hoy.
# ------------------------------------------------------------------ #

def test_f043_r27_el_duplicado_sin_contexto_de_linea_no_escribe_nada():
    """Ninguna linea con contexto -> NO-OP. No se infiere la familia por
    LER, producto, texto ni CIF, y no se pisa lo que ya hubiera."""
    repo = RepoDuplicadoFake()

    resultado = _run(repo, _envelope(con_contexto=False))

    assert resultado.duplicate is True
    assert repo.contextos == []


# ------------------------------------------------------------------ #
# Best-effort: la escritura nunca puede tumbar el re-proceso.
# ------------------------------------------------------------------ #

def test_f043_t31_una_escritura_que_revienta_no_rompe_el_duplicado():
    repo = RepoDuplicadoFake(falla_escritura=True)

    resultado = _run(repo, _envelope())

    assert resultado.ok is True
    assert resultado.duplicate is True


def test_f043_t31_un_repositorio_sin_el_metodo_no_rompe_el_duplicado():
    """Duck-typing: el puerto ``AlbaranRepository`` solo declara
    ``initialize``, ``get_by_sha256`` y ``save``."""

    class RepoSinMetodo:
        def initialize(self) -> None:
            return None

        def get_by_sha256(self, source_sha256: str) -> ExistingDocument:
            return ExistingDocument(
                document_id=_MERGE_ID,
                source_sha256=source_sha256,
                sharepoint_url=None,
                stored_lines=1,
            )

    resultado = _pipeline(RepoSinMetodo()).run(
        PersistAlbaranRequest(
            filename="SALMEDINA_0003967.pdf",
            mime_type="application/pdf",
            file_bytes=_PDF,
            extraction_envelope=_envelope(),
            context={},
        )
    )

    assert resultado.ok is True
    assert resultado.duplicate is True


# ------------------------------------------------------------------ #
# La escritura en si (repositorio), sin BBDD.
# ------------------------------------------------------------------ #

class _LineaOrmFake:
    def __init__(self, line_index: int, contexto_linea_json=None) -> None:
        self.line_index = line_index
        self.contexto_linea_json = contexto_linea_json


class _SesionFake:
    """Lo justo que usa ``update_merge_lineas_contexto``."""

    def __init__(self, lineas: list[_LineaOrmFake]) -> None:
        self.lineas = lineas
        self.commits = 0
        self.sentencias: list[str] = []

    def __enter__(self):
        return self

    def __exit__(self, *_exc) -> bool:
        return False

    def scalars(self, stmt):
        self.sentencias.append(str(stmt))
        return self

    def all(self):
        return sorted(self.lineas, key=lambda l: l.line_index)

    def commit(self) -> None:
        self.commits += 1


class _FabricaSesionFake:
    generation = 1

    def __init__(self, lineas: list[_LineaOrmFake]) -> None:
        self.sesion = _SesionFake(lineas)

    def ensure_database_and_engine(self) -> None:
        return None

    def create_session(self):
        return self.sesion


def _repositorio(lineas: list[_LineaOrmFake]):
    from infrastructure.database.sqlalchemy_albaran_repository import (
        SqlAlchemyAlbaranRepository,
    )

    fabrica = _FabricaSesionFake(lineas)
    repo = SqlAlchemyAlbaranRepository(fabrica)
    # El DDL no pinta en un test sin BBDD: se da por aplicado.
    repo._initialized_generation = fabrica.generation
    return repo, fabrica


def _lineas_del_envelope(envelope: dict):
    from domain.models.extraction_models import ExtractionEnvelope

    return ExtractionEnvelope.model_validate(envelope).data.lineas


def test_f043_t31_update_merge_lineas_contexto_escribe_por_line_index():
    """La linea 1 del sobre va a la fila ``line_index = 1``."""
    lineas_orm = [_LineaOrmFake(1)]
    repo, fabrica = _repositorio(lineas_orm)

    escritas = repo.update_merge_lineas_contexto(
        document_id=_MERGE_ID,
        lineas=_lineas_del_envelope(_envelope()),
    )

    assert escritas == 1
    assert fabrica.sesion.commits == 1
    import json

    guardado = json.loads(lineas_orm[0].contexto_linea_json)
    assert guardado["tipo_familia"] == "residuos"
    assert guardado["codigo_ler"] == "170604"
    assert guardado["volumen_m3"] == pytest.approx(6.0)


def test_f043_t31_update_merge_lineas_contexto_no_escribe_si_no_cuadran():
    """Si el sobre y el merge no tienen el MISMO numero de lineas no se
    empareja a ciegas: se deja como esta y se avisa. Escribir el
    contexto de otra linea es peor que no escribir ninguno."""
    lineas_orm = [_LineaOrmFake(1), _LineaOrmFake(2)]
    repo, fabrica = _repositorio(lineas_orm)

    escritas = repo.update_merge_lineas_contexto(
        document_id=_MERGE_ID,
        lineas=_lineas_del_envelope(_envelope()),
    )

    assert escritas == 0
    assert fabrica.sesion.commits == 0
    assert all(l.contexto_linea_json is None for l in lineas_orm)


def test_f043_t31_update_merge_lineas_contexto_no_borra_lo_que_ya_hay():
    """Un sobre sin contexto NO pisa el contexto que ya estuviera
    escrito: enriquecer nunca puede destruir (R27)."""
    lineas_orm = [_LineaOrmFake(1, contexto_linea_json='{"tipo_familia": "residuos"}')]
    repo, fabrica = _repositorio(lineas_orm)

    escritas = repo.update_merge_lineas_contexto(
        document_id=_MERGE_ID,
        lineas=_lineas_del_envelope(_envelope(con_contexto=False)),
    )

    assert escritas == 0
    assert fabrica.sesion.commits == 0
    assert lineas_orm[0].contexto_linea_json == '{"tipo_familia": "residuos"}'


def test_f043_t31_update_merge_lineas_contexto_sin_lineas_es_noop():
    repo, fabrica = _repositorio([])

    assert repo.update_merge_lineas_contexto(
        document_id=_MERGE_ID, lineas=[],
    ) == 0
    assert fabrica.sesion.commits == 0
