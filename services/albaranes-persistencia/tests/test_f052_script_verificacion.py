# tests/test_f052_script_verificacion.py
"""F-052 T14 · script de verificación de solo lectura (R29, R30, design §8).

El script lo ejecuta el humano contra sigrid-api (T20, T21, T23). Aquí se
prueba contra el doble, sin red: que mide lo que dice medir (filas,
``truncated``, bytes, segundos), que su veredicto falla cuando debe y que
nunca imprime la clave ni la URL de sigrid-api.
"""
from __future__ import annotations

import logging
from types import SimpleNamespace

import httpx
import pytest
from doble_sigrid_api import (
    CIF_GRANDE_0668,
    CIF_SALMEDINA,
    CONTRATO_SALMEDINA,
    DobleSigridApi,
    ErrorSql,
)
from infrastructure.sigrid.sigrid_api_contrato_client import SigridApiContratoClient
from pydantic import BaseModel, ValidationError

from scripts import verificar_f052_proveedores_obra as script

_CLAVE = "clave-de-test"
_URL = "https://sigrid-api.doble"


def _entorno(doble: DobleSigridApi, *, reloj=None, umbral: float = 0.5) -> script.Entorno:
    transporte = script.TransporteQueMide(
        fabrica=lambda: doble.transport,
        **({"reloj": reloj} if reloj else {}),
    )
    cliente = SigridApiContratoClient(
        base_url=_URL, function_key=_CLAVE, database="ruesma", transport=transporte,
    )
    return script.Entorno(cliente=cliente, transporte=transporte, umbral=umbral, secretos=(_CLAVE, _URL))


def _ejecutar(argv: list[str], doble: DobleSigridApi, **kwargs) -> tuple[int, str]:
    lineas: list[str] = []
    codigo = script.main(argv, construir=lambda: _entorno(doble, **kwargs), salida=lineas.append)
    return codigo, "\n".join(lineas)


class _RelojFijo:
    """Cada lectura avanza ``paso`` segundos: una petición mide ``paso``."""

    def __init__(self, paso: float) -> None:
        self.t = 0.0
        self.paso = paso

    def __call__(self) -> float:
        self.t += self.paso
        return self.t


# ------------------------------------------------------------------ #
# R29 · la agregada de la obra, N veces, y fetch_contratos
# ------------------------------------------------------------------ #
def test_f052_r29_obra_0691_ok_con_salmedina():
    doble = DobleSigridApi()
    codigo, texto = _ejecutar(
        ["--obra", "0691", "--cif", CIF_SALMEDINA, "--nombre", "SALMEDINA", "--repeticiones", "3"], doble,
    )
    assert codigo == 0, texto
    assert len(doble.peticiones_con("FOR XML PATH")) == 3
    for n in (1, 2, 3):
        assert f"  #{n}  filas=81  truncated=false" in texto
    assert f"CIF {CIF_SALMEDINA}: dentro" in texto
    assert "Consulta agregada: 3/3 completas (truncated=false), CIF dentro en 3/3" in texto
    assert f"  1,00  {CIF_SALMEDINA}  SALMEDINA, S.L." in texto
    assert f"Mejor candidato: {CIF_SALMEDINA} (score 1,00) -> propuesta" in texto
    assert f"fetch_contratos({CIF_SALMEDINA}, 0691): 1 contrato(s)" in texto
    assert f"  {CONTRATO_SALMEDINA}  5 línea(s)" in texto
    assert "header_and_lines: 1 petición(es), filas=5, truncated=false" in texto
    assert texto.rstrip().endswith("RESULTADO R29: OK")


def test_f052_r29_normaliza_la_obra_como_sv3():
    doble = DobleSigridApi()
    codigo, texto = _ejecutar(["--obra", "691", "--repeticiones", "1"], doble)
    assert codigo == 0, texto
    assert doble.peticiones_con("FOR XML PATH")[0]["parameters"] == ["0691"]
    assert "Obra 0691" in texto


def test_f052_r29_obra_invalida_no_consulta():
    doble = DobleSigridApi()
    codigo, texto = _ejecutar(["--obra", "12"], doble)
    assert codigo == 2
    assert "no es un código de obra válido" in texto
    assert doble.peticiones == []


def test_f052_r29_mide_bytes_y_segundos_de_cada_peticion():
    doble = DobleSigridApi()
    codigo, texto = _ejecutar(["--obra", "0691", "--repeticiones", "2"], doble, reloj=_RelojFijo(2.5))
    assert codigo == 0, texto
    bytes_agregada = len(httpx.Response(200, json=doble.respuestas[0]).content)
    assert f"bytes={script.miles(bytes_agregada)}  segundos=2,50" in texto
    assert "tiempo máximo 2,50 s (límite 15 s)" in texto


