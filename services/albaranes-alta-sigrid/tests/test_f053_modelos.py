# tests/test_f053_modelos.py
"""F-053 · T4 · modelos de dominio y puertos de sv9 (design §3).

Sin red ni BBDD: construcción y serialización de los modelos, y forma de los
tres puertos.
"""
from __future__ import annotations

import inspect
from abc import ABC

import pytest

from domain.models.alta_models import (
    ESTADOS_BLOQUEANTES,
    AccionAlta,
    AdjuntoEstado,
    AltaActual,
    CabeceraAlta,
    Decision,
    ErrorAlta,
    EstadoAlta,
    LineaAlta,
    LineaPeticion,
    ModoAlta,
    Motivo,
    PeticionAlbaran,
    RespuestaAlta,
    ResultadoAlta,
    TipoFallo,
)


def test_f053_modelos_los_nueve_estados():
    assert {e.value for e in EstadoAlta} == {
        "en_curso", "no_admitido", "ya_en_sigrid", "simulado", "revisar",
        "error", "incierto", "registrado", "anulado",
    }
    assert ESTADOS_BLOQUEANTES == frozenset(
        {EstadoAlta.EN_CURSO, EstadoAlta.INCIERTO, EstadoAlta.REGISTRADO},
    )


def test_f053_modelos_enumerados_auxiliares():
    assert {m.value for m in ModoAlta} == {"simulacion", "real"}
    assert {a.value for a in AccionAlta} == {"alta", "verificar_anulacion"}
    assert {a.value for a in AdjuntoEstado} == {"colgado", "error"}
    assert {d.value for d in Decision} == {
        "ignorar", "solo_adjunto", "a_incierto", "procesar", "verificar_anulacion",
    }


def test_f053_modelos_motivo_ida_y_vuelta():
    motivo = Motivo("importe_distinto", "pedido 10.00, previa 10.10", "77")
    assert motivo.a_dict() == {
        "codigo": "importe_distinto", "detalle": "pedido 10.00, previa 10.10",
        "referencia_linea": "77",
    }
    assert Motivo.desde_dict(motivo.a_dict()) == motivo
    assert Motivo("sin_lineas").a_dict() == {"codigo": "sin_lineas", "detalle": ""}
    assert Motivo.desde_dict({"codigo": "x"}) == Motivo("x")


def test_f053_modelos_clasificacion_del_documento():
    base = {"document_id": "d", "obra_codigo": "0404", "proveedor_cif": "B1",
                "numero_albaran": "1", "fecha": "2026-10-01", "valoracion_status": "ok",
                "contrato_codigo": None}
    assert CabeceraAlta(**base).clasificacion is None
    assert CabeceraAlta(**base, tipologia="hormigon").clasificacion == {
        "familia": "hormigon", "mixto": False,
    }
    assert CabeceraAlta(**base, tipologia="residuos", tipologia_mixta=True).clasificacion == {
        "familia": "residuos", "mixto": True,
    }


def test_f053_modelos_referencia_linea_es_el_id_en_texto():
    linea = LineaAlta(id=123456789, merge_line_id=None, line_index=None,
                      cantidad_albaran=1.0, cantidad_convertida=None,
                      unidad_albaran="UD", importe_calculado=1.0,
                      matched_contrato_line_id=None, derived_contrato_line_id=None,
                      ctrpro_ide=None, contrato_linea=None, codigo_partida_final=None,
                      descripcion_linea="x", descripcion_merge=None,
                      tipo_familia=None, producto_sigrid=None)
    assert linea.referencia_linea == "123456789"


def test_f053_modelos_linea_de_peticion_omite_lo_que_no_va():
    vinculada = LineaPeticion(referencia_linea="1", cantidad=2.0, precio=3.5, ctrpro_ide=70)
    assert vinculada.a_dict() == {
        "referencia_linea": "1", "ctrpro_ide": 70, "cantidad": 2.0, "precio": 3.5,
    }
    sin_vincular = LineaPeticion(referencia_linea="2", cantidad=-1.0, precio=9.0,
                                 producto="MA9999", descripcion="PORTES",
                                 unidad="UD", partida="03.01")
    assert sin_vincular.a_dict() == {
        "referencia_linea": "2", "producto": "MA9999", "descripcion": "PORTES",
        "unidad": "UD", "cantidad": -1.0, "precio": 9.0, "partida": "03.01",
    }
    for prohibida in ("almacen", "naturaleza", "paride", "lineas_recibidas"):
        assert prohibida not in sin_vincular.a_dict()


def test_f053_modelos_peticion_cabecera_completa_sin_database_ni_commit():
    peticion = PeticionAlbaran(
        cod_obra="0404", cif_proveedor="B00000000", cod_contrato=None,
        referencia_externa="ALB-d1", su_referencia="A-1", usu="USU",
        fecha_albaran=20261001, empide=None,
        lineas=(LineaPeticion(referencia_linea="1", cantidad=1.0, precio=1.0, ctrpro_ide=7),),
    )
    cuerpo = peticion.a_dict()
    assert list(cuerpo) == [
        "cod_obra", "cif_proveedor", "cod_contrato", "referencia_externa",
        "su_referencia", "usu", "fecha_albaran", "empide", "lineas",
    ]
    assert cuerpo["cod_contrato"] is None and cuerpo["empide"] is None
    assert cuerpo["lineas"] == [{"referencia_linea": "1", "ctrpro_ide": 7,
                                 "cantidad": 1.0, "precio": 1.0}]


