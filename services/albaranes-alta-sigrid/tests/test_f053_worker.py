# tests/test_f053_worker.py
"""F-053 · T16 · worker de sv9 sobre ``q-feedback``, composición y arranque.

- Un resultado de negocio (cualquier estado del alta, también ``ignorar``)
  CONFIRMA el mensaje (se borra de la cola).
- Un fallo de infraestructura ANTES de reclamar (BBDD caída) lo deja en la cola
  para reintentarlo.
- Un mensaje de otro ``tipo`` va a poison sin tocar el servicio.
- La composición pasa al servicio TODO lo de ``Settings`` (modo, DESDE, Espera,
  tolerancia, avisos, usuario, mapeo; F-069: la Lista, y ya no un empide fijo)
  y ``main_worker`` arranca sobre
  ``COLA_FEEDBACK`` con ``tipo="feedback"``; con el mapeo roto no arranca (R44)
  y dice por qué en el log.

Sin red ni BBDD ni Azurite: clientes de cola falsos y ``ejecutar_worker``
sustituido.
"""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta

import pytest
from ruesma_comun.colas import COLA_FEEDBACK, MensajeFeedback, MensajeValoracion
from ruesma_comun.colas.consumidor import ConfiguracionConsumidor, ConsumidorCola

import main_worker
from domain.services.usuario_sigrid import Equivalencia
from application.alta_sigrid_service import ResultadoProceso
from domain.models.alta_models import AccionAlta, Decision, EstadoAlta, ModoAlta
from interface_adapters import composition
from interface_adapters.worker.alta_worker import construir_handler_alta
from tests.f053_fakes import Explota


@dataclass
class _Mensaje:
    content: str
    dequeue_count: int = 1


@dataclass
class ColaFalsa:
    pendientes: list[_Mensaje] = field(default_factory=list)
    borrados: list[_Mensaje] = field(default_factory=list)
    enviados: list[str] = field(default_factory=list)

    def receive_message(self, visibility_timeout=None):
        return self.pendientes.pop(0) if self.pendientes else None

    def delete_message(self, mensaje):
        self.borrados.append(mensaje)

    def send_message(self, cuerpo):
        self.enviados.append(cuerpo)


@dataclass
class ServicioFalso:
    resultado: ResultadoProceso = field(
        default_factory=lambda: ResultadoProceso(Decision.PROCESAR, EstadoAlta.SIMULADO))
    falla: bool = False
    llamadas: list[tuple[str, AccionAlta]] = field(default_factory=list)

    def procesar(self, document_id, accion):
        self.llamadas.append((document_id, AccionAlta(accion)))
        if self.falla:
            raise Explota("BBDD caída al reclamar")
        return self.resultado


def _consumir(cuerpo: str, servicio: ServicioFalso):
    cola, poison = ColaFalsa([_Mensaje(cuerpo)]), ColaFalsa()
    consumidor = ConsumidorCola(
        config=ConfiguracionConsumidor(nombre_cola=COLA_FEEDBACK, tipo_mensaje="feedback"),
        cliente=cola, cliente_poison=poison, handler=construir_handler_alta(servicio=servicio),
    )
    assert consumidor.procesar_uno() is True
    return cola, poison


@pytest.mark.parametrize("resultado", [
    ResultadoProceso(Decision.PROCESAR, EstadoAlta.SIMULADO),
    ResultadoProceso(Decision.PROCESAR, EstadoAlta.ERROR),
    ResultadoProceso(Decision.PROCESAR, EstadoAlta.INCIERTO),
    ResultadoProceso(Decision.IGNORAR, None, "no aprobado"),
    ResultadoProceso(Decision.A_INCIERTO, EstadoAlta.INCIERTO),
])
def test_f053_worker_resultado_de_negocio_confirma(resultado):
    servicio = ServicioFalso(resultado=resultado)
    cola, poison = _consumir(MensajeFeedback(document_id="d1", approved_by="ana").a_texto(), servicio)
    assert servicio.llamadas == [("d1", AccionAlta.ALTA)]
    assert len(cola.borrados) == 1 and poison.enviados == []


def test_f053_worker_pasa_la_accion_del_mensaje():
    servicio = ServicioFalso()
    _consumir(MensajeFeedback(document_id="d9", accion="verificar_anulacion").a_texto(), servicio)
    assert servicio.llamadas == [("d9", AccionAlta.VERIFICAR_ANULACION)]


