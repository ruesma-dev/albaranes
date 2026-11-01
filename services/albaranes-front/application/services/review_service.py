# application/services/review_service.py
from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from datetime import UTC, datetime

from ruesma_comun.alta_sigrid import (
    clasificacion_documento,
    es_linea_a_registrar,
    es_linea_vinculada,
    nombre_producto,
    producto_efectivo,
)
from ruesma_comun.sigrid import ListaPartidasObra

from application.services.busqueda_contratos import (
    cambio_de_cabecera,
    debe_relanzar_busqueda,
    hay_datos_para_buscar,
)
from domain.models.alta_sigrid_models import (
    AlbaranBloqueadoError,
    ConfigAltaSigrid,
    ProductoLinea,
    ProductoOpcion,
    ResultadoAprobacion,
)
from domain.models.contrato_refetch_models import ContratoRefetchOutcome
from domain.models.review_models import (
    VIEW_MODE_MERGE,
    AlbaranAprobadoError,
    posiciones_filas_ficha,
    DivisionHecha,
    DocumentDetailPayload,
    DocumentListFilters,
    MergeDocumentUpdatePayload,
    ObraResumenItem,
    PaginatedDocuments,
    ParteDivision,
    ProveedorResumenItem,
)
from domain.ports.contrato_refetch_port import ContratoRefetchClient
from domain.ports.orchestrator_port import OrchestratorClient
from domain.ports.partidas_obra_port import PartidasObraPort
from domain.services.partidas_ficha import presentar_partidas, traducir_partida
from domain.services.alta_sigrid import (
    FASE_RESULTADO,
    fase_alta,
    motivos_linea_vista,
    puede_reintentar_adjunto,
    puede_solicitar_alta,
)
from infrastructure.database.review_repository import AlbaranReviewRepository

logger = logging.getLogger(__name__)


def _familia_de_la_linea(contexto_linea_json: str | None) -> str | None:
    """``tipo_familia`` del contexto de línea que escribe sv3 (F-043), como
    lo lee sv9; JSON ausente o roto = sin familia (se usa la del documento)."""
    try:
        contexto = json.loads(contexto_linea_json) if contexto_linea_json else {}
    except (TypeError, ValueError):
        return None
    familia = contexto.get("tipo_familia") if isinstance(contexto, dict) else None
    return str(familia) if familia else None


@dataclass(frozen=True)
class ResultadoGuardado:
    """«Guardar» del portal: el detalle guardado, la re-búsqueda de
    contratos relanzada (F-052 D4-A) y lo que pasó con la aprobación
    (F-053 R1–R4)."""

    detail: DocumentDetailPayload
    busqueda: ContratoRefetchOutcome | None
    aprobacion: ResultadoAprobacion
    # (F-115 R11) El contrato que el guardado quitó por no ser del proveedor
    # y la obra guardados, y qué cambió (``proveedor`` u ``obra``).
    contrato_retirado: str | None = None
    cambio: str | None = None


@dataclass(frozen=True)
class ResultadoAlmacenTodas:
    """«Almacén a todas las líneas» (F-051 R16): las que pasaron a almacén y
    las que se saltó por estar guardadas (F-065 R14)."""

    tocadas: int
    saltadas: int


@dataclass(frozen=True)
class ResultadoBorradoMultiple:
    """Borrado en bloque (F-053 R27): movidos a la papelera y saltados por
    tener un alta en Sigrid bloqueante."""

    movidos: int
    saltados: int


