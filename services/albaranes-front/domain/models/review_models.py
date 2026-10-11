# domain/models/review_models.py
from __future__ import annotations

import json
import math
from typing import Any, Literal

from urllib.parse import quote

from pydantic import BaseModel, Field, ValidationError, computed_field, field_validator

from ruesma_comun.contratos import (
    MOTIVOS_REVISION_ORIGEN,
    ClasificacionAlbaran,
    OrigenCampo,
    OrigenDatos,
)
from ruesma_comun.contratos.clasificacion import ORIGEN_IA1
from ruesma_comun.contratos.familias import obtener as obtener_familia
from ruesma_comun.contratos.origen_datos import (
    FUENTE_CORREO,
    MOTIVO_CORREO_AMBIGUO,
    MOTIVO_CORREO_CONFIRMA_PAPEL,
    MOTIVO_CORREO_FUERA_DE_LISTA,
    normalizar_codigo,
)
from ruesma_comun.importes import importe_de_linea
from ruesma_comun.valoracion import esta_valorado

from domain.models.alta_sigrid_models import (
    AltaSigridVista,
    ProductoLinea,
    ProductoOpcion,
    etiqueta_estado_alta,
)
from domain.services.almacen import ACCION_ALMACEN_ELEGIDO

VIEW_MODE_MERGE = "merge"
KNOWN_PROVIDER_VIEWS = ("openai", "gemini", "claude")
ALLOWED_VIEW_MODES = (VIEW_MODE_MERGE, *KNOWN_PROVIDER_VIEWS)


def numeros_iguales(a: Any, b: Any) -> bool:
    """Compara dos números tolerando el ruido de coma flotante.

    Se usa para decidir si el recálculo de importes cambia algo de
    verdad (F-019 R24) y para clasificar la conversión de una línea
    (F-036 R1): media unidad de céntimo de margen, muy por debajo de
    cualquier diferencia real y muy por encima del ruido binario de un
    DOUBLE PRECISION.
    """
    if a is None and b is None:
        return True
    if a is None or b is None:
        return False
    try:
        return abs(float(a) - float(b)) < 5e-3
    except (TypeError, ValueError):
        return False


def conversion_reproducible(
    *,
    factor: Any,
    cantidad_albaran: Any,
    cantidad_convertida: Any,
) -> bool:
    """¿Puede sv4 REHACER la conversión de unidad de esta línea?

    F-036 R1, R6, R7 (SALMEDINA, ago 2026) — POR QUÉ EXISTE
    -------------------------------------------------------
    sv6 no siempre convierte multiplicando por un factor. En residuos
    aplica su REGLA DE CONTENEDORES: el albarán declara 6 m³, el
    contrato tarifa CONTENEDORES, y sv6 persiste
    ``cantidad_albaran=6``, ``cantidad_convertida=1``,
    ``factor_conversion=NULL`` (no existe factor entre m³ y UD: es el
    *hard mismatch* de ``unit_converter``). El importe correcto es
    1 × 120 = 120,00 €.

    Cuando sv4 recalculaba al guardar, tiraba esa `cantidad_convertida`
    y multiplicaba por la cantidad CRUDA: 6 × 120 = 720,00 €. Seis veces.

    La pregunta que responde esta función NO es «¿es una línea de
    residuos?» —R6 prohíbe expresamente condicionar nada a
    ``tipo_familia``— sino «¿la cantidad convertida guardada se explica
    como ``factor × cantidad_albaran``?». Si no se explica, es que
    aguas arriba se aplicó una regla de negocio que sv4 no conoce, y el
    dato se conserva en vez de reinventarse.

    Se decide por CONSISTENCIA, no por ``factor is None`` (R7). Hoy
    ``factor is None`` bastaría, porque el *hard mismatch* deja el
    factor a NULL; pero ``unit_converter`` tiene una rama
    ``no_albaran_unit_assumed_same`` que devuelve ``factor=1.0``, y en
    cuanto F-024 haga que se lea la ``unidad_medida`` del albarán, esa
    rama devolvería el ×6. Comparar contra el producto aguanta ese
    cambio.

    Devuelve True solo si los tres valores existen, son numéricos y
    ``cantidad_convertida ≈ factor × cantidad_albaran``.
    """
    if factor is None or cantidad_albaran is None or cantidad_convertida is None:
        return False
    try:
        producto = float(factor) * float(cantidad_albaran)
    except (TypeError, ValueError):
        return False
    return numeros_iguales(cantidad_convertida, producto)


def motivos_de_json(valor: Any) -> list[str]:
    """Lista de motivos a partir de una columna ``review_reasons_json``.

    F-036 R23. Las columnas ``review_reasons_json`` —la del documento
    (sv3) y la de cada línea de valoración (sv6)— guardan una lista JSON
    de textos. sv4 solo las LEE, y no es su dueño: NULL, cadena vacía,
    JSON ilegible o un JSON que no es una lista devuelven `[]` en vez de
    reventar la ficha. Los elementos que no son texto se descartan uno a
    uno, sin tirar los que sí lo son.
    """
    if not valor:
        return []
    try:
        motivos = json.loads(valor)
    except (TypeError, ValueError):
        return []
    if not isinstance(motivos, list):
        return []
    return [motivo for motivo in motivos if isinstance(motivo, str)]


#: Motivos de revisión que sella sv3 cuando la clasificación de IA1 no
#: es de fiar (F-043 R11, R28, R29). sv4 los LEE para pintar el bloque
#: de clasificación como aviso: no recalcula el umbral —que vive en
#: `CLASIFICACION_CONFIANZA_MINIMA_PCT` de sv3, que es quien lo
#: aplica—, porque el mismo número en dos servicios diverge a la
#: primera vez que el humano lo cambie (la trampa de F-023).
MOTIVOS_CLASIFICACION_EN_DUDA = (
    "clasificacion_confianza_baja",
    "clasificacion_mixta",
    "clasificacion_ausente",
)


class DocumentListFilters(BaseModel):
    search: str | None = None
    # Filtros por columna (jun 2026): cada uno filtra su columna.
    proveedor: str | None = None
    fecha: str | None = None
    # Fecha de recepcion (jul 2026): filtra por la fecha de ALTA del
    # documento en el sistema (created_at_utc, ISO UTC) via ILIKE.
    recepcion: str | None = None
    obra: str | None = None
    # Filtros EXACTOS (jul 2026) para las vistas de Obra y de Proveedor:
    # a diferencia de ``obra``/``proveedor`` (ILIKE por texto), estos
    # filtran por igualdad (codigo de obra / CIF normalizado). Viajan
    # ocultos en el formulario y en la paginacion/ordenacion.
    obra_codigo: str | None = None
    proveedor_cif: str | None = None
    albaran: str | None = None
    contrato: str | None = None
    lineas: str | None = None
    min_importe: float | None = None
    max_importe: float | None = None
    approved: str = Field(default="pending")
    review_required: str = Field(default="all")
    min_confidence: float | None = None
    max_confidence: float | None = None
    sort_by: str = Field(default="confidence_pct_calc")
    sort_dir: str = Field(default="asc")
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=25, ge=1, le=100)
    # Soft-delete (jun 2026): "activos" (is_active=true, vista normal) o
    # "papelera" (is_active=false, los borrados, restaurables).
    vista: str = Field(default="activos")

    @field_validator("vista")
    @classmethod
    def validate_vista(cls, value: str) -> str:
        value = (value or "activos").strip().lower()
        return value if value in {"activos", "papelera"} else "activos"

    @field_validator("approved")
    @classmethod
    def validate_approved(cls, value: str) -> str:
        value = (value or "all").strip().lower()
        return value if value in {"all", "approved", "pending"} else "all"

    @field_validator("review_required")
    @classmethod
    def validate_review_required(cls, value: str) -> str:
        value = (value or "all").strip().lower()
        return value if value in {"all", "yes", "no"} else "all"

    @field_validator("sort_by")
    @classmethod
    def validate_sort_by(cls, value: str) -> str:
        allowed = {
            "created_at_utc",
            "fecha",
            "proveedor_nombre",
            "obra_codigo",
            "numero_albaran",
            "confidence_pct_calc",
            "approved",
        }
        value = (value or "confidence_pct_calc").strip()
        return value if value in allowed else "confidence_pct_calc"

    @field_validator("sort_dir")
    @classmethod
    def validate_sort_dir(cls, value: str) -> str:
        value = (value or "asc").strip().lower()
        return value if value in {"asc", "desc"} else "asc"


class DocumentLineSummary(BaseModel):
    """Resumen compacto de una línea de valoración (línea salmón) para la
    vista rápida de la bandeja. Solo lectura — no se edita aquí.
    """

    kind: str = "from_albaran"
    codigo_partida: str | None = None
    concepto: str | None = None
    cantidad: float | None = None
    unidad: str | None = None
    precio_unitario: float | None = None
    importe: float | None = None


