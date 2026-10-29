# infrastructure/database/review_repository.py
from __future__ import annotations

from urllib.parse import quote

import json
import logging
import math
import re
from datetime import datetime, timezone
from typing import Any
from urllib.parse import urlencode

from sqlalchemy import (
    bindparam,
    delete,
    func,
    inspect,
    literal_column,
    nullslast,
    or_,
    select,
    text,
)
from sqlalchemy.orm import object_session

from ruesma_comun.alta_sigrid import (
    ESTADOS_ALTA_BLOQUEANTES,
    es_linea_a_registrar,
    es_linea_vinculada,
)
from ruesma_comun.edicion_manual import CAMPO_IMPORTE, recalcular_fila
from ruesma_comun.importes import (
    clasificar_descuento,
    cuadra_linea,
    importe_albaran,
    importe_de_linea,
)
from ruesma_comun.linea_valorada import (
    CamposFila,
    LineaDeLaFila,
    cambios_a_guardar,
    fila_a_guardar,
    sin_conversion,
)
from ruesma_comun.obras import canonizar_codigo_obra
from ruesma_comun.valoracion import esta_valorado

# F-036: la comparación numérica vive en el dominio (`review_models`),
# con la reproducibilidad de la conversión (que F-065 usa en
# `cantidades_tras_editar`). Se importa con el nombre privado con el que
# la llama el resto de este módulo.
from domain.models.review_models import (
    AlbaranAprobadoError,
    aviso_reparto,
    cambia_origen,
    recalculo_de_fila,
    cantidades_tras_editar,
    cantidades_tras_reapuntar,
    aviso_partida_texto,
    coincide_partida,
    MOTIVO_UNIDAD_CAMBIADA,
    motivos_con,
    ConciliacionDisplay,
    ConciliacionSibling,
    ContratoLinePayload,
    ContratoPayload,
    DisplayLine,
    DivisionHecha,
    DocumentDetailPayload,
    DocumentListFilters,
    DocumentLineSummary,
    DocumentListItem,
    KNOWN_PROVIDER_VIEWS,
    LineaBloqueadaError,
    LineasIncompletasError,
    LineValuationPayload,
    MergeDocumentUpdatePayload,
    MergeLinePayload,
    motivos_de_json,
    numeros_iguales as _num_iguales,
    ObraOption,
    ObraResumenItem,
    PaginatedDocuments,
    ProveedorResumenItem,
    ProveedorOption,
    ProviderSnapshot,
    RastroBusquedaContratos,
    RESULTADOS_BUSQUEDA_CONTRATOS,
    ValuationPayload,
    VIEW_MODE_MERGE,
    normalize_view_mode,
    es_fila_manual,
    orden_filas_ficha,
    ParteDivision,
    RepartoInvalido,
    repartir,
)
from infrastructure.database.orm_models import (
    AlbaranContratoLineMergeOrm,
    AlbaranContratoMergeOrm,
    AlbaranDocumentBaseOrm,
    AlbaranDocumentMergeOrm,
    AlbaranLineBaseOrm,
    AlbaranLineMergeOrm,
)
from application.services.busqueda_contratos import estado_busqueda
from domain.services.almacen import (
    ACCION_ALMACEN_ELEGIDO,
    contar_con_partida,
    estado_partida,
)
from domain.models.alta_sigrid_models import (
    AlbaranBloqueadoError,
    AlbaranSinValorarError,
    AltaSigridVista,
)
from domain.services.confianza import compute_confianza_pct
from infrastructure.database.session_factory import SessionFactory

logger = logging.getLogger(__name__)


def _sanear_descuento(descuento_pct: float | None) -> float | None:
    """Descuento aplicable a esta línea, o None.

    Los rangos los decide `ruesma_comun.importes.clasificar_descuento`,
    compartido con sv6. Lo que este servicio pone encima es su POLÍTICA:
    un `0 %` se persiste como NULL —sv4 no distingue en su columna «0 %»
    de «sin descuento»— y un valor imposible deja aviso en el log.
    """
    estado, valor = clasificar_descuento(descuento_pct)
    if estado == "invalido":
        logger.warning(
            "[importe] descuento fuera de rango (0,100]: %s. Se ignora.",
            descuento_pct,
        )
        return None
    if estado != "aplicable":
        return None
    return valor


def _importe_de_linea(
    *,
    precio_unitario: float | None,
    cantidad: float | None,
    descuento_pct: float | None,
) -> float | None:
    """Importe de una línea. Único punto del BACKEND de sv4 que lo calcula.

    La fórmula canónica —`cantidad × precio × (1 − dto/100)`— vive en
    `ruesma_comun.importes`, compartida con sv6 (`ImporteCalculator`):
    `CLAUDE.md` (LÍMITE DE SERVICIO) prohíbe copiar lógica entre
    servicios, y estas dos copias ya habían empezado a divergir. Aquí
    queda solo la firma que usa este repositorio.

    F-019, round trip 2 (2026-08-18) — POR QUÉ HAY UN ÚNICO PUNTO
    ------------------------------------------------------------
    Esta fórmula estaba escrita CUATRO veces en este fichero y tres de
    ellas se dejaban el factor del descuento. sv6 valoró el albarán
    Feymaco 2.137.569 en sus 139,66 € correctos y, seis minutos después,
    el primer guardado del revisor lo dejó en 232,76 € recalculando
    `cantidad × precio` a secas sobre las cinco líneas. El descuento del
    40 % seguía escrito en `descuento_albaran_aplicado` —el UPDATE no lo
    tocaba—, lo que hacía el dato persistido internamente contradictorio
    y despistaba al leerlo.

    Regla: ningún sitio del **backend** de este servicio vuelve a
    multiplicar precio por cantidad por su cuenta. Si hace falta un
    importe, se pide aquí. (`templates/document_detail.html` y
    `static/app.js` tienen su propia copia para pintar al vuelo, ambas
    CON el descuento; el guardián estructural de los tests vigila el
    backend, que es quien persiste.)
    """
    return importe_de_linea(
        cantidad=cantidad,
        precio_unitario=precio_unitario,
        descuento_pct=descuento_pct,
    )



def _mismo_numero(a: Any, b: Any) -> bool:
    """(F-065 R8) ¿Es el mismo número? Para decidir si un campo editado
    cambia: tolerancia de coma flotante, no de dinero (``numeros_iguales``
    admite 5 milésimas y se tragaría un precio de 4 decimales o una cantidad
    de 3). Un valor ilegible no es igual a nada."""
    try:
        return abs(float(a) - float(b)) < 1e-9
    except (TypeError, ValueError):
        # ``float(None)`` también cae aquí: dos vacíos son el mismo «número».
        return a is None and b is None


#: (F-053) Tabla del alta en Sigrid: la crea sv3 (DDL) y la escribe SOLO sv9
#: (R34); sv4 solo la lee.
TABLA_ALTAS_SIGRID = "albaran_altas_sigrid"

#: (F-053 R26) Lectura del alta de UN documento, en su propia sentencia y
#: DESPUÉS del cerrojo del merge (ver ``_exigir_desbloqueado``).
_SQL_ALTA_DEL_DOCUMENTO = text(
    "SELECT estado, sigrid_cod FROM albaran_altas_sigrid WHERE document_id = :id"
)

# ---------------------------------------------------------------------- #
# (F-075 R19–R22) El importe de la bandeja: «manda el albarán».
#
# Una sola expresión SQL, portable (PostgreSQL y SQLite), para el orden, el
# filtro mín/máx, la tarjeta «Importe pendiente» y las vistas Obras y
# Proveedores: la suma de los ``precio_neto`` leídos del documento (sin IVA)
# si alguno trae importe; si no, el valorado de su última valoración CON
# filas (una cabecera sin filas, como la ``no_contract`` vacía, no es un
# valorado). Sustituye a ``LATERAL`` y ``DISTINCT ON`` (solo PostgreSQL);
# ``document_id`` es único en ``albaran_valuations``, así que «la última» es
# la única, y el ``ORDER BY id DESC`` lo deja dicho por si dejara de serlo.
# La misma regla, en Python, es ``ruesma_comun.importes.importe_albaran``.
# ---------------------------------------------------------------------- #
def sql_importe_albaran_documento(alias: str) -> str:
    """(F-075) Suma de los importes leídos del documento ``alias`` (o NULL)."""
    return (
        "(SELECT SUM(lm.precio_neto) FROM albaran_lines_merge lm "
        f"WHERE lm.document_id = {alias}.id)"
    )


def sql_valorado_documento(alias: str) -> str:
    """(F-075) ``total_valorado`` de la última valoración con filas (o NULL)."""
    return (
        "(SELECT av.total_valorado FROM albaran_valuations av "
        f"WHERE av.document_id = {alias}.id AND EXISTS ("
        "SELECT 1 FROM albaran_line_valuations alv WHERE alv.valuation_id = av.id) "
        "ORDER BY av.id DESC LIMIT 1)"
    )


def sql_importe_mostrado(alias: str) -> str:
    """(F-075 R19) La cifra de la columna «Importe» del documento ``alias``."""
    return (
        f"COALESCE({sql_importe_albaran_documento(alias)}, "
        f"{sql_valorado_documento(alias)})"
    )


#: (F-075 R23) El pie del merge (columnas de sv3), leído a la defensiva.
_SQL_PIE_MERGE = text(
    "SELECT base_imponible, tipo_iva_pct, cuota_iva, total_albaran "
    "FROM albaran_documents_merge WHERE id = :id"
)


#: (F-075 R19) Los importes leídos de los documentos de una página.
_SQL_IMPORTES_LEIDOS_DOCS = (
    "SELECT document_id, precio_neto FROM albaran_lines_merge "
    "WHERE document_id IN :ids"
)


#: (F-053 R29) El alta entera, para pintarla (sin cerrojo: solo lectura).
_SQL_ALTA_COMPLETA = text(
    "SELECT estado, modo, sigrid_con_ide, sigrid_cod, adjunto_estado, "
    "       motivos_json, avisos_json, peticion_json, respuesta_json, intentos, "
    "       approved_at_utc, approved_by, ultimo_intento_at_utc, actualizado_at_utc "
    "FROM albaran_altas_sigrid WHERE document_id = :id"
)

#: (F-053 R37) Estado de la valoración e importe de cada línea valorada.
_SQL_DATOS_VALORACION = text(
    "SELECT v.status AS status, lv.id AS linea_id, "
    "       lv.importe_calculado AS importe_calculado "
    "FROM albaran_valuations v "
    "LEFT JOIN albaran_line_valuations lv ON lv.valuation_id = v.id "
    "WHERE v.document_id = :id "
    "ORDER BY v.id, lv.id"
)


#: (F-053 R40, R41, R43) Lo que decide el producto de cada línea valorada: lo
#: mismo que lee sv9 al construir la petición (``SQL_LINEAS`` de sv9).
_SQL_LINEAS_PRODUCTO = text(
    "SELECT lv.id, lv.producto_sigrid, lv.importe_calculado, "
    "       lv.matched_contrato_line_id, lv.derived_contrato_line_id, "
    "       cl.sigrid_ide, cl.codigo_contrato AS contrato_linea, "
    "       cl.codigo_producto, l.contexto_linea_json, "
    "       v.contrato_codigo AS contrato_valoracion "
    "FROM albaran_valuations v "
    "JOIN albaran_line_valuations lv ON lv.valuation_id = v.id "
    "LEFT JOIN albaran_contrato_lines_merge cl ON cl.id = lv.matched_contrato_line_id "
    "LEFT JOIN albaran_lines_merge l ON l.id = lv.merge_line_id "
    "WHERE v.document_id = :doc "
    "ORDER BY lv.id"
)

_SQL_LINEA_PRODUCTO = text(
    "SELECT lv.id, lv.matched_contrato_line_id, lv.derived_contrato_line_id, "
    "       cl.sigrid_ide, cl.codigo_contrato AS contrato_linea, "
    "       v.contrato_codigo AS contrato_valoracion "
    "FROM albaran_line_valuations lv "
    "JOIN albaran_valuations v ON v.id = lv.valuation_id "
    "LEFT JOIN albaran_contrato_lines_merge cl ON cl.id = lv.matched_contrato_line_id "
    "WHERE lv.id = :lv AND v.document_id = :doc"
)


#: (F-065 R20) Las blancas del documento en el orden de la ficha.
_SQL_BLANCAS_EN_ORDEN = text(
    "SELECT id FROM albaran_lines_merge WHERE document_id = :doc "
    "ORDER BY line_index, id"
)

#: (F-065 R20) Lo que decide si una fila se puede aprobar y su posición; (F-078
#: R17) con su descripción y lo que dice si va vinculada (lo mismo que sv9).
_SQL_FILAS_PARA_APROBAR = text(
    "SELECT lv.id, lv.merge_line_id, lv.parent_merge_line_id, lv.line_kind, "
    "       lv.matched_contrato_line_id, lv.derived_contrato_line_id, "
    "       lv.cantidad_albaran, lv.cantidad_convertida, lv.importe_calculado, "
    "       lv.precio_unitario_final, lv.descuento_albaran_aplicado, "
    "       lv.review_reasons_json, lv.descripcion_linea, "
    "       cl.sigrid_ide, cl.codigo_contrato AS contrato_linea, "
    "       v.contrato_codigo AS contrato_valoracion "
    "FROM albaran_line_valuations lv "
    "JOIN albaran_valuations v ON v.id = lv.valuation_id "
    "LEFT JOIN albaran_contrato_lines_merge cl ON cl.id = lv.matched_contrato_line_id "
    "WHERE v.document_id = :doc"
)

#: (F-078 R16) La fila, su línea (de contrato o derivada) y el concepto de su
#: blanca: lo que decide ``fila_a_guardar``.
_SQL_FILA_A_MATERIALIZAR = text(
    "SELECT lv.descripcion_linea, lv.unidad_contrato, lv.unidad_albaran, "
    "       lv.precio_unitario_final, lv.cantidad_albaran, lv.cantidad_convertida, "
    "       lv.factor_conversion, "
    "       cl.id AS cl_id, cl.descripcion_linea AS cl_descripcion, "
    "       cl.unidad_medida AS cl_unidad, cl.precio_unitario AS cl_precio, "
    "       d.id AS d_id, d.descripcion_linea AS d_descripcion, "
    "       d.unidad_medida AS d_unidad, d.precio_unitario AS d_precio, "
    "       l.concepto AS concepto_blanca "
    "FROM albaran_line_valuations lv "
    "LEFT JOIN albaran_contrato_lines_merge cl ON cl.id = lv.matched_contrato_line_id "
    "LEFT JOIN contrato_lines_derived d ON d.id = lv.derived_contrato_line_id "
    "LEFT JOIN albaran_lines_merge l ON l.id = lv.merge_line_id "
    "WHERE lv.id = :vid"
)

#: Las columnas de la fila que decide ``fila_a_guardar`` (las de ``CamposFila``).
_COLUMNAS_FILA_A_GUARDAR = (
    "descripcion_linea", "unidad_contrato", "unidad_albaran", "precio_unitario_final",
    "cantidad_albaran", "cantidad_convertida", "factor_conversion",
)


def _linea_de_la_fila(fila: Any) -> LineaDeLaFila | None:
    """(F-078) Su línea: la de contrato si la tiene; si no, su derivada (el
    mismo orden con el que la ficha decide Contrato / Nueva)."""
    if fila["cl_id"] is not None:
        return LineaDeLaFila(
            es_contrato=True, descripcion=fila["cl_descripcion"],
            unidad=fila["cl_unidad"], precio_unitario=fila["cl_precio"],
        )
    if fila["d_id"] is not None:
        return LineaDeLaFila(
            es_contrato=False, descripcion=fila["d_descripcion"],
            unidad=fila["d_unidad"], precio_unitario=fila["d_precio"],
        )
    return None


#: (F-065 R14) ¿Está guardada (bloqueada) esta fila del documento?
_SQL_FILA_BLOQUEADA = text(
    "SELECT lv.bloqueada FROM albaran_line_valuations lv "
    "JOIN albaran_valuations v ON v.id = lv.valuation_id "
    "WHERE lv.id = :vid AND v.document_id = :doc"
)


def _json_o(valor: Any, defecto: Any, tipo: type) -> Any:
    """JSON de una columna de texto, o ``defecto`` si falta, no se lee o no es
    del ``tipo`` esperado: un JSON roto no puede dejar sin abrir la ficha."""
    if valor in (None, ""):
        return defecto
    try:
        leido = json.loads(valor)
    except (TypeError, ValueError):
        return defecto
    return leido if isinstance(leido, tipo) else defecto


def _partida_del_contrato(conc: ConciliacionDisplay) -> str | None:
    """Partida del CONTRATO contra la que se comparan los avisos ✓/⚠.

    (F-051, review pasada 2) ``codigo_partida`` es ya la partida final
    (la que se pinta); la del contrato es la de la línea casada. En
    almacén no hay nada que comparar (sin aviso, como antes).
    """
    if conc.estado_partida == "almacen":
        return None
    return conc.codigo_partida_casada


