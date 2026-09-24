# tests/test_f048_r32_r34_vista_avisos.py
"""F-048 · R32–R34 (plantilla): la ficha pinta el aviso de la obra.

Jinja2 sobre la plantilla REAL (``templates/document_detail.html``):

- Discrepancia ⇒ aviso con el campo, el codigo del correo y el del papel.
- ``correo_ambiguo``, ``correo_confirma_papel`` y ``correo_fuera_de_lista``
  ⇒ aviso con los candidatos del correo y el motivo.
- Estilo ``warning`` SOLO si el documento trae un motivo de
  ``MOTIVOS_REVISION_ORIGEN``; ``correo_confirma_papel`` y
  ``correo_fuera_de_lista`` son informativos (``info``).
- Los dos motivos nuevos salen en el bloque «Motivos de revision» que ya
  existe (F-036 R23), sin tocarlo.
- Sin bloque, o con un JSON roto, la ficha se pinta igual que hoy.

Sin red, sin BBDD y sin LLM. Codigos inventados.
"""
from __future__ import annotations

import json
import re

import pytest
from ruesma_comun.contratos.origen_datos import (
    MOTIVO_REVISION_OBRA_CORREO_AMBIGUA,
    MOTIVO_REVISION_OBRA_CORREO_DISTINTA,
)


def _origen(motivo: str, *, final="0945", correo=None, candidatos=(), papel="0945", discrepancia=False,
            fuente="papel", validada=True) -> dict:
    return {
        "version": 1, "correo_presente": True, "correo_sha256": "f" * 64, "correo_truncado": False,
        "evidencia": "la 945",
        "obra": {"fuente": fuente, "motivo": motivo, "valor_final": final, "valor_correo": correo,
                 "candidatos_correo": list(candidatos), "valor_papel": papel,
                 "discrepancia": discrepancia, "validada": validada},
    }


DISCREPANCIA = _origen("correo_unico", correo="0945", candidatos=["0945"], papel="0937", discrepancia=True,
                       fuente="correo")
AMBIGUO = _origen("correo_ambiguo", final="0937", candidatos=["0945", "0320"], papel="0937")
CONFIRMA = _origen("correo_confirma_papel", candidatos=["0945", "0320"], papel="0945")
FUERA = _origen("correo_fuera_de_lista", candidatos=["PED-555"], validada=False)


def _raw(origen: dict | None) -> str:
    data: dict = {"cabecera": {"obra_codigo": "0945"}, "lineas": []}
    if origen is not None:
        data["origen_datos"] = origen
    return json.dumps({"meta": {}, "data": data}, ensure_ascii=False)


def _html(render_detalle, documento_detalle, raw: str | None, motivos=None) -> str:
    documento = documento_detalle(motivos_documento=motivos).model_copy(update={"raw_extraction_json": raw})
    return render_detalle(documento)


def _bloque_origen(html: str) -> str | None:
    """El ``<div>`` del aviso de la obra, o ``None`` si no se pinto."""
    encontrado = re.search(r'<div class="alert [^"]*origen-datos[^"]*">.*?</div>', html, re.DOTALL)
    return encontrado.group(0) if encontrado else None


# ---------------------------------------------------------------- #
# R32 · discrepancia
# ---------------------------------------------------------------- #
def test_f048_r32_la_discrepancia_ensena_campo_correo_y_papel_como_advertencia(render_detalle, documento_detalle):
    html = _html(render_detalle, documento_detalle, _raw(DISCREPANCIA), [MOTIVO_REVISION_OBRA_CORREO_DISTINTA])
    bloque = _bloque_origen(html)

    assert bloque is not None
    assert "Obra" in bloque
    assert "el correo dice 0945 y el papel dice 0937" in bloque
    assert "warning" in bloque and "origen-duda" in bloque


# ---------------------------------------------------------------- #
# R33 · candidatos y motivo
# ---------------------------------------------------------------- #
@pytest.mark.parametrize(
    ("origen", "motivo", "candidatos"),
    [
        (AMBIGUO, "correo_ambiguo", ["0945", "0320"]),
        (CONFIRMA, "correo_confirma_papel", ["0945", "0320"]),
        (FUERA, "correo_fuera_de_lista", ["PED-555"]),
    ],
    ids=["ambiguo", "confirma_papel", "fuera_de_lista"],
)
def test_f048_r33_el_aviso_ensena_los_candidatos_y_el_motivo(render_detalle, documento_detalle, origen, motivo,
                                                             candidatos):
    bloque = _bloque_origen(_html(render_detalle, documento_detalle, _raw(origen)))

    assert bloque is not None
    assert f"<code>{motivo}</code>" in bloque
    for candidato in candidatos:
        assert candidato in bloque


