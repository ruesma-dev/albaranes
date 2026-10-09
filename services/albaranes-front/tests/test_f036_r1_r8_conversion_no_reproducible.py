# tests/test_f036_r1_r8_conversion_no_reproducible.py
"""F-036 · D1: sv4 no puede rehacer una conversion que no sabe hacer.

El fallo, medido (SALMEDINA, agosto 2026)
-----------------------------------------
sv6 valora un albaran de residuos aplicando SU regla de contenedores:
el albaran declara 6 m3, el contrato tarifa CONTENEDORES, y sv6 escribe
``cantidad_albaran=6``, ``cantidad_convertida=1`` (un contenedor),
``precio_unitario_final=120`` e ``importe_calculado=120``. El
``factor_conversion`` queda a NULL porque ``unit_converter`` devuelve un
*hard mismatch* m3 <-> UD: no existe factor entre esas dos unidades.

En cuanto el revisor abria la ficha en sv4 y guardaba, el recalculo del PUT
tiraba la ``cantidad_convertida`` y recalculaba con la cantidad CRUDA del
albaran: 6 x 120 = 720,00 EUR. Seis veces el importe correcto.

La regla es GENERAL (R6), no de residuos: si la ``cantidad_convertida``
guardada NO se explica como ``factor x cantidad_albaran``, alguien de aguas
arriba aplico una regla propia que sv4 no conoce. Ese dato se conserva.

F-065 (T6) — DONDE VIVEN AHORA ESTAS GARANTIAS
----------------------------------------------
F-065 R1 retira el recalculo del PUT (guardar la cabecera no toca las
lineas) y R6-R8 llevan la regla a la fila: la ficha ensena y edita Q =
``cantidad_convertida ?? cantidad_albaran`` (en la unidad del precio) y el
PATCH manda solo lo que cambio. Con una conversion no reproducible, Q es la
convertida (1 contenedor): editarla fija la convertida y CONSERVA la del
albaran (``cantidades_tras_editar``, caso c). Los casos de abajo son los de
siempre, ejercidos contra ``update_line_conciliacion``. La tabla caso viejo
-> caso nuevo (y los que se retiran con su motivo) esta en
``progress/impl_F-065_fase1.md``.

Sin red ni BBDD real: SQLite en memoria (``f065_bbdd``).
"""
from __future__ import annotations

import json

import pytest
from f065_bbdd import ejecutar, fila, fila_nueva, motor_con_valoracion, repositorio, total

VALUATION_ID = "f036-0000-0000-0000-000000000589"
DOCUMENT_ID = "f036-doc-0000-0000-000000000589"

#: La linea tal cual la dejo sv6 en SS-0000589: 6 m3 declarados, un
#: contenedor valorado, 120,00 EUR. Sin factor de conversion.
LINEA_RESIDUOS = {
    "id": 900,
    "pu": 120.0,
    "factor": None,
    "cantidad_albaran": 6.0,
    "cantidad_convertida": 1.0,
    "importe": 120.0,
    "dto": None,
    "source": "declared_albaran",
}

#: Lo que sale si sv4 recalcula con la cantidad cruda del albaran.
IMPORTE_INFLADO = 720.0


def _sembrar(**cambios):
    """Deja una valoracion de una sola linea, como la escribio sv6."""
    linea = dict(LINEA_RESIDUOS)
    linea.update(cambios)
    motor = motor_con_valoracion(
        document_id=DOCUMENT_ID, valuation_id=VALUATION_ID, total=linea["importe"],
    )
    fila_nueva(
        motor, valuation_id=VALUATION_ID, id=linea["id"], merge_line_id=500,
        precio_unitario_final=linea["pu"], factor_conversion=linea["factor"],
        cantidad_albaran=linea["cantidad_albaran"],
        cantidad_convertida=linea["cantidad_convertida"],
        importe_calculado=linea["importe"], importe_source=linea["source"],
        descuento_albaran_aplicado=linea["dto"], review_required=False,
        review_reasons_json=linea.get("razones"),
    )
    return motor


def _editar(motor, **campos):
    return repositorio(motor).update_line_conciliacion(
        document_id=DOCUMENT_ID, valuation_line_id=LINEA_RESIDUOS["id"], campos=campos,
    )


def _linea(motor):
    return fila(motor, LINEA_RESIDUOS["id"])


def _traza(motor):
    """(review_required, [razones]) de la linea de valoracion."""
    f = _linea(motor)
    return bool(f["review_required"]), json.loads(f["review_reasons_json"] or "[]")


