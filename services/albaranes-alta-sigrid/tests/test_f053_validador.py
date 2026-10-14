# tests/test_f053_validador.py
"""F-053 · T5 · ``validador_alta``: validación local y construcción de la
petición del modo extendido (R10–R13, R39, R43, R46).

Puro: ni red ni BBDD. Lo que la validación rechaza no llega a sigrid-api.
"""
from __future__ import annotations

from datetime import timedelta

import pytest

from domain.models.alta_models import EstadoAlta, Motivo, PeticionAlbaran
from domain.services.validador_alta import (
    ConfigAlta,
    estado_de_motivos,
    importes_por_referencia,
    lineas_de_otro_contrato,
    normalizar_cif,
    validar_y_construir,
)
from tests.f053_datos import (
    CONFIG,
    CONTRATO,
    DOCUMENT_ID,
    HOY,
    USU,
    MAPEO,
    datos,
    sin_vincular,
    vinculada,
)


def _motivos(resultado) -> list[Motivo]:
    assert isinstance(resultado, list), f"se esperaban motivos y llegó {resultado!r}"
    return resultado


def _codigos(resultado) -> list[str]:
    return [m.codigo for m in _motivos(resultado)]


def _peticion(resultado) -> PeticionAlbaran:
    assert isinstance(resultado, PeticionAlbaran), f"se esperaba petición y llegó {resultado!r}"
    return resultado


def _validar(d, hoy=HOY, config=CONFIG):
    return validar_y_construir(d, config, hoy, USU)


# ------------------------------------------------------------------ #
# normalizar_cif (H21)
# ------------------------------------------------------------------ #
@pytest.mark.parametrize(
    ("entrada", "esperado"),
    [
        ("b00000000", "B00000000"),
        (" B-00.000 000 ", "B00000000"),
        ("ES B00000000", "B00000000"),
        ("ESB00000000", "B00000000"),
        ("es-b00000000", "B00000000"),
        ("ES12345678", "ES12345678"),  # ES delante de 8, no de 9: se queda
        ("ESB000000001", "ESB000000001"),  # ES delante de 10: se queda
        (None, ""),
        ("", ""),
    ],
)
def test_f053_r10_normalizar_cif(entrada, esperado):
    assert normalizar_cif(entrada) == esperado


# ------------------------------------------------------------------ #
# R10 · un motivo por test
# ------------------------------------------------------------------ #
@pytest.mark.parametrize("valor", [None, "", "   "])
def test_f053_r10_falta_obra(valor):
    assert _codigos(_validar(datos(vinculada(1), obra_codigo=valor))) == ["falta_obra"]


@pytest.mark.parametrize("valor", [None, "", "  "])
def test_f053_r10_falta_cif(valor):
    assert _codigos(_validar(datos(vinculada(1), proveedor_cif=valor))) == ["falta_cif"]


@pytest.mark.parametrize("valor", [None, " "])
def test_f053_r10_falta_numero_albaran(valor):
    assert _codigos(_validar(datos(vinculada(1), numero_albaran=valor))) == ["falta_numero_albaran"]


@pytest.mark.parametrize("valor", ["B0000000/0", "B_0000000", "B0000000Ñ", "-.-"])
def test_f053_r10_cif_no_valido(valor):
    assert _codigos(_validar(datos(vinculada(1), proveedor_cif=valor))) == ["cif_no_valido"]


def test_f053_r10_campo_demasiado_largo_en_cabecera():
    for campo, valor in (("obra_codigo", "X" * 25), ("proveedor_cif", "B" * 25),
                         ("numero_albaran", "9" * 129), ("contrato_codigo", "C" * 25)):
        lineas = (sin_vincular(1),) if campo == "contrato_codigo" else (vinculada(1),)
        motivos = _motivos(_validar(datos(*lineas, **{campo: valor})))
        assert [m.codigo for m in motivos] == ["campo_demasiado_largo"], campo


