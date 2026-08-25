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

En cuanto el revisor abre la ficha en sv4 y guarda,
``_recalc_valuation_importes`` ve ``factor IS NULL``, tira la
``cantidad_convertida`` que escribio sv6 y recalcula con la cantidad
CRUDA del albaran: 6 x 120 = 720,00 EUR. Seis veces el importe correcto.

La regla que arregla esto es GENERAL (R6), no de residuos: si la
``cantidad_convertida`` guardada NO se explica como
``factor x cantidad_albaran``, es que alguien de aguas arriba aplico una
regla de calculo propia que sv4 no conoce. Ese dato se conserva; no se
reinventa.

Los tests de este fichero no tocan red ni BBDD real: SQLite en memoria
del ``conftest.py`` de sv4.
"""
from __future__ import annotations

import pytest
from sqlalchemy import text

VALUATION_ID = "f036-0000-0000-0000-000000000589"
DOCUMENT_ID = "f036-doc-0000-0000-000000000589"

#: La linea tal cual la dejo sv6 en SS-0000589: 6 m3 declarados, un
#: contenedor valorado, 120,00 EUR. Sin factor de conversion.
LINEA_RESIDUOS = {
    "id": 900,
    "merge_line_id": 500,
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


def _sembrar(sesion, **cambios):
    """Deja una valoracion de una sola linea, como la escribio sv6."""
    linea = dict(LINEA_RESIDUOS)
    linea.update(cambios)
    sesion.execute(
        text(
            "INSERT INTO albaran_valuations "
            "(id, document_id, total_valorado, updated_at_utc) "
            "VALUES (:id, :doc, :tot, '2026-08-19T10:00:00Z')"
        ),
        {"id": VALUATION_ID, "doc": DOCUMENT_ID, "tot": linea["importe"]},
    )
    sesion.execute(
        text(
            "INSERT INTO albaran_line_valuations ("
            "  id, valuation_id, merge_line_id, precio_unitario_final, "
            "  factor_conversion, cantidad_albaran, cantidad_convertida, "
            "  importe_calculado, importe_albaran_declarado, "
            "  importe_source, descuento_albaran_aplicado) "
            "VALUES (:id, :vid, :mid, :pu, :factor, :ca, :cc, "
            "        :imp, NULL, :src, :dto)"
        ),
        {
            "id": linea["id"],
            "vid": VALUATION_ID,
            "mid": linea["merge_line_id"],
            "pu": linea["pu"],
            "factor": linea["factor"],
            "ca": linea["cantidad_albaran"],
            "cc": linea["cantidad_convertida"],
            "imp": linea["importe"],
            "src": linea["source"],
            "dto": linea["dto"],
        },
    )
    sesion.flush()
    return linea


def _leer_linea(sesion, merge_line_id=500):
    return sesion.execute(
        text(
            "SELECT cantidad_albaran, cantidad_convertida, "
            "       importe_calculado, importe_source "
            "FROM albaran_line_valuations WHERE merge_line_id = :m"
        ),
        {"m": merge_line_id},
    ).mappings().one()


def _leer_total(sesion):
    return sesion.execute(
        text("SELECT total_valorado FROM albaran_valuations WHERE id = :v"),
        {"v": VALUATION_ID},
    ).scalar_one()


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
    from infrastructure.database.review_repository import (
        _conversion_reproducible,
    )

    assert _conversion_reproducible(
        factor=factor,
        cantidad_albaran=cantidad_albaran,
        cantidad_convertida=cantidad_convertida,
    ) is esperado


def test_f036_r1_la_tolerancia_absorbe_el_ruido_de_coma_flotante():
    """0,1 x 3 = 0,30000000000000004 en binario. Sigue siendo el producto."""
    from infrastructure.database.review_repository import (
        _conversion_reproducible,
    )

    assert _conversion_reproducible(
        factor=0.1, cantidad_albaran=3.0, cantidad_convertida=0.3
    ) is True


# ------------------------------------------------------------------ #
# R2 — la cantidad convertida que no sabemos rehacer se CONSERVA
# ------------------------------------------------------------------ #
def test_f036_r2_guardar_sin_tocar_nada_no_multiplica_el_importe_por_seis(
    repositorio, sesion,
):
    """El caso EXACTO de SS-0000589: abrir la ficha y guardar.

    Antes: 6 m3 x 120 EUR = 720,00 y la ``cantidad_convertida`` a NULL.
    """
    _sembrar(sesion)

    repositorio._recalc_valuation_importes(
        session=sesion,
        document_id=DOCUMENT_ID,
        new_line_quantities={},
    )

    linea = _leer_linea(sesion)
    assert linea["importe_calculado"] != pytest.approx(IMPORTE_INFLADO)
    assert linea["importe_calculado"] == pytest.approx(120.0)
    assert linea["cantidad_convertida"] == pytest.approx(1.0), (
        "R2: sv4 tiro la cantidad convertida que escribio sv6"
    )
    assert _leer_total(sesion) == pytest.approx(120.0)


def test_f036_r2_el_importe_se_calcula_con_la_convertida_conservada(
    repositorio, sesion,
):
    """El revisor cambia SOLO el descuento: la fila se reescribe.

    Es el caso que obliga a pasar por el UPDATE conservando la
    convertida: 1 contenedor x 120 EUR x 0,90 = 108,00. Con la cantidad
    cruda saldrian 648,00.
    """
    _sembrar(sesion)

    repositorio._recalc_valuation_importes(
        session=sesion,
        document_id=DOCUMENT_ID,
        new_line_quantities={},
        new_line_discounts={500: 10.0},
    )

    linea = _leer_linea(sesion)
    assert linea["importe_calculado"] == pytest.approx(108.0)
    assert linea["importe_calculado"] != pytest.approx(648.0)
    assert linea["cantidad_convertida"] == pytest.approx(1.0)
    assert linea["cantidad_albaran"] == pytest.approx(6.0)


def test_f036_r2_una_conversion_reproducible_si_se_rehace(
    repositorio, sesion,
):
    """Contrapunto: cuando SI sabemos rehacerla, se rehace.

    Factor 1000 (Tn -> Kg): el revisor corrige 2 Tn a 3 Tn y la
    convertida pasa de 2000 a 3000 Kg. Aqui sv4 manda, y debe mandar.
    """
    _sembrar(
        sesion,
        factor=1000.0,
        cantidad_albaran=2.0,
        cantidad_convertida=2000.0,
        pu=0.05,
        importe=100.0,
    )

    repositorio._recalc_valuation_importes(
        session=sesion,
        document_id=DOCUMENT_ID,
        new_line_quantities={500: 3.0},
    )

    linea = _leer_linea(sesion)
    assert linea["cantidad_convertida"] == pytest.approx(3000.0)
    assert linea["importe_calculado"] == pytest.approx(150.0)


def test_f036_r2_sin_convertida_guardada_manda_la_cantidad_cruda(
    repositorio, sesion,
):
    """R4 (parte de comportamiento): sin convertida, todo sigue igual.

    Es el caso de la inmensa mayoria de albaranes —y el de las cinco
    lineas del Feymaco de F-019—: no hay conversion ninguna, el importe
    se calcula con la cantidad del albaran.
    """
    _sembrar(
        sesion,
        factor=None,
        cantidad_albaran=10.0,
        cantidad_convertida=None,
        pu=2.5,
        importe=25.0,
    )

    repositorio._recalc_valuation_importes(
        session=sesion,
        document_id=DOCUMENT_ID,
        new_line_quantities={500: 8.0},
    )

    linea = _leer_linea(sesion)
    assert linea["cantidad_convertida"] is None
    assert linea["importe_calculado"] == pytest.approx(20.0)


# ------------------------------------------------------------------ #
# R5 — el guardian de F-019 R24 mira las ENTRADAS, no la convertida
# ------------------------------------------------------------------ #
def test_f036_r5_la_convertida_no_entra_en_el_criterio_de_sin_cambios(
    repositorio, sesion,
):
    """La linea no la ha tocado nadie: sigue siendo 'declared_albaran'.

    Antes, la comparacion incluia
    ``_num_iguales(row['cantidad_convertida'], nueva_cant_conv)``, y
    como el recalculo dejaba ``nueva_cant_conv=None`` frente al 1
    guardado, TODA linea de residuos se veia como cambiada en cada
    guardado. El guardian de F-019 no la protegia jamas.
    """
    _sembrar(sesion)

    repositorio._recalc_valuation_importes(
        session=sesion,
        document_id=DOCUMENT_ID,
        new_line_quantities={},
    )

    assert _leer_linea(sesion)["importe_source"] == "declared_albaran"


def test_f036_r5_reenviar_las_mismas_entradas_no_toca_la_fila(
    repositorio, sesion,
):
    """El front reenvia cantidad y descuento en cada guardado.

    Reenviar los MISMOS valores no es intervenir: la fila se queda como
    la dejo sv6, importe y fuente incluidos.
    """
    _sembrar(sesion)

    repositorio._recalc_valuation_importes(
        session=sesion,
        document_id=DOCUMENT_ID,
        new_line_quantities={500: 6.0},
        new_line_discounts={500: None},
    )

    linea = _leer_linea(sesion)
    assert linea["importe_source"] == "declared_albaran"
    assert linea["importe_calculado"] == pytest.approx(120.0)
    assert linea["cantidad_convertida"] == pytest.approx(1.0)


# ------------------------------------------------------------------ #
# R6 — la regla es GENERAL, no de residuos
# ------------------------------------------------------------------ #
def test_f036_r6_la_regla_vale_para_cualquier_familia(
    repositorio, sesion,
):
    """Nada en el codigo puede mirar ``tipo_familia == 'residuos'``.

    Aqui la linea es de HORMIGON con una regla de cargas: el albaran
    declara 7,5 m3 y el contrato tarifa CARGAS; sv6 dejo 2 cargas a
    45 EUR = 90,00. sv4 no sabe convertir m3 en cargas, luego conserva.
    """
    _sembrar(
        sesion,
        factor=None,
        cantidad_albaran=7.5,
        cantidad_convertida=2.0,
        pu=45.0,
        importe=90.0,
    )

    repositorio._recalc_valuation_importes(
        session=sesion,
        document_id=DOCUMENT_ID,
        new_line_quantities={},
        new_line_discounts={500: 20.0},
    )

    linea = _leer_linea(sesion)
    assert linea["cantidad_convertida"] == pytest.approx(2.0)
    assert linea["importe_calculado"] == pytest.approx(72.0)


def test_f036_r6_el_codigo_del_repositorio_no_mira_la_familia():
    """R6 prohibe condicionar la regla a ``tipo_familia == 'residuos'``.

    Se inspecciona el CODIGO, no el fichero: los docstrings y los
    comentarios si nombran la familia —explican por que la regla NO
    puede mirarla— y eso es exactamente lo que se quiere leer ahi. Lo
    que no puede existir es un ``if`` que la mire.
    """
    import ast
    from pathlib import Path

    import infrastructure.database.review_repository as modulo

    arbol = ast.parse(
        Path(modulo.__file__).read_text(encoding="utf-8")
    )
    for nodo in ast.walk(arbol):
        if isinstance(
            nodo,
            (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef),
        ) and ast.get_docstring(nodo) is not None:
            nodo.body = nodo.body[1:]
    codigo = ast.unparse(arbol)

    assert "tipo_familia" not in codigo
    assert "residuos" not in codigo


# ------------------------------------------------------------------ #
# R7 — independiente del valor del factor (blindaje ante F-024)
# ------------------------------------------------------------------ #
def test_f036_r7_con_factor_uno_y_convertida_distinta_sigue_conservando(
    repositorio, sesion,
):
    """El caso que traera F-024 y que hoy no se puede reproducir.

    ``unit_converter`` tiene una rama ``no_albaran_unit_assumed_same``
    que devuelve ``factor=1.0``. Si sv4 decidiera por ``factor IS NULL``,
    esa rama devolveria el x6 en cuanto F-024 entre. Decidiendo por
    consistencia (1 != 1,0 x 6) la linea sigue protegida.
    """
    _sembrar(sesion, factor=1.0)

    repositorio._recalc_valuation_importes(
        session=sesion,
        document_id=DOCUMENT_ID,
        new_line_quantities={},
        new_line_discounts={500: 10.0},
    )

    linea = _leer_linea(sesion)
    assert linea["cantidad_convertida"] == pytest.approx(1.0)
    assert linea["importe_calculado"] == pytest.approx(108.0)
    assert linea["importe_calculado"] != pytest.approx(648.0)


def test_f036_r7_punto_ciego_conocido_un_contenedor_y_una_unidad(
    repositorio, sesion,
):
    """PUNTO CIEGO documentado, no un comportamiento deseado.

    Si el albaran declara 1 (no 6) y sv6 valora 1 contenedor con
    ``factor=1.0``, la comparacion 1 == 1,0 x 1 dice «reproducible»
    aunque sv6 SI haya aplicado su regla de contenedores. Es
    indistinguible desde sv4 con los datos persistidos hoy: no hay
    columna que diga «aqui hubo una regla de negocio».

    En la practica no hace dano —rehacer 1,0 x 1 devuelve el mismo 1—,
    y solo se notaria si el revisor EDITA la cantidad: pasar a 2
    daria 2 contenedores. Este test fija ese comportamiento para que un
    cambio futuro (p.e. una columna ``conversion_source`` escrita por
    sv6) lo tenga que romper a proposito.
    """
    _sembrar(sesion, factor=1.0, cantidad_albaran=1.0, cantidad_convertida=1.0)

    repositorio._recalc_valuation_importes(
        session=sesion,
        document_id=DOCUMENT_ID,
        new_line_quantities={500: 2.0},
    )

    linea = _leer_linea(sesion)
    assert linea["cantidad_convertida"] == pytest.approx(2.0)
    assert linea["importe_calculado"] == pytest.approx(240.0)


# ------------------------------------------------------------------ #
# R3 / R4 — la decision queda escrita en las razones de la linea
# ------------------------------------------------------------------ #
def _leer_traza(sesion, merge_line_id=500):
    """(review_required, [razones]) de la linea de valoracion."""
    import json

    fila = sesion.execute(
        text(
            "SELECT review_required, review_reasons_json "
            "FROM albaran_line_valuations WHERE merge_line_id = :m"
        ),
        {"m": merge_line_id},
    ).mappings().one()
    return (
        bool(fila["review_required"]),
        json.loads(fila["review_reasons_json"] or "[]"),
    )


def test_f036_r3_editar_la_cantidad_sin_conversion_reproducible_va_a_revision(
    repositorio, sesion,
):
    """El revisor corrige 6 m3 -> 8 m3 en una linea de contenedores.

    sv4 no sabe cuantos contenedores son 8 m3 —esa regla es de sv6—, asi
    que CONSERVA el contenedor valorado y avisa: la cantidad cambio pero
    la conversion no se ha rehecho, que lo mire un humano. Lo que NO
    hace es re-encolar a q-valoracion (decision del 2026-08-22).
    """
    from infrastructure.database.review_repository import (
        REASON_CANTIDAD_EDITADA_SIN_CONVERSION,
    )

    _sembrar(sesion)

    repositorio._recalc_valuation_importes(
        session=sesion,
        document_id=DOCUMENT_ID,
        new_line_quantities={500: 8.0},
    )

    linea = _leer_linea(sesion)
    assert linea["cantidad_albaran"] == pytest.approx(8.0)
    assert linea["cantidad_convertida"] == pytest.approx(1.0)
    assert linea["importe_calculado"] == pytest.approx(120.0)

    revision, razones = _leer_traza(sesion)
    assert revision is True
    assert REASON_CANTIDAD_EDITADA_SIN_CONVERSION in razones


def test_f036_r3_la_razon_no_se_duplica_al_guardar_dos_veces(
    repositorio, sesion,
):
    """Idempotencia: el revisor guarda dos veces, la razon sigue una."""
    from infrastructure.database.review_repository import (
        REASON_CANTIDAD_EDITADA_SIN_CONVERSION,
    )

    _sembrar(sesion)

    for cantidad in (8.0, 9.0):
        repositorio._recalc_valuation_importes(
            session=sesion,
            document_id=DOCUMENT_ID,
            new_line_quantities={500: cantidad},
        )

    _, razones = _leer_traza(sesion)
    assert razones.count(REASON_CANTIDAD_EDITADA_SIN_CONVERSION) == 1


def test_f036_r3_sin_editar_la_cantidad_no_se_avisa_de_nada(
    repositorio, sesion,
):
    """Solo cambia el descuento: la conversion no queda en entredicho.

    La cantidad convertida sigue describiendo la misma entrega, asi que
    no hay nada que revisar por este motivo.
    """
    from infrastructure.database.review_repository import (
        REASON_CANTIDAD_EDITADA_SIN_CONVERSION,
    )

    _sembrar(sesion)

    repositorio._recalc_valuation_importes(
        session=sesion,
        document_id=DOCUMENT_ID,
        new_line_quantities={},
        new_line_discounts={500: 10.0},
    )

    revision, razones = _leer_traza(sesion)
    assert REASON_CANTIDAD_EDITADA_SIN_CONVERSION not in razones
    assert revision is False


def test_f036_r3_una_conversion_reproducible_no_va_a_revision(
    repositorio, sesion,
):
    """Contrapunto: si sabemos rehacerla, editar la cantidad es normal."""
    _sembrar(
        sesion,
        factor=1000.0,
        cantidad_albaran=2.0,
        cantidad_convertida=2000.0,
        pu=0.05,
        importe=100.0,
    )

    repositorio._recalc_valuation_importes(
        session=sesion,
        document_id=DOCUMENT_ID,
        new_line_quantities={500: 3.0},
    )

    revision, razones = _leer_traza(sesion)
    assert revision is False
    assert razones == []


def test_f036_r3_la_razon_no_pisa_las_que_dejo_sv6(repositorio, sesion):
    """Las razones de sv6 (``residuos_*``) se conservan; se ANADE."""
    from infrastructure.database.review_repository import (
        REASON_CANTIDAD_EDITADA_SIN_CONVERSION,
    )

    _sembrar(sesion)
    sesion.execute(
        text(
            "UPDATE albaran_line_valuations "
            "SET review_reasons_json = '[\"residuos_contenedores\"]' "
            "WHERE merge_line_id = 500"
        )
    )
    sesion.flush()

    repositorio._recalc_valuation_importes(
        session=sesion,
        document_id=DOCUMENT_ID,
        new_line_quantities={500: 8.0},
    )

    _, razones = _leer_traza(sesion)
    assert razones == [
        "residuos_contenedores",
        REASON_CANTIDAD_EDITADA_SIN_CONVERSION,
    ]


def test_f036_r4_sin_cantidad_convertida_se_deja_dicho(repositorio, sesion):
    """R4: el importe sale de la cantidad cruda, y consta que fue asi.

    No es un aviso de revision —el resultado es el de siempre y es
    correcto—: es trazabilidad de con que cantidad se calculo.
    """
    from infrastructure.database.review_repository import (
        REASON_SIN_CANTIDAD_CONVERTIDA,
    )

    _sembrar(
        sesion,
        factor=None,
        cantidad_albaran=10.0,
        cantidad_convertida=None,
        pu=2.5,
        importe=25.0,
    )

    repositorio._recalc_valuation_importes(
        session=sesion,
        document_id=DOCUMENT_ID,
        new_line_quantities={500: 8.0},
    )

    revision, razones = _leer_traza(sesion)
    assert REASON_SIN_CANTIDAD_CONVERTIDA in razones
    assert revision is False, (
        "R4 no manda la linea a revision: solo R3 lo hace"
    )


def test_f036_r4_una_linea_que_nadie_toca_no_recibe_razones(
    repositorio, sesion,
):
    """El guardian de F-019 R24 manda tambien sobre las razones.

    Si el revisor no ha intervenido en la linea, el guardado no la toca:
    ni el importe, ni la fuente, ni las razones. Sin esto, abrir y
    guardar un documento cualquiera sellaria
    ``front_sin_cantidad_convertida`` en TODAS sus lineas —que es el
    caso mayoritario: sin conversion de unidad no hay convertida— y la
    traza dejaria de significar nada.
    """
    _sembrar(
        sesion,
        factor=None,
        cantidad_albaran=10.0,
        cantidad_convertida=None,
        pu=2.5,
        importe=25.0,
    )

    repositorio._recalc_valuation_importes(
        session=sesion,
        document_id=DOCUMENT_ID,
        new_line_quantities={},
    )

    revision, razones = _leer_traza(sesion)
    assert razones == []
    assert revision is False


def test_f036_r3_el_helper_de_razones_es_idempotente(repositorio, sesion):
    """``_anadir_reason_linea_in_session`` no duplica ni pierde nada."""
    _sembrar(sesion)

    for _ in range(3):
        repositorio._anadir_reason_linea_in_session(
            session=sesion,
            valuation_line_id=LINEA_RESIDUOS["id"],
            reason="una_razon",
        )
    repositorio._anadir_reason_linea_in_session(
        session=sesion,
        valuation_line_id=LINEA_RESIDUOS["id"],
        reason="otra_razon",
    )
    sesion.flush()

    _, razones = _leer_traza(sesion)
    assert razones == ["una_razon", "otra_razon"]




# ------------------------------------------------------------------ #
# R8 — la plantilla tampoco puede rehacer la conversion
#
# El backend ya no destroza el dato (R1-R7), pero la celda de importe de
# la tabla del detalle calcula SU propio numero en Jinja:
#   cantidad x precio_de_contrato x (1 - dto/100)
# Con la linea de SS-0000589 —6 en la celda de cantidad, 120 EUR de
# precio de contrato— eso pinta 720,00 EUR sobre un importe persistido
# de 120,00. El revisor ve un numero que no esta en ninguna parte de la
# BBDD y que no cuadra con el total del documento.
#
# Las factorias (`documento_detalle`, `linea_valorada`, `fila_detalle`) y
# el renderizador viven en el conftest.
# ------------------------------------------------------------------ #
def _celda_importe(html):
    """La celda de importe de la fila de la tabla del detalle.

    Se aisla a proposito: el HTML de la ficha entera trae el mismo
    importe en el banner, en el precio unitario y en el total, asi que
    buscar «120,00» en toda la pagina no probaria nada.
    """
    import re

    celda = re.search(
        r'<td[^>]*data-col="importe"[^>]*>.*?</td>', html, re.DOTALL
    )
    assert celda is not None, "no se encontro la celda de importe"
    return celda.group(0)


def test_f036_r8_el_detalle_muestra_el_importe_persistido(
    render_detalle, documento_detalle, linea_valorada, fila_detalle,
):
    """Cantidad 6, convertida 1, importe 120: la celda pinta 120,00.

    Se mira el campo editable porque es lo que ve el revisor: la tabla
    del detalle solo se pinta en modo edicion (la vista de solo lectura
    del documento es otra plantilla dentro del mismo fichero).
    """
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
    """Ordenar por importe debe ordenar por lo que se ve.

    La celda lleva un ``data-sort-value`` que usa la tabla para ordenar.
    Si ahi sigue el producto de Jinja, la columna se ordena por un numero
    distinto del que pinta.
    """
    html = render_detalle(
        documento_detalle(
            lineas_valoracion=[linea_valorada()],
            display=[fila_detalle()],
        )
    )

    celda = _celda_importe(html)
    assert 'data-sort-value="120.0"' in celda
    assert 'data-sort-value="720.0"' not in celda


def test_f036_r8_una_conversion_reproducible_sigue_calculando_en_jinja(
    render_detalle, documento_detalle, linea_valorada, fila_detalle,
):
    """Contrapunto: donde no hay regla ajena, la celda sigue como estaba.

    Linea normal: 8 unidades a 2,50 EUR = 20,00. El importe persistido
    esta viejo a proposito (99,00) porque es lo que pasa mientras el
    revisor teclea: la celda sigue mostrando el producto, que es lo que
    hace que editar la cantidad se refleje al instante en la tabla.
    """
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
            display=[fila_detalle(cantidad=8.0, conciliacion={"unitario": 2.5})],
        )
    )

    celda = _celda_importe(html)
    assert 'value="20.00"' in celda
    assert "99" not in celda


def test_f036_r8_sin_importe_persistido_se_calcula_como_siempre(
    render_detalle, documento_detalle, linea_valorada, fila_detalle,
):
    """No reproducible pero sin importe guardado: no hay nada que pintar.

    Es el caso de la sintetica sin tarifa (R17). Mejor el producto que un
    hueco: la celda no puede quedarse vacia por no tener el dato bueno.
    """
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
    """El importe persistido YA lleva el descuento aplicado.

    1 contenedor x 120 EUR x 0,90 = 108,00, que es lo que hay en BBDD. Si
    la celda volviera a aplicar el 10 % sobre el persistido saldrian
    97,20; si recalculara desde la cantidad, 648,00.
    """
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
