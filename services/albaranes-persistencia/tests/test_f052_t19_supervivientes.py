# tests/test_f052_t19_supervivientes.py
"""F-052 T19 · supervivientes de la campaña de mutación en sv3.

Cada test fija un borde, un valor por defecto o un texto que la campaña
(``progress/mutacion_F-052.md``) demostró que ningún test leía: la red de
obra del resolver con un código inválido, los límites inferiores y el
tope de páginas del cliente de contratos, el orden por nombre de la
agregada y las cuentas y textos del script de verificación (T14).
"""
from __future__ import annotations

import dataclasses
import os
import subprocess
import sys
from pathlib import Path

import pytest
from application.services.header_resolver_service import HeaderResolverService
from doble_sigrid_api import (
    CIF_GRANDE_0668,
    CIF_SALMEDINA,
    CONTRATO_SALMEDINA,
    DobleSigridApi,
    ErrorSql,
    Fixture,
    Linea,
)
from domain.models.obra_models import ObraEnrichmentResult
from infrastructure.sigrid.sigrid_api_contrato_client import SigridApiContratoClient
from ruesma_comun.sigrid import SigridRespuestaTruncada
from test_f052_script_verificacion import _CLAVE, _URL, _DobleAlterado, _ejecutar

from scripts import verificar_f052_proveedores_obra as script

_RAIZ_SV3 = Path(__file__).resolve().parents[1]


# ------------------------------------------------------------------ #
# Resolver · red de obra (código leído válido frente a inválido)
# ------------------------------------------------------------------ #
class _ObrasFalsas:
    def __init__(self) -> None:
        self.llamadas = 0

    def search_obras(self):
        self.llamadas += 1
        return [ObraEnrichmentResult(
            codigo_obra="0695", nombre_obra="EDIFICIO EJEMPLO", direccion_linea1="CALLE FALSA 1",
            direccion_linea2=None, codigo_postal="50001", municipio="ZARAGOZA", provincia="ZARAGOZA",
        )]


def _resolver_obra(codigo: str | None) -> tuple[str | None, int]:
    obras = _ObrasFalsas()
    resolver = HeaderResolverService(obra_client=obras, proveedor_client=None, repository=None)
    return resolver._resolve_obra(codigo, "EDIFICIO EJEMPLO", None), obras.llamadas


def test_f052_t19_obra_valida_no_se_busca_por_texto():
    assert _resolver_obra("691") == (None, 0)


@pytest.mark.parametrize("codigo", ["12345", "1234", "abc"])
def test_f052_t19_obra_invalida_se_deduce_por_texto(codigo):
    """Un código que ``normalizar_codigo_obra`` no admite NO cuenta como
    «la IA ya trajo obra»: se deduce por nombre, como sin código."""
    assert _resolver_obra(codigo) == ("0695", 1)


# ------------------------------------------------------------------ #
# Cliente de contratos · bordes y valores por defecto
# ------------------------------------------------------------------ #
def test_f052_t19_cliente_admite_una_fila_por_peticion_y_por_pagina():
    """1 es el mínimo válido de ``max_rows`` y de ``pagina_lineas``."""
    doble = DobleSigridApi()
    cliente = doble.cliente(max_rows=1, pagina_lineas=1)
    [contrato] = cliente.fetch_contratos(cif_proveedor=CIF_SALMEDINA, codigo_obra_normalizado="0691")
    assert len(contrato.lines) == 5
    assert {p["max_rows"] for p in doble.peticiones_con("AS contrato_ide")} == {2}
    # Con max_rows=1 la fila única llega marcada truncated (``>=``, como
    # sigrid-api): lo que se fija aquí es que la petición sale con 1.
    with pytest.raises(SigridRespuestaTruncada):
        cliente.fetch_proveedor_by_cif(cif=CIF_SALMEDINA)
    assert doble.peticiones[-1]["max_rows"] == 1


def test_f052_t19_tope_de_paginas_por_defecto_es_20():
    doble = DobleSigridApi()
    with pytest.raises(SigridRespuestaTruncada) as info:
        doble.cliente(pagina_lineas=50).fetch_contratos(
            cif_proveedor=CIF_GRANDE_0668, codigo_obra_normalizado="0668",
        )
    assert info.value.filas == 1000
    assert len(doble.peticiones_con("AS contrato_ide")) == 20


