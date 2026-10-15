# infrastructure/sharepoint/pdf_sharepoint.py
"""PDF del albarán desde SharePoint (F-053, R22).

sv3 sube el PDF de cada albarán a SharePoint y guarda su ruta dentro del drive
en ``albaran_documents_merge.sharepoint_relative_path``. sv9 lo baja por esa
ruta con el cliente Graph común (``ruesma_comun.sharepoint``), igual que sv5
baja el PDF del contrato, y lo adjunta en Sigrid con ``concepto-grafico``.

Sin ruta (o con un fichero vacío) no hay PDF: ``PdfNoDisponibleError``, y el
servicio deja el alta ``registrado`` con el adjunto en error (R23). El PDF no
se loguea (R35).
"""
from __future__ import annotations

import logging
from typing import Protocol

import httpx
from ruesma_comun.sharepoint import GraphSharePointClient, SharePointMode

from domain.models.alta_models import DatosAlta
from domain.ports.pdf_port import PdfAlbaranPort, PdfNoDisponibleError

logger = logging.getLogger(__name__)


class DescargadorPorRuta(Protocol):
    def descargar_por_ruta(self, relative_path: str) -> bytes: ...


class SharePointAlbaranDownloader(GraphSharePointClient):
    """Mecánica Graph común + la única operación que necesita sv9."""

    def __init__(
        self,
        *,
        graph_key: str,
        timeout_s: int,
        mode: SharePointMode,
        hostname: str | None,
        site_path: str | None,
        drive_name: str,
        drive_id: str | None,
        folder_url: str | None = None,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        super().__init__(
            graph_key=graph_key, timeout_s=timeout_s, mode=mode, hostname=hostname,
            site_path=site_path, drive_name=drive_name, drive_id=drive_id,
            folder_url=folder_url, transport=transport,
        )

    def descargar_por_ruta(self, relative_path: str) -> bytes:
        drive_id = self._resolve_drive_id_all_modes()
        contenido, _tipo = self._download_bytes_by_relative_path(
            drive_id=drive_id, relative_path=relative_path,
        )
        return contenido


class PdfSharePoint(PdfAlbaranPort):
    def __init__(self, descargador: DescargadorPorRuta) -> None:
        self._descargador = descargador

    def descargar(self, datos: DatosAlta) -> bytes:
        ruta = (datos.cabecera.sharepoint_relative_path or "").strip()
        if not ruta:
            raise PdfNoDisponibleError(
                f"el documento {datos.cabecera.document_id} no tiene ruta de SharePoint",
            )
        contenido = self._descargador.descargar_por_ruta(ruta)
        if not contenido:
            raise PdfNoDisponibleError(f"PDF vacío en {ruta}")
        logger.info("[sv9-alta][pdf] document_id=%s bytes=%s", datos.cabecera.document_id,
                    len(contenido))
        return contenido
