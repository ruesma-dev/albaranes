# tests/test_humo_sharepoint.py
"""Test de humo del cliente SharePoint común contra un Graph SIMULADO.

No toca el tenant: inyecta un ``httpx.MockTransport`` por el parámetro
``transport`` del cliente base y un token directo en ``graph_key`` (el
GraphTokenProvider devuelve el token tal cual si no es un JSON de
credenciales). Verifica que la mecánica extraída produce EXACTAMENTE las
mismas llamadas Graph (método + URL) que tenían los adaptadores de sv3
(subida) y sv5 (descarga) — lo único que garantiza no romper la
integración real.

Ejecutar:  pytest tests/test_humo_sharepoint.py -v
"""
from __future__ import annotations

import json
import re

import httpx
import pytest

from ruesma_comun.sharepoint import GraphSharePointClient

GRAPH = "https://graph.microsoft.com/v1.0"
PDF = b"%PDF-1.4 contenido de prueba"


class GraphSimulado:
    """Handler de MockTransport que emula los endpoints Graph usados."""

    def __init__(self) -> None:
        self.carpetas_creadas: list[str] = []
        self.subidas: list[str] = []
        self.peticiones: list[str] = []

    def __call__(self, request: httpx.Request) -> httpx.Response:
        ruta = request.url.path
        metodo = request.method
        self.peticiones.append(f"{metodo} {ruta}")
        assert request.headers.get("Authorization") == "Bearer token-directo"

        if metodo == "GET" and re.match(r"^/v1\.0/sites/[^/]+:/", ruta):
            return httpx.Response(200, json={"id": "site-1"})
        if metodo == "GET" and ruta == "/v1.0/sites/site-1/drives":
            return httpx.Response(
                200,
                json={"value": [
                    {"name": "Otra", "id": "drive-otro"},
                    {"name": "Documentos", "id": "drive-1"},
                ]},
            )
        if metodo == "GET" and ruta.startswith("/v1.0/shares/"):
            return httpx.Response(
                200,
                json={
                    "id": "folder-base",
                    "folder": {},
                    "name": "albaranes",
                    "webUrl": "https://sp/albaranes",
                    "parentReference": {"driveId": "drive-9"},
                },
            )
        if metodo == "GET" and ruta.endswith("/children"):
            return httpx.Response(200, json={"value": []})
        if metodo == "POST" and ruta.endswith("/children"):
            nombre = json.loads(request.content.decode("utf-8"))["name"]
            self.carpetas_creadas.append(nombre)
            return httpx.Response(201, json={"id": f"f-{nombre}"})
        if metodo == "PUT" and ruta.endswith(":/content"):
            self.subidas.append(str(request.url))
            return httpx.Response(201, json={"id": "item-1", "webUrl": "https://sp/item-1"})
        if metodo == "GET" and ruta.endswith(":/content"):
            return httpx.Response(
                200, content=PDF, headers={"Content-Type": "application/pdf"}
            )
        if metodo == "POST" and ruta.endswith("/createLink"):
            return httpx.Response(201, json={"link": {"webUrl": "https://sp/share-1"}})
        return httpx.Response(404, json={"error": f"sin ruta: {metodo} {ruta}"})


def _cliente(simulado: GraphSimulado, **kwargs) -> GraphSharePointClient:
    base = dict(
        graph_key="token-directo",
        timeout_s=10,
        mode="drive_id",
        hostname=None,
        site_path=None,
        drive_name="Documentos",
        drive_id="drive-7",
        transport=httpx.MockTransport(simulado),
    )
    base.update(kwargs)
    return GraphSharePointClient(**base)


def test_site_path_resuelve_drive_por_nombre_y_cachea() -> None:
    sim = GraphSimulado()
    cliente = _cliente(
        sim,
        mode="site_path",
        hostname="ruesma.sharepoint.com",
        site_path="/sites/albaranes",
        drive_id=None,
    )
    assert cliente._resolve_drive_id_all_modes() == "drive-1"
    assert sim.peticiones == [
        "GET /v1.0/sites/ruesma.sharepoint.com:/sites/albaranes",
        "GET /v1.0/sites/site-1/drives",
    ]
    # 2ª resolución: el drive_id ya está cacheado, no vuelve a llamar.
    n = len(sim.peticiones)
    assert cliente._resolve_drive_id_all_modes() == "drive-1"
    assert len(sim.peticiones) == n


def test_folder_url_resuelve_drive_de_la_carpeta_compartida() -> None:
    sim = GraphSimulado()
    cliente = _cliente(
        sim,
        mode="folder_url",
        drive_id=None,
        folder_url="https://ruesma.sharepoint.com/sites/x/Shared/albaranes",
    )
    assert cliente._resolve_drive_id_all_modes() == "drive-9"
    base = cliente._resolve_folder_from_share_url()
    assert base.item_id == "folder-base"
    assert base.folder_name == "albaranes"


def test_ensure_folder_path_crea_jerarquia() -> None:
    sim = GraphSimulado()
    cliente = _cliente(sim)
    ultimo = cliente._ensure_folder_path_from_root(
        drive_id="drive-7", folder_path="albaranes/2026/03"
    )
    assert sim.carpetas_creadas == ["albaranes", "2026", "03"]
    assert ultimo == "f-03"


def test_subida_por_path_relativo_url_y_contenido() -> None:
    sim = GraphSimulado()
    cliente = _cliente(sim)
    res = cliente._upload_file_by_relative_path(
        drive_id="drive-7",
        relative_path="albaranes/2026/03/a.pdf",
        mime_type="application/pdf",
        file_bytes=PDF,
    )
    assert res["id"] == "item-1"
    assert sim.subidas == [
        f"{GRAPH}/drives/drive-7/root:/albaranes/2026/03/a.pdf:/content"
    ]


def test_descarga_por_path_relativo() -> None:
    sim = GraphSimulado()
    cliente = _cliente(sim)
    contenido, content_type = cliente._download_bytes_by_relative_path(
        drive_id="drive-7",
        relative_path="albaranes/2026/03/contratos/C-1_9_foo.pdf",
    )
    assert contenido == PDF
    assert content_type == "application/pdf"
    assert sim.peticiones[-1] == (
        "GET /v1.0/drives/drive-7/root:/"
        "albaranes/2026/03/contratos/C-1_9_foo.pdf:/content"
    )


def test_descarga_vacia_lanza() -> None:
    def vacia(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, content=b"")

    cliente = GraphSharePointClient(
        graph_key="token-directo",
        timeout_s=10,
        mode="drive_id",
        hostname=None,
        site_path=None,
        drive_name="Documentos",
        drive_id="d",
        transport=httpx.MockTransport(vacia),
    )
    with pytest.raises(RuntimeError, match="binario vacío"):
        cliente._download_bytes_by_relative_path(drive_id="d", relative_path="a/b.pdf")


def test_validacion_de_modos() -> None:
    comun = dict(
        graph_key="t", timeout_s=5, hostname=None, site_path=None,
        drive_name="D", drive_id=None,
    )
    with pytest.raises(RuntimeError, match="SHAREPOINT_DRIVE_ID"):
        GraphSharePointClient(mode="drive_id", **comun)
    with pytest.raises(RuntimeError, match="SHAREPOINT_FOLDER_URL"):
        GraphSharePointClient(mode="folder_url", **comun)
    with pytest.raises(RuntimeError, match="SHAREPOINT_HOSTNAME"):
        GraphSharePointClient(mode="site_path", **comun)
