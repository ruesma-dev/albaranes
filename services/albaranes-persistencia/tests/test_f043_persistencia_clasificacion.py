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


# ------------------------------------------------------------------ #
# T15 · R22 — los seis campos se escriben en albaran_documents_merge.
# ------------------------------------------------------------------ #

def _envelope_validado(*, con_clasificacion: bool = True, **campos):
    """`ExtractionEnvelope` de sv3 con la clasificacion ya validada."""
    clasificacion = {**_CLASIFICACION, **campos}
    saneado = _sanear_envelope(_envelope_de_sv2(
        con_clasificacion=con_clasificacion,
    ))
    if con_clasificacion:
        saneado["data"]["clasificacion"] = clasificacion
    return ExtractionEnvelope.model_validate(saneado)


def _stored_file():
    from domain.models.persistence_models import StoredFile

    return StoredFile(
        drive_id="drive-de-prueba",
        item_id="item-de-prueba",
        relative_path="albaranes/2026/SS-0003967.pdf",
        web_url=None,
        share_url=None,
    )


def test_f043_r22_el_merge_conserva_la_clasificacion_y_la_persiste():
    """El merge multi-proveedor rehace `data` campo a campo. Si al
    rehacerlo no copia la clasificacion, se pierde AQUI —igual que se
    perdia en `meta`— y las seis columnas se quedan a NULL."""
    from application.services.albaran_confidence_service import (
        AlbaranConfidenceService,
    )

    analisis = AlbaranConfidenceService().build_merge_analysis(
        openai=_envelope_validado(),
        gemini=None,
    )

    assert analisis.merged_envelope.data.clasificacion is not None
    assert analisis.merged_envelope.data.clasificacion.familia == "residuos"


def test_f043_r22_persiste_los_seis_campos_del_documento():
    from infrastructure.database.sqlalchemy_albaran_repository import (
        campos_clasificacion_merge,
    )

    campos = campos_clasificacion_merge(
        _envelope_validado().data.clasificacion
    )

    assert campos == {
        "tipologia": "residuos",
        "tipologia_confianza_pct": 93.0,
        "tipologia_motivo": (
            "Gestor autorizado de RCD, codigos LER y contenedores."
        ),
        "tipologia_origen": "ia1",
        "tipologia_mixta": False,
        "tipologia_secundarias_json": "[]",
    }


def test_f043_r22_persiste_las_familias_secundarias_como_json():
    from infrastructure.database.sqlalchemy_albaran_repository import (
        campos_clasificacion_merge,
    )

    campos = campos_clasificacion_merge(
        _envelope_validado(
            mixto=True,
            familias_secundarias=["hormigon", "generico"],
        ).data.clasificacion
    )

    assert campos["tipologia_mixta"] is True
    assert campos["tipologia_secundarias_json"] == (
        '["hormigon", "generico"]'
    )


def test_f043_r22_no_persiste_clasificacion_cuando_el_envelope_no_la_trae():
    """R11/R27 · sv3 NO la inventa: columnas a NULL y a revision.

    Si sv3 escribiera aqui `generico`/0/`ausente`, sv5 leeria una
    clasificacion donde no la hay y los documentos anteriores a la
    feature dejarian de comportarse como hoy.
    """
    from infrastructure.database.sqlalchemy_albaran_repository import (
        campos_clasificacion_merge,
    )

    assert campos_clasificacion_merge(None) == {}


def test_f043_r22_persiste_recortando_lo_que_no_cabe_en_la_columna():
    """`tipologia` es VARCHAR(32) y `tipologia_origen` VARCHAR(16): un
    valor largo tumbaria el INSERT entero y con el, el albaran."""
    from infrastructure.database.sqlalchemy_albaran_repository import (
        campos_clasificacion_merge,
    )

    campos = campos_clasificacion_merge(
        _envelope_validado(familia="x" * 90, origen="y" * 90).data.clasificacion
    )

    assert campos["tipologia"] == "x" * 32
    assert campos["tipologia_origen"] == "y" * 16