# ------------------------------------------------------------------ #
# R1 — que significa «la conversion es reproducible»
# ------------------------------------------------------------------ #
@pytest.mark.parametrize(
    ("factor", "cantidad_albaran", "cantidad_convertida", "esperado"),
    [
        # Los tres existen y la convertida ES el producto.
        (2.0, 3.0, 6.0, True),
        (1.0, 6.0, 6.0, True),
        (0.001, 1500.0, 1.5, True),
        # Los tres existen y la convertida NO es el producto: alguien
        # de aguas arriba aplico una regla que sv4 no conoce.
        (1.0, 6.0, 1.0, False),
        (2.0, 3.0, 5.0, False),
        # Falta alguno de los tres.
        (None, 6.0, 1.0, False),
        (None, 6.0, None, False),
        (2.0, None, 6.0, False),
        (2.0, 3.0, None, False),
        # Basura en la columna: no es reproducible, y no revienta.
        ("ilegible", 3.0, 6.0, False),
        (2.0, 3.0, "ilegible", False),
    ],
)
def test_f036_r1_conversion_reproducible_solo_si_cuadra_el_producto(
    factor, cantidad_albaran, cantidad_convertida, esperado,
):
    """R1: reproducible = los tres valores existen Y cc = factor x ca."""
    from domain.models.review_models import conversion_reproducible

    assert conversion_reproducible(
        factor=factor,
        cantidad_albaran=cantidad_albaran,
        cantidad_convertida=cantidad_convertida,
    ) is esperado


def test_f036_r1_la_tolerancia_absorbe_el_ruido_de_coma_flotante():
    """0,1 x 3 = 0,30000000000000004 en binario. Sigue siendo el producto."""
    from domain.models.review_models import conversion_reproducible

    assert conversion_reproducible(
        factor=0.1, cantidad_albaran=3.0, cantidad_convertida=0.3
    ) is True


# ------------------------------------------------------------------ #
# R2 — la cantidad convertida que no sabemos rehacer se CONSERVA
# ------------------------------------------------------------------ #
def test_f036_r2_guardar_sin_tocar_nada_no_multiplica_el_importe_por_seis():
    """El caso EXACTO de SS-0000589: abrir la ficha y guardar la fila."""
    motor = _sembrar()

    _editar(motor)

    linea = _linea(motor)
    assert linea["importe_calculado"] != pytest.approx(IMPORTE_INFLADO)
    assert linea["importe_calculado"] == pytest.approx(120.0)
    assert linea["cantidad_convertida"] == pytest.approx(1.0), (
        "R2: sv4 tiro la cantidad convertida que escribio sv6"
    )
    assert total(motor, VALUATION_ID) == pytest.approx(120.0)


def test_f036_r2_el_importe_se_calcula_con_la_convertida_conservada():
    """El revisor cambia SOLO el descuento: 1 contenedor x 120 x 0,90 = 108,00.
    Con la cantidad cruda saldrian 648,00."""
    motor = _sembrar()

    _editar(motor, descuento=10.0)

    linea = _linea(motor)
    assert linea["importe_calculado"] == pytest.approx(108.0)
    assert linea["importe_calculado"] != pytest.approx(648.0)
    assert linea["cantidad_convertida"] == pytest.approx(1.0)
    assert linea["cantidad_albaran"] == pytest.approx(6.0)


def test_f036_r2_una_conversion_reproducible_si_se_rehace():
    """Factor 1000 (t -> kg, precio por kg): la ficha ensena Q = 2000 kg; el
    revisor pone 3000 y la del albaran pasa a 3 t. Aqui sv4 manda."""
    motor = _sembrar(factor=1000.0, cantidad_albaran=2.0, cantidad_convertida=2000.0,
                     pu=0.05, importe=100.0)

    _editar(motor, cantidad=3000.0)

    linea = _linea(motor)
    assert linea["cantidad_albaran"] == pytest.approx(3.0)
    assert linea["cantidad_convertida"] == pytest.approx(3000.0)
    assert linea["importe_calculado"] == pytest.approx(150.0)
    # (antes F-036 R3) una conversión reproducible no va a revisión ni
    # recibe razones.
    assert _traza(motor) == (False, [])


