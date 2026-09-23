# tests/test_f048_r24_origen_datos.py
"""F-048 · R24 y R31 · el contrato ``origen_datos`` vive en ``ruesma_comun``.

- R24: ``origen_datos`` no contiene el cuerpo del correo: solo huella,
  ``truncado``, codigos y la frase de evidencia recortada a 160 caracteres.
  Del correo solo la OBRA (D8): no hay bloque ``partida``.
- R31: los nombres de los dos motivos de revision se definen UNA vez aqui
  (los importan sv3 y sv4).
- R18 · ``normalizar_codigo`` (D9 del design, «si, normaliza todo»):
  mayusculas, fuera todo lo que no sea alfanumerico y fuera los ceros a la
  izquierda; si no queda nada, no hay codigo (``None``).

Solo modelos y funciones puras: sin red ni BBDD.
"""
from __future__ import annotations

import pytest
from pydantic import ValidationError
from ruesma_comun.contratos import OrigenCampo, OrigenDatos
from ruesma_comun.contratos import origen_datos as od

CENTINELA = "CENTINELA-F048"


def _campo(**kw) -> OrigenCampo:
    base = {"fuente": od.FUENTE_PAPEL, "motivo": od.MOTIVO_SIN_CORREO}
    return OrigenCampo(**(base | kw))


def _origen(**kw) -> OrigenDatos:
    base = {"correo_presente": False, "obra": _campo()}
    return OrigenDatos(**(base | kw))


# ------------------------------------------------------------------ #
# R24 · que hay (y que no hay) en origen_datos
# ------------------------------------------------------------------ #
def test_f048_r24_origen_datos_declara_solo_huella_truncado_evidencia_y_obra():
    assert set(OrigenDatos.model_fields) == {
        "version", "correo_presente", "correo_sha256", "correo_truncado",
        "evidencia", "obra",
    }


def test_f048_r24_origen_campo_declara_fuente_motivo_valores_y_cruce():
    assert set(OrigenCampo.model_fields) == {
        "fuente", "motivo", "valor_final", "valor_correo", "candidatos_correo",
        "valor_papel", "discrepancia", "validada",
    }


def test_f048_r24_defectos():
    origen = _origen()
    assert origen.version == 1
    assert origen.correo_sha256 is None
    assert origen.correo_truncado is False
    assert origen.evidencia is None
    assert origen.obra.valor_final is None
    assert origen.obra.valor_correo is None
    assert origen.obra.valor_papel is None
    assert origen.obra.candidatos_correo == []
    assert origen.obra.discrepancia is False
    assert origen.obra.validada is None


def test_f048_r24_cuerpo_asunto_y_partida_se_descartan_al_validar():
    datos = {
        "correo_presente": True,
        "cuerpo": CENTINELA,
        "asunto": CENTINELA,
        "partida": {"fuente": "correo", "motivo": "correo_unico"},
        "obra": {"fuente": "correo", "motivo": "correo_unico", "cuerpo": CENTINELA},
    }
    volcado = OrigenDatos.model_validate(datos).model_dump_json()
    assert CENTINELA not in volcado
    assert "partida" not in volcado


def test_f048_r24_evidencia_recortada_a_160():
    assert od.MAX_EVIDENCIA == 160
    assert len(_origen(evidencia="x" * 500).evidencia) == 160
    assert _origen(evidencia="y" * 161).evidencia == "y" * 160


def test_f048_r24_evidencia_de_160_o_menos_queda_entera():
    assert _origen(evidencia="z" * 160).evidencia == "z" * 160
    assert _origen(evidencia="Obra 1234").evidencia == "Obra 1234"


def test_f048_r24_evidencia_normaliza_espacios_antes_de_recortar():
    texto = "Para   la\n\nobra\t1234 " + "w" * 200
    evidencia = _origen(evidencia=texto).evidencia
    assert evidencia.startswith("Para la obra 1234 w")
    assert len(evidencia) == 160


@pytest.mark.parametrize("vacia", [None, "", "   \n\t "])
def test_f048_r24_evidencia_vacia_es_none(vacia):
    assert _origen(evidencia=vacia).evidencia is None


def test_f048_r24_ida_y_vuelta_json():
    origen = _origen(
        correo_presente=True,
        correo_sha256="a" * 64,
        correo_truncado=True,
        evidencia="obra 1234",
        obra=_campo(
            fuente=od.FUENTE_CORREO, motivo=od.MOTIVO_CORREO_UNICO,
            valor_final="1234", valor_correo="1234", valor_papel="999",
            candidatos_correo=["1234"], discrepancia=True, validada=True,
        ),
    )
    assert OrigenDatos.model_validate_json(origen.model_dump_json()) == origen