def test_f053_r10_longitudes_en_el_borde_valen():
    d = datos(vinculada(1, codigo_partida_final="P" * 24), obra_codigo="X" * 24,
              proveedor_cif="B" * 24, numero_albaran="9" * 128, contrato_codigo="C" * 24,
              )
    resultado = _validar(d)
    # La vinculada deja de serlo (su contrato es otro), pero nada es «largo».
    assert "campo_demasiado_largo" not in (_codigos(resultado) if isinstance(resultado, list) else [])


def test_f053_r10_partida_de_mas_de_24_en_campo_demasiado_largo():
    motivos = _motivos(_validar(datos(sin_vincular(7, codigo_partida_final="P" * 25))))
    assert motivos == [Motivo("campo_demasiado_largo", "partida", "7")]


@pytest.mark.parametrize("valor", [None, "", "01/10/2026", "2026-02-30", "2026-1-3", "20261001"])
def test_f053_r10_fecha_ilegible(valor):
    assert _codigos(_validar(datos(vinculada(1), fecha=valor))) == ["fecha_ilegible"]


@pytest.mark.parametrize("status", ["partial", "failed", None])
def test_f053_r10_no_valorado(status):
    assert _codigos(_validar(datos(vinculada(1), valoracion_status=status))) == ["no_valorado"]


def test_f053_r10_no_valorado_manual_con_importe_nulo():
    d = datos(sin_vincular(1), sin_vincular(2, importe_calculado=None),
              valoracion_status="manual", contrato_codigo=None)
    assert _codigos(_validar(d)) == ["no_valorado"]


def test_f053_r10_sin_lineas():
    d = datos(vinculada(1, importe_calculado=0.0), sin_vincular(2, importe_calculado=None))
    assert _codigos(_validar(d)) == ["sin_lineas"]


def test_f053_r10_cantidad_no_valida():
    for linea in (sin_vincular(3, cantidad_albaran=None), sin_vincular(3, cantidad_albaran=0.0),
                  vinculada(3, cantidad_convertida=0.0)):
        assert _motivos(_validar(datos(linea))) == [Motivo("cantidad_no_valida", "", "3")]


def test_f053_r10_cantidad_sin_convertir():
    linea = vinculada(4, cantidad_convertida=None, cantidad_albaran=6.0)
    assert _motivos(_validar(datos(linea))) == [Motivo("cantidad_sin_convertir", "", "4")]


@pytest.mark.parametrize(("valoracion", "merge"), [(None, None), ("  ", ""), (None, "  ")])
def test_f053_r10_falta_descripcion(valoracion, merge):
    linea = sin_vincular(5, descripcion_linea=valoracion, descripcion_merge=merge)
    assert _motivos(_validar(datos(linea))) == [Motivo("falta_descripcion", "", "5")]


def test_f053_r10_producto_no_admitido():
    motivos = _motivos(_validar(datos(sin_vincular(6, producto_sigrid="ZZ9999"))))
    assert motivos == [Motivo("producto_no_admitido", "ZZ9999", "6")]


def test_f053_r10_todos_los_motivos_a_la_vez():
    d = datos(
        vinculada(1, cantidad_convertida=None),
        sin_vincular(2, cantidad_albaran=0.0, descripcion_linea=None, descripcion_merge=None,
                     producto_sigrid="ZZ9999", codigo_partida_final="P" * 30),
        obra_codigo=None, proveedor_cif="B-0/0", numero_albaran=" ",
        fecha="mañana", valoracion_status="partial",
    )
    assert sorted(_codigos(_validar(d))) == sorted([
        "falta_obra", "cif_no_valido", "falta_numero_albaran", "fecha_ilegible",
        "no_valorado", "cantidad_sin_convertir", "cantidad_no_valida",
        "falta_descripcion", "producto_no_admitido", "campo_demasiado_largo",
    ])


def test_f053_r10_estado_de_los_motivos_locales():
    assert estado_de_motivos([Motivo("falta_obra")]) is EstadoAlta.NO_ADMITIDO
    assert estado_de_motivos([Motivo("fecha_no_plausible")]) is EstadoAlta.REVISAR
    assert estado_de_motivos([Motivo("signo_incoherente", "", "1")]) is EstadoAlta.REVISAR