def test_f036_r2_sin_convertida_guardada_manda_la_cantidad_editada():
    """Sin conversion ninguna (la inmensa mayoria): el importe sale de la
    cantidad que pone el revisor, y desde F-065 R10 la convertida queda
    fijada a esa misma cantidad (sv9 no admite una vinculada sin ella)."""
    motor = _sembrar(factor=None, cantidad_albaran=10.0, cantidad_convertida=None,
                     pu=2.5, importe=25.0)

    _editar(motor, cantidad=8.0)

    linea = _linea(motor)
    assert (linea["cantidad_albaran"], linea["cantidad_convertida"]) == (8.0, 8.0)
    assert linea["importe_calculado"] == pytest.approx(20.0)


def test_f036_r2_una_cantidad_convertida_ilegible_no_tumba_el_guardado():
    """Basura en ``cantidad_convertida``: no es reproducible, la del albaran
    se conserva y la convertida pasa a ser lo tecleado (2 x 120 = 240)."""
    motor = _sembrar()
    ejecutar(motor, "UPDATE albaran_line_valuations SET cantidad_convertida = 'ilegible' "
             "WHERE id = 900")

    _editar(motor, cantidad=2.0)

    linea = _linea(motor)
    assert linea["importe_calculado"] == pytest.approx(240.0)
    assert linea["cantidad_convertida"] == pytest.approx(2.0)
    assert linea["cantidad_albaran"] == pytest.approx(6.0)


# ------------------------------------------------------------------ #
# R5 — lo que no se cambia no se toca (la convertida no es una entrada)
# ------------------------------------------------------------------ #
def test_f036_r5_la_convertida_no_entra_en_el_criterio_de_sin_cambios():
    """La linea no la ha tocado nadie: sigue siendo 'declared_albaran'."""
    motor = _sembrar()

    _editar(motor)

    assert _linea(motor)["importe_source"] == "declared_albaran"


def test_f036_r5_reenviar_las_mismas_entradas_no_toca_la_fila():
    """Reenviar la MISMA Q (1 contenedor) y el mismo descuento no es
    intervenir: la fila se queda como la dejo sv6."""
    motor = _sembrar()

    _editar(motor, cantidad=1.0, descuento=None)

    linea = _linea(motor)
    assert linea["importe_source"] == "declared_albaran"
    assert linea["importe_calculado"] == pytest.approx(120.0)
    assert linea["cantidad_convertida"] == pytest.approx(1.0)


# ------------------------------------------------------------------ #
# R6 — la regla es GENERAL, no de residuos
# ------------------------------------------------------------------ #
def test_f036_r6_la_regla_vale_para_cualquier_familia():
    """HORMIGON con una regla de cargas: 7,5 m3 declarados, 2 cargas a 45 EUR.
    El revisor pone un 20 % de descuento: 2 x 45 x 0,8 = 72,00."""
    motor = _sembrar(factor=None, cantidad_albaran=7.5, cantidad_convertida=2.0,
                     pu=45.0, importe=90.0)

    _editar(motor, descuento=20.0)

    linea = _linea(motor)
    assert linea["cantidad_convertida"] == pytest.approx(2.0)
    assert linea["importe_calculado"] == pytest.approx(72.0)


def test_f036_r6_el_codigo_no_mira_la_familia():
    """R6 prohibe condicionar la regla a ``tipo_familia == 'residuos'``.

    Se inspecciona el CODIGO, sin docstrings (que si nombran la familia para
    explicar por que la regla NO puede mirarla): el del repositorio y el de
    ``cantidades_tras_editar``, donde vive ahora la regla de la fila.
    """
    import ast
    import inspect
    import textwrap
    from pathlib import Path

    import infrastructure.database.review_repository as modulo
    from domain.models.review_models import cantidades_tras_editar

    def _sin_docstrings(fuente):
        arbol = ast.parse(fuente)
        for nodo in ast.walk(arbol):
            if isinstance(
                nodo,
                (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef),
            ) and ast.get_docstring(nodo) is not None:
                nodo.body = nodo.body[1:]
        return ast.unparse(arbol)

    for codigo in (
        _sin_docstrings(Path(modulo.__file__).read_text(encoding="utf-8")),
        _sin_docstrings(textwrap.dedent(inspect.getsource(cantidades_tras_editar))),
    ):
        assert "tipo_familia" not in codigo
        assert "residuos" not in codigo


