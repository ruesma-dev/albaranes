# config/logging_config.py
"""Log de sv9 (patrón de sv6): consola + fichero rotado.

Nada de secretos en el log: ni la clave de sigrid-api, ni el PDF, ni datos
bancarios (R35). Los adaptadores solo registran códigos y estados.
"""
from __future__ import annotations

import logging.config
from pathlib import Path


def configure_logging(log_dir: Path, level: str) -> None:
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "albaranes_alta_sigrid.log"
    config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "standard": {
                "format": (
                    "%(asctime)s | %(levelname)s | %(name)s | "
                    "%(filename)s:%(lineno)d | %(message)s"
                )
            }
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": level,
                "formatter": "standard",
            },
            "file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": level,
                "formatter": "standard",
                "filename": str(log_file),
                "maxBytes": 5 * 1024 * 1024,
                "backupCount": 5,
                "encoding": "utf-8",
            },
        },
        "root": {
            "handlers": ["console", "file"],
            "level": level,
        },
    }
    logging.config.dictConfig(config)
