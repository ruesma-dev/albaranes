# tests/test_f045_r25_r26_observables.py
"""F-045 · R25 y R26: IA1 e IA2 se comparan solo por lo que la corrida VE.

La pasada con LLM del 2026-09-16 lo puso en números: de 1456 fallos, **1295
eran «obtenido None»**, y 186 de ellos venían de exigirle a la extracción dos
columnas de CONTROL DEL BANCO —`caso_id`, que es la etiqueta que le ponemos
nosotros al caso, y `fichero_albaran`, que es el nombre que nosotros le dimos
al papel—. No están impresas en ningún albarán y sv2 no las produce: pedirlas
es ruido que tapa los defectos de verdad.

Otros 72 eran `unidad`, que sv2 no extrae hoy (F-024) y que R26 manda
**declarar** en vez de dar por mala. Un rojo permanente que nadie va a
arreglar deja de informar el día dos.

La regla que cierra las dos cosas: **observable es exactamente lo que la
proyección del proceso produce**. Lo demás se poda antes de comparar y se
declara en el informe.
"""

from __future__ import annotations

from evals.comparador import Criticidad, campos_no_observables
from evals.informe import render
from evals.modelos import NO_COMPARAR, ResultadoFase, ResultadoPasada
from evals.procesos import sv2_extraccion

CRITICIDAD = Criticidad(por_defecto="critico")

DOCUMENTO = {
    "cabecera": {
        "proveedor_nombre": "HORPRESOL, S.L.",
        "proveedor_cif": "B04685541",
        "fecha": "2026-03-11",
        "numero_albaran": "H132525",
        "obra_codigo": None,
        "obra_nombre": None,
        "forma_pago": None,
    },
    "lineas": [
        {"concepto": "HA-25/B/20/IIa", "cantidad": 8, "precio": 72.5,
         "precio_neto": 580, "codigo_imputacion": "P5.14.01"},
    ],
}


# --- R25: las columnas de control del banco no se le exigen a la IA -------


def test_f045_r25_ia1_declara_sus_campos_observables():
    assert set(sv2_extraccion.OBSERVABLES) == {"cabeceras", "lineas", "contexto"}


def test_f045_r25_el_caso_id_y_el_fichero_no_son_observables():
    """Son etiquetas NUESTRAS: ningún albarán las imprime y sv2 no las devuelve."""
    assert "caso_id" not in sv2_extraccion.OBSERVABLES["cabeceras"]
    assert "fichero_albaran" not in sv2_extraccion.OBSERVABLES["cabeceras"]
    assert "caso_id" not in sv2_extraccion.OBSERVABLES["lineas"]
    assert "caso_id" not in sv2_extraccion.OBSERVABLES["contexto"]


def test_f045_r26_la_unidad_no_es_observable_mientras_sv2_no_la_extraiga():
    """F-024. Cuando sv2 la extraiga, entra aquí y el banco la vigila sola."""
    assert "unidad" not in sv2_extraccion.OBSERVABLES["lineas"]
    assert "descuentos" not in sv2_extraccion.OBSERVABLES["lineas"]


def test_f045_r25_observable_es_EXACTAMENTE_lo_que_la_proyeccion_produce():
    """La lista y la proyección no pueden divergir: si divergen, o se compara

    contra `None` para siempre, o se deja de mirar algo que sí llega."""
    ia1 = sv2_extraccion.proyectar_ia1(DOCUMENTO, "HOR-001")
    assert set(ia1["cabeceras"][0]) == set(sv2_extraccion.OBSERVABLES["cabeceras"])
    assert set(ia1["lineas"][0]) == set(sv2_extraccion.OBSERVABLES["lineas"])

    documento = {"lineas": [{"contexto_linea": {"codigo_ler": "170201"}}]}
    ia2 = sv2_extraccion.proyectar_ia2(documento, "RES-001")
    assert set(ia2["contexto"][0]) == set(sv2_extraccion.OBSERVABLES["contexto"])


def test_f045_r25_lo_no_observable_no_genera_ni_un_fallo():
    """El test que habría evitado los 186 fallos de ruido de la pasada real."""
    from evals.comparador import comparar_tablas

    # Tal como sale del conversor: el `?` de los libros viaja como sentinela.
    esperadas = [
        {
            "caso_id": "HOR-001",
            "fichero_albaran": "HOR-001.pdf",
            "proveedor_nombre": "HORPRESOL, S.L.",
            "proveedor_cif": NO_COMPARAR,
            "fecha": "2026-03-11",
            "numero_albaran": NO_COMPARAR,
            "obra_codigo": NO_COMPARAR,
            "obra_nombre": NO_COMPARAR,
            "forma_pago": NO_COMPARAR,
            "comentario": "lo que sea",
        }
    ]
    obtenidas = sv2_extraccion.proyectar_ia1(DOCUMENTO, "HOR-001")["cabeceras"]
    discrepancias = comparar_tablas(
        esperadas, obtenidas, CRITICIDAD, claves=(), prefijo="IA1.cabeceras",
        observables=sv2_extraccion.OBSERVABLES["cabeceras"],
    )
    assert [d.campo for d in discrepancias if d.severidad == "fallo"] == []


def test_f045_r26_lo_podado_se_declara_en_vez_de_desaparecer():
    esperadas = [{"caso_id": "HOR-001", "unidad": "M3", "cantidad": 8}]
    declarados = campos_no_observables(esperadas, sv2_extraccion.OBSERVABLES["lineas"])
    assert sorted(declarados) == ["caso_id", "unidad"]


# --- R26: el informe los declara, y no mezclados con otra cosa -----------


def test_f045_r26_el_informe_tiene_seccion_propia_para_lo_no_observable():
    """Hasta ahora el runner los colaba por el parámetro `sin_clasificar`, y el

    informe los anunciaba como «campos sin clasificar en criticidad.json», que
    es un problema distinto y con otro arreglo. Dos cosas distintas, dos
    secciones."""
    pasada = ResultadoPasada(modo="completa", fases=[ResultadoFase(nombre="IA1")])
    texto = render(pasada, sin_clasificar=["obra"], no_observables=["unidad", "caso_id"])
    assert "## Campos no observables en esta corrida" in texto
    assert "## Campos sin clasificar en evals/criticidad.json" in texto
    cabecera_no_obs = texto.index("## Campos no observables")
    cabecera_sin_clas = texto.index("## Campos sin clasificar")
    bloque = texto[cabecera_no_obs:cabecera_sin_clas]
    assert "`unidad`" in bloque and "`caso_id`" in bloque
    assert "`obra`" not in bloque


def test_f045_r26_sin_campos_no_observables_no_hay_seccion():
    pasada = ResultadoPasada(modo="completa", fases=[ResultadoFase(nombre="IA1")])
    assert "## Campos no observables" not in render(pasada)