# ------------------------------------------------------------------ #
# R7 — independiente del valor del factor (blindaje ante F-024)
# ------------------------------------------------------------------ #
def test_f036_r7_con_factor_uno_y_convertida_distinta_sigue_conservando():
    """``no_albaran_unit_assumed_same`` devuelve ``factor=1.0``: decidiendo por
    consistencia (1 != 1,0 x 6) la linea sigue protegida."""
    motor = _sembrar(factor=1.0)

    _editar(motor, descuento=10.0)

    linea = _linea(motor)
    assert linea["cantidad_convertida"] == pytest.approx(1.0)
    assert linea["importe_calculado"] == pytest.approx(108.0)
    assert linea["importe_calculado"] != pytest.approx(648.0)


def test_f036_r7_punto_ciego_conocido_un_contenedor_y_una_unidad():
    """PUNTO CIEGO documentado: 1 declarado, 1 contenedor, ``factor=1.0`` es
    indistinguible de una linea sin regla. Pasar Q a 2 da 2 contenedores, y
    la del albaran tambien pasa a 2 (``cantidades_tras_editar``, caso a)."""
    motor = _sembrar(factor=1.0, cantidad_albaran=1.0, cantidad_convertida=1.0)

    _editar(motor, cantidad=2.0)

    linea = _linea(motor)
    assert linea["cantidad_convertida"] == pytest.approx(2.0)
    assert linea["cantidad_albaran"] == pytest.approx(2.0)
    assert linea["importe_calculado"] == pytest.approx(240.0)


# ------------------------------------------------------------------ #
# R3 / R4 — la decision de la fila
# ------------------------------------------------------------------ #
def test_f036_r3_editar_la_cantidad_sin_conversion_reproducible_la_decide_el_revisor():
    """El revisor pone 2 contenedores en la fila de 6 m3.

    Antes (con la cantidad en m3) sv4 no sabia cuantos contenedores eran 8 m3
    y la mandaba a revision. Desde F-065 la cantidad que se edita YA es la de
    contenedores (Q): la decide el revisor, se conserva la del albaran y la
    fila sale de revision como cualquier edicion (R11). Nada se re-encola.
    """
    motor = _sembrar()

    _editar(motor, cantidad=2.0)

    linea = _linea(motor)
    assert linea["cantidad_albaran"] == pytest.approx(6.0)
    assert linea["cantidad_convertida"] == pytest.approx(2.0)
    assert linea["importe_calculado"] == pytest.approx(240.0)
    assert _traza(motor) == (False, [])


def test_f036_r3_sin_editar_la_cantidad_no_se_avisa_de_nada():
    motor = _sembrar()

    _editar(motor, descuento=10.0)

    assert _traza(motor) == (False, [])


def test_f036_r3_las_razones_que_dejo_sv6_no_se_tocan():
    """sv4 no es dueno de las razones: editar la fila no las pisa."""
    motor = _sembrar(razones='["residuos_contenedores"]')

    _editar(motor, cantidad=2.0)

    assert _traza(motor)[1] == ["residuos_contenedores"]


def test_f036_r4_sin_cantidad_convertida_la_edicion_la_fija():
    """Antes se sellaba ``front_sin_cantidad_convertida`` (el importe salia de
    la cantidad cruda). Desde F-065 R10 la convertida nunca queda vacia tras
    editar, asi que no hay nada que dejar dicho."""
    motor = _sembrar(factor=None, cantidad_albaran=10.0, cantidad_convertida=None,
                     pu=2.5, importe=25.0)

    _editar(motor, cantidad=8.0)

    assert _linea(motor)["cantidad_convertida"] == pytest.approx(8.0)
    assert _traza(motor) == (False, [])


def test_f036_r4_una_linea_que_nadie_toca_no_recibe_razones():
    motor = _sembrar(factor=None, cantidad_albaran=10.0, cantidad_convertida=None,
                     pu=2.5, importe=25.0)

    _editar(motor)

    assert _traza(motor) == (False, [])


# ------------------------------------------------------------------ #
# R8 — la plantilla tampoco puede rehacer la conversion
#
# La celda de importe de la tabla del detalle calculaba SU propio numero en
# Jinja: cantidad x precio x (1 - dto/100). Con la linea de SS-0000589 —6 en
# la celda de cantidad, 120 EUR— pintaba 720,00 EUR sobre un importe
# persistido de 120,00. Desde F-065 R12 la celda ensena SIEMPRE el importe
# guardado (el que repinta el JS al teclear es el que guardara el backend).
# ------------------------------------------------------------------ #
def _celda_importe(html):
    """La celda de importe de la fila (aislada: el banner y el total traen
    el mismo importe)."""
    import re

    celda = re.search(
        r'<td[^>]*data-col="importe"[^>]*>.*?</td>', html, re.DOTALL
    )
    assert celda is not None, "no se encontro la celda de importe"
    return celda.group(0)


