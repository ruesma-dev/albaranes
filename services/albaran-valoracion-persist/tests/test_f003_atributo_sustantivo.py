# tests/test_f003_atributo_sustantivo.py
"""F-003 · Red determinista de atributo sustantivo (R11, R12, R13).

Un ELEMENTO BASE de 0,5 mm no es un ELEMENTO BASE de 0,6 mm por mucho
que las descripciones se parezcan al 95 %. Cuando la IA casa dos lineas
cuyas magnitudes del MISMO tipo tienen valores distintos, la red anula
el match: mejor una linea nueva SIN precio a revision que un precio
equivocado con apariencia de bueno.

Lo que NO puede hacer la red es disparar por formato: 0,5 = 0.5 = 0,50 y
D-300 = D300 son el mismo numero escrito de otra manera.

Sin red, BBDD ni LLM.
"""
from __future__ import annotations

import pytest

from application.services.atributo_sustantivo_guard import (
    extraer_tokens_dimension,
    sanear_matches_atributo_sustantivo,
)
from ayudas_f003 import (
    construir,
    construir_builder,
    envelope,
    linea_contexto,
    linea_contrato,
    linea_valorada,
)

PREFIJO = "atributo_sustantivo_mismatch:"


# ---------------------------------------------------------------------
# R11 · Tokens dimensionales (nucleo de la red)
# ---------------------------------------------------------------------


def _valores(texto: str, categoria: str) -> set:
    return {
        valor
        for cat, valor, _ in extraer_tokens_dimension(texto)
        if cat == categoria
    }


def test_f003_r11_lee_milimetros() -> None:
    assert _valores("ELEMENTO BASE 0,5 mm", "longitud")


def test_f003_r11_la_coma_y_el_punto_decimal_son_lo_mismo() -> None:
    assert extraer_tokens_dimension("0,5 mm") == extraer_tokens_dimension(
        "0.5 mm"
    )


def test_f003_r11_los_ceros_finales_no_cambian_el_numero() -> None:
    assert extraer_tokens_dimension("0,50 mm") == extraer_tokens_dimension(
        "0,5 mm"
    )


def test_f003_r11_distingue_espesores_distintos() -> None:
    assert extraer_tokens_dimension("0,5 mm") != extraer_tokens_dimension(
        "0,6 mm"
    )


def test_f003_r11_el_diametro_se_normaliza_escriba_como_escriba() -> None:
    referencia = extraer_tokens_dimension("TUBO D-300")
    assert extraer_tokens_dimension("TUBO D300") == referencia
    assert extraer_tokens_dimension("TUBO DN300") == referencia
    assert extraer_tokens_dimension("TUBO ø300") == referencia


def test_f003_r11_no_confunde_unidades_de_distinta_magnitud() -> None:
    """6 m3 y 6 kg no son el mismo atributo: categorias distintas."""
    volumen = extraer_tokens_dimension("CONTENEDOR 6 m3")
    masa = extraer_tokens_dimension("SACO 6 kg")

    assert volumen and masa
    assert volumen != masa


def test_f003_r11_un_texto_sin_magnitudes_no_da_tokens() -> None:
    assert extraer_tokens_dimension("BOLSA DE CUNAS") == set()
    assert extraer_tokens_dimension(None) == set()


def test_f003_r11_las_unidades_pegadas_al_numero_cuentan() -> None:
    assert extraer_tokens_dimension("CHAPA 12mm") == extraer_tokens_dimension(
        "CHAPA 12 mm"
    )


# ---------------------------------------------------------------------
# R11 · La red sobre los DTOs
# ---------------------------------------------------------------------


class _Dto:
    """Doble minimo de LineValuationDto para la red."""

    def __init__(self, **kwargs) -> None:
        self.merge_line_id = kwargs.get("merge_line_id", 1)
        self.line_kind = kwargs.get("line_kind", "from_albaran")
        self.matched_contrato_line_id = kwargs.get(
            "matched_contrato_line_id", 100
        )
        self.match_method = kwargs.get("match_method", "semantic")
        self.precio_unitario_contrato_db = kwargs.get(
            "precio_unitario_contrato_db", 10.0
        )
        self.precio_unitario_pdf_inferido = kwargs.get(
            "precio_unitario_pdf_inferido", 9.0
        )
        self.razon_corta = kwargs.get("razon_corta", "")


class _Ctx:
    def __init__(self, descripcion, contexto_linea=None) -> None:
        self.descripcion = descripcion
        self.contexto_linea = contexto_linea


