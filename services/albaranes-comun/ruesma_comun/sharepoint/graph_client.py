# ruesma_comun/sharepoint/graph_client.py
"""Núcleo común de acceso a SharePoint vía Microsoft Graph.

Resuelve la triplicación detectada en el análisis: sv3 (sube albaranes y
PDFs de contrato), sv4 (subía PDFs de contrato — hoy código muerto, lo
hace sv3) y sv5 (descarga el PDF de contrato para valorar) compartían un
mismo bloque de mecánica Graph casi idéntico (el propio sv4 lo admitía:
"Helpers idénticos al storage del servicio 3").

Este cliente base concentra esa mecánica:
  - configuración de los 3 modos (drive_id · folder_url · site_path),
  - resolución de site/drive,
  - cabeceras y codificación de sharing URL,
  - creación/garantía de carpetas,
  - subida por parent o por path relativo,
  - **descarga** por path relativo (lo que sv5 necesita para leer el
    contrato antes de valorar),
  - creación de enlace de compartición.

Cada servicio crea una subclase que añade SOLO su API de dominio (tipos
de retorno propios: ``StoredFile``, ``StoredContratoPdf``,
``DownloadedContratoPdf``). Las llamadas HTTP a Graph son byte a byte
las mismas que tenían los adaptadores originales.
"""
from __future__ import annotations

import base64
import logging
import re
import uuid
from dataclasses import dataclass
from pathlib import PurePosixPath
from typing import Literal
from urllib.parse import quote

import httpx

from ruesma_comun.graph.token_provider import GraphTokenProvider

logger = logging.getLogger(__name__)

SharePointMode = Literal["drive_id", "folder_url", "site_path"]

_GRAPH_BASE = "https://graph.microsoft.com/v1.0"


@dataclass(frozen=True)
class ResolvedFolder:
    """Carpeta raíz resuelta a partir de una sharing URL (modo folder_url)."""

    drive_id: str
    item_id: str
    folder_name: str | None
    web_url: str | None = None


