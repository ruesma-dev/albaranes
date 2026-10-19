# tests/test_f083_informe.py
"""F-083 · R6, R9, R18, R27–R29, R37: el resumen versionable y el detalle."""

from __future__ import annotations

from decimal import Decimal

from evals.decision import Metricas, Recomendacion
from evals.informe_modelos import (
    CABECERA,
    Seccion,
    anadir_seccion,
    gasto_acumulado,
    render_detalle,
    render_versionable,
    servido_difiere,
    tokens_medidos,
)
from evals.modelos import Discrepancia, ResultadoCaso

#: Valores de albarán que NUNCA pueden llegar al resumen versionable (R29, R37).
CIF = "B99887766"
NOMBRE = "HORMIGONES CENTINELA SL"


def _metricas(modelo, fase="IA1", **cambios):
    datos = dict(
        modelo=modelo, fase=fase, casos=2, verdes=1, fallos=Decimal(3), fallos_min=3,
        fallos_max=3, avisos=1, tiempo_medio_s=Decimal("2.5"), tiempo_max_s=Decimal("4"),
        llamadas=2, tokens_entrada_medios=Decimal("1000.4"), tokens_salida_medios=Decimal("300"),
        coste_total=Decimal("0.02"), coste_por_albaran=Decimal("0.01"),
        modelos_servidos=[modelo], motivos_parada={"STOP": 2},
    )
    datos.update(cambios)
    return Metricas(**datos)


def _caso_rojo():
    return ResultadoCaso.desde_discrepancias(
        "GEN-001", "IA1", [Discrepancia("IA1.cabeceras[0].proveedor_cif", CIF, NOMBRE, "fallo")]
    )


def _seccion(**cambios):
    datos = dict(
        fecha="2026-10-20T10:00:00Z",
        fase="IA1",
        commit="abc1234",
        casos=["GEN-001", "HOR-001"],
        omitidos={"GEN-002": "no existe el fichero del albarán"},
        repeticiones=1,
        referencia="gemini-3.7-flash",
        referencia_anadida=True,
        preparacion=None,
        metricas={
            "gemini-3.7-flash": _metricas("gemini-3.7-flash", modelos_servidos=["gemini-3.8-flash"]),
            "gpt-6-luna": _metricas("gpt-6-luna", errores=1, uso_incompleto=1,
                                    modelos_servidos=["gpt-6-luna-2026-09-01"]),
        },
        metricas_e2e={},
        metricas_preparacion=None,
        recomendacion=Recomendacion(
            ["gemini-3.7-flash"], ["gemini-3.7-flash"], "gemini-3.7-flash", "mantener", [],
            True, "provisional (1 repetición)",
        ),
        errores=[("gpt-6-luna", 1, "HOR-001", "ERROR en IA1 · ValidationError: json_invalid")],
        gasto_real=Decimal("0.0412345"),
        cortado=False,
        salida="evals/salidas/comparar_modelos/2026-10-20-100000",
    )
    datos.update(cambios)
    return Seccion(**datos)


# --- R27, R28: contenido ---------------------------------------------------------------


def test_f083_r27_tabla_por_modelo():
    texto = render_versionable(_seccion())
    assert "## 2026-10-20T10:00:00Z · IA1 · 2 casos × 1 repetición" in texto
    fila = next(linea for linea in texto.splitlines() if linea.startswith("| `gpt-6-luna`"))
    celdas = [c.strip() for c in fila.strip("|").split("|")]
    # Modelo, casos, ERROR, NO_EJECUTADO, verdes, fallos, avisos, t medio, t máx,
    # tokens entrada, tokens salida, USD/albarán, USD total, uso incompleto, servido, parada.
    assert celdas[1:14] == ["2", "1", "0", "1", "3", "1", "2.5", "4.0", "1001", "300",
                            "0.0100", "0.0200", "1"]
    assert celdas[15] == "STOP ×2"


def test_f083_r27_con_varias_repeticiones_media_y_rango():
    metricas = {"gemini-3.7-flash": _metricas(
        "gemini-3.7-flash", repeticiones=3, fallos=Decimal(7) / 3, fallos_min=1, fallos_max=4)}
    texto = render_versionable(_seccion(repeticiones=3, metricas=metricas))
    assert "× 3 repeticiones" in texto
    assert "| 2.33 (1–4) |" in texto


def test_f083_r27_preparacion_aparte():
    prep = _metricas("gemini-3.7-flash", llamadas=9, coste_total=Decimal("0.5"))
    texto = render_versionable(_seccion(fase="IA2", preparacion="gemini-3.7-flash",
                                        metricas_preparacion=prep))
    assert "- Preparación (IA1, una vez): `gemini-3.7-flash` · 9 llamadas · 0.5000 USD" in texto
    assert "TOKENS: IA1 · gemini-3.7-flash · 1001 · 300" in texto


def test_f083_r27_e2e_en_ia3_e_ia4():
    e2e = {"claude-opus-4-8": _metricas("claude-opus-4-8", fase="E2E", fallos=Decimal(9))}
    texto = render_versionable(_seccion(fase="IA3", metricas_e2e=e2e))
    assert "### E2E" in texto
    assert "| `claude-opus-4-8` | 2 | 0 | 0 | 1 | 9 |" in texto


def test_f083_r28_lineas_base_de_f075_con_advertencia():
    texto = render_versionable(_seccion())
    assert "IA1 141 · IA2 2 · IA3 408 · IA4 27 · E2E 537" in texto
    assert "no registran el modelo" in texto


