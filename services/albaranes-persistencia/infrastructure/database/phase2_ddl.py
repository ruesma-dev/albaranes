# infrastructure/database/phase2_ddl.py
"""DDL idempotente para soportar la persistencia de metadatos
de la revisión de fase 2 (sv2 phase-2).

Se aplica al arrancar sv3, después del DDL principal del repositorio.
Es 100% idempotente — todos los ALTER usan IF NOT EXISTS.

Columnas añadidas:

  En albaran_documents_merge:
    - review_phase2_status         VARCHAR(32)
        Resultado global de la fase 2: 'ok', 'ok_with_changes',
        'inconsistent', o NULL si fase 2 no se ejecutó.
    - review_phase2_summary        TEXT
        Explicación global breve devuelta por la fase 2.
    - review_phase2_changes_count  INTEGER
        Número de cambios propuestos por la fase 2 (no
        necesariamente todos aplicados).
    - review_phase2_payload_json   TEXT
        Payload completo en JSON: review_status, explicacion_global,
        cambios[], apply_summary, provider, model. Auditable para el
        algoritmo de confianza futuro.

    - tipologia                    VARCHAR(32)
    - tipologia_confianza_pct      DOUBLE PRECISION
    - tipologia_motivo             TEXT
    - tipologia_origen             VARCHAR(16)
    - tipologia_mixta              BOOLEAN
    - tipologia_secundarias_json   TEXT
        (F-043 · R22) La clasificación de DOCUMENTO que decidió la IA:
        familia, confianza, por qué, quién la puso ('ia1' | 'ia2' |
        'ausente'), si el albarán mezcla familias y cuáles son las
        secundarias (lista JSON). Llega en ``data.clasificacion`` del
        envelope —NO en ``meta``, que sv3 filtra y descartaba— y se
        persiste SOLO en el merge: las tablas ``albaran_documents`` son
        auditoría forense de lo que dijo cada proveedor.
        NULL cuando el envelope no traía clasificación (documentos
        anteriores a F-043): sv3 no la inventa, marca revisión (R11).
        Lectores acoplados a avisar si esto cambia: sv5 (SELECT con SQL
        crudo sobre el merge) y sv4 (ficha del documento).

    - contratos_busqueda_cif        VARCHAR(64)
    - contratos_busqueda_obra       VARCHAR(32)
    - contratos_busqueda_resultado  VARCHAR(16)
    - contratos_busqueda_at_utc     VARCHAR(64)
        (F-052 · R20) Rastro de la última búsqueda de contratos: CIF y
        obra normalizados, resultado ('encontrados' | 'ninguno' | 'error'
        | 'sin_datos') y fecha ISO UTC. Lo sella ContratoEnrichmentService
        al terminar cada búsqueda. Lector acoplado: sv4 (bloque de
        contrato de la ficha), que se despliega DESPUÉS de sv3. NULL en
        los documentos anteriores a F-052.

  En albaran_lines_merge:
    - source_phase                 VARCHAR(16) DEFAULT 'phase_1'
        'phase_1' si la línea proviene de la extracción inicial.
        'phase_2' si la línea fue modificada o introducida por la
        fase 2 (revisión).

  Tabla nueva albaran_altas_sigrid (F-053 · R36):
        Estado del alta en Sigrid de cada documento aprobado (una fila por
        documento, FK al merge con ON DELETE CASCADE). Tabla aparte y no
        columnas del merge porque el deshacer de sv4 restaura filas enteras
        del merge. La crea sv3 (dueño del schema del merge), la ESCRIBE
        SOLO sv9 (albaranes-alta-sigrid) y la LEE sv4. sv5 no la lee.
        Fechas en VARCHAR(64) ISO UTC, como el resto del merge.
"""
from __future__ import annotations

import logging

from sqlalchemy import text

from infrastructure.database.session_factory import SessionFactory

logger = logging.getLogger(__name__)