# ------------------------------------------------------------------ #
# R11 · casar con el contrato no es requisito; sin partida tampoco
# ------------------------------------------------------------------ #
def test_f053_r11_sin_vincular_sin_partida_y_negativa_son_admisibles():
    d = datos(
        sin_vincular(1),
        sin_vincular(2, codigo_partida_final=None),
        sin_vincular(3, codigo_partida_final="   "),
        vinculada(4, codigo_partida_final=""),
        sin_vincular(5, cantidad_albaran=-2.0, importe_calculado=-18.0),
    )
    assert isinstance(_validar(d), PeticionAlbaran)


def test_f053_r11_ninguna_linea_sin_partida_da_motivo():
    d = datos(*(sin_vincular(i, codigo_partida_final=None) for i in range(1, 6)))
    assert isinstance(_validar(d), PeticionAlbaran)


def test_f053_r11_valorado_a_mano_sin_contrato_es_admisible():
    d = datos(sin_vincular(1), valoracion_status="no_contract", contrato_codigo=None)
    assert isinstance(_validar(d), PeticionAlbaran)


# ------------------------------------------------------------------ #
# R12 · la petición del contrato §2
# ------------------------------------------------------------------ #
def test_f053_r12_peticion_mixta_como_el_ejemplo_6b():
    d = datos(
        vinculada(90201, line_index=0, cantidad_convertida=6.0, importe_calculado=410.4),
        vinculada(90202, line_index=1, cantidad_convertida=2.0, importe_calculado=136.8,
                  codigo_partida_final=None),
        sin_vincular(90203, line_index=2, cantidad_albaran=10.0, importe_calculado=44.0),
        sin_vincular(90204, line_index=3, cantidad_albaran=1.0, importe_calculado=30.0,
                     descripcion_linea="PORTES", codigo_partida_final=""),
        proveedor_cif="b-00000000",
    )
    cuerpo = _peticion(_validar(d)).a_dict()
    assert cuerpo == {
        "cod_obra": "0404", "cif_proveedor": "B00000000", "cod_contrato": CONTRATO,
        "referencia_externa": f"ALB-{DOCUMENT_ID}", "su_referencia": "ALB-58260",
        "usu": "USU_ALTA", "fecha_albaran": 20261003, "empide": None,
        "lineas": [
            {"referencia_linea": "90201", "ctrpro_ide": 700101, "cantidad": 6.0,
             "precio": 68.4, "partida": "03.02.01"},
            {"referencia_linea": "90202", "ctrpro_ide": 700101, "cantidad": 2.0,
             "precio": 68.4},
            {"referencia_linea": "90203", "producto": "MA9999",
             "descripcion": "SACO CEMENTO CEM II 25 KG", "unidad": "UD",
             "cantidad": 10.0, "precio": 4.4, "partida": "03.04.02"},
            {"referencia_linea": "90204", "producto": "MA9999", "descripcion": "PORTES",
             "unidad": "UD", "cantidad": 1.0, "precio": 30.0},
        ],
    }


def test_f053_r12_nunca_claves_prohibidas():
    cuerpo = _peticion(_validar(datos(vinculada(1), sin_vincular(2)))).a_dict()
    for prohibida in ("lineas_recibidas", "naturaleza", "almacen", "database", "commit"):
        assert prohibida not in cuerpo
    for linea in cuerpo["lineas"]:
        for prohibida in ("almacen", "naturaleza", "paride", "almide", "cenide"):
            assert prohibida not in linea


def test_f053_r12_cabecera_recorta_y_usa_la_configuracion():
    d = datos(sin_vincular(1), obra_codigo=" 0404 ", numero_albaran="  N-1  ",
              contrato_codigo=f" {CONTRATO} ")
    config = ConfigAlta(empide=2425207, mapeo=MAPEO)
    peticion = _peticion(validar_y_construir(d, config, HOY, "OTRO"))
    assert peticion.cod_obra == "0404" and peticion.su_referencia == "N-1"
    assert peticion.cod_contrato == CONTRATO
    assert peticion.usu == "OTRO" and peticion.empide == 2425207


