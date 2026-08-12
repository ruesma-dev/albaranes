# config/settings.py
from __future__ import annotations

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

_ENV_FILE = Path(__file__).resolve().parents[1] / ".env"


class Settings(BaseSettings):
    """Configuración del servicio 1 (email-albaranes-ingestor).

    Respeta los nombres de variables ya existentes en el .env (MAILBOX_ADDRESS,
    SOURCE_FOLDER, FOLDER_PROCESADOS, FOLDER_ERRORES, MAX_EMAILS, etc.).

    Cambio respecto a la versión previa (orquestador):
      - SE AÑADEN las variables SV7_* para apuntar al orquestador.
      - SE MANTIENEN las variables SERVICE2_*/SERVICE3_* declaradas como
        OPCIONALES, para no romper código existente que aún las lea
        durante la transición. Cuando todo el polling vaya por sv7,
        se pueden eliminar.
    """

    # --------------------------------------------------------------- #
    # Buzón de Microsoft 365 vía Microsoft Graph.
    # --------------------------------------------------------------- #
    mailbox_address: str = Field(..., alias="MAILBOX_ADDRESS")
    graph_key: str = Field(..., alias="GRAPH_KEY")
    graph_timeout_s: int = Field(60, alias="GRAPH_TIMEOUT_S")

    source_folder: str = Field("inbox", alias="SOURCE_FOLDER")
    folder_procesados: str = Field("Procesados", alias="FOLDER_PROCESADOS")
    folder_errores: str = Field("Errores", alias="FOLDER_ERRORES")

    poll_interval_s: int = Field(60, alias="POLL_INTERVAL_S")
    max_emails: int = Field(10, alias="MAX_EMAILS")
    max_attachment_mb: int = Field(25, alias="MAX_ATTACHMENT_MB")

    # --------------------------------------------------------------- #
    # Servicios downstream — LEGACY (sv1 → sv2 → sv3 directo).
    # Se mantienen declarados como opcionales durante la transición.
    # Cuando el polling_pipeline esté reescrito para usar SOLO sv7,
    # estas variables se pueden eliminar del .env y de aquí.
    # --------------------------------------------------------------- #
    service2_base_url: str | None = Field(
        default=None,
        alias="SERVICE2_BASE_URL",
    )
    service2_extract_path: str = Field(
        "/v1/albaranes/extract",
        alias="SERVICE2_EXTRACT_PATH",
    )
    service2_timeout_s: int = Field(300, alias="SERVICE2_TIMEOUT_S")

    service3_base_url: str | None = Field(
        default=None,
        alias="SERVICE3_BASE_URL",
    )
    service3_persist_path: str = Field(
        "/v1/albaranes/persist",
        alias="SERVICE3_PERSIST_PATH",
    )
    service3_timeout_s: int = Field(120, alias="SERVICE3_TIMEOUT_S")

    http_timeout_s: int = Field(60, alias="HTTP_TIMEOUT_S")

    # --------------------------------------------------------------- #
    # NUEVO — PostgreSQL (intake por colas).
    # sv1 crea la fila idempotente en ``workflow_runs`` (dedup por
    # correlation_key) antes de subir el PDF a blob y encolar q-extraccion.
    # --------------------------------------------------------------- #
    pg_host: str = Field("localhost", alias="PG_HOST")
    pg_port: int = Field(5432, alias="PG_PORT")
    pg_db: str = Field("albaranes", alias="PG_DB")
    pg_user: str = Field("postgres", alias="PG_USER")
    pg_password: str = Field(..., alias="PG_PASSWORD")

    # --------------------------------------------------------------- #
    # NUEVO — Orquestador (sv7).
    # Cuando el polling_pipeline esté reescrito, sv1 sólo conocerá sv7
    # y le hará un POST /v1/events/email-received por cada página de
    # adjunto detectada. sv7 se encarga de orquestar sv2/sv3/sv6.
    #
    # SV7_TIMEOUT_S es relativamente alto (60s) porque, aunque sv7
    # responde 202 inmediatamente, el upload del PDF en multipart puede
    # tardar unos segundos.
    # --------------------------------------------------------------- #
    sv7_base_url: str = Field("http://127.0.0.1:8005", alias="SV7_BASE_URL")
    sv7_timeout_s: int = Field(60, alias="SV7_TIMEOUT_S")
    sv7_path_email_received: str = Field(
        "/v1/events/email-received",
        alias="SV7_PATH_EMAIL_RECEIVED",
    )

    # --------------------------------------------------------------- #
    # Logging y meta.
    # --------------------------------------------------------------- #
    log_level: str = Field("INFO", alias="LOG_LEVEL")
    log_dir: str = Field("logs", alias="LOG_DIR")
    service_version: str = Field("1.0.0", alias="SERVICE_VERSION")

    @property
    def database_url(self) -> str:
        from urllib.parse import quote_plus

        user = quote_plus(self.pg_user)
        password = quote_plus(self.pg_password)
        database = quote_plus(self.pg_db)
        return (
            f"postgresql+psycopg://{user}:{password}"
            f"@{self.pg_host}:{self.pg_port}/{database}"
        )

    model_config = SettingsConfigDict(
        env_file=_ENV_FILE,
        env_file_encoding="utf-8",
        extra="ignore",
    )
