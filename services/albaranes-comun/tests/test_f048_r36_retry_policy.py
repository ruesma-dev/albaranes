# tests/test_f048_r36_retry_policy.py
"""F-048 · R36 en comun (CR-C4 de la review del bloque C2): ``retry_policy``
no escribe el texto del correo en el log.

Un SDK puede citar la peticion en el mensaje de su error, y la peticion
lleva el bloque del correo. ``run_with_retry`` escribe ``str(exc)``
recortado en TRES logs: error no reintentable (WARNING, 300), reintentos
agotados (ERROR, 300) e intento fallido que se reintenta (WARNING, 200).
Los tres pasan por ``_mensaje_para_log``, que redacta ANTES de recortar.

Vive en la suite de COMUN a proposito: la campana de mutacion muta comun
contra su propia suite, y un test en sv2 no mataria ningun mutante de aqui.

Sin red y sin LLM. Textos inventados, con el centinela ``CENTINELA-F048``.
"""
from __future__ import annotations

import logging

import pytest
from ruesma_comun.correo import (
    MARCA_INICIO,
    construir_contexto_correo,
    render_bloque_correo,
)
from ruesma_comun.llm.retry_policy import RetryPolicy, _mensaje_para_log, run_with_retry

CENTINELA = "CENTINELA-F048"
CENTINELA_ASUNTO = "ASUNTO-CENTINELA-F048"
CORREO = construir_contexto_correo(
    f"Albaran obra 945 {CENTINELA_ASUNTO}",
    f"Hola, os paso el albaran de la 945.\n{CENTINELA} datos personales de prueba",
)
LOGGER = "ruesma_comun.llm.retry_policy"
SIN_ESPERA = {"backoff_base_s": 0.0, "backoff_cap_s": 0.0}


class _ErrorApi(Exception):
    def __init__(self, mensaje: str, status_code: int) -> None:
        super().__init__(mensaje)
        self.status_code = status_code


def _error_que_cita_el_bloque(status_code: int) -> _ErrorApi:
    """Un SDK que cita la peticion justo desde donde empieza el correo."""
    bloque = render_bloque_correo(CORREO)
    return _ErrorApi(
        f"Error {status_code}: peticion invalida cerca de: {bloque[bloque.index(MARCA_INICIO):]}",
        status_code,
    )


def _lanzar(error: BaseException, reintentos: int, caplog) -> list[logging.LogRecord]:
    def _llamada():
        raise error

    with caplog.at_level(logging.DEBUG, logger=LOGGER), pytest.raises(type(error)):
        run_with_retry(
            provider="openai", operation=_llamada,
            policy=RetryPolicy(max_retries=reintentos, **SIN_ESPERA),
        )
    return [r for r in caplog.records if r.name == LOGGER]


def _registro(registros, nivel: int, frase: str) -> logging.LogRecord:
    candidatos = [r for r in registros if r.levelno == nivel and frase in r.getMessage()]
    assert len(candidatos) == 1, [r.getMessage() for r in registros]
    return candidatos[0]


def _msg(registro: logging.LogRecord) -> str:
    """El argumento ``msg=`` tal cual llego al log (el que sale de ``_mensaje_para_log``)."""
    return next(a for a in registro.args if isinstance(a, str) and a.startswith("Error "))


# ---------------------------------------------------------------- #
# Precondicion: sin redactar, el recorte NO salva el correo.
# ---------------------------------------------------------------- #
def test_f048_r36_el_error_de_prueba_lleva_el_correo_dentro_del_recorte():
    error = _error_que_cita_el_bloque(400)

    assert CENTINELA in str(error)[:200]
    assert CENTINELA_ASUNTO in str(error)[:200]


# ---------------------------------------------------------------- #
# La funcion.
# ---------------------------------------------------------------- #
@pytest.mark.parametrize("limite", [200, 300])
def test_f048_r36_mensaje_para_log_redacta_el_bloque_y_recorta(limite):
    mensaje = _mensaje_para_log(_error_que_cita_el_bloque(400), limite)

    assert mensaje.startswith("Error 400: peticion invalida cerca de: [correo omitido: sha256=")
    assert CENTINELA not in mensaje
    assert CENTINELA_ASUNTO not in mensaje
    assert len(mensaje) <= limite


@pytest.mark.parametrize("limite", [200, 300])
def test_f048_r36_mensaje_para_log_sin_correo_es_el_de_siempre(limite):
    """Sin bloque del correo, el mensaje es ``str(exc)`` recortado, como antes de F-048."""
    texto = "Error 500: " + "x" * 400
    assert _mensaje_para_log(_ErrorApi(texto, 500), limite) == texto[:limite]


# ---------------------------------------------------------------- #
# Los tres caminos de log.
# ---------------------------------------------------------------- #
def _sin_correo(registro: logging.LogRecord) -> None:
    texto = registro.getMessage()
    assert "[correo omitido: sha256=" in texto
    assert CENTINELA not in texto
    assert CENTINELA_ASUNTO not in texto


def test_f048_r36_camino_no_reintentable_no_loguea_el_correo(caplog):
    registros = _lanzar(_error_que_cita_el_bloque(400), 2, caplog)

    registro = _registro(registros, logging.WARNING, "error NO retryable")
    _sin_correo(registro)
    assert len(registros) == 1  # no reintenta


def test_f048_r36_camino_reintentos_agotados_no_loguea_el_correo(caplog):
    registros = _lanzar(_error_que_cita_el_bloque(503), 1, caplog)

    _sin_correo(_registro(registros, logging.ERROR, "agotados reintentos"))


def test_f048_r36_camino_intento_que_se_reintenta_no_loguea_el_correo(caplog):
    registros = _lanzar(_error_que_cita_el_bloque(503), 1, caplog)

    _sin_correo(_registro(registros, logging.WARNING, "falló con error retryable"))


def test_f048_r36_ningun_registro_del_ciclo_contiene_el_correo(caplog):
    registros = _lanzar(_error_que_cita_el_bloque(503), 2, caplog)

    todo = "\n".join(r.getMessage() for r in registros)
    # 3 intentos: 2 fallos que se reintentan, 2 avisos de «intento n/3» y 1 agotado.
    assert todo.count("[llm-retry]") == 5
    assert CENTINELA not in todo
    assert CENTINELA_ASUNTO not in todo


@pytest.mark.parametrize(
    ("status_code", "reintentos", "nivel", "frase", "limite"),
    [
        (400, 0, logging.WARNING, "error NO retryable", 300),
        (503, 0, logging.ERROR, "agotados reintentos", 300),
        (503, 1, logging.WARNING, "falló con error retryable", 200),
    ],
    ids=["no_reintentable", "agotados", "reintento"],
)
def test_f048_r36_cada_camino_recorta_a_su_limite(status_code, reintentos, nivel, frase, limite, caplog):
    """Un error largo SIN correo sale recortado a 300 o a 200, como antes de F-048."""
    texto = f"Error {status_code}: " + "x" * 400
    registros = _lanzar(_ErrorApi(texto, status_code), reintentos, caplog)

    assert _msg(_registro(registros, nivel, frase)) == texto[:limite]