def test_f083_r27_recomendacion_y_avisos():
    recomendacion = Recomendacion(["a", "b"], ["b"], "b", "cambiar", ["b tarda mucho"], False, "")
    texto = render_versionable(_seccion(recomendacion=recomendacion))
    assert "### Recomendación" in texto and "provisional" not in texto.split("### Recomendación")[1].split("\n")[0]
    assert "**cambiar** a `b`" in texto
    assert "- Elegibles: `a`, `b` · banda de empate: `b`" in texto
    assert "- AVISO: b tarda mucho" in texto


def test_f083_r30_sin_datos_y_mantener():
    sin_datos = Recomendacion([], [], None, "sin datos", [], True, "provisional (1 repetición)")
    texto = render_versionable(_seccion(recomendacion=sin_datos))
    assert "### Recomendación · provisional (1 repetición)" in texto
    assert "**sin datos**" in texto
    texto = render_versionable(_seccion())
    assert "**mantener** `gemini-3.7-flash`" in texto


def test_f083_r12_aviso_de_referencia_anadida():
    assert "añadida" in render_versionable(_seccion())
    assert "añadida" not in render_versionable(_seccion(referencia_anadida=False))


def test_f083_r19_cortado_por_tope():
    assert "CORTADO" in render_versionable(_seccion(cortado=True))
    assert "CORTADO" not in render_versionable(_seccion())


def test_f083_r24_errores_sin_valores():
    texto = render_versionable(_seccion())
    assert "- `gpt-6-luna` r1 · HOR-001 · ERROR en IA1 · ValidationError: json_invalid" in texto
    assert "(ninguno)" in render_versionable(_seccion(errores=[]))


def test_f083_omitidos():
    assert "- Omitidos: 1 (GEN-002: no existe el fichero del albarán)" in render_versionable(_seccion())
    assert "Omitidos" not in render_versionable(_seccion(omitidos={}))


# --- R9: modelo servido ---------------------------------------------------------------------


def test_f083_r9_servido_difiere():
    assert servido_difiere("gemini-3.7-flash", "gemini-3.8-flash") is True
    assert servido_difiere("gpt-6-luna", "gpt-6-luna") is False
    assert servido_difiere("gpt-6-luna", "gpt-6-luna-2026-09-01") is False
    assert servido_difiere("gpt-5.4", "gpt-5.4-pro") is True
    assert servido_difiere("gpt-5.4", "gpt-5.4-") is True
    assert servido_difiere("gpt-5.4", "gpt-5.4x") is True


def test_f083_r9_el_informe_avisa_junto_al_modelo():
    texto = render_versionable(_seccion())
    fila = next(linea for linea in texto.splitlines() if linea.startswith("| `gemini-3.7-flash`"))
    assert "gemini-3.8-flash ⚠ difiere del pedido" in fila
    fila = next(linea for linea in texto.splitlines() if linea.startswith("| `gpt-6-luna`"))
    assert "gpt-6-luna-2026-09-01" in fila and "difiere" not in fila


def test_f083_r9_servido_no_informado():
    metricas = {"gpt-6-luna": _metricas("gpt-6-luna", modelos_servidos=[], motivos_parada={})}
    texto = render_versionable(_seccion(metricas=metricas))
    fila = next(linea for linea in texto.splitlines() if linea.startswith("| `gpt-6-luna`"))
    assert fila.rstrip().endswith("| no informado | — |")


# --- R6, R15, R18, R29: líneas que se leen de vuelta --------------------------------------


def test_f083_r18_gasto_real_se_lee_de_vuelta():
    texto = render_versionable(_seccion())
    assert "GASTO: 2026-10-20T10:00:00Z · IA1 · 0.041235" in texto
    assert gasto_acumulado(texto) == Decimal("0.041235")


def test_f083_r15_tokens_de_cada_modelo_se_leen_de_vuelta():
    texto = render_versionable(_seccion())
    assert tokens_medidos(texto) == {
        ("IA1", "gemini-3.7-flash"): (1001, 300),
        ("IA1", "gpt-6-luna"): (1001, 300),
    }


def test_f083_r15_un_modelo_sin_llamadas_con_respuesta_no_deja_tokens():
    metricas = {"gpt-6-luna": _metricas("gpt-6-luna", tokens_entrada_medios=Decimal(0),
                                        tokens_salida_medios=Decimal(0))}
    assert "TOKENS:" not in render_versionable(_seccion(metricas=metricas))


def test_f083_r29_el_resumen_es_acumulativo():
    primero = anadir_seccion("", render_versionable(_seccion()))
    assert primero.startswith(CABECERA)
    segundo = anadir_seccion(primero, render_versionable(_seccion(fecha="2026-10-21T09:00:00Z")))
    assert segundo.startswith(primero)
    assert sum(linea.startswith("GASTO:") for linea in segundo.splitlines()) == 2
    assert gasto_acumulado(segundo) == Decimal("0.082470")


def test_f083_r29_r37_el_detalle_lleva_valores_y_el_versionable_no():
    seccion = _seccion()
    casos = {"gpt-6-luna": [[_caso_rojo()]]}
    detalle = render_detalle(seccion, casos)
    assert CIF in detalle and NOMBRE in detalle
    assert "no versionar" in detalle
    versionable = anadir_seccion("", render_versionable(seccion))
    assert CIF not in versionable and NOMBRE not in versionable


def test_f083_r29_detalle_de_casos_sin_discrepancias_y_con_motivo():
    casos = {"a": [[ResultadoCaso("A", "IA1"), ResultadoCaso.con_error("B", "IA1", "falló")]]}
    detalle = render_detalle(_seccion(), casos)
    assert "- `a` r1 · A · VERDE" in detalle
    assert "- `a` r1 · B · ERROR · falló" in detalle
