# tests/test_f053_pdf.py
"""F-053 · T15 · PDF del albarán desde SharePoint (``pdf_sharepoint``).

Se baja por la ruta relativa del merge (``sharepoint_relative_path``) con el
cliente Graph común (``ruesma_comun.sharepoint.GraphSharePointClient``). Sin
ruta, ``PdfNoDisponibleError`` (el servicio deja el adjunto en error, R23).

Sin red: un descargador falso y, para la subclase de Graph, un token en bruto y
``httpx.MockTransport``.
"""
from __future__ import annotations

import httpx
import pytest

from domain.ports.pdf_port import PdfNoDisponibleError
from infrastructure.sharepoint.pdf_sharepoint import (
    PdfSharePoint,
    SharePointAlbaranDownloader,
)
from tests.f053_datos import datos, sin_vincular

PDF = b"%PDF-1.4 de mentira"


class DescargadorFalso:
    def __init__(self, contenido=PDF, falla=False):
        self.contenido = contenido
        self.falla = falla
        self.rutas: list[str] = []

    def descargar_por_ruta(self, relative_path: str) -> bytes:
        self.rutas.append(relative_path)
        if self.falla:
            raise RuntimeError("Graph download 404")
        return self.contenido


def test_f053_pdf_se_baja_por_la_ruta_relativa_del_merge():
    descargador = DescargadorFalso()
    contenido = PdfSharePoint(descargador).descargar(
        datos(sin_vincular(1), sharepoint_relative_path="albaranes/2026/10/alb 1.pdf"),
    )
    assert contenido == PDF
    assert descargador.rutas == ["albaranes/2026/10/alb 1.pdf"]


@pytest.mark.parametrize("ruta", [None, "", "   "])
def test_f053_pdf_sin_ruta_no_hay_pdf(ruta):
    descargador = DescargadorFalso()
    with pytest.raises(PdfNoDisponibleError):
        PdfSharePoint(descargador).descargar(datos(sin_vincular(1), sharepoint_relative_path=ruta))
    assert descargador.rutas == []


def test_f053_pdf_vacio_no_vale():
    with pytest.raises(PdfNoDisponibleError):
        PdfSharePoint(DescargadorFalso(contenido=b"")).descargar(datos(sin_vincular(1)))


def test_f053_pdf_fallo_de_graph_se_propaga_al_servicio():
    with pytest.raises(RuntimeError):
        PdfSharePoint(DescargadorFalso(falla=True)).descargar(datos(sin_vincular(1)))


def test_f053_pdf_subclase_de_graph_descarga_del_drive():
    peticiones: list[httpx.Request] = []

    def graph(request: httpx.Request) -> httpx.Response:
        peticiones.append(request)
        return httpx.Response(200, content=PDF, headers={"Content-Type": "application/pdf"})

    descargador = SharePointAlbaranDownloader(
        graph_key="token-en-bruto-de-mentira", timeout_s=5, mode="drive_id", hostname=None,
        site_path=None, drive_name="Documentos", drive_id="drive-1",
        transport=httpx.MockTransport(graph),
    )
    assert descargador.descargar_por_ruta("albaranes/2026/x.pdf") == PDF
    (peticion,) = peticiones
    assert peticion.url.path == "/v1.0/drives/drive-1/root:/albaranes/2026/x.pdf:/content"
    assert peticion.headers["Authorization"] == "Bearer token-en-bruto-de-mentira"
