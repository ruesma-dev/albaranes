# tests/test_humo_colas.py
"""Test de humo del runtime de colas contra Azurite.

Requiere Azurite en marcha (docker compose -f local/docker-compose.azurite.yml
up -d, o `azurite-queue` vía npm). Si no hay Azurite, los tests se saltan.

Ejecutar:  pytest tests/test_humo_colas.py -v
"""
from __future__ import annotations

import time
import uuid

import pytest

from ruesma_comun.colas.conexion import ConfiguracionColas, FabricaColas
from ruesma_comun.colas.consumidor import ConfiguracionConsumidor, ConsumidorCola
from ruesma_comun.colas.mensajes import MensajeExtraccion
from ruesma_comun.colas.publicador import PublicadorColas

AZURITE_CONN = (
    "DefaultEndpointsProtocol=http;AccountName=devstoreaccount1;"
    "AccountKey=Eby8vdM02xNOcqFlqUwJPLlmEtlCDXJ1OUzFT50uSRZ6IFsuFq2UVErCz4I6"
    "tq/K1SZFPTOtr/KBHBeksoGMGw==;"
    "QueueEndpoint=http://127.0.0.1:10001/devstoreaccount1;"
)


@pytest.fixture(scope="module")
def fabrica() -> FabricaColas:
    fab = FabricaColas(ConfiguracionColas(connection_string=AZURITE_CONN))
    try:
        fab.cliente("humo-disponibilidad")
    except Exception:
        pytest.skip("Azurite no disponible en 127.0.0.1:10001")
    return fab


def _consumidor(fabrica: FabricaColas, cola: str, handler, **kwargs) -> ConsumidorCola:
    cfg = ConfiguracionConsumidor(
        nombre_cola=cola,
        tipo_mensaje="extraccion",
        visibilidad_s=kwargs.pop("visibilidad_s", 1),
        max_desencolados=kwargs.pop("max_desencolados", 5),
        espera_vacia_s=0.1,
    )
    return ConsumidorCola(
        config=cfg,
        cliente=fabrica.cliente(cola),
        cliente_poison=fabrica.cliente(f"{cola}-poison"),
        handler=handler,
        **kwargs,
    )


def test_publicar_y_consumir(fabrica: FabricaColas) -> None:
    cola = f"humo-{uuid.uuid4().hex[:8]}"
    publicador = PublicadorColas(fabrica, emitido_por="tests")
    doc_id = str(uuid.uuid4())
    publicador.publicar(cola, MensajeExtraccion(document_id=doc_id))

    recibidos: list[str] = []
    consumidor = _consumidor(fabrica, cola, lambda m: recibidos.append(m.document_id))

    assert consumidor.procesar_uno() is True
    assert recibidos == [doc_id]
    # El mensaje se borró: la cola está vacía.
    assert consumidor.procesar_uno() is False
    # Y nada llegó a poison.
    assert fabrica.cliente(f"{cola}-poison").receive_message() is None


def test_mensaje_invalido_va_a_poison_inmediatamente(fabrica: FabricaColas) -> None:
    cola = f"humo-{uuid.uuid4().hex[:8]}"
    fabrica.cliente(cola).send_message("esto no es JSON {{{")

    venenos: list[str] = []
    consumidor = _consumidor(
        fabrica,
        cola,
        lambda m: pytest.fail("no debería procesarse"),
        on_poison=lambda msg, cuerpo, motivo: venenos.append(motivo),
    )
    assert consumidor.procesar_uno() is True
    assert len(venenos) == 1
    assert fabrica.cliente(f"{cola}-poison").receive_message() is not None
    assert consumidor.procesar_uno() is False  # la cola original quedó limpia


def test_agotamiento_de_reintentos_envia_a_poison(fabrica: FabricaColas) -> None:
    cola = f"humo-{uuid.uuid4().hex[:8]}"
    publicador = PublicadorColas(fabrica, emitido_por="tests")
    publicador.publicar(cola, MensajeExtraccion(document_id="doc-fallon"))

    venenos: list[tuple[str | None, str]] = []

    def handler_que_falla(_msg) -> None:
        raise RuntimeError("fallo simulado del paso")

    consumidor = _consumidor(
        fabrica,
        cola,
        handler_que_falla,
        max_desencolados=1,
        visibilidad_s=1,
        on_poison=lambda msg, cuerpo, motivo: venenos.append(
            (msg.document_id if msg else None, motivo)
        ),
    )

    # Intento 1 (dequeue_count=1 ≤ max): el handler falla y el mensaje
    # queda en la cola hasta que expire la visibilidad.
    assert consumidor.procesar_uno() is True
    assert venenos == []

    time.sleep(1.3)  # expira la visibilidad → el mensaje reaparece

    # Intento 2 (dequeue_count=2 > max): va a poison ANTES de procesar.
    assert consumidor.procesar_uno() is True
    assert len(venenos) == 1
    assert venenos[0][0] == "doc-fallon"
    assert fabrica.cliente(f"{cola}-poison").receive_message() is not None