def test_f052_r29_tiempo_por_encima_de_15_s_falla():
    doble = DobleSigridApi()
    codigo, texto = _ejecutar(["--obra", "0691", "--repeticiones", "1"], doble, reloj=_RelojFijo(16.0))
    assert codigo == 1
    assert "tiempo máximo 16,00 s (límite 15 s)" in texto
    assert "RESULTADO R29: FALLA" in texto
    assert "  - la consulta agregada tardó 16,00 s (límite 15 s)" in texto


def test_f052_r29_justo_15_s_ya_falla():
    """design §10: «si pasara de 15 s» se abre feature; T20 exige < 15 s."""
    codigo, texto = _ejecutar(["--obra", "0691", "--repeticiones", "1"], DobleSigridApi(), reloj=_RelojFijo(15.0))
    assert codigo == 1
    assert "  - la consulta agregada tardó 15,00 s (límite 15 s)" in texto


def test_f052_r29_truncado_falla_y_lo_dice():
    doble = DobleSigridApi(forzar_truncado=True)
    codigo, texto = _ejecutar(["--obra", "0691", "--repeticiones", "2"], doble)
    assert codigo == 1
    assert "  #1  filas=81  truncated=true" in texto
    assert "SigridRespuestaTruncada" in texto
    assert "Consulta agregada: 0/2 completas" in texto
    assert "  - 2 de 2 llamadas a la consulta agregada fallaron o llegaron truncadas" in texto


def test_f052_r29_error_xml_falla_sin_filtrar_la_clave():
    doble = DobleSigridApi(error_xml=True)
    codigo, texto = _ejecutar(["--obra", "0691", "--nombre", "SALMEDINA"], doble)
    assert codigo == 1
    assert "FOR XML could not serialize" in texto
    assert "  #1  ERROR: RuntimeError" in texto
    assert "sin candidatos: la consulta agregada no respondió" in texto
    assert _CLAVE not in texto
    assert _URL not in texto


def test_f052_r29_cif_ausente_falla():
    doble = DobleSigridApi()
    codigo, texto = _ejecutar(["--obra", "0691", "--cif", "B00000000", "--repeticiones", "1"], doble)
    assert codigo == 1
    assert "CIF B00000000: FUERA" in texto
    assert "  - el CIF B00000000 no está en 1 de 1 respuestas" in texto
    assert "fetch_contratos(B00000000, 0691): 0 contrato(s)" in texto
    assert "  - fetch_contratos no devolvió ningún contrato" in texto


def test_f052_r29_nombre_que_no_casa_falla():
    doble = DobleSigridApi()
    codigo, texto = _ejecutar(["--obra", "0691", "--nombre", "ZZZZ QQQQ", "--repeticiones", "1"], doble)
    assert codigo == 1
    assert "-> nadie casa" in texto
    assert "  - ningún proveedor llega al umbral 0,50 con el nombre 'ZZZZ QQQQ'" in texto


def test_f052_r29_mejor_por_debajo_del_umbral_es_nadie_casa():
    """Score 0,50 con umbral 0,60 (``HEADER_RESOLVER_MIN_SCORE``): hay
    mejor candidato, pero no llega al umbral."""
    codigo, texto = _ejecutar(
        ["--obra", "0691", "--nombre", "PROVEEDOR XXXXX", "--repeticiones", "1"], DobleSigridApi(), umbral=0.6,
    )
    assert codigo == 1
    assert "Mejor candidato: B10000000 (score 0,50) -> nadie casa" in texto
    assert "  - ningún proveedor llega al umbral 0,60 con el nombre 'PROVEEDOR XXXXX'" in texto


def test_f052_r29_el_mejor_no_es_el_cif_esperado_falla():
    doble = DobleSigridApi()
    codigo, texto = _ejecutar(
        ["--obra", "0691", "--cif", CIF_SALMEDINA, "--nombre", "PROVEEDOR OBRA 07", "--repeticiones", "1"], doble,
    )
    assert codigo == 1
    assert f"  - el mejor candidato por nombre no es {CIF_SALMEDINA}" in texto
    # Empate a 1,00 entre los «PROVEEDOR OBRA xx»: gana el primero en el
    # orden de la agregada, como en el resolver (``>`` estricto).
    assert "Mejor candidato: B10000000 (score 1,00) -> propuesta" in texto
    assert f"Score del CIF {CIF_SALMEDINA}: 0," in texto


def test_f052_r29_fetch_contratos_que_lanza_falla():
    class _Rompe(DobleSigridApi):
        def _despachar(self, sql, params):
            if "AS contrato_ide" in sql:
                raise ErrorSql("error en header_and_lines")
            return super()._despachar(sql, params)

    doble = _Rompe()
    codigo, texto = _ejecutar(["--obra", "0691", "--cif", CIF_SALMEDINA, "--repeticiones", "1"], doble)
    assert codigo == 1
    assert "fetch_contratos: ERROR: RuntimeError" in texto
    assert "  - fetch_contratos falló" in texto