class ReviewService:
    def __init__(
        self,
        repository: AlbaranReviewRepository,
        default_reviewer: str | None,
        orchestrator: OrchestratorClient | None = None,
        config_alta: ConfigAltaSigrid | None = None,
        partidas: PartidasObraPort | None = None,
    ) -> None:
        """``orchestrator`` y ``config_alta`` (F-053) son posicionales y
        opcionales: sin ellos, la feature está apagada (R3) y el servicio
        se comporta como antes. ``partidas`` (F-098) es la lista de partidas
        por obra; sin ella, la ficha pinta y guarda la partida como antes."""
        self._repository = repository
        self._default_reviewer = (default_reviewer or "").strip() or None
        self._orchestrator = orchestrator
        self._config_alta = config_alta or ConfigAltaSigrid()
        self._partidas = partidas

    @property
    def config_alta(self) -> ConfigAltaSigrid:
        return self._config_alta

    def initialize(self) -> bool:
        return self._repository.initialize()

    def list_documents(self, filters: DocumentListFilters) -> PaginatedDocuments:
        return self._repository.list_documents(filters)

    def list_obras_resumen(
        self, *, search: str | None = None,
    ) -> list[ObraResumenItem]:
        """Vista de OBRAS (jul 2026): resumen agregado por obra."""
        return self._repository.list_obras_resumen(search=search)

    def list_proveedores_resumen(
        self, *, search: str | None = None,
    ) -> list[ProveedorResumenItem]:
        """Vista de PROVEEDORES (jul 2026): resumen agregado por CIF."""
        return self._repository.list_proveedores_resumen(search=search)

    def get_neighbor_ids(
        self,
        *,
        document_id: str,
        filters: DocumentListFilters,
    ) -> tuple[str | None, str | None]:
        """IDs del albaran anterior y siguiente segun el orden+filtros de
        la bandeja (para los botones de navegacion del detalle)."""
        return self._repository.get_neighbor_ids(
            document_id=document_id,
            filters=filters,
        )

    def get_document(
        self,
        document_id: str,
        *,
        view_mode: str = VIEW_MODE_MERGE,
    ) -> DocumentDetailPayload | None:
        detalle = self._repository.get_document_detail(
            document_id,
            view_mode=view_mode,
        )
        # F-098 R23, R24, R28: con la lista de la obra, la partida se pinta en
        # código completo y el ✓/⚠ compara por la hoja (en todas las vistas:
        # presentar no escribe). Sin lista, el mismo detalle de siempre.
        if detalle is not None and self._partidas is not None and detalle.obra_codigo:
            detalle = presentar_partidas(detalle, self._partidas.lista(detalle.obra_codigo))
        # F-053: con DESDE puesta, la ficha (vista merge) lleva el alta y el
        # producto de cada línea (R29, R30, R40). Con DESDE vacía, nada (R3).
        if (
            detalle is None
            or not self._config_alta.activa
            or detalle.view_mode != VIEW_MODE_MERGE
        ):
            return detalle
        alta = self._repository.leer_alta_sigrid(document_id)
        return detalle.model_copy(update={
            "alta_sigrid_activa": True,
            "alta_sigrid": alta,
            "alta_puede_solicitar": self.puede_solicitar_alta(document_id),
            "alta_puede_reintentar_adjunto": self.puede_reintentar_adjunto(document_id),
            "alta_fase": self.fase_alta(document_id) or FASE_RESULTADO,
            "alta_motivos_linea": motivos_linea_vista(
                alta, posiciones_filas_ficha(detalle.display_lines),
            ),
            "productos_sigrid": self.productos_sigrid(
                document_id,
                clasificacion_documento(detalle.tipologia, detalle.tipologia_mixta),
            ),
            "productos_admitidos": [
                ProductoOpcion(codigo=codigo, nombre=nombre_producto(codigo))
                for codigo in sorted(self._config_alta.admitidos)
            ],
        })

    def get_contrato_pdf_url(self, document_id: str) -> str | None:
        """URL del PDF del contrato en SharePoint para abrir desde el front.
        Resuelta por consulta directa en el repositorio (robusta)."""
        return self._repository.get_contrato_pdf_url(document_id)

    def save_document(
        self,
        *,
        document_id: str,
        payload: MergeDocumentUpdatePayload,
    ) -> DocumentDetailPayload:
        """Guarda (y, si pasa a aprobado, pide el alta: R1). Compatibilidad:
        devuelve solo el detalle; el portal usa :meth:`guardar`."""
        detail, _ = self._guardar_y_aprobar(document_id=document_id, payload=payload)
        return detail

    def _guardar_y_aprobar(
        self,
        *,
        document_id: str,
        payload: MergeDocumentUpdatePayload,
    ) -> tuple[DocumentDetailPayload, ResultadoAprobacion]:
        if payload.approved and not payload.approved_by:
            payload.approved_by = self._default_reviewer
        # Historial: estado previo de la cabecera, lo único que toca el
        # guardado (F-065 R1: las líneas del payload se ignoran).
        snaps = [
            self._repository.snapshot_row(
                table="albaran_documents_merge", row_id=document_id,
            ),
        ]
        # F-053: el repositorio comprueba el alta (R26), no deja aprobar lo
        # no valorado (R37) y dice si el documento PASÓ a aprobado en esta
        # transacción (R1, R2).
        detail, paso_a_aprobado = self._repository.update_document_y_transicion(
            document_id=document_id, payload=payload,
        )
        self._repository.record_undo(
            document_id=document_id,
            action="guardar",
            description=(
                "Guardar cabecera "
                f"({self._repository.doc_label(document_id=document_id)})"
            ),
            restore=snaps,
        )
        aprobacion = self._pedir_alta_si_toca(
            document_id=document_id,
            approved_by=payload.approved_by,
            paso_a_aprobado=paso_a_aprobado,
        )
        return detail, aprobacion

    def guardar(
        self,
        *,
        document_id: str,
        payload: MergeDocumentUpdatePayload,
        refetch_client: ContratoRefetchClient | None,
    ) -> ResultadoGuardado:
        """«Guardar» / «Guardar y aprobar» del portal (PUT): guarda, pide el
        alta si el documento pasó a aprobado (F-053 R1–R4) y, si toca,
        relanza la búsqueda de contratos (F-052 D4-A, ver
        :meth:`save_document_y_buscar_si_cambia`)."""
        detail, aprobacion = self._guardar_y_aprobar(
            document_id=document_id, payload=payload,
        )
        busqueda = self._relanzar_busqueda_si_cambia(
            document_id=document_id, payload=payload, detail=detail,
            refetch_client=refetch_client,
        )
        retirado = getattr(detail, "contrato_retirado", None)
        return ResultadoGuardado(
            detail=detail, busqueda=busqueda, aprobacion=aprobacion,
            contrato_retirado=retirado,
            cambio=(
                cambio_de_cabecera(detail.proveedor_cif, detail.busqueda_contratos)
                if retirado else None
            ),
        )

    #: (F-116 R6) Etiquetas del deshacer, en el orden de la ficha.
    ETIQUETAS_CABECERA = {
        "fecha": "Fecha", "numero_albaran": "Número",
        "forma_pago": "Forma de pago", "review_notes": "Notas",
    }

    def editar_cabecera(
        self, *, document_id: str, campos: dict[str, str | None],
    ) -> dict[str, str | None]:
        """(F-116 R1, R6) Autoguardado de la cabecera: guarda solo ``campos``
        (ver ``update_cabecera_campos``) y deja una entrada de deshacer
        «Editar cabecera · {campos}» que devuelve la cabecera a como estaba.
        Sin campos no escribe ni registra nada."""
        if not campos:
            return {}
        snap = self._repository.snapshot_row(
            table="albaran_documents_merge", row_id=document_id,
        )
        guardado = self._repository.update_cabecera_campos(
            document_id=document_id, campos=campos,
        )
        nombres = ", ".join(
            etiqueta for campo, etiqueta in self.ETIQUETAS_CABECERA.items() if campo in campos
        )
        self._repository.record_undo(
            document_id=document_id,
            action="cabecera",
            description=(
                f"Editar cabecera · {nombres} "
                f"({self._repository.doc_label(document_id=document_id)})"
            ),
            restore=[snap],
        )
        return guardado

    def save_document_y_buscar_si_cambia(
        self,
        *,
        document_id: str,
        payload: MergeDocumentUpdatePayload,
        refetch_client: ContratoRefetchClient | None,
    ) -> tuple[DocumentDetailPayload, ContratoRefetchOutcome | None]:
        """«Guardar» del portal (F-052 D4-A): guarda y, si el CIF o la obra
        guardados ya no son los del último rastro de búsqueda —o el
        documento no tiene rastro (O-C1)—, relanza la re-búsqueda de
        contratos por ``refetch_client`` (en producción, ``q-persistencia``
        con ``force=True``, la misma vía que «Guardar y volver a buscar»).

        No relanza: sin ``refetch_client`` (los demás PUT del portal), si
        el guardado aprueba el albarán, si el rastro coincide con los
        datos guardados (``debe_relanzar_busqueda``) o si CIF y obra están
        los dos vacíos (``hay_datos_para_buscar``, CR-C3). Un fallo al relanzar
        no deshace el guardado: vuelve como outcome ``sigrid_error`` para
        que el portal lo diga.
        """
        resultado = self.guardar(
            document_id=document_id, payload=payload, refetch_client=refetch_client,
        )
        return resultado.detail, resultado.busqueda

    def _relanzar_busqueda_si_cambia(
        self,
        *,
        document_id: str,
        payload: MergeDocumentUpdatePayload,
        detail: DocumentDetailPayload,
        refetch_client: ContratoRefetchClient | None,
    ) -> ContratoRefetchOutcome | None:
        if (
            refetch_client is None
            or payload.approved
            or not debe_relanzar_busqueda(detail.busqueda_contratos)
            or not hay_datos_para_buscar(detail.proveedor_cif, detail.obra_codigo)
        ):
            return None
        try:
            outcome = refetch_client.refetch(document_id=document_id)
        except Exception as exc:  # el guardado ya está hecho: no se deshace
            logger.exception(
                "[contrato-refetch][guardar] no se pudo relanzar la búsqueda "
                "document_id=%s",
                document_id,
            )
            outcome = ContratoRefetchOutcome(
                status="sigrid_error",
                count=0,
                selected_contrato_codigo=None,
                message=(
                    "Documento guardado, pero no se pudo relanzar la búsqueda "
                    f"de contratos: {exc}. Pulsa «Solo volver a buscar»."
                ),
                cif=None,
                obra_codigo=None,
            )
        logger.info(
            "[contrato-refetch][guardar] CIF u obra cambiados (o sin rastro): "
            "búsqueda relanzada document_id=%s status=%s",
            document_id,
            outcome.status,
        )
        return outcome

    def approve_document(
        self, *, document_id: str, approved_by: str | None,
    ) -> ResultadoAprobacion:
        """«Aprobar» del listado. El repositorio no deja aprobar lo no
        valorado (R37) y dice si el documento PASÓ a aprobado; solo
        entonces se pide el alta en Sigrid (R1, R2)."""
        quien = approved_by or self._default_reviewer
        paso_a_aprobado = self._repository.set_approved(
            document_id=document_id,
            approved=True,
            approved_by=quien,
        )
        return self._pedir_alta_si_toca(
            document_id=document_id,
            approved_by=quien,
            paso_a_aprobado=bool(paso_a_aprobado),
        )

    def _pedir_alta_si_toca(
        self,
        *,
        document_id: str,
        approved_by: str | None,
        paso_a_aprobado: bool,
    ) -> ResultadoAprobacion:
        """F-053 R1–R4: solo en el PASO a aprobado y con DESDE puesta se
        publica el alta. Si no se puede publicar, la aprobación se queda
        (ya está confirmada en BBDD) y el resultado lo dice (R4)."""
        if not paso_a_aprobado or not self._config_alta.activa:
            return ResultadoAprobacion(paso_a_aprobado=paso_a_aprobado)
        publicado = False
        if self._orchestrator is None:
            logger.warning(
                "[alta-sigrid][aprobar] sin cliente de colas: no se pide el "
                "alta de document_id=%s", document_id,
            )
        else:
            try:
                publicado = bool(self._orchestrator.notify_document_approved(
                    document_id=document_id, approved_by=approved_by,
                ))
            except Exception:  # noqa: BLE001 — R4: la aprobación se queda
                logger.exception(
                    "[alta-sigrid][aprobar] fallo publicando el alta "
                    "document_id=%s", document_id,
                )
        if not publicado:
            logger.warning(
                "[alta-sigrid][aprobar] aprobado, pero el alta en Sigrid NO "
                "se pidió document_id=%s (R4)", document_id,
            )
        return ResultadoAprobacion(paso_a_aprobado=True, alta_pedida=publicado)

    def delete_document(
        self, *, document_id: str, deleted_by: str | None
    ) -> None:
        """Soft-delete: mueve el albarán a la papelera (is_active=False)."""
        self._repository.soft_delete_document(
            document_id=document_id,
            deleted_by=deleted_by or self._default_reviewer,
        )

    def bulk_delete_documents(
        self, *, document_ids: list[str], deleted_by: str | None
    ) -> int:
        """Borrado en BLOQUE (jul 2026): soft-delete de varios
        albaranes seleccionados en la bandeja. Best-effort por id
        (uno corrupto no frena al resto). Devuelve cuantos se
        movieron a la papelera. Restaurables desde alli, como el
        borrado individual."""
        return self.bulk_delete_documents_con_saltos(
            document_ids=document_ids, deleted_by=deleted_by,
        ).movidos

    def bulk_delete_documents_con_saltos(
        self, *, document_ids: list[str], deleted_by: str | None
    ) -> ResultadoBorradoMultiple:
        """Como :meth:`bulk_delete_documents`, contando aparte los que se
        saltan por tener un alta en Sigrid bloqueante (F-053 R27)."""
        movidos = 0
        saltados = 0
        for document_id in document_ids:
            try:
                self._repository.soft_delete_document(
                    document_id=document_id,
                    deleted_by=deleted_by or self._default_reviewer,
                )
                movidos += 1
            except AlbaranBloqueadoError:
                saltados += 1
            except Exception:  # noqa: BLE001 - best-effort
                logger.exception("[bulk-delete] fallo con id=%s", document_id)
        return ResultadoBorradoMultiple(movidos=movidos, saltados=saltados)

    def restore_document(self, *, document_id: str) -> None:
        """Restaura un albarán desde la papelera (is_active=True)."""
        self._repository.restore_document(document_id=document_id)

    def hard_delete_document(self, *, document_id: str) -> str | None:
        """Purga DEFINITIVA: borra físicamente el albarán y todo lo que
        cuelga de él (líneas, valoración, contratos asociados, cruda).
        Irreversible. Pensado para usarse solo desde la papelera.

        Devuelve el ``source_sha256`` del documento purgado (o None) —
        el endpoint del portal lo reenvía a sv7 en el evento
        ``document-purged`` para desbloquear el dedup por contenido."""
        return self._repository.hard_delete_document(document_id=document_id)

    def update_line_conciliacion(
        self,
        *,
        document_id: str,
        valuation_line_id: int,
        campos: dict | None = None,
        bloquear: bool = False,
        cuadrar: str | None = None,
    ) -> bool:
        """Edición de una fila con SOLO los campos cambiados (F-065 R8) y,
        con ``bloquear``, «Guardar» = aplicar y bloquear (R13). Una entrada
        de deshacer que devuelve la fila (y el total) a como estaba.

        (F-098 R25, R26) Una partida no vacía se guarda como el cod de la
        lista de la obra si casa (``CD.99.01.64`` ⇒ ``99.01.64``); así el
        repositorio decide Contrato/Nueva con el cod.

        (F-106 R4, R9) ``cuadrar`` (``importe`` o ``precio``): los botones de
        una fila que no cuadra. ``NoDespejable`` sube tal cual (422)."""
        partida = (campos or {}).get("codigo_partida")
        if isinstance(partida, str) and partida.strip():
            campos = {**campos, "codigo_partida": self._traducir(document_id, partida)}
        etiqueta = self._undo_line_desc(valuation_line_id)
        snap_line = self._undo_snap_line(valuation_line_id)
        snap_val = self._undo_snap_valuation(document_id)
        ok = self._repository.update_line_conciliacion(
            document_id=document_id,
            valuation_line_id=valuation_line_id,
            campos=campos,
            bloquear=bloquear,
            cuadrar=cuadrar,
        )
        if ok:
            self._repository.record_undo(
                document_id=document_id,
                action="linea_edit",
                description=(
                    f"{'Guardar' if bloquear else 'Editar'} línea · {etiqueta} "
                    f"({self._repository.doc_label(document_id=document_id)})"
                ),
                restore=[snap_line, snap_val],
            )
        return ok

    def volver_a_calculado(self, *, document_id: str, valuation_line_id: int) -> bool:
        """(F-106 R30) «Volver a lo calculado»: la fila vuelve a lo que calculó
        sv6, sin edición y desbloqueada. Una entrada de deshacer que devuelve la
        fila (con su edición) y el total a como estaban."""
        etiqueta = self._undo_line_desc(valuation_line_id)
        snap_line = self._undo_snap_line(valuation_line_id)
        snap_val = self._undo_snap_valuation(document_id)
        ok = self._repository.volver_a_calculado(
            document_id=document_id, valuation_line_id=valuation_line_id,
        )
        if ok:
            self._repository.record_undo(
                document_id=document_id,
                action="volver_a_calculado",
                description=(
                    f"Volver a lo calculado · {etiqueta} "
                    f"({self._repository.doc_label(document_id=document_id)})"
                ),
                restore=[snap_line, snap_val],
            )
        return ok

    def bloquear_linea(self, *, document_id: str, valuation_line_id: int) -> bool:
        """(F-065 R13, R15) Bloquea la fila, con su entrada de deshacer."""
        return self._marcar_bloqueada(document_id, valuation_line_id, True)

    def desbloquear_linea(self, *, document_id: str, valuation_line_id: int) -> bool:
        """(F-065 R15) Desbloquea la fila, con su entrada de deshacer."""
        return self._marcar_bloqueada(document_id, valuation_line_id, False)

    def _marcar_bloqueada(
        self, document_id: str, valuation_line_id: int, bloqueada: bool,
    ) -> bool:
        etiqueta = self._undo_line_desc(valuation_line_id)
        snap_line = self._undo_snap_line(valuation_line_id)
        metodo = (
            self._repository.bloquear_linea if bloqueada
            else self._repository.desbloquear_linea
        )
        ok = metodo(document_id=document_id, valuation_line_id=valuation_line_id)
        if ok:
            accion = "bloquear" if bloqueada else "desbloquear"
            self._repository.record_undo(
                document_id=document_id,
                action=accion,
                description=(
                    f"{accion.capitalize()} línea · {etiqueta} "
                    f"({self._repository.doc_label(document_id=document_id)})"
                ),
                restore=[snap_line],
            )
        return ok

    def asignar_almacen_linea(
        self,
        *,
        document_id: str,
        valuation_line_id: int,
    ) -> bool:
        """(F-051 R14, R15, R18) «Almacén (sin partida)» en UNA línea:
        partida final vacía y marca ``almacen_elegido``; la fila Sigrid
        sigue Sigrid. Una entrada de deshacer con su estado anterior.
        ``False`` si la línea no es del documento (R23)."""
        etiqueta = self._undo_line_desc(valuation_line_id)
        snap_line = self._undo_snap_line(valuation_line_id)
        tocadas = self._repository.asignar_almacen(
            document_id=document_id,
            valuation_line_ids=[valuation_line_id],
        )
        if not tocadas:
            return False
        self._repository.record_undo(
            document_id=document_id,
            action="almacen",
            description=(
                f"Almacén · {etiqueta} "
                f"({self._repository.doc_label(document_id=document_id)})"
            ),
            restore=[snap_line],
        )
        return True

    def asignar_almacen_todas_con_saltos(
        self, *, document_id: str,
    ) -> ResultadoAlmacenTodas:
        """(F-065 R14) Como :meth:`asignar_almacen_todas`, diciendo cuántas
        filas se saltó por estar guardadas (bloqueadas)."""
        saltadas = sum(
            1 for snap in self._repository.snapshot_lineas_valoracion(
                document_id=document_id,
            )
            if snap["values"].get("bloqueada")
        )
        return ResultadoAlmacenTodas(
            tocadas=self.asignar_almacen_todas(document_id=document_id),
            saltadas=saltadas,
        )

    def asignar_almacen_todas(self, *, document_id: str) -> int:
        """(F-051 R16, R18) «Almacén a todas las líneas»: todas las líneas
        de la valoración del documento, también las que tenían partida,
        en una transacción. UNA entrada de deshacer que restaura todas las
        tocadas. Devuelve cuántas se tocaron (0 = ninguna, R23)."""
        snaps = self._repository.snapshot_lineas_valoracion(
            document_id=document_id,
        )
        tocadas = self._repository.asignar_almacen(
            document_id=document_id,
            valuation_line_ids=None,
        )
        if not tocadas:
            return 0
        ids_tocados = set(tocadas)
        self._repository.record_undo(
            document_id=document_id,
            action="almacen",
            description=(
                f"Almacén a todas las líneas ({len(tocadas)}) "
                f"({self._repository.doc_label(document_id=document_id)})"
            ),
            restore=[
                snap for snap in snaps
                if snap["values"].get("id") in ids_tocados
            ],
        )
        return len(tocadas)

    def remove_line_conciliacion(
        self,
        *,
        document_id: str,
        valuation_line_id: int,
    ) -> bool:
        etiqueta = self._undo_line_desc(valuation_line_id)
        brief = self._repository.line_brief(
            valuation_line_id=valuation_line_id,
        )
        snap_line = self._undo_snap_line(valuation_line_id)
        snap_derived = None
        if brief and brief.get("derived_contrato_line_id") is not None:
            snap_derived = self._repository.snapshot_row(
                table="contrato_lines_derived",
                row_id=brief["derived_contrato_line_id"],
            )
        snap_val = self._undo_snap_valuation(document_id)
        ok = self._repository.remove_line_valuation(
            document_id=document_id,
            valuation_line_id=valuation_line_id,
        )
        if ok:
            self._repository.record_undo(
                document_id=document_id,
                action="linea_borrar",
                description=(
                    f"Borrar línea · {etiqueta} "
                    f"({self._repository.doc_label(document_id=document_id)})"
                ),
                reinsert=[snap_derived, snap_line],
                restore=[snap_val],
            )
        return ok

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
        etiqueta = self._undo_line_desc(valuation_line_id)
        antes = self._repository.line_brief(
            valuation_line_id=valuation_line_id,
        )
        snap_line = self._undo_snap_line(valuation_line_id)
        snap_derived_previa = None
        if antes and antes.get("derived_contrato_line_id") is not None:
            # modo contract_line borra la derivada previa: hay que poder
            # reinsertarla al deshacer.
            snap_derived_previa = self._repository.snapshot_row(
                table="contrato_lines_derived",
                row_id=antes["derived_contrato_line_id"],
            )
        snap_val = self._undo_snap_valuation(document_id)
        ok = self._repository.set_line_conciliacion(
            document_id=document_id,
            valuation_line_id=valuation_line_id,
            mode=mode,
            matched_contrato_line_id=matched_contrato_line_id,
            descripcion=descripcion,
            precio_unitario=precio_unitario,
        )
        if ok:
            # modo 'nueva' crea una derivada NUEVA: al deshacer hay que
            # borrarla (se detecta releyendo la línea tras la mutación).
            delete_created = []
            despues = self._repository.line_brief(
                valuation_line_id=valuation_line_id,
            )
            derivada_antes = (
                antes.get("derived_contrato_line_id") if antes else None
            )
            derivada_despues = (
                despues.get("derived_contrato_line_id") if despues else None
            )
            if (
                derivada_despues is not None
                and derivada_despues != derivada_antes
            ):
                delete_created.append({
                    "table": "contrato_lines_derived",
                    "id": derivada_despues,
                })
            self._repository.record_undo(
                document_id=document_id,
                action="conciliar",
                description=(
                    f"Cambiar conciliación · {etiqueta} "
                    f"({self._repository.doc_label(document_id=document_id)})"
                ),
                restore=[snap_line, snap_val],
                reinsert=[snap_derived_previa],
                delete_created=delete_created,
            )
        return ok

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
        snap_val = self._undo_snap_valuation(document_id)
        ok = self._repository.add_conciliacion_for_merge_line(
            document_id=document_id,
            merge_line_id=merge_line_id,
            mode=mode,
            matched_contrato_line_id=matched_contrato_line_id,
            precio_unitario=precio_unitario,
            descripcion=descripcion,
        )
        if ok:
            creada = self._repository.latest_valuation_line_for_merge(
                merge_line_id=merge_line_id,
            )
            delete_created = []
            if creada:
                if creada.get("derived_contrato_line_id") is not None:
                    delete_created.append({
                        "table": "contrato_lines_derived",
                        "id": creada["derived_contrato_line_id"],
                    })
                delete_created.append({
                    "table": "albaran_line_valuations",
                    "id": creada["id"],
                })
            self._repository.record_undo(
                document_id=document_id,
                action="linea_add",
                description=(
                    ("Copiar → Nueva" if mode == "nueva" else "Casar línea")
                    + f" · línea albarán {merge_line_id} "
                    + f"({self._repository.doc_label(document_id=document_id)})"
                ),
                restore=[snap_val],
                delete_created=delete_created,
            )
        return ok

    def add_standalone_valuation_line(
        self,
        *,
        document_id: str,
    ) -> int | None:
        new_id = self._repository.add_standalone_valuation_line(
            document_id=document_id,
        )
        if new_id is not None:
            brief = self._repository.line_brief(valuation_line_id=new_id)
            delete_created = []
            if brief and brief.get("derived_contrato_line_id") is not None:
                delete_created.append({
                    "table": "contrato_lines_derived",
                    "id": brief["derived_contrato_line_id"],
                })
            delete_created.append({
                "table": "albaran_line_valuations", "id": new_id,
            })
            self._repository.record_undo(
                document_id=document_id,
                action="linea_add",
                description=(
                    "Añadir línea "
                    f"({self._repository.doc_label(document_id=document_id)})"
                ),
                delete_created=delete_created,
            )
        return new_id

    def add_valuation_lines_from_contrato(
        self,
        *,
        document_id: str,
        lineas: list[tuple[int, float]],
    ) -> int:
        """Trae líneas del contrato a la tabla (F-065 R23): una fila Contrato
        por cada ``(línea de contrato, cantidad)``, ya válida para sv9; con
        su entrada de deshacer. Devuelve cuántas se crearon."""
        snap_val = self._undo_snap_valuation(document_id)
        creadas = self._repository.add_valuation_lines_from_contrato(
            document_id=document_id,
            lineas=lineas,
        )
        if creadas:
            self._repository.record_undo(
                document_id=document_id,
                action="linea_add",
                description=(
                    f"Traer {len(creadas)} línea(s) de contrato "
                    f"({self._repository.doc_label(document_id=document_id)})"
                ),
                restore=[snap_val],
                delete_created=[
                    {"table": "albaran_line_valuations", "id": i}
                    for i in creadas
                ],
            )
        return len(creadas)

    def dividir_linea(
        self,
        *,
        document_id: str,
        valuation_line_id: int,
        partes: list[ParteDivision],
    ) -> DivisionHecha | None:
        """(F-065 R29–R34) Divide una fila en ``partes`` con UNA entrada de
        deshacer: borra las partes y las derivadas creadas y devuelve la
        original (con su derivada, si era Nueva) y el total a como estaban.
        ``None`` si la fila no es del documento.

        (F-098 R25) La partida de cada parte se guarda como el cod de la lista
        de la obra si casa; la lista se pide solo si alguna parte trae una."""
        if any(p.codigo_partida for p in partes):
            lista = self._lista_del_documento(document_id)
            partes = [
                p.model_copy(update={"codigo_partida": traducir_partida(lista, p.codigo_partida)})
                if p.codigo_partida else p
                for p in partes
            ]
        etiqueta = self._undo_line_desc(valuation_line_id)
        snap_line = self._undo_snap_line(valuation_line_id)
        derivada = (snap_line or {}).get("values", {}).get("derived_contrato_line_id")
        snap_derivada = (
            self._repository.snapshot_row(table="contrato_lines_derived", row_id=derivada)
            if derivada is not None else None
        )
        snap_val = self._undo_snap_valuation(document_id)
        hecha = self._repository.dividir_linea(
            document_id=document_id,
            valuation_line_id=valuation_line_id,
            partes=partes,
        )
        if hecha is not None:
            self._repository.record_undo(
                document_id=document_id,
                action="dividir",
                description=(
                    f"Dividir en {len(partes)} · {etiqueta} "
                    f"({self._repository.doc_label(document_id=document_id)})"
                ),
                restore=[snap_line, snap_derivada, snap_val],
                delete_created=(
                    [{"table": "albaran_line_valuations", "id": i} for i in hecha.partes]
                    + [{"table": "contrato_lines_derived", "id": i} for i in hecha.derivadas]
                ),
            )
        return hecha

    # ------------------------------------------------------------------ #
    # F-053 · Producto Sigrid de las líneas sin vincular (R40-R43)
    # ------------------------------------------------------------------ #
    def productos_sigrid(
        self, document_id: str, clasificacion: object,
    ) -> dict[int, ProductoLinea]:
        """Producto de cada línea valorada, por ``valuation_line_id`` (R40):
        vinculada, el de su línea de contrato (R43, se ignora el elegido);
        sin vincular, el elegido o el por defecto de su familia con el mismo
        mapeo y la misma función que sv9 (R38). Con DESDE vacía, nada (R3).
        ``clasificacion``: la del documento (``familia`` y ``mixto``)."""
        if not self._config_alta.activa:
            return {}
        productos: dict[int, ProductoLinea] = {}
        for fila in self._repository.lineas_producto_sigrid(document_id):
            vinculada = es_linea_vinculada(
                matched_contrato_line_id=fila["matched_contrato_line_id"],
                derived_contrato_line_id=fila["derived_contrato_line_id"],
                sigrid_ide=fila["sigrid_ide"],
                contrato_linea=fila["contrato_linea"],
                contrato_valoracion=fila["contrato_valoracion"],
            )
            elegido = (fila["producto_sigrid"] or "").strip() or None
            if vinculada:
                codigo, por_defecto, elegido = fila["codigo_producto"], False, None
                defecto = None
            else:
                familia = _familia_de_la_linea(fila["contexto_linea_json"])
                mapeo = self._config_alta.mapeo
                codigo = producto_efectivo(elegido, familia, clasificacion, mapeo)
                defecto = producto_efectivo(None, familia, clasificacion, mapeo)
                por_defecto = elegido is None
            productos[int(fila["id"])] = ProductoLinea(
                valuation_line_id=int(fila["id"]),
                vinculada=vinculada,
                a_registrar=es_linea_a_registrar(fila["importe_calculado"]),
                elegido=elegido,
                codigo=codigo,
                defecto=defecto,
                por_defecto=por_defecto,
            )
        return productos

    def elegir_producto_sigrid(
        self,
        *,
        document_id: str,
        valuation_line_id: int,
        producto: str | None,
    ) -> str:
        """R41: guarda el producto elegido en una sin vincular (``None`` o
        vacío = por defecto) con su entrada de deshacer. Devuelve
        ``guardado``; o, sin cambiar nada, ``apagada`` (DESDE vacía, R3),
        ``no_admitido`` (no está en el mapeo), ``linea_ajena`` o
        ``vinculada``. Con alta bloqueante, ``AlbaranBloqueadoError`` (R25)."""
        if not self._config_alta.activa:
            return "apagada"
        codigo = (producto or "").strip() or None
        if codigo is not None and codigo not in self._config_alta.admitidos:
            return "no_admitido"
        etiqueta = self._undo_line_desc(valuation_line_id)
        snap_line = self._undo_snap_line(valuation_line_id)
        resultado = self._repository.guardar_producto_sigrid(
            document_id=document_id,
            valuation_line_id=valuation_line_id,
            producto=codigo,
        )
        if resultado == "guardado":
            self._repository.record_undo(
                document_id=document_id,
                action="producto",
                description=(
                    f"Producto Sigrid {codigo or 'por defecto'} · {etiqueta} "
                    f"({self._repository.doc_label(document_id=document_id)})"
                ),
                restore=[snap_line],
            )
        return resultado

    # ------------------------------------------------------------------ #
    # F-053 · Alta en Sigrid desde la ficha (R25, R28, R30)
    # ------------------------------------------------------------------ #
    def comprobar_desbloqueado(self, document_id: str) -> None:
        """R25 para lo que solo PUBLICA (revalorar, volver a buscar
        contratos): mira el alta sin cerrojo (design §11) y lanza
        :class:`AlbaranBloqueadoError` si es bloqueante."""
        alta = self._repository.leer_alta_sigrid(document_id)
        if alta is not None and alta.bloqueante:
            raise AlbaranBloqueadoError(document_id, alta.estado, alta.sigrid_cod)

    def comprobar_editable(self, document_id: str) -> None:
        """F-065 R4 para lo que solo PUBLICA (revalorar, volver a buscar
        contratos): con alta bloqueante, :class:`AlbaranBloqueadoError` (F-053
        R25); con el albarán aprobado, :class:`AlbaranAprobadoError`. Sin
        cerrojo, como :meth:`comprobar_desbloqueado`."""
        self.comprobar_desbloqueado(document_id)
        estado = self._repository.estado_aprobacion(document_id)
        if estado is not None and estado["approved"]:
            raise AlbaranAprobadoError(document_id)

    def puede_solicitar_alta(
        self, document_id: str, *, ahora: datetime | None = None,
    ) -> bool:
        """R30: ¿se ofrece «Solicitar alta en Sigrid» para el documento?"""
        if not self._config_alta.activa:
            return False
        estado = self._repository.estado_aprobacion(document_id)
        if estado is None:
            return False
        return puede_solicitar_alta(
            aprobado=estado["approved"],
            activo=estado["is_active"],
            approved_at_utc=estado["approved_at_utc"],
            alta=self._repository.leer_alta_sigrid(document_id),
            config=self._config_alta,
            ahora=ahora or datetime.now(UTC),
        )

    def fase_alta(
        self, document_id: str, *, ahora: datetime | None = None,
    ) -> str | None:
        """F-077 R14, R18: fase del panel del alta. Solo lectura (estado de
        aprobación del merge y alta, sin cerrojo; R20). Feature apagada =>
        ``resultado`` sin leer nada; documento inexistente => ``None``."""
        if not self._config_alta.activa:
            return FASE_RESULTADO
        estado = self._repository.estado_aprobacion(document_id)
        if estado is None:
            return None
        return fase_alta(
            aprobado=estado["approved"],
            activo=estado["is_active"],
            approved_at_utc=estado["approved_at_utc"],
            alta=self._repository.leer_alta_sigrid(document_id),
            config=self._config_alta,
            ahora=ahora or datetime.now(UTC),
        )

    def solicitar_alta_sigrid(
        self,
        *,
        document_id: str,
        solicitado_por: str | None,
        ahora: datetime | None = None,
    ) -> str:
        """R30: publica ``accion="alta"`` solo cuando procede. Devuelve
        ``pedida``, ``no_publicada``, ``no_procede`` o ``apagada`` (R3)."""
        if not self._config_alta.activa:
            return "apagada"
        if not self.puede_solicitar_alta(document_id, ahora=ahora):
            return "no_procede"
        return self._publicar_feedback(document_id, "alta", solicitado_por)

    def puede_reintentar_adjunto(self, document_id: str) -> bool:
        """R30 (v8, O1 = a): ¿se ofrece «Reintentar adjunto»? Alta
        ``registrado`` en ``real`` con el PDF sin colgar."""
        if not self._config_alta.activa:
            return False
        estado = self._repository.estado_aprobacion(document_id)
        if estado is None:
            return False
        return puede_reintentar_adjunto(
            aprobado=estado["approved"],
            activo=estado["is_active"],
            approved_at_utc=estado["approved_at_utc"],
            alta=self._repository.leer_alta_sigrid(document_id),
            config=self._config_alta,
        )

    def reintentar_adjunto_sigrid(
        self, *, document_id: str, solicitado_por: str | None,
    ) -> str:
        """R30/R23: publica ``accion="alta"`` (sv9 solo reintenta el adjunto)
        cuando procede. No escribe en BBDD: R25 no la bloquea. Devuelve
        ``pedida``, ``no_publicada``, ``no_procede`` o ``apagada``."""
        if not self._config_alta.activa:
            return "apagada"
        if not self.puede_reintentar_adjunto(document_id):
            return "no_procede"
        return self._publicar_feedback(document_id, "alta", solicitado_por)

    def verificar_anulacion_sigrid(
        self, *, document_id: str, solicitado_por: str | None,
    ) -> str:
        """R28: «Ya lo he anulado en Sigrid» publica
        ``accion="verificar_anulacion"`` solo con un alta ``registrado``;
        quien decide si pasa a ``anulado`` es sv9 (lo busca en Sigrid)."""
        if not self._config_alta.activa:
            return "apagada"
        alta = self._repository.leer_alta_sigrid(document_id)
        if alta is None or alta.estado != "registrado":
            return "no_procede"
        return self._publicar_feedback(document_id, "verificar_anulacion", solicitado_por)

    def _publicar_feedback(
        self, document_id: str, accion: str, solicitado_por: str | None,
    ) -> str:
        if self._orchestrator is None:
            return "no_publicada"
        try:
            publicado = self._orchestrator.solicitar_alta_sigrid(
                document_id=document_id, accion=accion, solicitado_por=solicitado_por,
            )
        except Exception:  # noqa: BLE001 — best-effort: se avisa al revisor
            logger.exception(
                "[alta-sigrid][%s] fallo publicando document_id=%s", accion, document_id,
            )
            publicado = False
        return "pedida" if publicado else "no_publicada"

    def list_trash_document_ids(self) -> list[str]:
        """Ids de los albaranes en la papelera (para vaciarla)."""
        return self._repository.list_trash_document_ids()

    # ------------------------------------------------------------------ #
    # DESHACER (jul 2026): los ganchos viven AQUÍ (snapshot antes de
    # Alcance POR ALBARÁN (jul 2026): cada entrada se sella con su
    # document_id y listar/deshacer se filtra por él.
    # delegar en el repo, registro después solo si la mutación fue bien)
    # para no tocar la lógica interna de los métodos mutadores. El motor
    # (tabla undo_log, aplicar restore/reinsert/delete_created) está en
    # el repositorio. Ver nota de no-atomicidad en el repositorio.
    # ------------------------------------------------------------------ #
    def list_undo(
        self, *, document_id: str, limit: int = 15,
    ) -> list[dict]:
        return self._repository.list_undo(
            document_id=document_id, limit=limit,
        )

    def undo_last(self, *, document_id: str) -> dict:
        return self._repository.undo_last(document_id=document_id)

    def _undo_snap_line(self, valuation_line_id: int) -> dict | None:
        return self._repository.snapshot_row(
            table="albaran_line_valuations", row_id=valuation_line_id,
        )

    def _undo_snap_valuation(self, document_id: str) -> dict | None:
        vid = self._repository.valuation_header_id(document_id=document_id)
        if vid is None:
            return None
        return self._repository.snapshot_row(
            table="albaran_valuations", row_id=vid,
        )

    def _lista_del_documento(self, document_id: str) -> ListaPartidasObra | None:
        """(F-098) La lista de partidas de la obra del merge, o ``None`` (sin
        puerto, sin obra o sin lista)."""
        if self._partidas is None:
            return None
        _cif, obra = self._repository.get_merge_cif_and_obra(document_id=document_id)
        return self._partidas.lista(obra) if obra else None

    def _traducir(self, document_id: str, partida: str) -> str | None:
        return traducir_partida(self._lista_del_documento(document_id), partida)

    def _undo_line_desc(self, valuation_line_id: int) -> str:
        b = self._repository.line_brief(valuation_line_id=valuation_line_id)
        if not b:
            return f"línea {valuation_line_id}"
        partida = b.get("codigo_partida_final") or ""
        descr = (b.get("descripcion_linea") or "").strip()
        if len(descr) > 40:
            descr = descr[:37] + "…"
        etiqueta = " ".join(x for x in (partida, descr) if x)
        return etiqueta or f"línea {valuation_line_id}"

    def unapprove_document(self, *, document_id: str) -> None:
        self._repository.set_approved(
            document_id=document_id,
            approved=False,
            approved_by=None,
        )
