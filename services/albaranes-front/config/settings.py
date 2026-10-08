# config/settings.py
from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path
from urllib.parse import quote_plus

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from ruesma_comun.alta_sigrid import (
    MAPEO_PRODUCTO_POR_DEFECTO_TEXTO,
    leer_instante_utc,
    leer_mapeo,
)

from domain.models.alta_sigrid_models import ConfigAltaSigrid

_ENV_FILE = Path(__file__).resolve().parents[1] / ".env"


class Settings(BaseSettings):
    """Configuración del servicio 4 (portal de revisión humana).

    REFACTOR "el sv3 es dueño de los contratos"
    -------------------------------------------
    Antes el sv4 tenía aquí variables ``SIGRID_API_*`` y un wiring
    duplicado del sv3 (cliente Sigrid + repository.replace_contratos_and_select
    + SharePointContratoPdfStorage). Eso era un acoplamiento incorrecto:
    el sv3 ya tenía el ``ContratoEnrichmentService`` con UPSERT por
    ``sigrid_ide`` y manejaba los PDFs. El sv4 duplicaba esa lógica
    con un viejo DELETE+INSERT que rompía la deduplicación.

    Refactor (mayo 2026): el sv4 deja de llamar a Sigrid directamente
    y llama al sv3 vía HTTP (``POST /v1/albaranes/{id}/re-fetch-contratos``).
    El sv3 reutiliza su enrichment con ``force_refetch=True`` y devuelve
    un outcome (status/message/...) que el sv4 reenvía al front tal cual.

    Consecuencias en este settings:
      * NO hay variables ``SIGRID_*`` — esas vivien solo en el .env del sv3.
      * Nuevas variables ``SV3_*`` (base_url, path, timeout) — análogas
        a las ``SV7_*`` que ya teníamos.
      * Cero variables relacionadas con SharePoint para contratos —
        ese caso lo cubre el sv3.

    Lo que se mantiene
    -------------------
    PostgreSQL (mismo cluster que sv3, lectura del merge para pintar
    el portal); Graph + SharePoint solo para preview del PDF del
    propio albarán (no contratos); cliente al orquestador sv7 para
    eventos de revisión.
    """

    # ------------------------------------------------------------ #
    # BBDD compartida.
    # ------------------------------------------------------------ #
    pg_host: str = Field("localhost", alias="PG_HOST")
    pg_port: int = Field(5432, alias="PG_PORT")
    pg_db: str = Field("albaranes", alias="PG_DB")
    pg_user: str = Field("postgres", alias="PG_USER")
    pg_password: str = Field(..., alias="PG_PASSWORD")

    pg_admin_db: str = Field("postgres", alias="PG_ADMIN_DB")
    pg_admin_user: str = Field("postgres", alias="PG_ADMIN_USER")
    pg_admin_password: str = Field(..., alias="PG_ADMIN_PASSWORD")
    auto_create_database: bool = Field(True, alias="AUTO_CREATE_DATABASE")

    # ------------------------------------------------------------ #
    # Graph + SharePoint — SOLO para previsualización del PDF del
    # propio albarán en el portal. El PDF de contrato lo gestiona el
    # sv3 (no este servicio).
    # ------------------------------------------------------------ #
    graph_key: str | None = Field(None, alias="GRAPH_KEY")
    sharepoint_drive_id: str | None = Field(
        None, alias="SHAREPOINT_DRIVE_ID",
    )
    graph_timeout_s: int = Field(60, alias="GRAPH_TIMEOUT_S")

    # ------------------------------------------------------------ #
    # API + presentación + UX.
    # ------------------------------------------------------------ #
    api_host: str = Field("127.0.0.1", alias="API_HOST")
    api_port: int = Field(8004, alias="API_PORT")
    log_level: str = Field("INFO", alias="LOG_LEVEL")
    log_dir: str = Field("logs", alias="LOG_DIR")
    service_version: str = Field("1.0.0", alias="SERVICE_VERSION")
    app_title: str = Field(
        "Revisión de Albaranes IA", alias="APP_TITLE",
    )
    default_page_size: int = Field(25, alias="DEFAULT_PAGE_SIZE")
    max_page_size: int = Field(100, alias="MAX_PAGE_SIZE")
    default_reviewer: str | None = Field(None, alias="DEFAULT_REVIEWER")

    # ------------------------------------------------------------ #
    # Colas (sustituyen a los antiguos clientes HTTP a sv7 y sv3).
    #
    # sv4 ya NO llama por HTTP a sv7 (disuelto) ni a sv3. En su lugar
    # publica mensajes en las colas del sistema mediante el publicador
    # de ``ruesma_comun.colas`` (best-effort):
    #   - Elegir/cambiar contrato  → MensajeValoracion(force=True) → q-valoracion
    #   - Aprobar documento        → MensajeFeedback              → q-feedback
    #   - Re-fetch de contratos    → MensajePersistencia(force=True) → q-persistencia
    #   - Purga (hard-delete)      → limpieza directa de workflow_runs (BBDD)
    #
    # La conexión a las colas la resuelve ``construir_publicador`` leyendo
    # del ENTORNO (no de este settings):
    #   - COLAS_ACCOUNT_URL          (managed identity en Azure)
    #   - COLAS_CONNECTION_STRING    (local/Azurite)
    # Por eso aquí no hay campos COLAS_*: ``extra="ignore"`` los tolera y
    # comun los consume directamente vía os.environ.
    # ------------------------------------------------------------ #
    # ------------------------------------------------------------ #
    # Sigrid API — SOLO LECTURA para los desplegables de cabecera
    # (elegir proveedor / obra). NO reintroduce el camino de escritura
    # de contratos (UPSERT/PDF), que sigue yendo por sv3. Estas
    # consultas (proveedores de una obra, lista de obras) son lookups
    # de referencia para la UI. Mismos valores que el .env del sv3.
    # Si falta alguna credencial, los endpoints /api/sigrid/* devuelven
    # ok=false y el front mantiene la entrada manual.
    # ------------------------------------------------------------ #
    sigrid_api_base_url: str | None = Field(
        default=None, alias="SIGRID_API_BASE_URL",
    )
    sigrid_api_function_key: str | None = Field(
        default=None, alias="SIGRID_API_FUNCTION_KEY",
    )
    sigrid_api_database: str | None = Field(
        default=None, alias="SIGRID_API_DATABASE",
    )
    sigrid_api_timeout_s: float = Field(30.0, alias="SIGRID_API_TIMEOUT_S")

    # ------------------------------------------------------------ #
    # F-053 · Alta en Sigrid (design §7). MISMO valor que en sv9 (el
    # script de despliegue las pone desde una sola variable):
    #   - ALTA_SIGRID_DESDE_UTC: vacía = feature apagada (R3): sv4 no
    #     publica ni pinta nada del alta ni del producto.
    #   - ALTA_SIGRID_ESPERA_INCIERTO_MIN: minutos tras el último
    #     intento para ofrecer «Solicitar alta» en en_curso/incierto (R30).
    #   - ALTA_SIGRID_PRODUCTO_POR_DEFECTO: JSON familia -> producto con
    #     clave '*' (R40, R41); mal formado = sv4 no arranca (R44).
    # Una variable vacía vale su defecto, como en sv9.
    # ------------------------------------------------------------ #
    alta_sigrid_desde_utc: str = Field("", alias="ALTA_SIGRID_DESDE_UTC")
    alta_sigrid_espera_incierto_min: int = Field(
        15, alias="ALTA_SIGRID_ESPERA_INCIERTO_MIN", ge=0,
    )
    alta_sigrid_producto_por_defecto: str = Field(
        MAPEO_PRODUCTO_POR_DEFECTO_TEXTO, alias="ALTA_SIGRID_PRODUCTO_POR_DEFECTO",
    )

    @field_validator("alta_sigrid_espera_incierto_min", mode="before")
    @classmethod
    def _espera_vacia_es_defecto(cls, valor: object) -> object:
        return 15 if isinstance(valor, str) and not valor.strip() else valor

    @field_validator("alta_sigrid_producto_por_defecto", mode="before")
    @classmethod
    def _mapeo_vacio_es_defecto(cls, valor: object) -> object:
        if isinstance(valor, str) and not valor.strip():
            return MAPEO_PRODUCTO_POR_DEFECTO_TEXTO
        return valor

    @field_validator("alta_sigrid_producto_por_defecto")
    @classmethod
    def _mapeo_valido(cls, valor: str) -> str:
        # R44: el motivo viaja en el ValueError (y de ahí al log de arranque).
        leer_mapeo(valor)
        return valor

    @field_validator("alta_sigrid_desde_utc")
    @classmethod
    def _desde_legible(cls, valor: str) -> str:
        try:
            leer_instante_utc(valor)
        except ValueError as exc:
            raise ValueError(
                "ALTA_SIGRID_DESDE_UTC no es una fecha ISO 8601",
            ) from exc
        return valor

    @property
    def alta_sigrid_desde(self) -> datetime | None:
        return leer_instante_utc(self.alta_sigrid_desde_utc)

    @property
    def alta_sigrid_espera(self) -> timedelta:
        return timedelta(minutes=self.alta_sigrid_espera_incierto_min)

    @property
    def mapeo_producto(self) -> dict[str, str]:
        return leer_mapeo(self.alta_sigrid_producto_por_defecto)

    @property
    def config_alta_sigrid(self) -> ConfigAltaSigrid:
        return ConfigAltaSigrid(
            desde=self.alta_sigrid_desde,
            espera=self.alta_sigrid_espera,
            mapeo=self.mapeo_producto,
        )

    @property
    def sigrid_lookup_enabled(self) -> bool:
        return bool(
            (self.sigrid_api_base_url or "").strip()
            and (self.sigrid_api_function_key or "").strip()
            and (self.sigrid_api_database or "").strip()
        )

    model_config = SettingsConfigDict(
        env_file=_ENV_FILE,
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def database_url(self) -> str:
        user = quote_plus(self.pg_user)
        password = quote_plus(self.pg_password)
        database = quote_plus(self.pg_db)
        return (
            f"postgresql+psycopg://{user}:{password}"
            f"@{self.pg_host}:{self.pg_port}/{database}"
        )

    @property
    def admin_database_url(self) -> str:
        user = quote_plus(self.pg_admin_user)
        password = quote_plus(self.pg_admin_password)
        database = quote_plus(self.pg_admin_db)
        return (
            f"postgresql+psycopg://{user}:{password}"
            f"@{self.pg_host}:{self.pg_port}/{database}"
        )

    @property
    def preview_enabled(self) -> bool:
        return bool(self.graph_key and self.sharepoint_drive_id)
