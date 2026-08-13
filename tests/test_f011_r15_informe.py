# tests/test_f011_r15_informe.py
"""F-011 · R15 y R16 — El informe de una corrida y su lectura por la puerta.

El informe es la evidencia: si no dice qué se ejecutó, con qué proveedores y
qué falló campo a campo, no sirve ni al humano ni a la puerta del arnés.
"""

from evals.informe import (
    MODO_COMPLETA,
    MODO_DETERMINISTA,
    es_pasada_completa,
    parsear_veredicto,
    render,
)
from evals.modelos import (
    NO_EVALUABLE,
    ROJO,
    VERDE,
    Discrepancia,
    ResultadoCaso,
    ResultadoFase,
    ResultadoPasada,
)


def _pasada_completa():
    ia1 = ResultadoFase(
        nombre="IA1",
        proveedores=["gemini"],
        casos=[
            ResultadoCaso.desde_discrepancias("HOR-001", "IA1", []),
            ResultadoCaso.omitido("HOR-002", "IA1", "falta HOR-002.pdf"),
        ],
    )
    e2e = ResultadoFase(
        nombre="E2E",
        proveedores=["gemini", "openai"],
        casos=[
            ResultadoCaso.desde_discrepancias(
                "HOR-001",
                "E2E",
                [
                    Discrepancia(
                        campo="lineas[0].precio_unitario_final",
                        esperado=72.5,
                        obtenido=80.0,
                        severidad="fallo",
                    ),
                    Discrepancia(
                        campo="lineas[0].descripcion",
                        esperado="HA-25",
                        obtenido="hormigon 25",
                        severidad="aviso",
                    ),
                ],
            )
        ],
    )
    intermedias = [
        ResultadoFase(
            nombre=nombre,
            proveedores=["openai"],
            casos=[ResultadoCaso.desde_discrepancias("HOR-001", nombre, [])],
        )
        for nombre in ("IA2", "IA3", "IA4")
    ]
    return ResultadoPasada(
        modo=MODO_COMPLETA,
        fases=[ia1, *intermedias, e2e],
        feature="F-011",
        commit="abc1234",
        fecha="2026-08-13T09:00:00Z",
    )


def test_f011_r15_el_informe_dice_cuando_como_y_con_que_proveedores():
    texto = render(_pasada_completa())

    assert "2026-08-13T09:00:00Z" in texto
    assert "abc1234" in texto
    assert "F-011" in texto
    assert "gemini" in texto and "openai" in texto


def test_f011_r15_hay_una_fila_por_caso_con_su_estado():
    texto = render(_pasada_completa())

    assert "HOR-001" in texto
    assert "OMITIDO" in texto
    assert "falta HOR-002.pdf" in texto


def test_f011_r15_los_fallos_criticos_y_los_avisos_laxos_se_distinguen():
    texto = render(_pasada_completa())

    assert "lineas[0].precio_unitario_final" in texto
    assert "lineas[0].descripcion" in texto
    assert "AVISO" in texto


def test_f011_r15_los_campos_sin_clasificar_constan():
    texto = render(_pasada_completa(), sin_clasificar=["campo_raro"])

    assert "campo_raro" in texto
    assert "sin clasificar" in texto


def test_f011_r15_la_ultima_linea_es_el_veredicto_parseable():
    texto = render(_pasada_completa())

    assert texto.strip().splitlines()[-1] == f"VEREDICTO: {ROJO}"
    assert parsear_veredicto(texto) == ROJO


def test_f011_r15_la_puerta_reconoce_una_pasada_completa():
    texto = render(_pasada_completa())

    assert es_pasada_completa(texto) is True


def test_f011_r15_una_corrida_determinista_no_es_una_pasada_completa():
    pasada = _pasada_completa()
    pasada.modo = MODO_DETERMINISTA

    texto = render(pasada)

    assert es_pasada_completa(texto) is False


def test_f011_r15_una_pasada_a_la_que_le_falta_una_fase_no_cuenta():
    pasada = ResultadoPasada(
        modo=MODO_COMPLETA,
        fases=[ResultadoFase(nombre="IA1")],
        fecha="2026-08-13T09:00:00Z",
    )

    assert es_pasada_completa(render(pasada)) is False


def test_f011_r18_sin_casos_el_veredicto_es_no_evaluable():
    pasada = ResultadoPasada(
        modo=MODO_DETERMINISTA,
        fases=[ResultadoFase(nombre="IA3"), ResultadoFase(nombre="E2E")],
        fecha="2026-08-13T09:00:00Z",
    )

    texto = render(pasada)

    assert parsear_veredicto(texto) == NO_EVALUABLE
    assert pasada.codigo_salida() == 2


def test_f011_r16_los_avisos_laxos_no_impiden_el_verde():
    fase = ResultadoFase(
        nombre="IA3",
        casos=[
            ResultadoCaso.desde_discrepancias(
                "MOR-001",
                "IA3",
                [
                    Discrepancia(
                        campo="descripcion",
                        esperado="a",
                        obtenido="b",
                        severidad="aviso",
                    )
                ],
            )
        ],
    )
    pasada = ResultadoPasada(modo=MODO_DETERMINISTA, fases=[fase])

    assert parsear_veredicto(render(pasada)) == VERDE
    assert pasada.codigo_salida() == 0


def test_f011_r15_un_texto_sin_veredicto_no_se_inventa_uno():
    assert parsear_veredicto("informe cualquiera sin línea de veredicto") == ""
    assert es_pasada_completa("informe cualquiera") is False