class _Contrato:
    def __init__(self, descripcion) -> None:
        self.descripcion = descripcion


class _Familia:
    def __init__(self, tipo_familia) -> None:
        self.tipo_familia = tipo_familia


def _sanear(albaran_desc, contrato_desc, *, dto=None, contexto_linea=None):
    dto = dto or _Dto()
    motivos = sanear_matches_atributo_sustantivo(
        lineas=[(0, dto)],
        albaran_by_id={1: _Ctx(albaran_desc, contexto_linea)},
        contrato_by_id={100: _Contrato(contrato_desc)},
    )
    return dto, motivos


def test_f003_r11_espesores_distintos_anulan_el_match() -> None:
    dto, motivos = _sanear(
        "ELEMENTO BASE 0,5 mm", "ELEMENTO BASE 0,6 mm",
    )

    assert dto.matched_contrato_line_id is None
    assert dto.match_method == "no_match"
    assert motivos[1][0].startswith(PREFIJO)


def test_f003_r11_al_anular_tambien_se_van_los_dos_precios() -> None:
    """Dejar vivo el precio 1b reintroduciria el precio equivocado por
    la puerta de atras (D6)."""
    dto, _ = _sanear("ELEMENTO BASE 0,5 mm", "ELEMENTO BASE 0,6 mm")

    assert dto.precio_unitario_contrato_db is None
    assert dto.precio_unitario_pdf_inferido is None


def test_f003_r11_el_mismo_valor_con_otro_formato_no_anula() -> None:
    dto, motivos = _sanear("ELEMENTO BASE 0,50 mm", "ELEMENTO BASE 0.5 mm")

    assert dto.matched_contrato_line_id == 100
    assert motivos == {}


def test_f003_r11_d300_y_d_300_no_anulan() -> None:
    dto, motivos = _sanear("TUBO D-300 PVC", "TUBO D300 PVC")

    assert dto.matched_contrato_line_id == 100
    assert motivos == {}


def test_f003_r11_sin_magnitudes_en_un_lado_no_se_anula() -> None:
    """La red solo actua cuando AMBOS textos traen magnitudes del mismo
    tipo: si uno no dice nada, no hay contradiccion que detectar."""
    dto, motivos = _sanear("BOLSA DE CUNAS", "CUNAS 0,5 mm")

    assert dto.matched_contrato_line_id == 100
    assert motivos == {}


def test_f003_r11_magnitudes_de_distinto_tipo_no_se_comparan() -> None:
    dto, motivos = _sanear("CONTENEDOR 6 m3", "CONTENEDOR 500 kg")

    assert dto.matched_contrato_line_id == 100
    assert motivos == {}


def test_f003_r11_una_magnitud_compartida_y_otra_no_no_anula() -> None:
    """El contrato detalla mas que el albaran: mientras no se
    CONTRADIGAN en la misma magnitud, el match aguanta."""
    dto, motivos = _sanear("TUBO 300 mm", "TUBO 300 mm 6 kg")

    assert dto.matched_contrato_line_id == 100
    assert motivos == {}


def test_f003_r11_el_hormigon_esta_excluido() -> None:
    """El hormigon tiene su propia maquinaria posicional (designacion
    HA-25/B/20/XC2): la red generica lo estropearia."""
    dto, motivos = _sanear(
        "HA-25/B/20/XC2 20 mm",
        "HA-30/B/12/XC2 12 mm",
        contexto_linea=_Familia("hormigon"),
    )

    assert dto.matched_contrato_line_id == 100
    assert motivos == {}


def test_f003_r11_el_mortero_esta_excluido() -> None:
    dto, motivos = _sanear(
        "MORTERO 0,5 mm",
        "MORTERO 0,6 mm",
        contexto_linea=_Familia("mortero"),
    )

    assert dto.matched_contrato_line_id == 100
    assert motivos == {}


def test_f003_r11_las_sinteticas_estan_excluidas() -> None:
    dto, motivos = _sanear(
        "ELEMENTO BASE 0,5 mm",
        "ELEMENTO BASE 0,6 mm",
        dto=_Dto(line_kind="synthetic_modifier", merge_line_id=None),
    )

    assert dto.matched_contrato_line_id == 100
    assert motivos == {}


def test_f003_r11_una_linea_sin_match_no_se_toca() -> None:
    dto, motivos = _sanear(
        "ELEMENTO BASE 0,5 mm",
        "ELEMENTO BASE 0,6 mm",
        dto=_Dto(matched_contrato_line_id=None, match_method="no_match"),
    )

    assert motivos == {}


