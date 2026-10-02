# infrastructure/graph/mail_client.py
from __future__ import annotations

import logging
from html.parser import HTMLParser
from typing import Any, Dict, List

import httpx

from domain.models.email_models import ContenidoCorreo, EmailAttachment, EmailMessage
from domain.ports.mailbox_client import MailboxClient
from infrastructure.graph.token_provider import GraphTokenProvider

logger = logging.getLogger(__name__)

# Pide el cuerpo en texto plano (F-048, D2). Graph puede ignorarlo y
# devolver HTML: por eso ``get_contenido`` mira el ``contentType``.
_PREFER_TEXTO = 'outlook.body-content-type="text"'

# Etiquetas que separan bloques de texto: se traducen a un salto de linea.
_ETIQUETAS_DE_BLOQUE = frozenset({
    "br", "p", "div", "li", "tr", "table", "ul", "ol",
    "h1", "h2", "h3", "h4", "h5", "h6",
})
# Etiquetas cuyo contenido no es texto del correo (estilos y codigo).
_ETIQUETAS_SIN_TEXTO = frozenset({"script", "style"})


class _ExtractorTexto(HTMLParser):
    """Se queda con el texto de un HTML; no sigue enlaces ni ejecuta nada."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._trozos: list[str] = []
        self._dentro_sin_texto = 0

    def handle_starttag(self, tag: str, attrs: list) -> None:
        if tag in _ETIQUETAS_SIN_TEXTO:
            self._dentro_sin_texto += 1
        elif tag in _ETIQUETAS_DE_BLOQUE:
            self._trozos.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if tag in _ETIQUETAS_SIN_TEXTO:
            self._dentro_sin_texto = max(0, self._dentro_sin_texto - 1)
        elif tag in _ETIQUETAS_DE_BLOQUE:
            self._trozos.append("\n")

    def handle_data(self, data: str) -> None:
        if not self._dentro_sin_texto:
            self._trozos.append(data)

    def texto(self) -> str:
        lineas = (linea.strip() for linea in "".join(self._trozos).split("\n"))
        return "\n".join(linea for linea in lineas if linea)


def html_a_texto(html: str) -> str:
    """Reduce un HTML a texto plano (F-048, R4) sin interpretar su contenido.

    Solo quita marcado: las etiquetas de bloque pasan a saltos de linea, las
    entidades se resuelven y se descartan ``script`` y ``style``. Lo que diga
    el texto no se mira: esa decision es de la IA, y el texto le llega como
    dato (D7).
    """
    extractor = _ExtractorTexto()
    extractor.feed(html)
    extractor.close()
    return extractor.texto()


class GraphMailClient(MailboxClient):
    def __init__(
        self,
        token_provider: GraphTokenProvider,
        timeout_s: int,
        *,
        http_client: httpx.Client | None = None,
    ) -> None:
        self._token_provider = token_provider
        # ``http_client`` solo lo pasan los tests (``httpx.MockTransport``).
        self._client = http_client or httpx.Client(timeout=timeout_s)
        self._base = "https://graph.microsoft.com/v1.0"

    def _headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self._token_provider.get_token()}"}

    @staticmethod
    def _escape_odata(value: str) -> str:
        return value.replace("'", "''")

    def assert_folder_accessible(self, mailbox: str, folder: str) -> None:
        url = f"{self._base}/users/{mailbox}/mailFolders/{folder}"
        response = self._client.get(
            url,
            headers=self._headers(),
            params={"$select": "id,displayName"},
        )
        if response.status_code >= 300:
            raise RuntimeError(
                "Graph folder not accessible "
                f"({folder}) {response.status_code}: {response.text[:400]}"
            )
        data = response.json() or {}
        logger.info(
            "SOURCE_FOLDER accesible: %s (%s)",
            data.get("displayName"),
            data.get("id"),
        )

    def ensure_folder(self, mailbox: str, display_name: str) -> str:
        url = f"{self._base}/users/{mailbox}/mailFolders"
        params = {
            "$filter": f"displayName eq '{self._escape_odata(display_name)}'",
            "$select": "id,displayName",
        }
        response = self._client.get(
            url,
            headers=self._headers(),
            params=params,
        )
        if response.status_code >= 300:
            raise RuntimeError(
                f"Graph list folders {response.status_code}: "
                f"{response.text[:400]}"
            )

        items = (response.json() or {}).get("value") or []
        if items:
            folder_id = items[0]["id"]
            logger.info("Carpeta existe: %s id=%s", display_name, folder_id)
            return folder_id

        logger.info("Carpeta no existe, creando: %s", display_name)
        response = self._client.post(
            url,
            headers=self._headers(),
            json={"displayName": display_name},
        )
        if response.status_code >= 300:
            raise RuntimeError(
                f"Graph create folder {response.status_code}: "
                f"{response.text[:400]}"
            )

        folder_id = response.json()["id"]
        logger.info("Carpeta creada: %s id=%s", display_name, folder_id)
        return folder_id

    def list_unread_with_attachments(
        self,
        mailbox: str,
        folder: str,
        top: int,
    ) -> List[EmailMessage]:
        url = f"{self._base}/users/{mailbox}/mailFolders/{folder}/messages"
        params = {
            "$top": str(top),
            "$select": (
                "id,subject,from,receivedDateTime,isRead,hasAttachments"
            ),
            "$orderby": "receivedDateTime desc",
            "$filter": (
                "receivedDateTime ge 1900-01-01T00:00:00Z "
                "and isRead eq false and hasAttachments eq true"
            ),
        }
        response = self._client.get(
            url,
            headers=self._headers(),
            params=params,
        )
        if response.status_code >= 300:
            logger.warning(
                "Graph list messages falló (%s). Reintento sin filter. %s",
                response.status_code,
                response.text[:300],
            )
            params.pop("$filter", None)
            response = self._client.get(
                url,
                headers=self._headers(),
                params=params,
            )
            if response.status_code >= 300:
                raise RuntimeError(
                    f"Graph list messages {response.status_code}: "
                    f"{response.text[:400]}"
                )

        items = (response.json() or {}).get("value") or []
        messages: List[EmailMessage] = []
        for item in items:
            if item.get("isRead") is True:
                continue
            if item.get("hasAttachments") is not True:
                continue

            sender = None
            raw_sender = item.get("from") or {}
            email_address = (raw_sender.get("emailAddress") or {})
            sender = email_address.get("address")

            messages.append(
                EmailMessage(
                    id=item["id"],
                    subject=str(item.get("subject") or ""),
                    sender=sender,
                    received_datetime=item.get("receivedDateTime"),
                )
            )
        return messages

    def list_attachments(
        self,
        mailbox: str,
        message_id: str,
    ) -> List[EmailAttachment]:
        url = f"{self._base}/users/{mailbox}/messages/{message_id}/attachments"
        params = {"$select": "id,name,contentType,size,isInline"}
        response = self._client.get(
            url,
            headers=self._headers(),
            params=params,
        )
        if response.status_code >= 300:
            raise RuntimeError(
                f"Graph list attachments {response.status_code}: "
                f"{response.text[:400]}"
            )

        items = (response.json() or {}).get("value") or []
        attachments: List[EmailAttachment] = []
        for item in items:
            attachments.append(
                EmailAttachment(
                    id=item["id"],
                    name=str(item.get("name") or "attachment.bin"),
                    content_type=str(
                        item.get("contentType") or "application/octet-stream"
                    ),
                    size=int(item.get("size") or 0),
                    is_inline=bool(item.get("isInline") or False),
                    odata_type=(
                        str(item.get("@odata.type"))
                        if item.get("@odata.type")
                        else None
                    ),
                )
            )
        return attachments

    def download_attachment_value(
        self,
        mailbox: str,
        message_id: str,
        attachment_id: str,
    ) -> bytes:
        url = (
            f"{self._base}/users/{mailbox}/messages/{message_id}/attachments/"
            f"{attachment_id}/$value"
        )
        response = self._client.get(url, headers=self._headers())
        if response.status_code >= 300:
            raise RuntimeError(
                f"Graph attachment $value {response.status_code}: "
                f"{response.text[:400]}"
            )
        return response.content

    def move_message(
        self,
        mailbox: str,
        message_id: str,
        destination_folder_id: str,
    ) -> None:
        url = f"{self._base}/users/{mailbox}/messages/{message_id}/move"
        response = self._client.post(
            url,
            headers=self._headers(),
            json={"destinationId": destination_folder_id},
        )
        if response.status_code >= 300:
            raise RuntimeError(
                f"Graph move {response.status_code}: {response.text[:400]}"
            )

    def get_contenido(
        self,
        mailbox: str,
        message_id: str,
    ) -> ContenidoCorreo:
        """Asunto, ``uniqueBody`` en texto y fecha de recepcion con UN GET (F-048, R2-R4).

        Nunca pide ``body``: arrastra la cadena de respuestas citada (R3). El
        error no lleva ``response.text``, que podria citar el correo (R36).
        """
        url = f"{self._base}/users/{mailbox}/messages/{message_id}"
        headers = {**self._headers(), "Prefer": _PREFER_TEXTO}
        response = self._client.get(
            url,
            headers=headers,
            params={"$select": "subject,uniqueBody,receivedDateTime"},
        )
        if response.status_code >= 300:
            raise RuntimeError(f"Graph contenido del mensaje {response.status_code}")

        data = response.json() or {}
        unico = data.get("uniqueBody") or {}
        tipo = str(unico.get("contentType") or "text").lower()
        cuerpo = str(unico.get("content") or "")
        if tipo == "html":
            cuerpo = html_a_texto(cuerpo)
        return ContenidoCorreo(
            asunto=str(data.get("subject") or ""),
            cuerpo_unico=cuerpo,
            tipo=tipo,
            recibido_utc=str(data.get("receivedDateTime") or "") or None,
        )