def test_f048_cr_d3_confirma_papel_pinta_la_lectura_del_papel_y_la_de_la_lista(render_detalle, documento_detalle):
    """Menor 3 de la review del bloque D: ``945`` en el papel, ``0945`` en la cabecera."""
    confirma = _origen("correo_confirma_papel", candidatos=["0945", "0320"], papel="945")

    bloque = _bloque_origen(_html(render_detalle, documento_detalle, _raw(confirma)))

    assert "(el papel dice 945; en la lista de obras, 0945). Se ha usado 0945." in bloque


def test_f048_cr_d4_el_revisor_cambio_la_obra_se_pinta_distinto(render_detalle, documento_detalle):
    """Aviso C de la review del bloque D, opción (b): sigue siendo advertencia
    (el motivo sellado no se toca, R34/R35) pero dice que el revisor la cambió."""
    documento = documento_detalle(motivos_documento=[MOTIVO_REVISION_OBRA_CORREO_DISTINTA]).model_copy(
        update={"raw_extraction_json": _raw(DISCREPANCIA), "obra_codigo": "0999"}
    )

    bloque = _bloque_origen(render_detalle(documento))

    assert 'class="alert warning origen-duda origen-datos obra-cambiada"' in bloque
    assert "el revisor cambió la obra a 0999; al extraer se fijó 0945, la que decía el correo." in bloque
    assert "Al extraer, el correo dice 0945 y el papel dice 0937." in bloque


def test_f048_cr_d4_sin_cambio_no_lleva_la_marca(render_detalle, documento_detalle):
    documento = documento_detalle(motivos_documento=[MOTIVO_REVISION_OBRA_CORREO_DISTINTA]).model_copy(
        update={"raw_extraction_json": _raw(DISCREPANCIA), "obra_codigo": "0945"}
    )

    bloque = _bloque_origen(render_detalle(documento))

    assert 'class="alert warning origen-duda origen-datos"' in bloque
    assert "revisor" not in bloque


@pytest.mark.parametrize("origen", [CONFIRMA, FUERA], ids=["confirma_papel", "fuera_de_lista"])
def test_f048_r33_confirma_papel_y_fuera_de_lista_son_informativos(render_detalle, documento_detalle, origen):
    bloque = _bloque_origen(_html(render_detalle, documento_detalle, _raw(origen)))

    assert 'class="alert info origen-datos"' in bloque
    assert "warning" not in bloque


# ---------------------------------------------------------------- #
# R34 · advertencia y bloque de motivos
# ---------------------------------------------------------------- #
def test_f048_r34_el_ambiguo_con_su_motivo_es_advertencia(render_detalle, documento_detalle):
    bloque = _bloque_origen(
        _html(render_detalle, documento_detalle, _raw(AMBIGUO), [MOTIVO_REVISION_OBRA_CORREO_AMBIGUA])
    )

    assert 'class="alert warning origen-duda origen-datos"' in bloque


def test_f048_r34_sin_motivo_sellado_el_mismo_aviso_es_informativo(render_detalle, documento_detalle):
    """El estilo lo decide el motivo de sv3, no el bloque."""
    bloque = _bloque_origen(_html(render_detalle, documento_detalle, _raw(DISCREPANCIA), ["single_provider_openai"]))

    assert 'class="alert info origen-datos"' in bloque


def test_f048_r34_los_motivos_nuevos_salen_en_el_bloque_de_motivos(render_detalle, documento_detalle):
    motivos = [MOTIVO_REVISION_OBRA_CORREO_DISTINTA, MOTIVO_REVISION_OBRA_CORREO_AMBIGUA]
    html = _html(render_detalle, documento_detalle, _raw(DISCREPANCIA), motivos)

    assert "Motivos de revisión" in html
    for motivo in motivos:
        assert f"<li><code>{motivo}</code></li>" in html


# ---------------------------------------------------------------- #
# R35 · la ficha abre igual sin bloque
# ---------------------------------------------------------------- #
@pytest.mark.parametrize("raw", [None, "{ roto", _raw(None), _raw(_origen("sin_correo"))],
                         ids=["sin_json", "json_roto", "sin_bloque", "sin_correo"])
def test_f048_r35_sin_aviso_la_ficha_es_la_de_hoy(render_detalle, documento_detalle, raw):
    html = _html(render_detalle, documento_detalle, raw)
    hoy = render_detalle(documento_detalle())

    assert _bloque_origen(html) is None
    assert html == hoy