def test_f003_r11_el_motivo_lleva_los_dos_valores() -> None:
    _, motivos = _sanear("ELEMENTO BASE 0,5 mm", "ELEMENTO BASE 0,6 mm")

    motivo = motivos[1][0]
    assert "0.5" in motivo
    assert "0.6" in motivo


# ---------------------------------------------------------------------
# R11/R12 · La red integrada en el builder
# ---------------------------------------------------------------------


def _sobre_espesores(
    albaran_desc: str, contrato_desc: str, *, partida: str | None = "01.01",
):
    return envelope(
        lineas_data=[
            linea_valorada(
                merge_line_id=1,
                matched_contrato_line_id=100,
                match_method="semantic",
                precio_unitario_contrato_db=99.0,
            )
        ],
        lineas_albaran=[
            linea_contexto(
                merge_line_id=1,
                descripcion=albaran_desc,
                cantidad=2.0,
                precio_unitario_albaran=None,
                importe_albaran=None,
                codigo_partida_albaran=partida,
            )
        ],
        lineas_contrato=[
            linea_contrato(contrato_line_id=100, descripcion=contrato_desc,
                           precio_unitario=99.0),
        ],
    )


def test_f003_r12_la_linea_anulada_no_hereda_el_precio() -> None:
    _, records = construir(
        construir_builder(),
        _sobre_espesores("ELEMENTO BASE 0,5 mm", "ELEMENTO BASE 0,6 mm"),
    )

    record = records[0]
    assert record.precio_unitario_final is None
    assert record.precio_unitario_contrato_db is None
    assert record.precio_unitario_pdf_inferido is None


def test_f003_r12_la_linea_anulada_cae_a_derivada_y_a_revision() -> None:
    """Con partida impresa en el albaran, el mecanismo existente crea la
    linea derivada en ESA partida (origen 'no_ia_match'), sin precio."""
    _, records = construir(
        construir_builder(),
        _sobre_espesores("ELEMENTO BASE 0,5 mm", "ELEMENTO BASE 0,6 mm"),
    )

    record = records[0]
    assert record.match_method == "no_match"
    assert record.review_required is True
    derivada = record.derived_contrato_line_record
    assert derivada is not None
    assert derivada.origen == "no_ia_match"
    assert derivada.precio_unitario is None


def test_f003_r12_sin_partida_la_linea_anulada_cae_a_nueva_no_match() -> None:
    """Sin partida en el albaran no hay donde derivar: entra el fallback
    de LINEA NUEVA, tambien sin precio y a revision."""
    _, records = construir(
        construir_builder(),
        _sobre_espesores(
            "ELEMENTO BASE 0,5 mm", "ELEMENTO BASE 0,6 mm", partida=None,
        ),
    )

    record = records[0]
    assert record.match_method == "no_match"
    assert record.review_required is True
    derivada = record.derived_contrato_line_record
    assert derivada is not None
    assert derivada.origen == "nueva_no_match"
    assert derivada.precio_unitario is None


def test_f003_r12_el_motivo_viaja_al_record() -> None:
    _, records = construir(
        construir_builder(),
        _sobre_espesores("ELEMENTO BASE 0,5 mm", "ELEMENTO BASE 0,6 mm"),
    )

    assert any(
        motivo.startswith(PREFIJO) for motivo in records[0].review_reasons
    )


def test_f003_r11_un_match_legitimo_sobrevive_al_builder() -> None:
    _, records = construir(
        construir_builder(),
        _sobre_espesores("ELEMENTO BASE 0,50 mm", "ELEMENTO BASE 0.5 mm"),
    )

    record = records[0]
    assert record.matched_contrato_line_id == 100
    assert record.precio_unitario_final == pytest.approx(99.0)
    assert not [
        motivo
        for motivo in record.review_reasons
        if motivo.startswith(PREFIJO)
    ]


def test_f003_r13_la_red_se_puede_apagar() -> None:
    _, records = construir(
        construir_builder(red_atributo_sustantivo_enabled=False),
        _sobre_espesores("ELEMENTO BASE 0,5 mm", "ELEMENTO BASE 0,6 mm"),
    )

    record = records[0]
    assert record.matched_contrato_line_id == 100
    assert not [
        motivo
        for motivo in record.review_reasons
        if motivo.startswith(PREFIJO)
    ]