_PHASE2_DDL: tuple[str, ...] = (
    # albaran_documents_merge
    "ALTER TABLE albaran_documents_merge "
    "ADD COLUMN IF NOT EXISTS review_phase2_status VARCHAR(32)",
    "ALTER TABLE albaran_documents_merge "
    "ADD COLUMN IF NOT EXISTS review_phase2_summary TEXT",
    "ALTER TABLE albaran_documents_merge "
    "ADD COLUMN IF NOT EXISTS review_phase2_changes_count INTEGER",
    "ALTER TABLE albaran_documents_merge "
    "ADD COLUMN IF NOT EXISTS review_phase2_payload_json TEXT",
    "CREATE INDEX IF NOT EXISTS ix_albaran_documents_merge_review_phase2_status "
    "ON albaran_documents_merge(review_phase2_status)",

    # Origen determinista de cabecera (obra_codigo / proveedor_cif).
    "ALTER TABLE albaran_documents_merge "
    "ADD COLUMN IF NOT EXISTS obra_codigo_origen VARCHAR(24)",
    "ALTER TABLE albaran_documents_merge "
    "ADD COLUMN IF NOT EXISTS proveedor_cif_origen VARCHAR(24)",

    # Clasificacion de DOCUMENTO decidida por la IA (F-043 · R22).
    # Solo en el merge. Todas nullable: un documento anterior a la
    # feature no la trae y sv3 NO la reconstruye (R11).
    "ALTER TABLE albaran_documents_merge "
    "ADD COLUMN IF NOT EXISTS tipologia VARCHAR(32)",
    "ALTER TABLE albaran_documents_merge "
    "ADD COLUMN IF NOT EXISTS tipologia_confianza_pct DOUBLE PRECISION",
    "ALTER TABLE albaran_documents_merge "
    "ADD COLUMN IF NOT EXISTS tipologia_motivo TEXT",
    "ALTER TABLE albaran_documents_merge "
    "ADD COLUMN IF NOT EXISTS tipologia_origen VARCHAR(16)",
    "ALTER TABLE albaran_documents_merge "
    "ADD COLUMN IF NOT EXISTS tipologia_mixta BOOLEAN",
    "ALTER TABLE albaran_documents_merge "
    "ADD COLUMN IF NOT EXISTS tipologia_secundarias_json TEXT",
    "CREATE INDEX IF NOT EXISTS ix_albaran_documents_merge_tipologia "
    "ON albaran_documents_merge(tipologia)",

    # Rastro de la ultima busqueda de contratos (F-052 · R20). Solo en
    # el merge; todas nullable (un documento anterior no tiene rastro).
    "ALTER TABLE albaran_documents_merge "
    "ADD COLUMN IF NOT EXISTS contratos_busqueda_cif VARCHAR(64)",
    "ALTER TABLE albaran_documents_merge "
    "ADD COLUMN IF NOT EXISTS contratos_busqueda_obra VARCHAR(32)",
    "ALTER TABLE albaran_documents_merge "
    "ADD COLUMN IF NOT EXISTS contratos_busqueda_resultado VARCHAR(16)",
    "ALTER TABLE albaran_documents_merge "
    "ADD COLUMN IF NOT EXISTS contratos_busqueda_at_utc VARCHAR(64)",

    # Pie del albarán (F-075 · R15): base, tipo de IVA, cuota y total tal como
    # están impresos. En las DOS tablas de documento (por proveedor y merge),
    # como el resto de la cabecera. Todas nullable: un documento anterior no
    # lo trae. Lectores acoplados: sv5 lee el merge por nombre de columna (no
    # le afecta); sv4 las lee con SELECT defensivo.
    "ALTER TABLE albaran_documents "
    "ADD COLUMN IF NOT EXISTS base_imponible DOUBLE PRECISION",
    "ALTER TABLE albaran_documents "
    "ADD COLUMN IF NOT EXISTS tipo_iva_pct DOUBLE PRECISION",
    "ALTER TABLE albaran_documents "
    "ADD COLUMN IF NOT EXISTS cuota_iva DOUBLE PRECISION",
    "ALTER TABLE albaran_documents "
    "ADD COLUMN IF NOT EXISTS total_albaran DOUBLE PRECISION",
    "ALTER TABLE albaran_documents_merge "
    "ADD COLUMN IF NOT EXISTS base_imponible DOUBLE PRECISION",
    "ALTER TABLE albaran_documents_merge "
    "ADD COLUMN IF NOT EXISTS tipo_iva_pct DOUBLE PRECISION",
    "ALTER TABLE albaran_documents_merge "
    "ADD COLUMN IF NOT EXISTS cuota_iva DOUBLE PRECISION",
    "ALTER TABLE albaran_documents_merge "
    "ADD COLUMN IF NOT EXISTS total_albaran DOUBLE PRECISION",

    # albaran_lines_merge
    "ALTER TABLE albaran_lines_merge "
    "ADD COLUMN IF NOT EXISTS source_phase VARCHAR(16) "
    "NOT NULL DEFAULT 'phase_1'",
    "CREATE INDEX IF NOT EXISTS ix_albaran_lines_merge_source_phase "
    "ON albaran_lines_merge(source_phase)",

    # Alta en Sigrid de los aprobados (F-053 · R36, design §6). Va al final:
    # su FK apunta al merge, que ya existe cuando se aplica este DDL.
    "CREATE TABLE IF NOT EXISTS albaran_altas_sigrid ("
    "document_id VARCHAR(36) PRIMARY KEY "
    "REFERENCES albaran_documents_merge(id) ON DELETE CASCADE, "
    "estado VARCHAR(24) NOT NULL, "
    "modo VARCHAR(12), "
    "sigrid_con_ide INTEGER, "
    "sigrid_cod VARCHAR(24), "
    "adjunto_estado VARCHAR(16), "
    "sigrid_gra_ide INTEGER, "
    "motivos_json TEXT, "
    "avisos_json TEXT, "
    "peticion_json TEXT, "
    "respuesta_json TEXT, "
    "historial_json TEXT, "
    "intentos INTEGER NOT NULL DEFAULT 0, "
    "approved_at_utc VARCHAR(64), "
    "approved_by VARCHAR(255), "
    "ultimo_intento_at_utc VARCHAR(64), "
    "creado_at_utc VARCHAR(64) NOT NULL, "
    "actualizado_at_utc VARCHAR(64))",
    "CREATE INDEX IF NOT EXISTS ix_albaran_altas_sigrid_estado "
    "ON albaran_altas_sigrid (estado)",
)


def apply_phase2_ddl(session_factory: SessionFactory) -> None:
    """Ejecuta los ALTER de fase 2. Llamar después del initialize()
    principal del repositorio (que ya creó las tablas merge)."""
    with session_factory.create_session() as session:
        try:
            logger.info(
                "[svc3-ddl][phase2] Ejecutando %d sentencias DDL fase 2…",
                len(_PHASE2_DDL),
            )
            for stmt in _PHASE2_DDL:
                session.execute(text(stmt))
            session.commit()
            logger.info(
                "[svc3-ddl][phase2] DDL fase 2 OK. Columnas: "
                "albaran_documents_merge.review_phase2_*, "
                "albaran_documents_merge.tipologia*, "
                "albaran_documents_merge.contratos_busqueda_*, "
                "albaran_lines_merge.source_phase; tabla albaran_altas_sigrid"
            )
        except Exception:
            session.rollback()
            logger.exception(
                "[svc3-ddl][phase2] Fallo aplicando DDL fase 2; "
                "se continúa pero los UPDATE post-persist pueden fallar."
            )