class GraphSharePointClient:
    """Mecánica Graph compartida. No define API de dominio; eso lo añaden
    las subclases de cada servicio.
    """

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
        folder_root: str = "",
        folder_url: str | None = None,
        link_type: str = "view",
        link_scope: str = "organization",
        create_link: bool = False,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        self._token_provider = GraphTokenProvider(graph_key, timeout_s)
        # ``transport`` solo se usa en tests (MockTransport); en producción
        # es None y httpx abre su transporte HTTP real.
        if transport is not None:
            self._client = httpx.Client(timeout=timeout_s, transport=transport)
        else:
            self._client = httpx.Client(timeout=timeout_s)
        self._base = _GRAPH_BASE
        self._mode: SharePointMode = mode
        self._hostname = (hostname or "").strip() or None
        self._site_path = (site_path or "").strip() or None
        self._drive_name = (drive_name or "").strip()
        self._drive_id = (drive_id or "").strip() or None
        self._folder_root = (folder_root or "").replace("\\", "/").strip().strip("/")
        self._folder_url = (folder_url or "").strip() or None
        self._link_type = (link_type or "").strip() or "view"
        self._link_scope = (link_scope or "").strip() or "organization"
        self._create_link = bool(create_link)

        self._site_id_cache: str | None = None
        self._resolved_folder_cache: ResolvedFolder | None = None

        self._validate_mode_config()

    # ============================================================= #
    # Configuración / cabeceras
    # ============================================================= #
    def _validate_mode_config(self) -> None:
        if self._mode == "drive_id" and not self._drive_id:
            raise RuntimeError("SHAREPOINT_MODE=drive_id exige SHAREPOINT_DRIVE_ID.")
        if self._mode == "folder_url" and not self._folder_url:
            raise RuntimeError("SHAREPOINT_MODE=folder_url exige SHAREPOINT_FOLDER_URL.")
        if self._mode == "site_path":
            if not self._hostname or not self._site_path:
                raise RuntimeError(
                    "SHAREPOINT_MODE=site_path exige SHAREPOINT_HOSTNAME y "
                    "SHAREPOINT_SITE_PATH."
                )

    def _headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self._token_provider.get_token()}"}

    # ============================================================= #
    # Sanitización de nombres / paths
    # ============================================================= #
    @staticmethod
    def _safe_filename(filename: str) -> str:
        cleaned = "".join(
            char if char not in '<>:"\\|?*' else "_"
            for char in (filename or "document.bin")
        )
        return cleaned.strip().strip(".") or "document.bin"

    @staticmethod
    def _safe_segment(value: str, fallback: str) -> str:
        """Sanitiza un valor para usarlo como segmento de nombre de archivo
        (p. ej. ``<codigo>_<ide>_<nombre>.pdf``)."""
        if not value:
            return fallback
        cleaned = re.sub(r'[<>:"/\\|?*]+', "_", value.strip())
        cleaned = re.sub(r"\s+", "_", cleaned)
        cleaned = cleaned.strip("._")
        return cleaned or fallback

    @staticmethod
    def _encode_sharing_url(url: str) -> str:
        raw = base64.b64encode(url.encode("utf-8")).decode("ascii")
        token = raw.rstrip("=").replace("/", "_").replace("+", "-")
        return f"u!{token}"

    def _base_folder_path(self, folder_label: str | None) -> str:
        return (self._folder_root or folder_label or "albaranes").strip().strip("/")

    # ============================================================= #
    # Resolución de site / drive
    # ============================================================= #
    def _resolve_site_id(self) -> str:
        if self._site_id_cache:
            return self._site_id_cache
        if not self._hostname or not self._site_path:
            raise RuntimeError(
                "Faltan SHAREPOINT_HOSTNAME/SHAREPOINT_SITE_PATH para resolver "
                "el sitio por path."
            )
        relative_path = self._site_path.lstrip("/")
        url = f"{self._base}/sites/{self._hostname}:/{relative_path}"
        response = self._client.get(url, headers=self._headers())
        if response.status_code >= 300:
            raise RuntimeError(
                f"Graph get site by path {response.status_code}: "
                f"{response.text[:500]}"
            )
        site_id = str((response.json() or {}).get("id") or "").strip()
        if not site_id:
            raise RuntimeError("Graph no devolvió site.id para SharePoint.")
        self._site_id_cache = site_id
        return site_id

    def _resolve_drive_id(self, site_id: str) -> str:
        """Resuelve el drive dentro de un site ya resuelto (modo site_path)."""
        if self._drive_id:
            return self._drive_id
        url = f"{self._base}/sites/{site_id}/drives"
        response = self._client.get(url, headers=self._headers())
        if response.status_code >= 300:
            raise RuntimeError(
                f"Graph list drives {response.status_code}: {response.text[:500]}"
            )
        items = (response.json() or {}).get("value") or []
        for item in items:
            if str(item.get("name") or "").strip() == self._drive_name:
                self._drive_id = str(item["id"])
                return self._drive_id
        available = ", ".join(
            sorted(
                str(item.get("name") or "").strip()
                for item in items
                if str(item.get("name") or "").strip()
            )
        )
        raise RuntimeError(
            f"No se encontró la biblioteca SharePoint '{self._drive_name}'. "
            f"Disponibles: {available or '(none)'}"
        )

    def _resolve_drive_id_all_modes(self) -> str:
        """Resuelve el drive_id en CUALQUIERA de los 3 modos, sin necesidad
        de la carpeta raíz. Es lo que usa la descarga de sv5."""
        if self._drive_id:
            return self._drive_id
        if self._mode == "folder_url":
            return self._resolve_folder_from_share_url().drive_id
        # site_path
        site_id = self._resolve_site_id()
        return self._resolve_drive_id(site_id)

    def _resolve_folder_from_share_url(self) -> ResolvedFolder:
        if self._resolved_folder_cache:
            return self._resolved_folder_cache
        if not self._folder_url:
            raise RuntimeError("No se ha configurado SHAREPOINT_FOLDER_URL.")
        token = self._encode_sharing_url(self._folder_url)
        url = f"{self._base}/shares/{token}/driveItem"
        response = self._client.get(url, headers=self._headers())
        if response.status_code >= 300:
            raise RuntimeError(
                f"Graph get share driveItem {response.status_code}: "
                f"{response.text[:500]}"
            )
        payload = response.json() or {}
        if not isinstance(payload.get("folder"), dict):
            raise RuntimeError(
                "La URL configurada en SHAREPOINT_FOLDER_URL no apunta a una carpeta."
            )
        item_id = str(payload.get("id") or "").strip()
        parent_reference = payload.get("parentReference") or {}
        drive_id = str(parent_reference.get("driveId") or "").strip()
        web_url = str(payload.get("webUrl") or "").strip() or None
        folder_name = str(payload.get("name") or "").strip() or None
        if not item_id or not drive_id:
            raise RuntimeError(
                "Graph no devolvió id/driveId al resolver SHAREPOINT_FOLDER_URL."
            )
        resolved = ResolvedFolder(
            drive_id=drive_id,
            item_id=item_id,
            folder_name=folder_name,
            web_url=web_url,
        )
        self._resolved_folder_cache = resolved
        return resolved

    # ============================================================= #
    # Carpetas (listar / crear / garantizar)
    # ============================================================= #
    def _children_endpoint(self, *, drive_id: str, parent_item_id: str) -> str:
        if parent_item_id == "root":
            return f"{self._base}/drives/{drive_id}/root/children"
        return f"{self._base}/drives/{drive_id}/items/{parent_item_id}/children"

    def _list_children(self, *, drive_id: str, parent_item_id: str) -> list[dict]:
        url = self._children_endpoint(drive_id=drive_id, parent_item_id=parent_item_id)
        params: dict | None = {"$select": "id,name,folder"}
        items: list[dict] = []
        while url:
            response = self._client.get(url, headers=self._headers(), params=params)
            params = None
            if response.status_code >= 300:
                raise RuntimeError(
                    f"Graph list children {response.status_code}: "
                    f"{response.text[:500]}"
                )
            payload = response.json() or {}
            values = payload.get("value") or []
            if isinstance(values, list):
                items.extend(item for item in values if isinstance(item, dict))
            url = str(payload.get("@odata.nextLink") or "").strip() or None
        return items

    def _find_child_folder(
        self, *, drive_id: str, parent_item_id: str, folder_name: str
    ) -> dict | None:
        for item in self._list_children(
            drive_id=drive_id, parent_item_id=parent_item_id
        ):
            if str(item.get("name") or "").strip() != folder_name:
                continue
            if not isinstance(item.get("folder"), dict):
                continue
            return item
        return None

    def _create_folder(
        self, *, drive_id: str, parent_item_id: str, folder_name: str
    ) -> str:
        url = self._children_endpoint(drive_id=drive_id, parent_item_id=parent_item_id)
        payload = {
            "name": folder_name,
            "folder": {},
            "@microsoft.graph.conflictBehavior": "fail",
        }
        response = self._client.post(url, headers=self._headers(), json=payload)
        if response.status_code == 409:
            existing = self._find_child_folder(
                drive_id=drive_id,
                parent_item_id=parent_item_id,
                folder_name=folder_name,
            )
            if existing:
                existing_id = str(existing.get("id") or "").strip()
                if existing_id:
                    return existing_id
        if response.status_code < 200 or response.status_code >= 300:
            raise RuntimeError(
                f"Graph create folder {response.status_code}: {response.text[:500]}"
            )
        folder_id = str((response.json() or {}).get("id") or "").strip()
        if not folder_id:
            raise RuntimeError("Graph no devolvió id al crear carpeta.")
        return folder_id

    def _ensure_child_folder(
        self, *, drive_id: str, parent_item_id: str, folder_name: str
    ) -> str:
        existing = self._find_child_folder(
            drive_id=drive_id, parent_item_id=parent_item_id, folder_name=folder_name
        )
        if existing:
            folder_id = str(existing.get("id") or "").strip()
            if folder_id:
                return folder_id
        return self._create_folder(
            drive_id=drive_id, parent_item_id=parent_item_id, folder_name=folder_name
        )

    def _ensure_folder_path_from_root(self, *, drive_id: str, folder_path: str) -> str:
        parts = [
            part for part in PurePosixPath(folder_path).parts if part and part != "/"
        ]
        parent_id = "root"
        for folder_name in parts:
            parent_id = self._ensure_child_folder(
                drive_id=drive_id, parent_item_id=parent_id, folder_name=folder_name
            )
        return parent_id

    # ============================================================= #
    # Subida
    # ============================================================= #
    def _upload_file_by_parent(
        self,
        *,
        drive_id: str,
        parent_item_id: str,
        filename: str,
        mime_type: str,
        file_bytes: bytes,
    ) -> dict:
        encoded_name = quote(filename, safe="")
        if parent_item_id == "root":
            url = f"{self._base}/drives/{drive_id}/root:/{encoded_name}:/content"
        else:
            url = (
                f"{self._base}/drives/{drive_id}/items/{parent_item_id}:/"
                f"{encoded_name}:/content"
            )
        headers = self._headers()
        headers["Content-Type"] = mime_type or "application/octet-stream"
        response = self._client.put(url, headers=headers, content=file_bytes)
        if response.status_code < 200 or response.status_code >= 300:
            raise RuntimeError(
                f"Graph upload file {response.status_code}: {response.text[:500]}"
            )
        return response.json() or {}

    def _upload_file_by_relative_path(
        self, *, drive_id: str, relative_path: str, mime_type: str, file_bytes: bytes
    ) -> dict:
        encoded_path = quote(relative_path, safe="/")
        url = f"{self._base}/drives/{drive_id}/root:/{encoded_path}:/content"
        headers = self._headers()
        headers["Content-Type"] = mime_type or "application/octet-stream"
        response = self._client.put(url, headers=headers, content=file_bytes)
        if response.status_code < 200 or response.status_code >= 300:
            raise RuntimeError(
                f"Graph upload file {response.status_code}: {response.text[:500]}"
            )
        return response.json() or {}

    def convert_to_pdf(
        self,
        file_bytes: bytes,
        src_ext: str,
        *,
        temp_folder: str = "_conversion_tmp",
    ) -> bytes | None:
        """Convierte un documento de Office a PDF con el motor de Microsoft
        365 (Graph ``content?format=pdf``), la misma fidelidad que Word.

        Mecánica: sube el fichero a una carpeta temporal del drive, pide la
        versión PDF, descarga los bytes y BORRA el temporal. Best-effort:
        ante cualquier fallo devuelve ``None`` (el llamante degrada).

        Formatos de origen admitidos por Graph: doc, docx, ppt, pptx, xls,
        xlsx, rtf, odt, etc. NO admite .docm (macros) ni ficheros con IRM.
        """
        if not file_bytes:
            return None
        ext = src_ext if src_ext.startswith(".") else f".{src_ext}"
        try:
            drive_id = self._resolve_drive_id_all_modes()
        except Exception:
            logger.exception("convert_to_pdf: no se pudo resolver el drive.")
            return None

        rel = f"{temp_folder.strip('/')}/{uuid.uuid4().hex}{ext}"
        item_id: str | None = None
        try:
            item = self._upload_file_by_relative_path(
                drive_id=drive_id,
                relative_path=rel,
                mime_type="application/octet-stream",
                file_bytes=file_bytes,
            )
            item_id = str(item.get("id") or "").strip()
            if not item_id:
                logger.warning("convert_to_pdf: subida sin id de item.")
                return None
            url = (
                f"{self._base}/drives/{drive_id}/items/{item_id}"
                "/content?format=pdf"
            )
            # follow_redirects: Graph responde 302 a la URL de descarga del
            # PDF ya convertido (httpx quita el header Authorization en el
            # salto cross-host, que es justo lo que queremos).
            resp = self._client.get(
                url, headers=self._headers(), follow_redirects=True
            )
            if resp.status_code < 200 or resp.status_code >= 300:
                logger.warning(
                    "convert_to_pdf format=pdf %s: %s",
                    resp.status_code,
                    resp.text[:300],
                )
                return None
            return resp.content
        except Exception:
            logger.exception("convert_to_pdf: fallo convirtiendo %s.", ext)
            return None
        finally:
            if item_id:
                try:
                    self._client.delete(
                        f"{self._base}/drives/{drive_id}/items/{item_id}",
                        headers=self._headers(),
                    )
                except Exception:
                    logger.warning(
                        "convert_to_pdf: no se pudo borrar el temporal %s.",
                        item_id,
                    )

    def _create_share_link(self, *, drive_id: str, item_id: str) -> str | None:
        url = f"{self._base}/drives/{drive_id}/items/{item_id}/createLink"
        payload = {"type": self._link_type, "scope": self._link_scope}
        response = self._client.post(url, headers=self._headers(), json=payload)
        if response.status_code < 200 or response.status_code >= 300:
            logger.warning(
                "No se pudo crear createLink en SharePoint. status=%s body=%s",
                response.status_code,
                response.text[:500],
            )
            return None
        data = response.json() or {}
        link = data.get("link") or {}
        return str(link.get("webUrl") or "").strip() or None

    # ============================================================= #
    # Descarga (lo que sv5 necesita para leer el contrato)
    # ============================================================= #
    def _download_bytes_by_relative_path(
        self, *, drive_id: str, relative_path: str
    ) -> tuple[bytes, str]:
        """Descarga el contenido de un fichero por su path relativo dentro
        del drive. Devuelve ``(contenido, content_type)``."""
        normalized = relative_path.replace("\\", "/").lstrip("/")
        encoded_path = quote(normalized, safe="/")
        url = f"{self._base}/drives/{drive_id}/root:/{encoded_path}:/content"
        logger.info("[sp-download] GET %s", url[:200])
        response = self._client.get(
            url, headers=self._headers(), follow_redirects=True
        )
        if response.status_code == 302:
            location = response.headers.get("Location")
            if location:
                response = self._client.get(location)
        if response.status_code >= 300:
            raise RuntimeError(
                f"Graph download {response.status_code}: {response.text[:500]}"
            )
        content = response.content or b""
        if not content:
            raise RuntimeError(f"Graph devolvió binario vacío para {relative_path}")
        content_type = response.headers.get("Content-Type") or "application/pdf"
        return content, content_type

    def _download_text_by_relative_path(
        self, *, drive_id: str, relative_path: str, encoding: str = "utf-8"
    ) -> str:
        """Descarga un fichero de texto (p. ej. el Markdown del contrato)
        por su path relativo y lo decodifica. Lo usa sv5 para leer el MD."""
        content, _ = self._download_bytes_by_relative_path(
            drive_id=drive_id, relative_path=relative_path
        )
        return content.decode(encoding, errors="replace")