def test_f053_worker_fallo_antes_de_reclamar_reencola():
    servicio = ServicioFalso(falla=True)
    cola, poison = _consumir(MensajeFeedback(document_id="d1").a_texto(), servicio)
    assert cola.borrados == [] and poison.enviados == []  # vuelve a aparecer


@pytest.mark.parametrize("cuerpo", [
    MensajeValoracion(document_id="d1").a_texto(),
    json.dumps({"tipo": "feedback", "document_id": "d1", "accion": "borrar"}),
    "no es json",
])
def test_f053_worker_mensaje_de_otro_tipo_a_poison(cuerpo):
    servicio = ServicioFalso()
    cola, poison = _consumir(cuerpo, servicio)
    assert servicio.llamadas == []
    assert poison.enviados == [cuerpo] and len(cola.borrados) == 1


# ------------------------------------------------------------------ #
# Composición y arranque
# ------------------------------------------------------------------ #
ENTORNO = {
    "PG_USER": "usuario", "PG_PASSWORD": "clave-de-mentira", "GRAPH_KEY": "token-de-mentira",
    "SHAREPOINT_DRIVE_ID": "drive-1", "SIGRID_API_BASE_URL": "http://sigrid.invalid",
    "SIGRID_API_FUNCTION_KEY": "clave-de-mentira",
    "ALTA_SIGRID_DESDE_UTC": "2026-10-01T00:00:00Z", "ALTA_SIGRID_COMMIT": "true",
    "ALTA_SIGRID_ESPERA_INCIERTO_MIN": "20", "ALTA_SIGRID_TOLERANCIA_EUR": "0.1",
    "ALTA_SIGRID_AVISOS_BLOQUEANTES": "producto_sin_historico,stock_negativo",
    "ALTA_SIGRID_USUARIO_RESPALDO": "USU_ALTA", "ALTA_SIGRID_EMPIDE": "2425207",
    "ALTA_SIGRID_EQUIVALENCIAS_USUARIO": '{"login1": {"empide": 1234567}}',
    "ALTA_SIGRID_PRODUCTO_POR_DEFECTO": '{"*": "MA9999", "alquiler_maquinaria": "QA9999"}',
}


def _settings(monkeypatch, **cambios):
    from config.settings import Settings

    for nombre, valor in {**ENTORNO, **cambios}.items():
        monkeypatch.setenv(nombre, valor)
    return Settings(_env_file=None)


def test_f053_worker_composicion_pasa_toda_la_configuracion(monkeypatch):
    servicio = composition.construir_servicio(_settings(monkeypatch))
    # Atributos privados a propósito: un parámetro que no llegue desde
    # Settings es un interruptor silencioso (lección de F-051, review H1).
    assert servicio.modo is ModoAlta.REAL
    assert servicio._desde == datetime(2026, 10, 1, tzinfo=UTC)
    assert servicio._espera == timedelta(minutes=20)
    assert servicio._tolerancia == pytest.approx(0.1)
    assert servicio._bloqueantes == frozenset({"producto_sin_historico", "stock_negativo"})
    # F-069 R4: el ALTA_SIGRID_EMPIDE que quede en el entorno ya no llega; la Lista, sí.
    assert servicio._respaldo == "USU_ALTA" and not hasattr(servicio._config, "empide")
    assert servicio._equivalencias == {"login1": Equivalencia(usu=None, empide=1234567)}
    assert dict(servicio._config.mapeo) == {"*": "MA9999", "alquiler_maquinaria": "QA9999"}
    assert type(servicio._repo).__name__ == "SqlAltaRepository"
    assert type(servicio._sigrid).__name__ == "SigridApiAltaClient"
    assert type(servicio._pdf).__name__ == "PdfSharePoint"


def test_f053_worker_composicion_en_simulacion_por_defecto(monkeypatch):
    monkeypatch.delenv("ALTA_SIGRID_COMMIT", raising=False)
    entorno = {k: v for k, v in ENTORNO.items() if k != "ALTA_SIGRID_COMMIT"}
    from config.settings import Settings

    for nombre, valor in entorno.items():
        monkeypatch.setenv(nombre, valor)
    servicio = composition.construir_servicio(Settings(_env_file=None))
    assert servicio.modo is ModoAlta.SIMULACION


