# tests/test_f114_js.py
"""F-114 · el combo de proveedor con «Solo de la obra» (``static/app.js``), con node.

- Funciones puras (T4): R3 mínimo de 3, R6 etiqueta con «N fichas», R10 mensaje
  de lista de la obra vacía. Patrón de ``test_f065_f1_js.py``.
- ``initCombo`` en modo global (T5): R2, R4, R5, R6, R7, R8, R9, R10, R11, con
  ``tests/dom_falso.js``, ``fetch`` falso y temporizadores falsos.
Nombres y CIF inventados.
"""
from __future__ import annotations

from test_f065_f1_js import _ejecutar, con_node

_PURAS = ["_comboLabel", "textoBusquedaProveedor", "urlProveedoresTodos",
          "etiquetaProveedorGlobal", "mensajeListaObraVacia"]


# =================================================================== #
# T4 · funciones puras
# =================================================================== #
@con_node
def test_f114_r3_minimo_de_tres_caracteres_utiles(tmp_path):
    casos = _ejecutar(tmp_path, _PURAS, """
        console.log(JSON.stringify([
            textoBusquedaProveedor(""), textoBusquedaProveedor(null),
            textoBusquedaProveedor(undefined), textoBusquedaProveedor("ab"),
            textoBusquedaProveedor("  ab  "), textoBusquedaProveedor("abc"),
            textoBusquedaProveedor("  b12 3 "), textoBusquedaProveedor("     "),
            urlProveedoresTodos("/api/sigrid/proveedores/todos", "a&b ñ%"),
        ]));
    """)
    assert casos == [None, None, None, None, None, "abc", "b12 3", None,
                     "/api/sigrid/proveedores/todos?q=a%26b%20%C3%B1%25"]


@con_node
def test_f114_r6_etiqueta_con_varias_fichas(tmp_path):
    casos = _ejecutar(tmp_path, _PURAS, """
        console.log(JSON.stringify([
            etiquetaProveedorGlobal({cif: "B00000001", nombre: "ALFA SL", fichas: 1}),
            etiquetaProveedorGlobal({cif: "B00000002", nombre: "BETA SA", fichas: 3}),
            etiquetaProveedorGlobal({cif: "B00000003", nombre: "GAMMA", fichas: 2}),
            etiquetaProveedorGlobal({cif: "B00000004", nombre: "", fichas: null}),
            etiquetaProveedorGlobal({cif: "B00000005", nombre: "DELTA"}),
        ]));
    """)
    assert casos == [
        "ALFA SL — B00000001",
        "BETA SA — B00000002 · 3 fichas en Sigrid",
        "GAMMA — B00000003 · 2 fichas en Sigrid",
        "Sin nombre — B00000004",
        "DELTA — B00000005",
    ]


@con_node
def test_f114_r10_mensaje_lista_de_la_obra_vacia(tmp_path):
    casos = _ejecutar(tmp_path, _PURAS, """
        console.log(JSON.stringify([
            mensajeListaObraVacia(null),
            mensajeListaObraVacia("Falta el codigo de obra."),
            mensajeListaObraVacia("Falta el codigo de obra"),
        ]));
    """)
    desmarca = "Desmarca «Solo de la obra» para buscar entre todos los proveedores de Sigrid"
    assert casos == [
        "Sin proveedores con contrato en la obra. " + desmarca,
        "Falta el codigo de obra. " + desmarca,
        "Falta el codigo de obra. " + desmarca,
    ]