# ------------------------------------------------------------------ #
# R30 · familias agregada frente a por líneas, y CIF frente a DISTINCT
# ------------------------------------------------------------------ #
def test_f052_r30_comparar_familias_sin_diferencias():
    doble = DobleSigridApi()
    codigo, texto = _ejecutar(["--comparar-familias", "--obra", "0691", "--obra", "0668"], doble)
    assert codigo == 0, texto
    assert "  agregada: 81 filas, truncated=false" in texto
    assert "  por líneas: 2.083 filas, truncated=false" in texto
    assert "  por líneas: 1.202 filas, truncated=false" in texto
    assert "  CIF: agregada 81 · por líneas 81 · DISTINCT 81 · de más 0 · de menos 0" in texto
    assert texto.count("  Diferencias de familias: 0") == 2
    assert texto.rstrip().endswith("RESULTADO R30: OK (2 obra(s), 0 diferencias de familias, 0 CIF distintos)")
    [lineas] = [
        p for p in doble.peticiones
        if "AS descripcion_linea" in p["sql"] and "contrato_ide" not in p["sql"] and p["parameters"] == ["0691"]
    ]
    assert lineas["max_rows"] == 500_000


class _DobleAlterado(DobleSigridApi):
    """La agregada pierde el texto de un CIF y deja fuera a otro."""

    def __init__(self, *, sin_texto: str, fuera: str) -> None:
        super().__init__()
        self.sin_texto = sin_texto
        self.fuera = fuera

    def _despachar(self, sql, params):
        columnas, filas, ordenado = super()._despachar(sql, params)
        if "FOR XML PATH" in sql:
            filas = [
                [f[0], f[1], f[2], None if f[0] == self.sin_texto else f[3]]
                for f in filas if f[0] != self.fuera
            ]
        return columnas, filas, ordenado


def test_f052_r30_detecta_diferencias_de_familias_y_cif_de_menos():
    doble = _DobleAlterado(sin_texto=CIF_SALMEDINA, fuera=CIF_GRANDE_0668)
    codigo, texto = _ejecutar(["--comparar-familias", "--obra", "0691", "--obra", "0668"], doble)
    assert codigo == 1
    assert f"    {CIF_SALMEDINA}: por líneas ['residuos'] · agregada []" in texto
    assert "de menos 1" in texto
    assert f"    de menos: {CIF_GRANDE_0668}" in texto
    assert "RESULTADO R30: FALLA" in texto


def test_f052_r30_detecta_cif_de_mas():
    class _ConIntruso(DobleSigridApi):
        def _despachar(self, sql, params):
            columnas, filas, ordenado = super()._despachar(sql, params)
            if "FOR XML PATH" in sql:
                filas = [*filas, ["X9999999", "INTRUSO", "CT/1", None]]
            return columnas, filas, ordenado

    codigo, texto = _ejecutar(["--comparar-familias", "--obra", "0691"], _ConIntruso())
    assert codigo == 1
    assert "  Diferencias de familias: 0" in texto  # falla SOLO por el CIF de más
    assert "de más 1" in texto
    assert "    de más: X9999999" in texto


def test_f052_r30_consulta_fallida_cuenta_como_falla():
    codigo, texto = _ejecutar(["--comparar-familias", "--obra", "0691"], DobleSigridApi(error_xml=True))
    assert codigo == 1
    assert "  ERROR: RuntimeError" in texto
    assert "RESULTADO R30: FALLA" in texto


def test_f052_r30_texto_por_lineas_como_el_codigo_antiguo():
    columnas = ["cif", "nombre", "codigo_contrato", "nombre_contrato", "descripcion_linea", "codigo_producto"]
    filas = [
        [" B1 ", "UNO", "C1", "  SUMINISTRO ", "HORMIGON", None],
        ["B1", "UNO", "C1", "SUMINISTRO", "   ", "P1"],
        [None, "SIN CIF", "C2", "X", "Y", "Z"],
        ["B2", "DOS", "C3", None, "", None],
    ]
    assert script.texto_por_lineas(columnas, filas) == {
        "B1": "SUMINISTRO HORMIGON SUMINISTRO P1",
        "B2": "",
    }


# ------------------------------------------------------------------ #
# design §8 · obras de más de 1.000 líneas
# ------------------------------------------------------------------ #
def test_f052_listar_obras_grandes():
    doble = DobleSigridApi()
    codigo, texto = _ejecutar(["--listar-obras-grandes"], doble)
    assert codigo == 0, texto
    [peticion] = doble.peticiones
    assert "HAVING COUNT(*) > 1000" in peticion["sql"]
    assert "Obras con más de 1.000 líneas de contrato: 2" in texto
    assert "  0691     2.083           81" in texto
    assert "  0668     1.202            3" in texto
    assert "Lista para el SELECT de sospechosos (T23): '0691', '0668'" in texto


