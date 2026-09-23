# capturar_correo.py
"""Captura de SOLO LECTURA del texto de un correo para el banco de evals.

F-048, R39. Uso, desde ``services/albaranes-email`` y con su ``.env``::

    .\\.venv\\Scripts\\python.exe capturar_correo.py --message-id <ID> --caso <CASO>

Pide a Graph el asunto y la parte unica del cuerpo por el MISMO camino que
el pipeline (``GraphMailClient.get_contenido``: un GET) y lo guarda en
``evals/inputs/correos/{caso}.json``. No mueve, no marca como leido y no
modifica nada del buzon.

La ruta de salida la ignora git (R38): un correo real nunca se versiona.

Formato del fichero (``version`` 1): ``caso_id``, ``message_id``,
``asunto`` y ``cuerpo`` TAL CUAL los da Graph (el HTML ya reducido a texto,
sin normalizar ni recortar), ``tipo_origen`` (``text`` o ``html``) y
``capturado_utc``. Quien lo lea construye el contexto con
``ruesma_comun.correo.construir_contexto_correo``, la MISMA funcion que usa
sv1: asi la huella sale igual que si el correo hubiera entrado por el buzon.
"""
from __future__ import annotations

import argparse
import json
import re
from datetime import UTC, datetime
from pathlib import Path

from config.settings import Settings
from domain.ports.mailbox_client import MailboxClient
from dotenv import load_dotenv
from infrastructure.graph.mail_client import GraphMailClient
from infrastructure.graph.token_provider import GraphTokenProvider
from ruesma_comun.correo import construir_contexto_correo

VERSION_CAPTURA = 1
RAIZ_SERVICIO = Path(__file__).resolve().parent
DIRECTORIO_SALIDA = RAIZ_SERVICIO.parents[1] / "evals" / "inputs" / "correos"

# Un nombre de fichero sencillo: sin separadores, sin ``..`` y sin ocultos.
_CASO_VALIDO = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]*$")


def ruta_captura(caso_id: str, directorio: Path = DIRECTORIO_SALIDA) -> Path:
    """Fichero de la captura de ``caso_id``; ``ValueError`` si el nombre no vale."""
    if not _CASO_VALIDO.fullmatch(caso_id or ""):
        raise ValueError(f"caso no valido: {caso_id!r} (letras, digitos, '_', '.' o '-')")
    return Path(directorio) / f"{caso_id}.json"


def capturar(
    buzon: MailboxClient,
    *,
    mailbox: str,
    message_id: str,
    caso_id: str,
    directorio: Path = DIRECTORIO_SALIDA,
) -> Path:
    """Pide el contenido del mensaje (solo ``get_contenido``) y lo guarda."""
    ruta = ruta_captura(caso_id, directorio)
    contenido = buzon.get_contenido(mailbox=mailbox, message_id=message_id)
    datos = {
        "version": VERSION_CAPTURA,
        "caso_id": caso_id,
        "message_id": message_id,
        "asunto": contenido.asunto,
        "cuerpo": contenido.cuerpo_unico,
        "tipo_origen": contenido.tipo,
        "capturado_utc": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
    }
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_text(json.dumps(datos, ensure_ascii=False, indent=2), encoding="utf-8")
    return ruta


def _buzon_desde_entorno() -> tuple[MailboxClient, str]:
    """El cliente de Graph de sv1 con la configuracion de su ``.env``."""
    load_dotenv(RAIZ_SERVICIO / ".env")
    settings = Settings()
    proveedor = GraphTokenProvider(settings.graph_key, timeout_s=settings.graph_timeout_s)
    buzon = GraphMailClient(token_provider=proveedor, timeout_s=settings.graph_timeout_s)
    return buzon, settings.mailbox_address


def main(argv: list[str] | None = None) -> int:
    analizador = argparse.ArgumentParser(
        description="Guarda el asunto y la parte unica del cuerpo de un correo (solo lectura)."
    )
    analizador.add_argument("--message-id", required=True, help="id de Graph del mensaje")
    analizador.add_argument("--caso", required=True, help="id del caso del banco de evals")
    analizador.add_argument(
        "--directorio", type=Path, default=DIRECTORIO_SALIDA, help="carpeta de salida"
    )
    opciones = analizador.parse_args(argv)

    buzon, mailbox = _buzon_desde_entorno()
    ruta = capturar(
        buzon,
        mailbox=mailbox,
        message_id=opciones.message_id,
        caso_id=opciones.caso,
        directorio=opciones.directorio,
    )
    datos = json.loads(ruta.read_text(encoding="utf-8"))
    # Solo la huella (con el recorte por defecto, 4.000) y el tamano: el
    # texto se mira abriendo el fichero, nunca por pantalla.
    ctx = construir_contexto_correo(datos["asunto"], datos["cuerpo"])
    print(
        f"Guardado {ruta} (sha={ctx.sha256[:8]} caracteres={ctx.caracteres_originales} "
        f"tipo={datos['tipo_origen']})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
