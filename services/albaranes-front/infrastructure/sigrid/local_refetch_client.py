# infrastructure/sigrid/local_refetch_client.py
"""Re-fetch de contratos LOCAL y SÍNCRONO para el modo ``solo-front``.

Implementa el puerto ``ContratoRefetchClient`` SIN pasar por colas ni por
el sv3: lee (CIF, obra) del merge, consulta Sigrid DIRECTAMENTE (cabecera
+ líneas vía ``SigridApiContratoClient``) y PERSISTE los contratos en
BBDD (``replace_contratos_and_select``). No descarga PDFs (eso es del
sv3 en producción).

Se cablea como fallback en ``build_app`` SOLO cuando NO hay colas
(publicador NULO) y SÍ hay credenciales Sigrid. Con colas se mantiene el
``ColasRefetchClient`` (asíncrono → sv3), que es el camino de producción.

F-052 R22: deja el mismo rastro de la búsqueda que sv3 (R21) en las
columnas ``contratos_busqueda_*`` del merge —``sin_datos``, ``error``,
``ninguno`` o ``encontrados``, con CIF y obra normalizados—, best-effort.
"""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from application.services.obra_code_normalizer import normalize_obra_code
from domain.models.contrato_refetch_models import ContratoRefetchOutcome
from domain.models.review_models import (
    BUSQUEDA_ENCONTRADOS,
    BUSQUEDA_ERROR,
    BUSQUEDA_NINGUNO,
    BUSQUEDA_SIN_DATOS,
)
from domain.ports.contrato_refetch_port import ContratoRefetchClient

if TYPE_CHECKING:  # evita import circular en runtime
    from infrastructure.database.review_repository import AlbaranReviewRepository
    from infrastructure.sigrid.sigrid_api_contrato_client import (
        SigridApiContratoClient,
    )

logger = logging.getLogger(__name__)

_LOG_PREFIX = "[contrato-refetch][local]"


class LocalContratoRefetchClient(ContratoRefetchClient):
    """Refetch síncrono local: Sigrid directo → persiste contratos+líneas."""

    def __init__(
        self,
        *,
        sigrid_client: "SigridApiContratoClient",
        repository: "AlbaranReviewRepository",
    ) -> None:
        self._client = sigrid_client
        self._repository = repository
        logger.info(
            "%s INSTANCIADO (fallback solo-front; Sigrid directo, sin sv3).",
            _LOG_PREFIX,
        )

    def refetch(self, *, document_id: str) -> ContratoRefetchOutcome:
        cif, obra_raw = self._repository.get_merge_cif_and_obra(
            document_id=document_id,
        )
        if cif is None and obra_raw is None:
            # Documento inexistente → KeyError (el endpoint lo mapea a 404).
            raise KeyError(document_id)

        cif_clean = (cif or "").strip().upper().replace(" ", "") or None
        obra_norm = normalize_obra_code(obra_raw)

        if not cif_clean or not obra_norm:
            faltan = []
            if not cif_clean:
                faltan.append("CIF del proveedor vacío")
            if not obra_norm:
                faltan.append(
                    f"código de obra inválido ({obra_raw!r}); debe ser 1-4 dígitos"
                )
            self._sellar(document_id, cif_clean, obra_norm, BUSQUEDA_SIN_DATOS)
            return ContratoRefetchOutcome(
                status="skipped_missing_data",
                count=0,
                selected_contrato_codigo=None,
                message=(
                    "No se consultó el ERP: "
                    + " y ".join(faltan)
                    + ". Corrige los datos del albarán y vuelve a buscar."
                ),
                cif=cif_clean,
                obra_codigo=obra_norm,
            )

        try:
            contratos = self._client.fetch_contratos(
                cif_proveedor=cif_clean,
                codigo_obra_normalizado=obra_norm,
            )
        except Exception as exc:  # noqa: BLE001
            logger.exception(
                "%s ERROR consultando Sigrid. document_id=%s",
                _LOG_PREFIX,
                document_id,
            )
            self._sellar(document_id, cif_clean, obra_norm, BUSQUEDA_ERROR)
            return ContratoRefetchOutcome(
                status="sigrid_error",
                count=0,
                selected_contrato_codigo=None,
                message=f"Error consultando Sigrid: {exc}",
                cif=cif_clean,
                obra_codigo=obra_norm,
            )

        try:
            selected = self._repository.replace_contratos_and_select(
                document_id=document_id,
                contratos=contratos,
            )
        except Exception:
            # Misma extensión de R21 que sv3: sin los contratos guardados,
            # ni «encontrados» ni «ninguno» serían verdad. El error sigue
            # subiendo al endpoint como antes de F-052.
            self._sellar(document_id, cif_clean, obra_norm, BUSQUEDA_ERROR)
            raise
        count = len(contratos)
        self._sellar(
            document_id,
            cif_clean,
            obra_norm,
            BUSQUEDA_ENCONTRADOS if count else BUSQUEDA_NINGUNO,
        )
        if count == 0:
            status = "no_results"
            message = (
                "Sigrid respondió sin contratos para esa combinación "
                "CIF + obra. Este albarán queda sin contrato."
            )
        elif count == 1:
            status = "found_single"
            message = "1 contrato encontrado y autoseleccionado."
        else:
            status = "found_multiple"
            message = (
                f"{count} contratos encontrados; elige uno en el desplegable."
            )

        logger.info(
            "%s document_id=%s outcome=%s count=%s selected=%s",
            _LOG_PREFIX,
            document_id,
            status,
            count,
            selected,
        )
        return ContratoRefetchOutcome(
            status=status,
            count=count,
            selected_contrato_codigo=selected,
            message=message,
            cif=cif_clean,
            obra_codigo=obra_norm,
        )

    def _sellar(
        self,
        document_id: str,
        cif: str | None,
        obra: str | None,
        resultado: str,
    ) -> None:
        """Rastro de la búsqueda (F-052 R22), best-effort: un fallo aquí se
        registra y no cambia el resultado del re-fetch."""
        try:
            self._repository.sellar_busqueda_contratos(
                document_id=document_id,
                cif=cif,
                obra=obra,
                resultado=resultado,
            )
        except Exception:  # best-effort: el re-fetch sigue su curso
            logger.exception(
                "%s no se pudo sellar el rastro de la búsqueda de contratos "
                "document_id=%s resultado=%s",
                _LOG_PREFIX,
                document_id,
                resultado,
            )