def test_f048_r24_ignora_campos_futuros():
    datos = _origen().model_dump(mode="json") | {"campo_futuro": 1}
    assert OrigenDatos.model_validate(datos) == _origen()


def test_f048_r24_motivos_del_origen_son_los_siete():
    assert od.MOTIVOS == (
        "sin_correo",
        "ia_sin_lectura_correo",
        "correo_sin_dato",
        "correo_unico",
        "correo_confirma_papel",
        "correo_ambiguo",
        "correo_fuera_de_lista",
    )


@pytest.mark.parametrize("motivo", od.MOTIVOS)
def test_f048_r24_cada_motivo_valida(motivo):
    assert _campo(motivo=motivo).motivo == motivo


def test_f048_r24_motivo_desconocido_no_valida():
    with pytest.raises(ValidationError):
        _campo(motivo="lo_decidio_la_ia")


def test_f048_r24_fuente_solo_correo_o_papel():
    assert (od.FUENTE_CORREO, od.FUENTE_PAPEL) == ("correo", "papel")
    assert _campo(fuente="correo").fuente == "correo"
    with pytest.raises(ValidationError):
        _campo(fuente="ia")


def test_f048_r24_obra_es_obligatoria():
    with pytest.raises(ValidationError):
        OrigenDatos(correo_presente=False)


def test_f048_r24_hay_discrepancia_es_la_de_la_obra():
    assert _origen(obra=_campo(discrepancia=True)).hay_discrepancia is True
    assert _origen(obra=_campo(discrepancia=False)).hay_discrepancia is False
    assert "hay_discrepancia" not in _origen().model_dump()


# ------------------------------------------------------------------ #
# R31 · los nombres de los motivos de revision, una sola vez
# ------------------------------------------------------------------ #
def test_f048_r31_nombres_de_los_motivos_de_revision():
    assert od.MOTIVO_REVISION_OBRA_CORREO_DISTINTA == "obra_correo_distinta_papel"
    assert od.MOTIVO_REVISION_OBRA_CORREO_AMBIGUA == "obra_correo_ambigua"
    assert od.MOTIVOS_REVISION_ORIGEN == (
        "obra_correo_distinta_papel",
        "obra_correo_ambigua",
    )


def test_f048_r31_se_importan_desde_contratos():
    from ruesma_comun import contratos

    assert contratos.MOTIVOS_REVISION_ORIGEN is od.MOTIVOS_REVISION_ORIGEN
    assert contratos.OrigenDatos is od.OrigenDatos
    assert contratos.normalizar_codigo is od.normalizar_codigo


# ------------------------------------------------------------------ #
# R18 · normalizar_codigo (D9)
# ------------------------------------------------------------------ #
@pytest.mark.parametrize("codigo", ["0945", "945", "09-45", "09.45", " 0945 ", "09/45", "0 9 4 5"])
def test_f048_r18_normalizar_codigo_equivalentes_dan_lo_mismo(codigo):
    assert od.normalizar_codigo(codigo) == "945"


def test_f048_r18_normalizar_codigo_distintos_siguen_distintos():
    assert od.normalizar_codigo("0945") != od.normalizar_codigo("0946")
    assert od.normalizar_codigo("9045") == "9045"
    assert od.normalizar_codigo("0900") == "900"


def test_f048_r18_normalizar_codigo_pasa_a_mayusculas():
    assert od.normalizar_codigo("ab-12") == "AB12"
    assert od.normalizar_codigo("ab 12") == od.normalizar_codigo("AB12")


def test_f048_r18_normalizar_codigo_no_quita_palabras():
    """Extraer el codigo es trabajo de IA1: aqui solo se normaliza."""
    assert od.normalizar_codigo("obra 0945") == "OBRA0945"
    assert od.normalizar_codigo("obra 0945") != od.normalizar_codigo("0945")


def test_f048_r18_normalizar_codigo_solo_quita_ceros_de_la_izquierda():
    assert od.normalizar_codigo("0A012") == "A012"
    assert od.normalizar_codigo("_0_945_") == "945"


@pytest.mark.parametrize("vacio", [None, "", "   ", "000", "--", "0-0", ". / _"])
def test_f048_r18_normalizar_codigo_vacio_es_sin_codigo(vacio):
    assert od.normalizar_codigo(vacio) is None