def test_f043_r22_el_orm_del_merge_persiste_los_seis_campos():
    """Del envelope a la fila: el objeto ORM sale con los seis valores."""
    from infrastructure.database.orm_models import (
        AlbaranDocumentMergeOrm,
        AlbaranLineMergeOrm,
    )
    from infrastructure.database.sqlalchemy_albaran_repository import (
        SqlAlchemyAlbaranRepository,
        campos_clasificacion_merge,
    )

    envelope = _envelope_validado()
    repositorio = SqlAlchemyAlbaranRepository(session_factory=None)

    documento = repositorio._build_document_orm(
        orm_document_cls=AlbaranDocumentMergeOrm,
        orm_line_cls=AlbaranLineMergeOrm,
        document_id="doc-merge",
        provider_origin="openai_fallback",
        provider_envelope=envelope,
        context={},
        email_ctx={},
        document_ctx={},
        stored_file=_stored_file(),
        ia_input_payload={},
        ia_output_payload={},
        ia_input_relative_path=None,
        ia_input_web_url=None,
        ia_output_relative_path=None,
        ia_output_web_url=None,
        raw_lines=envelope.data.lineas,
        document_confidence_pct=88.0,
        review_required=False,
        review_reasons=[],
        comparison_summary={},
        line_results=None,
        campos_clasificacion=campos_clasificacion_merge(
            envelope.data.clasificacion
        ),
    )

    assert documento.tipologia == "residuos"
    assert documento.tipologia_confianza_pct == 93.0
    assert documento.tipologia_origen == "ia1"
    assert documento.tipologia_mixta is False
    assert documento.tipologia_secundarias_json == "[]"
    assert "Gestor autorizado" in documento.tipologia_motivo


def test_f043_r22_la_tabla_raw_no_persiste_la_clasificacion():
    """El mismo constructor sirve para las tablas por proveedor, que NO
    tienen esas columnas: sin campos, no se les cuela nada."""
    from infrastructure.database.orm_models import (
        AlbaranDocumentOrm,
        AlbaranLineOrm,
    )
    from infrastructure.database.sqlalchemy_albaran_repository import (
        SqlAlchemyAlbaranRepository,
    )

    envelope = _envelope_validado()
    repositorio = SqlAlchemyAlbaranRepository(session_factory=None)

    documento = repositorio._build_document_orm(
        orm_document_cls=AlbaranDocumentOrm,
        orm_line_cls=AlbaranLineOrm,
        document_id="doc-raw",
        provider_origin="openai",
        provider_envelope=envelope,
        context={},
        email_ctx={},
        document_ctx={},
        stored_file=_stored_file(),
        ia_input_payload={},
        ia_output_payload={},
        ia_input_relative_path=None,
        ia_input_web_url=None,
        ia_output_relative_path=None,
        ia_output_web_url=None,
        raw_lines=envelope.data.lineas,
        document_confidence_pct=88.0,
        review_required=None,
        review_reasons=None,
        comparison_summary=None,
        line_results=None,
    )

    assert not hasattr(documento, "tipologia")


# ------------------------------------------------------------------ #
# T16 · R11, R28, R29 — umbral configurable y motivos de revision.
# ------------------------------------------------------------------ #

def _motivos(*, umbral: float | None = None, **campos) -> list[str]:
    """Motivos de revision del merge para una clasificacion dada."""
    from application.services.albaran_confidence_service import (
        AlbaranConfidenceService,
    )

    servicio = (
        AlbaranConfidenceService()
        if umbral is None
        else AlbaranConfidenceService(clasificacion_confianza_minima_pct=umbral)
    )
    analisis = servicio.build_merge_analysis(
        openai=_envelope_validado(**campos),
        gemini=None,
    )
    return analisis.review_reasons


def test_f043_r28_motivos_confianza_por_debajo_del_umbral():
    assert "clasificacion_confianza_baja" in _motivos(confianza_pct=59.9)