class DocumentListItem(BaseModel):
    id: str
    source_document_id: str | None = None
    source_filename: str
    proveedor_nombre: str | None = None
    fecha: str | None = None
    obra_codigo: str | None = None
    obra_nombre: str | None = None
    numero_albaran: str | None = None
    confidence_pct_calc: float | None = None
    review_required: bool | None = None
    approved: bool = False
    total_valorado: float | None = None
    contrato_codigo: str | None = None
    contrato_nombre: str | None = None
    provider_origin: str
    created_at_utc: str
    document_url: str | None = None
    lines: list[DocumentLineSummary] = []
    # F-053 R37: ¿se puede aprobar? (``esta_valorado`` de comun).
    valorado: bool = False
    # F-053 R31: estado del alta en Sigrid (None = sin alta o DESDE vacía).
    alta_estado: str | None = None

    @computed_field  # type: ignore[prop-decorator]
    @property
    def alta_estado_texto(self) -> str | None:
        return etiqueta_estado_alta(self.alta_estado)


class ProviderSnapshot(BaseModel):
    id: str
    provider_origin: str
    model_name: str
    proveedor_nombre: str | None = None
    fecha: str | None = None
    numero_albaran: str | None = None
    obra_codigo: str | None = None
    raw_extraction_json: str | None = None
    ia_output_json: str | None = None


class MergeLinePayload(BaseModel):
    id: int | None = None
    line_index: int | None = None
    external_line_id: str | None = None
    cabecera_id: str | None = None
    codigo: str | None = None
    cantidad: float | None = None
    concepto: str | None = None
    precio: float | None = None
    descuento: float | None = None
    precio_neto: float | None = None
    codigo_imputacion: str | None = None
    confianza_pct: float | None = None
    confidence_pct_calc: float | None = None
    line_match_score: float | None = None
    comparison_status_json: str | None = None
    field_scores_json: str | None = None


class ProveedorOption(BaseModel):
    """Opcion de proveedor para el desplegable de cabecera. Lista de
    proveedores que tienen algun contrato en el proyecto (cif + nombre)."""

    cif: str | None = None
    nombre: str | None = None


class ObraOption(BaseModel):
    """Opcion de obra para el desplegable de cabecera. Lista de obras que
    tienen algun contrato en el proyecto (codigo + nombre)."""

    codigo: str | None = None
    nombre: str | None = None


class ContratoOption(BaseModel):
    """Opcion de contrato para el desplegable de contratos (jun 2026).
    Resultado de buscar EN VIVO en Sigrid por obra (+ cif opcional), igual
    que los desplegables de obra/proveedor."""

    codigo: str | None = None
    nombre: str | None = None
    cif: str | None = None
    nombre_proveedor: str | None = None


class PartidaOption(BaseModel):
    """Partida HOJA del presupuesto de una obra en Sigrid (obrparpar).

    Solo las partidas sin descomposición (sin hijos); nunca capítulos ni
    subcapítulos. ``descripcion_agregada`` es la ruta completa de capítulos
    hasta la partida (capítulo › subcapítulo › … › partida)."""

    codigo: str
    descripcion: str | None = None
    descripcion_agregada: str | None = None


class ContratoPayload(BaseModel):
    id: int
    codigo_contrato: str
    nombre_contrato: str | None = None
    fecha_alta_contrato: int | None = None
    fecha_contrato: int | None = None
    vigencia_desde: int | None = None
    vigencia_hasta: int | None = None
    importe_total: float | None = None
    cif_proveedor: str | None = None
    nombre_proveedor: str | None = None
    codigo_obra: str | None = None
    nombre_obra: str | None = None
    pdf_sharepoint_relative_path: str | None = None
    pdf_sharepoint_web_url: str | None = None


class ContratoLinePayload(BaseModel):
    """Una linea de albaran_contrato_lines_merge del contrato
    seleccionado. Se expone al detalle para poblar el desplegable
    de conciliacion editable (elegir otra linea o derivar nueva)."""
    id: int
    codigo_contrato: str
    codigo_partida: str | None = None
    descripcion: str | None = None
    precio_unitario: float | None = None
    unidad_medida: str | None = None
    codigo_producto: str | None = None


# ====================================================================== #
# Sub-tanda 2D — ValuationLineUpdate
#
# Payload con los campos editables de una línea sintética cuando el
# revisor la toca en la tabla del formulario. Identifica la fila por
# su valuation_line_id (PK de albaran_line_valuations). El servicio 4
# hace UPDATE limitado a estos campos.
#
# Se coloca antes de MergeDocumentUpdatePayload para que éste pueda
# referenciarlo directamente sin forward-reference.
# ====================================================================== #

class ValuationLineUpdate(BaseModel):
    valuation_line_id: int
    codigo_partida_final: str | None = None
    descripcion_linea: str | None = None
    cantidad_albaran: float | None = None
    unidad_contrato: str | None = None
    precio_unitario_final: float | None = None
    importe_calculado: float | None = None


class ConciliacionOverridePayload(BaseModel):
    """Override manual de la conciliacion de UNA linea de valoracion.
    mode='contract_line' apunta a otra linea del contrato;
    mode='nueva' deriva una linea nueva en la partida de la linea."""
    mode: Literal["contract_line", "nueva"]
    matched_contrato_line_id: int | None = None
    descripcion: str | None = None
    precio_unitario: float | None = None


class MergeDocumentUpdatePayload(BaseModel):
    proveedor_nombre: str | None = None
    proveedor_cif: str | None = None
    fecha: str | None = None
    numero_albaran: str | None = None
    forma_pago: str | None = None
    obra_codigo: str | None = None
    obra_nombre: str | None = None
    obra_direccion: str | None = None
    selected_contrato_codigo: str | None = None
    review_notes: str | None = None
    approved: bool = False
    approved_by: str | None = None
    # (F-065 R1) ``lines`` y ``valuation_line_updates`` se ACEPTAN y se
    # IGNORAN: guardar la cabecera no toca las líneas. Siguen en el modelo
    # para que un ``app.js`` en caché (que aún las manda) no reciba un 422.
    lines: list[MergeLinePayload] = Field(default_factory=list)
    valuation_line_updates: list[ValuationLineUpdate] = Field(
        default_factory=list,
    )


# ====================================================================== #
# F-065 · fase 1 — lo editado en las líneas manda.
#
# Q de una fila = ``cantidad_convertida ?? cantidad_albaran``: la que enseña
# y edita la ficha, en la unidad del precio (``importe = precio × Q × (1 −
# dto/100)``). Guardar la cabecera no toca las líneas (R1), un aprobado es de
# solo lectura (R4), una fila guardada queda bloqueada (R13–R15) y no se
# aprueba con filas sin cantidad o importe (R20).
# ====================================================================== #

#: (R4) Aviso de toda escritura sobre un albarán aprobado.
AVISO_ALBARAN_APROBADO = "Albarán aprobado: desapruébalo para editar"

#: (R14) Aviso de toda escritura sobre una fila guardada (bloqueada).
AVISO_LINEA_BLOQUEADA = "Línea guardada: desbloquéala para editarla"


class AlbaranAprobadoError(Exception):
    """(R4) El albarán está aprobado: no se escribe nada hasta desaprobarlo."""

    def __init__(self, document_id: str) -> None:
        self.document_id = document_id
        super().__init__(AVISO_ALBARAN_APROBADO)

    @property
    def aviso(self) -> str:
        return AVISO_ALBARAN_APROBADO


class LineaBloqueadaError(Exception):
    """(R14) La fila está guardada (bloqueada): no se toca hasta desbloquearla."""

    def __init__(self, document_id: str, valuation_line_id: int) -> None:
        self.document_id = document_id
        self.valuation_line_id = valuation_line_id
        super().__init__(AVISO_LINEA_BLOQUEADA)

    @property
    def aviso(self) -> str:
        return AVISO_LINEA_BLOQUEADA


