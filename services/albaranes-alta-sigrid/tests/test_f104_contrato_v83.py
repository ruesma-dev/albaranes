# tests/test_f104_contrato_v83.py
"""F-104 · sv9 entiende los códigos del contrato v8.3 de sigrid-api.

Contrato v8.3: ``sigrid-api`` ``871cc0c``, ``specs/F-009-alta-albaran-compra/
contrato_albaranes.md`` §3.2 (avisos) y §3.3 (errores). Se enlaza, no se copia.

- R1: ``proveedor_no_encontrado``, ``proveedor_ambiguo`` y
  ``retencion_no_soportada`` ⇒ ``no_admitido`` en la previa y en la grabación,
  con el código como motivo de cabecera y el ``error`` de sigrid-api de detalle.
- R2: ``proveedor_sin_albaran_previo`` (retirado en la v8.3) sigue en
  ``no_admitido`` hasta la verificación M2 y la retirada (T8, D1).
- R3: el resto de la tabla no cambia y un código desconocido sigue en
  ``error`` (F-053 H25).
- R4: los avisos ``retencion_del_contrato`` y ``cabecera_sin_dato`` no son
  bloqueantes por defecto, ni los nombra ``infra/*.ps1`` ni ``.env.example``.
- R5: con la configuración por defecto, esos avisos no añaden motivos y se
  guardan con su ``codigo`` y su ``mensaje`` (``simulado``, ``revisar`` y
  ``registrado``).
- R6: un 200 con los campos nuevos de la v8.3 (``totales.tot``,
  ``totales.retenciones``, ``totales.n_retenciones``, ``filas.dcarec``) se
  clasifica y se compara igual que sin ellos; ``filas`` no se guarda.

Sin red ni BBDD: dobles de ``tests/f053_fakes.py`` y ``Settings`` con
variables de entorno de mentira.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from application.alta_sigrid_service import AltaSigridService
from domain.models.alta_models import (
    AccionAlta,
    ErrorAlta,
    EstadoAlta,
    ModoAlta,
    Motivo,
    PeticionAlbaran,
    RespuestaAlta,
    TipoFallo,
)
from domain.services.clasificador import (
    CODIGOS_CABECERA,
    CODIGOS_LINEA,
    clasificar,
    motivos_de_error,
)
from domain.services.validador_alta import validar_y_construir
from tests.f053_datos import CONFIG, HOY, USU, datos, sin_vincular, vinculada
from tests.f053_fakes import AHORA, DESDE, ESPERA, PdfFalso, RepoFalso, SigridFalso, previa_ok
from tests.test_f053_t3_esqueleto import ENTORNO_MINIMO, VARIABLES_ALTA

NO_ADMITIDO = EstadoAlta.NO_ADMITIDO
ERROR = EstadoAlta.ERROR
REVISAR = EstadoAlta.REVISAR

RAIZ_SERVICIO = Path(__file__).resolve().parents[1]
RAIZ_REPO = RAIZ_SERVICIO.parents[1]

#: Errores de cabecera nuevos de la v8.3 (§3.3).
ERRORES_V83 = ("proveedor_no_encontrado", "proveedor_ambiguo", "retencion_no_soportada")
#: Avisos de cabecera nuevos de la v8.3 (§3.2).
AVISOS_V83 = ("retencion_del_contrato", "cabecera_sin_dato")
#: Retirado en la v8.3; se mantiene hasta M2 (R2, D1).
RETIRADO = "proveedor_sin_albaran_previo"

#: La tabla de cabecera tal como estaba en la v8.2 (``13fd99d``): R3 exige que
#: lo que no es de F-104 siga exactamente así.
TABLA_CABECERA_V82 = {
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
TABLA_LINEA_V82 = {
    "linea_no_es_del_contrato": NO_ADMITIDO, "partida_no_encontrada": NO_ADMITIDO,
    "partida_ambigua": NO_ADMITIDO, "partida_no_imputable": NO_ADMITIDO,
    "paride_no_valido": NO_ADMITIDO, "analitica_no_resuelta": NO_ADMITIDO,
    "producto_no_permitido": ERROR, "producto_no_encontrado": ERROR,
    "naturaleza_no_valida": ERROR, "precio_negativo": ERROR,
}

#: Avisos de cabecera como los describe la v8.3 (mensajes de mentira).
AVISOS_CABECERA_V83 = (
    {"codigo": "retencion_del_contrato",
     "mensaje": "Retención del contrato (código 3, 5 %): base 120,00, cuota 6,00"},
    {"codigo": "cabecera_sin_dato", "mensaje": "Columnas de pago vacías: forpag, banco"},
)

D = datos(vinculada(1), sin_vincular(2, codigo_partida_final=None))


def _peticion() -> PeticionAlbaran:
    peticion = validar_y_construir(D, CONFIG, HOY, USU)
    assert isinstance(peticion, PeticionAlbaran)
    return peticion


def _settings(monkeypatch, **extra):
    from config.settings import Settings

    for nombre in VARIABLES_ALTA:
        monkeypatch.delenv(nombre, raising=False)
    for nombre, valor in {**ENTORNO_MINIMO, **extra}.items():
        monkeypatch.setenv(nombre, valor)
    return Settings(_env_file=None)


def _procesar(sigrid, modo, bloqueantes):
    repo = RepoFalso()
    doc = repo.anadir(D)
    servicio = AltaSigridService(
        repo=repo, sigrid=sigrid, pdf=PdfFalso(), config=CONFIG, usuario_respaldo=USU, modo=modo,
        desde=DESDE, espera=ESPERA, tolerancia_eur=0.05, avisos_bloqueantes=bloqueantes,
        reloj=lambda: AHORA,
    )
    resultado = servicio.procesar(doc, AccionAlta.ALTA)
    return repo, doc, resultado


def _rechazo(codigo: str, mensaje: str = "") -> ErrorAlta:
    return ErrorAlta(tipo=TipoFallo.RECHAZO, status=400, codigo=codigo, mensaje=mensaje)


# ------------------------------------------------------------------ #
# R1 · los tres Errores v8.3 ⇒ no_admitido
# ------------------------------------------------------------------ #
@pytest.mark.parametrize("codigo", ERRORES_V83)
def test_f104_r1_errores_v83_en_la_tabla_como_no_admitido(codigo):
    assert CODIGOS_CABECERA[codigo] is NO_ADMITIDO


@pytest.mark.parametrize("codigo", ERRORES_V83)
@pytest.mark.parametrize("grabacion", [False, True])
def test_f104_r1_errores_v83_se_clasifican_no_admitido(codigo, grabacion):
    assert clasificar(_rechazo(codigo), grabacion=grabacion) is NO_ADMITIDO


@pytest.mark.parametrize("codigo", ERRORES_V83)
def test_f104_r1_motivo_de_cabecera_con_el_error_de_sigrid_api(codigo):
    mensaje = f"sigrid-api: {codigo} (detalle)"
    assert motivos_de_error(_rechazo(codigo, mensaje)) == [Motivo(codigo, mensaje)]


@pytest.mark.parametrize("codigo", ERRORES_V83)
@pytest.mark.parametrize("modo", [ModoAlta.SIMULACION, ModoAlta.REAL])
def test_f104_r1_previa_rechazada_por_un_error_v83_es_no_admitido(codigo, modo):
    error = _rechazo(codigo, "El proveedor no se pudo resolver.")
    repo, doc, resultado = _procesar(SigridFalso(previa=error), modo,
                                     frozenset({"producto_sin_historico"}))
    assert resultado.estado is NO_ADMITIDO
    guardado = repo.ultimo(doc)
    assert [(m.codigo, m.detalle, m.referencia_linea) for m in guardado.motivos] == [
        (codigo, "El proveedor no se pudo resolver.", None),
    ]
    assert guardado.respuesta == error.a_dict()


@pytest.mark.parametrize("codigo", ERRORES_V83)
def test_f104_r1_grabacion_rechazada_por_un_error_v83_es_no_admitido(codigo):
    error = _rechazo(codigo, "La retención no se puede aplicar.")
    sigrid = SigridFalso(previa=previa_ok(_peticion()), grabacion=error)
    repo, doc, resultado = _procesar(sigrid, ModoAlta.REAL, frozenset({"producto_sin_historico"}))
    assert resultado.estado is NO_ADMITIDO
    assert sigrid.commits() == [False, True]
    assert [(m.codigo, m.detalle) for m in repo.ultimo(doc).motivos] == [
        (codigo, "La retención no se puede aplicar."),
    ]


# ------------------------------------------------------------------ #
# R2 · el Código retirado sigue mapeado hasta M2 (D1)
# ------------------------------------------------------------------ #
@pytest.mark.parametrize("grabacion", [False, True])
def test_f104_r2_el_retirado_sigue_en_no_admitido(grabacion):
    assert CODIGOS_CABECERA[RETIRADO] is NO_ADMITIDO
    assert clasificar(_rechazo(RETIRADO), grabacion=grabacion) is NO_ADMITIDO


# ------------------------------------------------------------------ #
# R3 · el resto de la tabla, intacto; lo desconocido, a error (H25)
# ------------------------------------------------------------------ #
def test_f104_r3_la_tabla_es_la_v82_mas_los_tres_errores():
    assert dict(CODIGOS_CABECERA) == {**TABLA_CABECERA_V82, **dict.fromkeys(ERRORES_V83, NO_ADMITIDO)}
    assert dict(CODIGOS_LINEA) == TABLA_LINEA_V82


@pytest.mark.parametrize("codigo", ["codigo_de_la_v84", "proveedor_no_encontrad", *AVISOS_V83])
@pytest.mark.parametrize("grabacion", [False, True])
def test_f104_r3_codigo_desconocido_sigue_en_error(codigo, grabacion):
    """Un aviso de la v8.3 llegado como código de error tampoco está en la tabla."""
    assert clasificar(_rechazo(codigo), grabacion=grabacion) is ERROR


@pytest.mark.parametrize("codigo", ERRORES_V83)
def test_f104_r3_los_errores_v83_no_son_codigos_de_linea(codigo):
    error = ErrorAlta(tipo=TipoFallo.RECHAZO, status=400, codigo="lineas_no_validas",
                      lineas=({"indice": 0, "referencia_linea": "1", "codigo": codigo},))
    assert codigo not in CODIGOS_LINEA
    assert clasificar(error, grabacion=False) is ERROR


# ------------------------------------------------------------------ #
# R4 · los Avisos v8.3 no son bloqueantes por defecto
# ------------------------------------------------------------------ #
def test_f104_r4_defecto_de_avisos_bloqueantes(monkeypatch):
    bloqueantes = _settings(monkeypatch).avisos_bloqueantes
    assert bloqueantes == frozenset({"producto_sin_historico"})
    assert bloqueantes.isdisjoint(AVISOS_V83)


def test_f104_r4_ni_infra_ni_env_example_nombran_los_avisos_v83():
    ficheros = sorted((RAIZ_REPO / "infra").glob("*.ps1")) + [RAIZ_SERVICIO / ".env.example"]
    assert len(ficheros) > 1
    for fichero in ficheros:
        texto = fichero.read_text(encoding="utf-8-sig", errors="replace")
        for aviso in AVISOS_V83:
            assert aviso not in texto, f"{fichero.name} nombra {aviso}"


# ------------------------------------------------------------------ #
# R5 · con el defecto, los Avisos v8.3 se guardan y no bloquean
# ------------------------------------------------------------------ #
def _codigo_y_mensaje(avisos) -> list[tuple[str, str]]:
    return [(a["codigo"], a["mensaje"]) for a in avisos]


@pytest.mark.parametrize("caso", ["simulado", "revisar", "registrado"])
def test_f104_r5_avisos_v83_se_guardan_sin_motivo(monkeypatch, caso):
    bloqueantes = _settings(monkeypatch).avisos_bloqueantes
    peticion = _peticion()
    if caso == "revisar":
        previa = previa_ok(peticion, totales={"1": 400.0}, avisos=AVISOS_CABECERA_V83)
    else:
        previa = previa_ok(peticion, avisos=AVISOS_CABECERA_V83)
    creado = previa_ok(peticion, estado="creado", con_ide=9123461, cod="AC26/16004",
                       avisos=AVISOS_CABECERA_V83)
    modo = ModoAlta.REAL if caso == "registrado" else ModoAlta.SIMULACION
    repo, doc, resultado = _procesar(SigridFalso(previa=previa, grabacion=creado), modo, bloqueantes)

    assert resultado.estado is EstadoAlta(caso)
    guardado = repo.ultimo(doc)
    codigos = [m.codigo for m in guardado.motivos]
    assert "aviso_bloqueante" not in codigos
    assert codigos == (["importe_distinto"] if caso == "revisar" else [])
    assert _codigo_y_mensaje(guardado.avisos) == _codigo_y_mensaje(AVISOS_CABECERA_V83)


def test_f104_r5_si_alguien_los_configura_bloquean(monkeypatch):
    """Contraste: el no bloquear sale de la configuración, no del código."""
    bloqueantes = _settings(
        monkeypatch, ALTA_SIGRID_AVISOS_BLOQUEANTES="retencion_del_contrato",
    ).avisos_bloqueantes
    previa = previa_ok(_peticion(), avisos=AVISOS_CABECERA_V83)
    repo, doc, resultado = _procesar(SigridFalso(previa=previa), ModoAlta.SIMULACION, bloqueantes)
    assert resultado.estado is REVISAR
    assert [m.codigo for m in repo.ultimo(doc).motivos] == ["aviso_bloqueante"]


# ------------------------------------------------------------------ #
# R6 · los campos nuevos del 200 no cambian nada
# ------------------------------------------------------------------ #
def _con_campos_v83(respuesta: RespuestaAlta) -> RespuestaAlta:
    """El mismo 200 con lo que añade la v8.3, pasado por ``desde_cuerpo``."""
    cuerpo = respuesta.a_dict()
    cuerpo["totales"] = {
        **cuerpo["totales"], "tot": 114.0, "n_retenciones": 1,
        "retenciones": [{"codigo": 3, "porcentaje": 5.0, "base": 120.0, "cuota": 6.0}],
    }
    cuerpo["filas"] = {"dcarec": [{"dcaide": 1, "reccod": 3, "recpor": 5.0, "recimp": 6.0}]}
    return RespuestaAlta.desde_cuerpo(cuerpo)


def _resumen(repo, doc, resultado):
    guardado = repo.ultimo(doc)
    return (resultado.estado, [(m.codigo, m.detalle, m.referencia_linea) for m in guardado.motivos],
            guardado.sigrid_cod, guardado.sigrid_con_ide)


@pytest.mark.parametrize("caso", ["simulado", "revisar", "registrado"])
def test_f104_r6_un_200_con_los_campos_v83_se_trata_igual(caso):
    peticion = _peticion()
    totales = {"1": 400.0} if caso == "revisar" else None
    previa = previa_ok(peticion, totales=totales)
    creado = previa_ok(peticion, estado="creado", con_ide=9123461, cod="AC26/16004")
    modo = ModoAlta.REAL if caso == "registrado" else ModoAlta.SIMULACION
    bloqueantes = frozenset({"producto_sin_historico"})

    sin = _procesar(SigridFalso(previa=previa, grabacion=creado), modo, bloqueantes)
    con = _procesar(SigridFalso(previa=_con_campos_v83(previa), grabacion=_con_campos_v83(creado)),
                    modo, bloqueantes)

    assert con[2].estado is EstadoAlta(caso)
    assert _resumen(*con) == _resumen(*sin)
    guardado = con[0].ultimo(con[1])
    assert "filas" not in guardado.respuesta
    assert "dcarec" not in json.dumps(guardado.respuesta)
    assert guardado.respuesta["totales"]["tot"] == 114.0  # totales se guarda entero (R16)


@pytest.mark.parametrize("grabacion", [False, True])
@pytest.mark.parametrize("estado", ["previsto", "creado", "idempotente"])
def test_f104_r6_clasificar_ignora_los_campos_v83(estado, grabacion):
    respuesta = previa_ok(_peticion(), estado=estado)
    assert clasificar(_con_campos_v83(respuesta), grabacion=grabacion) == clasificar(
        respuesta, grabacion=grabacion,
    )