def test_f052_t19_agregada_con_dos_nombres_se_queda_el_primero_por_nombre():
    """Si un CIF trae dos ``raz``, gana el primero ordenando por nombre,
    aunque sigrid-api los devuelva en otro orden."""

    class _DosNombres(DobleSigridApi):
        def _despachar(self, sql, params):
            columnas, filas, ordenado = super()._despachar(sql, params)
            if "FOR XML PATH" in sql:
                filas = [["B1", "ZETA, S.L.", "CT/1", "x"], ["B1", "ALFA, S.L.", "CT/2", "y"]]
            return columnas, filas, ordenado

    [resumen] = _DosNombres().cliente().fetch_contratos_resumen_por_obra(codigo_obra="0691")
    assert resumen.nombre == "ALFA, S.L."


# ------------------------------------------------------------------ #
# Script de verificación (T14) · arranque, medición y transporte
# ------------------------------------------------------------------ #
def test_f052_t19_script_arranca_como_script_desde_otra_carpeta(tmp_path):
    """``python scripts\\verificar_...py`` desde cualquier carpeta: el
    propio script pone la raíz de sv3 en ``sys.path``. Obra inválida para
    salir con 2 antes de leer el ``.env`` ni consultar nada."""
    entorno = {k: v for k, v in os.environ.items() if k != "PYTHONPATH"}
    proceso = subprocess.run(
        [sys.executable, str(_RAIZ_SV3 / "scripts" / "verificar_f052_proveedores_obra.py"), "--obra", "12"],
        cwd=tmp_path, capture_output=True, text=True, env=entorno, timeout=120, check=False,
    )
    assert proceso.returncode == 2, proceso.stderr
    assert "no es un código de obra válido" in proceso.stdout
    assert script._RAIZ_SV3 == _RAIZ_SV3


def test_f052_t19_medicion_es_inmutable_y_se_compara_sin_la_sql():
    a = script.Medicion(filas=1, truncated=False, bytes=10, segundos=0.5, sql="SELECT 1")
    assert a == script.Medicion(filas=1, truncated=False, bytes=10, segundos=0.5, sql="SELECT 2")
    with pytest.raises(dataclasses.FrozenInstanceError):
        a.filas = 2  # type: ignore[misc]


def test_f052_t19_transporte_real_con_un_reintento(monkeypatch):
    creados: list[dict] = []
    monkeypatch.setattr(script.httpx, "HTTPTransport", lambda **kw: creados.append(kw) or object())
    script._transporte_real()
    assert creados == [{"retries": 1}]


# ------------------------------------------------------------------ #
# Script · R29
# ------------------------------------------------------------------ #
class _AgregadaVariable(DobleSigridApi):
    """La llamada nº ``falla_en`` a la agregada falla y en la nº
    ``sin_cif_en`` el CIF de SALMEDINA no viene (1-based)."""

    def __init__(self, *, falla_en: int | None = None, sin_cif_en: int | None = None) -> None:
        super().__init__()
        self.falla_en = falla_en
        self.sin_cif_en = sin_cif_en
        self.agregadas = 0

    def _despachar(self, sql, params):
        if "FOR XML PATH" in sql:
            self.agregadas += 1
            if self.agregadas == self.falla_en:
                raise ErrorSql("fallo puntual")
        columnas, filas, ordenado = super()._despachar(sql, params)
        if "FOR XML PATH" in sql and self.agregadas == self.sin_cif_en:
            filas = [f for f in filas if f[0] != CIF_SALMEDINA]
        return columnas, filas, ordenado


def test_f052_t19_r29_cabecera_con_y_sin_cif():
    _, con = _ejecutar(["--obra", "0691", "--cif", CIF_SALMEDINA], DobleSigridApi())
    _, sin = _ejecutar(["--obra", "0691"], DobleSigridApi())
    assert con.splitlines()[1] == f"Obra 0691 · CIF {CIF_SALMEDINA} · nombre None · 1 repetición(es)"
    assert sin.splitlines()[1] == "Obra 0691 · CIF - · nombre None · 1 repetición(es)"


def test_f052_t19_r29_por_defecto_una_repeticion():
    doble = DobleSigridApi()
    codigo, texto = _ejecutar(["--obra", "0691"], doble)
    assert codigo == 0, texto
    assert len(doble.peticiones_con("FOR XML PATH")) == 1
    assert "Consulta agregada: 1/1 completas" in texto


def test_f052_t19_r29_cuenta_las_llamadas_fallidas():
    codigo, texto = _ejecutar(["--obra", "0691", "--repeticiones", "3"], _AgregadaVariable(falla_en=2))
    assert codigo == 1
    assert "  - 1 de 3 llamadas a la consulta agregada fallaron o llegaron truncadas" in texto


