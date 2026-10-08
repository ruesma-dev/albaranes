# application/services/review_service.py
from __future__ import annotations

import logging
from dataclasses import dataclass

from ruesma_comun.alta_sigrid import (
    es_linea_a_registrar,
    es_linea_vinculada,
    producto_efectivo,
)

from application.services.busqueda_contratos import (
    debe_relanzar_busqueda,
    hay_datos_para_buscar,
)
from domain.models.alta_sigrid_models import (
    ConfigAltaSigrid,
    ProductoLinea,
    ResultadoAprobacion,
)
from domain.models.contrato_refetch_models import ContratoRefetchOutcome
from domain.models.review_models import (
    VIEW_MODE_MERGE,
    DocumentDetailPayload,
    DocumentListFilters,
    MergeDocumentUpdatePayload,
    ObraResumenItem,
    PaginatedDocuments,
    ProveedorResumenItem,
)
from domain.ports.contrato_refetch_port import ContratoRefetchClient
from domain.ports.orchestrator_port import OrchestratorClient
from infrastructure.database.review_repository import AlbaranReviewRepository

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ResultadoGuardado:
    """«Guardar» del portal: el detalle guardado, la re-búsqueda de
    contratos relanzada (F-052 D4-A) y lo que pasó con la aprobación
    (F-053 R1–R4)."""

    detail: DocumentDetailPayload
    busqueda: ContratoRefetchOutcome | None
    aprobacion: ResultadoAprobacion


class ReviewService:
    def __init__(
        self,
        repository: AlbaranReviewRepository,
        default_reviewer: str | None,
        orchestrator: OrchestratorClient | None = None,
        config_alta: ConfigAltaSigrid | None = None,
    ) -> None:
        """``orchestrator`` y ``config_alta`` (F-053) son posicionales y
        opcionales: sin ellos, la feature está apagada (R3) y el servicio
        se comporta como antes."""
        self._repository = repository
        self._default_reviewer = (default_reviewer or "").strip() or None
        self._orchestrator = orchestrator
        self._config_alta = config_alta or ConfigAltaSigrid()

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
        return self._repository.get_document_detail(
            document_id,
            view_mode=view_mode,
        )

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
        # Historial: estado previo de cabecera, valoración y las líneas
        # que este guardado va a tocar.
        snaps = [
            self._repository.snapshot_row(
                table="albaran_documents_merge", row_id=document_id,
            ),
            self._undo_snap_valuation(document_id),
        ]
        for upd in (payload.valuation_line_updates or []):
            snaps.append(self._undo_snap_line(upd.valuation_line_id))
        # F-053: el repositorio comprueba el alta (R26), no deja aprobar lo
        # no valorado (R37) y dice si el documento PASÓ a aprobado en esta
        # transacción (R1, R2).
        detail, paso_a_aprobado = self._repository.update_document_y_transicion(
            document_id=document_id, payload=payload,
        )
        n_lineas = len(payload.valuation_line_updates or [])
        que = "cabecera" if not n_lineas else (
            f"cabecera + {n_lineas} línea(s)"
        )
        self._repository.record_undo(
            document_id=document_id,
            action="guardar",
            description=(
                f"Guardar {que} "
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
        return ResultadoGuardado(detail=detail, busqueda=busqueda, aprobacion=aprobacion)

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
        movidos = 0
        for document_id in document_ids:
            try:
                self._repository.soft_delete_document(
                    document_id=document_id,
                    deleted_by=deleted_by or self._default_reviewer,
                )
                movidos += 1
            except Exception:  # noqa: BLE001 - best-effort
                import logging
                logging.getLogger(__name__).exception(
                    "[bulk-delete] fallo con id=%s", document_id,
                )
        return movidos

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
        codigo_partida: str | None = None,
        descripcion: str | None = None,
        cantidad: float | None = None,
        unidad: str | None = None,
        precio_unitario: float | None = None,
        descuento: float | None = None,
        codigo_externo: str | None = None,
    ) -> bool:
        """Edición de la fila salmon (ver repositorio para la regla
        SIGRID→NUEVA al cambiar imputación/unidad/precio)."""
        etiqueta = self._undo_line_desc(valuation_line_id)
        snap_line = self._undo_snap_line(valuation_line_id)
        snap_val = self._undo_snap_valuation(document_id)
        ok = self._repository.update_line_conciliacion(
            document_id=document_id,
            valuation_line_id=valuation_line_id,
            codigo_partida=codigo_partida,
            descripcion=descripcion,
            cantidad=cantidad,
            unidad=unidad,
            precio_unitario=precio_unitario,
            descuento=descuento,
            codigo_externo=codigo_externo,
        )
        if ok:
            self._repository.record_undo(
                document_id=document_id,
                action="linea_edit",
                description=(
                    f"Editar línea · {etiqueta} "
                    f"({self._repository.doc_label(document_id=document_id)})"
                ),
                restore=[snap_line, snap_val],
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
        contrato_line_ids: list[int],
    ) -> int:
        """Trae líneas del contrato a la tabla salmón (jul 2026): crea
        una línea salmón ya casada por cada línea de contrato elegida.
        Devuelve cuántas se crearon."""
        creadas = self._repository.add_valuation_lines_from_contrato(
            document_id=document_id,
            contrato_line_ids=contrato_line_ids,
        )
        if creadas:
            self._repository.record_undo(
                document_id=document_id,
                action="linea_add",
                description=(
                    f"Traer {len(creadas)} línea(s) de contrato "
                    f"({self._repository.doc_label(document_id=document_id)})"
                ),
                delete_created=[
                    {"table": "albaran_line_valuations", "id": i}
                    for i in creadas
                ],
            )
        return len(creadas)

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
            else:
                codigo = producto_efectivo(
                    elegido, fila["tipo_familia"], clasificacion, self._config_alta.mapeo,
                )
                por_defecto = elegido is None
            productos[int(fila["id"])] = ProductoLinea(
                valuation_line_id=int(fila["id"]),
                vinculada=vinculada,
                a_registrar=es_linea_a_registrar(fila["importe_calculado"]),
                elegido=elegido,
                codigo=codigo,
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