def test_f053_r12_cod_contrato_tambien_sin_vinculadas():
    peticion = _peticion(_validar(datos(sin_vincular(1), sin_vincular(2))))
    assert peticion.cod_contrato == CONTRATO
    sin_contrato = _peticion(_validar(datos(sin_vincular(1), contrato_codigo=None)))
    assert sin_contrato.cod_contrato is None


def test_f053_r12_orden_por_line_index_y_manuales_al_final_por_id():
    d = datos(
        sin_vincular(30, line_index=2), sin_vincular(10, line_index=5),
        sin_vincular(99, merge_line_id=None, line_index=None),
        sin_vincular(20, line_index=0), sin_vincular(40, merge_line_id=None, line_index=None),
        sin_vincular(25, line_index=2),
    )
    referencias = [l.referencia_linea for l in _peticion(_validar(d)).lineas]
    assert referencias == ["20", "25", "30", "10", "40", "99"]


def test_f053_r12_referencia_linea_es_el_id_y_cabe_en_24():
    peticion = _peticion(_validar(datos(sin_vincular(2**62))))
    assert peticion.lineas[0].referencia_linea == str(2**62)
    assert len(peticion.lineas[0].referencia_linea) <= 24


def test_f053_r12_vinculada_solo_con_ctrpro_sin_unidad_ni_descripcion():
    linea = _peticion(_validar(datos(vinculada(1)))).lineas[0].a_dict()
    assert set(linea) == {"referencia_linea", "ctrpro_ide", "cantidad", "precio", "partida"}


def test_f053_r12_vinculada_usa_la_cantidad_convertida():
    linea = _peticion(_validar(datos(vinculada(
        1, cantidad_albaran=6000.0, cantidad_convertida=6.0, importe_calculado=60.0,
    )))).lineas[0]
    assert linea.cantidad == 6.0 and linea.precio == 10.0


@pytest.mark.parametrize(
    "linea",
    [
        vinculada(1, matched_contrato_line_id=None),
        vinculada(1, derived_contrato_line_id=9),
        vinculada(1, ctrpro_ide=None),
        # Casada con una línea de contrato sin código de contrato: no se puede
        # decir que sea de otro (R46), así que va sin vincular como antes.
        vinculada(1, contrato_linea=None),
    ],
)
def test_f053_r12_lo_que_no_casa_del_todo_va_sin_vincular(linea):
    enviada = _peticion(_validar(datos(linea))).lineas[0]
    assert enviada.ctrpro_ide is None and enviada.producto == "MA9999"
    assert enviada.descripcion == "HORMIGON HA-25" and enviada.unidad == "M3"
    assert enviada.cantidad == 6.0  # la del albarán


def test_f053_r12_sin_contrato_en_la_valoracion_nada_es_vinculada():
    enviada = _peticion(_validar(datos(vinculada(1, contrato_linea=None),
                                       contrato_codigo=None))).lineas[0]
    assert enviada.ctrpro_ide is None and enviada.producto == "MA9999"


def test_f053_r12_producto_por_defecto_segun_familia_de_la_linea():
    d = datos(sin_vincular(1, tipo_familia="alquiler_maquinaria"),
              sin_vincular(2, tipo_familia="otro"), sin_vincular(3))
    productos = [l.producto for l in _peticion(_validar(d)).lineas]
    assert productos == ["QA9999", "MA9999", "MA9999"]


def test_f053_r12_producto_por_familia_del_documento_y_mixto():
    linea = sin_vincular(1)
    del_documento = _peticion(_validar(datos(linea, tipologia="alquiler_maquinaria")))
    assert del_documento.lineas[0].producto == "QA9999"
    mixto = _peticion(_validar(datos(linea, tipologia="alquiler_maquinaria",
                                     tipologia_mixta=True)))
    assert mixto.lineas[0].producto == "MA9999"


def test_f053_r12_producto_elegido_en_sv4():
    linea = sin_vincular(1, tipo_familia="alquiler_maquinaria", producto_sigrid="XA9999")
    assert _peticion(_validar(datos(linea))).lineas[0].producto == "XA9999"


