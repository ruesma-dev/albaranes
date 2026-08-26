# tests/test_f043_persistencia_clasificacion.py
"""F-043 · sv3 conserva, persiste y marca a revision la clasificacion.

Cubre el BLOQUE C de la feature:

- **R9** — la clasificacion SOBREVIVE al saneado de `meta` de sv3
  (`persistence_worker._sanear_envelope`), porque viaja dentro de `data`.
  El espejo `meta.tipologia` se sigue descartando: es exactamente el
  defecto que motivo la feature, y aqui queda escrito como test.
- **R22** — las seis columnas de `albaran_documents_merge` (DDL idempotente,
  ORM y escritura del merge).
- **R11, R28, R29** — motivos de revision `clasificacion_ausente`,
  `clasificacion_confianza_baja` y `clasificacion_mixta`.
- **R19** — motivo `linea_sin_familia_en_albaran_mixto` en las lineas que
  NO heredan la familia del documento.

Sin red, sin BBDD, sin LLM.
"""
from __future__ import annotations

from domain.models.extraction_models import ExtractionEnvelope
from interface_adapters.worker.persistence_worker import _sanear_envelope
from ruesma_comun.contratos import ClasificacionAlbaran

_CABECERA = {"proveedor_nombre": "SALMEDINA", "numero_albaran": "SS-0003967"}
_LINEAS = [{"concepto": "Contenedor RCD 6 m3", "cantidad": 1}]
_CLASIFICACION = {
    "familia": "residuos",
    "confianza_pct": 93.0,
    "motivo": "Gestor autorizado de RCD, codigos LER y contenedores.",
    "mixto": False,
    "familias_secundarias": [],
    "origen": "ia1",
}
_META = {
    "prompt_key": "albaran_revision_fase2_residuos",
    "schema": "albaran_v2",
    "source_filename": "SS-0003967.pdf",
    "source_mime_type": "application/pdf",
    "source_sha256": "0" * 64,
    "model": "modelo-de-prueba",
    "processed_at_utc": "2026-08-26T10:00:00Z",
}


def _envelope_de_sv2(*, con_clasificacion: bool = True) -> dict:
    """El envelope tal y como lo deja `phase_merge.construir_envelope_final`.

    `meta` trae las claves que sv3 NO declara (`phase`, `merged`, `provider`
    y el espejo `tipologia`); `data` trae la clasificacion de verdad.
    """
    data: dict = {"cabecera": dict(_CABECERA), "lineas": list(_LINEAS)}
    meta = {**_META, "phase": "phase_2", "merged": True, "provider": "openai"}
    if con_clasificacion:
        data["clasificacion"] = dict(_CLASIFICACION)
        meta["tipologia"] = _CLASIFICACION["familia"]
    return {"meta": meta, "data": data, "debug": {"phase_1": {}}}


# ------------------------------------------------------------------ #
# T13 · R9 — la clasificacion sobrevive al saneado de `meta`.
# ------------------------------------------------------------------ #

def test_f043_r9_sanear_conserva_la_clasificacion_dentro_de_data():
    saneado = _sanear_envelope(_envelope_de_sv2())

    assert saneado["data"]["clasificacion"] == _CLASIFICACION


def test_f043_r9_sanear_descarta_el_espejo_de_meta():
    """El defecto de origen, por escrito: `meta.tipologia` NO llega.

    `_sanear_envelope` filtra `meta` contra `ExtractionMeta`, que es
    `extra='forbid'`. Por eso la tipologia sellada en `meta` se perdia y
    sv5/sv6 la exigian sin recibirla nunca. Si alguien vuelve a colgarla
    de `meta`, este test le recuerda que ese camino sigue cerrado.
    """
    saneado = _sanear_envelope(_envelope_de_sv2())

    assert "tipologia" not in saneado["meta"]
    assert "phase" not in saneado["meta"]
    assert saneado["meta"]["prompt_key"] == _META["prompt_key"]


def test_f043_r9_sanear_no_toca_data_aunque_filtre_meta():
    """`data` se pasa TAL CUAL: el saneado es solo de `meta`."""
    envelope = _envelope_de_sv2()

    saneado = _sanear_envelope(envelope)

    assert saneado["data"] is envelope["data"]


def test_f043_r9_sanear_y_validar_deja_viva_la_clasificacion():
    """De la cola al modelo de sv3, el recorrido entero.

    Es el test de R9: sanear + validar con el `extra='forbid'` de sv3 y
    que la clasificacion siga ahi, ya como `ClasificacionAlbaran`.
    """
    saneado = _sanear_envelope(_envelope_de_sv2())

    envelope = ExtractionEnvelope.model_validate(saneado)

    assert isinstance(envelope.data.clasificacion, ClasificacionAlbaran)
    assert envelope.data.clasificacion.familia == "residuos"
    assert envelope.data.clasificacion.confianza_pct == 93.0
    assert envelope.data.clasificacion.origen == "ia1"


def test_f043_r27_sanear_un_envelope_anterior_sigue_validando_sin_ella():
    """Documento previo a la feature: mismo camino, `clasificacion` None."""
    saneado = _sanear_envelope(_envelope_de_sv2(con_clasificacion=False))

    envelope = ExtractionEnvelope.model_validate(saneado)

    assert envelope.data.clasificacion is None


