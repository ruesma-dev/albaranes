# config/settings.py
"""Configuración de sv9 (albaranes-alta-sigrid), F-053 design §7.

Llaves propias del alta (con sus defectos):

- ``ALTA_SIGRID_DESDE_UTC``: solo se dan de alta los documentos aprobados desde
  ese instante (ISO 8601; sin zona = UTC). **Vacía = feature apagada**: sv9
  confirma los mensajes sin hacer nada.
- ``ALTA_SIGRID_COMMIT``: modo **real** SOLO con el literal ``true``; cualquier
  otro valor, o ninguno, es **simulación** y sv9 nunca manda ``commit=true``.
  Lo cambia el humano; en local no se pone nunca.
- ``ALTA_SIGRID_ESPERA_INCIERTO_MIN`` (15), ``ALTA_SIGRID_TOLERANCIA_EUR``
  (0,05), ``ALTA_SIGRID_AVISOS_BLOQUEANTES`` (CSV; ``producto_sin_historico``),
  ``ALTA_SIGRID_USUARIO`` (login de ``dbo.usu``, va en ``usu`` y en el
  adjunto), ``ALTA_SIGRID_EMPIDE`` (vacía = defecto de sigrid-api) y
  ``ALTA_SIGRID_PRODUCTO_POR_DEFECTO`` (JSON familia → producto, con ``*``;
  mal formado = no arranca, R44). DESDE, Espera y mapeo llevan el MISMO valor
  en sv4.

El resto, con los nombres de sv3/sv6: sigrid-api, PostgreSQL, Graph/SharePoint
y log. Las colas se leen del entorno en ``ruesma_comun.colas.arranque``.
``SIGRID_API_FUNCTION_KEY`` y ``PG_PASSWORD`` son secretos: nunca en el repo.
"""
from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Literal
from urllib.parse import quote_plus

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from ruesma_comun.alta_sigrid import MAPEO_PRODUCTO_POR_DEFECTO_TEXTO, leer_mapeo

_ENV_FILE = Path(__file__).resolve().parents[1] / ".env"

SharePointMode = Literal["drive_id", "folder_url", "site_path"]

#: Único valor de ``ALTA_SIGRID_COMMIT`` que activa el modo real.
LITERAL_COMMIT_REAL = "true"


def leer_instante_utc(texto: str) -> datetime | None:
    """ISO 8601 a instante UTC; vacío = ``None``; sin zona = UTC."""
    limpio = (texto or "").strip()
    if not limpio:
        return None
    instante = datetime.fromisoformat(limpio.replace("Z", "+00:00"))
    if instante.tzinfo is None:
        instante = instante.replace(tzinfo=UTC)
    return instante.astimezone(UTC)