def test_f053_r12_descripcion_a_128_y_unidad_a_8():
    linea = sin_vincular(1, descripcion_linea="  " + "D" * 200, unidad_albaran=" METROS CUBICOS ")
    enviada = _peticion(_validar(datos(linea))).lineas[0]
    assert enviada.descripcion == "D" * 128
    assert enviada.unidad == "METROS C"


def test_f053_r12_descripcion_del_merge_si_la_valoracion_no_la_tiene():
    linea = sin_vincular(1, descripcion_linea=None, descripcion_merge=" ARENA ")
    assert _peticion(_validar(datos(linea))).lineas[0].descripcion == "ARENA"


def test_f053_r12_sin_unidad_no_se_manda():
    linea = sin_vincular(1, unidad_albaran="  ")
    assert "unidad" not in _peticion(_validar(datos(linea))).lineas[0].a_dict()


def test_f053_r12_partida_recortada_y_solo_si_no_esta_vacia():
    con = _peticion(_validar(datos(sin_vincular(1, codigo_partida_final=" 03.04 "))))
    assert con.lineas[0].partida == "03.04"
    sin = _peticion(_validar(datos(sin_vincular(1, codigo_partida_final=" "))))
    assert "partida" not in sin.lineas[0].a_dict()


def test_f053_r12_precio_neto_a_seis_decimales():
    linea = _peticion(_validar(datos(sin_vincular(1, cantidad_albaran=3.0,
                                                  importe_calculado=100.0)))).lineas[0]
    assert linea.precio == 33.333333 and linea.cantidad == 3.0
    assert round(linea.cantidad * linea.precio, 2) == 100.0


def test_f053_r12_devolucion_cantidad_e_importe_negativos():
    d = datos(sin_vincular(1, cantidad_albaran=-2.0, importe_calculado=-18.0),
              vinculada(2, cantidad_convertida=-3.0, importe_calculado=-36.3))
    lineas = _peticion(_validar(d)).lineas
    assert [(l.cantidad, l.precio) for l in lineas] == [(-2.0, 9.0), (-3.0, 12.1)]
    assert all(l.precio >= 0 for l in lineas)


def test_f053_r12_fecha_en_aaaammdd():
    assert _peticion(_validar(datos(sin_vincular(1), fecha="2026-01-02"))).fecha_albaran == 20260102


def test_f053_r12_importes_por_referencia_solo_de_lineas_a_registrar():
    d = datos(sin_vincular(1, importe_calculado=44.0), sin_vincular(2, importe_calculado=0.0),
              vinculada(3, importe_calculado=-5.5))
    assert importes_por_referencia(d) == {"1": 44.0, "3": -5.5}


# ------------------------------------------------------------------ #
# R13 · fuera las de importe nulo o 0, también vinculadas con cantidad
# ------------------------------------------------------------------ #
def test_f053_r13_fuera_las_lineas_sin_importe():
    d = datos(vinculada(1), vinculada(2, importe_calculado=0.0, cantidad_convertida=5.0),
              sin_vincular(3, importe_calculado=None), sin_vincular(4))
    assert [l.referencia_linea for l in _peticion(_validar(d)).lineas] == ["1", "4"]


def test_f053_r13_linea_sin_importe_no_aporta_motivos():
    d = datos(sin_vincular(1), sin_vincular(2, importe_calculado=0.0, cantidad_albaran=None,
                                            descripcion_linea=None, descripcion_merge=None,
                                            producto_sigrid="ZZ"))
    assert isinstance(_validar(d), PeticionAlbaran)


# ------------------------------------------------------------------ #
# R43 · producto_sigrid ignorado en vinculadas
# ------------------------------------------------------------------ #
def test_f053_r43_vinculada_ignora_el_producto_elegido():
    for elegido in ("XA9999", "ZZ9999"):
        resultado = _validar(datos(vinculada(1, producto_sigrid=elegido)))
        linea = _peticion(resultado).lineas[0]
        assert linea.producto is None and linea.ctrpro_ide == 700101


