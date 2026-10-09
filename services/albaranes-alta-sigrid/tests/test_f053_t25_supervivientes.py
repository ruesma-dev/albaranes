# tests/test_f053_t25_supervivientes.py
"""F-053 · T25 · tests que matan los supervivientes de la campaña de mutación en sv9.

Cada test fija un valor o una rama que la campaña (``progress/mutacion_F-053.md``)
demostró que ningún test leía. Los equivalentes se justifican en el informe.
"""
from __future__ import annotations

import dataclasses
import logging
from pathlib import Path

import pytest

from application import alta_sigrid_service as servicio_mod
from application.alta_sigrid_service import AltaSigridService, ResultadoProceso
from domain.models import alta_models
from domain.models.alta_models import (
    AccionAlta,
    AdjuntoEstado,
    AltaActual,
    ErrorAlta,
    EstadoAlta,
    LineaPeticion,
    ModoAlta,
    PeticionAlbaran,
    RespuestaAlta,
    TipoFallo,
)
from domain.services.clasificador import clasificar
from domain.services.comparador_previa import comparar
from tests.f053_datos import CONFIG, datos, sin_vincular, vinculada
from tests.f053_fakes import (
    AHORA,
    DESDE,
    ESPERA,
    PdfFalso,
    RepoFalso,
    SigridFalso,
    previa_ok,
)

D = datos(vinculada(1), sin_vincular(2))


def _servicio(repo, sigrid=None, *, modo=ModoAlta.REAL, pdf=None):
    return AltaSigridService(
        repo=repo, sigrid=sigrid or SigridFalso(), pdf=pdf or PdfFalso(), config=CONFIG,
        modo=modo, desde=DESDE, espera=ESPERA, tolerancia_eur=0.05,
        avisos_bloqueantes=frozenset({"producto_sin_historico"}),
        reloj=lambda: AHORA,
    )


# ------------------------------------------------------------------ #
# Modelos inmutables (R16: lo guardado no se toca a medio camino)
# ------------------------------------------------------------------ #
_DATACLASSES = [
    c for c in vars(alta_models).values()
    if isinstance(c, type) and dataclasses.is_dataclass(c) and c.__module__ == alta_models.__name__
]


@pytest.mark.parametrize("clase", [*_DATACLASSES, ResultadoProceso], ids=lambda c: c.__name__)
def test_f053_t25_los_modelos_son_inmutables(clase):
    assert clase.__dataclass_params__.frozen is True


def test_f053_t25_alta_actual_sin_intentos_por_defecto():
    assert AltaActual(estado=EstadoAlta.SIMULADO).intentos == 0


# ------------------------------------------------------------------ #
# R9 · salida sin estado final: el finally la cierra en error
# ------------------------------------------------------------------ #
def test_f053_t25_r9_salida_sin_estado_final_deja_error(monkeypatch):
    repo = RepoFalso()
    doc = repo.anadir(D)
    servicio = _servicio(repo, modo=ModoAlta.SIMULACION)
    monkeypatch.setattr(servicio, "_flujo", lambda document_id, previa, paso: None)

    resultado = servicio.procesar(doc, AccionAlta.ALTA)

    assert resultado.estado is EstadoAlta.ERROR
    guardado = repo.ultimo(doc)
    assert guardado.estado is EstadoAlta.ERROR
    assert [(m.codigo, m.detalle) for m in guardado.motivos] == [
        ("excepcion", "salida sin estado final"),
    ]


# ------------------------------------------------------------------ #
# R23 · detalle del adjunto fallido
# ------------------------------------------------------------------ #
def _peticion():
    from domain.services.validador_alta import validar_y_construir
    from tests.f053_datos import HOY

    return validar_y_construir(D, CONFIG, HOY)


def _registrado_con_adjunto_que_falla(sigrid):
    sigrid.previa = previa_ok(_peticion())
    sigrid.grabacion = previa_ok(_peticion(), estado="creado", con_ide=9, cod="AC26/9")
    repo = RepoFalso()
    doc = repo.anadir(D)
    _servicio(repo, sigrid).procesar(doc, AccionAlta.ALTA)
    guardado = repo.ultimo(doc)
    assert guardado.estado is EstadoAlta.REGISTRADO
    assert guardado.adjunto_estado is AdjuntoEstado.ERROR
    return next(m.detalle for m in guardado.motivos if m.codigo == "adjunto_no_colgado")


def test_f053_t25_r23_detalle_del_adjunto_con_codigo():
    from domain.models.alta_models import ResultadoAdjunto

    sigrid = SigridFalso(adjunto=ResultadoAdjunto(False, codigo="usuario_no_valido",
                                                  mensaje="usu no existe"))
    assert _registrado_con_adjunto_que_falla(sigrid) == "usuario_no_valido: usu no existe"


def test_f053_t25_r23_excepcion_del_adjunto_recorta_el_mensaje_a_200():
    class _Largo(SigridFalso):
        def adjuntar_pdf(self, con_ide, nombre, contenido):
            raise RuntimeError("x" * 300)

    detalle = _registrado_con_adjunto_que_falla(_Largo())
    assert detalle == "RuntimeError: " + "x" * 200