class Settings(BaseSettings):
    """Configuración de sv9 (solo worker sobre ``q-feedback``)."""

    # ----------------------------------------------------------------- #
    # Llaves del alta (design §7).
    # ----------------------------------------------------------------- #
    alta_sigrid_desde_utc: str = Field("", alias="ALTA_SIGRID_DESDE_UTC")
    alta_sigrid_commit: str = Field("false", alias="ALTA_SIGRID_COMMIT")
    espera_incierto_min: int = Field(15, alias="ALTA_SIGRID_ESPERA_INCIERTO_MIN", ge=0)
    tolerancia_eur: float = Field(0.05, alias="ALTA_SIGRID_TOLERANCIA_EUR", ge=0)
    alta_sigrid_avisos_bloqueantes: str = Field(
        "producto_sin_historico", alias="ALTA_SIGRID_AVISOS_BLOQUEANTES",
    )
    usuario: str = Field("", alias="ALTA_SIGRID_USUARIO")
    alta_sigrid_empide: str = Field("", alias="ALTA_SIGRID_EMPIDE")
    alta_sigrid_producto_por_defecto: str = Field(
        MAPEO_PRODUCTO_POR_DEFECTO_TEXTO, alias="ALTA_SIGRID_PRODUCTO_POR_DEFECTO",
    )

    # ----------------------------------------------------------------- #
    # sigrid-api (la grabación usa su propio timeout de 240 s > 230 s del
    # balanceador; ver el cliente).
    # ----------------------------------------------------------------- #
    sigrid_api_base_url: str = Field(..., alias="SIGRID_API_BASE_URL")
    sigrid_api_function_key: str = Field(..., alias="SIGRID_API_FUNCTION_KEY")
    sigrid_api_database: str = Field("ruesma", alias="SIGRID_API_DATABASE")
    sigrid_api_timeout_s: float = Field(60.0, alias="SIGRID_API_TIMEOUT_S", gt=0)

    # ----------------------------------------------------------------- #
    # PostgreSQL (misma BBDD que sv3/sv4/sv6; sv9 solo escribe su tabla).
    # ----------------------------------------------------------------- #
    pg_host: str = Field("localhost", alias="PG_HOST")
    pg_port: int = Field(5432, alias="PG_PORT")
    pg_db: str = Field("albaranes", alias="PG_DB")
    pg_user: str = Field(..., alias="PG_USER")
    pg_password: str = Field(..., alias="PG_PASSWORD")

    # ----------------------------------------------------------------- #
    # Graph + SharePoint (para bajar el PDF del albarán y adjuntarlo).
    # ----------------------------------------------------------------- #
    graph_key: str = Field(..., alias="GRAPH_KEY")
    sharepoint_mode: SharePointMode = Field("drive_id", alias="SHAREPOINT_MODE")
    sharepoint_folder_url: str | None = Field(None, alias="SHAREPOINT_FOLDER_URL")
    sharepoint_hostname: str | None = Field(None, alias="SHAREPOINT_HOSTNAME")
    sharepoint_site_path: str | None = Field(None, alias="SHAREPOINT_SITE_PATH")
    sharepoint_drive_name: str = Field(
        "Documentos compartidos", alias="SHAREPOINT_DRIVE_NAME",
    )
    sharepoint_drive_id: str | None = Field(None, alias="SHAREPOINT_DRIVE_ID")
    graph_timeout_s: int = Field(60, alias="GRAPH_TIMEOUT_S", gt=0)

    # ----------------------------------------------------------------- #
    # Observabilidad.
    # ----------------------------------------------------------------- #
    log_level: str = Field("INFO", alias="LOG_LEVEL")
    log_dir: str = Field("logs", alias="LOG_DIR")

    model_config = SettingsConfigDict(
        env_file=_ENV_FILE,
        env_file_encoding="utf-8",
        extra="ignore",
        # Una variable vacía (como en .env.example) vale su defecto: así
        # ALTA_SIGRID_COMMIT= es simulación y DESDE= es feature apagada.
        env_ignore_empty=True,
    )

    # ----------------------------------------------------------------- #
    # Validación al arrancar: lo que no se puede leer, no arranca.
    # ----------------------------------------------------------------- #
    @field_validator("alta_sigrid_desde_utc")
    @classmethod
    def _desde_legible(cls, valor: str) -> str:
        try:
            leer_instante_utc(valor)
        except ValueError as exc:
            raise ValueError(
                f"ALTA_SIGRID_DESDE_UTC no es una fecha ISO 8601: {valor!r}",
            ) from exc
        return valor

    @field_validator("alta_sigrid_producto_por_defecto")
    @classmethod
    def _mapeo_valido(cls, valor: str) -> str:
        # R44: el motivo viaja en el ValueError (y de ahí al log de arranque).
        leer_mapeo(valor)
        return valor

    @field_validator("alta_sigrid_empide")
    @classmethod
    def _empide_entero(cls, valor: str) -> str:
        limpio = (valor or "").strip()
        if limpio and not limpio.isdigit():
            raise ValueError(f"ALTA_SIGRID_EMPIDE debe ser un entero: {valor!r}")
        return limpio

    # ----------------------------------------------------------------- #
    # Valores ya interpretados.
    # ----------------------------------------------------------------- #
    @property
    def desde(self) -> datetime | None:
        return leer_instante_utc(self.alta_sigrid_desde_utc)

    @property
    def commit_real(self) -> bool:
        """R19: real SOLO con el literal ``true`` (sin espacios ni mayúsculas)."""
        return self.alta_sigrid_commit == LITERAL_COMMIT_REAL

    @property
    def modo(self) -> str:
        return "real" if self.commit_real else "simulacion"

    @property
    def avisos_bloqueantes(self) -> frozenset[str]:
        return frozenset(
            c.strip() for c in self.alta_sigrid_avisos_bloqueantes.split(",") if c.strip()
        )

    @property
    def empide(self) -> int | None:
        return int(self.alta_sigrid_empide) if self.alta_sigrid_empide else None

    @property
    def mapeo_producto(self) -> dict[str, str]:
        return leer_mapeo(self.alta_sigrid_producto_por_defecto)

    @property
    def database_url(self) -> str:
        user = quote_plus(self.pg_user)
        password = quote_plus(self.pg_password)
        database = quote_plus(self.pg_db)
        return (
            f"postgresql+psycopg://{user}:{password}"
            f"@{self.pg_host}:{self.pg_port}/{database}"
        )