def test_f052_t19_r29_cuenta_las_respuestas_sin_el_cif():
    codigo, texto = _ejecutar(
        ["--obra", "0691", "--cif", CIF_SALMEDINA, "--repeticiones", "3"], _AgregadaVariable(sin_cif_en=2),
    )
    assert codigo == 1
    assert "CIF dentro en 2/3" in texto
    assert f"  - el CIF {CIF_SALMEDINA} no está en 1 de 3 respuestas" in texto


def test_f052_t19_r29_lista_los_cinco_mejores_por_nombre():
    _, texto = _ejecutar(["--obra", "0691", "--nombre", "SALMEDINA"], DobleSigridApi())
    lineas = texto.splitlines()
    inicio = next(i for i, ln in enumerate(lineas) if ln.startswith("Nombre 'SALMEDINA' frente a"))
    fin = next(i for i, ln in enumerate(lineas) if ln.startswith("Mejor candidato:"))
    assert fin - inicio - 1 == 5


def test_f052_t19_r29_score_igual_al_umbral_es_propuesta():
    codigo, texto = _ejecutar(
        ["--obra", "0691", "--cif", CIF_SALMEDINA, "--nombre", "SALMEDINA"], DobleSigridApi(), umbral=1.0,
    )
    assert codigo == 0, texto
    assert f"Mejor candidato: {CIF_SALMEDINA} (score 1,00) -> propuesta" in texto


def test_f052_t19_r29_lista_cada_contrato_con_su_nombre():
    _, texto = _ejecutar(["--obra", "0691", "--cif", CIF_SALMEDINA], DobleSigridApi())
    assert f"  {CONTRATO_SALMEDINA}  5 línea(s)  GESTION DE RESIDUOS OBRA 0691" in texto.splitlines()


def test_f052_t19_r29_filas_de_header_and_lines_suman_las_reales():
    """Con páginas de 5, las 5 líneas de SALMEDINA llegan en una página
    llena y otra vacía: 2 peticiones y 5 filas (la vacía suma 0)."""
    doble = DobleSigridApi()
    transporte = script.TransporteQueMide(fabrica=lambda: doble.transport)
    cliente = SigridApiContratoClient(
        base_url=_URL, function_key=_CLAVE, database="ruesma", transport=transporte, pagina_lineas=5,
    )
    entorno = script.Entorno(cliente=cliente, transporte=transporte, umbral=0.5, secretos=(_CLAVE, _URL))
    lineas: list[str] = []
    script.main(["--obra", "0691", "--cif", CIF_SALMEDINA], construir=lambda: entorno, salida=lineas.append)
    assert "  header_and_lines: 2 petición(es), filas=5, truncated=false" in lineas


# ------------------------------------------------------------------ #
# Script · R30
# ------------------------------------------------------------------ #
def test_f052_t19_r30_resultado_con_error_cuenta_una_obra():
    codigo, texto = _ejecutar(["--comparar-familias", "--obra", "0691"], DobleSigridApi(error_xml=True))
    assert codigo == 1
    assert texto.splitlines()[-1] == (
        "RESULTADO R30: FALLA (1 obra(s) con error, 1 obra(s), 0 diferencias de familias, 0 CIF distintos)"
    )


def test_f052_t19_r30_resultado_cuenta_diferencias_y_cif_distintos():
    doble = _DobleAlterado(sin_texto=CIF_SALMEDINA, fuera=CIF_GRANDE_0668)
    codigo, texto = _ejecutar(["--comparar-familias", "--obra", "0691", "--obra", "0668"], doble)
    assert codigo == 1
    assert texto.splitlines()[-1] == (
        "RESULTADO R30: FALLA (2 obra(s), 2 diferencias de familias, 1 CIF distintos)"
    )


def test_f052_t19_r30_obra_con_una_sola_linea():
    linea = Linea("0700", "B7000000", "UNO, S.L.", 1, "CT/1", "SUMINISTRO HORMIGON", 1, 1, "HORMIGON", None)
    doble = DobleSigridApi(Fixture(lineas=(linea,), proveedores_global=(("B7000000", "UNO, S.L."),)))
    codigo, texto = _ejecutar(["--comparar-familias", "--obra", "0700"], doble)
    assert codigo == 0, texto
    assert "  CIF: agregada 1 · por líneas 1 · DISTINCT 1 · de más 0 · de menos 0" in texto