def test_f052_listar_obras_grandes_truncada_falla():
    codigo, texto = _ejecutar(["--listar-obras-grandes"], DobleSigridApi(forzar_truncado=True))
    assert codigo == 1
    assert "ERROR: SigridRespuestaTruncada" in texto


# ------------------------------------------------------------------ #
# Argumentos
# ------------------------------------------------------------------ #
@pytest.mark.parametrize(
    "argv",
    [
        [],
        ["--repeticiones", "2"],
        ["--obra", "0691", "--obra", "0696"],
        ["--obra", "0691", "--repeticiones", "0"],
        ["--comparar-familias"],
        ["--listar-obras-grandes", "--obra", "0691"],
        ["--listar-obras-grandes", "--comparar-familias", "--obra", "0691"],
    ],
)
def test_f052_argumentos_invalidos_salen_con_2_sin_consultar(argv):
    doble = DobleSigridApi()
    with pytest.raises(SystemExit) as info:
        _ejecutar(argv, doble)
    assert info.value.code == 2
    assert doble.peticiones == []


# ------------------------------------------------------------------ #
# Cliente, .env y secretos
# ------------------------------------------------------------------ #
def _settings(**cambios):
    base = {
        "sigrid_api_base_url": _URL,
        "sigrid_api_function_key": _CLAVE,
        "sigrid_api_database": "ruesma",
        "sigrid_api_timeout_s": 12.0,
        "header_resolver_min_score": 0.6,
        "sigrid_credentials_present": True,
    }
    base.update(cambios)
    return SimpleNamespace(**base)


def test_f052_construir_cliente_como_la_composicion():
    entorno = script.construir_cliente(lambda: _settings())
    assert entorno.umbral == 0.6
    assert entorno.secretos == (_CLAVE, _URL)
    assert entorno.cliente._transport is entorno.transporte
    assert entorno.cliente._timeout_s == 12.0
    assert entorno.cliente._database == "ruesma"


def test_f052_construir_cliente_sin_credenciales_para():
    with pytest.raises(SystemExit) as info:
        script.construir_cliente(lambda: _settings(sigrid_credentials_present=False))
    assert "SIGRID_API_BASE_URL" in str(info.value.code)


def test_f052_construir_cliente_con_env_invalido_no_muestra_valores():
    class _Modelo(BaseModel):
        pg_port: int

    def _falla():
        _Modelo(pg_port="secreto-que-no-debe-salir")

    with pytest.raises(ValidationError):
        _falla()
    with pytest.raises(SystemExit) as info:
        script.construir_cliente(_falla)
    assert "pg_port" in str(info.value.code)
    assert "secreto-que-no-debe-salir" not in str(info.value.code)


def test_f052_redactar_oculta_clave_y_url():
    texto = f"fallo contra {_URL}/api/sql/read con {_CLAVE} y nada más"
    assert script.redactar(texto, (_CLAVE, _URL, "", None)) == "fallo contra ***/api/sql/read con *** y nada más"


def test_f052_configurar_logs_silencia_el_cliente_y_se_restaura():
    nombre = "infrastructure.sigrid.sigrid_api_contrato_client"
    antes = logging.getLogger(nombre).level
    try:
        script.configurar_logs()
        assert logging.getLogger(nombre).level == logging.CRITICAL
    finally:
        logging.getLogger(nombre).setLevel(antes)


def test_f052_transporte_que_mide_no_json():
    transporte = script.TransporteQueMide(
        fabrica=lambda: httpx.MockTransport(lambda r: httpx.Response(502, text="Bad Gateway")),
        reloj=_RelojFijo(1.0),
    )
    with httpx.Client(transport=transporte) as cliente:
        respuesta = cliente.post(f"{_URL}/api/sql/read", content=b"no es json")
    assert respuesta.status_code == 502
    assert respuesta.text == "Bad Gateway"
    [medicion] = transporte.mediciones
    assert medicion == script.Medicion(filas=None, truncated=None, bytes=11, segundos=1.0)
    assert medicion.sql == ""


def test_f052_transporte_real_como_el_cliente_de_sv3():
    transporte = script._transporte_real()
    assert isinstance(transporte, httpx.HTTPTransport)
    transporte.close()
    assert isinstance(script.TransporteQueMide().mediciones, list)


def test_f052_formatos_en_espanol():
    assert script.miles(2083) == "2.083"
    assert script.miles(None) == "?"
    assert script.decimal(3.456) == "3,46"
    assert script.bandera(True) == "true"
    assert script.bandera(False) == "false"
    assert script.bandera(None) == "?"