class LineasIncompletasError(Exception):
    """(R20) Hay filas sin cantidad o sin importe: no se aprueba. ``posiciones``
    son las de la tabla de la ficha (1, 2, ...), las que ve el administrativo.

    ``huerfanas`` (decisión del humano del 2026-10-11, O2 de la review de la
    fase 1): filas sin línea de contrato NI derivada. La ficha no las pinta y
    sv9 las mandaría sin vincular: tampoco se aprueba con ellas, y se pide
    revalorar. Una fila en almacén (partida final vacía) NO es ninguna de las
    dos cosas: el almacén nunca impide aprobar.

    ``unidad_cambiada`` (CR3, pasada 3 de la review de la fase 2): posiciones
    de las filas con la marca ``MOTIVO_UNIDAD_CAMBIADA`` («Origen ✎» a otra
    unidad sin poder convertir la cantidad). sv9 la mandaría tal cual (8 ud
    como 8 t): no se aprueba hasta revisar la cantidad."""

    def __init__(
        self,
        document_id: str,
        posiciones: list[int],
        huerfanas: int = 0,
        unidad_cambiada: list[int] | None = None,
    ) -> None:
        self.document_id = document_id
        self.posiciones = list(posiciones)
        self.huerfanas = huerfanas
        self.unidad_cambiada = list(unidad_cambiada or [])
        super().__init__(self.aviso)

    @property
    def aviso(self) -> str:
        partes = []
        if self.posiciones:
            partes.append("Líneas sin cantidad o importe: " + ", ".join(
                str(posicion) for posicion in self.posiciones
            ))
        if self.unidad_cambiada:
            partes.append("Líneas con la unidad cambiada: revisa la cantidad: " + ", ".join(
                str(posicion) for posicion in self.unidad_cambiada
            ))
        if self.huerfanas:
            lineas = "línea" if self.huerfanas == 1 else "líneas"
            partes.append(
                f"Hay {self.huerfanas} {lineas} sin línea de contrato ni Nueva "
                "que la ficha no enseña: revalora el albarán"
            )
        return ". ".join(partes)


def cantidades_tras_editar(
    *,
    q_nueva: float | None,
    cantidad_albaran: float | None,
    cantidad_convertida: float | None,
    factor: float | None,
) -> tuple[float | None, float | None]:
    """(R6, R7) ``(cantidad_albaran, cantidad_convertida)`` tras teclear Q.

    Lo tecleado YA es la convertida (la ficha enseña Q en la unidad del
    precio); lo que se deriva es la del albarán:

    - sin Q nueva (``None``), ninguna cambia (R7);
    - conversión reproducible (``cc = factor × ca``) y ``factor ≠ 0``: la del
      albarán es ``Q / factor`` (a);
    - sin conversión (``cc`` nula y ``factor`` nulo o 1): las dos son Q (b);
    - en otro caso (contenedores de residuos, regla de sv6 que sv4 no sabe
      rehacer, o filas legadas) la del albarán se conserva y la convertida
      es Q (c).
    """
    if q_nueva is None:
        return cantidad_albaran, cantidad_convertida
    if conversion_reproducible(
        factor=factor,
        cantidad_albaran=cantidad_albaran,
        cantidad_convertida=cantidad_convertida,
    ) and float(factor) != 0:
        return q_nueva / float(factor), q_nueva
    if cantidad_convertida is None and (factor is None or float(factor) == 1):
        return q_nueva, q_nueva
    return cantidad_albaran, q_nueva


def cambia_origen(
    *,
    es_contrato: bool,
    partida_casada: str | None,
    cambios: dict[str, Any],
) -> bool:
    """(R25, R26) ¿Pasa la fila Contrato a Nueva con estos cambios?

    ``cambios`` son SOLO los campos que de verdad cambian (ya normalizados: la
    partida sin espacios y vacía = ``None``). Una fila Contrato pasa a Nueva,
    sin confirmación, si cambia la partida a una no vacía distinta de la de su
    línea de contrato, el precio unitario o la unidad. Vaciar la partida
    (almacén) o poner la de su línea de contrato no cambia el origen (F-051 D4,
    R20; P10), ni la descripción, la cantidad, el descuento o el código
    externo. Una fila Nueva sigue Nueva (se edita su derivada). Nunca se llama
    a la IA: el origen solo lo vuelve a decidir «Origen ✎» o revalorar.
    """
    if not es_contrato:
        return False
    partida = cambios.get("codigo_partida")
    return (
        (partida is not None and partida != (partida_casada or "").strip())
        or "precio_unitario" in cambios
        or "unidad" in cambios
    )


#: (F-065 H2) «Origen ✎» llevó la fila a una línea de contrato de OTRA unidad y
#: sv4 no sabe convertir la cantidad: se deja, sin bloquear, y se avisa.
MOTIVO_UNIDAD_CAMBIADA = "front_unidad_cambiada_revisa_cantidad"


def _unidad(valor: str | None) -> str:
    return (valor or "").strip().upper()


def cantidades_tras_reapuntar(
    *,
    unidad_actual: str | None,
    unidad_nueva: str | None,
    unidad_albaran: str | None,
    cantidad_albaran: float | None,
    cantidad_convertida: float | None,
    factor: float | None,
) -> tuple[float | None, float | None, float | None, bool]:
    """(F-065 H2) ``(ca, cc, factor, aviso)`` al reapuntar a una línea de
    contrato con ``unidad_nueva``.

    Q (la convertida) está en la unidad del precio, así que si la unidad cambia
    Q deja de valer. sv4 no tiene el conversor de unidades (es de sv6): solo
    sabe rehacer el caso en que la unidad nueva es la del ALBARÁN, en el que Q
    es la cantidad leída (factor 1). Unidad nueva desconocida o la misma: nada
    cambia. Otra unidad, también si la actual se desconoce (P2-2): se deja la
    cantidad y ``aviso`` (la fila queda marcada para revisar la cantidad, nunca
    bloqueada, y no se aprueba hasta revisarla, CR3).
    """
    nueva = _unidad(unidad_nueva)
    if not nueva or nueva == _unidad(unidad_actual):
        return cantidad_albaran, cantidad_convertida, factor, False
    if nueva == _unidad(unidad_albaran) and cantidad_albaran is not None:
        return cantidad_albaran, cantidad_albaran, 1.0, False
    return cantidad_albaran, cantidad_convertida, factor, True


def motivos_con(valor: Any, motivo: str, presente: bool) -> str:
    """``review_reasons_json`` con ``motivo`` puesto o quitado, sin tocar los
    demás (los de sv6 se conservan; sv4 solo gestiona los suyos)."""
    motivos = [m for m in motivos_de_json(valor) if m != motivo]
    if presente:
        motivos.append(motivo)
    return json.dumps(motivos, ensure_ascii=False)


def descripcion_para_valoracion(
    *,
    descripcion: str | None,
    sin_blanca: bool,
    editada: bool,
    ya_fijada: bool,
) -> str | None:
    """(F-065 CR1, H1) Descripción que guarda la VALORACIÓN de una fila Nueva
    (``albaran_line_valuations.descripcion_linea``), que es la que sv9 manda a
    Sigrid antes que el concepto leído de la blanca.

    - Sin blanca (traída del contrato, «Añadir línea»): siempre la de la fila;
      si no, sv9 no tendría ninguna y el albarán saldría ``no_admitido``.
    - Con blanca: solo si el administrativo la editó (ahora o antes); sin
      editar, ``None`` y sv9 manda lo leído del albarán (diseño de F-053).
    """
    return descripcion if (sin_blanca or editada or ya_fijada) else None


def es_fila_manual(
    *,
    line_kind: str | None,
    bloqueada: bool,
    derivada_origen: str | None,
    precio_unitario_agreement: str | None,
    partida_action: str | None,
) -> bool:
    """(R22) ¿La tocó el administrativo? (definición de requirements): línea
    ``manual`` o ``reparto``, bloqueada, con derivada ``manual_override``,
    con precio fijado a mano o con el almacén elegido. Revalorar la descarta."""
    return (
        line_kind in ("manual", "reparto")
        or bool(bloqueada)
        or derivada_origen == "manual_override"
        or precio_unitario_agreement == "manual"
        or partida_action == ACCION_ALMACEN_ELEGIDO
    )