class AlbaranReviewRepository:
    def __init__(self, session_factory: SessionFactory) -> None:
        self._session_factory = session_factory
        self._initialized = False

    def initialize(self) -> bool:
        """Inicialización idempotente y robusta.

        Ejecuta los DDLs de compatibilidad del servicio 4 (añade
        columnas ``approved``, ``approved_at_utc``, etc., crea índices,
        etc.) sobre las tablas que ya creó el servicio 3.

        IMPORTANTE: sólo marcamos ``self._initialized = True`` CUANDO
        los DDLs se ejecutan con éxito. Si las tablas del servicio 3
        todavía no existen cuando arrancamos, devolvemos False y
        dejamos ``_initialized = False`` para reintentar en la próxima
        llamada (la primera GET /documents, por ejemplo).

        Antes, si el svc4 arrancaba antes que el svc3 creara las
        tablas, marcábamos initialized=True sin haber ejecutado nada,
        y cuando el svc3 ya había creado las tablas después, el svc4
        nunca llegaba a añadir sus columnas → la primera query cascaba
        por 'no existe columna approved'.
        """
        if self._initialized and self._tables_ready():
            return True

        # Rename legacy tables si existieran.
        self._rename_legacy_tables_if_needed()

        # Si las tablas del servicio 3 todavía no existen, no podemos
        # aplicar los ALTER. Devolvemos False (no cacheamos) para que
        # la próxima llamada reintente.
        if not self._tables_ready():
            return False

        with self._session_factory.create_session() as session:
            for ddl in self._review_schema_statements():
                session.execute(text(ddl))
            session.commit()

        self._initialized = True
        return True

    def _tables_ready(self) -> bool:
        inspector = inspect(self._session_factory.engine)
        return inspector.has_table("albaran_documents_merge") and inspector.has_table(
            "albaran_lines_merge"
        )

    def _rename_legacy_tables_if_needed(self) -> None:
        inspector = inspect(self._session_factory.engine)
        has_merge_docs = inspector.has_table("albaran_documents_merge")
        has_merge_lines = inspector.has_table("albaran_lines_merge")
        has_gem_docs = inspector.has_table("albaran_documents_gem")
        has_gem_lines = inspector.has_table("albaran_lines_gem")

        if (not has_merge_docs) and has_gem_docs:
            with self._session_factory.engine.begin() as connection:
                connection.execute(
                    text("ALTER TABLE albaran_documents_gem RENAME TO albaran_documents_merge")
                )
        if (not has_merge_lines) and has_gem_lines:
            with self._session_factory.engine.begin() as connection:
                connection.execute(
                    text("ALTER TABLE albaran_lines_gem RENAME TO albaran_lines_merge")
                )

    @staticmethod
    def _review_schema_statements() -> list[str]:
        return [
            "ALTER TABLE albaran_documents_merge ADD COLUMN IF NOT EXISTS approved BOOLEAN",
            "UPDATE albaran_documents_merge SET approved = FALSE WHERE approved IS NULL",
            "ALTER TABLE albaran_documents_merge ALTER COLUMN approved SET DEFAULT FALSE",
            "ALTER TABLE albaran_documents_merge ALTER COLUMN approved SET NOT NULL",
            "ALTER TABLE albaran_documents_merge ADD COLUMN IF NOT EXISTS approved_at_utc VARCHAR(64)",
            "ALTER TABLE albaran_documents_merge ADD COLUMN IF NOT EXISTS approved_by VARCHAR(255)",
            "ALTER TABLE albaran_documents_merge ADD COLUMN IF NOT EXISTS reviewed_at_utc VARCHAR(64)",
            "ALTER TABLE albaran_documents_merge ADD COLUMN IF NOT EXISTS last_modified_at_utc VARCHAR(64)",
            "ALTER TABLE albaran_documents_merge ADD COLUMN IF NOT EXISTS review_notes TEXT",
            "ALTER TABLE albaran_documents_merge ADD COLUMN IF NOT EXISTS selected_contrato_codigo VARCHAR(64)",
            "ALTER TABLE albaran_documents_merge ADD COLUMN IF NOT EXISTS selected_contrato_origen VARCHAR(32)",
            # Soft-delete (jun 2026). Defensa idempotente: normalmente las crea
            # sv3 (dueño del schema), pero si sv4 arranca primero en local, las
            # añadimos aquí para poder borrar/restaurar sin esperar a sv3. El
            # índice único parcial lo gobierna sv3.
            "ALTER TABLE albaran_documents_merge ADD COLUMN IF NOT EXISTS is_active BOOLEAN NOT NULL DEFAULT true",
            "ALTER TABLE albaran_documents_merge ADD COLUMN IF NOT EXISTS deleted_at_utc VARCHAR(64)",
            "ALTER TABLE albaran_documents_merge ADD COLUMN IF NOT EXISTS deleted_by VARCHAR(255)",
            "ALTER TABLE albaran_contratos_merge ADD COLUMN IF NOT EXISTS gra_rep_ide INTEGER",
            # Edición de la línea salmon (jun 2026): campos que viajarán a
            # Sigrid al insertar el albarán pero que no existen allí.
            # descuento_albaran_aplicado la crea sv6 en BBDD nuevas; la
            # añadimos defensivamente para BBDD antiguas. codigo_externo es
            # exclusiva de sv4 (sv6 no la toca: queda NULL al re-valorar).
            "ALTER TABLE albaran_line_valuations ADD COLUMN IF NOT EXISTS descuento_albaran_aplicado DOUBLE PRECISION",
            "ALTER TABLE albaran_line_valuations ADD COLUMN IF NOT EXISTS codigo_externo VARCHAR(64)",
            # (F-065 R17) Fila guardada = bloqueada. La declara sv6 (dueño
            # del esquema de valoración); aquí, defensiva como las de arriba.
            (
                "ALTER TABLE albaran_line_valuations ADD COLUMN IF NOT EXISTS bloqueada "
                "BOOLEAN NOT NULL DEFAULT FALSE"
            ),
            (
                "ALTER TABLE albaran_contratos_merge "
                "ADD COLUMN IF NOT EXISTS pdf_sharepoint_relative_path VARCHAR(1024)"
            ),
            (
                "ALTER TABLE albaran_contratos_merge "
                "ADD COLUMN IF NOT EXISTS pdf_sharepoint_web_url VARCHAR(1024)"
            ),
            """
            CREATE TABLE IF NOT EXISTS albaran_contrato_lines_merge (
                id                     SERIAL PRIMARY KEY,
                contrato_id            INTEGER NOT NULL
                    REFERENCES albaran_contratos_merge(id) ON DELETE CASCADE,
                codigo_contrato        VARCHAR(64) NOT NULL,
                linea                  INTEGER,
                numero_linea           INTEGER,
                codigo_producto        VARCHAR(64),
                codigo_alternativo     VARCHAR(64),
                unidad_medida          VARCHAR(32),
                descripcion_linea      TEXT,
                uds                    DOUBLE PRECISION,
                cantidad_servida       DOUBLE PRECISION,
                cantidad_facturada     DOUBLE PRECISION,
                pendiente_servir       DOUBLE PRECISION,
                precio_unitario        DOUBLE PRECISION,
                precio_bruto           DOUBLE PRECISION,
                descuentos             DOUBLE PRECISION,
                importe_linea          DOUBLE PRECISION,
                cuota_iva              DOUBLE PRECISION,
                doc_origen             VARCHAR(64),
                codigo_partida         VARCHAR(64),
                descripcion_partida    TEXT,
                fetched_at_utc         VARCHAR(64) NOT NULL
            )
            """,
            (
                "ALTER TABLE albaran_contrato_lines_merge "
                "ADD COLUMN IF NOT EXISTS codigo_partida VARCHAR(64)"
            ),
            (
                "ALTER TABLE albaran_contrato_lines_merge "
                "ADD COLUMN IF NOT EXISTS descripcion_partida TEXT"
            ),
            (
                "CREATE INDEX IF NOT EXISTS ix_albaran_contrato_lines_merge_contrato_id "
                "ON albaran_contrato_lines_merge (contrato_id)"
            ),
            (
                "CREATE INDEX IF NOT EXISTS ix_albaran_contrato_lines_merge_codigo "
                "ON albaran_contrato_lines_merge (codigo_contrato)"
            ),
            (
                "CREATE INDEX IF NOT EXISTS ix_albaran_contrato_lines_merge_partida "
                "ON albaran_contrato_lines_merge (codigo_partida)"
            ),
            (
                "CREATE INDEX IF NOT EXISTS ix_albaran_documents_merge_approved "
                "ON albaran_documents_merge (approved)"
            ),
            (
                "CREATE INDEX IF NOT EXISTS ix_albaran_documents_merge_conf_calc "
                "ON albaran_documents_merge (confidence_pct_calc)"
            ),
        ]

    def list_documents(self, filters: DocumentListFilters) -> PaginatedDocuments:
        self.initialize()
        if not self._tables_ready():
            return PaginatedDocuments(
                items=[],
                total=0,
                page=filters.page,
                page_size=filters.page_size,
                total_pages=0,
                approved_count=0,
                pending_count=0,
                review_required_count=0,
            )

        with self._session_factory.create_session() as session:
            stmt = select(AlbaranDocumentMergeOrm)
            stmt = self._apply_filters(stmt=stmt, filters=filters)
            total = session.scalar(select(func.count()).select_from(stmt.subquery())) or 0
            stmt = self._apply_sort(stmt=stmt, filters=filters)
            stmt = stmt.offset((filters.page - 1) * filters.page_size).limit(filters.page_size)
            rows = session.scalars(stmt).all()

            # Recalcular la confianza determinista de los documentos de esta
            # pagina que tengan valoracion, para que la LISTA muestre la
            # confianza de VALORACION (no la de extraccion IA) en cuanto el
            # pipeline valora, sin necesidad de abrir el documento.
            for _row in rows:
                try:
                    self._compute_and_persist_confianza(
                        session=session, merge_doc=_row
                    )
                except Exception:
                    # Best-effort: un documento problematico no debe tumbar
                    # el listado; conserva el valor previo.
                    pass

            approved_count = session.scalar(
                select(func.count()).select_from(AlbaranDocumentMergeOrm).where(
                    AlbaranDocumentMergeOrm.approved.is_(True),
                    AlbaranDocumentMergeOrm.is_active.is_(True),
                )
            ) or 0
            pending_count = session.scalar(
                select(func.count()).select_from(AlbaranDocumentMergeOrm).where(
                    AlbaranDocumentMergeOrm.approved.is_(False),
                    AlbaranDocumentMergeOrm.is_active.is_(True),
                )
            ) or 0
            review_required_count = session.scalar(
                select(func.count()).select_from(AlbaranDocumentMergeOrm).where(
                    AlbaranDocumentMergeOrm.review_required.is_(True),
                    AlbaranDocumentMergeOrm.is_active.is_(True),
                )
            ) or 0
            # Soft-delete (jun 2026): nº de albaranes en la papelera, para
            # el contador del enlace.
            trash_count = session.scalar(
                select(func.count()).select_from(AlbaranDocumentMergeOrm).where(
                    AlbaranDocumentMergeOrm.is_active.is_(False)
                )
            ) or 0
            # Importe total pendiente de aprobar (F-075 R22): suma del
            # importe de la bandeja (albarán o, si no, valorado) de los
            # albaranes activos NO aprobados.
            try:
                importe_pendiente_aprobar = session.scalar(
                    text(
                        f"SELECT COALESCE(SUM({sql_importe_mostrado('d')}), 0) "
                        "FROM albaran_documents_merge d "
                        "WHERE d.is_active = TRUE AND d.approved = FALSE"
                    )
                ) or 0.0
            except Exception:
                session.rollback()
                logger.warning(
                    "[bandeja] no se pudo sumar el importe pendiente; se pinta 0.",
                    exc_info=True,
                )
                importe_pendiente_aprobar = 0.0

            # Columnas nuevas de la lista: importe total valorado (de la
            # valoracion, por document_id) y nombre del contrato seleccionado
            # (por codigo, busqueda compartida). Dos consultas batch.
            doc_ids = [r.id for r in rows]
            totals_by_doc: dict[str, float | None] = {}
            # F-053 R37: estado de la valoración e importes, para «valorado».
            status_by_doc: dict[str, str | None] = {}
            importes_by_doc: dict[str, list[float | None]] = {}
            # F-053 R31: estado del alta en Sigrid de cada fila.
            alta_by_doc: dict[str, str] = {}
            names_by_code: dict[str, str | None] = {}
            lines_by_doc: dict[str, list[DocumentLineSummary]] = {}
            # (F-075 R19) Importes leídos por documento (``precio_neto``).
            leidos_by_doc: dict[str, list[float | None]] = {}
            importe_error = False
            if doc_ids:
                try:
                    for ir in session.execute(
                        text(_SQL_IMPORTES_LEIDOS_DOCS).bindparams(
                            bindparam("ids", expanding=True)
                        ),
                        {"ids": doc_ids},
                    ).mappings():
                        leidos_by_doc.setdefault(ir["document_id"], []).append(
                            ir["precio_neto"]
                        )
                except Exception:
                    # (F-075 R25) La bandeja se pinta igual, con «—».
                    session.rollback()
                    importe_error = True
                    logger.warning(
                        "[bandeja] no se pudo leer el importe del albarán; "
                        "la columna Importe se pinta con «—».",
                        exc_info=True,
                    )
                try:
                    for vr in session.execute(
                        text(
                            "SELECT document_id, total_valorado, status "
                            "FROM albaran_valuations "
                            "WHERE document_id IN :ids"
                        ).bindparams(bindparam("ids", expanding=True)),
                        {"ids": doc_ids},
                    ).mappings():
                        totals_by_doc[vr["document_id"]] = vr["total_valorado"]
                        status_by_doc[vr["document_id"]] = vr["status"]
                except Exception:
                    session.rollback()
                codes = sorted({
                    r.selected_contrato_codigo for r in rows
                    if getattr(r, "selected_contrato_codigo", None)
                })
                if codes:
                    try:
                        for cr in session.execute(
                            text(
                                "SELECT codigo_contrato, nombre_contrato "
                                "FROM albaran_contratos_merge "
                                "WHERE codigo_contrato IN :codes"
                            ).bindparams(bindparam("codes", expanding=True)),
                            {"codes": codes},
                        ).mappings():
                            names_by_code[cr["codigo_contrato"]] = (
                                cr["nombre_contrato"]
                            )
                    except Exception:
                        session.rollback()

                # Líneas salmón (valores de valoración aplicados) de TODOS
                # los documentos en una sola consulta, para la vista rápida
                # de la bandeja. Solo lectura. Mismo orden que el detalle:
                # base (from_albaran) primero, luego sintéticas.
                try:
                    for lr in session.execute(
                        text(
                            "SELECT v.document_id AS document_id, "
                            "       lv.line_kind AS line_kind, "
                            "       lv.codigo_partida_final AS codigo_partida_final, "
                            "       lv.codigo_partida_albaran AS codigo_partida_albaran, "
                            # Concepto IGUAL que el detalle: la edición del
                            # revisor (lv.descripcion_linea) tiene prioridad;
                            # si está vacía (caso de la línea base), se toma
                            # la descripción de la línea de contrato casada
                            # (matched) o derivada (derived).
                            "       COALESCE(NULLIF(lv.descripcion_linea, ''), "
                            "                mcl.descripcion_linea, "
                            "                dcl.descripcion_linea) AS concepto, "
                            "       lv.cantidad_convertida AS cantidad_convertida, "
                            "       lv.cantidad_albaran AS cantidad_albaran, "
                            "       lv.unidad_contrato AS unidad_contrato, "
                            "       lv.unidad_albaran AS unidad_albaran, "
                            "       lv.precio_unitario_final AS precio_unitario_final, "
                            "       lv.importe_calculado AS importe_calculado "
                            "FROM albaran_line_valuations lv "
                            "JOIN albaran_valuations v ON v.id = lv.valuation_id "
                            "LEFT JOIN albaran_contrato_lines_merge mcl "
                            "       ON mcl.id = lv.matched_contrato_line_id "
                            "LEFT JOIN albaran_contrato_lines_merge dcl "
                            "       ON dcl.id = lv.derived_contrato_line_id "
                            "WHERE v.document_id IN :ids "
                            "ORDER BY v.document_id, "
                            "  CASE WHEN lv.line_kind = 'synthetic_modifier' "
                            "       THEN 1 ELSE 0 END, "
                            "  lv.merge_line_id NULLS LAST, lv.id"
                        ).bindparams(bindparam("ids", expanding=True)),
                        {"ids": doc_ids},
                    ).mappings():
                        _did = lr["document_id"]
                        importes_by_doc.setdefault(_did, []).append(
                            lr["importe_calculado"]
                        )
                        _cant = lr["cantidad_convertida"]
                        if _cant is None:
                            _cant = lr["cantidad_albaran"]
                        lines_by_doc.setdefault(_did, []).append(
                            DocumentLineSummary(
                                kind=(lr["line_kind"] or "from_albaran"),
                                codigo_partida=(
                                    lr["codigo_partida_final"]
                                    or lr["codigo_partida_albaran"]
                                ),
                                concepto=lr["concepto"],
                                cantidad=_cant,
                                unidad=(
                                    lr["unidad_contrato"]
                                    or lr["unidad_albaran"]
                                ),
                                precio_unitario=lr["precio_unitario_final"],
                                importe=lr["importe_calculado"],
                            )
                        )
                except Exception:
                    session.rollback()

                if self._existe_tabla_altas(session):
                    for ar in session.execute(
                        text(
                            "SELECT document_id, estado FROM albaran_altas_sigrid "
                            "WHERE document_id IN :ids"
                        ).bindparams(bindparam("ids", expanding=True)),
                        {"ids": doc_ids},
                    ).mappings():
                        alta_by_doc[ar["document_id"]] = str(ar["estado"])

        importes_doc = {
            doc_id: importe_albaran(leidos) for doc_id, leidos in leidos_by_doc.items()
        }
        sin_lineas = importe_albaran([])
        items = [
            self._to_list_item(
                row,
                # (F-075) Sin filas no hay valorado (cabecera no_contract vacía).
                total_valorado=(
                    totals_by_doc.get(row.id) if row.id in importes_by_doc else None
                ),
                contrato_codigo=getattr(row, "selected_contrato_codigo", None),
                contrato_nombre=names_by_code.get(
                    getattr(row, "selected_contrato_codigo", None)
                ),
                lines=lines_by_doc.get(row.id),
            ).model_copy(update={
                "valorado": esta_valorado(
                    status_by_doc.get(row.id), importes_by_doc.get(row.id, []),
                ),
                "alta_estado": alta_by_doc.get(row.id),
                "importe_albaran": importes_doc.get(row.id, sin_lineas).total,
                "lineas_albaran": importes_doc.get(row.id, sin_lineas).lineas,
                "lineas_con_importe": importes_doc.get(row.id, sin_lineas).lineas_con_importe,
                "importe_error": importe_error,
            })
            for row in rows
        ]
        total_pages = math.ceil(total / filters.page_size) if total else 0
        return PaginatedDocuments(
            items=items,
            total=int(total),
            page=filters.page,
            page_size=filters.page_size,
            total_pages=total_pages,
            approved_count=int(approved_count),
            pending_count=int(pending_count),
            review_required_count=int(review_required_count),
            trash_count=int(trash_count),
            importe_pendiente_aprobar=float(importe_pendiente_aprobar or 0.0),
        )

    # ------------------------------------------------------------------ #
    # Vistas agregadas: Obras y Proveedores (jul 2026)
    # ------------------------------------------------------------------ #
    def list_obras_resumen(
        self, *, search: str | None = None,
    ) -> list[ObraResumenItem]:
        """Resumen de albaranes ACTIVOS agrupados por obra.

        Una fila por ``obra_codigo`` (los sin obra se agrupan bajo la
        fila con codigo NULL) con contadores de estado, el importe
        valorado agregado (ultima valoracion por documento, mismo
        criterio DISTINCT-por-documento que la bandeja) y la fecha de
        albaran mas reciente. Best-effort: ante error devuelve [].
        """
        self.initialize()
        if not self._tables_ready():
            return []
        sql = (
            "SELECT d.obra_codigo AS obra_codigo, "
            "       MAX(NULLIF(d.obra_nombre, '')) AS obra_nombre, "
            "       COUNT(*) AS total_albaranes, "
            "       COUNT(*) FILTER (WHERE d.approved = FALSE) "
            "           AS pendientes, "
            "       COUNT(*) FILTER (WHERE d.approved = TRUE) "
            "           AS aprobados, "
            "       COUNT(*) FILTER (WHERE d.review_required = TRUE) "
            "           AS revision_requerida, "
            # (F-075 R22) El importe de la bandeja, sumado por documento.
            f"       COALESCE(SUM({sql_importe_mostrado('d')}), 0) AS importe, "
            "       MAX(d.fecha) AS ultima_fecha "
            "FROM albaran_documents_merge d "
            "WHERE d.is_active = TRUE "
        )
        params: dict[str, Any] = {}
        if search and search.strip():
            sql += (
                "AND (d.obra_codigo ILIKE :term "
                "     OR d.obra_nombre ILIKE :term) "
            )
            params["term"] = f"%{search.strip()}%"
        sql += (
            "GROUP BY d.obra_codigo "
            "ORDER BY pendientes DESC, total_albaranes DESC, "
            "         obra_codigo ASC NULLS LAST"
        )
        try:
            with self._session_factory.create_session() as session:
                rows = session.execute(text(sql), params).mappings().all()
        except Exception:
            logger.exception("[obras-resumen] consulta fallo; se devuelve [].")
            return []
        return [
            ObraResumenItem(
                obra_codigo=r["obra_codigo"],
                obra_nombre=r["obra_nombre"],
                total_albaranes=int(r["total_albaranes"] or 0),
                pendientes=int(r["pendientes"] or 0),
                aprobados=int(r["aprobados"] or 0),
                revision_requerida=int(r["revision_requerida"] or 0),
                importe=float(r["importe"] or 0.0),
                ultima_fecha=(
                    str(r["ultima_fecha"]) if r["ultima_fecha"] else None
                ),
            )
            for r in rows
        ]

    def list_proveedores_resumen(
        self, *, search: str | None = None,
    ) -> list[ProveedorResumenItem]:
        """Resumen de albaranes ACTIVOS agrupados por proveedor.

        Se agrupa por CIF NORMALIZADO (mayusculas, sin espacios) para que
        variantes tipo "B 123" y "B123" caigan juntas; los documentos SIN
        CIF se agrupan por nombre (en minusculas) para no mezclarlos.
        Best-effort: ante error devuelve [].
        """
        self.initialize()
        if not self._tables_ready():
            return []
        sql = (
            "SELECT NULLIF(MAX(UPPER(REPLACE("
            "           TRIM(COALESCE(d.proveedor_cif, '')), ' ', ''))), '') "
            "           AS proveedor_cif, "
            "       MAX(NULLIF(d.proveedor_nombre, '')) AS proveedor_nombre, "
            "       COUNT(*) AS total_albaranes, "
            "       COUNT(*) FILTER (WHERE d.approved = FALSE) "
            "           AS pendientes, "
            "       COUNT(*) FILTER (WHERE d.approved = TRUE) "
            "           AS aprobados, "
            "       COUNT(*) FILTER (WHERE d.review_required = TRUE) "
            "           AS revision_requerida, "
            # (F-075 R22) El importe de la bandeja, sumado por documento.
            f"       COALESCE(SUM({sql_importe_mostrado('d')}), 0) AS importe, "
            "       MAX(d.fecha) AS ultima_fecha "
            "FROM albaran_documents_merge d "
            "WHERE d.is_active = TRUE "
        )
        params: dict[str, Any] = {}
        if search and search.strip():
            sql += (
                "AND (d.proveedor_cif ILIKE :term "
                "     OR d.proveedor_nombre ILIKE :term) "
            )
            params["term"] = f"%{search.strip()}%"
        sql += (
            "GROUP BY COALESCE("
            "    NULLIF(UPPER(REPLACE("
            "        TRIM(COALESCE(d.proveedor_cif, '')), ' ', '')), ''), "
            "    'sin-cif::' || LOWER(COALESCE(d.proveedor_nombre, ''))"
            ") "
            "ORDER BY pendientes DESC, total_albaranes DESC, "
            "         proveedor_nombre ASC"
        )
        try:
            with self._session_factory.create_session() as session:
                rows = session.execute(text(sql), params).mappings().all()
        except Exception:
            logger.exception(
                "[proveedores-resumen] consulta fallo; se devuelve []."
            )
            return []
        return [
            ProveedorResumenItem(
                proveedor_cif=r["proveedor_cif"],
                proveedor_nombre=r["proveedor_nombre"],
                total_albaranes=int(r["total_albaranes"] or 0),
                pendientes=int(r["pendientes"] or 0),
                aprobados=int(r["aprobados"] or 0),
                revision_requerida=int(r["revision_requerida"] or 0),
                importe=float(r["importe"] or 0.0),
                ultima_fecha=(
                    str(r["ultima_fecha"]) if r["ultima_fecha"] else None
                ),
            )
            for r in rows
        ]

    def _compute_and_persist_confianza(
        self,
        *,
        session,
        merge_doc,
        valuation=None,
        conc_map=None,
    ):
        """Confianza de valoracion (determinista) de un documento.

        Reemplaza la confianza de extraccion (IA). Considera TODAS las
        lineas valoradas (base + complementarias + sinteticas) y la
        resolucion de cabecera (obra/proveedor + su origen). Persiste en
        ``confidence_pct_calc`` (lo que lee la lista). Si el documento aun
        no tiene valoracion devuelve None y NO toca el valor existente.
        Carga valoracion/mapa si no se le pasan (para reusar desde el
        detalle, que ya los tiene). Devuelve el porcentaje (o None).
        """
        if valuation is None:
            valuation = self._load_valuation_in_session(
                session=session, document_id=merge_doc.id
            )
        if valuation is None:
            return None
        if conc_map is None:
            conc_map = self._load_conciliation_map_in_session(
                session=session, valuation=valuation
            )

        conciliaciones = []
        for _vline in valuation.lines_by_merge_line_id.values():
            _vid = _vline.valuation_line_id
            conciliaciones.append(
                conc_map.get(_vid) if _vid is not None else None
            )
        for _syn in valuation.synthetic_lines:
            _vid = _syn.valuation_line_id
            conciliaciones.append(
                conc_map.get(_vid) if _vid is not None else None
            )

        confianza = compute_confianza_pct(
            selected_contrato_origen=getattr(
                merge_doc, "selected_contrato_origen", None
            ),
            obra_codigo=merge_doc.obra_codigo,
            obra_codigo_origen=getattr(merge_doc, "obra_codigo_origen", None),
            proveedor_cif=merge_doc.proveedor_cif,
            proveedor_cif_origen=getattr(
                merge_doc, "proveedor_cif_origen", None
            ),
            conciliaciones=conciliaciones,
        )
        if merge_doc.confidence_pct_calc != confianza:
            merge_doc.confidence_pct_calc = confianza
            session.commit()
        return confianza

    def get_document_detail(
        self,
        document_id: str,
        *,
        view_mode: str = VIEW_MODE_MERGE,
    ) -> DocumentDetailPayload | None:
        self.initialize()
        if not self._tables_ready():
            return None

        normalized_view = normalize_view_mode(view_mode)

        with self._session_factory.create_session() as session:
            merge_doc = session.get(AlbaranDocumentMergeOrm, document_id)
            if merge_doc is None:
                return None
            _ = merge_doc.lines  # eager-load

            contratos_orm = session.scalars(
                select(AlbaranContratoMergeOrm)
                .where(AlbaranContratoMergeOrm.document_id == merge_doc.id)
                .order_by(AlbaranContratoMergeOrm.codigo_contrato.asc())
            ).all()

            selected_contrato_codigo = getattr(
                merge_doc, "selected_contrato_codigo", None
            )

            # Fix (jun 2026): la cabecera de contrato es ÚNICA por
            # ``sigrid_ide`` en ``albaran_contratos_merge`` y su
            # ``document_id`` se sobrescribe con el del ÚLTIMO albarán
            # enriquecido (UPSERT por sigrid_ide en sv3). Cuando varios
            # albaranes comparten el mismo contrato, el panel de los que
            # NO son "dueños" de la fila veía 0 cabeceras (su document_id
            # ya no figura en la fila compartida) y mostraba el falso aviso
            # "no se encontró contrato" — aunque la valoración SÍ lo usó.
            #
            # Recuperamos la cabecera por ``codigo_contrato`` a partir del
            # contrato seleccionado del documento, que es la fuente de
            # verdad de "qué contrato usa este albarán". Solo entramos aquí
            # si no hay ninguna cabecera por document_id (no alteramos el
            # caso normal ni el de varios contratos).
            if not contratos_orm and selected_contrato_codigo:
                contratos_orm = session.scalars(
                    select(AlbaranContratoMergeOrm)
                    .where(
                        AlbaranContratoMergeOrm.codigo_contrato
                        == selected_contrato_codigo
                    )
                    .order_by(AlbaranContratoMergeOrm.codigo_contrato.asc())
                ).all()

            # Dedup por codigo_contrato (#1): Sigrid puede tener el mismo
            # contrato con varios ``sigrid_ide`` (se recrea al modificarlo),
            # lo que deja filas duplicadas en ``albaran_contratos_merge``
            # para el mismo documento. El panel y el desplegable deben
            # mostrar UNO por codigo. Conservamos la primera aparicion.
            _contratos_all = [
                self._contrato_orm_to_payload(item) for item in contratos_orm
            ]
            # Dedup por codigo PREFIRIENDO la fila que tenga el PDF.
            _by_cod: dict[str, ContratoPayload] = {}
            for _cp in _contratos_all:
                _prev = _by_cod.get(_cp.codigo_contrato)
                if _prev is None:
                    _by_cod[_cp.codigo_contrato] = _cp
                elif (not _prev.pdf_sharepoint_web_url) and _cp.pdf_sharepoint_web_url:
                    _by_cod[_cp.codigo_contrato] = _cp
            contratos_payload = list(_by_cod.values())

            # Lineas del contrato seleccionado, para el desplegable de
            # conciliacion editable del front (elegir otra linea o nueva).
            _lines_raw = [
                ContratoLinePayload(
                    id=int(r["id"]),
                    codigo_contrato=r.get("codigo_contrato") or "",
                    codigo_partida=r.get("codigo_partida"),
                    descripcion=r.get("descripcion_linea"),
                    precio_unitario=r.get("precio_unitario"),
                    unidad_medida=r.get("unidad_medida"),
                    codigo_producto=r.get("codigo_producto"),
                )
                for r in self._fetch_contrato_lines_for_codigo_in_session(
                    session, selected_contrato_codigo
                )
            ]
            # Dedup de opciones identicas (misma partida+descripcion+precio+
            # unidad): si habia contratos duplicados con sus lineas repetidas,
            # el desplegable no debe mostrar la misma opcion dos veces.
            _seen_ln: set[tuple] = set()
            contrato_lines_payload = []
            for _ln in _lines_raw:
                _key = (
                    _ln.codigo_partida,
                    _ln.descripcion,
                    _ln.precio_unitario,
                    _ln.unidad_medida,
                )
                if _key in _seen_ln:
                    continue
                _seen_ln.add(_key)
                contrato_lines_payload.append(_ln)

            provider_docs = session.scalars(
                select(AlbaranDocumentBaseOrm)
                .where(AlbaranDocumentBaseOrm.source_sha256 == merge_doc.source_sha256)
                .order_by(AlbaranDocumentBaseOrm.created_at_utc.asc())
            ).all()

            seen_providers = {doc.provider_origin for doc in provider_docs}
            available_views: list[str] = [VIEW_MODE_MERGE]
            for provider in KNOWN_PROVIDER_VIEWS:
                if provider in seen_providers:
                    available_views.append(provider)
            for provider in sorted(seen_providers):
                if provider not in available_views:
                    available_views.append(provider)

            if (
                normalized_view != VIEW_MODE_MERGE
                and normalized_view not in seen_providers
            ):
                normalized_view = VIEW_MODE_MERGE

            provider_snapshots_payload = [
                ProviderSnapshot(
                    id=item.id,
                    provider_origin=item.provider_origin,
                    model_name=item.model_name,
                    proveedor_nombre=item.proveedor_nombre,
                    fecha=item.fecha,
                    numero_albaran=item.numero_albaran,
                    obra_codigo=item.obra_codigo,
                    raw_extraction_json=item.raw_extraction_json,
                    ia_output_json=item.ia_output_json,
                )
                for item in provider_docs
            ]

            # Los desplegables de cabecera (proveedor / obra) ya NO se
            # rellenan desde la BBDD local (solo tenia los contratos ya
            # ingeridos). Ahora el front los pide BAJO DEMANDA a Sigrid via
            # los endpoints /api/sigrid/* (ver app.py). Dejamos las listas
            # vacias aqui.
            proveedores_opts, obras_opts = [], []

            # NUEVO: leer valoración (si existe) en la misma sesión.
            valuation_payload = self._load_valuation_in_session(
                session=session,
                document_id=merge_doc.id,
            )

            # NUEVO: cargar el mapa de conciliación (qué línea de
            # contrato — sigrid o derivada — casó con cada línea del
            # albarán) para mostrar inline en sv4. None si no hay
            # valoración o ninguna línea tiene matched/derived.
            conciliation_by_valuation_line_id = (
                self._load_conciliation_map_in_session(
                    session=session,
                    valuation=valuation_payload,
                )
                if valuation_payload is not None
                else {}
            )

            # CONFIANZA de valoracion (determinista; reemplaza la de IA).
            # Se recalcula sobre el estado actual y se persiste en
            # confidence_pct_calc (lo que lee el badge y la lista). Reusa la
            # valoracion y el mapa ya cargados arriba.
            self._compute_and_persist_confianza(
                session=session,
                merge_doc=merge_doc,
                valuation=valuation_payload,
                conc_map=conciliation_by_valuation_line_id,
            )

            if normalized_view == VIEW_MODE_MERGE:
                return self._build_merge_detail(
                    merge_doc=merge_doc,
                    available_views=available_views,
                    provider_snapshots=provider_snapshots_payload,
                    contratos=contratos_payload,
                    contrato_lines=contrato_lines_payload,
                    proveedores=proveedores_opts,
                    obras=obras_opts,
                    selected_contrato_codigo=selected_contrato_codigo,
                    valuation=valuation_payload,
                    conciliation_by_valuation_line_id=conciliation_by_valuation_line_id,
                )

            provider_doc = next(
                (doc for doc in provider_docs if doc.provider_origin == normalized_view),
                None,
            )
            if provider_doc is None:
                return self._build_merge_detail(
                    merge_doc=merge_doc,
                    available_views=available_views,
                    provider_snapshots=provider_snapshots_payload,
                    contratos=contratos_payload,
                    contrato_lines=contrato_lines_payload,
                    proveedores=proveedores_opts,
                    obras=obras_opts,
                    selected_contrato_codigo=selected_contrato_codigo,
                    valuation=valuation_payload,
                    conciliation_by_valuation_line_id=conciliation_by_valuation_line_id,
                )

            provider_lines = session.scalars(
                select(AlbaranLineBaseOrm)
                .where(AlbaranLineBaseOrm.document_id == provider_doc.id)
                .order_by(AlbaranLineBaseOrm.line_index.asc())
            ).all()

            return self._build_provider_detail(
                merge_doc=merge_doc,
                provider_doc=provider_doc,
                provider_lines=provider_lines,
                available_views=available_views,
                provider_snapshots=provider_snapshots_payload,
                view_mode=normalized_view,
                contratos=contratos_payload,
                selected_contrato_codigo=selected_contrato_codigo,
                valuation=valuation_payload,
            )

    # ------------------------------------------------------------------ #
    # NUEVO: opciones de cabecera (proveedores / obras del proyecto) para
    # los desplegables. DISTINCT sobre TODA la tabla de contratos, dedup
    # por cif (proveedor) y por codigo (obra). Tolerante a tabla ausente.
    # ------------------------------------------------------------------ #
    @staticmethod
    def _load_header_options_in_session(
        session: Any,
    ) -> tuple[list[ProveedorOption], list[ObraOption]]:
        proveedores: list[ProveedorOption] = []
        obras: list[ObraOption] = []
        try:
            prov_rows = session.execute(
                text(
                    "SELECT DISTINCT cif_proveedor, nombre_proveedor "
                    "FROM albaran_contratos_merge "
                    "WHERE cif_proveedor IS NOT NULL AND cif_proveedor <> '' "
                    "ORDER BY nombre_proveedor"
                )
            ).mappings().all()
            obra_rows = session.execute(
                text(
                    "SELECT DISTINCT codigo_obra, nombre_obra "
                    "FROM albaran_contratos_merge "
                    "WHERE codigo_obra IS NOT NULL AND codigo_obra <> '' "
                    "ORDER BY codigo_obra"
                )
            ).mappings().all()
        except Exception:
            session.rollback()
            return [], []

        _seen_cif: set[str] = set()
        for r in prov_rows:
            cif = (r["cif_proveedor"] or "").strip()
            if not cif or cif in _seen_cif:
                continue
            _seen_cif.add(cif)
            nombre = (r["nombre_proveedor"] or "").strip() or None
            proveedores.append(ProveedorOption(cif=cif, nombre=nombre))

        _seen_cod: set[str] = set()
        for r in obra_rows:
            cod = (r["codigo_obra"] or "").strip()
            if not cod or cod in _seen_cod:
                continue
            _seen_cod.add(cod)
            nombre = (r["nombre_obra"] or "").strip() or None
            obras.append(ObraOption(codigo=cod, nombre=nombre))

        return proveedores, obras

    # ------------------------------------------------------------------ #
    # NUEVO: lectura de valoración desde las tablas del servicio 6.
    # SQL crudo para no acoplarnos al ORM del 6 dentro del servicio 4.
    # Si las tablas no existen (p.e. BBDD vieja) devuelve None sin
    # romper la carga del detalle.
    # ------------------------------------------------------------------ #
    def _load_valuation_in_session(
        self,
        *,
        session: Any,
        document_id: str,
    ) -> ValuationPayload | None:
        try:
            header_row = session.execute(
                text(
                    "SELECT id, contrato_codigo, status, provider_ia, "
                    "       model_name, total_valorado, total_lines, "
                    "       lines_matched_exact, lines_matched_semantic, "
                    "       lines_matched_price_only, lines_unmatched, "
                    "       review_required, created_at_utc, updated_at_utc "
                    "FROM albaran_valuations "
                    "WHERE document_id = :doc_id "
                    "LIMIT 1"
                ),
                {"doc_id": document_id},
            ).mappings().first()
        except Exception:
            # Tabla puede no existir (BBDD antigua).
            session.rollback()
            return None

        if header_row is None:
            return None

        valuation_id = str(header_row["id"])

        try:
            line_rows = session.execute(
                text(
                    "SELECT id, "
                    "       merge_line_id, matched_contrato_line_id, "
                    "       derived_contrato_line_id, "
                    "       precio_unitario_contrato_db, "
                    "       precio_unitario_pdf_inferido, "
                    "       precio_unitario_final, precio_unitario_source, "
                    "       precio_unitario_agreement, "
                    "       unidad_albaran, unidad_contrato, "
                    "       unidad_categoria, unidad_category_match, "
                    "       cantidad_albaran, cantidad_convertida, "
                    "       factor_conversion, "
                    "       importe_calculado, importe_albaran_declarado, "
                    "       importe_source, "
                    "       codigo_partida_albaran, codigo_partida_final, "
                    "       partida_action, "
                    "       match_confidence_pct, match_method, "
                    # F-036 R23: por qué la línea salió así. La columna
                    # existe desde sv6; sv4 no la leía y el revisor no
                    # veía nunca los motivos.
                    "       review_required, review_reasons_json, "
                    # ----- sub-tanda 2D: campos de líneas sintéticas -----
                    "       line_kind, parent_merge_line_id, "
                    "       modifier_source, modifier_reason, "
                    "       descripcion_linea, "
                    # ----- edición salmon (jun 2026) -----
                    "       descuento_albaran_aplicado, codigo_externo, "
                    # ----- F-065 R17: fila guardada (bloqueada) -----
                    "       bloqueada "
                    "FROM albaran_line_valuations "
                    "WHERE valuation_id = :vid "
                    # from_albaran primero (para poder iterar base, luego
                    # sintéticas agrupadas por parent en la UI futura).
                    "ORDER BY "
                    "  CASE WHEN line_kind = 'synthetic_modifier' "
                    "       THEN 1 ELSE 0 END, "
                    "  merge_line_id NULLS LAST, "
                    "  id"
                ),
                {"vid": valuation_id},
            ).mappings().all()
        except Exception:
            session.rollback()
            line_rows = []

        # Sub-tanda 2D: las líneas pueden ser 'from_albaran' (con
        # merge_line_id real, van al dict de siempre para que la UI
        # pinte cada línea del albarán con su valoración) o
        # 'synthetic_modifier' (merge_line_id NULL, se acumulan en una
        # lista aparte para que la UI las pinte como bloque adicional).
        #
        # Compatibilidad retroactiva: para valoraciones anteriores a
        # 2D (sin columna line_kind), tratamos NULL/'' como
        # 'from_albaran'. Así los albaranes valorados con la versión
        # anterior siguen funcionando.
        lines_by_id: dict[int, LineValuationPayload] = {}
        synthetic_lines: list[LineValuationPayload] = []
        for row in line_rows:
            raw_merge_line_id = row.get("merge_line_id") if hasattr(
                row, "get"
            ) else row["merge_line_id"]

            raw_line_kind = None
            try:
                raw_line_kind = row["line_kind"]
            except KeyError:
                # Columna no existe (BBDD anterior a 2D) — default.
                raw_line_kind = None
            line_kind = (raw_line_kind or "from_albaran").strip() or "from_albaran"

            # Columnas nuevas de 2D — opcionales, toleramos ausencia.
            try:
                parent_merge_line_id = row["parent_merge_line_id"]
            except KeyError:
                parent_merge_line_id = None
            try:
                modifier_source = row["modifier_source"]
            except KeyError:
                modifier_source = None
            try:
                modifier_reason = row["modifier_reason"]
            except KeyError:
                modifier_reason = None
            try:
                descripcion_linea = row["descripcion_linea"]
            except KeyError:
                descripcion_linea = None
            # F-036 R23 — opcional por el mismo motivo: una BBDD sin la
            # columna abre la ficha igual, sin razones.
            try:
                review_reasons = motivos_de_json(row["review_reasons_json"])
            except KeyError:
                review_reasons = []

            merge_line_id_typed: int | None
            if raw_merge_line_id is None:
                merge_line_id_typed = None
            else:
                try:
                    merge_line_id_typed = int(raw_merge_line_id)
                except (TypeError, ValueError):
                    merge_line_id_typed = None

            try:
                valuation_line_id = int(row["id"])
            except (TypeError, ValueError, KeyError):
                valuation_line_id = None

            payload = LineValuationPayload(
                valuation_line_id=valuation_line_id,
                merge_line_id=merge_line_id_typed,
                matched_contrato_line_id=row["matched_contrato_line_id"],
                derived_contrato_line_id=row["derived_contrato_line_id"],
                precio_unitario_contrato_db=row["precio_unitario_contrato_db"],
                precio_unitario_pdf_inferido=row["precio_unitario_pdf_inferido"],
                precio_unitario_final=row["precio_unitario_final"],
                precio_unitario_source=row["precio_unitario_source"],
                precio_unitario_agreement=row["precio_unitario_agreement"],
                unidad_albaran=row["unidad_albaran"],
                unidad_contrato=row["unidad_contrato"],
                unidad_categoria=row["unidad_categoria"],
                unidad_category_match=row["unidad_category_match"],
                cantidad_albaran=row["cantidad_albaran"],
                cantidad_convertida=row["cantidad_convertida"],
                factor_conversion=row["factor_conversion"],
                importe_calculado=row["importe_calculado"],
                importe_albaran_declarado=row["importe_albaran_declarado"],
                importe_source=row["importe_source"],
                codigo_partida_albaran=row["codigo_partida_albaran"],
                codigo_partida_final=row["codigo_partida_final"],
                partida_action=row["partida_action"],
                match_confidence_pct=row["match_confidence_pct"],
                match_method=row["match_method"],
                review_required=row["review_required"],
                review_reasons=review_reasons,
                # --- sub-tanda 2D ---
                line_kind=line_kind,
                parent_merge_line_id=parent_merge_line_id,
                modifier_source=modifier_source,
                modifier_reason=modifier_reason,
                descripcion_linea=descripcion_linea,
                # --- edición salmon (jun 2026) ---
                descuento_albaran_aplicado=row.get(
                    "descuento_albaran_aplicado"
                ) if hasattr(row, "get") else row["descuento_albaran_aplicado"],
                codigo_externo=row.get("codigo_externo")
                if hasattr(row, "get") else row["codigo_externo"],
                bloqueada=bool(row["bloqueada"]),
            )

            if line_kind == "synthetic_modifier":
                synthetic_lines.append(payload)
            else:
                # from_albaran. Si por la razón que sea merge_line_id es
                # None (BBDD corrupta, dato antiguo raro), no lo metemos
                # en el dict — se añade también a synthetic_lines para
                # que al menos no desaparezca.
                if merge_line_id_typed is None:
                    synthetic_lines.append(payload)
                else:
                    lines_by_id[merge_line_id_typed] = payload

        return ValuationPayload(
            valuation_id=valuation_id,
            contrato_codigo=header_row["contrato_codigo"],
            status=str(header_row["status"]),
            provider_ia=header_row["provider_ia"],
            model_name=header_row["model_name"],
            total_valorado=float(header_row["total_valorado"] or 0.0),
            total_lines=int(header_row["total_lines"] or 0),
            lines_matched_exact=int(header_row["lines_matched_exact"] or 0),
            lines_matched_semantic=int(header_row["lines_matched_semantic"] or 0),
            lines_matched_price_only=int(
                header_row["lines_matched_price_only"] or 0
            ),
            lines_unmatched=int(header_row["lines_unmatched"] or 0),
            review_required=bool(header_row["review_required"]),
            created_at_utc=header_row["created_at_utc"],
            updated_at_utc=header_row["updated_at_utc"],
            lines_by_merge_line_id=lines_by_id,
            synthetic_lines=synthetic_lines,
        )

    # ----------------------------------------------------------------- #
    # Carga de los datos de conciliación que se muestran inline en sv4
    # bajo cada línea del albarán.
    #
    # Para cada línea valorada (LineValuationPayload from_albaran), se
    # busca el bloque de detalle a mostrar:
    #
    #   - Si tiene matched_contrato_line_id (línea cacheada de Sigrid),
    #     leemos albaran_contrato_lines_merge.
    #   - Si tiene derived_contrato_line_id (línea creada por el
    #     valorador), leemos contrato_lines_derived.
    #
    # Las dos consultas son batch (un solo SELECT con IN) para no
    # disparar N+1.
    #
    # Devuelve un dict {merge_line_id -> ConciliacionDisplay}. Líneas
    # del albarán sin valoración (o cuya valoración no tiene match ni
    # derived) no aparecen en el dict; el front no muestra el bloque.
    # ----------------------------------------------------------------- #
    def _load_conciliation_map_in_session(
        self,
        *,
        session: Any,
        valuation: ValuationPayload | None,
    ) -> dict[int, ConciliacionDisplay]:
        """Devuelve ``{valuation_line_id -> ConciliacionDisplay}``.

        Bloque 2 (may 2026): antes se indexaba por ``merge_line_id``, lo
        que DEJABA FUERA a las líneas sintéticas (``merge_line_id`` NULL)
        y por eso solo conciliaba la línea base en el front. Ahora se
        indexa por ``valuation_line_id``, que existe para TODAS las
        líneas valoradas (``from_albaran`` y ``synthetic_modifier``), de
        modo que las sintéticas también muestran su conciliación contra
        Sigrid.

        El indicador verde/rojo (``price_agreement``) se calcula aquí
        comparando el precio de la línea de Sigrid con el precio
        valorado de la línea, para que el revisor vea de un vistazo si
        cuadran.
        """
        if valuation is None:
            return {}

        # Todas las líneas valoradas: base/complementarias + sintéticas.
        all_lines: list[LineValuationPayload] = list(
            valuation.lines_by_merge_line_id.values()
        ) + list(valuation.synthetic_lines)

        # Paso 1: agrupar por tipo (matched / derived) con la salida
        # indexada por valuation_line_id.
        #
        # IMPORTANTE (fix jun 2026 — líneas que se quedaban sin conciliar):
        # la relación línea_de_contrato → líneas_de_valoración es UNO-A-VARIOS,
        # no uno-a-uno. Varias líneas del albarán pueden casar con la MISMA
        # línea de contrato (p.ej. dos rejillas del mismo modelo en líneas
        # distintas del albarán casan ambas contra la misma línea de Sigrid).
        # Antes indexábamos ``matched_to_vline[contrato_line_id] = vid`` y la
        # segunda línea SOBREESCRIBÍA a la primera: solo la última conservaba
        # su bloque de conciliación y las demás aparecían vacías con el botón
        # "+". Ahora acumulamos TODOS los valuation_line_id que casan con cada
        # línea de contrato para pintarles el bloque a todos.
        matched_to_vlines: dict[int, list[int]] = {}
        derived_to_vlines: dict[int, list[int]] = {}
        precio_final_by_vline: dict[int, float | None] = {}
        vline_by_vid: dict[int, LineValuationPayload] = {}
        for vline in all_lines:
            vid = vline.valuation_line_id
            if vid is None:
                continue
            precio_final_by_vline[vid] = vline.precio_unitario_final
            vline_by_vid[vid] = vline
            if vline.matched_contrato_line_id is not None:
                matched_to_vlines.setdefault(
                    vline.matched_contrato_line_id, []
                ).append(vid)
            elif vline.derived_contrato_line_id is not None:
                derived_to_vlines.setdefault(
                    vline.derived_contrato_line_id, []
                ).append(vid)

        out: dict[int, ConciliacionDisplay] = {}

        # Paso 2: líneas matched (de Sigrid cacheadas) en bloque.
        for row in self._fetch_contrato_lines_in_session(
            session, list(matched_to_vlines.keys())
        ):
            # Todas las líneas de valoración que casaron con ESTA línea de
            # contrato reciben su propio bloque de conciliación (uno-a-varios).
            for vid in matched_to_vlines.get(row["id"], []):
                # (F-065 R9) La ficha pinta y edita el precio APLICADO (el de
                # la valoración); el de la línea de contrato va aparte, para el
                # title y los avisos.
                # (F-078 R6–R8) Concepto, unidad y precio salen SOLO de la
                # fila (vacío = vacío); su línea, para lo que no es de la fila.
                unitario_contrato = row.get("precio_unitario")
                precio_final = precio_final_by_vline.get(vid)
                _vl = vline_by_vid.get(vid)
                out[vid] = ConciliacionDisplay(
                    kind="assigned",
                    descripcion=getattr(_vl, "descripcion_linea", None),
                    unitario=precio_final,
                    unitario_contrato=unitario_contrato,
                    medicion_total=row.get("uds"),
                    medicion_pendiente=row.get("pendiente_servir"),
                    unidad=getattr(_vl, "unidad_contrato", None),
                    codigo_partida=row.get("codigo_partida"),
                    descripcion_partida=row.get("descripcion_partida"),
                    price_agreement=self._price_agreement(
                        unitario_contrato, precio_final,
                    ),
                    precio_unitario_final=precio_final,
                    sibling=None,
                    match_method=getattr(vline_by_vid.get(vid), "match_method", None),
                    match_confidence_pct=getattr(
                        vline_by_vid.get(vid), "match_confidence_pct", None
                    ),
                    precio_unitario_source=getattr(
                        vline_by_vid.get(vid), "precio_unitario_source", None
                    ),
                    descuento=getattr(
                        _vl, "descuento_albaran_aplicado", None
                    ),
                    codigo_externo=getattr(_vl, "codigo_externo", None),
                )

        # Paso 3: líneas derived (creadas por el valorador) en bloque.
        for row in self._fetch_derived_lines_in_session(
            session, list(derived_to_vlines.keys())
        ):
            for vid in derived_to_vlines.get(row["id"], []):
                # (F-078 R6–R8) Lo de la fila; la derivada, solo referencia.
                unitario = row.get("precio_unitario")
                precio_final = precio_final_by_vline.get(vid)
                _vl = vline_by_vid.get(vid)
                out[vid] = ConciliacionDisplay(
                    kind="derived",
                    descripcion=getattr(_vl, "descripcion_linea", None),
                    unitario=precio_final,
                    unitario_contrato=unitario,
                    medicion_total=row.get("uds"),
                    medicion_pendiente=None,  # derived: no hay pendiente
                    unidad=getattr(_vl, "unidad_contrato", None),
                    codigo_partida=row.get("codigo_partida"),
                    descripcion_partida=row.get("descripcion_partida"),
                    price_agreement=self._price_agreement(unitario, precio_final),
                    precio_unitario_final=precio_final,
                    sibling=None,
                    match_method=getattr(vline_by_vid.get(vid), "match_method", None),
                    match_confidence_pct=getattr(
                        vline_by_vid.get(vid), "match_confidence_pct", None
                    ),
                    precio_unitario_source=getattr(
                        vline_by_vid.get(vid), "precio_unitario_source", None
                    ),
                    derived_origen=row.get("origen"),
                    descuento=getattr(
                        vline_by_vid.get(vid),
                        "descuento_albaran_aplicado",
                        None,
                    ),
                    codigo_externo=getattr(
                        vline_by_vid.get(vid), "codigo_externo", None
                    ),
                )

        # (F-051 R10, R11) Estado de partida de cada fila según la partida
        # FINAL de su valoración. En almacén (vacía, tenga o no marca) no
        # se pinta la partida de la línea de contrato casada ni la de la
        # derivada: la ficha dice «Almacén». El resto del bloque (precio,
        # descripción, kind Sigrid/Nueva) no cambia.
        #
        # (Review pasada 2, decisión del humano) Fuera de almacén se pinta
        # la partida FINAL, no la de la casada: una complementaria que
        # hereda la partida de su base (R7) puede casar con una línea de
        # contrato de otra partida o sin partida. La descripción de la
        # casada solo se pinta si es de esa misma partida. La de la casada
        # queda en ``codigo_partida_casada``.
        for vid, conc in out.items():
            _vl = vline_by_vid.get(vid)
            final = getattr(_vl, "codigo_partida_final", None)
            conc.estado_partida = estado_partida(final)
            conc.codigo_partida_casada = conc.codigo_partida
            if conc.estado_partida == "almacen":
                conc.codigo_partida = None
                conc.descripcion_partida = None
            elif str(final).strip() != (conc.codigo_partida or "").strip():
                conc.codigo_partida = str(final).strip()
                conc.descripcion_partida = None

        return out

    @staticmethod
    def _fetch_contrato_lines_in_session(session: Any, ids: list[int]):
        """Carga en bloque líneas de ``albaran_contrato_lines_merge`` por
        id, con fallback a ``IN (...)`` si la BBDD no soporta ``ANY``.
        """
        if not ids:
            return []
        base_sql = (
            "SELECT id, descripcion_linea, unidad_medida, precio_unitario, "
            "       uds, pendiente_servir, codigo_partida, descripcion_partida "
            "FROM albaran_contrato_lines_merge "
        )
        try:
            return session.execute(
                text(base_sql + "WHERE id = ANY(:ids)"), {"ids": ids}
            ).mappings().all()
        except Exception:
            session.rollback()
            placeholders = ", ".join(f":id_{i}" for i in range(len(ids)))
            params = {f"id_{i}": v for i, v in enumerate(ids)}
            return session.execute(
                text(base_sql + f"WHERE id IN ({placeholders})"), params
            ).mappings().all()

    @staticmethod
    def _fetch_derived_lines_in_session(session: Any, ids: list[int]):
        """Carga en bloque líneas de ``contrato_lines_derived`` por id.
        Tolera que la tabla no exista (BBDD anterior a sv6 con derived).

        OJO: el esquema real de ``contrato_lines_derived`` (ver sv6
        ``schema_contribution``) NO tiene ``uds`` ni ``descripcion_partida``;
        solo ``codigo_partida`` y ``unidad_medida``. Seleccionar columnas
        inexistentes hacía petar la query en silencio y la conciliación de
        las líneas derivadas no aparecía.
        """
        if not ids:
            return []
        base_sql = (
            "SELECT id, descripcion_linea, unidad_medida, precio_unitario, "
            "       codigo_partida, origen "
            "FROM contrato_lines_derived "
        )
        try:
            return session.execute(
                text(base_sql + "WHERE id = ANY(:ids)"), {"ids": ids}
            ).mappings().all()
        except Exception:
            session.rollback()
            placeholders = ", ".join(f":id_{i}" for i in range(len(ids)))
            params = {f"id_{i}": v for i, v in enumerate(ids)}
            try:
                return session.execute(
                    text(base_sql + f"WHERE id IN ({placeholders})"), params
                ).mappings().all()
            except Exception:
                session.rollback()
                return []

    @staticmethod
    def _price_agreement(
        unitario: float | None,
        precio_final: float | None,
    ) -> str | None:
        """'agree' si el precio de Sigrid y el valorado cuadran (±1%),
        'disagree' si difieren, None si falta alguno.
        """
        if unitario is None or precio_final is None:
            return None
        try:
            a = float(unitario)
            b = float(precio_final)
        except (TypeError, ValueError):
            return None
        tol = max(0.01, 0.01 * max(abs(a), abs(b)))
        return "agree" if abs(a - b) <= tol else "disagree"

    @staticmethod
    def _fetch_contrato_lines_for_codigo_in_session(
        session: Any, codigo_contrato: str | None
    ):
        """Todas las lineas de albaran_contrato_lines_merge de un contrato,
        para poblar el desplegable de conciliacion editable. Tolerante a
        que la tabla no exista (BBDD antigua)."""
        if not codigo_contrato:
            return []
        sql = (
            "SELECT id, codigo_contrato, codigo_partida, descripcion_linea, "
            "       precio_unitario, unidad_medida, codigo_producto "
            "FROM albaran_contrato_lines_merge "
            "WHERE codigo_contrato = :cod "
            "ORDER BY codigo_partida NULLS LAST, descripcion_linea"
        )
        try:
            return session.execute(
                text(sql), {"cod": codigo_contrato}
            ).mappings().all()
        except Exception:
            session.rollback()
            return []

    def set_line_conciliacion(
        self,
        *,
        document_id: str,
        valuation_line_id: int,
        mode: str,
        matched_contrato_line_id: int | None = None,
        descripcion: str | None = None,
        precio_unitario: float | None = None,
    ) -> bool:
        """«Origen ✎» (F-065 R28): la ÚNICA vía de reapuntar una fila.

        mode='contract_line': la fila pasa a ser Contrato de
          ``matched_contrato_line_id`` y «cuadra» con ella: se trae su partida,
          su unidad y su precio (o ``precio_unitario`` si viene), la
          descripción pasa a ser la de la línea (si está vacía, la que tenía;
          F-078 R12) y el importe se recalcula con la cantidad de la fila. Se
          limpia la derivada.
        mode='nueva': la fila pasa a Nueva con SUS valores actuales (partida
          final, descripción, unidad y precio que pinta la ficha; ``descripcion``
          y ``precio_unitario`` los sustituyen si vienen). Si el precio no
          cambia, el importe tampoco.
        En los dos modos la fila acaba con ``fila_a_guardar`` aplicada
        (F-078 R16), en la misma transacción.

        NO revalora ni llama a la IA. Se pierde con «Valorar ahora» (F-058).
        Devuelve True si actualizó algo.
        """
        self.initialize()
        with self._session_factory.create_session() as session:
            # F-053 R26 (alta, con el merge bloqueado), F-065 R4 (aprobado) y
            # R14 (fila guardada).
            self._exigir_editable(session, document_id, valuation_line_id)
            row = session.execute(
                text(
                    "SELECT lv.id, lv.valuation_id, lv.merge_line_id, "
                    "       lv.matched_contrato_line_id, "
                    "       lv.derived_contrato_line_id, "
                    "       lv.cantidad_albaran, lv.cantidad_convertida, "
                    "       lv.codigo_partida_final, lv.descripcion_linea, "
                    "       lv.precio_unitario_final, lv.unidad_contrato, "
                    "       lv.unidad_albaran, lv.factor_conversion, "
                    "       lv.review_reasons_json, "
                    "       lv.descuento_albaran_aplicado, v.document_id, "
                    "       v.contrato_codigo "
                    "FROM albaran_line_valuations lv "
                    "JOIN albaran_valuations v ON v.id = lv.valuation_id "
                    "WHERE lv.id = :vid"
                ),
                {"vid": valuation_line_id},
            ).mappings().first()
            if row is None or row["document_id"] != document_id:
                return False

            valuation_id = row["valuation_id"]
            cantidad = (
                row["cantidad_convertida"]
                if row["cantidad_convertida"] is not None
                else row["cantidad_albaran"]
            )

            # Su línea actual (de contrato o derivada): lo que pinta la ficha
            # donde la valoración no tiene lo suyo.
            tabla = (
                "albaran_contrato_lines_merge"
                if row["matched_contrato_line_id"] is not None
                else "contrato_lines_derived"
            )
            casada = session.execute(
                text(
                    "SELECT descripcion_linea, unidad_medida, precio_unitario "
                    f"FROM {tabla} WHERE id = :id"  # noqa: S608
                ),
                {"id": row["matched_contrato_line_id"]
                 if row["matched_contrato_line_id"] is not None
                 else row["derived_contrato_line_id"]},
            ).mappings().first() or {}

            if mode == "contract_line":
                if matched_contrato_line_id is None:
                    return False
                cl = session.execute(
                    text(
                        "SELECT precio_unitario, codigo_partida, unidad_medida, "
                        "       descripcion_linea "
                        "FROM albaran_contrato_lines_merge WHERE id = :id"
                    ),
                    {"id": matched_contrato_line_id},
                ).mappings().first()
                if cl is None:
                    return False
                precio = (
                    precio_unitario
                    if precio_unitario is not None
                    else cl["precio_unitario"]
                )
                # (F-065 H2) Otra unidad: la cantidad solo se rehace hacia la
                # del albarán; si no se sabe, se deja y se avisa.
                unidad_actual = row["unidad_contrato"] or casada.get("unidad_medida")
                ca, cc, factor, aviso = cantidades_tras_reapuntar(
                    unidad_actual=unidad_actual,
                    unidad_nueva=cl["unidad_medida"],
                    unidad_albaran=row["unidad_albaran"],
                    cantidad_albaran=row["cantidad_albaran"],
                    cantidad_convertida=row["cantidad_convertida"],
                    factor=row["factor_conversion"],
                )
                # (F-078 R12) La fila queda con la descripción de esa línea (si
                # está vacía, la que tenía) y su unidad, también en
                # ``unidad_albaran`` sin conversión.
                session.execute(
                    text(
                        "UPDATE albaran_line_valuations SET "
                        "  matched_contrato_line_id = :mid, "
                        "  derived_contrato_line_id = NULL, "
                        "  precio_unitario_final = :pu, "
                        "  precio_unitario_source = 'manual_contract', "
                        "  precio_unitario_agreement = 'manual', "
                        "  codigo_partida_final = :part, "
                        "  unidad_contrato = :uni, "
                        + ("  unidad_albaran = :uni, " if sin_conversion(factor) else "")
                        + "  cantidad_albaran = :ca, "
                        "  cantidad_convertida = :cc, "
                        "  factor_conversion = :factor, "
                        "  descripcion_linea = :desc, "
                        "  importe_calculado = :imp, "
                        "  importe_source = 'calculated', "
                        "  review_required = :revisar, "
                        "  review_reasons_json = :razones "
                        "WHERE id = :vid"
                    ),
                    {
                        "mid": matched_contrato_line_id,
                        "pu": precio,
                        "part": cl["codigo_partida"],
                        "desc": (
                            (cl["descripcion_linea"] or "").strip()
                            or row["descripcion_linea"]
                        ),
                        "uni": cl["unidad_medida"] or unidad_actual,
                        "ca": ca,
                        "cc": cc,
                        "factor": factor,
                        "imp": _importe_de_linea(
                            precio_unitario=precio,
                            cantidad=cc if cc is not None else ca,
                            descuento_pct=row["descuento_albaran_aplicado"],
                        ),
                        "revisar": aviso,
                        "razones": motivos_con(
                            row["review_reasons_json"], MOTIVO_UNIDAD_CAMBIADA, aviso,
                        ),
                        "vid": valuation_line_id,
                    },
                )
            elif mode == "nueva":
                # Los valores ACTUALES de la fila (``casada`` donde la
                # valoración no tiene los suyos).
                actual = (
                    row["precio_unitario_final"]
                    if row["precio_unitario_final"] is not None
                    else casada.get("precio_unitario")
                )
                precio = precio_unitario if precio_unitario is not None else actual
                desc = (
                    descripcion or row["descripcion_linea"]
                    or casada.get("descripcion_linea")
                )
                new_id = session.execute(
                    text(
                        "INSERT INTO contrato_lines_derived ("
                        "  created_by_valuation_id, source_document_id, "
                        "  codigo_contrato, codigo_producto, descripcion_linea, "
                        "  unidad_medida, precio_unitario, codigo_partida, "
                        "  origen, created_at_utc) "
                        "VALUES (:vid, :doc, :cod, NULL, :desc, :uni, :pu, "
                        "  :part, 'manual_override', :now) "
                        "RETURNING id"
                    ),
                    {
                        "vid": valuation_id,
                        "doc": document_id,
                        "cod": row["contrato_codigo"] or "",
                        "desc": desc,
                        "uni": row["unidad_contrato"] or casada.get("unidad_medida"),
                        "pu": precio,
                        "part": row["codigo_partida_final"],
                        "now": self._utc_iso(),
                    },
                ).scalar_one()
                sets = (
                    "matched_contrato_line_id = NULL, "
                    "derived_contrato_line_id = :did, "
                    "precio_unitario_final = :pu, "
                    "precio_unitario_source = 'manual_derived', "
                    "precio_unitario_agreement = 'manual', "
                    "descripcion_linea = :desc, "
                    "review_required = FALSE"
                )
                # (F-078 R12) La descripción que tenía la fila (o la tecleada),
                # con o sin blanca: sustituye a F-065 CR1/H1.
                parametros: dict[str, Any] = {
                    "did": new_id, "pu": precio, "vid": valuation_line_id,
                    "desc": desc,
                }
                if not _mismo_numero(precio, actual):
                    sets += ", importe_calculado = :imp, importe_source = 'calculated'"
                    parametros["imp"] = _importe_de_linea(
                        precio_unitario=precio,
                        cantidad=cantidad,
                        descuento_pct=row["descuento_albaran_aplicado"],
                    )
                session.execute(
                    text(f"UPDATE albaran_line_valuations SET {sets} WHERE id = :vid"),
                    parametros,
                )
            else:
                return False

            self._materializar_fila_in_session(session, valuation_line_id)
            self._recalcular_total_in_session(session, valuation_id)
            session.commit()
            return True

    def update_line_conciliacion(
        self,
        *,
        document_id: str,
        valuation_line_id: int,
        campos: dict[str, Any] | None = None,
        bloquear: bool = False,
        cuadrar: str | None = None,
    ) -> bool:
        """Edición de UNA fila (la línea que se dará de alta en Sigrid).

        (F-065 R6–R11, R13) ``campos`` son SOLO los que el administrativo
        cambió (``ConciliacionEditBody.campos``): un campo ausente no cambia
        y uno presente a ``None`` se vacía. Claves: ``codigo_partida``,
        ``descripcion``, ``cantidad`` (Q, en la unidad del precio),
        ``unidad``, ``precio_unitario``, ``descuento``, ``codigo_externo``.

        - Lo que llega igual a lo que ya hay se descarta (R8). Si no queda
          nada, no se escribe lo valorado (importe, su origen, descuento ni
          revisión): solo se completa una ``cantidad_convertida`` nula con la
          del albarán (R10) y, con ``bloquear``, se marca la fila.
        - Las cantidades salen de ``cantidades_tras_editar`` (R6, R7); la
          convertida nunca queda nula si hay cantidad (R10).
        - El importe se recalcula (``precio × Q × (1 − dto/100)``) solo si
          cambia lo que entra en él: cantidad, precio o descuento. Editar la
          descripción, la partida o el código externo no reetiqueta un
          importe declarado (F-019 R24). Lo que cambia el administrativo pisa
          lo valorado y la fila sale de revisión (R11).
        - (F-051, regla vigente hasta la fase 2) Cambiar partida (salvo
          vaciarla = almacén, R12, o poner la de la casada, R20), unidad o
          precio de una fila Contrato la convierte en Nueva (derivada
          ``manual_override``); en una Nueva se edita la derivada in situ.
        - ``bloquear`` (R13): «Guardar» = aplicar y bloquear, en la misma
          transacción, aunque no haya cambios.
        - (F-078 R9–R11) El estado actual es el de la FILA (no se completa con
          su línea); la descripción cambiada va a ``descripcion_linea`` en toda
          fila y la unidad cambiada, sin conversión, también a
          ``unidad_albaran``. No aplica ``fila_a_guardar``: lo vaciado se ve
          vacío (R16).
        - (F-106 R5–R10, D1) Cantidad, precio o descuento ⇒ se recalcula el
          importe (``calculated``, sea cual sea su origen). ``importe`` ⇒ se
          guarda a 2 decimales y se despeja el precio (6 decimales) con la Q y
          el dto resultantes; el dto se queda. Un precio despejado distinto es
          un precio cambiado (Contrato → Nueva; en una Nueva, su derivada). Un
          importe igual al de hoy se descarta salvo que cambie Q o d (entonces
          manda: el revisor lo volvió a teclear). ``cuadrar`` (botones de una
          fila que NO cuadra): ``importe`` ⇒ como cambiar Q; ``precio`` ⇒ como
          teclear el importe actual. Sobre una que cuadra no escribe nada.
          ``NoDespejable`` (importe ≠ 0 con Q 0 o dto 100 %) antes de escribir.

        NO revalora. Devuelve True si la fila es del documento.
        """
        self.initialize()
        cambios_pedidos = dict(campos or {})

        def _txt(v: str | None) -> str:
            return (v or "").strip()

        with self._session_factory.create_session() as session:
            # F-053 R26 (alta, con el merge bloqueado), F-065 R4 (aprobado) y
            # R14 (fila guardada).
            self._exigir_editable(session, document_id, valuation_line_id)
            row = session.execute(
                text(
                    "SELECT lv.id, lv.valuation_id, lv.merge_line_id, "
                    "       lv.matched_contrato_line_id, "
                    "       lv.derived_contrato_line_id, "
                    "       lv.cantidad_albaran, lv.cantidad_convertida, "
                    "       lv.factor_conversion, "
                    "       lv.codigo_partida_final, lv.descripcion_linea, "
                    "       lv.precio_unitario_final, lv.unidad_contrato, "
                    "       lv.descuento_albaran_aplicado, lv.codigo_externo, "
                    "       lv.review_reasons_json, lv.importe_calculado, "
                    "       v.document_id, v.contrato_codigo "
                    "FROM albaran_line_valuations lv "
                    "JOIN albaran_valuations v ON v.id = lv.valuation_id "
                    "WHERE lv.id = :vid"
                ),
                {"vid": valuation_line_id},
            ).mappings().first()
            if row is None or row["document_id"] != document_id:
                return False

            valuation_id = row["valuation_id"]
            matched_id = row["matched_contrato_line_id"]
            derived_id = row["derived_contrato_line_id"]
            if matched_id is None and derived_id is None:
                return False

            # ---- estado ACTUAL: el de la FILA (F-078 R9) ----
            # Lo que la fila no tiene no se completa con su línea: la ficha lo
            # pinta vacío (R7) y así se guarda.
            # (F-051 D1) La partida actual es la FINAL: vacía = almacén.
            cur_partida = _txt(row["codigo_partida_final"]) or None
            cur_unidad = row["unidad_contrato"]
            cur_precio = row["precio_unitario_final"]
            cur_desc = row["descripcion_linea"]
            tabla_casada = (
                "albaran_contrato_lines_merge" if matched_id is not None
                else "contrato_lines_derived"
            )
            # Su línea, solo por su partida (R20/R25: poner la de su línea no
            # cambia el origen).
            partida_casada: str | None = session.execute(
                text(
                    f"SELECT codigo_partida FROM {tabla_casada} WHERE id = :id"  # noqa: S608
                ),
                {"id": matched_id if matched_id is not None else derived_id},
            ).scalar()
            q_actual = (
                row["cantidad_convertida"]
                if row["cantidad_convertida"] is not None
                else row["cantidad_albaran"]
            )
            actual: dict[str, Any] = {
                "codigo_partida": cur_partida,
                "descripcion": _txt(cur_desc) or None,
                "cantidad": q_actual,
                "unidad": _txt(cur_unidad) or None,
                "precio_unitario": cur_precio,
                "descuento": _sanear_descuento(row["descuento_albaran_aplicado"]),
                "codigo_externo": _txt(row["codigo_externo"]) or None,
                CAMPO_IMPORTE: row["importe_calculado"],
            }

            # ---- solo lo que de verdad cambia (R8) ----
            cambios: dict[str, Any] = {}
            for campo, valor in cambios_pedidos.items():
                if campo not in actual:
                    continue
                if campo in ("cantidad", "precio_unitario"):
                    nuevo = valor
                    igual = _mismo_numero(nuevo, actual[campo])
                elif campo == CAMPO_IMPORTE:
                    nuevo = round(float(valor), 2)
                    igual = _mismo_numero(nuevo, actual[campo])
                elif campo == "descuento":
                    nuevo = _sanear_descuento(valor)
                    igual = _mismo_numero(nuevo, actual[campo])
                else:
                    nuevo = _txt(valor) or None
                    igual = nuevo == actual[campo]
                if not igual:
                    cambios[campo] = nuevo
            # (F-106 R6) El importe tecleado manda aunque sea el de hoy si
            # cambian Q o d: si no, se recalcularía y se perdería.
            if (
                CAMPO_IMPORTE in cambios_pedidos
                and CAMPO_IMPORTE not in cambios
                and {"cantidad", "descuento"} & set(cambios)
            ):
                cambios[CAMPO_IMPORTE] = round(float(cambios_pedidos[CAMPO_IMPORTE]), 2)

            # (F-106 R9) Los botones solo actúan sobre una fila que no cuadra.
            modo = recalculo_de_fila(
                cambios=cambios,
                cuadrar=cuadrar,  # type: ignore[arg-type]
                no_cuadra=cuadra_linea(
                    q_actual, cur_precio, row["descuento_albaran_aplicado"],
                    row["importe_calculado"],
                ) is False,
            )

            # (F-065 H2) El aviso «revisa la cantidad» se va cuando la cantidad
            # se revisa: al cambiarla o al guardar la fila.
            quita_aviso = (
                (bloquear or "cantidad" in cambios)
                and MOTIVO_UNIDAD_CAMBIADA in motivos_de_json(row["review_reasons_json"])
            )
            razones = motivos_con(
                row["review_reasons_json"], MOTIVO_UNIDAD_CAMBIADA, False,
            )

            if not cambios and modo is None:
                # (R10) Completar la convertida y (R13) bloquear: nada más.
                session.execute(
                    text(
                        "UPDATE albaran_line_valuations SET "
                        "  cantidad_convertida = COALESCE("
                        "    cantidad_convertida, cantidad_albaran)"
                        + (", bloqueada = TRUE" if bloquear else "")
                        + (", review_reasons_json = :razones" if quita_aviso else "")
                        + (", review_required = FALSE"
                           if quita_aviso and not motivos_de_json(razones) else "")
                        + " WHERE id = :vid"
                    ),
                    {"vid": valuation_line_id, "razones": razones},
                )
                session.commit()
                return True

            nuevo = {**actual, **cambios}

            # ---- cantidades (R6, R7, R10) ----
            if "cantidad" in cambios and cambios["cantidad"] is None:
                cantidad_albaran, cantidad_convertida = None, None
            else:
                cantidad_albaran, cantidad_convertida = cantidades_tras_editar(
                    q_nueva=cambios.get("cantidad"),
                    cantidad_albaran=row["cantidad_albaran"],
                    cantidad_convertida=row["cantidad_convertida"],
                    factor=row["factor_conversion"],
                )
                if cantidad_convertida is None:
                    cantidad_convertida = cantidad_albaran

            # ---- importe y precio (F-106 D1) ----
            # Antes de escribir nada: ``NoDespejable`` no deja la fila a medias.
            importe_nuevo: float | None = None
            if modo == "precio":
                precio_despejado, importe_nuevo = recalcular_fila(
                    cantidad=cantidad_convertida,
                    precio=nuevo["precio_unitario"],
                    descuento=nuevo["descuento"],
                    importe=nuevo[CAMPO_IMPORTE],
                    editados={CAMPO_IMPORTE},
                )
                if not _mismo_numero(precio_despejado, cur_precio):
                    # (R8) Un precio despejado es un precio cambiado.
                    cambios["precio_unitario"] = precio_despejado
                    nuevo["precio_unitario"] = precio_despejado
            elif modo == "importe":
                importe_nuevo = _importe_de_linea(
                    precio_unitario=nuevo["precio_unitario"],
                    cantidad=cantidad_convertida,
                    descuento_pct=nuevo["descuento"],
                )

            params: dict[str, Any] = {
                "vid": valuation_line_id,
                "ca": cantidad_albaran,
                "cc": cantidad_convertida,
                "pu": nuevo["precio_unitario"],
                "uni": nuevo["unidad"],
                "part": nuevo["codigo_partida"],
                "codext": nuevo["codigo_externo"],
            }
            sets = [
                "cantidad_albaran = :ca", "cantidad_convertida = :cc",
                "precio_unitario_final = :pu", "unidad_contrato = :uni",
                "codigo_partida_final = :part", "codigo_externo = :codext",
                "review_required = FALSE",
            ]
            if bloquear:
                sets.append("bloqueada = TRUE")
            if quita_aviso:
                sets.append("review_reasons_json = :razones")
                params["razones"] = razones
            # (F-078 R10) La descripción cambiada va a la fila en TODA fila
            # (Contrato o Nueva, con o sin blanca); vaciarla la deja vacía.
            if "descripcion" in cambios:
                sets.append("descripcion_linea = :desc")
                params["desc"] = nuevo["descripcion"]
            # (F-078 R11) La unidad cambiada, también la del albarán sin
            # conversión (la que manda sv9 en una sin vincular).
            if "unidad" in cambios and sin_conversion(row["factor_conversion"]):
                sets.append("unidad_albaran = :uni")

            # ---- importe: solo si cambia lo que entra en él (R11) ----
            cambia_importe = modo is not None
            if cambia_importe:
                params["dto"] = nuevo["descuento"]
                params["imp"] = importe_nuevo
                sets += [
                    "descuento_albaran_aplicado = :dto",
                    "importe_calculado = :imp",
                    "importe_source = 'calculated'",
                ]

            # ---- origen ----
            elige_almacen = (
                "codigo_partida" in cambios and nuevo["codigo_partida"] is None
            )
            # (F-065 R25, R26) partida, precio o unidad ⇒ Nueva, sin
            # confirmación; vaciar (almacén) o la de su línea, no.
            if cambia_origen(
                es_contrato=matched_id is not None,
                partida_casada=partida_casada,
                cambios=cambios,
            ):
                # CONTRATO → NUEVA: derivada manual con los valores
                # resultantes; se conserva todo lo demás tal cual.
                params["did"] = session.execute(
                    text(
                        "INSERT INTO contrato_lines_derived ("
                        "  created_by_valuation_id, source_document_id, "
                        "  codigo_contrato, codigo_producto, "
                        "  descripcion_linea, unidad_medida, "
                        "  precio_unitario, codigo_partida, "
                        "  origen, created_at_utc) "
                        "VALUES (:vid, :doc, :cod, NULL, :desc, :uni, :pu, "
                        "  :part, 'manual_override', :now) "
                        "RETURNING id"
                    ),
                    {
                        "vid": valuation_id,
                        "doc": document_id,
                        "cod": row["contrato_codigo"] or "",
                        "desc": nuevo["descripcion"],
                        "uni": nuevo["unidad"],
                        "pu": nuevo["precio_unitario"],
                        "part": nuevo["codigo_partida"],
                        "now": self._utc_iso(),
                    },
                ).scalar_one()
                sets += [
                    "matched_contrato_line_id = NULL",
                    "derived_contrato_line_id = :did",
                    "precio_unitario_source = 'manual_derived'",
                    "precio_unitario_agreement = 'manual'",
                ]
            elif derived_id is not None:
                # NUEVA: edición in situ de la derivada.
                session.execute(
                    text(
                        "UPDATE contrato_lines_derived SET "
                        "  codigo_partida = :part, "
                        "  descripcion_linea = :desc, "
                        "  unidad_medida = :uni, "
                        "  precio_unitario = :pu "
                        "WHERE id = :did"
                    ),
                    {
                        "part": nuevo["codigo_partida"],
                        "desc": nuevo["descripcion"],
                        "uni": nuevo["unidad"],
                        "pu": nuevo["precio_unitario"],
                        "did": derived_id,
                    },
                )
                sets += [
                    "precio_unitario_source = 'manual_derived'",
                    "precio_unitario_agreement = 'manual'",
                ]

            if elige_almacen:
                sets.append("partida_action = :accion_almacen")
                params["accion_almacen"] = ACCION_ALMACEN_ELEGIDO

            session.execute(
                text(
                    "UPDATE albaran_line_valuations SET "
                    + ", ".join(sets)
                    + " WHERE id = :vid"
                ),
                params,
            )
            if cambia_importe:
                self._recalcular_total_in_session(session, valuation_id)
            session.commit()
            return True

    @staticmethod
    def _materializar_fila_in_session(session: Any, valuation_line_id: int) -> None:
        """(F-078 R16) Lee la fila, su línea y su blanca; aplica
        ``fila_a_guardar`` y escribe SOLO las columnas que cambian. Misma
        transacción que el llamador (no confirma). Toda vía que crea o
        reapunta una fila la llama al final; el PATCH no (lo vaciado se ve
        vacío)."""
        fila = session.execute(
            _SQL_FILA_A_MATERIALIZAR, {"vid": valuation_line_id},
        ).mappings().first()
        if fila is None:
            return
        cambios = cambios_a_guardar(
            CamposFila(**{c: fila[c] for c in _COLUMNAS_FILA_A_GUARDAR}),
            _linea_de_la_fila(fila),
            fila["concepto_blanca"],
        )
        if not cambios:
            return
        session.execute(
            text(
                "UPDATE albaran_line_valuations SET "
                + ", ".join(f"{c} = :{c}" for c in cambios)
                + " WHERE id = :vid"
            ),
            {**cambios, "vid": valuation_line_id},
        )

    def _recalcular_total_in_session(self, session: Any, valuation_id: str) -> None:
        """Total de la cabecera = suma de los importes de sus filas, en
        céntimos (F-019 R26: ``ROUND``, que la suma en coma flotante arrastra
        cola binaria y el total se compara por igualdad con Sigrid)."""
        session.execute(
            text(
                "UPDATE albaran_valuations SET "
                "total_valorado = ROUND(CAST(COALESCE(("
                "  SELECT SUM(importe_calculado) "
                "  FROM albaran_line_valuations "
                "  WHERE valuation_id = :vid"
                "), 0) AS numeric), 2), "
                "updated_at_utc = :now "
                "WHERE id = :vid"
            ),
            {"vid": valuation_id, "now": self._utc_iso()},
        )

    def bloquear_linea(self, *, document_id: str, valuation_line_id: int) -> bool:
        """(F-065 R13) Marca la fila guardada. ``False`` si no es del documento."""
        return self._marcar_bloqueada(document_id, valuation_line_id, True)

    def desbloquear_linea(self, *, document_id: str, valuation_line_id: int) -> bool:
        """(F-065 R15) La vuelve editable. ``False`` si no es del documento.
        No exige permiso especial (P13): cualquiera que edite."""
        return self._marcar_bloqueada(document_id, valuation_line_id, False)

    def _marcar_bloqueada(
        self, document_id: str, valuation_line_id: int, bloqueada: bool,
    ) -> bool:
        self.initialize()
        with self._session_factory.create_session() as session:
            # F-053 R26 (alta, con el merge bloqueado) y F-065 R4 (aprobado).
            self._exigir_editable(session, document_id)
            tocadas = session.execute(
                text(
                    "UPDATE albaran_line_valuations SET bloqueada = :b "
                    "WHERE id = :vid AND valuation_id IN ("
                    "  SELECT id FROM albaran_valuations WHERE document_id = :doc"
                    ") RETURNING id"
                ),
                {"b": bloqueada, "vid": int(valuation_line_id), "doc": document_id},
            ).all()
            session.commit()
            return bool(tocadas)

    def asignar_almacen(
        self,
        *,
        document_id: str,
        valuation_line_ids: list[int] | None,
    ) -> list[int]:
        """(F-051 R14-R16, R23) Pone en ALMACÉN líneas de valoración del
        documento: partida final NULL y ``partida_action =
        'almacen_elegido'``.

        ``valuation_line_ids=None`` = TODAS las líneas de la valoración
        del documento (base, complementarias y sintéticas), también las
        que tenían partida. Un único UPDATE en una transacción: o todas
        o ninguna. NO toca la casada (``matched_contrato_line_id``), la
        derivada, los importes ni la revisión: una fila Sigrid sigue
        siendo Sigrid (D4). Una línea ajena al documento no se toca.

        Devuelve los ids tocados (ordenados); ``[]`` si no tocó nada.
        Como todo override de sv4, se pierde al revalorar (D5, F-058).
        """
        if valuation_line_ids is not None and not valuation_line_ids:
            return []
        self.initialize()
        sql = (
            "UPDATE albaran_line_valuations SET "
            "  codigo_partida_final = NULL, "
            "  partida_action = :accion "
            "WHERE valuation_id = ("
            "  SELECT id FROM albaran_valuations WHERE document_id = :doc"
            ") AND NOT bloqueada"
        )
        params: dict[str, Any] = {
            "accion": ACCION_ALMACEN_ELEGIDO,
            "doc": document_id,
        }
        if valuation_line_ids is None:
            sentencia = text(sql + " RETURNING id")
        else:
            sentencia = text(sql + " AND id IN :ids RETURNING id").bindparams(
                bindparam("ids", expanding=True),
            )
            params["ids"] = [int(i) for i in valuation_line_ids]
        with self._session_factory.create_session() as session:
            # F-053 R26 (alta, con el merge bloqueado) y F-065 R4 (aprobado).
            self._exigir_editable(session, document_id)
            # (F-065 R14) Una fila guardada no pasa a almacén (409); «todas»
            # se la salta (``NOT bloqueada`` en la sentencia).
            for valuation_line_id in params.get("ids", []):
                self._exigir_linea_desbloqueada(session, document_id, valuation_line_id)
            tocadas = [int(r[0]) for r in session.execute(sentencia, params)]
            session.commit()
        return sorted(tocadas)

    def snapshot_lineas_valoracion(self, *, document_id: str) -> list[dict]:
        """(F-051 R18) Copia completa (estado ANTERIOR) de TODAS las
        líneas de valoración del documento, para el historial de
        «Almacén a todas las líneas». Mismo formato que ``snapshot_row``.
        """
        self.initialize()
        with self._session_factory.create_session() as session:
            filas = session.execute(
                text(
                    "SELECT * FROM albaran_line_valuations "
                    "WHERE valuation_id = ("
                    "  SELECT id FROM albaran_valuations "
                    "  WHERE document_id = :doc"
                    ") ORDER BY id"
                ),
                {"doc": document_id},
            ).mappings().all()
        return [
            {"table": "albaran_line_valuations", "values": dict(fila)}
            for fila in filas
        ]

    def remove_line_valuation(
        self,
        *,
        document_id: str,
        valuation_line_id: int,
    ) -> bool:
        """Borra DEFINITIVAMENTE la linea de valoracion (la fila salmon).

        La linea blanca (merge) NO se toca: sigue mostrandose y reaparece
        el boton '+' para volver a traer una conciliacion si se quiere.
        La linea borrada deja de contar en el total. Si tenia una linea
        derivada ('nueva'), tambien se limpia. Devuelve True si borro.
        """
        self.initialize()
        with self._session_factory.create_session() as session:
            # F-053 R26 (alta, con el merge bloqueado), F-065 R4 (aprobado) y
            # R14 (fila guardada).
            self._exigir_editable(session, document_id, valuation_line_id)
            row = session.execute(
                text(
                    "SELECT lv.id, lv.valuation_id, "
                    "       lv.derived_contrato_line_id, v.document_id "
                    "FROM albaran_line_valuations lv "
                    "JOIN albaran_valuations v ON v.id = lv.valuation_id "
                    "WHERE lv.id = :vid"
                ),
                {"vid": valuation_line_id},
            ).mappings().first()
            if row is None or row["document_id"] != document_id:
                return False

            valuation_id = row["valuation_id"]
            derived_id = row["derived_contrato_line_id"]

            session.execute(
                text("DELETE FROM albaran_line_valuations WHERE id = :vid"),
                {"vid": valuation_line_id},
            )
            if derived_id is not None:
                session.execute(
                    text("DELETE FROM contrato_lines_derived WHERE id = :did"),
                    {"did": derived_id},
                )

            # Recalcular total de la cabecera (la linea borrada ya no suma).
            self._recalcular_total_in_session(session, valuation_id)
            session.commit()
            return True

    def add_conciliacion_for_merge_line(
        self,
        *,
        document_id: str,
        merge_line_id: int,
        mode: str = "contract_line",
        matched_contrato_line_id: int | None = None,
        precio_unitario: float | None = None,
        descripcion: str | None = None,
    ) -> bool:
        """Trae una conciliacion a una linea de albaran SIN valoracion.

        mode='contract_line': apunta la linea a ``matched_contrato_line_id``
          (linea de albaran_contrato_lines_merge), trae su precio. Salmon
          "Sigrid".
        mode='nueva': crea una linea DERIVADA copiando la BLANCA del albaran
          (concepto/precio/partida declarados) -> salmon "Nueva", igual que
          el modo "nueva" del badge de edicion.

        Crea la cabecera de valoracion si el documento aun no la tiene. NO
        revalora: la correccion se pierde si luego se pulsa "Valorar ahora".
        Devuelve True si ok.
        """
        import uuid

        self.initialize()
        with self._session_factory.create_session() as session:
            # F-053 R26 (alta, con el merge bloqueado) y F-065 R4 (aprobado).
            self._exigir_editable(session, document_id)
            ml = session.execute(
                text(
                    "SELECT id, document_id, cantidad, concepto, "
                    "       codigo_imputacion, precio, descuento, unidad_medida "
                    "FROM albaran_lines_merge WHERE id = :id"
                ),
                {"id": merge_line_id},
            ).mappings().first()
            if ml is None or ml["document_id"] != document_id:
                return False

            now = self._utc_iso()

            # Cabecera de valoracion (crear si no existe). contrato_codigo
            # se usa como codigo_contrato de la derivada en modo "nueva".
            hdr = session.execute(
                text(
                    "SELECT id, contrato_codigo FROM albaran_valuations "
                    "WHERE document_id = :doc"
                ),
                {"doc": document_id},
            ).mappings().first()
            if hdr is None:
                valuation_id = str(uuid.uuid4())
                contrato_codigo = None
                session.execute(
                    text(
                        "INSERT INTO albaran_valuations "
                        "  (id, document_id, status, created_at_utc) "
                        "VALUES (:id, :doc, 'manual', :now)"
                    ),
                    {"id": valuation_id, "doc": document_id, "now": now},
                )
            else:
                valuation_id = hdr["id"]
                contrato_codigo = hdr["contrato_codigo"]

            cantidad = ml["cantidad"]

            # ----------------------------------------------------------------
            # Resolver la conciliacion segun el modo.
            # ----------------------------------------------------------------
            mid_val: int | None = None
            did_val: int | None = None

            if mode == "nueva":
                precio = (
                    precio_unitario
                    if precio_unitario is not None
                    else ml["precio"]
                )
                desc = descripcion or ml["concepto"]
                partida = ml["codigo_imputacion"]
                # (F-078 R13) En Nueva, la unidad de la blanca (fila y derivada).
                unidad_contrato = ml["unidad_medida"]
                source = "manual_derived"
                did_val = session.execute(
                    text(
                        "INSERT INTO contrato_lines_derived ("
                        "  created_by_valuation_id, source_document_id, "
                        "  codigo_contrato, codigo_producto, descripcion_linea, "
                        "  unidad_medida, precio_unitario, codigo_partida, "
                        "  origen, created_at_utc) "
                        "VALUES (:vid, :doc, :cod, NULL, :desc, :uni, :pu, "
                        "  :part, 'manual_override', :now) "
                        "RETURNING id"
                    ),
                    {
                        "vid": valuation_id,
                        "doc": document_id,
                        "cod": contrato_codigo or "",
                        "desc": desc,
                        "uni": unidad_contrato,
                        "pu": precio,
                        "part": partida,
                        "now": now,
                    },
                ).scalar_one()
            else:
                if matched_contrato_line_id is None:
                    return False
                cl = session.execute(
                    text(
                        "SELECT precio_unitario, unidad_medida, codigo_partida, "
                        "       descripcion_linea "
                        "FROM albaran_contrato_lines_merge WHERE id = :id"
                    ),
                    {"id": matched_contrato_line_id},
                ).mappings().first()
                if cl is None:
                    return False
                precio = (
                    precio_unitario
                    if precio_unitario is not None
                    else cl["precio_unitario"]
                )
                desc = ml["concepto"]
                partida = ml["codigo_imputacion"] or cl["codigo_partida"]
                unidad_contrato = cl["unidad_medida"]
                source = "manual_contract"
                mid_val = matched_contrato_line_id

            # (F-019 R23) El descuento leído en la línea blanca del
            # albarán entra en la fórmula también aquí.
            importe = _importe_de_linea(
                precio_unitario=precio,
                cantidad=cantidad,
                descuento_pct=ml["descuento"],
            )

            existing = session.execute(
                text(
                    "SELECT id FROM albaran_line_valuations "
                    "WHERE valuation_id = :v AND merge_line_id = :m"
                ),
                {"v": valuation_id, "m": merge_line_id},
            ).mappings().first()

            if existing is None:
                # Crear la linea de valoracion completa (todas las columnas
                # NOT NULL cubiertas). line_kind=from_albaran.
                fila_id = session.execute(
                    text(
                        "INSERT INTO albaran_line_valuations ("
                        "  valuation_id, merge_line_id, matched_contrato_line_id, "
                        "  derived_contrato_line_id, "
                        "  precio_unitario_contrato_db, precio_unitario_final, "
                        "  precio_unitario_source, precio_unitario_agreement, "
                        "  unidad_albaran, unidad_contrato, unidad_categoria, "
                        "  unidad_category_match, cantidad_albaran, "
                        "  cantidad_convertida, factor_conversion, importe_calculado, "
                        "  importe_source, codigo_partida_albaran, codigo_partida_final, "
                        "  partida_action, descripcion_linea, line_kind, "
                        "  match_confidence_pct, match_method, review_required, "
                        "  descuento_albaran_aplicado, created_at_utc) "
                        "VALUES ("
                        "  :v, :m, :mid, :did, :pu, :pu, :src, 'manual', "
                        "  NULL, :uc, 'manual', TRUE, :can, :can, 1.0, :imp, "
                        "  'calculated', :part, :part, 'manual', :desc, "
                        "  'from_albaran', 100.0, 'manual', FALSE, :dto, :now) "
                        "RETURNING id"
                    ),
                    {
                        "v": valuation_id,
                        "m": merge_line_id,
                        "mid": mid_val,
                        "did": did_val,
                        "pu": precio,
                        "src": source,
                        "uc": unidad_contrato,
                        "can": cantidad,
                        "imp": importe,
                        "part": partida,
                        "desc": desc,
                        "dto": _sanear_descuento(ml["descuento"]),
                        "now": now,
                    },
                ).scalar_one()
            else:
                # Ya habia valoracion para esa linea: la re-apuntamos
                # (al contrato o a la derivada nueva) como en
                # set_line_conciliacion, con su concepto y su unidad (F-078 R13).
                fila_id = existing["id"]
                session.execute(
                    text(
                        "UPDATE albaran_line_valuations SET "
                        "  matched_contrato_line_id = :mid, "
                        "  derived_contrato_line_id = :did, "
                        "  precio_unitario_final = :pu, "
                        "  precio_unitario_source = :src, "
                        "  precio_unitario_agreement = 'manual', "
                        "  unidad_contrato = :uc, "
                        "  descripcion_linea = :desc, "
                        "  importe_calculado = :imp, "
                        "  importe_source = 'calculated', "
                        "  review_required = FALSE "
                        "WHERE id = :id"
                    ),
                    {
                        "mid": mid_val,
                        "did": did_val,
                        "pu": precio,
                        "src": source,
                        "uc": unidad_contrato,
                        "desc": desc,
                        "imp": importe,
                        "id": fila_id,
                    },
                )

            # (F-078 R13, R16) La fila nace con lo que se va a ver.
            self._materializar_fila_in_session(session, int(fila_id))
            # Recalcular total de la cabecera.
            self._recalcular_total_in_session(session, valuation_id)
            session.commit()
            return True


    def add_standalone_valuation_line(self, *, document_id: str) -> int | None:
        """Crea una línea salmón SUELTA (sin línea blanca de la IA).

        Inserta una ``albaran_line_valuations`` con ``merge_line_id`` NULL y
        ``line_kind='manual'``, más una conciliación DERIVADA en blanco
        (salmón "Nueva"). Así aparece como una fila salmón editable que el
        usuario puede rellenar a mano, o enganchar a una línea de contrato
        (→ Sigrid) desde el desplegable de descripción de la propia salmón,
        igual que el resto de salmón. NO toca ninguna línea blanca.

        Crea la cabecera de valoración si el documento aún no la tiene.
        Devuelve el ``valuation_line_id`` nuevo, o ``None`` si el documento
        no existe.

        Nota: como el resto de correcciones manuales, esta línea se PIERDE
        si luego se pulsa "Valorar ahora" (sv5/sv6 regenera la valoración).
        """
        import uuid

        self.initialize()
        with self._session_factory.create_session() as session:
            # F-053 R26 (alta, con el merge bloqueado) y F-065 R4 (aprobado).
            self._exigir_editable(session, document_id)
            doc = session.execute(
                text(
                    "SELECT id FROM albaran_documents_merge WHERE id = :id"
                ),
                {"id": document_id},
            ).first()
            if doc is None:
                return None

            now = self._utc_iso()

            hdr = session.execute(
                text(
                    "SELECT id, contrato_codigo FROM albaran_valuations "
                    "WHERE document_id = :doc"
                ),
                {"doc": document_id},
            ).mappings().first()
            if hdr is None:
                valuation_id = str(uuid.uuid4())
                contrato_codigo = None
                session.execute(
                    text(
                        "INSERT INTO albaran_valuations "
                        "  (id, document_id, status, created_at_utc) "
                        "VALUES (:id, :doc, 'manual', :now)"
                    ),
                    {"id": valuation_id, "doc": document_id, "now": now},
                )
            else:
                valuation_id = hdr["id"]
                contrato_codigo = hdr["contrato_codigo"]

            # Línea derivada EN BLANCO -> salmón "Nueva" (kind=derived).
            did_val = session.execute(
                text(
                    "INSERT INTO contrato_lines_derived ("
                    "  created_by_valuation_id, source_document_id, "
                    "  codigo_contrato, codigo_producto, descripcion_linea, "
                    "  unidad_medida, precio_unitario, codigo_partida, "
                    "  origen, created_at_utc) "
                    "VALUES (:vid, :doc, :cod, NULL, NULL, NULL, NULL, NULL, "
                    "  'manual_override', :now) "
                    "RETURNING id"
                ),
                {
                    "vid": valuation_id,
                    "doc": document_id,
                    "cod": contrato_codigo or "",
                    "now": now,
                },
            ).scalar_one()

            # Valuation line SUELTA. Mismos literales que el INSERT de
            # add_conciliacion_for_merge_line (conocido válido) salvo:
            # merge_line_id NULL, line_kind 'manual' y campos de valor NULL
            # (línea en blanco que el usuario rellenará).
            new_id = session.execute(
                text(
                    "INSERT INTO albaran_line_valuations ("
                    "  valuation_id, merge_line_id, matched_contrato_line_id, "
                    "  derived_contrato_line_id, "
                    "  precio_unitario_contrato_db, precio_unitario_final, "
                    "  precio_unitario_source, precio_unitario_agreement, "
                    "  unidad_albaran, unidad_contrato, unidad_categoria, "
                    "  unidad_category_match, cantidad_albaran, "
                    "  cantidad_convertida, factor_conversion, importe_calculado, "
                    "  importe_source, codigo_partida_albaran, codigo_partida_final, "
                    "  partida_action, descripcion_linea, line_kind, "
                    "  match_confidence_pct, match_method, review_required, "
                    "  created_at_utc) "
                    "VALUES ("
                    "  :v, NULL, NULL, :did, NULL, NULL, 'manual_derived', "
                    "  'manual', NULL, NULL, 'manual', TRUE, NULL, NULL, 1.0, "
                    "  NULL, 'calculated', NULL, NULL, 'manual', NULL, "
                    "  'manual', 100.0, 'manual', FALSE, :now) "
                    "RETURNING id"
                ),
                {"v": valuation_id, "did": did_val, "now": now},
            ).scalar_one()

            # Total de cabecera no cambia (importe NULL no suma), pero
            # marcamos updated_at por consistencia.
            session.execute(
                text(
                    "UPDATE albaran_valuations SET updated_at_utc = :now "
                    "WHERE id = :v"
                ),
                {"v": valuation_id, "now": now},
            )
            session.commit()
            return int(new_id)

    # ------------------------------------------------------------------ #
    # Traer líneas de contrato (jul 2026): crea líneas salmón YA casadas.
    # ------------------------------------------------------------------ #
    def add_valuation_lines_from_contrato(
        self,
        *,
        document_id: str,
        lineas: list[tuple[int, float]],
    ) -> list[int]:
        """(F-065 R23) Crea UNA fila Contrato por cada ``(línea de contrato,
        cantidad)``: casada con ella (``matched_contrato_line_id``), con su
        partida, descripción, unidad y precio, ``cantidad_albaran =
        cantidad_convertida = Q``, ``factor`` 1 e importe calculado (válida
        para sv9 sin más edición). La cantidad es obligatoria y ≠ 0
        (``ValueError`` sin tocar nada).

        Solo admite líneas de contratos DEL PROPIO documento (las ajenas se
        ignoran). Crea la cabecera de valoración si no existe y recalcula su
        total. Devuelve los ids creados (el deshacer los borra).
        """
        import uuid

        pares = [(int(cid), cantidad) for cid, cantidad in (lineas or [])]
        if any(cantidad is None or float(cantidad) == 0 for _, cantidad in pares):
            raise ValueError("Cada línea traída necesita su cantidad (distinta de 0).")
        if not pares:
            return []

        self.initialize()
        with self._session_factory.create_session() as session:
            # F-053 R26 (alta, con el merge bloqueado) y F-065 R4 (aprobado).
            self._exigir_editable(session, document_id)
            doc = session.execute(
                text(
                    "SELECT id FROM albaran_documents_merge WHERE id = :id"
                ),
                {"id": document_id},
            ).first()
            if doc is None:
                raise KeyError(f"Documento no encontrado: {document_id}")

            # Líneas de contrato válidas: deben colgar de un contrato de
            # ESTE documento. Se conserva el orden de selección.
            rows = session.execute(
                text(
                    "SELECT l.id, l.codigo_partida, l.descripcion_linea, "
                    "       l.precio_unitario, l.unidad_medida "
                    "FROM albaran_contrato_lines_merge l "
                    "WHERE l.id IN :ids "
                    "  AND l.contrato_id IN ("
                    "    SELECT id FROM albaran_contratos_merge "
                    "    WHERE document_id = :doc)"
                ).bindparams(bindparam("ids", expanding=True)),
                {"ids": [cid for cid, _ in pares], "doc": document_id},
            ).mappings().all()
            por_id = {int(r["id"]): r for r in rows}

            now = self._utc_iso()
            hdr = session.execute(
                text(
                    "SELECT id FROM albaran_valuations "
                    "WHERE document_id = :doc"
                ),
                {"doc": document_id},
            ).mappings().first()
            if hdr is None:
                valuation_id = str(uuid.uuid4())
                session.execute(
                    text(
                        "INSERT INTO albaran_valuations "
                        "  (id, document_id, status, created_at_utc) "
                        "VALUES (:id, :doc, 'manual', :now)"
                    ),
                    {"id": valuation_id, "doc": document_id, "now": now},
                )
            else:
                valuation_id = hdr["id"]

            creadas: list[int] = []
            for cid, cantidad in pares:
                cl = por_id.get(cid)
                if cl is None:
                    logger.warning(
                        "[from-contrato] línea de contrato %s no pertenece "
                        "al documento %s; ignorada",
                        cid, document_id,
                    )
                    continue
                nuevo_id = session.execute(
                    text(
                        "INSERT INTO albaran_line_valuations ("
                        "  valuation_id, merge_line_id, "
                        "  matched_contrato_line_id, "
                        "  derived_contrato_line_id, "
                        "  precio_unitario_contrato_db, precio_unitario_final, "
                        "  precio_unitario_source, precio_unitario_agreement, "
                        "  unidad_albaran, unidad_contrato, unidad_categoria, "
                        "  unidad_category_match, cantidad_albaran, "
                        "  cantidad_convertida, factor_conversion, "
                        "  importe_calculado, importe_source, "
                        "  codigo_partida_albaran, codigo_partida_final, "
                        "  partida_action, descripcion_linea, line_kind, "
                        "  match_confidence_pct, match_method, "
                        "  review_required, created_at_utc) "
                        "VALUES ("
                        "  :v, NULL, :cid, NULL, :precio, :precio, "
                        "  'manual_contract', 'manual', NULL, :unidad, "
                        "  'manual', TRUE, :q, :q, 1.0, :imp, "
                        "  'calculated', NULL, :partida, 'manual', "
                        "  :descr, 'manual', 100.0, 'manual', FALSE, :now) "
                        "RETURNING id"
                    ),
                    {
                        "v": valuation_id,
                        "cid": cid,
                        "precio": cl["precio_unitario"],
                        "unidad": cl["unidad_medida"],
                        "q": float(cantidad),
                        "imp": _importe_de_linea(
                            precio_unitario=cl["precio_unitario"],
                            cantidad=float(cantidad),
                            descuento_pct=None,
                        ),
                        "partida": cl["codigo_partida"],
                        "descr": cl["descripcion_linea"],
                        "now": now,
                    },
                ).scalar_one()
                # (F-078 R14, R16) Con la unidad de su línea en ``unidad_albaran``.
                self._materializar_fila_in_session(session, int(nuevo_id))
                creadas.append(int(nuevo_id))

            if creadas:
                self._recalcular_total_in_session(session, valuation_id)
            session.commit()
            return creadas

    # ------------------------------------------------------------------ #
    # F-065 fase 3 · dividir una fila (R30–R34), modelo M1 sin DDL.
    # ------------------------------------------------------------------ #
    #: (R31, design §5.4) Lo que cada parte k ≥ 2 copia tal cual de la original.
    _COPIADAS_AL_DIVIDIR = (
        "valuation_id", "precio_unitario_contrato_db", "precio_unitario_final",
        "unidad_albaran", "unidad_contrato", "unidad_categoria",
        "unidad_category_match", "factor_conversion", "codigo_partida_albaran",
        "match_confidence_pct", "match_method", "descuento_albaran_aplicado",
        "codigo_externo", "producto_sigrid",
    )

    def dividir_linea(
        self,
        *,
        document_id: str,
        valuation_line_id: int,
        partes: list[ParteDivision],
    ) -> DivisionHecha | None:
        """(F-065 R30–R34) Divide una fila en ``partes`` (la 1 se la queda la
        original). ``None`` si la fila no es del documento (404).

        - 409 (excepciones de ``_exigir_editable``): alta bloqueante, albarán
          aprobado o fila guardada.
        - 422 (``RepartoInvalido``, sin cambios): fila sintética, sin línea de
          contrato ni derivada, con la marca «revisa la cantidad» (la Q no es
          de fiar: se resuelve antes, como una Q nula), y lo que rechaza
          ``repartir``.
        - Cada parte k ≥ 2 nace ``reparto``, sin blanca propia y colgando de la
          de la original (``parent_merge_line_id``), con los campos de
          ``_COPIADAS_AL_DIVIDIR``, su descripción (la de la original, el
          concepto de su blanca o el de su línea; ``fila_a_guardar``, F-078 R15), sus
          cantidades e importe (``repartir``), sin revisión y desbloqueada.
        - Origen (R32, la regla de editar): con la partida de la original, la
          de su línea de contrato o vacía (almacén), conserva origen y vínculo;
          con otra, una Contrato pasa a Nueva con derivada ``manual_override``
          propia. Las partes de una Nueva llevan SIEMPRE derivada propia (una
          derivada compartida se editaría in situ desde dos filas).
        - Una transacción: partes, derivadas, original y total, o nada.
        """
        self.initialize()
        with self._session_factory.create_session() as session:
            # F-053 R26 (alta), F-065 R4 (aprobado) y R14 (fila guardada).
            self._exigir_editable(session, document_id, valuation_line_id)
            row = session.execute(
                text(
                    "SELECT lv.valuation_id, lv.merge_line_id, "
                    "       lv.parent_merge_line_id, lv.line_kind, "
                    "       lv.matched_contrato_line_id, "
                    "       lv.derived_contrato_line_id, "
                    "       lv.cantidad_albaran, lv.cantidad_convertida, "
                    "       lv.importe_calculado, lv.precio_unitario_final, "
                    "       lv.precio_unitario_source, lv.precio_unitario_agreement, "
                    "       lv.unidad_contrato, lv.unidad_albaran, "
                    "       lv.factor_conversion, lv.descuento_albaran_aplicado, "
                    "       lv.codigo_partida_final, lv.partida_action, "
                    "       lv.descripcion_linea, lv.review_reasons_json, "
                    "       v.document_id, v.contrato_codigo "
                    "FROM albaran_line_valuations lv "
                    "JOIN albaran_valuations v ON v.id = lv.valuation_id "
                    "WHERE lv.id = :vid"
                ),
                {"vid": valuation_line_id},
            ).mappings().first()
            if row is None or row["document_id"] != document_id:
                return None
            if row["line_kind"] == "synthetic_modifier":
                raise RepartoInvalido(
                    "Una línea sintética (portes, incrementos…) no se divide: "
                    "la genera la valoración."
                )
            matched_id = row["matched_contrato_line_id"]
            derived_id = row["derived_contrato_line_id"]
            if matched_id is None and derived_id is None:
                raise RepartoInvalido(
                    "La línea no tiene línea de contrato ni es Nueva: "
                    "revalora antes de dividirla."
                )
            if MOTIVO_UNIDAD_CAMBIADA in motivos_de_json(row["review_reasons_json"]):
                raise RepartoInvalido(
                    "Antes de dividir, revisa la cantidad: cambió la unidad "
                    "(corrígela o guarda la fila)."
                )

            es_contrato = matched_id is not None
            casada = session.execute(
                text(
                    "SELECT codigo_partida, descripcion_linea, unidad_medida, "
                    "       precio_unitario, codigo_contrato, codigo_producto "
                    + (
                        "FROM albaran_contrato_lines_merge" if es_contrato
                        else "FROM contrato_lines_derived"
                    )
                    + " WHERE id = :id"
                ),
                {"id": matched_id if es_contrato else derived_id},
            ).mappings().first() or {}
            padre = (
                row["merge_line_id"] if row["merge_line_id"] is not None
                else row["parent_merge_line_id"]
            )
            concepto = session.execute(
                text("SELECT concepto FROM albaran_lines_merge WHERE id = :id"),
                {"id": padre},
            ).scalar() if padre is not None else None
            # (F-078 R15) Descripción, precio y unidad de la original: los que se
            # guardan (``fila_a_guardar``: la regla con la que la ficha la enseña;
            # una ``reparto`` no tiene blanca propia). Las partes nacen con ellos.
            vista = fila_a_guardar(
                CamposFila(**{c: row[c] for c in _COLUMNAS_FILA_A_GUARDAR}),
                LineaDeLaFila(
                    es_contrato=es_contrato,
                    descripcion=casada.get("descripcion_linea"),
                    unidad=casada.get("unidad_medida"),
                    precio_unitario=casada.get("precio_unitario"),
                ) if casada else None,
                concepto if row["merge_line_id"] is not None else None,
            )
            descripcion = vista.descripcion_linea
            precio = vista.precio_unitario_final
            unidad = vista.unidad_contrato
            q = (
                row["cantidad_convertida"] if row["cantidad_convertida"] is not None
                else row["cantidad_albaran"]
            )
            calculadas = repartir(
                q=q,
                ca0=row["cantidad_albaran"],
                importe0=row["importe_calculado"],
                precio=precio,
                descuento=_sanear_descuento(row["descuento_albaran_aplicado"]),
                partes=[parte.cantidad for parte in partes],
            )

            partida_actual = (row["codigo_partida_final"] or "").strip() or None
            now = self._utc_iso()

            def _pasa_a_nueva(partida: str | None) -> bool:
                return partida != partida_actual and cambia_origen(
                    es_contrato=es_contrato,
                    partida_casada=casada.get("codigo_partida"),
                    cambios={"codigo_partida": partida},
                )

            def _derivada(partida: str | None) -> int:
                """Derivada ``manual_override`` con los valores de la fila."""
                return int(session.execute(
                    text(
                        "INSERT INTO contrato_lines_derived ("
                        "  created_by_valuation_id, source_document_id, "
                        "  codigo_contrato, codigo_producto, "
                        "  descripcion_linea, unidad_medida, "
                        "  precio_unitario, codigo_partida, "
                        "  origen, created_at_utc) "
                        "VALUES (:vid, :doc, :cod, :prod, :desc, :uni, :pu, "
                        "  :part, 'manual_override', :now) "
                        "RETURNING id"
                    ),
                    {
                        "vid": row["valuation_id"],
                        "doc": document_id,
                        "cod": (
                            row["contrato_codigo"] or "" if es_contrato
                            else casada.get("codigo_contrato")
                        ),
                        "prod": None if es_contrato else casada.get("codigo_producto"),
                        "desc": descripcion,
                        "uni": unidad,
                        "pu": precio,
                        "part": partida,
                        "now": now,
                    },
                ).scalar_one())

            derivadas: list[int] = []

            # ---- parte 1: la original ----
            primera, calc = partes[0], calculadas[0]
            params: dict[str, Any] = {
                "vid": valuation_line_id,
                "ca": calc.cantidad_albaran,
                "cc": calc.cantidad_convertida,
                "imp": calc.importe,
                "part": primera.codigo_partida,
                "almacen": ACCION_ALMACEN_ELEGIDO,
            }
            # (F-078 R15) La original queda con su descripción (también si pasa
            # a Nueva: la que se veía, R12).
            params["desc"] = descripcion
            sets = [
                "cantidad_albaran = :ca", "cantidad_convertida = :cc",
                "importe_calculado = :imp", "importe_source = 'calculated'",
                "descripcion_linea = :desc",
            ]
            if primera.codigo_partida != partida_actual:
                sets.append("codigo_partida_final = :part")
                if primera.codigo_partida is None:
                    sets.append("partida_action = :almacen")
                if _pasa_a_nueva(primera.codigo_partida):
                    params["did"] = _derivada(primera.codigo_partida)
                    derivadas.append(params["did"])
                    sets += [
                        "matched_contrato_line_id = NULL",
                        "derived_contrato_line_id = :did",
                        "precio_unitario_source = 'manual_derived'",
                        "precio_unitario_agreement = 'manual'",
                    ]
                elif not es_contrato:
                    # NUEVA: su partida vive también en su derivada.
                    session.execute(
                        text(
                            "UPDATE contrato_lines_derived SET codigo_partida = :part "
                            "WHERE id = :did"
                        ),
                        {"part": primera.codigo_partida, "did": derived_id},
                    )
            session.execute(
                text(
                    "UPDATE albaran_line_valuations SET " + ", ".join(sets)
                    + " WHERE id = :vid"
                ),
                params,
            )
            # (F-078 R16) Antes de copiarla: las partes heredan sus unidades.
            self._materializar_fila_in_session(session, valuation_line_id)

            # ---- partes 2..N: filas «reparto» ----
            copiadas = dict(session.execute(
                text(
                    f"SELECT {', '.join(self._COPIADAS_AL_DIVIDIR)} "  # noqa: S608
                    "FROM albaran_line_valuations WHERE id = :vid"
                ),
                {"vid": valuation_line_id},
            ).mappings().one())
            creadas: list[int] = []
            for parte, calc in zip(partes[1:], calculadas[1:]):
                nueva = not es_contrato or _pasa_a_nueva(parte.codigo_partida)
                did = _derivada(parte.codigo_partida) if nueva else None
                if did is not None:
                    derivadas.append(did)
                valores = {
                    **copiadas,
                    "merge_line_id": None,
                    "matched_contrato_line_id": None if nueva else matched_id,
                    "derived_contrato_line_id": did,
                    "precio_unitario_source": (
                        "manual_derived" if nueva else row["precio_unitario_source"]
                    ),
                    "precio_unitario_agreement": (
                        "manual" if nueva else row["precio_unitario_agreement"]
                    ),
                    "cantidad_albaran": calc.cantidad_albaran,
                    "cantidad_convertida": calc.cantidad_convertida,
                    "importe_calculado": calc.importe,
                    "importe_source": "calculated",
                    "codigo_partida_final": parte.codigo_partida,
                    "partida_action": (
                        ACCION_ALMACEN_ELEGIDO if parte.codigo_partida is None
                        else row["partida_action"]
                    ),
                    "descripcion_linea": descripcion,
                    "line_kind": "reparto",
                    "parent_merge_line_id": padre,
                    "review_required": False,
                    "review_reasons_json": None,
                    "bloqueada": False,
                    "created_at_utc": now,
                }
                creadas.append(int(session.execute(
                    text(
                        f"INSERT INTO albaran_line_valuations ({', '.join(valores)}) "  # noqa: S608
                        f"VALUES ({', '.join(':' + c for c in valores)}) RETURNING id"
                    ),
                    valores,
                ).scalar_one()))
                self._materializar_fila_in_session(session, creadas[-1])

            self._recalcular_total_in_session(session, row["valuation_id"])
            session.commit()
            return DivisionHecha(partes=creadas, derivadas=derivadas)

    # ------------------------------------------------------------------ #
    # Vaciar papelera (jul 2026): ids de los borrados, para purgarlos
    # uno a uno reutilizando hard_delete_document (y su limpieza de
    # dedup vía orquestador, que gestiona la ruta web por documento).
    # ------------------------------------------------------------------ #
    def list_trash_document_ids(self) -> list[str]:
        self.initialize()
        with self._session_factory.create_session() as session:
            rows = session.execute(
                text(
                    "SELECT id FROM albaran_documents_merge "
                    "WHERE is_active = FALSE "
                    "ORDER BY deleted_at_utc NULLS LAST, id"
                )
            ).all()
            return [str(r[0]) for r in rows]

    # ------------------------------------------------------------------ #
    # DESHACER (jul 2026, patrón portado de partes-front)
    #
    # Historial persistente en ``undo_log`` (misma forma que en partes:
    # id/created_at_utc/action/description/payload/undone/actor). El
    # payload guarda snapshots del estado ANTERIOR:
    #   - restore:        filas a RESTAURAR (UPDATE de todas sus columnas)
    #   - reinsert:       filas que la acción BORRÓ (INSERT de vuelta)
    #   - delete_created: filas que la acción CREÓ (DELETE al deshacer)
    #
    # A diferencia de partes (que registra dentro de la sesión mutadora),
    # aquí los snapshots se toman ANTES y el registro DESPUÉS de la
    # mutación, desde el servicio (review_service): así no se toca la
    # lógica interna de los métodos mutadores. No es atómico con la
    # mutación: si el registro falla, la acción queda hecha sin entrada
    # de deshacer (aceptable para una herramienta monousuario).
    #
    # Solo se tocan tablas de la whitelist y con identificadores
    # validados, para que un payload corrupto no pueda inyectar SQL.
    # ------------------------------------------------------------------ #
    _UNDO_TABLES: frozenset = frozenset({
        "albaran_line_valuations",
        "albaran_valuations",
        "albaran_documents_merge",
        "contrato_lines_derived",
    })
    _UNDO_IDENT_RE = re.compile(r"^[a-z_][a-z0-9_]*$")
    _UNDO_LIMIT = 15

    def _ensure_undo_table(self, session: Any) -> None:
        if getattr(self, "_undo_table_ready", False):
            return
        session.execute(text(
            "CREATE TABLE IF NOT EXISTS undo_log ("
            "  id SERIAL PRIMARY KEY,"
            "  created_at_utc VARCHAR(40) NOT NULL,"
            "  action VARCHAR(40) NOT NULL,"
            "  description TEXT NOT NULL,"
            "  payload TEXT NOT NULL,"
            "  undone BOOLEAN NOT NULL DEFAULT false,"
            "  actor VARCHAR(120)"
            ")"
        ))
        # Alcance POR ALBARÁN (jul 2026): columna nueva. En
        # instalaciones existentes el CREATE de arriba no hace nada,
        # asi que la columna se añade aqui (idempotente en PG).
        session.execute(text(
            "ALTER TABLE undo_log "
            "ADD COLUMN IF NOT EXISTS document_id VARCHAR(64)"
        ))
        session.execute(text(
            "CREATE INDEX IF NOT EXISTS ix_undo_log_doc "
            "ON undo_log (document_id, undone)"
        ))
        self._undo_table_ready = True

    def snapshot_row(self, *, table: str, row_id: Any) -> dict | None:
        """Copia completa de una fila (estado ANTERIOR) para el historial.
        Devuelve None si la fila no existe o la tabla no está permitida."""
        if table not in self._UNDO_TABLES:
            return None
        self.initialize()
        with self._session_factory.create_session() as session:
            row = session.execute(
                text(f"SELECT * FROM {table} WHERE id = :id"),  # noqa: S608
                {"id": row_id},
            ).mappings().first()
            if row is None:
                return None
            return {"table": table, "values": dict(row)}

    def record_undo(
        self,
        *,
        action: str,
        description: str,
        document_id: str | None = None,
        restore: list[dict] | None = None,
        reinsert: list[dict] | None = None,
        delete_created: list[dict] | None = None,
        actor: str | None = None,
    ) -> None:
        """Inserta una entrada de historial (best-effort: nunca revienta
        la operación principal)."""
        try:
            payload = {
                "restore": [s for s in (restore or []) if s],
                "reinsert": [s for s in (reinsert or []) if s],
                "delete_created": list(delete_created or []),
            }
            if not any(payload.values()):
                return
            self.initialize()
            with self._session_factory.create_session() as session:
                self._ensure_undo_table(session)
                session.execute(
                    text(
                        "INSERT INTO undo_log "
                        "  (created_at_utc, action, description, payload, "
                        "   undone, actor, document_id) "
                        "VALUES (:now, :action, :descr, :payload, FALSE, "
                        "        :actor, :doc)"
                    ),
                    {
                        "now": self._utc_iso(),
                        "action": action,
                        "descr": description,
                        "payload": json.dumps(payload, default=str),
                        "actor": actor,
                        "doc": document_id,
                    },
                )
                session.commit()
        except Exception:  # noqa: BLE001 - best-effort
            logger.exception("[undo] no se pudo registrar '%s'", description)

    def list_undo(
        self, *, document_id: str, limit: int = _UNDO_LIMIT,
    ) -> list[dict]:
        """Historial NO deshecho de UN albarán (jul 2026): el widget
        del detalle solo enseña —y por tanto solo deja deshacer— lo
        hecho en ese albarán. Entradas antiguas sin document_id
        (previas a la migración) quedan fuera del widget."""
        self.initialize()
        try:
            with self._session_factory.create_session() as session:
                self._ensure_undo_table(session)
                session.commit()
                rows = session.execute(
                    text(
                        "SELECT id, action, description, created_at_utc "
                        "FROM undo_log WHERE undone = FALSE "
                        "  AND document_id = :doc "
                        "ORDER BY id DESC LIMIT :lim"
                    ),
                    {"doc": document_id, "lim": int(limit)},
                ).mappings().all()
                return [
                    {
                        "id": r["id"],
                        "action": r["action"],
                        "description": r["description"],
                        "created_at": r["created_at_utc"],
                    }
                    for r in rows
                ]
        except Exception:  # noqa: BLE001
            logger.exception("[undo] list falló")
            return []

    def undo_last(self, *, document_id: str) -> dict:
        """Deshace la entrada no-deshecha más reciente DE ESE ALBARÁN
        (jul 2026): borra lo creado, reinserta lo borrado y restaura
        lo modificado. La marca undone."""
        self.initialize()
        with self._session_factory.create_session() as session:
            # F-053 R26 (alta, con el merge bloqueado) y F-065 R4 (aprobado).
            self._exigir_editable(session, document_id)
            self._ensure_undo_table(session)
            row = session.execute(
                text(
                    "SELECT id, description, payload FROM undo_log "
                    "WHERE undone = FALSE AND document_id = :doc "
                    "ORDER BY id DESC LIMIT 1 "
                    "FOR UPDATE"
                ),
                {"doc": document_id},
            ).mappings().first()
            if row is None:
                return {"ok": False, "error": "No hay nada que deshacer."}
            try:
                payload = json.loads(row["payload"])
            except Exception:  # noqa: BLE001
                payload = {}

            try:
                # 1) Borrar lo CREADO por la acción.
                for item in payload.get("delete_created", []):
                    tabla = item.get("table")
                    if tabla not in self._UNDO_TABLES:
                        continue
                    session.execute(
                        text(f"DELETE FROM {tabla} WHERE id = :id"),  # noqa: S608
                        {"id": item.get("id")},
                    )
                # 2) Reinsertar lo BORRADO (si ya existe, se ignora).
                for snap in payload.get("reinsert", []):
                    self._undo_apply_reinsert(session, snap)
                # 3) Restaurar lo MODIFICADO.
                for snap in payload.get("restore", []):
                    self._undo_apply_restore(session, snap)
                session.execute(
                    text("UPDATE undo_log SET undone = TRUE WHERE id = :id"),
                    {"id": row["id"]},
                )
                session.commit()
            except Exception as exc:  # noqa: BLE001
                session.rollback()
                logger.exception("[undo] fallo aplicando id=%s", row["id"])
                return {"ok": False, "error": f"No se pudo deshacer: {exc}"}

            remaining = session.execute(
                text(
                    "SELECT COUNT(*) FROM undo_log "
                    "WHERE undone = FALSE AND document_id = :doc"
                ),
                {"doc": document_id},
            ).scalar_one()
        return {
            "ok": True,
            "description": row["description"],
            "remaining": int(remaining),
        }

    def _undo_cols_ok(self, values: dict) -> dict:
        return {
            k: v for k, v in (values or {}).items()
            if self._UNDO_IDENT_RE.match(str(k))
        }

    def _undo_apply_restore(self, session: Any, snap: dict) -> None:
        tabla = snap.get("table")
        values = self._undo_cols_ok(snap.get("values") or {})
        if tabla not in self._UNDO_TABLES or "id" not in values:
            return
        sets = ", ".join(
            f"{col} = :{col}" for col in values.keys() if col != "id"
        )
        if not sets:
            return
        session.execute(
            text(f"UPDATE {tabla} SET {sets} WHERE id = :id"),  # noqa: S608
            values,
        )

    def _undo_apply_reinsert(self, session: Any, snap: dict) -> None:
        tabla = snap.get("table")
        values = self._undo_cols_ok(snap.get("values") or {})
        if tabla not in self._UNDO_TABLES or "id" not in values:
            return
        existe = session.execute(
            text(f"SELECT 1 FROM {tabla} WHERE id = :id"),  # noqa: S608
            {"id": values["id"]},
        ).first()
        if existe:
            return
        cols = ", ".join(values.keys())
        marks = ", ".join(f":{c}" for c in values.keys())
        session.execute(
            text(f"INSERT INTO {tabla} ({cols}) VALUES ({marks})"),  # noqa: S608
            values,
        )
        # Realinear la secuencia del SERIAL para que futuros INSERT no
        # choquen con el id reinsertado. pg_get_serial_sequence devuelve
        # NULL (sin error) si el id no es SERIAL (p. ej. uuid): se omite.
        seq = session.execute(
            text("SELECT pg_get_serial_sequence(:t, 'id')"),
            {"t": tabla},
        ).scalar()
        if seq:
            session.execute(
                text(
                    "SELECT setval(:s, "
                    "  (SELECT COALESCE(MAX(id), 1) FROM " + tabla + "), "
                    "  true)"
                ),
                {"s": seq},
            )

    def doc_label(self, *, document_id: str) -> str:
        """Etiqueta corta para las descripciones del historial."""
        try:
            self.initialize()
            with self._session_factory.create_session() as session:
                num = session.execute(
                    text(
                        "SELECT numero_albaran FROM albaran_documents_merge "
                        "WHERE id = :id"
                    ),
                    {"id": document_id},
                ).scalar()
            return f"alb {num}" if num else f"alb {document_id[:8]}"
        except Exception:  # noqa: BLE001
            return f"alb {document_id[:8]}"

    def valuation_header_id(self, *, document_id: str) -> str | None:
        try:
            self.initialize()
            with self._session_factory.create_session() as session:
                return session.execute(
                    text(
                        "SELECT id FROM albaran_valuations "
                        "WHERE document_id = :doc"
                    ),
                    {"doc": document_id},
                ).scalar()
        except Exception:  # noqa: BLE001
            return None

    def line_brief(self, *, valuation_line_id: int) -> dict | None:
        """Partida/descr/derivada de una línea, para descripciones y
        snapshots del historial."""
        try:
            self.initialize()
            with self._session_factory.create_session() as session:
                r = session.execute(
                    text(
                        "SELECT id, codigo_partida_final, descripcion_linea, "
                        "       derived_contrato_line_id, valuation_id "
                        "FROM albaran_line_valuations WHERE id = :id"
                    ),
                    {"id": valuation_line_id},
                ).mappings().first()
                return dict(r) if r else None
        except Exception:  # noqa: BLE001
            return None

    def latest_valuation_line_for_merge(
        self, *, merge_line_id: int
    ) -> dict | None:
        """La línea de valoración más reciente de una línea blanca (para
        capturar la recién creada por add_conciliacion_for_merge_line)."""
        try:
            self.initialize()
            with self._session_factory.create_session() as session:
                r = session.execute(
                    text(
                        "SELECT id, derived_contrato_line_id "
                        "FROM albaran_line_valuations "
                        "WHERE merge_line_id = :m ORDER BY id DESC LIMIT 1"
                    ),
                    {"m": merge_line_id},
                ).mappings().first()
                return dict(r) if r else None
        except Exception:  # noqa: BLE001
            return None


    @staticmethod
    def _pie_del_merge(merge_doc: AlbaranDocumentMergeOrm) -> dict[str, float | None]:
        """(F-075 R23) El pie del merge con un SELECT defensivo: las columnas
        son de sv3 y sv4 puede salir antes (design §7). Si no existen o la
        consulta falla, todo nulo («no leído»); dentro de un SAVEPOINT para no
        dejar abortada la transacción de la ficha."""
        vacio: dict[str, float | None] = {
            "pie_base": None, "pie_tipo_iva": None, "pie_cuota": None, "pie_total": None,
        }
        sesion = object_session(merge_doc)
        if sesion is None:
            return vacio
        try:
            with sesion.begin_nested():
                fila = sesion.execute(_SQL_PIE_MERGE, {"id": merge_doc.id}).first()
        except Exception:
            logger.info(
                "[ficha] sin columnas del pie todavía (sv3); se pinta «no leído». doc=%s",
                merge_doc.id,
            )
            return vacio
        if fila is None:
            return vacio
        return {
            clave: (None if valor is None else float(valor))
            for clave, valor in zip(vacio, fila)
        }

    def _build_merge_detail(
        self,
        *,
        merge_doc: AlbaranDocumentMergeOrm,
        available_views: list[str],
        provider_snapshots: list[ProviderSnapshot],
        contratos: list[ContratoPayload],
        selected_contrato_codigo: str | None,
        valuation: ValuationPayload | None = None,
        conciliation_by_valuation_line_id: dict[int, ConciliacionDisplay] | None = None,
        contrato_lines: list[ContratoLinePayload] | None = None,
        proveedores: list[ProveedorOption] | None = None,
        obras: list[ObraOption] | None = None,
    ) -> DocumentDetailPayload:
        merge_lines_payload = [
            self._merge_line_to_payload(line) for line in merge_doc.lines
        ]
        display_lines = self._build_display_lines(
            merge_lines=merge_lines_payload,
            valuation=valuation,
            conciliation_by_valuation_line_id=conciliation_by_valuation_line_id or {},
        )
        filas = (
            list(valuation.lines_by_valuation_line_id.values()) if valuation else []
        )
        conc_map = conciliation_by_valuation_line_id or {}
        importes_filas = [f.importe_calculado for f in filas if f.importe_calculado is not None]
        # (F-075 R24) La suma leída es ``importe_albaran`` de comun.
        importe_leido = importe_albaran(m.precio_neto for m in merge_lines_payload)
        n_filas_manuales = sum(
            1 for f in filas
            if es_fila_manual(
                line_kind=f.line_kind,
                bloqueada=f.bloqueada,
                derivada_origen=getattr(conc_map.get(f.valuation_line_id), "derived_origen", None),
                precio_unitario_agreement=f.precio_unitario_agreement,
                partida_action=f.partida_action,
            )
        )
        return DocumentDetailPayload(
            id=merge_doc.id,
            view_mode=VIEW_MODE_MERGE,
            available_views=available_views,
            is_editable=True,
            provider_document_id=None,
            source_document_id=merge_doc.source_document_id,
            document_storage_ref=merge_doc.document_storage_ref,
            source_filename=merge_doc.source_filename,
            provider_origin=merge_doc.provider_origin,
            model_name=merge_doc.model_name,
            proveedor_nombre=merge_doc.proveedor_nombre,
            proveedor_cif=merge_doc.proveedor_cif,
            fecha=merge_doc.fecha,
            numero_albaran=merge_doc.numero_albaran,
            forma_pago=merge_doc.forma_pago,
            obra_codigo=merge_doc.obra_codigo,
            obra_nombre=merge_doc.obra_nombre,
            obra_direccion=merge_doc.obra_direccion,
            document_url=self._document_url(merge_doc),
            confidence_pct_calc=merge_doc.confidence_pct_calc,
            review_required=merge_doc.review_required,
            review_reasons_json=merge_doc.review_reasons_json,
            # F-043 R30 — la clasificación que decidió IA1 viaja tal cual
            # a la ficha. El payload la monta en su `clasificacion`; aquí
            # no se interpreta, ni se completa, ni se corrige.
            tipologia=merge_doc.tipologia,
            tipologia_confianza_pct=merge_doc.tipologia_confianza_pct,
            tipologia_motivo=merge_doc.tipologia_motivo,
            tipologia_origen=merge_doc.tipologia_origen,
            tipologia_mixta=merge_doc.tipologia_mixta,
            tipologia_secundarias_json=merge_doc.tipologia_secundarias_json,
            comparison_summary_json=merge_doc.comparison_summary_json,
            raw_extraction_json=merge_doc.raw_extraction_json,
            ia_output_json=None,
            approved=bool(merge_doc.approved),
            approved_at_utc=merge_doc.approved_at_utc,
            approved_by=merge_doc.approved_by,
            reviewed_at_utc=merge_doc.reviewed_at_utc,
            review_notes=merge_doc.review_notes,
            created_at_utc=merge_doc.created_at_utc,
            lines=merge_lines_payload,
            display_lines=display_lines,
            lineas_con_partida=self._lineas_con_partida(valuation),
            # (F-065 R21, R22)
            # (sin redondear: el aviso redondea la diferencia y pinta 2 decimales)
            suma_filas=sum(importes_filas) if importes_filas else None,
            suma_leida=importe_leido.total,
            n_filas_manuales=n_filas_manuales,
            **self._pie_del_merge(merge_doc),
            provider_snapshots=provider_snapshots,
            contratos=contratos,
            contrato_lines=contrato_lines or [],
            proveedores_disponibles=proveedores or [],
            obras_disponibles=obras or [],
            selected_contrato_codigo=selected_contrato_codigo,
            valuation=valuation,
            busqueda_contratos=estado_busqueda(
                merge_doc.proveedor_cif,
                merge_doc.obra_codigo,
                self._rastro_busqueda(merge_doc),
            ),
        )

    @staticmethod
    def _lineas_con_partida(valuation: ValuationPayload | None) -> int:
        """(F-051 R17) Líneas de la valoración (base, complementarias y
        sintéticas) cuya partida final no está vacía."""
        if valuation is None:
            return 0
        lineas = list(valuation.lines_by_merge_line_id.values()) + list(
            valuation.synthetic_lines
        )
        return contar_con_partida(
            linea.codigo_partida_final for linea in lineas
        )

    @staticmethod
    def _rastro_busqueda(
        merge_doc: AlbaranDocumentMergeOrm,
    ) -> RastroBusquedaContratos:
        """Las cuatro columnas ``contratos_busqueda_*`` (F-052 R20)."""
        return RastroBusquedaContratos(
            cif=merge_doc.contratos_busqueda_cif,
            obra=merge_doc.contratos_busqueda_obra,
            resultado=merge_doc.contratos_busqueda_resultado,
            at_utc=merge_doc.contratos_busqueda_at_utc,
        )

    def _build_provider_detail(
        self,
        *,
        merge_doc: AlbaranDocumentMergeOrm,
        provider_doc: AlbaranDocumentBaseOrm,
        provider_lines: list[AlbaranLineBaseOrm],
        available_views: list[str],
        provider_snapshots: list[ProviderSnapshot],
        view_mode: str,
        contratos: list[ContratoPayload],
        selected_contrato_codigo: str | None,
        valuation: ValuationPayload | None = None,
    ) -> DocumentDetailPayload:
        return DocumentDetailPayload(
            id=merge_doc.id,
            view_mode=view_mode,
            available_views=available_views,
            is_editable=False,
            provider_document_id=provider_doc.id,
            source_document_id=provider_doc.source_document_id
            or merge_doc.source_document_id,
            document_storage_ref=merge_doc.document_storage_ref,
            source_filename=provider_doc.source_filename or merge_doc.source_filename,
            provider_origin=provider_doc.provider_origin,
            model_name=provider_doc.model_name,
            proveedor_nombre=provider_doc.proveedor_nombre,
            proveedor_cif=None,
            fecha=provider_doc.fecha,
            numero_albaran=provider_doc.numero_albaran,
            forma_pago=None,
            obra_codigo=provider_doc.obra_codigo,
            obra_nombre=None,
            obra_direccion=None,
            document_url=self._document_url(merge_doc),
            confidence_pct_calc=None,
            review_required=None,
            review_reasons_json=None,
            # F-043 R30: la clasificación es del MERGE y se enseña ahí.
            # Esta vista es la extracción CRUDA de un proveedor —igual
            # que no trae motivos de revisión ni confianza calculada—, y
            # las seis columnas se quedan a su default `None`.
            comparison_summary_json=None,
            raw_extraction_json=provider_doc.raw_extraction_json,
            ia_output_json=provider_doc.ia_output_json,
            approved=bool(merge_doc.approved),
            approved_at_utc=merge_doc.approved_at_utc,
            approved_by=merge_doc.approved_by,
            reviewed_at_utc=merge_doc.reviewed_at_utc,
            review_notes=merge_doc.review_notes,
            created_at_utc=provider_doc.created_at_utc,
            lines=[self._base_line_to_payload(line) for line in provider_lines],
            provider_snapshots=provider_snapshots,
            contratos=contratos,
            selected_contrato_codigo=selected_contrato_codigo,
            valuation=valuation,
        )

    def get_merge_cif_and_obra(
        self,
        *,
        document_id: str,
    ) -> tuple[str | None, str | None]:
        self.initialize()
        with self._session_factory.create_session() as session:
            document = session.get(AlbaranDocumentMergeOrm, document_id)
            if document is None:
                return None, None
            return document.proveedor_cif, document.obra_codigo

    def merge_existe(self, *, document_id: str) -> bool:
        """¿Existe el merge? ``get_merge_cif_and_obra`` devuelve
        ``(None, None)`` tanto si no existe como si no tiene CIF ni obra."""
        self.initialize()
        with self._session_factory.create_session() as session:
            return session.get(AlbaranDocumentMergeOrm, document_id) is not None

    def sellar_busqueda_contratos(
        self,
        *,
        document_id: str,
        cif: str | None,
        obra: str | None,
        resultado: str,
    ) -> None:
        """Rastro de la última búsqueda de contratos (F-052 R22).

        SOLO para el fallback local de solo-front
        (``LocalContratoRefetchClient``); en producción lo sella sv3,
        dueño de las columnas, con la misma semántica (R21). Rechaza un
        resultado desconocido antes de tocar la BBDD: el bloque de
        contrato decide su mensaje por ese valor.
        """
        if resultado not in RESULTADOS_BUSQUEDA_CONTRATOS:
            raise ValueError(
                f"resultado de búsqueda de contratos desconocido: {resultado!r}"
            )
        self.initialize()
        with self._session_factory.create_session() as session:
            document = session.get(AlbaranDocumentMergeOrm, document_id)
            if document is None:
                raise KeyError(f"Documento no encontrado: {document_id}")
            document.contratos_busqueda_cif = cif
            document.contratos_busqueda_obra = obra
            document.contratos_busqueda_resultado = resultado
            document.contratos_busqueda_at_utc = self._utc_iso()
            session.commit()

    def replace_contratos_and_select(
        self,
        *,
        document_id: str,
        contratos: "list",
    ) -> str | None:
        """Reemplaza los contratos del documento (delete + insert de
        cabecera y líneas) y devuelve el código auto-seleccionado.

        Re-añadido (jun 2026) SOLO para el fallback LOCAL síncrono de
        solo-front (``LocalContratoRefetchClient``): permite asociar
        contratos sin sv3/colas. En producción el dueño de estas tablas
        sigue siendo el sv3 (UPSERT por sigrid_ide); este método NO se
        cablea cuando hay colas.

        Auto-selección:
          * exactamente 1 contrato → ese código.
          * 0 o varios → conserva la selección previa si sigue presente
            en la nueva lista; si no, ``None``.

        El borrado de cada contrato arrastra sus líneas por el
        ``ondelete=CASCADE`` de la FK a nivel de BBDD.
        """
        self.initialize()
        now = self._utc_iso()
        with self._session_factory.create_session() as session:
            document = session.get(AlbaranDocumentMergeOrm, document_id)
            if document is None:
                raise KeyError(f"Documento no encontrado: {document_id}")

            session.execute(
                delete(AlbaranContratoMergeOrm).where(
                    AlbaranContratoMergeOrm.document_id == document_id
                )
            )

            codes: list[str] = []
            for c in contratos:
                contrato_orm = AlbaranContratoMergeOrm(
                    document_id=document_id,
                    codigo_contrato=c.codigo_contrato,
                    nombre_contrato=c.nombre_contrato,
                    fecha_alta_contrato=c.fecha_alta_contrato,
                    fecha_contrato=c.fecha_contrato,
                    vigencia_desde=c.vigencia_desde,
                    vigencia_hasta=c.vigencia_hasta,
                    importe_total=c.importe_total,
                    cif_proveedor=c.cif_proveedor,
                    nombre_proveedor=c.nombre_proveedor,
                    codigo_obra=c.codigo_obra,
                    nombre_obra=c.nombre_obra,
                    gra_rep_ide=c.gra_rep_ide,
                    pdf_sharepoint_relative_path=c.pdf_sharepoint_relative_path,
                    pdf_sharepoint_web_url=c.pdf_sharepoint_web_url,
                    fetched_at_utc=now,
                )
                session.add(contrato_orm)
                session.flush()  # necesitamos contrato_orm.id para las líneas
                codes.append(c.codigo_contrato)

                for ln in (c.lines or []):
                    session.add(
                        AlbaranContratoLineMergeOrm(
                            contrato_id=contrato_orm.id,
                            codigo_contrato=c.codigo_contrato,
                            linea=ln.linea,
                            numero_linea=ln.numero_linea,
                            codigo_producto=ln.codigo_producto,
                            codigo_alternativo=ln.codigo_alternativo,
                            unidad_medida=ln.unidad_medida,
                            descripcion_linea=ln.descripcion_linea,
                            uds=ln.uds,
                            cantidad_servida=ln.cantidad_servida,
                            cantidad_facturada=ln.cantidad_facturada,
                            pendiente_servir=ln.pendiente_servir,
                            precio_unitario=ln.precio_unitario,
                            precio_bruto=ln.precio_bruto,
                            descuentos=ln.descuentos,
                            importe_linea=ln.importe_linea,
                            cuota_iva=ln.cuota_iva,
                            doc_origen=ln.doc_origen,
                            codigo_partida=ln.codigo_partida,
                            descripcion_partida=ln.descripcion_partida,
                            fetched_at_utc=now,
                        )
                    )

            if len(contratos) == 1:
                selected = contratos[0].codigo_contrato
            else:
                prev = document.selected_contrato_codigo
                selected = prev if (prev and prev in codes) else None

            document.selected_contrato_codigo = selected
            document.last_modified_at_utc = now
            session.commit()
            return selected

    # ---------------------------------------------------------------- #
    # NOTA REFACTOR (mayo 2026): se eliminaron de aquí 2 métodos
    # obsoletos del wiring antiguo (PDF de contrato vía sv4):
    #
    #   * get_existing_pdf_paths
    #   * update_contrato_pdf_paths
    #
    # El PDF de contrato es responsabilidad del sv3. ``replace_contratos
    # _and_select`` se RE-AÑADIÓ arriba (jun 2026) solo para el fallback
    # local de solo-front, SIN lógica de PDF.
    # ---------------------------------------------------------------- #

    def update_document(
        self,
        *,
        document_id: str,
        payload: MergeDocumentUpdatePayload,
    ) -> DocumentDetailPayload:
        detail, _ = self.update_document_y_transicion(
            document_id=document_id, payload=payload,
        )
        return detail

    def update_document_y_transicion(
        self,
        *,
        document_id: str,
        payload: MergeDocumentUpdatePayload,
    ) -> tuple[DocumentDetailPayload, bool]:
        """Guarda el documento y dice si PASÓ a aprobado en esta transacción
        (F-053 R1, R2). Con el merge bloqueado: con un alta bloqueante no se
        guarda nada (R25, R26), y si pasa a aprobado sin estar valorado,
        tampoco (R37), comprobado DESPUÉS de aplicar las ediciones de líneas
        del propio guardado («Guardar y aprobar» de una valoración manual)."""
        self.initialize()
        with self._session_factory.create_session() as session:
            # F-053 R26 (alta, con el merge bloqueado) y F-065 R4 (aprobado).
            self._exigir_editable(session, document_id)
            document = session.get(AlbaranDocumentMergeOrm, document_id)
            if document is None:
                raise KeyError(f"Documento no encontrado: {document_id}")
            estaba_aprobado = bool(document.approved)

            document.proveedor_nombre = self._clean_text(payload.proveedor_nombre)
            document.proveedor_cif = self._clean_text(payload.proveedor_cif)
            document.fecha = self._clean_text(payload.fecha)
            document.numero_albaran = self._clean_text(payload.numero_albaran)
            document.forma_pago = self._clean_text(payload.forma_pago)
            # F-070 · R12: obra canónica (``686`` ⇒ ``0686``); lo que no
            # encaja, recortado como hoy.
            document.obra_codigo = canonizar_codigo_obra(
                self._clean_text(payload.obra_codigo),
            )
            document.obra_nombre = self._clean_text(payload.obra_nombre)
            document.obra_direccion = self._clean_text(payload.obra_direccion)
            document.review_notes = self._clean_text(payload.review_notes)
            document.reviewed_at_utc = self._utc_iso()
            document.last_modified_at_utc = self._utc_iso()

            proposed_codigo = self._clean_text(payload.selected_contrato_codigo)
            if proposed_codigo is not None:
                existing_codes = set(
                    session.scalars(
                        select(AlbaranContratoMergeOrm.codigo_contrato).where(
                            AlbaranContratoMergeOrm.document_id == document.id
                        )
                    ).all()
                )
                if proposed_codigo not in existing_codes:
                    # Contrato COMPARTIDO: la cabecera de contrato es unica
                    # por sigrid_ide y su document_id se sobrescribe con el
                    # del ULTIMO albaran enriquecido (UPSERT en sv3). Un
                    # albaran que comparte el mismo contrato no es "dueno" de
                    # la fila, asi que el filtro por document_id no lo
                    # encuentra y antes borrabamos la seleccion a None -> el
                    # boton Valorar daba 409 "no tiene contrato seleccionado".
                    # Aceptamos el codigo si existe como contrato en
                    # albaran_contratos_merge (misma recuperacion por codigo
                    # que el detalle).
                    shared = session.scalar(
                        select(AlbaranContratoMergeOrm.codigo_contrato)
                        .where(
                            AlbaranContratoMergeOrm.codigo_contrato
                            == proposed_codigo
                        )
                        .limit(1)
                    )
                    if shared is None:
                        proposed_codigo = None
            document.selected_contrato_codigo = proposed_codigo

            # (F-065 R3) El PUT nunca desaprueba: sin ``approved`` deja la
            # aprobación como está (desaprobar es su propia acción).
            if payload.approved:
                document.approved = True
                document.approved_at_utc = self._utc_iso()
                document.approved_by = self._clean_text(payload.approved_by)

            # (F-065 R1) Guardar la cabecera solo guarda la cabecera: ni las
            # blancas (``payload.lines``) ni las filas
            # (``payload.valuation_line_updates``) se tocan, y no se recalcula
            # nada. Las filas se editan con su PATCH (lo que cambia el
            # administrativo manda, R11). Antes este bloque reescribía las
            # blancas y ``_recalc_valuation_importes`` devolvía las filas a la
            # cantidad leída (METALFIRE: 23 puertas en vez de 18).

            # (F-036 R24) El guardado es el ÚNICO momento en que el CIF
            # del proveedor puede haber cambiado, así que es aquí donde
            # caducan los motivos que llevan un CIF sellado dentro.
            self._depurar_motivos_documento_in_session(
                session=session,
                document_id=document.id,
                cif_actual=document.proveedor_cif,
            )

            # (F-053 R37) No se aprueba lo no valorado: la sesión se cierra
            # sin confirmar y no cambia nada.
            paso_a_aprobado = bool(payload.approved) and not estaba_aprobado
            if paso_a_aprobado and not self._valorado_in_session(session, document.id):
                raise AlbaranSinValorarError(document_id)
            # (F-065 R20) Ni con filas sin cantidad o importe.
            if paso_a_aprobado:
                self._exigir_lineas_completas(session, document.id)

            session.commit()

        detail = self.get_document_detail(document_id)
        if detail is None:
            raise KeyError(f"Documento no encontrado tras guardar: {document_id}")
        return detail, paso_a_aprobado

    @staticmethod
    def _cif_normalizado(cif: str | None) -> str:
        """CIF comparable: sin espacios, sin guiones/puntos, en mayúsculas.

        Lo teclea un humano en un formulario libre, y el que sella sv3
        viene del contrato. `b-12345678` y `B12345678` son el mismo.
        """
        if cif is None:
            return ""
        return re.sub(r"[^0-9A-Z]", "", str(cif).upper())

    def _depurar_motivos_documento_in_session(
        self,
        *,
        session: Any,
        document_id: str,
        cif_actual: str | None,
    ) -> None:
        """Retira los ``proveedor_cif_no_casa:<cif>`` que ya no aplican.

        F-036 R24. sv3 sella el motivo con el CIF DENTRO
        (``proveedor_cif_no_casa:B12345678``). Cuando el revisor corrige
        el CIF del proveedor, el motivo se queda ahí describiendo un
        problema que ya no existe: en SS-0801977 seguía colgado meses
        después. Como el CIF viejo va sellado en el propio texto, se
        puede saber si el aviso sigue vigente sin preguntarle a nadie.

        ACOTADO a ``proveedor_cif_no_casa`` (decisión del humano,
        2026-08-22): los demás motivos de sv3 se revisan en ficha
        aparte. Un motivo SIN CIF sellado no se toca — no hay con qué
        compararlo, y retirarlo sería inventarse que ha caducado.
        """
        prefijo = "proveedor_cif_no_casa:"
        try:
            with session.begin_nested():
                fila = session.execute(
                    text(
                        "SELECT review_reasons_json "
                        "FROM albaran_documents_merge WHERE id = :id"
                    ),
                    {"id": document_id},
                ).mappings().first()
                if fila is None:
                    return
                motivos = motivos_de_json(fila["review_reasons_json"])
                if not motivos:
                    return

                actual = self._cif_normalizado(cif_actual)
                vigentes = [
                    motivo
                    for motivo in motivos
                    if not motivo.startswith(prefijo)
                    or self._cif_normalizado(motivo[len(prefijo):]) == actual
                ]
                if len(vigentes) == len(motivos):
                    return

                logger.info(
                    "[revision] documento %s: retirados %s motivos "
                    "'%s' cuyo CIF ya no es el del merge.",
                    document_id,
                    len(motivos) - len(vigentes),
                    prefijo.rstrip(":"),
                )
                session.execute(
                    text(
                        "UPDATE albaran_documents_merge "
                        "SET review_reasons_json = :motivos WHERE id = :id"
                    ),
                    {
                        "motivos": json.dumps(vigentes, ensure_ascii=False),
                        "id": document_id,
                    },
                )
        except Exception:
            logger.warning(
                "[revision] no se pudieron depurar los motivos del "
                "documento %s. El guardado sigue.",
                document_id,
                exc_info=True,
            )

    # ------------------------------------------------------------------ #
    # F-053 · Alta en Sigrid: cerrojo (R25, R26), valorado (R37) y lectura
    # del alta (R29-R31). sv4 NUNCA escribe ``albaran_altas_sigrid`` (R34).
    # ------------------------------------------------------------------ #
    @staticmethod
    def _existe_tabla_altas(session: Any) -> bool:
        """Sin la tabla (DDL de sv3 sin aplicar) no hay alta: como hoy."""
        return inspect(session.connection()).has_table(TABLA_ALTAS_SIGRID)

    def _exigir_desbloqueado(self, session: Any, document_id: str) -> None:
        """(F-053 R25, R26) Lanza :class:`AlbaranBloqueadoError` si el
        documento tiene un alta bloqueante (``en_curso``, ``incierto`` o
        ``registrado``). Se llama al EMPEZAR la sesión de cada método que
        escribe, antes de tocar nada; el cerrojo dura hasta su ``commit``.

        DOS sentencias a propósito (review fase 1, pasada 3, §7.1; como H4 y
        T40 en sv3): primero ``SELECT ... FOR UPDATE`` del merge, que espera
        a sv9 si está reclamando (``reclamar`` bloquea la misma fila); y
        DESPUÉS, ya con el cerrojo, la lectura del alta. En READ COMMITTED la
        instantánea se toma al empezar cada sentencia: una sola con ``FOR
        UPDATE`` + ``LEFT JOIN`` no vería el ``en_curso`` que sv9 confirma
        mientras se espera, y dejaría editar mientras sv9 graba en Sigrid.
        """
        session.execute(
            select(AlbaranDocumentMergeOrm.id)
            .where(AlbaranDocumentMergeOrm.id == document_id)
            .with_for_update()
        ).first()
        if not self._existe_tabla_altas(session):
            return
        fila = session.execute(
            _SQL_ALTA_DEL_DOCUMENTO, {"id": document_id},
        ).mappings().first()
        if fila is not None and fila["estado"] in ESTADOS_ALTA_BLOQUEANTES:
            logger.info(
                "[alta-sigrid][R25] rechazado: document_id=%s alta=%s cod=%s",
                document_id, fila["estado"], fila["sigrid_cod"],
            )
            raise AlbaranBloqueadoError(
                document_id, str(fila["estado"]), fila["sigrid_cod"],
            )

    def _exigir_editable(
        self, session: Any, document_id: str, valuation_line_id: int | None = None,
    ) -> None:
        """(F-065 R4, R14) Lo que toda escritura de sv4 comprueba al empezar su
        sesión, antes de tocar nada: el alta de F-053 (con el merge bloqueado,
        :meth:`_exigir_desbloqueado`), que el albarán NO esté aprobado
        (:class:`AlbaranAprobadoError`) y, si se escribe una fila, que no esté
        guardada (:class:`LineaBloqueadaError`). Desaprobar es lo único que no
        pasa por aquí: es justo lo que hace editable un aprobado."""
        self._exigir_desbloqueado(session, document_id)
        aprobado = session.execute(
            select(AlbaranDocumentMergeOrm.approved)
            .where(AlbaranDocumentMergeOrm.id == document_id)
        ).scalar()
        if aprobado:
            raise AlbaranAprobadoError(document_id)
        if valuation_line_id is not None:
            self._exigir_linea_desbloqueada(session, document_id, valuation_line_id)

    @staticmethod
    def _exigir_linea_desbloqueada(
        session: Any, document_id: str, valuation_line_id: int,
    ) -> None:
        """(F-065 R14) :class:`LineaBloqueadaError` si la fila del documento
        está guardada. Una fila ajena o que no existe no se rechaza aquí: el
        método que escribe ya la trata como «no es de este albarán»."""
        bloqueada = session.execute(
            _SQL_FILA_BLOQUEADA,
            {"vid": int(valuation_line_id), "doc": document_id},
        ).scalar()
        if bloqueada:
            raise LineaBloqueadaError(document_id, int(valuation_line_id))

    @staticmethod
    def _exigir_lineas_completas(session: Any, document_id: str) -> None:
        """(F-065 R20, P12) :class:`LineasIncompletasError` si alguna fila de
        la tabla de la ficha no tiene cantidad (Q) o importe: sv9 no la daría
        de alta y se perdería en silencio. Las posiciones son las de la tabla
        (``orden_filas_ficha``), que solo pinta las filas con línea de
        contrato o derivada.

        (F-106 R16) Tampoco con filas a registrar que no cuadran
        (``cuadra_linea`` is ``False``): sv9 las dejaría en ``no_admitido``
        (``linea_no_cuadra``). Las no comparables no cuentan; estar en almacén
        no es motivo (si no cuadra, sí: sv9 la rechazaría igual)."""
        merge_line_ids = [
            int(r[0]) for r in session.execute(
                _SQL_BLANCAS_EN_ORDEN, {"doc": document_id},
            ).all()
        ]
        filas = [
            dict(r) for r in session.execute(
                _SQL_FILAS_PARA_APROBAR, {"doc": document_id},
            ).mappings().all()
        ]
        posiciones: list[int] = []
        unidad_cambiada: list[int] = []
        sin_descripcion: list[int] = []
        no_cuadran: list[int] = []
        posicion = 0
        huerfanas = 0
        for fila in orden_filas_ficha(merge_line_ids, filas):
            if (
                fila["matched_contrato_line_id"] is None
                and fila["derived_contrato_line_id"] is None
            ):
                # (O2, humano 2026-10-11) La ficha no la pinta: «revalora».
                huerfanas += 1
                continue
            posicion += 1
            q = (
                fila["cantidad_convertida"]
                if fila["cantidad_convertida"] is not None
                else fila["cantidad_albaran"]
            )
            if q is None or fila["importe_calculado"] is None:
                posiciones.append(posicion)
            if es_linea_a_registrar(fila["importe_calculado"]) and cuadra_linea(
                q, fila["precio_unitario_final"], fila["descuento_albaran_aplicado"],
                fila["importe_calculado"],
            ) is False:
                no_cuadran.append(posicion)
            # (F-078 R17) Sin vincular, a registrar y sin descripción: sv9 no
            # tendría concepto que mandar (``falta_descripcion``).
            if (
                es_linea_a_registrar(fila["importe_calculado"])
                and not es_linea_vinculada(
                    matched_contrato_line_id=fila["matched_contrato_line_id"],
                    derived_contrato_line_id=fila["derived_contrato_line_id"],
                    sigrid_ide=fila["sigrid_ide"],
                    contrato_linea=fila["contrato_linea"],
                    contrato_valoracion=fila["contrato_valoracion"],
                )
                and not (fila["descripcion_linea"] or "").strip()
            ):
                sin_descripcion.append(posicion)
            # (CR3) «Origen ✎» cambió la unidad y nadie ha revisado la cantidad.
            if MOTIVO_UNIDAD_CAMBIADA in motivos_de_json(fila["review_reasons_json"]):
                unidad_cambiada.append(posicion)
        if posiciones or huerfanas or unidad_cambiada or sin_descripcion or no_cuadran:
            raise LineasIncompletasError(
                document_id, posiciones, huerfanas, unidad_cambiada,
                sin_descripcion=sin_descripcion, no_cuadran=no_cuadran,
            )

    @staticmethod
    def _valorado_in_session(session: Any, document_id: str) -> bool:
        """(F-053 R37, R38) «Valorado» con ``ruesma_comun.valoracion``:
        ``ok`` de sv6 o valoración manual completa. Sin tabla de
        valoración o sin valoración: no."""
        if not inspect(session.connection()).has_table("albaran_valuations"):
            return False
        filas = session.execute(
            _SQL_DATOS_VALORACION, {"id": document_id},
        ).mappings().all()
        if not filas:
            return False
        status = filas[0]["status"]
        importes = [
            f["importe_calculado"] for f in filas
            if f["linea_id"] is not None and f["status"] == status
        ]
        return esta_valorado(status, importes)

    def leer_alta_sigrid(self, document_id: str) -> AltaSigridVista | None:
        """(F-053 R29-R31) El alta del documento, o ``None`` si no hay (o
        no existe la tabla). Solo lectura, sin cerrojo."""
        self.initialize()
        with self._session_factory.create_session() as session:
            if not self._existe_tabla_altas(session):
                return None
            fila = session.execute(
                _SQL_ALTA_COMPLETA, {"id": document_id},
            ).mappings().first()
        if fila is None:
            return None
        return AltaSigridVista(
            estado=str(fila["estado"]),
            modo=fila["modo"],
            sigrid_con_ide=fila["sigrid_con_ide"],
            sigrid_cod=fila["sigrid_cod"],
            adjunto_estado=fila["adjunto_estado"],
            motivos=[
                m for m in _json_o(fila["motivos_json"], [], list)
                if isinstance(m, dict)
            ],
            avisos=[
                a for a in _json_o(fila["avisos_json"], [], list)
                if isinstance(a, dict)
            ],
            peticion=_json_o(fila["peticion_json"], None, dict),
            respuesta=_json_o(fila["respuesta_json"], None, dict),
            intentos=int(fila["intentos"] or 0),
            approved_at_utc=fila["approved_at_utc"],
            approved_by=fila["approved_by"],
            ultimo_intento_at_utc=fila["ultimo_intento_at_utc"],
            actualizado_at_utc=fila["actualizado_at_utc"],
        )

    def estado_aprobacion(self, document_id: str) -> dict[str, Any] | None:
        """(F-053 R30) ``approved``, ``approved_at_utc`` e ``is_active`` del
        merge, o ``None`` si no existe. Solo lectura."""
        self.initialize()
        with self._session_factory.create_session() as session:
            document = session.get(AlbaranDocumentMergeOrm, document_id)
            if document is None:
                return None
            return {
                "approved": bool(document.approved),
                "approved_at_utc": document.approved_at_utc,
                "is_active": bool(document.is_active),
            }

    def lineas_producto_sigrid(self, document_id: str) -> list[dict[str, Any]]:
        """(F-053 R40, R43) Por línea valorada del documento: producto
        elegido, importe, casada (con ``sigrid_ide``, contrato y producto de
        la línea de contrato), contrato de la valoración y el
        ``contexto_linea_json`` de su línea del albarán. Solo lectura."""
        self.initialize()
        with self._session_factory.create_session() as session:
            filas = session.execute(
                _SQL_LINEAS_PRODUCTO, {"doc": document_id},
            ).mappings().all()
        # La familia de la línea (``contexto_linea_json``) la interpreta el
        # servicio: este repositorio no decide nada por familia (F-036 R6).
        return [dict(fila) for fila in filas]

    def guardar_producto_sigrid(
        self,
        *,
        document_id: str,
        valuation_line_id: int,
        producto: str | None,
    ) -> str:
        """(F-053 R41) Guarda el producto elegido (``None`` = por defecto) en
        una línea SIN VINCULAR del documento. Devuelve ``guardado``,
        ``linea_ajena`` (no es del documento o no existe) o ``vinculada``
        (manda el ``ctrpro_ide``, R43); en los dos últimos no cambia nada.
        Con el merge bloqueado: con alta bloqueante, ``AlbaranBloqueadoError``
        (R25, R26). Validar que el código es admitido es del servicio."""
        self.initialize()
        with self._session_factory.create_session() as session:
            # F-053 R26 (alta, con el merge bloqueado), F-065 R4 (aprobado) y
            # R14 (fila guardada).
            self._exigir_editable(session, document_id, valuation_line_id)
            fila = session.execute(
                _SQL_LINEA_PRODUCTO, {"lv": valuation_line_id, "doc": document_id},
            ).mappings().first()
            if fila is None:
                return "linea_ajena"
            if es_linea_vinculada(
                matched_contrato_line_id=fila["matched_contrato_line_id"],
                derived_contrato_line_id=fila["derived_contrato_line_id"],
                sigrid_ide=fila["sigrid_ide"],
                contrato_linea=fila["contrato_linea"],
                contrato_valoracion=fila["contrato_valoracion"],
            ):
                return "vinculada"
            session.execute(
                text(
                    "UPDATE albaran_line_valuations SET producto_sigrid = :p "
                    "WHERE id = :lv"
                ),
                {"p": producto, "lv": valuation_line_id},
            )
            session.commit()
            return "guardado"

    def set_approved(
        self,
        *,
        document_id: str,
        approved: bool,
        approved_by: str | None,
    ) -> bool:
        """Aprueba o desaprueba. Devuelve si el documento PASÓ a aprobado en
        esta transacción (F-053 R1, R2): solo entonces se pide el alta.

        Con el merge bloqueado: desaprobar se rechaza con un alta
        bloqueante (R25, R26) y aprobar lo no valorado, también (R37); en
        los dos casos sin cambiar nada."""
        self.initialize()
        with self._session_factory.create_session() as session:
            if approved:
                session.execute(
                    select(AlbaranDocumentMergeOrm.id)
                    .where(AlbaranDocumentMergeOrm.id == document_id)
                    .with_for_update()
                ).first()
            else:
                # F-053 R26: el alta, con el merge bloqueado (dos sentencias).
                self._exigir_desbloqueado(session, document_id)
            document = session.get(AlbaranDocumentMergeOrm, document_id)
            if document is None:
                raise KeyError(f"Documento no encontrado: {document_id}")
            if approved and document.approved:
                # (F-065, O5 de la review) Aprobar un aprobado es un no-op real:
                # no reescribe ni la fecha ni quién lo aprobó.
                return False
            paso_a_aprobado = bool(approved) and not bool(document.approved)
            if paso_a_aprobado and not self._valorado_in_session(session, document_id):
                raise AlbaranSinValorarError(document_id)
            # (F-065 R20) Ni con filas sin cantidad o importe.
            if paso_a_aprobado:
                self._exigir_lineas_completas(session, document_id)
            document.approved = approved
            document.reviewed_at_utc = document.reviewed_at_utc or self._utc_iso()
            document.last_modified_at_utc = self._utc_iso()
            if approved:
                document.approved_at_utc = self._utc_iso()
                document.approved_by = self._clean_text(approved_by)
            else:
                document.approved_at_utc = None
                document.approved_by = None
            session.commit()
            return paso_a_aprobado

    # ------------------------------------------------------------------ #
    # Soft-delete (jun 2026): borrar / restaurar desde la portada.
    #
    # Borrar = is_active=False (el albarán desaparece de la portada y deja
    # de bloquear el dedup en sv3, que prefiltra por is_active). NO se tocan
    # líneas, valoración ni contratos: cuelgan de la cabecera por FK y se
    # ocultan con ella, de modo que restaurar lo deja exactamente como
    # estaba. Reversible y auditable (deleted_at_utc / deleted_by).
    # ------------------------------------------------------------------ #
    def soft_delete_document(
        self,
        *,
        document_id: str,
        deleted_by: str | None,
    ) -> None:
        self.initialize()
        with self._session_factory.create_session() as session:
            # F-053 R26: el alta, con el merge bloqueado (dos sentencias).
            self._exigir_desbloqueado(session, document_id)
            document = session.get(AlbaranDocumentMergeOrm, document_id)
            if document is None:
                raise KeyError(f"Documento no encontrado: {document_id}")
            document.is_active = False
            document.deleted_at_utc = self._utc_iso()
            document.deleted_by = self._clean_text(deleted_by)
            document.last_modified_at_utc = self._utc_iso()
            session.commit()

    def restore_document(self, *, document_id: str) -> None:
        self.initialize()
        with self._session_factory.create_session() as session:
            document = session.get(AlbaranDocumentMergeOrm, document_id)
            if document is None:
                raise KeyError(f"Documento no encontrado: {document_id}")
            document.is_active = True
            document.deleted_at_utc = None
            document.deleted_by = None
            document.last_modified_at_utc = self._utc_iso()
            session.commit()

    # ------------------------------------------------------------------ #
    # Hard-delete (jun 2026): purga DEFINITIVA desde la papelera.
    #
    # Borra físicamente el albarán y TODO lo que cuelga de él. No nos
    # fiamos del ON DELETE CASCADE (existe en las tablas de valoración de
    # sv6 hacia albaran_documents_merge, pero no necesariamente en líneas
    # merge / contratos): borramos EXPLÍCITAMENTE en orden hijos→padres,
    # en una sola transacción y tolerando que alguna tabla no exista
    # (to_regclass), de modo que el orden de despliegue no rompa la purga.
    #
    # Incluye además la tabla cruda por-proveedor (albaran_documents /
    # albaran_lines) por source_sha256, para no dejar rastro. OJO: cruza
    # los schemas de sv3 (cruda/contratos) y sv6 (valoración); es pragmático
    # porque sv4 ya lee esas tablas y comparten BBDD.
    # ------------------------------------------------------------------ #
    def hard_delete_document(self, *, document_id: str) -> str | None:
        self.initialize()
        with self._session_factory.create_session() as session:
            # F-053 R26: el alta, con el merge bloqueado (dos sentencias).
            self._exigir_desbloqueado(session, document_id)
            document = session.get(AlbaranDocumentMergeOrm, document_id)
            if document is None:
                raise KeyError(f"Documento no encontrado: {document_id}")
            source_sha256 = document.source_sha256

            # Plan por document_id (merge), de hijos a padres.
            plan_by_doc: list[tuple[str, str]] = [
                (
                    "contrato_lines_derived",
                    "DELETE FROM contrato_lines_derived "
                    "WHERE source_document_id = :id",
                ),
                (
                    "albaran_line_valuations",
                    "DELETE FROM albaran_line_valuations WHERE valuation_id IN "
                    "(SELECT id FROM albaran_valuations WHERE document_id = :id)",
                ),
                (
                    "albaran_valuations",
                    "DELETE FROM albaran_valuations WHERE document_id = :id",
                ),
                (
                    "albaran_contrato_lines_merge",
                    "DELETE FROM albaran_contrato_lines_merge WHERE contrato_id IN "
                    "(SELECT id FROM albaran_contratos_merge WHERE document_id = :id)",
                ),
                (
                    "albaran_contratos_merge",
                    "DELETE FROM albaran_contratos_merge WHERE document_id = :id",
                ),
                (
                    "albaran_lines_merge",
                    "DELETE FROM albaran_lines_merge WHERE document_id = :id",
                ),
                (
                    "albaran_documents_merge",
                    "DELETE FROM albaran_documents_merge WHERE id = :id",
                ),
            ]
            # Plan de la tabla cruda por-proveedor, por source_sha256.
            plan_by_sha: list[tuple[str, str]] = [
                (
                    "albaran_lines",
                    "DELETE FROM albaran_lines WHERE document_id IN "
                    "(SELECT id FROM albaran_documents WHERE source_sha256 = :sha)",
                ),
                (
                    "albaran_documents",
                    "DELETE FROM albaran_documents WHERE source_sha256 = :sha",
                ),
            ]

            def _table_exists(table: str) -> bool:
                return session.scalar(
                    text("SELECT to_regclass(:qualified)"),
                    {"qualified": f"public.{table}"},
                ) is not None

            for table, sql in plan_by_doc:
                if _table_exists(table):
                    session.execute(text(sql), {"id": document_id})

            if source_sha256:
                for table, sql in plan_by_sha:
                    if _table_exists(table):
                        session.execute(text(sql), {"sha": source_sha256})

            session.commit()
            # Devolvemos el sha del archivo purgado: el endpoint del
            # portal lo reenvía a sv7 en el evento document-purged para
            # que el guard de idempotencia deje de bloquear el mismo PDF.
            return source_sha256

    def build_query_string(
        self,
        *,
        filters: DocumentListFilters,
        overrides: dict[str, Any] | None = None,
    ) -> str:
        payload: dict[str, Any] = filters.model_dump()
        if overrides:
            payload.update(overrides)
        return urlencode(
            {
                key: value
                for key, value in payload.items()
                if value not in (None, "")
            }
        )

    @staticmethod
    def _clean_text(value: str | None) -> str | None:
        if value is None:
            return None
        value = str(value).strip()
        return value or None

    @staticmethod
    def _utc_iso() -> str:
        return datetime.now(timezone.utc).isoformat()

    @staticmethod
    def _num_iguales(a: Any, b: Any) -> bool:
        """Compara dos números tolerando el ruido de coma flotante.

        La comparación vive en ``domain.models.review_models.
        numeros_iguales`` (F-036), importada arriba con el alias
        ``_num_iguales``: ``_conversion_reproducible`` la necesita y no
        puede depender de un método de esta clase. Este método se
        conserva como delegación porque es el nombre con el que lo
        llama el resto del repositorio.
        """
        return _num_iguales(a, b)

    @staticmethod
    def _document_url(document: AlbaranDocumentMergeOrm) -> str | None:
        return (
            document.sharepoint_share_url
            or document.sharepoint_web_url
            or document.document_storage_ref
            or document.sharepoint_relative_path
        )

    # ------------------------------------------------------------------ #
    # Sub-tanda 2D — construcción de display_lines
    #
    # Mezcla líneas del merge (from_albaran) y líneas sintéticas de
    # valoración en una sola lista ordenada:
    #
    #   [base_1, sint_a_de_base_1, sint_b_de_base_1,
    #    base_2, sint_c_de_base_2,
    #    base_3, ...]
    #
    # Criterio: por cada línea del merge (respetando su line_index),
    # emitimos su DisplayLine y justo después las sintéticas cuyo
    # parent_merge_line_id apunte a ella. Las sintéticas huérfanas
    # (parent no encontrado) se emiten al final.
    #
    # Los campos se rellenan priorizando valoración sobre albarán:
    #   - codigo_imputacion   ← codigo_partida_final ?? codigo_imputacion
    #   - cantidad            ← cantidad_convertida ?? cantidad_albaran
    #   - unidad              ← unidad_contrato    ?? unidad_albaran
    #   - precio_unitario     ← precio_unitario_final
    #   - importe             ← importe_calculado  ?? precio_neto
    #
    # Para sintéticas, todos los campos vienen del payload de
    # valoración (no hay merge equivalente).
    # ------------------------------------------------------------------ #
    @staticmethod
    def _build_display_lines(
        *,
        merge_lines: list[MergeLinePayload],
        valuation: ValuationPayload | None,
        conciliation_by_valuation_line_id: dict[int, ConciliacionDisplay] | None = None,
    ) -> list[DisplayLine]:
        val_lines_by_merge = (
            valuation.lines_by_merge_line_id if valuation else {}
        )
        synthetic_all = (
            list(valuation.synthetic_lines) if valuation else []
        )
        conc_map: dict[int, ConciliacionDisplay] = (
            conciliation_by_valuation_line_id or {}
        )

        # Agrupar sintéticas por parent_merge_line_id (int | None).
        synth_by_parent: dict[int | None, list[LineValuationPayload]] = {}
        for syn in synthetic_all:
            key = syn.parent_merge_line_id
            synth_by_parent.setdefault(key, []).append(syn)

        display: list[DisplayLine] = []

        # Avisos tri-estado de la fila salmon: comparan lo DECLARADO en la
        # linea blanca contra la referencia de contrato. None = no hay dato
        # declarado que comparar (sin icono); True = coincide (✓);
        # False = difiere (⚠).
        def _agree_num(declared, expected):
            if declared is None or expected is None:
                return None
            try:
                return abs(float(declared) - float(expected)) < 0.01
            except (TypeError, ValueError):
                return None

        def _agree_txt(declared, expected):
            if declared is None or str(declared).strip() == "":
                return None
            if expected is None or str(expected).strip() == "":
                return None
            return str(declared).strip() == str(expected).strip()

        for idx, line in enumerate(merge_lines, start=1):
            v = val_lines_by_merge.get(line.id) if line.id is not None else None

            # MODELO "la fila salmon nunca modifica la blanca": la linea
            # blanca (from_albaran) muestra SOLO lo leido del albaran (merge).
            # La valoracion/conciliacion (precio del contrato, importe
            # calculado, partida casada) vive en la fila salmon (concilia),
            # NO aqui. Asi conciliar o cambiar la linea de contrato nunca
            # pisa lo leido/escrito por el usuario.
            eff_codimp = line.codigo_imputacion
            # (F-051 R11) Con valoración y partida final vacía la línea
            # está en ALMACÉN: no se pinta la partida que leyó IA1 (la
            # fila blanca del albarán sigue enseñando lo leído).
            if v is not None and estado_partida(v.codigo_partida_final) == "almacen":
                eff_codimp = None
            # La cantidad EDITABLE de la fila salmón vive en la LÍNEA DE
            # VALORACIÓN (cantidad_albaran / cantidad_convertida): es la que
            # el revisor edita y guarda en .../conciliacion/campos. Antes se
            # mostraba line.cantidad (la BLANCA leída por la IA), de modo que
            # editar la cantidad de la salmón no se reflejaba al recargar
            # ("la cantidad no se guarda"). Preferimos la de la valoración
            # cuando existe; si no, la blanca.
            eff_cantidad = line.cantidad
            if v is not None:
                _v_cant = (
                    v.cantidad_convertida
                    if v.cantidad_convertida is not None
                    else v.cantidad_albaran
                )
                if _v_cant is not None:
                    eff_cantidad = _v_cant
            eff_unidad = None
            # Regla general: la fila blanca muestra lo LEÍDO del albarán
            # (line.precio / line.precio_neto). PERO hay albaranes que NO
            # traen precio en sus líneas — el caso típico es el HORMIGÓN:
            # la línea del albarán llega con precio=NULL y precio_neto=NULL
            # porque el precio lo pone el CONTRATO, no el albarán. En ese
            # caso la fila principal salía con precio e importe VACÍOS aun
            # cuando la valoración SÍ los había calculado (el importe entra
            # en el total pero no se veía en la línea base). 
            #
            # Fix (jun 2026): si el albarán no trajo precio/importe en la
            # línea, la fila principal hereda el valor de la valoración
            # (precio_unitario_final / importe_calculado). Esto NO pisa lo
            # leído del albarán cuando sí existe (se mantiene el modelo
            # "la salmon no modifica la blanca"): el fallback solo actúa
            # cuando el dato del albarán es None.
            eff_precio_unit = line.precio
            if eff_precio_unit is None and v is not None:
                eff_precio_unit = v.precio_unitario_final
            eff_importe = line.precio_neto
            if eff_importe is None and v is not None:
                eff_importe = v.importe_calculado

            _conc = (
                conc_map.get(v.valuation_line_id)
                if v is not None and v.valuation_line_id is not None
                else None
            )
            if _conc is not None:
                _exp_imp = (
                    line.cantidad * _conc.unitario_contrato
                    if line.cantidad is not None
                    and _conc.unitario_contrato is not None
                    else None
                )
                # partida: lo imputado en la blanca vs la partida del contrato,
                # por la clave de comun (F-076 R23, R24): ``CI.04.18`` leída
                # frente a ``CI.4.18`` casada es ✓ con nota «Normalizada».
                (
                    _conc.agree_partida,
                    _conc.partida_normalizada_desde,
                ) = coincide_partida(
                    line.codigo_imputacion, _partida_del_contrato(_conc)
                )
                # (F-077 R21, R22) el ⚠ solo aquí, con lectura del albarán y
                # en filas Contrato; las sin blanca (abajo) nunca lo llevan.
                _conc.aviso_partida = aviso_partida_texto(
                    _conc.agree_partida, kind=_conc.kind,
                    leida=line.codigo_imputacion,
                )
                # cantidad: la salmon copia la de la blanca (coincide si hay)
                _conc.agree_cantidad = _agree_num(line.cantidad, line.cantidad)
                # unitario: precio declarado del albaran vs precio de contrato
                _conc.agree_unitario = _agree_num(
                    line.precio, _conc.unitario_contrato,
                )
                # importe: importe declarado vs cantidad x unitario de contrato
                _conc.agree_importe = _agree_num(line.precio_neto, _exp_imp)

            base_dl = DisplayLine(
                line_kind="from_albaran",
                merge_line_id=line.id,
                valuation_line_id=(v.valuation_line_id if v else None),
                line_index=idx,
                codigo_imputacion=eff_codimp,
                concepto=line.concepto,
                cantidad=eff_cantidad,
                unidad=eff_unidad,
                precio_unitario=eff_precio_unit,
                importe=eff_importe,
                descuento=line.descuento,
                codigo=line.codigo,
                confianza_pct=line.confianza_pct,
                is_valued=v is not None,
                parent_merge_line_id=None,
                concilia=_conc,
            )
            display.append(base_dl)

            # Sintéticas que cuelgan de esta base, en el orden del cargador
            # (las de sv6 al final, cada grupo por id: el de
            # ``orden_filas_ficha``); (F-065 R35) las partes de un reparto van
            # así detrás de su original.
            hijas = synth_by_parent.get(line.id, [])
            hijas_dl = [
                AlbaranReviewRepository._synthetic_to_display(
                    syn=syn,
                    line_index=idx,
                    conc_map=conc_map,
                )
                for syn in hijas
            ]
            display.extend(hijas_dl)
            AlbaranReviewRepository._marcar_reparto(
                numero_linea=idx,
                leida=line.cantidad,
                familia=(
                    ([(v, base_dl)] if v is not None else [])
                    + [
                        (syn, dl) for syn, dl in zip(hijas, hijas_dl)
                        if syn.line_kind == "reparto"
                    ]
                ),
            )

        # Sintéticas huérfanas (parent no encontrado). Raro, pero no
        # podemos silenciarlas sin avisar: las colocamos al final.
        orphans: list[LineValuationPayload] = []
        known_parents = {line.id for line in merge_lines if line.id is not None}
        for parent_key, syns in synth_by_parent.items():
            if parent_key is None or parent_key not in known_parents:
                orphans.extend(syns)
        for orphan_idx, syn in enumerate(orphans, start=len(merge_lines) + 1):
            display.append(
                AlbaranReviewRepository._synthetic_to_display(
                    syn=syn,
                    line_index=orphan_idx,
                    conc_map=conc_map,
                )
            )

        return display

    @staticmethod
    def _marcar_reparto(
        *,
        numero_linea: int,
        leida: float | None,
        familia: list[tuple[LineValuationPayload, DisplayLine]],
    ) -> None:
        """(F-065 R35) «Parte k de N» en cada fila de una blanca repartida (la
        original es la 1; las ``reparto``, por id) y, en la primera, el aviso
        mientras la familia no sume lo que dice el albarán. Se compara en la
        unidad del ALBARÁN (``cantidad_albaran``, o la convertida si no hay):
        con conversión (t → kg) la Q de la ficha no es la de la blanca."""
        if not any(v.line_kind == "reparto" for v, _ in familia):
            return
        total = len(familia)
        for k, (_, dl) in enumerate(familia, start=1):
            dl.parte = f"Parte {k} de {total}"
        suma = sum(
            v.cantidad_albaran if v.cantidad_albaran is not None
            else (v.cantidad_convertida or 0.0)
            for v, _ in familia
        )
        familia[0][1].aviso_reparto = aviso_reparto(numero_linea, suma, leida)

    @staticmethod
    def _synthetic_to_display(
        *,
        syn: LineValuationPayload,
        line_index: int,
        conc_map: dict[int, ConciliacionDisplay] | None = None,
    ) -> DisplayLine:
        conc = (
            (conc_map or {}).get(syn.valuation_line_id)
            if syn.valuation_line_id is not None
            else None
        )

        # Avisos tri-estado tambien para las sinteticas (antes solo se
        # calculaban para from_albaran -> en hormigon no salian los ✓/⚠
        # de partida/precio/importe). Para una sintetica la "linea blanca"
        # es su propio valor (no hay merge): se compara contra el contrato
        # de la salmon (conc). None = nada que comparar (sin icono).
        if conc is not None:
            _cant = (
                syn.cantidad_convertida
                if syn.cantidad_convertida is not None
                else syn.cantidad_albaran
            )
            _unit = conc.unitario_contrato
            _exp_imp = (
                _cant * _unit
                if _cant is not None and _unit is not None
                else None
            )

            def _num(d, e):
                if d is None or e is None:
                    return None
                try:
                    return abs(float(d) - float(e)) < 0.01
                except (TypeError, ValueError):
                    return None

            def _txt(d, e):
                if d is None or str(d).strip() == "":
                    return None
                if e is None or str(e).strip() == "":
                    return None
                return str(d).strip() == str(e).strip()

            # (F-076 R23, R24) Sin línea del albarán: la final frente a la
            # casada, por la clave de comun.
            (
                conc.agree_partida,
                conc.partida_normalizada_desde,
            ) = coincide_partida(
                syn.codigo_partida_final, _partida_del_contrato(conc)
            )
            conc.agree_cantidad = _num(_cant, _cant)
            conc.agree_unitario = _num(syn.precio_unitario_final, _unit)
            conc.agree_importe = _num(syn.importe_calculado, _exp_imp)

        return DisplayLine(
            # (F-065 R35) ``manual`` y ``reparto`` se conservan; lo demás sin
            # blanca es una sintética de sv6.
            line_kind=(
                syn.line_kind
                if syn.line_kind in ("manual", "reparto")
                else "synthetic_modifier"
            ),
            merge_line_id=None,
            valuation_line_id=syn.valuation_line_id,
            line_index=line_index,
            codigo_imputacion=syn.codigo_partida_final,
            concepto=syn.descripcion_linea,
            cantidad=(
                syn.cantidad_convertida
                if syn.cantidad_convertida is not None
                else syn.cantidad_albaran
            ),
            unidad=(syn.unidad_contrato or syn.unidad_albaran),
            precio_unitario=syn.precio_unitario_final,
            importe=syn.importe_calculado,
            descuento=None,
            codigo=None,
            confianza_pct=None,
            is_valued=True,
            parent_merge_line_id=syn.parent_merge_line_id,
            concilia=conc,
        )

    def get_contrato_pdf_url(self, document_id: str) -> str | None:
        """Resuelve la URL del PDF del contrato para un documento, por
        consulta DIRECTA a ``albaran_contratos_merge`` (sin pasar por el
        payload ni la deduplicacion del detalle).

        Estrategia robusta frente al hecho de que la fila de contrato es
        unica por ``sigrid_ide`` y su ``document_id`` apunta al ULTIMO
        albaran que la enriquecio:
          1) filas cuyo ``document_id`` es el de este albaran;
          2) si no hay, filas del ``selected_contrato_codigo`` del albaran;
          3) de las candidatas, la primera con ``pdf_sharepoint_web_url``;
             si ninguna lo tiene, se construye desde
             ``pdf_sharepoint_relative_path`` reusando la base del enlace
             del albaran (``document_url``).
        Devuelve ``None`` si no hay ni web_url ni relative_path.
        """
        self.initialize()
        if not self._tables_ready():
            return None
        with self._session_factory.create_session() as session:
            merge_doc = session.get(AlbaranDocumentMergeOrm, document_id)
            if merge_doc is None:
                return None
            albaran_url = getattr(merge_doc, "document_url", None)
            selected = getattr(merge_doc, "selected_contrato_codigo", None)

            filas = session.scalars(
                select(AlbaranContratoMergeOrm)
                .where(AlbaranContratoMergeOrm.document_id == document_id)
            ).all()
            if not filas and selected:
                filas = session.scalars(
                    select(AlbaranContratoMergeOrm)
                    .where(AlbaranContratoMergeOrm.codigo_contrato == selected)
                ).all()
            if not filas:
                return None

            # Preferimos la fila del contrato seleccionado.
            elegido = None
            if selected:
                for f in filas:
                    if f.codigo_contrato == selected and (
                        f.pdf_sharepoint_web_url or f.pdf_sharepoint_relative_path
                    ):
                        elegido = f
                        break
            if elegido is None:
                for f in filas:
                    if f.pdf_sharepoint_web_url or f.pdf_sharepoint_relative_path:
                        elegido = f
                        break
            if elegido is None:
                return None

            if elegido.pdf_sharepoint_web_url:
                return elegido.pdf_sharepoint_web_url
            rel = elegido.pdf_sharepoint_relative_path
            if rel and albaran_url and "/albaranes/" in albaran_url:
                base = albaran_url.split("/albaranes/", 1)[0]
                return base + "/" + quote(rel, safe="/")
            return None

    @staticmethod
    def _contrato_orm_to_payload(item: AlbaranContratoMergeOrm) -> ContratoPayload:
        return ContratoPayload(
            id=item.id,
            codigo_contrato=item.codigo_contrato,
            nombre_contrato=item.nombre_contrato,
            fecha_alta_contrato=item.fecha_alta_contrato,
            fecha_contrato=item.fecha_contrato,
            vigencia_desde=item.vigencia_desde,
            vigencia_hasta=item.vigencia_hasta,
            importe_total=item.importe_total,
            cif_proveedor=item.cif_proveedor,
            nombre_proveedor=item.nombre_proveedor,
            codigo_obra=item.codigo_obra,
            nombre_obra=item.nombre_obra,
            pdf_sharepoint_relative_path=getattr(
                item, "pdf_sharepoint_relative_path", None
            ),
            pdf_sharepoint_web_url=getattr(
                item, "pdf_sharepoint_web_url", None
            ),
        )

    @staticmethod
    def _merge_line_to_payload(line: AlbaranLineMergeOrm) -> MergeLinePayload:
        return MergeLinePayload(
            id=line.id,
            line_index=line.line_index,
            external_line_id=line.external_line_id,
            cabecera_id=line.cabecera_id,
            codigo=line.codigo,
            cantidad=line.cantidad,
            concepto=line.concepto,
            precio=line.precio,
            descuento=line.descuento,
            precio_neto=line.precio_neto,
            codigo_imputacion=line.codigo_imputacion,
            confianza_pct=line.confianza_pct,
            confidence_pct_calc=line.confidence_pct_calc,
            line_match_score=line.line_match_score,
            comparison_status_json=line.comparison_status_json,
            field_scores_json=line.field_scores_json,
        )

    @staticmethod
    def _base_line_to_payload(line: AlbaranLineBaseOrm) -> MergeLinePayload:
        return MergeLinePayload(
            id=line.id,
            line_index=line.line_index,
            external_line_id=line.external_line_id,
            cabecera_id=line.cabecera_id,
            codigo=line.codigo,
            cantidad=line.cantidad,
            concepto=line.concepto,
            precio=line.precio,
            descuento=line.descuento,
            precio_neto=line.precio_neto,
            codigo_imputacion=line.codigo_imputacion,
            confianza_pct=line.confianza_pct,
            confidence_pct_calc=None,
            line_match_score=None,
            comparison_status_json=None,
            field_scores_json=None,
        )

    @staticmethod
    def _to_list_item(
        row: AlbaranDocumentMergeOrm,
        total_valorado: float | None = None,
        contrato_codigo: str | None = None,
        contrato_nombre: str | None = None,
        lines: list[DocumentLineSummary] | None = None,
    ) -> DocumentListItem:
        return DocumentListItem(
            id=row.id,
            source_document_id=row.source_document_id,
            source_filename=row.source_filename,
            proveedor_nombre=row.proveedor_nombre,
            fecha=row.fecha,
            obra_codigo=row.obra_codigo,
            obra_nombre=row.obra_nombre,
            numero_albaran=row.numero_albaran,
            confidence_pct_calc=row.confidence_pct_calc,
            review_required=row.review_required,
            approved=bool(row.approved),
            total_valorado=total_valorado,
            contrato_codigo=contrato_codigo,
            contrato_nombre=contrato_nombre,
            provider_origin=row.provider_origin,
            created_at_utc=row.created_at_utc,
            document_url=AlbaranReviewRepository._document_url(row),
            lines=lines or [],
            review_reasons_json=row.review_reasons_json,
        )

    # ------------------------------------------------------------------ #
    # Navegacion anterior/siguiente (jun 2026).
    #
    # Devuelve los ids del documento ANTERIOR y SIGUIENTE segun EXACTAMENTE
    # el mismo orden + filtros de la bandeja (``_apply_filters`` +
    # ``_apply_sort``), ignorando la paginacion. Asi los botones del detalle
    # recorren el conjunto filtrado completo (cruzando paginas) y casan con
    # lo que el revisor vio en la lista.
    #
    # Carga solo la columna ``id`` del conjunto ordenado (cadenas de 36
    # chars; el volumen de albaranes lo hace trivial) y localiza la posicion
    # del documento actual. ``(None, None)`` si las tablas no estan listas o
    # el documento no pertenece al conjunto filtrado (p. ej. se filtro por
    # algo que el no cumple).
    # ------------------------------------------------------------------ #
    def get_neighbor_ids(
        self,
        *,
        document_id: str,
        filters: DocumentListFilters,
    ) -> tuple[str | None, str | None]:
        self.initialize()
        if not self._tables_ready():
            return (None, None)
        with self._session_factory.create_session() as session:
            stmt = select(AlbaranDocumentMergeOrm.id)
            stmt = self._apply_filters(stmt=stmt, filters=filters)
            stmt = self._apply_sort(stmt=stmt, filters=filters)
            ids = list(session.scalars(stmt).all())
        try:
            pos = ids.index(document_id)
        except ValueError:
            return (None, None)
        prev_id = ids[pos - 1] if pos > 0 else None
        next_id = ids[pos + 1] if pos < len(ids) - 1 else None
        return (prev_id, next_id)

    @staticmethod
    def _apply_filters(*, stmt: Any, filters: DocumentListFilters) -> Any:
        # Soft-delete (jun 2026): por defecto la portada muestra solo los
        # ACTIVOS; la papelera muestra solo los borrados (is_active=false).
        if filters.vista == "papelera":
            stmt = stmt.where(AlbaranDocumentMergeOrm.is_active.is_(False))
        else:
            stmt = stmt.where(AlbaranDocumentMergeOrm.is_active.is_(True))
        if filters.search:
            term = f"%{filters.search.strip()}%"
            stmt = stmt.where(
                or_(
                    AlbaranDocumentMergeOrm.proveedor_nombre.ilike(term),
                    AlbaranDocumentMergeOrm.numero_albaran.ilike(term),
                    AlbaranDocumentMergeOrm.obra_codigo.ilike(term),
                    AlbaranDocumentMergeOrm.obra_nombre.ilike(term),
                    AlbaranDocumentMergeOrm.source_filename.ilike(term),
                    AlbaranDocumentMergeOrm.source_document_id.ilike(term),
                )
            )
        if filters.approved == "approved":
            stmt = stmt.where(AlbaranDocumentMergeOrm.approved.is_(True))
        elif filters.approved == "pending":
            stmt = stmt.where(AlbaranDocumentMergeOrm.approved.is_(False))
        # ---- Filtros por columna (jun 2026) ----
        if filters.proveedor:
            stmt = stmt.where(
                AlbaranDocumentMergeOrm.proveedor_nombre.ilike(
                    f"%{filters.proveedor.strip()}%"
                )
            )
        if filters.fecha:
            stmt = stmt.where(
                AlbaranDocumentMergeOrm.fecha.ilike(f"%{filters.fecha.strip()}%")
            )
        if filters.recepcion:
            # Fecha de recepcion (jul 2026): created_at_utc es ISO UTC
            # ('2026-07-21T09:14:03...'); un ILIKE por prefijo
            # 'AAAA-MM' o 'AAAA-MM-DD' basta. Matiz consciente: la
            # fecha es UTC, asi que recepciones entre las 00:00 y las
            # ~02:00 hora local caen en el dia UTC anterior.
            stmt = stmt.where(
                AlbaranDocumentMergeOrm.created_at_utc.ilike(
                    f"%{filters.recepcion.strip()}%"
                )
            )
        if filters.obra:
            term = f"%{filters.obra.strip()}%"
            stmt = stmt.where(
                or_(
                    AlbaranDocumentMergeOrm.obra_codigo.ilike(term),
                    AlbaranDocumentMergeOrm.obra_nombre.ilike(term),
                )
            )
        # ---- Filtros EXACTOS de las vistas Obra/Proveedor (jul 2026) ----
        if filters.obra_codigo:
            stmt = stmt.where(
                AlbaranDocumentMergeOrm.obra_codigo
                == filters.obra_codigo.strip()
            )
        if filters.proveedor_cif:
            cif_norm = (
                filters.proveedor_cif.strip().upper().replace(" ", "")
            )
            stmt = stmt.where(
                func.upper(
                    func.replace(
                        func.coalesce(
                            AlbaranDocumentMergeOrm.proveedor_cif, ""
                        ),
                        " ",
                        "",
                    )
                )
                == cif_norm
            )
        if filters.albaran:
            stmt = stmt.where(
                AlbaranDocumentMergeOrm.numero_albaran.ilike(
                    f"%{filters.albaran.strip()}%"
                )
            )
        if filters.contrato:
            stmt = stmt.where(
                AlbaranDocumentMergeOrm.selected_contrato_codigo.ilike(
                    f"%{filters.contrato.strip()}%"
                )
            )
        if filters.lineas:
            # Busca en las líneas de valoración (descripción / partida)
            # mediante un EXISTS correlacionado con el documento.
            stmt = stmt.where(
                text(
                    "EXISTS (SELECT 1 FROM albaran_valuations av "
                    "  JOIN albaran_line_valuations alv "
                    "    ON alv.valuation_id = av.id "
                    "  WHERE av.document_id = albaran_documents_merge.id "
                    "    AND (alv.descripcion_linea ILIKE :lineas_term "
                    "      OR alv.codigo_partida_final ILIKE :lineas_term "
                    "      OR alv.codigo_partida_albaran ILIKE :lineas_term))"
                ).bindparams(lineas_term=f"%{filters.lineas.strip()}%")
            )
        if filters.min_importe is not None or filters.max_importe is not None:
            # (F-075 R21) Sobre la cifra de la columna «Importe»: el importe
            # del albarán o, si no trae, el valorado. Los documentos sin
            # ninguno de los dos quedan fuera cuando se aplica este filtro.
            _importe = sql_importe_mostrado("albaran_documents_merge")
            _conds: list[str] = []
            _params: dict[str, Any] = {}
            if filters.min_importe is not None:
                _conds.append(f"{_importe} >= :min_imp")
                _params["min_imp"] = filters.min_importe
            if filters.max_importe is not None:
                _conds.append(f"{_importe} <= :max_imp")
                _params["max_imp"] = filters.max_importe
            stmt = stmt.where(
                text("(" + " AND ".join(_conds) + ")").bindparams(**_params)
            )
        if filters.review_required == "yes":
            stmt = stmt.where(AlbaranDocumentMergeOrm.review_required.is_(True))
        elif filters.review_required == "no":
            stmt = stmt.where(AlbaranDocumentMergeOrm.review_required.is_(False))
        if filters.min_confidence is not None:
            stmt = stmt.where(
                AlbaranDocumentMergeOrm.confidence_pct_calc >= filters.min_confidence
            )
        if filters.max_confidence is not None:
            stmt = stmt.where(
                AlbaranDocumentMergeOrm.confidence_pct_calc <= filters.max_confidence
            )
        return stmt

    @staticmethod
    def _apply_sort(*, stmt: Any, filters: DocumentListFilters) -> Any:
        sort_map = {
            "created_at_utc": AlbaranDocumentMergeOrm.created_at_utc,
            "fecha": AlbaranDocumentMergeOrm.fecha,
            "proveedor_nombre": AlbaranDocumentMergeOrm.proveedor_nombre,
            "obra_codigo": AlbaranDocumentMergeOrm.obra_codigo,
            "numero_albaran": AlbaranDocumentMergeOrm.numero_albaran,
            "confidence_pct_calc": AlbaranDocumentMergeOrm.confidence_pct_calc,
            "approved": AlbaranDocumentMergeOrm.approved,
        }
        column = sort_map.get(filters.sort_by, AlbaranDocumentMergeOrm.confidence_pct_calc)
        if filters.sort_by == "importe":
            # (F-075 R21) La misma cifra de la columna; sin importe, al final.
            column = literal_column(sql_importe_mostrado("albaran_documents_merge"))
        if filters.sort_dir == "desc":
            stmt = stmt.order_by(nullslast(column.desc()))
        else:
            stmt = stmt.order_by(nullslast(column.asc()))
        stmt = stmt.order_by(AlbaranDocumentMergeOrm.created_at_utc.desc())
        return stmt