def test_f036_r8_el_detalle_muestra_el_importe_persistido(
    render_detalle, documento_detalle, linea_valorada, fila_detalle,
):
    html = render_detalle(
        documento_detalle(
            lineas_valoracion=[linea_valorada()],
            display=[fila_detalle()],
        )
    )

    celda = _celda_importe(html)
    assert 'value="120.00"' in celda
    assert "720" not in celda, (
        "R8: la plantilla rehizo la conversion en Jinja"
    )


def test_f036_r8_el_valor_de_ordenacion_tampoco_es_el_producto(
    render_detalle, documento_detalle, linea_valorada, fila_detalle,
):
    html = render_detalle(
        documento_detalle(
            lineas_valoracion=[linea_valorada()],
            display=[fila_detalle()],
        )
    )

    celda = _celda_importe(html)
    assert 'data-sort-value="120.0"' in celda
    assert 'data-sort-value="720.0"' not in celda


def test_f036_r8_una_conversion_reproducible_tambien_ensena_lo_guardado(
    render_detalle, documento_detalle, linea_valorada, fila_detalle,
):
    """Antes la celda pintaba el producto de Jinja (20,00) aunque lo guardado
    fuera otro (99,00). F-065 R12: la celda es lo guardado; lo que cambia al
    teclear lo repinta el JS con la misma formula que el backend."""
    html = render_detalle(
        documento_detalle(
            lineas_valoracion=[
                linea_valorada(
                    factor_conversion=1.0,
                    cantidad_albaran=8.0,
                    cantidad_convertida=8.0,
                    precio_unitario_final=2.5,
                    importe_calculado=99.0,
                )
            ],
            display=[
                fila_detalle(cantidad=8.0, conciliacion={"unitario": 2.5})
            ],
        )
    )

    celda = _celda_importe(html)
    assert 'value="99.00"' in celda
    assert "20.00" not in celda


def test_f036_r8_sin_importe_persistido_se_calcula_como_siempre(
    render_detalle, documento_detalle, linea_valorada, fila_detalle,
):
    """Sin importe guardado: mejor el producto que un hueco."""
    html = render_detalle(
        documento_detalle(
            lineas_valoracion=[linea_valorada(importe_calculado=None)],
            display=[fila_detalle()],
        )
    )

    assert 'value="720.00"' in _celda_importe(html)


def test_f036_r8_el_descuento_no_se_aplica_dos_veces(
    render_detalle, documento_detalle, linea_valorada, fila_detalle,
):
    """El importe persistido YA lleva el descuento aplicado: 108,00."""
    html = render_detalle(
        documento_detalle(
            lineas_valoracion=[linea_valorada(importe_calculado=108.0)],
            display=[fila_detalle(conciliacion={"descuento": 10.0})],
        )
    )

    celda = _celda_importe(html)
    assert 'value="108.00"' in celda
    assert "97.20" not in celda
    assert "648" not in celda


# ------------------------------------------------------------------ #
# Lo defensivo: la purga de motivos del documento (F-036 R24) nunca tumba
# el guardado de la cabecera, y deja la traza del fallo en el log.
# ------------------------------------------------------------------ #
class _SesionRota:
    """Una sesion en la que cualquier escritura falla."""

    def begin_nested(self):
        raise RuntimeError("columna inexistente")


def test_f036_r24_depurar_motivos_no_tumba_el_guardado(repositorio):
    repositorio._depurar_motivos_documento_in_session(
        session=_SesionRota(), document_id="da-igual", cif_actual="B1"
    )


def test_f036_r24_el_aviso_de_lo_defensivo_lleva_la_traza_del_fallo(
    repositorio, caplog,
):
    """Tragar la excepcion SIN el traceback deja el fallo indiagnosticable."""
    import logging

    with caplog.at_level(logging.WARNING):
        repositorio._depurar_motivos_documento_in_session(
            session=_SesionRota(), document_id="da-igual", cif_actual="B1"
        )

    avisos = [r for r in caplog.records if r.levelno == logging.WARNING]
    assert len(avisos) == 1, [r.getMessage() for r in avisos]
    assert avisos[0].exc_info is not None
    assert avisos[0].exc_info[0] is RuntimeError