def orden_filas_ficha(
    merge_line_ids: list[int], filas: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """(R20) Las filas de valoración en el orden en que las pinta la ficha.

    Replica ``_load_valuation_in_session`` (sintéticas al final, el resto por
    ``id``) y ``_build_display_lines`` (cada blanca, en el orden de
    ``merge_line_ids``, con sus sintéticas detrás; después las huérfanas,
    agrupadas por padre en orden de aparición). Cada fila lleva ``id``,
    ``merge_line_id``, ``parent_merge_line_id`` y ``line_kind``.

    El cargador ordena además por ``merge_line_id``; aquí no hace falta: las
    blancas se recorren en el orden de ``merge_line_ids`` y las sintéticas y
    sueltas tienen ``merge_line_id`` nulo (sv6 nunca lo pone en una
    sintética), así que el ``id`` decide lo mismo.
    """

    def _sintetica(fila: dict[str, Any]) -> bool:
        return fila.get("line_kind") == "synthetic_modifier"

    ordenadas = sorted(filas, key=lambda f: (_sintetica(f), f["id"]))
    base: dict[int, dict[str, Any]] = {}
    por_padre: dict[int | None, list[dict[str, Any]]] = {}
    for fila in ordenadas:
        if not _sintetica(fila) and fila.get("merge_line_id") is not None:
            base[fila["merge_line_id"]] = fila
        else:
            por_padre.setdefault(fila.get("parent_merge_line_id"), []).append(fila)
    salida: list[dict[str, Any]] = []
    for merge_line_id in merge_line_ids:
        if merge_line_id in base:
            salida.append(base[merge_line_id])
        salida.extend(por_padre.pop(merge_line_id, []))
    for huerfanas in por_padre.values():
        salida.extend(huerfanas)
    return salida


def _euros(valor: float) -> str:
    entero, _, decimales = f"{valor:,.2f}".partition(".")
    return f"{entero.replace(',', '.')},{decimales} €"


def aviso_suma_importes(
    suma_filas: float | None, suma_leida: float | None,
) -> str | None:
    """(R21) Confirmación antes de aprobar si la suma de las filas difiere en
    0,01 € o más de la de lo leído en el albarán; ``None`` si cuadra o falta
    alguna de las dos. No bloquea: una recepción parcial es legítima."""
    if suma_filas is None or suma_leida is None:
        return None
    if round(abs(suma_filas - suma_leida), 2) < 0.01:
        return None
    return (
        f"La suma de las líneas ({_euros(suma_filas)}) no cuadra con la del "
        f"albarán ({_euros(suma_leida)}). ¿Aprobar igualmente?"
    )


def _numero_es(valor: object) -> object:
    """Número tecleado en la ficha: admite coma decimal (``1.234,5``); vacío
    o «—» es ``None``; uno ilegible o no finito es un error de validación
    (422), nunca un ``None`` silencioso. Lo que no es texto pasa tal cual a
    la validación de Pydantic."""
    if not isinstance(valor, str):
        return valor
    texto = valor.strip()
    if texto in ("", "—"):  # vacío o «—»
        return None
    if "," in texto:
        texto = texto.replace(".", "").replace(",", ".")
    numero = float(texto)
    if not math.isfinite(numero):
        raise ValueError("número no finito")
    return numero


class LineaATraer(BaseModel):
    """(R23) Una línea de contrato a traer, con su cantidad (obligatoria, ≠ 0)."""

    contrato_line_id: int
    cantidad: float

    @field_validator("cantidad", mode="before")
    @classmethod
    def _cantidad(cls, valor: object) -> object:
        return _numero_es(valor)

    @field_validator("cantidad")
    @classmethod
    def _no_cero(cls, valor: float) -> float:
        if valor == 0:
            raise ValueError("la cantidad no puede ser 0")
        return valor


class TraerLineasBody(BaseModel):
    """(R23) Cuerpo de «Traer líneas contrato»: al menos una, cada una con su
    cantidad. El cuerpo viejo (``contrato_line_ids`` sin cantidades) es un 422."""

    lineas: list[LineaATraer] = Field(min_length=1)


# ------------------------------------------------------------------ #
# F-065 fase 3 · dividir una fila (R29–R35), modelo M1 sin DDL
# ------------------------------------------------------------------ #
#: (R30) La suma de las partes puede diferir de Q en menos de media milésima.
TOLERANCIA_REPARTO = 0.005
#: (R29) Entre 2 y 20 partes.
MIN_PARTES, MAX_PARTES = 2, 20


class RepartoInvalido(ValueError):
    """(R30) La división no se hace (422, sin cambios). El mensaje es para el
    administrativo: dice qué parte o qué suma falla."""


class ParteDivision(BaseModel):
    """(R29) Una parte: su cantidad (en la unidad del precio, como la Q de la
    ficha) y su partida (vacía = almacén). Una cantidad nula o 0 se acepta
    aquí y la rechaza ``repartir`` diciendo qué parte es."""

    cantidad: float | None = None
    codigo_partida: str | None = None

    @field_validator("cantidad", mode="before")
    @classmethod
    def _cantidad(cls, valor: object) -> object:
        return _numero_es(valor)

    @field_validator("codigo_partida")
    @classmethod
    def _partida(cls, valor: str | None) -> str | None:
        return (valor or "").strip() or None


class DivisionBody(BaseModel):
    """(R29, R30) Cuerpo de ``POST .../lines/{vid}/dividir``: de 2 a 20 partes."""

    partes: list[ParteDivision] = Field(min_length=MIN_PARTES, max_length=MAX_PARTES)


class ParteCalculada(BaseModel):
    """(R31, R33) Cantidades e importe de una parte."""

    cantidad_convertida: float
    cantidad_albaran: float | None
    importe: float | None


class DivisionHecha(BaseModel):
    """(R34) Lo que creó una división: las filas ``reparto`` (partes 2..N) y
    las derivadas ``manual_override`` nuevas. El «Deshacer» borra las dos."""

    partes: list[int]
    derivadas: list[int]


def _cantidad_es(valor: float) -> str:
    """Una cantidad como la escribe el administrativo: «9,5», «10»."""
    return f"{valor:.3f}".rstrip("0").rstrip(".").replace(".", ",")


def _fuera_de_tolerancia(a: float, b: float) -> bool:
    return round(abs(a - b), 6) >= TOLERANCIA_REPARTO


def repartir(
    *,
    q: float | None,
    ca0: float | None,
    importe0: float | None,
    precio: float | None,
    descuento: float | None,
    partes: list[float | None],
) -> list[ParteCalculada]:
    """(R30, R31, R33) Reparte una fila de cantidad ``q`` (la convertida, o la
    del albarán si no hay) entre ``partes`` (sus cantidades, la 1 es la que se
    queda la original). Pura: no toca nada.

    - Cada parte: ``cantidad_convertida = qk`` y ``cantidad_albaran = ca0 × qk
      / q`` (``None`` si la original no la tiene).
    - Importe: ``round(importe0 × qk / q, 2)`` y la última absorbe el
      redondeo, así la familia suma ``importe0``; sin ``importe0``, la fórmula
      canónica con el precio y el descuento de la original.
    - ``RepartoInvalido`` si ``q`` es nula o 0, no hay de 2 a 20 partes, una es
      nula, 0 o de otro signo que ``q``, o suman ``q`` ± 0,005 o más.
    """
    if q is None or q == 0:
        raise RepartoInvalido("La línea está sin cantidad: no se puede dividir.")
    if not MIN_PARTES <= len(partes) <= MAX_PARTES:
        raise RepartoInvalido(
            f"Se divide en entre {MIN_PARTES} y {MAX_PARTES} líneas "
            f"(llegaron {len(partes)})."
        )
    for numero, cantidad in enumerate(partes, start=1):
        if cantidad is None or cantidad == 0:
            raise RepartoInvalido(f"La parte {numero} no tiene cantidad (o es 0).")
        if (cantidad > 0) != (q > 0):
            raise RepartoInvalido(
                f"La parte {numero} tiene otro signo que la línea ({_cantidad_es(q)})."
            )
    suma = sum(partes)  # type: ignore[arg-type]
    if _fuera_de_tolerancia(suma, q):
        raise RepartoInvalido(
            f"Las partes suman {_cantidad_es(suma)}; la línea tiene {_cantidad_es(q)}."
        )

    if importe0 is None:
        importes = [
            importe_de_linea(cantidad=cantidad, precio_unitario=precio,
                             descuento_pct=descuento)
            for cantidad in partes
        ]
    else:
        importes = [round(importe0 * cantidad / q, 2) for cantidad in partes[:-1]]
        importes.append(round(importe0 - sum(importes), 2))
    return [
        ParteCalculada(
            cantidad_convertida=cantidad,
            cantidad_albaran=None if ca0 is None else ca0 * cantidad / q,
            importe=importe,
        )
        for cantidad, importe in zip(partes, importes)
    ]


def aviso_reparto(numero_linea: int, suma: float | None, leida: float | None) -> str | None:
    """(R35) Aviso no bloqueante mientras las partes de una blanca no sumen lo
    que dice el albarán (comparado en la unidad del albarán); ``None`` si
    cuadra o falta alguna de las dos."""
    if suma is None or leida is None or not _fuera_de_tolerancia(suma, leida):
        return None
    return (
        f"Las partes de la línea {numero_linea} suman {_cantidad_es(suma)}; "
        f"el albarán dice {_cantidad_es(leida)}"
    )


class ConciliacionEditBody(BaseModel):
    """(R8) Cuerpo del PATCH de edición de una fila.

    Un campo AUSENTE no cambia; uno presente a ``null`` (o vacío) se vacía.
    El front manda solo lo que el administrativo cambió; :meth:`campos`
    devuelve exactamente eso (``model_fields_set``). Los numéricos admiten
    coma decimal; uno ilegible es un error (422), nunca un vaciado.

    A nivel de módulo (no dentro de ``build_app``): una clase local provoca un
    ForwardRef que Pydantic 2.12 no resuelve como ``Body(...)``.
    """

    codigo_partida: str | None = None
    descripcion: str | None = None
    cantidad: float | None = None
    unidad: str | None = None
    precio_unitario: float | None = None
    descuento: float | None = None
    codigo_externo: str | None = None

    @field_validator("cantidad", "precio_unitario", "descuento", mode="before")
    @classmethod
    def _numero(cls, valor: object) -> object:
        return _numero_es(valor)

    @field_validator(
        "codigo_partida", "descripcion", "unidad", "codigo_externo", mode="before",
    )
    @classmethod
    def _texto(cls, valor: object) -> str | None:
        if valor is None:
            return None
        return str(valor).strip() or None

    def campos(self) -> dict[str, Any]:
        """Los campos que vinieron en el cuerpo, con su valor (``None`` =
        vaciar)."""
        return {nombre: getattr(self, nombre) for nombre in sorted(self.model_fields_set)}


# ====================================================================== #
# NUEVO — bloque de VALORACIÓN.
#
# Se rellena cuando existe una fila en ``albaran_valuations`` para el
# document_id. Si no hay valoración todavía, ``valuation=None`` y el
# front pinta los campos con los valores extraídos del albarán (como
# antes). No añade UI de edición/relanzado — solo lectura.
# ====================================================================== #

class LineValuationPayload(BaseModel):
    """Una fila de ``albaran_line_valuations`` (servicio 6)."""

    # ---- sub-tanda 2D ----
    # id de la fila en albaran_line_valuations. Necesario para que el
    # revisor pueda editar las sintéticas (UPDATE por id).
    # Opcional para compatibilidad con payloads ya construidos
    # (se fue añadiendo progresivamente).
    valuation_line_id: int | None = None

    # merge_line_id:
    #   - int: línea 'from_albaran' (viene del albarán, línea del merge).
    #   - None: línea 'synthetic_modifier' (generada por el valorador
    #     para representar un modificador implícito: incremento por
    #     año, consistencia, árido, aditivo, residuos, tiempo).
    merge_line_id: int | None = None

    matched_contrato_line_id: int | None = None
    derived_contrato_line_id: int | None = None

    precio_unitario_contrato_db: float | None = None
    precio_unitario_pdf_inferido: float | None = None
    precio_unitario_final: float | None = None
    precio_unitario_source: str | None = None
    precio_unitario_agreement: str | None = None

    unidad_albaran: str | None = None
    unidad_contrato: str | None = None
    unidad_categoria: str | None = None
    unidad_category_match: bool | None = None

    cantidad_albaran: float | None = None
    cantidad_convertida: float | None = None
    factor_conversion: float | None = None

    importe_calculado: float | None = None
    importe_albaran_declarado: float | None = None
    importe_source: str | None = None

    codigo_partida_albaran: str | None = None
    codigo_partida_final: str | None = None

    # ---- edición de la salmon (jun 2026) ----
    descuento_albaran_aplicado: float | None = None
    codigo_externo: str | None = None
    partida_action: str | None = None
    # ---- F-065 R13–R17: el administrativo la guardó (guardar = bloquear) ----
    bloqueada: bool = False

    match_confidence_pct: float | None = None
    match_method: str | None = None
    review_required: bool | None = None

    # ---- F-036 R23: por qué esta línea salió así ----
    # Razones que sellaron sv6 (`residuos_contenedores`,
    # `declared_vs_calculated_mismatch`...) y sv4
    # (`front_sin_cantidad_convertida`...) en
    # `albaran_line_valuations.review_reasons_json`. Llega ya parseada:
    # siempre una lista, nunca None, para que la plantilla itere sin
    # guardas.
    review_reasons: list[str] = []

    # ---- sub-tanda 2D: identificación de línea sintética ----
    # Opcionales por compatibilidad con valoraciones anteriores a 2D.
    line_kind: str = "from_albaran"
    parent_merge_line_id: int | None = None
    modifier_source: str | None = None
    modifier_reason: str | None = None
    descripcion_linea: str | None = None

    @computed_field  # type: ignore[prop-decorator]
    @property
    def conversion_reproducible(self) -> bool:
        """¿Sabe sv4 rehacer la conversión de unidad de esta línea?

        F-036 R1/R8. Es un campo CALCULADO y no un dato guardado a
        propósito: así no puede quedar desincronizado de las tres
        columnas que lo determinan. El backend lo usa para no destrozar
        la cantidad convertida al guardar; la plantilla, para no
        rehacer en Jinja un importe que ya está calculado en BBDD.
        """
        return conversion_reproducible(
            factor=self.factor_conversion,
            cantidad_albaran=self.cantidad_albaran,
            cantidad_convertida=self.cantidad_convertida,
        )


class ValuationPayload(BaseModel):
    """Cabecera + mapa ``merge_line_id -> LineValuationPayload``."""

    valuation_id: str
    contrato_codigo: str | None = None
    status: str
    provider_ia: str | None = None
    model_name: str | None = None
    total_valorado: float = 0.0
    total_lines: int = 0
    lines_matched_exact: int = 0
    lines_matched_semantic: int = 0
    lines_matched_price_only: int = 0
    lines_unmatched: int = 0
    review_required: bool = False
    created_at_utc: str | None = None
    updated_at_utc: str | None = None
    lines_by_merge_line_id: dict[int, LineValuationPayload] = Field(
        default_factory=dict,
    )
    # ---- sub-tanda 2D ----
    # Líneas sintéticas (line_kind='synthetic_modifier'). No están en
    # lines_by_merge_line_id porque no tienen merge_line_id. El template
    # las itera aparte o las mezcla en display_lines.
    synthetic_lines: list[LineValuationPayload] = Field(default_factory=list)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def lines_by_valuation_line_id(self) -> dict[int, LineValuationPayload]:
        """Mapa ``valuation_line_id -> línea``, base Y sintéticas (F-036).

        ``lines_by_merge_line_id`` deja fuera a las sintéticas —no tienen
        ``merge_line_id``—, así que la plantilla necesitaba dos búsquedas
        distintas según el tipo de fila. La tabla del detalle sí tiene un
        identificador que vale para TODAS: ``DisplayLine.valuation_line_id``.
        Con este mapa, pintar las razones de una fila (R23) o decidir si
        su conversión es reproducible (R8) es la misma expresión para
        cualquier línea.
        """
        todas = list(self.lines_by_merge_line_id.values()) + list(
            self.synthetic_lines
        )
        return {
            linea.valuation_line_id: linea
            for linea in todas
            if linea.valuation_line_id is not None
        }


# ====================================================================== #
class ConciliacionDisplay(BaseModel):
    """Datos de la conciliación que se muestran inline bajo cada línea
    del albarán en sv4. NO contiene lógica — solo lo que el revisor
    debe ver: con qué línea casó (Sigrid o derivada) y si el precio
    coincide con la valoración.

    Lo rellena el repositorio (sv4) haciendo JOIN entre
    ``albaran_line_valuations`` (que sabe a qué línea casó: bien
    ``matched_contrato_line_id`` para una línea cacheada de Sigrid,
    bien ``derived_contrato_line_id`` para una línea creada por el
    valorador) y la tabla correspondiente.

    Si una línea del albarán no tiene valoración, ``concilia`` será
    None y la UI no muestra nada para esa fila.
    """

    # 'assigned' = la valoración casó con una línea cacheada de Sigrid
    #              (albaran_contrato_lines_merge).
    # 'derived'  = la valoración creó una línea nueva en
    #              contrato_lines_derived (porque no había hermana en
    #              Sigrid o el precio no cuadraba).
    kind: str

    # Datos a mostrar (vienen de la tabla origen según kind):
    descripcion: str | None = None
    unitario: float | None = None
    medicion_total: float | None = None
    medicion_pendiente: float | None = None
    unidad: str | None = None
    codigo_partida: str | None = None
    descripcion_partida: str | None = None

    # Indicador verde/rojo. Lo decide el motor (no el front):
    #   'agree'    -> precio del contrato coincide con el valorado
    #   'disagree' -> precio difiere
    #   None       -> no hay precio del contrato comparable (ej. línea
    #                 derived sin hermana de Sigrid)
    price_agreement: str | None = None
    precio_unitario_final: float | None = None  # el de la valoración

    # (F-065 R9) ``unitario`` es el precio APLICADO (el de la valoración, el
    # que pinta y edita la ficha); el de la línea de contrato va aquí (para
    # el ``title`` y los avisos ✓/⚠ contra el contrato).
    unitario_contrato: float | None = None

    # Avisos por campo de la fila salmon, comparando lo DECLARADO en la
    # linea blanca (lo leido del albaran) contra la referencia de contrato:
    #   True  -> declarado presente y coincide      (✓)
    #   False -> declarado presente pero difiere     (⚠)
    #   None  -> nada declarado que comparar          (sin icono)
    # Los calcula el repositorio en _build_display_lines (tiene a la vez
    # la linea blanca/merge y esta conciliacion).
    agree_partida: bool | None = None
    agree_cantidad: bool | None = None
    agree_unitario: bool | None = None

    # ---- edición de la salmon (jun 2026) ----
    # Campos que NO existen en Sigrid pero que la línea a insertar debe
    # llevar. Se persisten en albaran_line_valuations (columnas añadidas
    # por sv4: descuento_albaran_aplicado la crea sv6; codigo_externo es
    # propia de sv4) y el revisor puede editarlos en la fila salmon.
    descuento: float | None = None
    codigo_externo: str | None = None

    # (F-051 R10, R11) 'partida' | 'almacen' segun la partida FINAL de la
    # valoracion (vacia = almacen, sin mirar partida_action). En almacen,
    # codigo_partida y descripcion_partida van a None: la ficha pinta
    # «Almacén» y nunca la partida de la linea de contrato casada.
    estado_partida: str | None = None

    # (F-051, review pasada 2 · decisión del humano 2026-10-05) Fuera de
    # almacén ``codigo_partida`` es la partida FINAL de la valoración (la
    # que pinta el input), no la de la línea de contrato casada. La de la
    # casada se conserva aquí, también en almacén (donde no se pinta):
    # la usan los avisos ✓/⚠ contra el contrato y el aviso «pasará a
    # NUEVA» del navegador (R20: la de la casada no cambia la identidad).
    codigo_partida_casada: str | None = None

    # Senales para el calculo determinista de CONFIANZA (no se pintan):
    #   match_method / match_confidence_pct -> distinguir match fuerte
    #     (codigo/exacto) de semantico-familia (conf <= 50) y de manual.
    #   precio_unitario_source -> 'manual_contract'/'manual_derived' = el
    #     revisor lo fijo a mano.
    #   derived_origen -> 'manual_override' (nueva del revisor) vs
    #     'nueva_no_match' (nueva automatica: la IA no caso).
    match_method: str | None = None
    match_confidence_pct: float | None = None
    precio_unitario_source: str | None = None
    derived_origen: str | None = None
    agree_importe: bool | None = None

    # Solo para kind='derived': si la línea nueva se creó por
    # discrepancia de precio con una línea hermana de Sigrid, esta
    # caja lleva los datos de esa hermana para que el revisor lo vea.
    # None si la nueva se creó porque no había hermana en absoluto.
    sibling: "ConciliacionSibling | None" = None


class ConciliacionSibling(BaseModel):
    """Datos de la línea hermana de Sigrid que existió pero no se
    usó por discrepancia de precio. Solo aplica a líneas derived
    de origen 'price_mismatch' (futuro). Hoy se rellena None y el
    template oculta el sub-bloque."""
    descripcion: str | None = None
    unitario: float | None = None
    unidad: str | None = None
    codigo_partida: str | None = None


# Sub-tanda 2D — DisplayLine
#
# DTO uniforme para la tabla de líneas del detalle. Mezcla las líneas
# del merge (from_albaran) con las sintéticas de valoración, en el
# orden correcto para la UI (cada sintética justo después de su base).
#
# El template itera display_lines y trata todas las filas por igual.
# El campo ``line_kind`` y los ids internos (``merge_line_id`` para
# from_albaran, ``valuation_line_id`` para sintéticas) permiten al JS
# del front saber a qué endpoint enviar las ediciones al guardar.
# ====================================================================== #

class DisplayLine(BaseModel):
    """Una fila visible en la tabla de líneas del detalle."""

    # Identificación
    line_kind: str  # 'from_albaran' | 'synthetic_modifier' | 'manual' | 'reparto'
    merge_line_id: int | None = None       # solo si from_albaran
    valuation_line_id: int | None = None   # solo si synthetic_modifier
    line_index: int | None = None          # orden visual (para base y
                                            # para la sintética se usa
                                            # el line_index de la base +
                                            # orden de modificador)

    # Datos a mostrar / editar
    codigo_imputacion: str | None = None
    concepto: str | None = None
    cantidad: float | None = None
    unidad: str | None = None
    precio_unitario: float | None = None
    importe: float | None = None
    descuento: float | None = None
    codigo: str | None = None
    confianza_pct: float | None = None

    # Sub-campos que el template solo usa en modo traza (no de entrada).
    is_valued: bool = False                # True si hay valoración ligada
    parent_merge_line_id: int | None = None  # sintéticas: a qué base cuelgan

    # Bloque de conciliación inline. Solo no-None para líneas
    # 'from_albaran' que tienen una valoración (matched o derived).
    # El template lo renderiza en una fila expandible bajo la línea.
    concilia: ConciliacionDisplay | None = None

    # (F-065 R35) Reparto: «Parte k de N» y, en la primera fila de la familia,
    # el aviso mientras las partes no sumen lo que dice el albarán.
    parte: str | None = None
    aviso_reparto: str | None = None


def _aviso_de_obra(obra: OrigenCampo) -> str | None:
    """Texto del aviso de la obra para la ficha (F-048 R32, R33); ``None`` sin aviso."""
    candidatos = ", ".join(obra.candidatos_correo)
    if obra.discrepancia:
        return (
            f"Obra: el correo dice {obra.valor_correo} y el papel dice "
            f"{obra.valor_papel}. Se ha usado la del correo."
        )
    if obra.motivo == MOTIVO_CORREO_AMBIGUO:
        if obra.valor_papel:
            cierre = (
                f"ninguna es la del papel ({obra.valor_papel}). "
                "Se ha dejado la del papel."
            )
        else:
            cierre = "el papel no trae obra. Se ha dejado sin obra."
        return f"Obra: el correo cita varias obras ({candidatos}) y {cierre}"
    if obra.motivo == MOTIVO_CORREO_CONFIRMA_PAPEL:
        if obra.valor_final and obra.valor_final != obra.valor_papel:
            # Desde CR-C5 la cabecera lleva la forma de la lista (945 ⇒
            # 0945): se citan las dos para que no parezcan dos obras.
            return (
                f"Obra: el correo cita varias obras ({candidatos}) y una es "
                f"la del papel (el papel dice {obra.valor_papel}; en la lista "
                f"de obras, {obra.valor_final}). Se ha usado {obra.valor_final}."
            )
        return (
            f"Obra: el correo cita varias obras ({candidatos}) y una es "
            f"la del papel ({obra.valor_papel}). Se ha usado esa."
        )
    if obra.motivo == MOTIVO_CORREO_FUERA_DE_LISTA:
        verbo = "están" if len(obra.candidatos_correo) > 1 else "está"
        return (
            f"Obra: el correo cita {candidatos}, que no {verbo} en la lista "
            "de obras de Sigrid. Se ha usado la lectura del papel."
        )
    return None


# --------------------------------------------------------------------- #
# F-052 R20–R27 · rastro de la última búsqueda de contratos.
#
# Lo sella sv3 (dueño del schema) en las columnas `contratos_busqueda_*`
# del merge, y el fallback local de sv4 con la misma semántica (R22). Los
# literales de resultado son los de sv3 (`domain/models/contrato_models.py`):
# sv4 no puede importarlo, así que los ata un test que lee ese fichero.
# --------------------------------------------------------------------- #
BUSQUEDA_ENCONTRADOS = "encontrados"  # >= 1 contrato, por Sigrid o por caché
BUSQUEDA_NINGUNO = "ninguno"  # consulta correcta, 0 contratos
BUSQUEDA_ERROR = "error"  # la búsqueda falló (incluido un truncado)
BUSQUEDA_SIN_DATOS = "sin_datos"  # faltaba CIF u obra: no se buscó
RESULTADOS_BUSQUEDA_CONTRATOS = frozenset({
    BUSQUEDA_ENCONTRADOS, BUSQUEDA_NINGUNO, BUSQUEDA_ERROR, BUSQUEDA_SIN_DATOS,
})

# Qué mensaje pinta el bloque de contrato (R23–R26). Lo decide
# `application.services.busqueda_contratos.estado_busqueda` (R27).
ESTADO_BUSQUEDA_SIN_RASTRO = "sin_rastro"  # anterior a F-052: no consta
ESTADO_BUSQUEDA_VIGENTE = "vigente"  # rastro = datos actuales, búsqueda correcta
ESTADO_BUSQUEDA_DESFASADA = "desfasada"  # CIF u obra actuales distintos del rastro
ESTADO_BUSQUEDA_ERROR = "error"  # rastro = datos actuales, la búsqueda falló
ESTADO_BUSQUEDA_SIN_DATOS = "sin_datos"  # rastro = datos actuales, no se buscó

EstadoBusquedaContratos = Literal[
    "sin_rastro", "vigente", "desfasada", "error", "sin_datos",
]


class RastroBusquedaContratos(BaseModel):
    """Las cuatro columnas `contratos_busqueda_*` del merge, tal cual."""

    cif: str | None = None
    obra: str | None = None
    resultado: str | None = None
    at_utc: str | None = None


class BusquedaContratosVista(BaseModel):
    """Lo que el bloque de contrato necesita para decir la verdad (R23–R27).

    ``cif``, ``obra``, ``fecha`` y ``resultado`` son los del RASTRO (con
    qué se buscó), no los actuales del albarán: esos ya viajan en el
    propio payload.
    """

    estado: EstadoBusquedaContratos
    cif: str | None = None
    obra: str | None = None
    fecha: str | None = None
    resultado: str | None = None


class DocumentDetailPayload(BaseModel):
    id: str
    view_mode: str = Field(default=VIEW_MODE_MERGE)
    available_views: list[str] = Field(default_factory=list)
    is_editable: bool = True
    provider_document_id: str | None = None
    source_document_id: str | None = None
    document_storage_ref: str | None = None
    source_filename: str
    provider_origin: str
    model_name: str
    proveedor_nombre: str | None = None
    proveedor_cif: str | None = None
    fecha: str | None = None
    numero_albaran: str | None = None
    forma_pago: str | None = None
    obra_codigo: str | None = None
    obra_nombre: str | None = None
    obra_direccion: str | None = None
    document_url: str | None = None
    confidence_pct_calc: float | None = None
    review_required: bool | None = None
    review_reasons_json: str | None = None
    # F-043 R30 — las seis columnas de clasificación que sv3 escribe en
    # `albaran_documents_merge`. Se llaman IGUAL que allí a propósito:
    # sv4 no puede importar de sv3 (los dos tienen un paquete
    # `infrastructure` de primer nivel y en un proceso uno tapa al
    # otro), así que lo que ata las dos puntas es el nombre y el test
    # `test_f043_r30_los_seis_campos_se_llaman_como_las_columnas_de_sv3`.
    tipologia: str | None = None
    tipologia_confianza_pct: float | None = None
    tipologia_motivo: str | None = None
    tipologia_origen: str | None = None
    tipologia_mixta: bool | None = None
    tipologia_secundarias_json: str | None = None
    comparison_summary_json: str | None = None
    raw_extraction_json: str | None = None
    ia_output_json: str | None = None
    approved: bool = False
    approved_at_utc: str | None = None
    approved_by: str | None = None
    reviewed_at_utc: str | None = None
    review_notes: str | None = None
    created_at_utc: str
    lines: list[MergeLinePayload] = Field(default_factory=list)
    # Sub-tanda 2D — lista unificada para la UI: mezcla líneas del
    # merge (from_albaran) con las sintéticas de valoración en orden.
    # El template la usa en lugar de ``lines`` para pintar la tabla
    # en el detalle. ``lines`` se mantiene por compatibilidad (API).
    display_lines: list[DisplayLine] = Field(default_factory=list)
    # (F-051 R17) Cuántas líneas de la valoración tienen partida: las que
    # perderá el botón «Almacén a todas las líneas» (se avisa antes).
    lineas_con_partida: int = 0
    provider_snapshots: list[ProviderSnapshot] = Field(default_factory=list)
    contratos: list[ContratoPayload] = Field(default_factory=list)
    contrato_lines: list[ContratoLinePayload] = Field(default_factory=list)
    # Listas para los desplegables de cabecera: proveedores y obras que
    # tienen algun contrato en el proyecto (no solo los de este documento).
    proveedores_disponibles: list[ProveedorOption] = Field(default_factory=list)
    obras_disponibles: list[ObraOption] = Field(default_factory=list)
    selected_contrato_codigo: str | None = None
    # NUEVO — None mientras no exista valoración en BBDD.
    valuation: ValuationPayload | None = None
    # F-052 R27 — con qué se buscaron los contratos y si sigue valiendo
    # para el CIF y la obra actuales. Lo rellena el repositorio en el
    # detalle del merge; ``None`` en las vistas de proveedor.
    busqueda_contratos: BusquedaContratosVista | None = None
    # F-053 — alta en Sigrid (R29-R30) y producto de cada línea (R40). Lo
    # rellena el servicio en la vista merge SOLO con DESDE puesta (R3).
    # F-065 R21: suma de importes de las filas y de lo leído en las blancas
    # (None si no hay ninguno); R22: filas tocadas a mano (revalorar las
    # descarta). Los rellena el repositorio en el detalle del merge.
    suma_filas: float | None = None
    suma_leida: float | None = None
    n_filas_manuales: int = 0
    alta_sigrid_activa: bool = False
    alta_sigrid: AltaSigridVista | None = None
    alta_puede_solicitar: bool = False
    productos_sigrid: dict[int, ProductoLinea] = Field(default_factory=dict)
    productos_admitidos: list[ProductoOpcion] = Field(default_factory=list)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def aviso_suma(self) -> str | None:
        """(F-065 R21) Confirmación antes de aprobar si las sumas no cuadran."""
        return aviso_suma_importes(self.suma_filas, self.suma_leida)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def valorado(self) -> bool:
        """(F-053 R37, R38) ¿Está valorado? Con ``esta_valorado`` de comun,
        la misma regla que aplica el repositorio al aprobar y sv9 al dar de
        alta: ``ok`` de sv6 o valoración manual completa."""
        valoracion = self.valuation
        if valoracion is None:
            return False
        lineas = list(valoracion.lines_by_merge_line_id.values()) + list(
            valoracion.synthetic_lines
        )
        return esta_valorado(valoracion.status, [l.importe_calculado for l in lineas])

    @computed_field  # type: ignore[prop-decorator]
    @property
    def review_reasons(self) -> list[str]:
        """Motivos de revisión del documento, ya parseados (F-036 R23).

        ``review_reasons_json`` viajaba al payload desde siempre y nadie
        lo abría: la plantilla no puede hacer `json.loads` en Jinja, así
        que los motivos que sella sv3 —``proveedor_cif_no_casa:<cif>``,
        ``obra_no_resuelta``...— no se pintaban en ninguna parte.
        """
        return motivos_de_json(self.review_reasons_json)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def clasificacion(self) -> ClasificacionAlbaran | None:
        """La clasificación de DOCUMENTO que decidió IA1 (F-043 R30).

        Inverso exacto de `campos_clasificacion_merge` de sv3: allí se
        escriben las seis columnas, aquí se leen. sv4 **pinta** lo que
        decidió la IA; no infiere, no corrige y no completa la familia
        por código LER, designación de producto, palabras clave ni CIF
        (R12, R13). El front es el sitio más tentador para «arreglarlo»
        con un `if` —tiene delante todo el papel— y es justo el lazo
        cerrado que esta feature desmonta.

        `None` cuando `tipologia` viene NULL: un documento anterior a
        F-043, que no se reclasifica (decisión 5 del humano: sin
        backfill). Devolver `generico`/0 sería enseñarle al revisor una
        decisión de IA que nadie tomó.

        Los dos recortes son defensivos, con el mismo criterio con que
        sv3 recorta `tipologia` a VARCHAR(32): ni un JSON corrupto en
        `tipologia_secundarias_json` ni una confianza fuera de 0..100
        pueden dejar al revisor sin poder ABRIR la ficha. Lo que el
        revisor necesita —familia, confianza y motivo— sobrevive.
        """
        familia = (self.tipologia or "").strip()
        if not familia:
            return None
        confianza = float(self.tipologia_confianza_pct or 0.0)
        return ClasificacionAlbaran(
            familia=familia,
            confianza_pct=min(100.0, max(0.0, confianza)),
            motivo=self.tipologia_motivo or "",
            mixto=bool(self.tipologia_mixta),
            familias_secundarias=motivos_de_json(
                self.tipologia_secundarias_json
            ),
            origen=self.tipologia_origen or ORIGEN_IA1,
        )

    @computed_field  # type: ignore[prop-decorator]
    @property
    def clasificacion_nombre(self) -> str | None:
        """Nombre legible de la familia, sacado del catálogo compartido.

        sv4 NO mantiene lista propia de familias (F-043 R2): la única
        vive en `ruesma_comun.contratos.familias`. Una etiqueta que no
        esté en el catálogo se enseña tal cual —sv2 ya normaliza a
        `generico` lo que la IA se invente (R10)—: taparla aquí sería
        decidir, y sv4 no decide.
        """
        clasificacion = self.clasificacion
        if clasificacion is None:
            return None
        familia = obtener_familia(clasificacion.familia)
        return familia.nombre if familia else clasificacion.familia

    @computed_field  # type: ignore[prop-decorator]
    @property
    def clasificacion_en_duda(self) -> bool:
        """¿Sv3 marcó esta clasificación como poco fiable? (R28, R29).

        La respuesta sale de los motivos que sv3 ya selló, NO de
        recalcular el umbral aquí: el umbral es configurable y vive en
        sv3, que es quien lo aplica. Con una copia en sv4, el día que el
        humano lo cambie la ficha diría una cosa y la BBDD otra.
        """
        motivos = set(self.review_reasons)
        return any(motivo in motivos for motivo in MOTIVOS_CLASIFICACION_EN_DUDA)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def origen_datos(self) -> OrigenDatos | None:
        """De dónde salió la OBRA —correo o papel— (F-048 R32–R35).

        sv3 guarda el bloque dentro del ``raw_extraction_json`` del merge y
        aquí solo se LEE, con el modelo de ``comun``. Todo lo que no sea un
        bloque válido —JSON ausente, roto o que no es un objeto, sin
        ``data``, sin bloque o un bloque que no valida— da ``None`` y la
        ficha abre como hoy, sin aviso (R35): perder el aviso es mejor que
        dejar al revisor sin poder abrir el documento.

        Solo en la vista MERGE, como la clasificación de F-043: la vista
        de un proveedor es su extracción cruda.
        """
        if self.view_mode != VIEW_MODE_MERGE or not self.raw_extraction_json:
            return None
        try:
            envelope = json.loads(self.raw_extraction_json)
        except (TypeError, ValueError):
            return None
        data = envelope.get("data") if isinstance(envelope, dict) else None
        bloque = data.get("origen_datos") if isinstance(data, dict) else None
        if not isinstance(bloque, dict):
            return None
        try:
            return OrigenDatos.model_validate(bloque)
        except ValidationError:
            return None

    @computed_field  # type: ignore[prop-decorator]
    @property
    def avisos_origen_datos(self) -> list[str]:
        """Lo que el revisor tiene que saber de la obra (R32, R33).

        - Discrepancia: el campo, lo que dice el correo y lo que dice el
          papel (manda el correo).
        - ``correo_ambiguo``, ``correo_confirma_papel`` y
          ``correo_fuera_de_lista``: los códigos que cita el correo.

        El resto de casos (sin correo, sin código, sin lectura de la IA o
        un código que casa con el papel) no pinta nada. sv4 PINTA: el
        cruce lo hizo sv2 y aquí no se recalcula.

        Si la cabecera cambió de obra después (``obra_cambiada_tras_extraer``),
        el primer aviso lo dice y el resto queda como lo que pasó al extraer.
        Sin sujeto (CR-F1): la pudo cambiar el revisor o sv3, y sv4 no sabe
        quién.
        """
        origen = self.origen_datos
        if origen is None:
            return []
        obra = origen.obra
        aviso = _aviso_de_obra(obra)
        if not self.obra_cambiada_tras_extraer:
            return [aviso] if aviso else []
        # CR-D4 (aviso C de la review del bloque D, opción (b) del líder):
        # la cabecera ya no es la que fijó la extracción. Se dice primero y
        # lo demás pasa a ser historia. Sin sujeto (CR-F1, bloqueante 1 de
        # la review del bloque F): además del revisor, la cambia sv3
        # (``HeaderResolverService`` deduce la obra si el código no pasa su
        # normalizador) ya en la primera persistencia, y ``update_document``
        # no deja marca de quién fue. Solo si el correo dijo algo: sin
        # aviso de siempre y sin obra impuesta por el correo, no hay nada
        # «según el correo» que contar.
        if aviso is None and obra.fuente != FUENTE_CORREO:
            return []
        de_donde = "la que decía el correo" if obra.fuente == FUENTE_CORREO else "la del papel"
        cambio = (
            f"Obra: la cabecera lleva ahora {self.obra_codigo} (cambiada "
            f"después de extraer); al extraer se fijó {obra.valor_final}, "
            f"{de_donde}."
        )
        historia = [aviso.replace("Obra: ", "Al extraer, ", 1)] if aviso else []
        return [cambio, *historia]

    @computed_field  # type: ignore[prop-decorator]
    @property
    def obra_cambiada_tras_extraer(self) -> bool:
        """¿La obra de la cabecera ya no es la que fijó la extracción? (CR-D4).

        Compara la obra actual del merge con ``origen_datos.obra.valor_final``
        con ``normalizar_codigo`` de ``comun`` (D9: ``945`` y ``0945`` son la
        misma). Solo cuenta un cambio a OTRA obra: sin ``valor_final`` no hay
        con qué comparar, y una obra vacía la deja la red de obra de sv3
        (R28), que añade su propio motivo; eso no es un cambio de obra.
        No dice QUIÉN la cambió (CR-F1): puede ser el revisor o sv3
        (``HeaderResolverService``, al persistir, en el duplicado o al
        «volver a buscar»), y el payload no trae con qué distinguirlos.
        Solo pinta: no escribe nada ni toca ``review_reasons`` (R35, §6).
        """
        origen = self.origen_datos
        if origen is None:
            return False
        final = normalizar_codigo(origen.obra.valor_final)
        actual = normalizar_codigo(self.obra_codigo)
        return final is not None and actual is not None and actual != final

    @computed_field  # type: ignore[prop-decorator]
    @property
    def origen_en_duda(self) -> bool:
        """¿Sv3 mandó la obra a revisión por el correo? (R34).

        Sale de los motivos que sv3 ya selló (``MOTIVOS_REVISION_ORIGEN``
        de ``comun``), no del bloque: la regla vive en sv3, que es quien la
        aplica. ``correo_confirma_papel`` y ``correo_fuera_de_lista`` son
        informativos y no la ponen en duda.
        """
        motivos = set(self.review_reasons)
        return any(motivo in motivos for motivo in MOTIVOS_REVISION_ORIGEN)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def contrato_pdf_url(self) -> str | None:
        """URL para abrir el PDF del contrato en SharePoint.

        Robusto: prioriza el contrato seleccionado; usa su
        ``pdf_sharepoint_web_url`` y, si no lo tuviera, construye la URL
        desde ``pdf_sharepoint_relative_path`` reutilizando la base del
        enlace del albarán (``document_url``), que comparte el mismo
        document library. Devuelve None solo si NINGÚN contrato tiene ni
        web_url ni relative_path (entonces el path no se guardó en sv3).
        """
        contratos = self.contratos or []
        if not contratos:
            return None
        elegido = None
        if self.selected_contrato_codigo:
            for c in contratos:
                if c.codigo_contrato == self.selected_contrato_codigo:
                    elegido = c
                    break
        if elegido is None:
            for c in contratos:
                if c.pdf_sharepoint_web_url or c.pdf_sharepoint_relative_path:
                    elegido = c
                    break
        if elegido is None:
            elegido = contratos[0]

        if elegido.pdf_sharepoint_web_url:
            return elegido.pdf_sharepoint_web_url
        rel = elegido.pdf_sharepoint_relative_path
        if rel and self.document_url and "/albaranes/" in self.document_url:
            base = self.document_url.split("/albaranes/", 1)[0]
            return base + "/" + quote(rel, safe="/")
        return None

    @computed_field  # type: ignore[prop-decorator]
    @property
    def contrato_pdf_codigo(self) -> str | None:
        """Código del contrato cuyo PDF abre ``contrato_pdf_url``."""
        contratos = self.contratos or []
        if not contratos:
            return None
        if self.selected_contrato_codigo:
            for c in contratos:
                if c.codigo_contrato == self.selected_contrato_codigo:
                    return c.codigo_contrato
        for c in contratos:
            if c.pdf_sharepoint_web_url or c.pdf_sharepoint_relative_path:
                return c.codigo_contrato
        return contratos[0].codigo_contrato


class PaginatedDocuments(BaseModel):
    items: list[DocumentListItem]
    total: int
    page: int
    page_size: int
    total_pages: int
    approved_count: int
    pending_count: int
    review_required_count: int
    trash_count: int = 0
    importe_pendiente_aprobar: float = 0.0


class ObraResumenItem(BaseModel):
    """Fila de la vista de OBRAS (jul 2026): una obra con sus contadores
    de albaranes activos y el importe valorado agregado."""

    obra_codigo: str | None = None
    obra_nombre: str | None = None
    total_albaranes: int = 0
    pendientes: int = 0
    aprobados: int = 0
    revision_requerida: int = 0
    importe_valorado: float = 0.0
    ultima_fecha: str | None = None


class ProveedorResumenItem(BaseModel):
    """Fila de la vista de PROVEEDORES (jul 2026): un proveedor (por CIF
    normalizado; los sin CIF se agrupan por nombre) con sus contadores."""

    proveedor_cif: str | None = None
    proveedor_nombre: str | None = None
    total_albaranes: int = 0
    pendientes: int = 0
    aprobados: int = 0
    revision_requerida: int = 0
    importe_valorado: float = 0.0
    ultima_fecha: str | None = None


class SaveResponse(BaseModel):
    ok: bool
    document_id: str
    approved: bool
    redirect_url: str
    message: str
    # F-052 D4-A: «Guardar» relanzó la búsqueda de contratos (CIF u obra
    # distintos del último rastro).
    busqueda_relanzada: bool = False


class HealthResponse(BaseModel):
    ok: bool
    service: str
    version: str
    tables_ready: bool
    details: dict[str, Any]


def normalize_view_mode(value: str | None) -> str:
    if not value:
        return VIEW_MODE_MERGE
    cleaned = str(value).strip().lower()
    if cleaned in ALLOWED_VIEW_MODES:
        return cleaned
    return cleaned or VIEW_MODE_MERGE
