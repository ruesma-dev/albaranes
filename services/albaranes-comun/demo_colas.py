# demo_colas.py
"""Demo/test del adaptador de colas (paquete ``ruesma_comun.colas``) contra Azurite.

Valida lo que sustituye a las llamadas HTTP entre servicios:

  ESCENARIO 1 — Encadenado del pipeline:
      productor (sv1) -> q-extraccion -> worker sv2 -> q-persistencia -> worker sv3
  ESCENARIO 2 — Reintento + cola poison:
      un handler que siempre falla; el mensaje reaparece por visibilidad y,
      al superar max_desencolados, acaba en la cola *-poison.

Requisito: Azurite levantado y escuchando en el puerto 10001 (ver INSTRUCCIONES).
Uso:  python demo_colas.py
"""
from __future__ import annotations

import logging
import sys
import time

from ruesma_comun.colas import (
    AZURITE_CONNECTION_STRING,
    COLA_EXTRACCION,
    COLA_PERSISTENCIA,
    COLA_VALORACION,
    ConfiguracionColas,
    ConfiguracionConsumidor,
    ConsumidorCola,
    FabricaColas,
    MensajeBase,
    MensajeExtraccion,
    MensajePersistencia,
    MensajeValoracion,
    PublicadorColas,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s | %(message)s",
)
logging.getLogger("azure").setLevel(logging.WARNING)
log = logging.getLogger("demo")


def _fabrica() -> FabricaColas:
    return FabricaColas(
        ConfiguracionColas(connection_string=AZURITE_CONNECTION_STRING)
    )


def _vaciar(fabrica: FabricaColas, nombre_cola: str) -> None:
    """Deja la cola y su poison vacías antes del escenario."""
    fabrica.cliente(nombre_cola).clear_messages()
    fabrica.cliente_poison(nombre_cola).clear_messages()


def _contar_poison(fabrica: FabricaColas, nombre_cola: str) -> int:
    props = fabrica.cliente_poison(nombre_cola).get_queue_properties()
    return int(props.approximate_message_count or 0)


# --------------------------------------------------------------------------- #
def escenario_encadenado(fabrica: FabricaColas) -> None:
    log.info("=== ESCENARIO 1: encadenado de colas ===")
    _vaciar(fabrica, COLA_EXTRACCION)
    _vaciar(fabrica, COLA_PERSISTENCIA)

    pub = PublicadorColas(fabrica, emitido_por="demo-sv1")

    # 1) Productor: lo que hoy haría sv1/sv7 al recibir el email.
    docs = ["DOC-1001", "DOC-1002", "DOC-1003"]
    for doc in docs:
        pub.publicar(
            COLA_EXTRACCION,
            MensajeExtraccion(document_id=doc, correlation_key=f"corr-{doc}"),
        )
    log.info("Productor: encolados %s en %s", len(docs), COLA_EXTRACCION)

    # 2) Worker sv2 (simulado): procesa y reenvía a q-persistencia.
    procesados_sv2: list[str] = []

    def handler_sv2(m: MensajeBase) -> None:
        log.info("[sv2] extrae document_id=%s -> %s", m.document_id, COLA_PERSISTENCIA)
        procesados_sv2.append(m.document_id)
        pub.publicar(COLA_PERSISTENCIA, MensajePersistencia(document_id=m.document_id))

    cons_sv2 = ConsumidorCola(
        config=ConfiguracionConsumidor(
            nombre_cola=COLA_EXTRACCION, tipo_mensaje="extraccion", visibilidad_s=30
        ),
        cliente=fabrica.cliente(COLA_EXTRACCION),
        cliente_poison=fabrica.cliente_poison(COLA_EXTRACCION),
        handler=handler_sv2,
    )
    for _ in range(20):
        if not cons_sv2.procesar_uno():
            break
    assert sorted(procesados_sv2) == docs, procesados_sv2

    # 3) Worker sv3 (simulado): consume q-persistencia.
    procesados_sv3: list[str] = []

    def handler_sv3(m: MensajeBase) -> None:
        log.info("[sv3] persiste document_id=%s", m.document_id)
        procesados_sv3.append(m.document_id)

    cons_sv3 = ConsumidorCola(
        config=ConfiguracionConsumidor(
            nombre_cola=COLA_PERSISTENCIA, tipo_mensaje="persistencia", visibilidad_s=30
        ),
        cliente=fabrica.cliente(COLA_PERSISTENCIA),
        cliente_poison=fabrica.cliente_poison(COLA_PERSISTENCIA),
        handler=handler_sv3,
    )
    for _ in range(20):
        if not cons_sv3.procesar_uno():
            break
    assert sorted(procesados_sv3) == docs, procesados_sv3
    log.info("ESCENARIO 1 OK: 3 docs fluyeron extraccion -> persistencia\n")


# --------------------------------------------------------------------------- #
def escenario_reintento_y_poison(fabrica: FabricaColas) -> None:
    log.info("=== ESCENARIO 2: reintento + poison ===")
    _vaciar(fabrica, COLA_VALORACION)

    pub = PublicadorColas(fabrica, emitido_por="demo")
    pub.publicar(COLA_VALORACION, MensajeValoracion(document_id="DOC-FALLO"))

    intentos = {"n": 0}

    def handler_que_falla(m: MensajeBase) -> None:
        intentos["n"] += 1
        log.info("[falla] intento=%s document_id=%s", intentos["n"], m.document_id)
        raise RuntimeError("fallo simulado")

    # visibilidad=1s -> reaparece en 1s; max_desencolados=3 -> a la 4ª entrega
    # va a poison ANTES de procesar.
    cons = ConsumidorCola(
        config=ConfiguracionConsumidor(
            nombre_cola=COLA_VALORACION,
            tipo_mensaje="valoracion",
            visibilidad_s=1,
            max_desencolados=3,
        ),
        cliente=fabrica.cliente(COLA_VALORACION),
        cliente_poison=fabrica.cliente_poison(COLA_VALORACION),
        handler=handler_que_falla,
    )

    for _ in range(15):
        cons.procesar_uno()
        if _contar_poison(fabrica, COLA_VALORACION) >= 1:
            break
        time.sleep(1.2)  # deja que el mensaje reaparezca

    log.info("intentos totales=%s", intentos["n"])
    assert intentos["n"] >= 3, f"esperaba >=3 reintentos, hubo {intentos['n']}"
    assert _contar_poison(fabrica, COLA_VALORACION) >= 1, "debería estar en poison"
    log.info(
        "ESCENARIO 2 OK: reintentado %s veces y movido a poison\n", intentos["n"]
    )


# --------------------------------------------------------------------------- #
def main() -> int:
    fabrica = _fabrica()
    try:
        fabrica.cliente("q-conectividad")  # crea cola -> prueba conexión
    except Exception as exc:  # noqa: BLE001
        log.error("No conecto con Azurite (%s). ¿Levantado en :10001?", exc)
        return 2

    escenario_encadenado(fabrica)
    escenario_reintento_y_poison(fabrica)
    log.info("TODOS LOS ESCENARIOS OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
