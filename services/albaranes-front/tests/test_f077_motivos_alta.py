# tests/test_f077_motivos_alta.py
"""F-077 · D · motivos del alta: siempre visibles y legibles.

Caso real (documento ``86c13097-…``): ``no_admitido`` con
``motivos_json = [{"codigo": "falta_descripcion", "detalle": "",
"referencia_linea": "386"}]`` y sin petición ni respuesta (sv9 lo rechazó en
local). El panel decía «No admitido» sin ninguna razón.

- R24, R25: los motivos de línea que no casan con ninguna fila de la tabla del
  panel salen en la lista como «Línea N: …», con N la posición de la línea
  valorada en la tabla de la ficha («Línea (ref. X)» si no está).
- R26: todo motivo con su texto legible (+ « · detalle»), el código en el
  ``title``; ``http_<NNN>``; desconocido tal cual.
- R27: la tabla cubre todo código que sv9 escribe hoy (lee sus fuentes como
  texto, sin importarlas).
- R28: los de una fila de la tabla, solo en su fila; en ``en_curso`` o
  ``sin_respuesta``, ninguno.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

from domain.models import alta_sigrid_models as modelos
from domain.models.alta_sigrid_models import AltaSigridVista, ConfigAltaSigrid
from domain.models.review_models import ConciliacionDisplay, DisplayLine

DOC_REAL = "86c13097-98f8-4e4b-91af-6a378c28d9cf"
MOTIVO_REAL = {"codigo": "falta_descripcion", "detalle": "", "referencia_linea": "386"}
SV9 = Path(__file__).resolve().parents[2] / "albaranes-alta-sigrid"


def _caso_real(**campos) -> AltaSigridVista:
    base = {"estado": "no_admitido", "modo": "simulacion", "motivos": [MOTIVO_REAL],
            "peticion": None, "respuesta": None, "approved_at_utc": "2026-10-16T10:00:00+00:00"}
    base.update(campos)
    return AltaSigridVista(**base)


def _fila(vid, *, concilia=True, line_kind="from_albaran"):
    return DisplayLine(
        line_kind=line_kind, merge_line_id=None, valuation_line_id=vid, line_index=1,
        is_valued=True, concilia=ConciliacionDisplay(kind="assigned") if concilia else None,
    )


# =================================================================== #
# R26 · texto legible
# =================================================================== #
@pytest.mark.parametrize("codigo, texto", [
    ("falta_descripcion", "La línea no tiene descripción"),
    ("fecha_no_plausible", "La fecha del albarán no es plausible (futura o demasiado antigua)"),
    ("lineas_no_validas", "Sigrid rechazó alguna línea"),
    ("partida_no_encontrada", "La partida no existe en la obra en Sigrid"),
    ("http_503", "sigrid-api respondió con HTTP 503"),
    ("http_404", "sigrid-api respondió con HTTP 404"),
    ("http_5031", "http_5031"),                     # no es un HTTP de tres cifras
    ("codigo_que_no_existe", "codigo_que_no_existe"),  # desconocido: tal cual
    ("", ""),
])
def test_f077_r26_texto_motivo_alta(codigo, texto):
    assert modelos.texto_motivo_alta(codigo) == texto


def test_f077_r26_motivos_de_documento_y_de_fila_llevan_texto():
    alta = AltaSigridVista(
        estado="revisar",
        motivos=[{"codigo": "fecha_no_plausible", "detalle": "2025-01-01"},
                 {"codigo": "importe_distinto", "detalle": "120 frente a 118", "referencia_linea": "900"}],
        peticion={"lineas": [{"referencia_linea": "900", "producto": "MA9999"}]},
    )
    assert alta.motivos_documento == [{"codigo": "fecha_no_plausible", "detalle": "2025-01-01",
                                       "texto": "La fecha del albarán no es plausible (futura o "
                                                "demasiado antigua)"}]
    (linea,) = alta.lineas
    assert linea["motivos"] == [{"codigo": "importe_distinto", "detalle": "120 frente a 118",
                                 "referencia_linea": "900",
                                 "texto": "El importe no coincide con el que calcula Sigrid"}]
    assert alta.motivos_linea_sueltos == []


# =================================================================== #
# R24, R25 · motivos de línea sin fila en la tabla del panel
# =================================================================== #
def test_f077_r24_caso_real_motivo_suelto():
    alta = _caso_real()
    assert alta.motivos_documento == [] and alta.lineas == []
    assert alta.motivos_linea_sueltos == [{**MOTIVO_REAL, "texto": "La línea no tiene descripción"}]


def test_f077_r25_posiciones_filas_ficha():
    from domain.models.review_models import posiciones_filas_ficha

    filas = [_fila(379), _fila(None, concilia=False), _fila(385), _fila(390, concilia=False),
             _fila(386, line_kind="manual"), _fila(None)]
    assert posiciones_filas_ficha(filas) == {379: 1, 385: 2, 386: 3}


def test_f077_r25_motivos_linea_vista():
    from domain.services.alta_sigrid import motivos_linea_vista

    alta = _caso_real()
    assert motivos_linea_vista(alta, {379: 1, 385: 2, 386: 3}) == [
        {"linea": "Línea 3", "texto": "La línea no tiene descripción", "detalle": "",
         "codigo": "falta_descripcion"}]
    assert motivos_linea_vista(alta, {379: 1}) == [
        {"linea": "Línea (ref. 386)", "texto": "La línea no tiene descripción", "detalle": "",
         "codigo": "falta_descripcion"}]
    raro = _caso_real(motivos=[{"codigo": "http_503", "detalle": "x", "referencia_linea": "ALB-9"}])
    assert motivos_linea_vista(raro, {9: 1})[0]["linea"] == "Línea (ref. ALB-9)"
    assert motivos_linea_vista(None, {386: 1}) == []


def test_f077_r25_get_document_calcula_los_motivos_sueltos(documento_detalle):
    from application.services.review_service import ReviewService

    documento = documento_detalle(display=[_fila(379), _fila(385), _fila(386, line_kind="manual")])
    documento.approved = True
    alta = _caso_real()

    class _Repo:
        def get_document_detail(self, document_id, *, view_mode):
            return documento

        def leer_alta_sigrid(self, document_id):
            return alta

        def estado_aprobacion(self, document_id):
            return {"approved": True, "approved_at_utc": alta.approved_at_utc, "is_active": True}

        def lineas_producto_sigrid(self, document_id):
            return []

    from datetime import UTC, datetime

    ficha = ReviewService(_Repo(), "r", None, ConfigAltaSigrid(desde=datetime(2026, 10, 1, tzinfo=UTC))
                          ).get_document(DOC_REAL)
    assert ficha.alta_motivos_linea == [{"linea": "Línea 3", "texto": "La línea no tiene descripción",
                                         "detalle": "", "codigo": "falta_descripcion"}]


# =================================================================== #
# R24, R26, R28 · la plantilla del panel
# =================================================================== #
def _panel(html):
    encontrado = re.search(r'<section[^>]*id="alta-sigrid".*?</section>', html, re.DOTALL)
    return encontrado.group(0) if encontrado else None


def _ficha(documento, alta, fase="resultado", sueltos=()):
    documento.approved = True
    documento.alta_sigrid_activa = True
    documento.alta_sigrid = alta
    documento.alta_fase = fase
    documento.alta_motivos_linea = list(sueltos)
    return documento


_SUELTO = {"linea": "Línea 3", "texto": "La línea no tiene descripción", "detalle": "",
           "codigo": "falta_descripcion"}


def test_f077_r24_caso_real_en_el_panel(render_detalle, documento_detalle):
    panel = _panel(render_detalle(_ficha(documento_detalle(), _caso_real(), sueltos=[_SUELTO])))
    lista = re.search(r'<ul class="alta-sigrid-motivos">(.*?)</ul>', panel, re.DOTALL).group(1)
    assert re.findall(r"<li[^>]*>(.*?)</li>", lista, re.DOTALL) == ["Línea 3: La línea no tiene descripción"]
    assert '<li title="falta_descripcion">' in lista
    assert "Error en el alta en Sigrid: No admitido" in panel


def test_f077_r24_sueltos_despues_de_los_del_documento(render_detalle, documento_detalle):
    alta = _caso_real(motivos=[MOTIVO_REAL, {"codigo": "fecha_no_plausible", "detalle": "2025-01-01"}])
    suelto = {**_SUELTO, "linea": "Línea (ref. 386)"}
    panel = _panel(render_detalle(_ficha(documento_detalle(), alta, sueltos=[suelto])))
    lista = re.search(r'<ul class="alta-sigrid-motivos">(.*?)</ul>', panel, re.DOTALL).group(1)
    assert re.findall(r"<li[^>]*>(.*?)</li>", lista, re.DOTALL) == [
        "La fecha del albarán no es plausible (futura o demasiado antigua) · 2025-01-01",
        "Línea (ref. 386): La línea no tiene descripción",
    ]


def test_f077_r26_motivo_de_documento_texto_y_codigo_en_title(render_detalle, documento_detalle):
    alta = AltaSigridVista(estado="no_admitido", motivos=[{"codigo": "fecha_no_plausible",
                                                           "detalle": "2025-01-01"}])
    panel = _panel(render_detalle(_ficha(documento_detalle(), alta)))
    assert ('<li title="fecha_no_plausible">La fecha del albarán no es plausible (futura o demasiado '
            'antigua) · 2025-01-01</li>') in panel
    assert "<code>fecha_no_plausible</code>" not in panel


@pytest.mark.parametrize("codigo, texto", [("codigo_raro", "codigo_raro"),
                                           ("http_503", "sigrid-api respondió con HTTP 503")])
def test_f077_r26_desconocido_y_http(render_detalle, documento_detalle, codigo, texto):
    alta = AltaSigridVista(estado="error", motivos=[{"codigo": codigo, "detalle": ""}])
    panel = _panel(render_detalle(_ficha(documento_detalle(), alta)))
    assert f'<li title="{codigo}">{texto}</li>' in panel


def test_f077_r28_motivo_de_una_fila_de_la_peticion_solo_en_su_fila(render_detalle, documento_detalle):
    alta = AltaSigridVista(
        estado="revisar",
        motivos=[{"codigo": "importe_distinto", "detalle": "120 frente a 118", "referencia_linea": "900"}],
        peticion={"lineas": [{"referencia_linea": "900", "producto": "MA9999", "descripcion": "ARIDO"}]},
    )
    panel = _panel(render_detalle(_ficha(documento_detalle(), alta, sueltos=[])))
    assert "alta-sigrid-motivos" not in panel
    tabla = re.search(r'<table class="table alta-sigrid-lineas">.*?</table>', panel, re.DOTALL).group(0)
    assert ('<div title="importe_distinto">El importe no coincide con el que calcula Sigrid · 120 frente '
            'a 118</div>') in tabla
    assert panel.count("El importe no coincide") == 1


@pytest.mark.parametrize("fase", ["en_curso", "sin_respuesta"])
def test_f077_r28_en_curso_o_sin_respuesta_ningun_motivo(render_detalle, documento_detalle, fase):
    panel = _panel(render_detalle(_ficha(documento_detalle(), _caso_real(), fase=fase, sueltos=[_SUELTO])))
    assert "La línea no tiene descripción" not in panel and "falta_descripcion" not in panel
    assert "alta-sigrid-motivos" not in panel


# =================================================================== #
# R27 · catálogo completo frente a las fuentes de sv9 (leídas como texto)
# =================================================================== #
def _fuente_sv9(nombre: str) -> str:
    (ruta,) = [r for r in SV9.rglob(nombre) if "tests" not in r.parts and ".venv" not in r.parts]
    return ruta.read_text(encoding="utf-8")


def _codigos_sv9() -> set[str]:
    codigos: set[str] = set()
    for nombre in ("validador_alta.py", "comparador_previa.py", "clasificador.py", "alta_sigrid_service.py"):
        fuente = _fuente_sv9(nombre)
        constantes = dict(re.findall(r'^([A-Z][A-Z0-9_]*)\s*=\s*"([a-z0-9_]+)"', fuente, re.MULTILINE))
        # Motivo("codigo", …), también partido en varias líneas.
        codigos |= set(re.findall(r'Motivo\(\s*"([a-z0-9_]+)"', fuente))
        # Motivo(CONSTANTE, …) => el valor de la constante del mismo fichero.
        for nombre_constante in re.findall(r"Motivo\(\s*([A-Z][A-Z0-9_]*)\s*,", fuente):
            codigos.add(constantes[nombre_constante])
        # Motivo(codigo_xxx, …) => los literales con los que se asigna esa variable.
        for variable in re.findall(r"Motivo\(\s*(codigo_[a-z_]+)\s*,", fuente):
            for asignacion in re.findall(rf"^\s*{variable}\s*=\s*(.+)$", fuente, re.MULTILINE):
                codigos |= set(re.findall(r'"([a-z0-9_]+)"', asignacion))
        # Los mapas de clasificador.py y sus CODIGO_* (códigos de sigrid-api).
        codigos |= set(re.findall(r'"([a-z0-9_]+)"\s*:\s*_(?:NO_ADMITIDO|REVISAR|ERROR)\b', fuente))
        codigos |= {v for k, v in constantes.items() if k.startswith("CODIGO_")}
    # TipoFallo (alta_models.py): el motivo de un fallo sin código ni HTTP.
    modelos_sv9 = _fuente_sv9("alta_models.py")
    bloque = modelos_sv9[modelos_sv9.index("class TipoFallo("):]
    bloque = bloque[:bloque.index("\nclass ", 1)]
    codigos |= set(re.findall(r'=\s*"([a-z0-9_]+)"', bloque))
    return codigos


def test_f077_r27_la_extraccion_ve_los_codigos_de_cada_fuente():
    codigos = _codigos_sv9()
    for esperado in ("falta_descripcion", "signo_incoherente", "linea_de_otro_contrato",  # validador
                     "lineas_distintas", "registrado_distinto", "partida_distinta",       # comparador
                     "obra_no_encontrada", "lineas_no_validas", "precio_negativo",        # clasificador
                     "excepcion", "alta_a_mano", "adjunto_no_colgado", "sigue_en_sigrid",  # servicio
                     "rechazo", "respuesta_invalida"):                                    # TipoFallo
        assert esperado in codigos, esperado


def test_f077_r27_todo_codigo_de_sv9_tiene_texto():
    sin_texto = sorted(_codigos_sv9() - set(modelos.TEXTOS_MOTIVO_ALTA))
    assert sin_texto == []


def test_f077_r27_ningun_texto_vacio_ni_igual_al_codigo():
    for codigo, texto in modelos.TEXTOS_MOTIVO_ALTA.items():
        assert texto.strip() and texto != codigo, codigo