def test_f043_r28_motivos_confianza_justo_en_el_umbral_no_lo_anade():
    """El umbral es «menor que», no «menor o igual»: 60 es suficiente."""
    assert "clasificacion_confianza_baja" not in _motivos(confianza_pct=60.0)


def test_f043_r28_motivos_el_umbral_es_configurable():
    """Con el umbral por defecto (60) una confianza de 93 no marca nada;
    subiendolo a 95, la misma clasificacion si."""
    assert "clasificacion_confianza_baja" not in _motivos(confianza_pct=93.0)
    assert "clasificacion_confianza_baja" in _motivos(
        umbral=95.0,
        confianza_pct=93.0,
    )


def test_f043_r28_motivos_el_umbral_por_defecto_es_60_y_lo_declara_settings():
    """Un solo numero: el que trae el servicio y el que declara la
    configuracion tienen que ser el mismo (F-023: cuatro sitios)."""
    from application.services.albaran_confidence_service import (
        UMBRAL_CLASIFICACION_CONFIANZA_POR_DEFECTO,
    )
    from config.settings import Settings

    campo = Settings.model_fields["clasificacion_confianza_minima_pct"]

    assert UMBRAL_CLASIFICACION_CONFIANZA_POR_DEFECTO == 60.0
    assert campo.default == UMBRAL_CLASIFICACION_CONFIANZA_POR_DEFECTO


def test_f043_r28_motivos_de_confianza_baja_mandan_el_documento_a_revision():
    from application.services.albaran_confidence_service import (
        AlbaranConfidenceService,
    )

    analisis = AlbaranConfidenceService().build_merge_analysis(
        openai=_envelope_validado(confianza_pct=10.0),
        gemini=None,
    )

    assert analisis.review_required is True
    assert "clasificacion_confianza_baja" in analisis.review_reasons
    assert "clasificacion_confianza_baja" in (
        analisis.comparison_summary["review_reasons"]
    )


def test_f043_r29_motivos_albaran_mixto():
    motivos = _motivos(mixto=True, familias_secundarias=["hormigon"])

    assert "clasificacion_mixta" in motivos


def test_f043_r29_motivos_un_albaran_de_una_sola_familia_no_lo_anade():
    assert "clasificacion_mixta" not in _motivos()


def test_f043_r11_motivos_clasificacion_ausente():
    """Envelope sin clasificacion (documento anterior a la feature)."""
    motivos = _motivos(con_clasificacion=False)

    assert "clasificacion_ausente" in motivos


def test_f043_r11_motivos_ia_sin_clasificacion_cuenta_como_ausente():
    """El caso REAL en produccion: sv2 si sella un bloque, pero con
    `origen='ausente'` porque la IA no clasifico. Es el mismo hueco."""
    motivos = _motivos(
        familia="generico",
        confianza_pct=0.0,
        motivo="ia_sin_clasificacion",
        origen="ausente",
    )

    assert "clasificacion_ausente" in motivos
    # El hueco se nombra UNA vez: la confianza 0 es consecuencia de que
    # no hay clasificacion, no un segundo problema que investigar.
    assert "clasificacion_confianza_baja" not in motivos


def test_f043_r11_motivos_sin_clasificacion_sv3_no_se_la_inventa():
    """PROHIBIDO deducir la familia por LER, texto, producto o CIF: el
    documento se queda sin clasificacion y va a revision."""
    from application.services.albaran_confidence_service import (
        AlbaranConfidenceService,
    )

    analisis = AlbaranConfidenceService().build_merge_analysis(
        openai=_envelope_validado(con_clasificacion=False),
        gemini=None,
    )

    assert analisis.merged_envelope.data.clasificacion is None
    assert analisis.review_required is True


def test_f043_r28_motivos_una_clasificacion_solida_no_anade_ninguno():
    motivos = _motivos()

    for motivo in (
        "clasificacion_confianza_baja",
        "clasificacion_mixta",
        "clasificacion_ausente",
    ):
        assert motivo not in motivos
