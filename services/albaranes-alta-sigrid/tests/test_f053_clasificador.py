# tests/test_f053_clasificador.py
"""F-053 · T7 · ``clasificador``: respuesta de sigrid-api → estado del alta.

La tabla de códigos (design §2) es un DATO del módulo y se prueba código a
código con el contrato tal como está en F-009 v8 (``8a6ecab``, §3.3 y §3.4).
R15 (``idempotente``), R18 (400 por ``details.codigo``), R20 (``creado``) y
R21 (5xx, tiempo agotado y conexión: ``incierto`` en la grabación, ``error`` en
la previa). Puro: sin red.
"""
from __future__ import annotations

import pytest

from domain.models.alta_models import (
    ErrorAlta,
    EstadoAlta,
    Motivo,
    RespuestaAlta,
    TipoFallo,
)
from domain.services.clasificador import (
    CODIGOS_CABECERA,
    CODIGOS_LINEA,
    clasificar,
    motivos_de_error,
)

NO_ADMITIDO = EstadoAlta.NO_ADMITIDO
ERROR = EstadoAlta.ERROR
REVISAR = EstadoAlta.REVISAR

#: Contrato v8 §3.3 (cabecera) y design §2.
TABLA_CABECERA = {
    "obra_no_encontrada": NO_ADMITIDO, "obra_ambigua": NO_ADMITIDO,
    "contrato_no_encontrado": NO_ADMITIDO, "contrato_ambiguo": NO_ADMITIDO,
    "proveedor_sin_albaran_previo": NO_ADMITIDO, "almacen_de_obra_no_resuelto": NO_ADMITIDO,
    "demasiadas_lineas": NO_ADMITIDO,
    "referencia_en_conflicto": REVISAR,
    "escritura_albaranes_deshabilitada": ERROR, "base_de_datos_no_permitida": ERROR,
    "referencia_no_permitida": ERROR, "obra_de_empresa_no_permitida": ERROR,
    "usuario_no_valido": ERROR, "estado_inicial_no_encontrado": ERROR,
    "peticion_mixta": ERROR, "colision_de_clave": ERROR,
    "filas_afectadas_inesperadas": ERROR,
}
#: Contrato v8 §3.3 (códigos de línea dentro de ``lineas_no_validas``).
TABLA_LINEA = {
    "linea_no_es_del_contrato": NO_ADMITIDO, "partida_no_encontrada": NO_ADMITIDO,
    "partida_ambigua": NO_ADMITIDO, "partida_no_imputable": NO_ADMITIDO,
    "paride_no_valido": NO_ADMITIDO, "analitica_no_resuelta": NO_ADMITIDO,
    "producto_no_permitido": ERROR, "producto_no_encontrado": ERROR,
    "naturaleza_no_valida": ERROR, "precio_negativo": ERROR,
}


def _rechazo(codigo: str | None, *lineas: str) -> ErrorAlta:
    return ErrorAlta(
        tipo=TipoFallo.RECHAZO, status=400, codigo=codigo,
        lineas=tuple({"indice": i, "referencia_linea": str(10 + i), "codigo": c,
                      "mensaje": f"m{i}"} for i, c in enumerate(lineas)),
        mensaje="Solicitud rechazada.",
    )


def test_f053_r18_la_tabla_es_la_del_contrato_v8():
    assert dict(CODIGOS_CABECERA) == TABLA_CABECERA
    assert dict(CODIGOS_LINEA) == TABLA_LINEA


@pytest.mark.parametrize(("codigo", "estado"), sorted(TABLA_CABECERA.items()))
@pytest.mark.parametrize("grabacion", [False, True])
def test_f053_r18_cada_codigo_de_cabecera_a_su_estado(codigo, estado, grabacion):
    assert clasificar(_rechazo(codigo), grabacion=grabacion) is estado


@pytest.mark.parametrize(("codigo", "estado"), sorted(TABLA_LINEA.items()))
def test_f053_r18_cada_codigo_de_linea_a_su_estado(codigo, estado):
    assert clasificar(_rechazo("lineas_no_validas", codigo), grabacion=False) is estado


@pytest.mark.parametrize("codigo", ["partida_ambigua", "paride_no_valido", "analitica_no_resuelta"])
def test_f053_r18_lineas_que_se_corrigen_en_sv4_son_no_admitido(codigo):
    assert clasificar(_rechazo("lineas_no_validas", codigo), grabacion=False) is NO_ADMITIDO


@pytest.mark.parametrize("codigo", ["naturaleza_no_valida", "precio_negativo", "producto_no_permitido"])
def test_f053_r18_lineas_de_configuracion_son_error(codigo):
    assert clasificar(_rechazo("lineas_no_validas", codigo), grabacion=False) is ERROR


def test_f053_r18_obra_de_empresa_no_permitida_es_error():
    assert clasificar(_rechazo("obra_de_empresa_no_permitida"), grabacion=False) is ERROR


