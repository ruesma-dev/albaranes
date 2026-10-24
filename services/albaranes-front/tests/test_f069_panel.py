# tests/test_f069_panel.py
"""F-069 · T12 · el panel del alta enseña el empleado y los Avisos de
resolución (R21–R24).

- R21: con petición guardada, «Empleado de Sigrid: N» junto al usuario; con
  ``empide`` nulo, «Empleado de Sigrid: el de defecto de sigrid-api».
- R22: cada Aviso de ``resolucion.avisos`` con su texto legible, como aviso:
  ni en la lista de motivos (error) ni en el bloqueo, y sin cambiar el color
  del panel; un código sin texto se enseña tal cual.
- R23: «(respaldo)» sale de ``resolucion.usu == "respaldo"``; sin
  ``resolucion`` (altas anteriores a F-069), la regla de hoy.
- R24: los textos y la clave coinciden con las constantes de sv9 (leídas como
  texto: sv4 no importa sv9, como en F-077); ``usuario_no_resuelto`` vale para
  el alta, no solo para el PDF.
Plantillas reales; Logins e ``ide`` ficticios.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest
from test_f053_t21_panel import _alta, _con_alta, _panel

from domain.models import alta_sigrid_models as modelos
from domain.models.alta_sigrid_models import AltaSigridVista

SV9 = Path(__file__).resolve().parents[2] / "albaranes-alta-sigrid"


def _resolucion(usu="correo", empide="correo", avisos=()):
    return {"usu": usu, "empide": empide, "avisos": list(avisos)}


def _peticion(*, usu="login1", empide=1000001, resolucion=None):
    peticion = {"usu": usu, "empide": empide, "lineas": []}
    if resolucion is not None:
        peticion["resolucion"] = resolucion
    return peticion


def _fragmento(panel, clase):
    encontrado = re.search(rf'class="{clase}"[^>]*>(.*?)</span>', panel, re.DOTALL)
    return None if encontrado is None else re.sub(r"\s+", " ", encontrado.group(1)).strip()


# ------------------------------------------------------------------ #
# R21 · empleado
# ------------------------------------------------------------------ #
@pytest.mark.parametrize("valor, esperado", [
    (1000001, 1000001), (None, None), ("1000001", None), (True, None), (0, 0),
])
def test_f069_r21_empide_de_la_peticion(valor, esperado):
    alta = AltaSigridVista(estado="simulado", peticion=_peticion(empide=valor))
    assert alta.empide == esperado


def test_f069_r21_sin_peticion_no_hay_empide():
    assert AltaSigridVista(estado="no_admitido", peticion=None).empide is None


def test_f069_r21_panel_empleado_junto_al_usuario(render_detalle, documento_detalle):
    alta = _alta(approved_by="login1@ruesma.es", peticion=_peticion(resolucion=_resolucion()))
    panel = _panel(render_detalle(_con_alta(documento_detalle(), alta)))
    assert _fragmento(panel, "alta-sigrid-empide") == "Empleado de Sigrid: <code>1000001</code>"
    assert panel.index("alta-sigrid-usu") < panel.index("alta-sigrid-empide")


def test_f069_r21_panel_empleado_nulo(render_detalle, documento_detalle):
    alta = _alta(approved_by="login1@ruesma.es", peticion=_peticion(empide=None))
    panel = _panel(render_detalle(_con_alta(documento_detalle(), alta)))
    assert _fragmento(panel, "alta-sigrid-empide") == (
        "Empleado de Sigrid: el de defecto de sigrid-api")


def test_f069_r21_panel_sin_peticion_no_dice_empleado(render_detalle, documento_detalle):
    alta = _alta("no_admitido", peticion=None, approved_by="login1@ruesma.es")
    panel = _panel(render_detalle(_con_alta(documento_detalle(), alta)))
    assert "Empleado de Sigrid" not in panel


# ------------------------------------------------------------------ #
# R22 · avisos de resolución
# ------------------------------------------------------------------ #
AVISOS = [
    {"codigo": "empleado_correo_ambiguo", "detalle": "2 empleados de alta con el correo"},
    {"codigo": "defecto_sigrid_api", "detalle": ""},
]


def test_f069_r22_avisos_con_texto_y_desconocido_tal_cual():
    alta = AltaSigridVista(estado="simulado", peticion=_peticion(resolucion=_resolucion(
        avisos=[*AVISOS, {"codigo": "codigo_nuevo", "detalle": "x"}])))
    assert alta.avisos_resolucion == [
        {"codigo": "empleado_correo_ambiguo",
         "texto": modelos.TEXTOS_AVISO_RESOLUCION["empleado_correo_ambiguo"],
         "detalle": "2 empleados de alta con el correo"},
        {"codigo": "defecto_sigrid_api",
         "texto": modelos.TEXTOS_AVISO_RESOLUCION["defecto_sigrid_api"], "detalle": ""},
        {"codigo": "codigo_nuevo", "texto": "codigo_nuevo", "detalle": "x"},
    ]


@pytest.mark.parametrize("peticion", [
    None, {}, _peticion(), _peticion(resolucion=_resolucion()),
    _peticion(resolucion={"usu": "correo"}), _peticion(resolucion="roto"),
    _peticion(resolucion={"avisos": "roto"}), _peticion(resolucion={"avisos": ["roto", 3]}),
])
def test_f069_r22_sin_avisos_lista_vacia(peticion):
    assert AltaSigridVista(estado="simulado", peticion=peticion).avisos_resolucion == []


def test_f069_r22_panel_avisos_como_aviso_sin_bloquear(render_detalle, documento_detalle):
    alta = _alta(approved_by="login1@ruesma.es", motivos=[], peticion=_peticion(
        empide=None, resolucion=_resolucion(empide="defecto_sigrid_api", avisos=AVISOS)))
    panel = _panel(render_detalle(_con_alta(documento_detalle(), alta)))
    bloque = re.search(r'<ul class="alta-sigrid-avisos alta-sigrid-avisos-resolucion">(.*?)</ul>',
                       panel, re.DOTALL).group(1)
    textos = re.findall(r"<li[^>]*>(.*?)</li>", bloque, re.DOTALL)
    assert textos == [
        modelos.TEXTOS_AVISO_RESOLUCION["empleado_correo_ambiguo"]
        + " · 2 empleados de alta con el correo",
        modelos.TEXTOS_AVISO_RESOLUCION["defecto_sigrid_api"],
    ]
    assert '<li title="empleado_correo_ambiguo">' in bloque
    # Aviso, no error ni bloqueo: el panel sigue en «info» y no hay motivos.
    assert re.search(r'<section class="alert alta-sigrid info"', panel)
    assert "alta-sigrid-motivos" not in panel and "alta-sigrid-bloqueo" not in panel


def test_f069_r22_panel_sin_avisos_no_pinta_el_bloque(render_detalle, documento_detalle):
    alta = _alta(peticion=_peticion(resolucion=_resolucion()))
    panel = _panel(render_detalle(_con_alta(documento_detalle(), alta)))
    assert "alta-sigrid-avisos-resolucion" not in panel


def test_f069_r22_en_un_error_los_avisos_no_se_mezclan_con_los_motivos(render_detalle,
                                                                         documento_detalle):
    alta = _alta("revisar", peticion={**_peticion(resolucion=_resolucion(avisos=AVISOS)),
                                      "lineas": []})
    panel = _panel(render_detalle(_con_alta(documento_detalle(), alta)))
    motivos = re.search(r'<ul class="alta-sigrid-motivos">(.*?)</ul>', panel, re.DOTALL).group(1)
    assert "empleado_correo_ambiguo" not in motivos
    assert "alta-sigrid-avisos-resolucion" in panel


# ------------------------------------------------------------------ #
# R23 · respaldo
# ------------------------------------------------------------------ #
@pytest.mark.parametrize("approved_by, usu, origen, respaldo", [
    ("login1@ruesma.es", "login1", "respaldo", True),     # manda la resolucion
    ("login1@ruesma.es", "login1b", "lista", False),      # la Lista no es respaldo
    ("reviewer", "pgris", "correo", False),
    ("login1@ruesma.es", "pgris", "respaldo", True),
])
def test_f069_r23_respaldo_de_la_resolucion(approved_by, usu, origen, respaldo):
    alta = AltaSigridVista(estado="simulado", approved_by=approved_by,
                           peticion=_peticion(usu=usu, resolucion=_resolucion(usu=origen)))
    assert alta.usu_respaldo is respaldo


@pytest.mark.parametrize("resolucion", [None, {}, {"usu": None}, {"usu": 3}, "roto"])
def test_f069_r23_sin_resolucion_la_regla_de_hoy(resolucion):
    peticion = _peticion(usu="login1b")
    if resolucion is not None:
        peticion["resolucion"] = resolucion
    alta = AltaSigridVista(estado="simulado", approved_by="login1@ruesma.es", peticion=peticion)
    assert alta.usu_respaldo is True   # login1b no es la parte local
    peticion["usu"] = "LOGIN1"
    assert AltaSigridVista(estado="simulado", approved_by="login1@ruesma.es",
                           peticion=peticion).usu_respaldo is False


def test_f069_r23_panel_la_lista_no_sale_como_respaldo(render_detalle, documento_detalle):
    alta = _alta(approved_by="login1@ruesma.es",
                 peticion=_peticion(usu="login1b", resolucion=_resolucion(usu="lista")))
    panel = _panel(render_detalle(_con_alta(documento_detalle(), alta)))
    assert _fragmento(panel, "alta-sigrid-usu") == "Usuario de Sigrid: <code>login1b</code>"


# ------------------------------------------------------------------ #
# R24 · constantes contrastadas con sv9 (como texto)
# ------------------------------------------------------------------ #
def _fuente_sv9(nombre: str) -> str:
    (ruta,) = [r for r in SV9.rglob(nombre) if "tests" not in r.parts and ".venv" not in r.parts]
    return ruta.read_text(encoding="utf-8")


def test_f069_r24_codigos_de_aviso_iguales_a_los_de_sv9():
    fuente = _fuente_sv9("usuario_sigrid.py")
    codigos = set(re.findall(r'^AVISO_[A-Z_]+\s*=\s*"([a-z0-9_]+)"', fuente, re.MULTILINE))
    assert len(codigos) == 8
    assert set(modelos.TEXTOS_AVISO_RESOLUCION) == codigos
    assert all(texto.strip() for texto in modelos.TEXTOS_AVISO_RESOLUCION.values())


def test_f069_r24_clave_y_origen_respaldo_iguales_a_los_de_sv9():
    fuente = _fuente_sv9("alta_models.py")
    (clave,) = re.findall(r'^CLAVE_RESOLUCION\s*=\s*"([a-z_]+)"', fuente, re.MULTILINE)
    assert modelos.CLAVE_RESOLUCION == clave == "resolucion"
    bloque = fuente[fuente.index("class OrigenUsuario("):]
    bloque = bloque[:bloque.index("\nclass ", 1)]
    assert f'RESPALDO = "{modelos.ORIGEN_RESPALDO}"' in bloque


def test_f069_r24_usuario_no_resuelto_vale_para_el_alta():
    texto = modelos.TEXTOS_MOTIVO_ALTA["usuario_no_resuelto"]
    assert "alta" in texto.lower()
    assert texto != "No se pudo saber con qué usuario de Sigrid colgar el PDF"