# ------------------------------------------------------------------ #
# R39 · fecha no plausible y signos opuestos (revisar sin llamar a nadie)
# ------------------------------------------------------------------ #
@pytest.mark.parametrize(
    ("dias", "motivo"),
    [(0, False), (1, True), (-365, False), (-366, True), (-10, False), (30, True)],
)
def test_f053_r39_fecha_no_plausible_en_el_borde(dias, motivo):
    fecha = (HOY + timedelta(days=dias)).isoformat()
    resultado = _validar(datos(sin_vincular(1), fecha=fecha))
    if motivo:
        assert _codigos(resultado) == ["fecha_no_plausible"]
    else:
        assert isinstance(resultado, PeticionAlbaran)


def test_f053_r39_signo_incoherente_descuento():
    resultado = _validar(datos(sin_vincular(1), sin_vincular(8, cantidad_albaran=1.0,
                                                             importe_calculado=-12.0)))
    assert _motivos(resultado) == [Motivo("signo_incoherente", "cantidad 1.0, importe -12.0", "8")]


def test_f053_r39_signo_incoherente_al_reves():
    resultado = _validar(datos(vinculada(9, cantidad_convertida=-2.0, importe_calculado=20.0)))
    assert [(m.codigo, m.referencia_linea) for m in _motivos(resultado)] == [
        ("signo_incoherente", "9"),
    ]


def test_f053_r39_los_dos_motivos_a_la_vez():
    d = datos(sin_vincular(1, cantidad_albaran=2.0, importe_calculado=-4.0),
              sin_vincular(2, cantidad_albaran=-2.0, importe_calculado=4.0),
              fecha=(HOY + timedelta(days=2)).isoformat())
    assert sorted(_codigos(_validar(d))) == [
        "fecha_no_plausible", "signo_incoherente", "signo_incoherente",
    ]


def test_f053_r46_linea_de_otro_contrato_va_a_revisar():
    """D2 (humano, 2026-10-06): casar con OTRO contrato «no debería ocurrir
    nunca». Antes iba sin vincular, en silencio (desviación 8)."""
    resultado = _validar(datos(vinculada(1), vinculada(2, contrato_linea="CTOTRO/9")))
    assert _motivos(resultado) == [
        Motivo("linea_de_otro_contrato", f"CTOTRO/9 (valoración: {CONTRATO})", "2"),
    ]
    assert estado_de_motivos(resultado) is EstadoAlta.REVISAR


def test_f053_r46_valoracion_sin_contrato_con_una_linea_casada():
    resultado = _validar(datos(vinculada(1), contrato_codigo=None))
    assert _motivos(resultado) == [
        Motivo("linea_de_otro_contrato", f"{CONTRATO} (valoración: sin contrato)", "1"),
    ]


def test_f053_r46_junto_a_los_de_r39():
    d = datos(vinculada(2, contrato_linea="CTOTRO/9", importe_calculado=-5.0))
    assert sorted(_codigos(_validar(d))) == ["linea_de_otro_contrato", "signo_incoherente"]
    assert estado_de_motivos(_validar(d)) is EstadoAlta.REVISAR


def test_f053_r46_no_se_evalua_si_hay_motivos_de_r10():
    d = datos(vinculada(2, contrato_linea="CTOTRO/9"), obra_codigo=None)
    assert _codigos(_validar(d)) == ["falta_obra"]


def test_f053_r46_solo_cuentan_las_lineas_a_registrar():
    d = datos(vinculada(1), vinculada(2, contrato_linea="CTOTRO/9", importe_calculado=0.0))
    assert [l.referencia_linea for l in _peticion(_validar(d)).lineas] == ["1"]
    assert lineas_de_otro_contrato(d) == []


def test_f053_r46_lineas_de_otro_contrato_las_devuelve_en_orden():
    d = datos(vinculada(3, contrato_linea="CTOTRO/9"), vinculada(1),
              vinculada(2, contrato_linea=" CTSU16/0206 "))  # mismo contrato, con espacios
    assert [l.id for l in lineas_de_otro_contrato(d)] == [3]


def test_f053_r39_no_se_evalua_si_hay_motivos_de_r10():
    d = datos(sin_vincular(1, cantidad_albaran=2.0, importe_calculado=-4.0),
              obra_codigo=None, fecha=(HOY + timedelta(days=5)).isoformat())
    assert _codigos(_validar(d)) == ["falta_obra"]