# ------------------------------------------------------------------ #
# R15 · importes de una petición retomada y avisos de línea (R16, R17)
# ------------------------------------------------------------------ #
def test_f053_t25_r15_importe_de_linea_retomada_sale_de_la_peticion():
    linea = LineaPeticion(referencia_linea="999999", cantidad=2.0, precio=0.063,
                          producto="MA9999", descripcion="X")
    peticion = PeticionAlbaran(
        cod_obra="0404", cif_proveedor="B1", cod_contrato=None, referencia_externa="ALB-d",
        su_referencia="N", usu="u", fecha_albaran=20261001, empide=None, lineas=(linea,),
    )
    importes = servicio_mod._importes(D, peticion)
    assert importes["999999"] == 0.13  # round(2 × 0.063, 2) = 0,13: ni // (0,0) ni 3 decimales (0,126)


def test_f053_t25_r16_avisos_de_linea_con_su_referencia():
    respuesta = RespuestaAlta(
        estado="previsto", avisos=({"codigo": "cod_provisional"},),
        lineas=({"referencia_linea": "7", "avisos": [{"codigo": "stock_negativo"}]},
                {"referencia_linea": "8", "avisos": None}),
    )
    assert servicio_mod._avisos(respuesta) == (
        {"codigo": "cod_provisional"},
        {"codigo": "stock_negativo", "referencia_linea": "7"},
    )


def test_f053_t25_r17_aviso_bloqueante_lleva_su_mensaje():
    peticion = _peticion()
    respuesta = previa_ok(peticion)
    respuesta = dataclasses.replace(respuesta, avisos=(
        {"codigo": "producto_sin_historico", "mensaje": "MA9999 nunca comprado"},))
    from domain.services.validador_alta import importes_por_referencia

    motivos = comparar(peticion, respuesta, importes_por_referencia(D), 0.05,
                       frozenset({"producto_sin_historico"}))
    assert [(m.codigo, m.detalle) for m in motivos] == [
        ("aviso_bloqueante", "producto_sin_historico: MA9999 nunca comprado"),
    ]


# ------------------------------------------------------------------ #
# R18 · un código de cabecera que no llega con un 400 es error
# ------------------------------------------------------------------ #
@pytest.mark.parametrize("tipo", [TipoFallo.AUTORIZACION, TipoFallo.CLIENTE])
def test_f053_t25_r18_codigo_sin_400_es_error(tipo):
    error = ErrorAlta(tipo=tipo, status=403, codigo="obra_no_encontrada")
    assert clasificar(error, grabacion=False) is EstadoAlta.ERROR


# ------------------------------------------------------------------ #
# Configuración y log (patrón de sv6)
# ------------------------------------------------------------------ #
BASE = {
    "SIGRID_API_BASE_URL": "https://sigrid.invalid", "SIGRID_API_FUNCTION_KEY": "k",
    "PG_USER": "u", "PG_PASSWORD": "p", "GRAPH_KEY": "g",
}


def _settings(**extra):
    from config.settings import Settings

    return Settings(_env_file=None, **{**BASE, **extra})


def test_f053_t25_env_file_es_el_del_servicio():
    from config import settings

    assert settings._ENV_FILE == Path(settings.__file__).resolve().parents[1] / ".env"
    assert settings._ENV_FILE.parent.name == "albaranes-alta-sigrid"


def test_f053_t25_defectos_de_configuracion():
    ajustes = _settings()
    assert ajustes.pg_port == 5432
    assert ajustes.graph_timeout_s == 60


@pytest.mark.parametrize("variable, valor", [
    ("ALTA_SIGRID_ESPERA_INCIERTO_MIN", "0"),
    ("SIGRID_API_TIMEOUT_S", "0.5"),
    ("GRAPH_TIMEOUT_S", "1"),
])
def test_f053_t25_limites_inferiores_admitidos(variable, valor):
    _settings(**{variable: valor})


@pytest.mark.parametrize("variable, valor", [
    ("ALTA_SIGRID_ESPERA_INCIERTO_MIN", "-1"),
    ("SIGRID_API_TIMEOUT_S", "0"),
    ("GRAPH_TIMEOUT_S", "0"),
])
def test_f053_t25_limites_inferiores_rechazados(variable, valor):
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        _settings(**{variable: valor})


def test_f053_t25_configure_logging(monkeypatch, tmp_path):
    from config import logging_config

    capturadas = []
    monkeypatch.setattr(logging_config.logging.config, "dictConfig", capturadas.append)
    destino = tmp_path / "a" / "b"
    logging_config.configure_logging(destino, "INFO")
    logging_config.configure_logging(destino, "INFO")  # dos veces: exist_ok

    assert destino.is_dir()
    config = capturadas[-1]
    assert config["version"] == 1
    assert config["disable_existing_loggers"] is False
    fichero = config["handlers"]["file"]
    assert fichero["maxBytes"] == 5 * 1024 * 1024
    assert fichero["backupCount"] == 5
    assert fichero["filename"] == str(destino / "albaranes_alta_sigrid.log")
    assert logging.getLevelName("INFO") == 20