def test_f053_r18_lineas_no_validas_sin_codigo_de_error_es_no_admitido():
    error = _rechazo("lineas_no_validas", "partida_no_encontrada", "linea_no_es_del_contrato")
    assert clasificar(error, grabacion=False) is NO_ADMITIDO


def test_f053_r18_en_lineas_no_validas_gana_error():
    error = _rechazo("lineas_no_validas", "partida_no_encontrada", "producto_no_encontrado")
    assert clasificar(error, grabacion=False) is ERROR


def test_f053_r18_linea_con_codigo_desconocido_es_error():
    error = _rechazo("lineas_no_validas", "partida_no_encontrada", "codigo_nuevo_de_f009")
    assert clasificar(error, grabacion=False) is ERROR


def test_f053_r18_lineas_no_validas_sin_lineas_es_error():
    assert clasificar(_rechazo("lineas_no_validas"), grabacion=False) is ERROR


@pytest.mark.parametrize("codigo", ["codigo_desconocido", "fecha_no_valida", "plantilla_de_otro_proveedor"])
def test_f053_r18_codigo_desconocido_es_error(codigo):
    """H25. ``fecha_no_valida`` y ``plantilla_de_otro_proveedor`` ya no existen."""
    assert clasificar(_rechazo(codigo), grabacion=False) is ERROR


@pytest.mark.parametrize("grabacion", [False, True])
def test_f053_r18_400_sin_codigo_es_error(grabacion):
    assert clasificar(_rechazo(None), grabacion=grabacion) is ERROR


@pytest.mark.parametrize("status", [401, 403])
def test_f053_r18_clave_rechazada_es_error(status):
    error = ErrorAlta(tipo=TipoFallo.AUTORIZACION, status=status, mensaje="Unauthorized")
    assert clasificar(error, grabacion=True) is ERROR


def test_f053_r18_otro_4xx_es_error():
    error = ErrorAlta(tipo=TipoFallo.CLIENTE, status=404, mensaje="Not found")
    assert clasificar(error, grabacion=True) is ERROR


def test_f053_r18_motivos_del_error_con_sus_lineas():
    error = _rechazo("lineas_no_validas", "partida_no_encontrada", "linea_no_es_del_contrato")
    assert motivos_de_error(error) == [
        Motivo("lineas_no_validas", "Solicitud rechazada."),
        Motivo("partida_no_encontrada", "m0", "10"),
        Motivo("linea_no_es_del_contrato", "m1", "11"),
    ]
    sin_codigo = ErrorAlta(tipo=TipoFallo.TIEMPO_AGOTADO, mensaje="timeout")
    assert motivos_de_error(sin_codigo) == [Motivo("tiempo_agotado", "timeout")]
    http = ErrorAlta(tipo=TipoFallo.RECHAZO, status=400, mensaje="Solicitud invalida.")
    assert motivos_de_error(http) == [Motivo("http_400", "Solicitud invalida.")]


# ------------------------------------------------------------------ #
# R20, R15 · 200
# ------------------------------------------------------------------ #
@pytest.mark.parametrize("grabacion", [False, True])
def test_f053_r20_creado_es_registrado(grabacion):
    respuesta = RespuestaAlta(estado="creado", con_ide=9123461, cod="AC26/16004")
    assert clasificar(respuesta, grabacion=grabacion) is EstadoAlta.REGISTRADO


@pytest.mark.parametrize("grabacion", [False, True])
def test_f053_r15_idempotente_es_registrado(grabacion):
    respuesta = RespuestaAlta(estado="idempotente", con_ide=9123461, cod="AC26/16004")
    assert clasificar(respuesta, grabacion=grabacion) is EstadoAlta.REGISTRADO


def test_f053_r15_previsto_en_la_previa_se_compara():
    assert clasificar(RespuestaAlta(estado="previsto"), grabacion=False) is None


def test_f053_r20_previsto_en_la_grabacion_es_error():
    """La grabación respondió como previa: sigrid-api dice que no escribió."""
    assert clasificar(RespuestaAlta(estado="previsto"), grabacion=True) is ERROR


def test_f053_r20_estado_desconocido():
    assert clasificar(RespuestaAlta(estado="raro"), grabacion=False) is ERROR
    assert clasificar(RespuestaAlta(estado="raro"), grabacion=True) is EstadoAlta.INCIERTO


# ------------------------------------------------------------------ #
# R21 · 5xx, tiempo agotado y conexión
# ------------------------------------------------------------------ #
@pytest.mark.parametrize("tipo", [TipoFallo.SERVIDOR, TipoFallo.TIEMPO_AGOTADO,
                                  TipoFallo.CONEXION, TipoFallo.RESPUESTA_INVALIDA])
def test_f053_r21_fallo_transitorio_incierto_en_grabacion_error_en_previa(tipo):
    error = ErrorAlta(tipo=tipo, status=500 if tipo is TipoFallo.SERVIDOR else None)
    assert clasificar(error, grabacion=True) is EstadoAlta.INCIERTO
    assert clasificar(error, grabacion=False) is ERROR
