# main.py
from __future__ import annotations

import logging
from pathlib import Path

import uvicorn
from dotenv import load_dotenv
from pydantic import ValidationError
from ruesma_comun.configuracion import motivos_configuracion

from config.logging_config import configure_logging
from config.settings import Settings
from interface_adapters.web.app import build_app

logger = logging.getLogger(__name__)


def main() -> int:
    # Vuelca el .env a os.environ antes de build_app: el publicador de
    # colas (construir_publicador, en ruesma_comun) lee de os.environ.
    # Así COLAS_CONNECTION_STRING vive en el .env y sv4 corre CON colas
    # (modo pipeline). Sin la variable, sigue el modo solo-front.
    load_dotenv(Path(__file__).resolve().parent / ".env")
    try:
        settings = Settings()
    except ValidationError as exc:
        # F-053 R44: una configuración que no se puede leer (p. ej. el mapeo
        # de productos sin '*') NO arranca y dice por qué, sin volcar los
        # valores del entorno (secretos: lección H1 de la fase 1).
        logging.basicConfig(level=logging.INFO)
        logger.error(
            "[sv4] configuración inválida, no arranco: %s",
            motivos_configuracion(exc),
        )
        return 2
    configure_logging(Path(settings.log_dir), settings.log_level)
    app = build_app(settings)
    uvicorn.run(
        app,
        host=settings.api_host,
        port=settings.api_port,
        log_level=settings.log_level.lower(),
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