def test_f053_modelos_respuesta_solo_guarda_lo_de_r16():
    cuerpo = {
        "ok": True, "estado": "previsto", "con_ide": 9, "cod": "AC26/1",
        "avisos": [{"codigo": "cod_provisional", "mensaje": "m"}],
        "lineas": [{"referencia_linea": "1", "total": 10.0}],
        "totales": {"totdoc": 12.1},
        "cabecera": {"bancos": "NO"}, "filas": {"dca": {}}, "warnings": ["m"],
        "contrato": {}, "movimientos": [],
    }
    respuesta = RespuestaAlta.desde_cuerpo(cuerpo)
    assert respuesta.a_dict() == {
        "estado": "previsto", "con_ide": 9, "cod": "AC26/1",
        "avisos": [{"codigo": "cod_provisional", "mensaje": "m"}],
        "lineas": [{"referencia_linea": "1", "total": 10.0}],
        "totales": {"totdoc": 12.1},
    }


def test_f053_modelos_respuesta_tolerante_con_campos_ausentes():
    respuesta = RespuestaAlta.desde_cuerpo({"estado": "previsto"})
    assert respuesta.con_ide is None and respuesta.cod is None
    assert respuesta.avisos == () and respuesta.lineas == () and respuesta.totales == {}


def test_f053_modelos_error_alta_serializa():
    error = ErrorAlta(tipo=TipoFallo.RECHAZO, status=400, codigo="lineas_no_validas",
                      lineas=({"referencia_linea": "1", "codigo": "partida_no_encontrada"},),
                      mensaje="Hay líneas…")
    assert error.a_dict() == {
        "tipo": "rechazo", "status": 400, "codigo": "lineas_no_validas",
        "lineas": [{"referencia_linea": "1", "codigo": "partida_no_encontrada"}],
        "error": "Hay líneas…",
    }


def test_f053_modelos_alta_actual_a_resultado_conserva_y_cambia():
    actual = AltaActual(estado=EstadoAlta.REGISTRADO, modo="real", sigrid_con_ide=5,
                        sigrid_cod="AC26/5", motivos=(Motivo("registrado_distinto"),),
                        peticion={"a": 1})
    resultado = actual.a_resultado(adjunto_estado=AdjuntoEstado.COLGADO, sigrid_gra_ide=8)
    assert isinstance(resultado, ResultadoAlta)
    assert resultado.estado is EstadoAlta.REGISTRADO and resultado.sigrid_con_ide == 5
    assert resultado.sigrid_cod == "AC26/5" and resultado.peticion == {"a": 1}
    assert resultado.motivos == (Motivo("registrado_distinto"),)
    assert resultado.adjunto_estado is AdjuntoEstado.COLGADO and resultado.sigrid_gra_ide == 8


# ------------------------------------------------------------------ #
# Puertos
# ------------------------------------------------------------------ #
def _abstractos(clase) -> set[str]:
    return set(getattr(clase, "__abstractmethods__", set()))


def test_f053_modelos_puerto_del_repositorio():
    from domain.ports.alta_repository import AltaRepository

    assert issubclass(AltaRepository, ABC)
    assert _abstractos(AltaRepository) == {"reclamar", "leer_datos", "guardar", "leer_alta"}


def test_f053_modelos_puerto_de_sigrid_solo_cinco_operaciones():
    """R33: buscar albaranes, concepto y usuario (sql/read; el usuario, v8 R47),
    alta y adjunto."""
    from domain.ports.sigrid_alta_port import SigridAltaPort

    assert _abstractos(SigridAltaPort) == {
        "buscar_albaranes", "existe_concepto", "buscar_usuario", "alta_albaran",
        "adjuntar_pdf",
    }
    publicos = {n for n, _ in inspect.getmembers(SigridAltaPort) if not n.startswith("_")}
    assert publicos == _abstractos(SigridAltaPort)
    assert list(inspect.signature(SigridAltaPort.alta_albaran).parameters) == [
        "self", "peticion", "commit",
    ]


def test_f053_modelos_puerto_del_pdf():
    from domain.ports.pdf_port import PdfAlbaranPort, PdfNoDisponibleError

    assert _abstractos(PdfAlbaranPort) == {"descargar"}
    assert issubclass(PdfNoDisponibleError, Exception)


@pytest.mark.parametrize("clase", ["AltaRepository", "SigridAltaPort", "PdfAlbaranPort"])
def test_f053_modelos_los_puertos_no_se_instancian(clase):
    import domain.ports.alta_repository as r
    import domain.ports.pdf_port as p
    import domain.ports.sigrid_alta_port as s

    modulo = {"AltaRepository": r, "SigridAltaPort": s, "PdfAlbaranPort": p}[clase]
    with pytest.raises(TypeError):
        getattr(modulo, clase)()


def test_f053_r45_bloqueantes_de_sv9_son_los_de_comun():
    """sv3 (R45) y sv4 (R25) leen los bloqueantes de comun: los mismos que sv9."""
    from ruesma_comun.alta_sigrid import ESTADOS_ALTA_BLOQUEANTES

    from domain.models.alta_models import ESTADOS_BLOQUEANTES

    assert {e.value for e in ESTADOS_BLOQUEANTES} == set(ESTADOS_ALTA_BLOQUEANTES)
