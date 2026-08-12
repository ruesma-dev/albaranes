# ruesma_comun/colas/__init__.py
"""Adaptador de Azure Storage Queues del pipeline de albaranes.

Sustituye los clientes HTTP entre servicios. Modo local contra Azurite
(connection string) o nube con managed identity (account_url).
"""
from ruesma_comun.colas.conexion import (
    AZURITE_CONNECTION_STRING,
    COLA_EMAILS,
    COLA_EXTRACCION,
    COLA_FEEDBACK,
    COLA_PERSISTENCIA,
    COLA_VALORACION,
    ConfiguracionColas,
    FabricaColas,
    TODAS_LAS_COLAS,
    nombre_poison,
)
from ruesma_comun.colas.mensajes import (
    MensajeBase,
    MensajeExtraccion,
    MensajeFeedback,
    MensajeInvalidoError,
    MensajePersistencia,
    MensajeValoracion,
    desde_texto,
)
from ruesma_comun.colas.publicador import (
    PublicadorBestEffort,
    PublicadorColas,
)
from ruesma_comun.colas.consumidor import (
    ConfiguracionConsumidor,
    ConsumidorCola,
    ManejadorMensaje,
    ManejadorPoison,
)

from ruesma_comun.colas.arranque import (
    ConfiguracionColasAusenteError,
    construir_consumidor,
    construir_fabrica_desde_entorno,
    construir_publicador,
    ejecutar_worker,
)

__all__ = [
    # conexion
    "AZURITE_CONNECTION_STRING",
    "ConfiguracionColas",
    "FabricaColas",
    "COLA_EMAILS",
    "COLA_EXTRACCION",
    "COLA_PERSISTENCIA",
    "COLA_VALORACION",
    "COLA_FEEDBACK",
    "TODAS_LAS_COLAS",
    "nombre_poison",
    # mensajes
    "MensajeBase",
    "MensajeExtraccion",
    "MensajePersistencia",
    "MensajeValoracion",
    "MensajeFeedback",
    "desde_texto",
    "MensajeInvalidoError",
    # publicador
    "PublicadorColas",
    "PublicadorBestEffort",
    # consumidor
    "ConsumidorCola",
    "ConfiguracionConsumidor",
    "ManejadorMensaje",
    "ManejadorPoison",
    # arranque
    "construir_fabrica_desde_entorno",
    "construir_publicador",
    "construir_consumidor",
    "ejecutar_worker",
    "ConfiguracionColasAusenteError",
]
