# config/settings.py
from __future__ import annotations

from pathlib import Path
from urllib.parse import quote_plus

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

_ENV_FILE = Path(__file__).resolve().parents[1] / ".env"


class Settings(BaseSettings):
    """Configuración del servicio 6 (valuation-persistence).

    Este servicio orquesta al servicio 5 (HTTP), aplica las reglas
    deterministas de valoración (conversión unidad, reconciliación
    precios, matching partida) y persiste en 3 tablas nuevas.
    """

    # BBDD (misma que svc 3 y svc 5; escribe)
    pg_host: str = Field("localhost", alias="PG_HOST")
    pg_port: int = Field(5432, alias="PG_PORT")
    pg_db: str = Field("albaranes", alias="PG_DB")
    pg_user: str = Field(..., alias="PG_USER")
    pg_password: str = Field(..., alias="PG_PASSWORD")

    # Cliente HTTP contra el servicio 5
    valuation_api_base_url: str = Field(
        "http://127.0.0.1:8002",
        alias="VALUATION_API_BASE_URL",
    )
    valuation_api_timeout_s: float = Field(
        300.0,
        alias="VALUATION_API_TIMEOUT_S",
    )

    # Registro de unidades (YAML con factores por categoría)
    unit_registry_yaml_path: str = Field(
        "config/unit_registry.yaml",
        alias="UNIT_REGISTRY_YAML_PATH",
    )

    # Reglas numéricas (pueden ajustarse por .env sin tocar código)
    price_tolerance_pct: float = Field(
        2.0,
        alias="PRICE_TOLERANCE_PCT",
        description="Tolerancia (%) para considerar que precio 1a y 1b "
                    "coinciden.",
    )
    importe_tolerance_pct: float = Field(
        5.0,
        alias="IMPORTE_TOLERANCE_PCT",
        description="Tolerancia (%) entre importe declarado del albarán "
                    "y el calculado.",
    )

    # Código literal que identifica 'almacén/acopio' en el albarán
    alm_codigo_partida: str = Field("ALM", alias="ALM_CODIGO_PARTIDA")

    # ----------------------------------------------------------------- #
    # F-051 · almacén por línea.
    #
    # Una línea base sin partida en el albarán va a ALMACÉN
    # (codigo_partida_final vacío, partida_action 'almacen_sin_partida')
    # en vez de copiar la partida de la línea de contrato casada. False
    # = valorar exactamente como antes de F-051 (interruptor de vuelta
    # atrás sin desplegar).
    #
    # FAMILIAS_DESTINADAS (CSV, sin distinguir mayúsculas ni espacios;
    # vacío = ninguna): una línea en almacén de esas familias se marca
    # para revisión NO bloqueante (partida_ausente_familia_destinada).
    # ----------------------------------------------------------------- #
    almacen_sin_partida_enabled: bool = Field(
        True,
        alias="ALMACEN_SIN_PARTIDA_ENABLED",
    )
    familias_destinadas: str = Field(
        "hormigon,mortero,combustible,alquiler_maquinaria,residuos",
        alias="FAMILIAS_DESTINADAS",
    )

    # ----------------------------------------------------------------- #
    # F-076 · la partida se normaliza contra las de la obra.
    #
    # sv6 LEE de sigrid-api (solo ``POST /api/sql/read``) las partidas hoja
    # de la obra del albarán y, antes de sus reglas, cambia la partida leída
    # por el código exacto de la lista cuando la equivalencia es segura
    # (``CI.04.18`` => ``CI.4.18``). Sin URL, clave o base de datos, o con
    # sigrid-api caído, se valora como siempre (R11): nunca falla.
    # PARTIDAS_OBRA_NORMALIZAR_ENABLED=false es el interruptor de vuelta
    # atrás sin desplegar. Caché por réplica: TTL, obras en memoria y cuánto
    # se recuerda un fallo antes de reconsultar.
    # ----------------------------------------------------------------- #
    sigrid_api_base_url: str | None = Field(None, alias="SIGRID_API_BASE_URL")
    sigrid_api_function_key: str | None = Field(None, alias="SIGRID_API_FUNCTION_KEY")
    sigrid_api_database: str | None = Field(None, alias="SIGRID_API_DATABASE")
    sigrid_api_timeout_s: float = Field(30.0, alias="SIGRID_API_TIMEOUT_S")
    partidas_obra_normalizar_enabled: bool = Field(
        True,
        alias="PARTIDAS_OBRA_NORMALIZAR_ENABLED",
    )
    partidas_obra_ttl_s: float = Field(21600.0, alias="PARTIDAS_OBRA_TTL_S")
    partidas_obra_max_obras: int = Field(64, alias="PARTIDAS_OBRA_MAX_OBRAS")
    partidas_obra_fallo_ttl_s: float = Field(300.0, alias="PARTIDAS_OBRA_FALLO_TTL_S")

    # ----------------------------------------------------------------- #
    # F-111 · una línea de residuos sin partida no va a almacén: se le
    # busca partida en el capítulo de gestión de residuos de la obra
    # (con una candidata, esa; con varias, la elige la IA de sv5 en
    # ``POST /v1/albaranes/partida-residuos``, misma VALUATION_API_BASE_URL).
    # Usa el mismo lector de sigrid-api y la misma caché que F-076.
    # PARTIDA_RESIDUOS_ENABLED=false es la vuelta atrás sin imagen (R29).
    # ----------------------------------------------------------------- #
    partida_residuos_enabled: bool = Field(
        True,
        alias="PARTIDA_RESIDUOS_ENABLED",
    )

    # ----------------------------------------------------------------- #
    # Bloque 1 (may 2026): CONCILIACIÓN de modificadores (líneas
    # sintéticas) contra la tabla de líneas de contrato de Sigrid.
    #
    # Si True (recomendado), cada sintética de hormigón se enlaza con su
    # línea de incremento en la MISMA partida que la base
    # (matched_contrato_line_id) para que concilie igual que la base. El
    # precio SIGUE priorizando el PDF; la línea de Sigrid solo aporta
    # precio como fallback cuando el PDF no lo trae. Si False, se
    # mantiene el comportamiento anterior (sin enlace de las sintéticas)
    # — interruptor de seguridad.
    # ----------------------------------------------------------------- #
    modifier_table_match_enabled: bool = Field(
        True,
        alias="MODIFIER_TABLE_MATCH_ENABLED",
        description="Si True, las líneas sintéticas concilian contra la "
                    "tabla de Sigrid en la partida de la base. El precio "
                    "prioriza el PDF; la tabla es fallback de precio.",
    )

    # ----------------------------------------------------------------- #
    # Schema integrity.
    #
    # Si está activado (recomendado en local y en stage; opcional en
    # prod), al arrancar se ejecuta un chequeo de drift que compara
    # el ORM con la BBDD real y avisa por log si hay columnas
    # ausentes. NO modifica nada — solo diagnóstico.
    # ----------------------------------------------------------------- #
    schema_drift_check_enabled: bool = Field(
        True,
        alias="SCHEMA_DRIFT_CHECK_ENABLED",
        description="Si True, al arrancar compara columnas del ORM con "
                    "la BBDD y avisa por log si hay drift.",
    )

    api_host: str = Field("127.0.0.1", alias="API_HOST")
    api_port: int = Field(8003, alias="API_PORT")
    log_level: str = Field("INFO", alias="LOG_LEVEL")
    log_dir: str = Field("logs", alias="LOG_DIR")
    service_version: str = Field("1.0.0", alias="SERVICE_VERSION")

    model_config = SettingsConfigDict(
        env_file=_ENV_FILE,
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def sigrid_api_configurada(self) -> bool:
        """(F-076 R17) URL, clave y base de datos de sigrid-api presentes."""
        return all(
            (valor or "").strip()
            for valor in (
                self.sigrid_api_base_url,
                self.sigrid_api_function_key,
                self.sigrid_api_database,
            )
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
