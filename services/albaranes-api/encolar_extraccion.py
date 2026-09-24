# encolar_extraccion.py
"""Encola a mano un mensaje de extraccion en q-extraccion (para probar el worker).

Uso:  python encolar_extraccion.py DOC-PRUEBA-1
      python encolar_extraccion.py DOC-PRUEBA-1 --correo ..\\..\\evals\\inputs\\correos\\<CASO>.json

(F-048, R42) ``--correo`` lee un fichero de captura (el formato de
``capturar_correo.py`` de sv1: ``asunto`` y ``cuerpo`` tal cual), construye
el contexto con ``construir_contexto_correo`` y lo guarda con
``guardar_contexto_correo`` en ``input/{document_id}.correo.json``: las
MISMAS funciones que usa sv1, asi la huella sale igual que si el correo
hubiera entrado por el buzon. El blob se guarda ANTES de publicar y el
mensaje lleva ``correo_blob``. Por pantalla, solo la huella abreviada y los
caracteres: el texto se mira abriendo el fichero.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from ruesma_comun.blobs import construir_almacen_desde_entorno
from ruesma_comun.colas import COLA_EXTRACCION, MensajeExtraccion
from ruesma_comun.colas.arranque import construir_publicador
from ruesma_comun.correo import (
    ContextoCorreo,
    construir_contexto_correo,
    guardar_contexto_correo,
)

DOCUMENTO_POR_DEFECTO = "DOC-PRUEBA-1"


def _cargar_entorno() -> None:
    """Carga el .env en os.environ (igual que main_worker.py): asi
    COLAS_CONNECTION_STRING esta disponible al ejecutar en otra consola."""
    try:
        from dotenv import load_dotenv

        load_dotenv()
    except ImportError:
        pass


def leer_captura(ruta: Path) -> ContextoCorreo:
    """Contexto del correo a partir de un fichero de captura.

    Lanza ``ValueError`` si el fichero no existe, no es JSON o no trae
    ``asunto`` y ``cuerpo``; el mensaje nunca cita el contenido.
    """
    try:
        datos = json.loads(ruta.read_text(encoding="utf-8"))
    except OSError as exc:
        raise ValueError(f"no se pudo leer {ruta} ({type(exc).__name__})") from None
    except ValueError as exc:
        raise ValueError(f"{ruta} no es JSON valido ({type(exc).__name__})") from None
    if not isinstance(datos, dict) or "asunto" not in datos or "cuerpo" not in datos:
        raise ValueError(f"{ruta} no es una captura de correo: faltan 'asunto' y 'cuerpo'")
    return construir_contexto_correo(
        datos["asunto"], datos["cuerpo"], recibido_utc=datos.get("recibido_utc"),
    )


def main(argv: list[str] | None = None) -> int:
    analizador = argparse.ArgumentParser(description="Encola un documento en q-extraccion.")
    analizador.add_argument("document_id", nargs="?", default=DOCUMENTO_POR_DEFECTO)
    analizador.add_argument(
        "--correo", type=Path, default=None,
        help="fichero de captura del correo (evals/inputs/correos/<CASO>.json)",
    )
    opciones = analizador.parse_args(argv)
    document_id = opciones.document_id

    # Se lee ANTES de tocar la cola o el Blob: un fichero malo no deja nada a medias.
    correo = None
    if opciones.correo is not None:
        try:
            correo = leer_captura(opciones.correo)
        except ValueError as exc:
            analizador.error(str(exc))

    _cargar_entorno()
    correo_blob = None
    if correo is not None:
        correo_blob = guardar_contexto_correo(construir_almacen_desde_entorno(), document_id, correo)
        print(
            f"Correo guardado en input/{correo_blob} "
            f"(sha={correo.sha256[:8]} caracteres={correo.caracteres_originales} "
            f"truncado={correo.truncado})"
        )

    pub = construir_publicador(emitido_por="encolar-manual")
    pub.publicar(
        COLA_EXTRACCION,
        MensajeExtraccion(
            document_id=document_id,
            correlation_key=f"corr-{document_id}",
            correo_blob=correo_blob,
        ),
    )
    print(f"Encolado document_id={document_id} en {COLA_EXTRACCION}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
