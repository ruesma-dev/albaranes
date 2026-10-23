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
  ``ALTA_SIGRID_USUARIO_RESPALDO`` (v8, R47: login de ``dbo.usu`` que va en
  ``usu`` cuando quien aprobó no casa con uno; SIN defecto en código: vacía,
  esas altas van a ``error``, R48), ``ALTA_SIGRID_EQUIVALENCIAS_USUARIO``
  (F-069: la Lista de excepciones, JSON Login → ``{"usu"?, "empide"?}``; vacía
  es lo normal; mal escrita = no arranca, R2) y
  ``ALTA_SIGRID_PRODUCTO_POR_DEFECTO`` (JSON familia → producto, con ``*``;
  mal formado = no arranca, R44). DESDE, Espera y mapeo llevan el MISMO valor
  en sv4. La variable del empleado fijo de F-053 ya no se lee (F-069 R4): el
  ``empide`` sale de la resolución por documento; si queda en el entorno, se
  ignora (``extra="ignore"``).

El resto, con los nombres de sv3/sv6: sigrid-api, PostgreSQL, Graph/SharePoint
y log. Las colas se leen del entorno en ``ruesma_comun.colas.arranque``.
``SIGRID_API_FUNCTION_KEY`` y ``PG_PASSWORD`` son secretos: nunca en el repo.
"""
from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Literal
from urllib.parse import quote_plus

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from ruesma_comun.alta_sigrid import (
    MAPEO_PRODUCTO_POR_DEFECTO_TEXTO,
    leer_instante_utc,
    leer_mapeo,
)

from domain.services.usuario_sigrid import Equivalencia, leer_equivalencias

_ENV_FILE = Path(__file__).resolve().parents[1] / ".env"

SharePointMode = Literal["drive_id", "folder_url", "site_path"]

#: Único valor de ``ALTA_SIGRID_COMMIT`` que activa el modo real.
LITERAL_COMMIT_REAL = "true"


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
    usuario_respaldo: str = Field("", alias="ALTA_SIGRID_USUARIO_RESPALDO")
    alta_sigrid_equivalencias_usuario: str = Field("", alias="ALTA_SIGRID_EQUIVALENCIAS_USUARIO")
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

    @field_validator("alta_sigrid_equivalencias_usuario")
    @classmethod
    def _lista_valida(cls, valor: str) -> str:
        # F-069 R2: el motivo y la clave viajan en el ValueError (y de ahí al
        # log de arranque, como R44).
        leer_equivalencias(valor)
        return valor

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
    def equivalencias(self) -> dict[str, Equivalencia]:
        """La Lista de excepciones por Login (F-069 R1); vacía es lo normal."""
        return leer_equivalencias(self.alta_sigrid_equivalencias_usuario)

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