# ------------------------------------------------------------------ #
# T14 · R22 — DDL idempotente, espejo en schema_contribution y ORM.
# ------------------------------------------------------------------ #

# Las seis columnas del diseño §3, con el tipo PostgreSQL que les toca.
_COLUMNAS_CLASIFICACION: tuple[tuple[str, str], ...] = (
    ("tipologia", "VARCHAR(32)"),
    ("tipologia_confianza_pct", "DOUBLE PRECISION"),
    ("tipologia_motivo", "TEXT"),
    ("tipologia_origen", "VARCHAR(16)"),
    ("tipologia_mixta", "BOOLEAN"),
    ("tipologia_secundarias_json", "TEXT"),
)
_INDICE_TIPOLOGIA = "ix_albaran_documents_merge_tipologia"


def _sentencias_de_clasificacion(sentencias: tuple[str, ...]) -> list[str]:
    """Las sentencias del DDL que hablan de las columnas nuevas."""
    return [s for s in sentencias if "tipologia" in s]


def test_f043_r22_el_ddl_anade_las_seis_columnas_al_merge():
    from infrastructure.database.phase2_ddl import _PHASE2_DDL

    for columna, tipo in _COLUMNAS_CLASIFICACION:
        esperado = (
            "ALTER TABLE albaran_documents_merge "
            f"ADD COLUMN IF NOT EXISTS {columna} {tipo}"
        )
        assert esperado in _PHASE2_DDL, f"falta el ALTER de {columna}"


def test_f043_r22_el_ddl_crea_el_indice_de_tipologia():
    from infrastructure.database.phase2_ddl import _PHASE2_DDL

    esperado = (
        f"CREATE INDEX IF NOT EXISTS {_INDICE_TIPOLOGIA} "
        "ON albaran_documents_merge(tipologia)"
    )

    assert esperado in _PHASE2_DDL


def test_f043_r22_el_ddl_de_clasificacion_es_idempotente():
    """Se ejecuta en CADA arranque, sobre bases que ya existen.

    Idempotente = re-ejecutarla no cambia nada ni revienta: todas las
    sentencias llevan `IF NOT EXISTS` y ninguna destruye o renombra.
    """
    from infrastructure.database.phase2_ddl import _PHASE2_DDL

    nuevas = _sentencias_de_clasificacion(_PHASE2_DDL)
    assert len(nuevas) == 7

    for sentencia in nuevas:
        assert "IF NOT EXISTS" in sentencia, sentencia
        for prohibido in ("DROP", "RENAME", "NOT NULL", "DELETE", "UPDATE"):
            assert prohibido not in sentencia, f"{prohibido} en {sentencia}"


def test_f043_r22_el_ddl_de_clasificacion_no_toca_las_tablas_raw():
    """Solo el merge: las `albaran_documents` son auditoria forense."""
    from infrastructure.database.phase2_ddl import _PHASE2_DDL

    for sentencia in _sentencias_de_clasificacion(_PHASE2_DDL):
        assert "albaran_documents_merge" in sentencia
        assert "albaran_lines" not in sentencia


def test_f043_r22_schema_contribution_espeja_el_ddl_de_clasificacion():
    """sv7 aplica el schema de sv3 desde aqui: si no lo espeja, las
    columnas no existen en la base que monta el orquestador."""
    from infrastructure.database.phase2_ddl import _PHASE2_DDL
    from infrastructure.database.schema_contribution import (
        get_ddl_statements,
    )

    exportadas = {sql for _, sql in get_ddl_statements()}

    for sentencia in _sentencias_de_clasificacion(_PHASE2_DDL):
        assert sentencia in exportadas, sentencia


def test_f043_r22_el_orm_del_merge_espeja_las_columnas_del_ddl():
    from infrastructure.database.orm_models import AlbaranDocumentMergeOrm

    columnas = AlbaranDocumentMergeOrm.__table__.columns

    for nombre, _ in _COLUMNAS_CLASIFICACION:
        assert nombre in columnas, f"el ORM no declara {nombre}"
        assert columnas[nombre].nullable, f"{nombre} debe admitir NULL"


def test_f043_r22_el_orm_de_la_tabla_raw_no_espeja_ese_ddl():
    """El ORM comparte mixin entre raw y merge: si las columnas caen en
    el mixin, se cuelan en `albaran_documents`, que no las quiere."""
    from infrastructure.database.orm_models import AlbaranDocumentOrm

    columnas = AlbaranDocumentOrm.__table__.columns

    for nombre, _ in _COLUMNAS_CLASIFICACION:
        assert nombre not in columnas, f"{nombre} se colo en la tabla raw"


def test_f043_r22_el_orm_indexa_la_tipologia_con_el_nombre_del_ddl():
    """Mismo nombre de indice que el DDL: si no, `CREATE INDEX IF NOT
    EXISTS` crearia un SEGUNDO indice sobre la misma columna."""
    from infrastructure.database.orm_models import AlbaranDocumentMergeOrm

    nombres = {
        indice.name for indice in AlbaranDocumentMergeOrm.__table__.indexes
    }

    assert _INDICE_TIPOLOGIA in nombres