def test_f053_worker_main_arranca_sobre_q_feedback(monkeypatch, tmp_path, caplog):
    ajustes = _settings(monkeypatch, LOG_DIR=str(tmp_path))
    monkeypatch.setattr(main_worker, "_cargar_entorno", lambda: None)
    monkeypatch.setattr(main_worker, "Settings", lambda: ajustes)
    capturado = {}

    def ejecutar_worker(**kwargs):
        capturado.update(kwargs)
        return 0

    monkeypatch.setattr(main_worker, "ejecutar_worker", ejecutar_worker)
    # dictConfig quitaría el manejador de caplog: el log real se prueba aparte.
    monkeypatch.setattr(main_worker, "configure_logging", lambda *a, **k: None)
    caplog.set_level(logging.INFO)
    assert main_worker.main() == 0
    assert capturado["nombre_cola"] == COLA_FEEDBACK == "q-feedback"
    assert capturado["tipo_mensaje"] == "feedback"
    assert capturado["emitido_por"] == "ca-sv9-alta-sigrid"
    assert callable(capturado["handler"])
    assert "modo=real" in caplog.text
    assert "clave-de-mentira" not in caplog.text


def _visibilidad_con(monkeypatch, tmp_path, **cambios) -> int:
    ajustes = _settings(monkeypatch, LOG_DIR=str(tmp_path), **cambios)
    monkeypatch.setattr(main_worker, "_cargar_entorno", lambda: None)
    monkeypatch.setattr(main_worker, "Settings", lambda: ajustes)
    monkeypatch.setattr(main_worker, "configure_logging", lambda *a, **k: None)
    capturado = {}

    def ejecutar_worker(**kwargs):
        capturado.update(kwargs)
        return 0

    monkeypatch.setattr(main_worker, "ejecutar_worker", ejecutar_worker)
    assert main_worker.main() == 0
    return capturado["visibilidad_s"]


def _peor_caso_s(t_sigrid: float, t_graph: float) -> float:
    """Peor caso de UN mensaje, contado a mano (review fase 1 · O1).

    sigrid-api con reintentos (lectura R14, previa y adjunto): 3 intentos de
    ``t_sigrid`` y esperas de 1 s y 2 s (tenacity, ``wait_exponential``).
    Grabación: una vez, 240 s. PDF: el token de Graph (5 intentos de
    ``t_graph`` con hasta 20 s entre ellos) y 4 peticiones (sitio, drive,
    descarga y redirección, en el peor modo)."""
    con_reintentos = 3 * t_sigrid + 1 + 2
    pdf = (5 * t_graph + 4 * 20) + 4 * t_graph
    return con_reintentos + con_reintentos + 240 + pdf + con_reintentos


def test_f053_o1_visibilidad_por_encima_del_peor_caso(monkeypatch, tmp_path):
    peor = _peor_caso_s(60, 60)
    assert peor == 1409  # 23,5 min: la visibilidad común de 600 s no basta
    visibilidad = _visibilidad_con(monkeypatch, tmp_path)
    assert visibilidad >= peor + 300  # con margen para la BBDD y el arranque
    assert visibilidad < 7 * 24 * 3600  # máximo de Azure Storage Queues


def test_f053_o1_la_visibilidad_sigue_a_los_timeouts_configurados(monkeypatch, tmp_path):
    peor = _peor_caso_s(120, 90)
    visibilidad = _visibilidad_con(monkeypatch, tmp_path, SIGRID_API_TIMEOUT_S="120",
                                   GRAPH_TIMEOUT_S="90")
    assert visibilidad >= peor + 300


def test_f053_o1_las_constantes_del_calculo_son_las_del_codigo(monkeypatch):
    """El cálculo usa los reintentos REALES del cliente y del token de Graph."""
    from ruesma_comun.graph.token_provider import GraphTokenProvider

    from infrastructure.sigrid import sigrid_api_alta_client as cliente

    servicio_sigrid = cliente.construir_desde_settings(_settings(monkeypatch))
    assert servicio_sigrid._intentos == cliente.INTENTOS_POR_DEFECTO == 3
    assert servicio_sigrid._espera_base == cliente.ESPERA_BASE_S == 1.0
    assert servicio_sigrid._timeout_grabacion == cliente.TIMEOUT_GRABACION_S == 240.0
    token = GraphTokenProvider("token-de-mentira", 60)
    assert token._max_attempts == main_worker.GRAPH_TOKEN_INTENTOS
    assert token._backoff_cap_s == main_worker.GRAPH_TOKEN_ESPERA_MAX_S


