# tests/test_f075_evals.py
"""F-075 R27 · los evals de IA1 observan el pie del albarán.

- IA1 devuelve en la cabecera ``base_imponible``, ``tipo_iva_pct``,
  ``cuota_iva`` y ``total_albaran``: entran en ``OBSERVABLES`` y en la
  proyección (y quedan atados por el test de F-045).
- Mientras el libro ``IA1_extraccion`` no los tenga rellenos, el informe los
  declara «no medido» (como hoy ``unidad`` y ``descuentos`` en el sentido
  contrario): no se comparan, pero se ve que nadie los está midiendo.
- El conversor lee las columnas del pie como números.

Sin LLM ni libros reales.
"""
from __future__ import annotations

from evals import conversor, informe
from evals.criticidad import cargar_criticidad
from evals.modelos import NO_COMPARAR, ResultadoFase, ResultadoPasada
from evals.procesos import sv2_extraccion

PIE = ("base_imponible", "tipo_iva_pct", "cuota_iva", "total_albaran")


def _fixture(caso, **cabecera):
    return {"caso_id": caso, "fase": "IA1", "tablas": {"cabeceras": [{"caso_id": caso, **cabecera}], "lineas": []}}


def test_f075_r27_el_pie_es_observable_en_la_cabecera():
    for campo in PIE:
        assert campo in sv2_extraccion.OBSERVABLES["cabeceras"]
    assert sv2_extraccion.CAMPOS_PIE == PIE


def test_f075_r27_la_proyeccion_de_ia1_lleva_el_pie():
    documento = {"cabecera": {"base_imponible": 100.0, "tipo_iva_pct": 21.0, "cuota_iva": 21.0,
                              "total_albaran": 121.0}, "lineas": []}
    (cabecera,) = sv2_extraccion.proyectar_ia1(documento, "C-1")["cabeceras"]
    assert [cabecera[c] for c in PIE] == [100.0, 21.0, 21.0, 121.0]
    (vacia,) = sv2_extraccion.proyectar_ia1({"cabecera": {}, "lineas": []}, "C-1")["cabeceras"]
    assert all(vacia[c] is None for c in PIE)


def test_f075_r27_no_medido_mientras_el_libro_no_los_rellene():
    fixtures = {
        "A": _fixture("A", proveedor_nombre="X"),
        "B": _fixture("B", base_imponible=NO_COMPARAR, total_albaran=121.0),
    }
    assert sv2_extraccion.campos_no_medidos(fixtures) == ["base_imponible", "tipo_iva_pct", "cuota_iva"]
    assert sv2_extraccion.campos_no_medidos({}) == list(PIE)
    rellenos = {"C": _fixture("C", **{c: 1.0 for c in PIE})}
    assert sv2_extraccion.campos_no_medidos(rellenos) == []
    # Un null explícito es una expectativa («no figura»): cuenta como medido.
    assert "cuota_iva" not in sv2_extraccion.campos_no_medidos({"D": _fixture("D", cuota_iva=None)})


def test_f075_r27_el_informe_declara_no_medido():
    pasada = ResultadoPasada(modo="completa", fases=[ResultadoFase(nombre="IA1")],
                             no_medidos=["base_imponible", "total_albaran"])
    texto = informe.render(pasada)
    assert "## Campos no medidos" in texto
    assert "no medido" in texto
    assert "- `base_imponible`" in texto and "- `total_albaran`" in texto
    assert "IA1_extraccion" in texto


def test_f075_r27_sin_no_medidos_no_hay_seccion():
    assert "## Campos no medidos" not in informe.render(ResultadoPasada(modo="determinista"))


def test_f075_r27_ejecutar_los_declara_solo_si_se_evalua_ia1(tmp_path, monkeypatch):
    import argparse

    from evals import runner

    monkeypatch.setattr(runner, "corrida_completa", lambda *a, **k: ([ResultadoFase(nombre="IA1")], []))
    monkeypatch.setattr(runner, "corrida_determinista", lambda *a, **k: ([ResultadoFase(nombre="IA3")], []))
    monkeypatch.setattr(runner, "comprobar_peticion", lambda *a: None)
    monkeypatch.setattr(runner, "cargar_fixtures", lambda d, fase: {"A": _fixture("A", total_albaran=1.0)})

    def _opciones(**kw):
        base = dict(fases="", con_llm=True, fixtures=str(tmp_path), casos="", proveedores="", feature="")
        base.update(kw)
        return argparse.Namespace(**base)

    pasada, _ = runner.ejecutar(_opciones())
    assert pasada.no_medidos == ["base_imponible", "tipo_iva_pct", "cuota_iva"]
    pasada, _ = runner.ejecutar(_opciones(con_llm=False))
    assert pasada.no_medidos == []


def test_f075_r27_el_conversor_lee_el_pie_como_numero():
    assert conversor.clave_de_encabezado("Base imponible") == "base_imponible"
    assert conversor.clave_de_encabezado("Tipo IVA (%)") == "tipo_iva_pct"
    assert conversor.clave_de_encabezado("Cuota IVA") == "cuota_iva"
    assert conversor.clave_de_encabezado("Total albarán") == "total_albaran"
    assert conversor.normalizar_celda("1.234,56", "base_imponible").valor == 1234.56
    assert conversor.normalizar_celda("21", "tipo_iva_pct").valor == 21.0
    assert conversor.normalizar_celda("259,26", "cuota_iva").valor == 259.26


def test_f075_r27_el_pie_esta_clasificado_en_criticidad():
    criticidad = cargar_criticidad()
    for campo in PIE:
        assert criticidad.clasificar(f"IA1.cabeceras[].{campo}").clasificado, campo


def test_f075_r27_la_variante_dev_del_comparador_de_obra_no_pide_el_pie():
    """F-048 compara el prompt de la base con el de la rama: la base no conoce el pie.

    Con modelos sintéticos de la misma forma (importar el `domain` de sv2 aquí
    chocaría con el de otros servicios en el mismo proceso)."""
    from typing import Optional

    from pydantic import BaseModel

    from evals.procesos import sv2_obra

    class CabeceraAlbaran(BaseModel):
        proveedor_nombre: Optional[str] = None
        base_imponible: Optional[float] = None
        tipo_iva_pct: Optional[float] = None
        cuota_iva: Optional[float] = None
        total_albaran: Optional[float] = None
        id: Optional[str] = None

    class LineaAlbaran(BaseModel):
        concepto: Optional[str] = None

    class DocumentoAlbaran(BaseModel):
        """El documento."""

        cabecera: CabeceraAlbaran
        lineas: list[LineaAlbaran]
        lectura_correo: Optional[dict] = None

    recortado = sv2_obra.modelo_sin_campo(DocumentoAlbaran)
    cabecera = recortado.model_fields["cabecera"].annotation
    assert list(recortado.model_fields) == ["cabecera", "lineas"]
    assert cabecera.__name__ == "CabeceraAlbaran" and cabecera is not CabeceraAlbaran
    assert list(cabecera.model_fields) == ["proveedor_nombre", "id"]
    assert recortado.model_fields["cabecera"].is_required()
    assert recortado.model_json_schema()["description"] == "El documento."  # sin perder la docstring
    assert sv2_obra.modelo_sin_campo(LineaAlbaran) is LineaAlbaran  # sin nada que quitar, el mismo