def test_f053_r44_main_no_arranca_con_el_mapeo_roto(monkeypatch, caplog):
    from config.settings import Settings

    for nombre, valor in ENTORNO.items():
        monkeypatch.setenv(nombre, valor)
    monkeypatch.setenv("ALTA_SIGRID_PRODUCTO_POR_DEFECTO", '{"sin_comodin": "MA9999"}')
    monkeypatch.setattr(main_worker, "_cargar_entorno", lambda: None)
    monkeypatch.setattr(main_worker, "Settings", lambda: Settings(_env_file=None))
    monkeypatch.setattr(main_worker, "ejecutar_worker", lambda **_: pytest.fail("arrancó"))
    caplog.set_level(logging.ERROR)
    assert main_worker.main() == 2
    assert "ALTA_SIGRID_PRODUCTO_POR_DEFECTO" in caplog.text


#: Secretos ficticios: ninguno puede acabar en el log de arranque (R35).
SECRETOS_FICTICIOS = {
    "PG_PASSWORD": "PGSECRETO-de-prueba-9f3a",
    "GRAPH_KEY": "GRAPHSECRETO-de-prueba-7b21",
    "SIGRID_API_FUNCTION_KEY": "FKSECRETO-de-prueba-c0de",
    "COLAS_CONNECTION_STRING": "AccountName=x;AccountKey=COLASSECRETO-de-prueba-55aa",
}


def test_f053_r35_configuracion_invalida_sin_secretos_en_el_log(monkeypatch, caplog):
    """Review fase 1 · H1: el ``ValidationError`` de ``Settings`` lleva en
    ``input_value`` TODO el entorno leído. El log de arranque dice qué campo
    falla y por qué (R44), nunca los valores."""
    from config.settings import Settings

    for nombre, valor in {**ENTORNO, **SECRETOS_FICTICIOS}.items():
        monkeypatch.setenv(nombre, valor)
    monkeypatch.delenv("PG_USER")  # falta un obligatorio: input_value = el entorno entero
    monkeypatch.setenv("ALTA_SIGRID_PRODUCTO_POR_DEFECTO", '{"sin_comodin": "MA9999"}')
    monkeypatch.setattr(main_worker, "_cargar_entorno", lambda: None)
    monkeypatch.setattr(main_worker, "Settings", lambda: Settings(_env_file=None))
    monkeypatch.setattr(main_worker, "ejecutar_worker", lambda **_: pytest.fail("arrancó"))
    caplog.set_level(logging.DEBUG)
    assert main_worker.main() == 2
    for secreto in SECRETOS_FICTICIOS.values():
        assert secreto not in caplog.text
    assert "input_value" not in caplog.text
    # El motivo sigue en el log: qué campo falla y por qué (R44).
    assert "PG_USER" in caplog.text and "Field required" in caplog.text
    assert "ALTA_SIGRID_PRODUCTO_POR_DEFECTO debe tener la clave '*'" in caplog.text


@pytest.mark.parametrize("variable", ["PG_PASSWORD", "GRAPH_KEY", "SIGRID_API_FUNCTION_KEY"])
def test_f053_r35_secreto_solo_en_el_entorno_no_sale_en_el_log(monkeypatch, caplog, variable):
    """Con un entorno corto pydantic no recorta ``input_value``: el secreto
    saldría entero. Es el caso que reprodujo el reviewer."""
    from config.settings import Settings

    for alias in [c.alias for c in Settings.model_fields.values() if c.alias]:
        monkeypatch.delenv(alias, raising=False)
    monkeypatch.setenv(variable, "S3CR3T0")
    monkeypatch.setattr(main_worker, "_cargar_entorno", lambda: None)
    monkeypatch.setattr(main_worker, "Settings", lambda: Settings(_env_file=None))
    monkeypatch.setattr(main_worker, "ejecutar_worker", lambda **_: pytest.fail("arrancó"))
    caplog.set_level(logging.DEBUG)
    assert main_worker.main() == 2
    assert "S3CR3T0" not in caplog.text
    assert "Field required" in caplog.text and "PG_USER" in caplog.text


def test_f053_worker_main_py_delega_en_main_worker(monkeypatch):
    import main

    monkeypatch.setattr(main_worker, "main", lambda: 7)
    assert main.main() == 7
