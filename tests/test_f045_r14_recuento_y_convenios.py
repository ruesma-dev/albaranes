# tests/test_f045_r14_recuento_y_convenios.py
"""F-045 · los detalles que la campaña de mutación destapó sin cubrir.

La campaña del 2026-09-15 (266 mutantes) dejó 90 supervivientes, y la mayoría
señalaban lo mismo: el banco comprobaba QUÉ se escribe y casi nada de CÓMO se
cuenta ni de cuándo se deja de escribir. Y justo eso es lo que promete R14 —el
recuento por columna— y lo que sostiene R18 —no guardar un libro que no
cambia—. Un informe que suma mal es peor que no tener informe: se lee igual de
convincente.

Cada bloque de aquí abajo nació de un mutante que sobrevivió.
"""

from __future__ import annotations

import dataclasses
import json
from pathlib import Path

import pytest

from evals.revision import albaranes, escritura, informe as informe_mod
from evals.revision import lectura, mapa, reparto, vocabulario
from evals.revision.modelos import (
    DEFECTO_CONOCIDO,
    NO_REGRESION,
    CasoRevisado,
    FilaPlana,
    InformeImportacion,
    LineaRevisada,
)

VOCAB = vocabulario.cargar()


# --- El recuento del informe: R14 promete números, no impresiones ---------


def test_f045_r14_cada_celda_cae_en_su_cubo_y_suma_uno():
    informe = InformeImportacion()
    informe.contar("IA1", "lineas", "importe", 19.41)
    informe.contar("IA1", "lineas", "importe", "?")
    informe.contar("IA1", "lineas", "importe", None)
    informe.contar("IA1", "lineas", "importe", "   ")
    assert informe.celdas["IA1"]["lineas"]["importe"] == {
        "valor": 1,
        "interrogante": 1,
        "vacia": 2,
    }


def test_f045_r14_el_recuento_arranca_en_cero_y_no_en_otro_numero():
    informe = InformeImportacion()
    informe.contar("IA1", "cabeceras", "fecha", "2024-07-03")
    assert informe.celdas["IA1"]["cabeceras"]["fecha"] == {
        "valor": 1,
        "interrogante": 0,
        "vacia": 0,
    }


def test_f045_r14_un_cero_no_es_una_celda_vacia():
    """`0` es un valor afirmado: contarlo como vacío falsearía el informe."""
    informe = InformeImportacion()
    informe.contar("FINAL", "lineas", "importe_final", 0)
    assert informe.celdas["FINAL"]["lineas"]["importe_final"]["valor"] == 1


def test_f045_r14_el_reparto_por_clasificacion_cuenta_casos_no_lineas():
    informe = InformeImportacion(casos=[_caso(), _caso("hay comentario"), _caso()])
    assert informe.por_clasificacion == {NO_REGRESION: 2, DEFECTO_CONOCIDO: 1}


def test_f045_r14_sin_casos_el_reparto_es_cero_y_cero():
    assert InformeImportacion().por_clasificacion == {
        NO_REGRESION: 0,
        DEFECTO_CONOCIDO: 0,
    }


def test_f045_r14_el_informe_arranca_sin_filas_leidas():
    assert InformeImportacion().filas_leidas == 0


# --- El informe en Markdown: sus ramas también son promesas ---------------


def test_f045_r14_sin_incidencias_el_informe_lo_dice_en_vez_de_callar():
    informe = InformeImportacion(casos=[_caso()])
    informe.casos[0].caso_id = "HOR-001"
    texto = informe_mod.render(informe)
    assert "Sin incidencias: cada caso tiene su documento." in texto
    assert "(ningún fichero emparejado)" in texto


def test_f045_r14_cada_caso_sale_en_su_grupo_y_no_en_el_otro():
    uno, otro = _caso(), _caso("falla la partida")
    uno.caso_id, otro.caso_id = "HOR-001", "HOR-002"
    texto = informe_mod.render(InformeImportacion(casos=[uno, otro]))
    no_regresion = texto.split("No regresión: ")[1].split("\n")[0]
    defecto = texto.split("Defecto conocido: ")[1].split("\n")[0]
    assert no_regresion == "HOR-001"
    assert defecto == "HOR-002"


def test_f045_r14_ninguno_tiene_dos_motivos_y_el_informe_los_separa():
    """«En seco» es no haber querido escribir; «nada cambiaba» es R18 diciendo

    que la importación es idempotente. Llamar «en seco» a la segunda haría
    pasar por simulacro una pasada de verdad, y eso ya despistó a un reviewer.
    """
    seco = informe_mod.render(InformeImportacion(en_seco=True))
    assert "pasada EN SECO" in seco
    real = informe_mod.render(InformeImportacion())
    assert "ningún libro cambiaba" in real
    escrita = informe_mod.render(InformeImportacion(libros_escritos=["INPUTS.xlsx"]))
    assert "- Libros escritos: INPUTS.xlsx" in escrita


def test_f045_r14_sin_avisos_no_se_escribe_la_seccion_de_avisos():
    assert "## Avisos" not in informe_mod.render(InformeImportacion())
    con_aviso = InformeImportacion(avisos=["algo que contar"])
    assert "## Avisos" in informe_mod.render(con_aviso)
    assert "- algo que contar" in informe_mod.render(con_aviso)


# --- El mapa se escribe determinista: es lo que lo hace comparable --------


def test_f045_r7_el_mapa_se_escribe_ordenado_legible_y_sin_escapes(tmp_path):
    ruta = tmp_path / "mapa.json"
    mapa.guardar(
        {
            "RES-002": {"clave": "X/2", "codigo": "2", "pestana": "Residuos"},
            "RES-001": {"clave": "X/1", "codigo": "1", "pestana": "Residuós"},
        },
        ruta,
    )
    texto = ruta.read_text(encoding="utf-8")
    # Ordenado: RES-001 antes que RES-002, aunque llegaran al revés.
    assert texto.index("RES-001") < texto.index("RES-002")
    # Con sangría: un JSON en una línea no se revisa en un diff.
    assert '\n  "casos": {' in texto
    # Sin escapes: el acento viaja tal cual, no como ó.
    assert "Residuós" in texto
    assert "\\u" not in texto


def test_f045_r7_el_mapa_se_escribe_byte_a_byte_como_dice_su_docstring(tmp_path):
    """El segundo bloqueante del reviewer: fijar el CONTENIDO, no solo el orden.

    `guardar` monta cada registro en el orden de `CAMPOS` —que NO es
    alfabético— y es `sort_keys` quien lo reordena. Sin este test, quitarlo
    pasaba desapercibido y una reimportación reescribía el mapa entero por un
    cambio de forma, no de dato.
    """
    ruta = tmp_path / "mapa.json"
    mapa.guardar(
        {"RES-001": {"clave": "B82899550/0000168", "codigo": "0000168",
                     "nombre_original": "RES-001.pdf", "formato": "pdf",
                     "gemelo_de": None, "pestana": "Residuos",
                     "familia_documento": "residuos"}},
        ruta,
    )
    esperado = """{
  "_doc": "%s",
  "casos": {
    "RES-001": {
      "clave": "B82899550/0000168",
      "codigo": "0000168",
      "familia_documento": "residuos",
      "formato": "pdf",
      "gemelo_de": null,
      "nombre_original": "RES-001.pdf",
      "pestana": "Residuos"
    }
  }
}
""" % mapa._DOC
    assert ruta.read_text(encoding="utf-8") == esperado


def test_f045_r7_el_mapa_declara_todos_sus_campos_aunque_vengan_vacios(tmp_path):
    ruta = tmp_path / "mapa.json"
    mapa.guardar({"RES-001": {"clave": "X/1"}}, ruta)
    registro = json.loads(ruta.read_text(encoding="utf-8"))["casos"]["RES-001"]
    assert set(registro) == set(mapa.CAMPOS)
    assert registro["formato"] is None


def test_f045_r7_el_indice_inverso_ignora_los_registros_sin_clave():
    inverso = mapa.por_clave({"RES-001": {"clave": "X/1"}, "RES-002": {"clave": ""}})
    assert inverso == {"X/1": "RES-001"}


# --- Los convenios de celda: `or None` no es adorno ------------------------


def test_f045_r2_el_comentario_de_cada_tabla_llega_a_su_fila():
    caso = _caso_completo(comentarios="la partida sale mal")
    tablas = reparto.repartir(caso, VOCAB)
    assert tablas["IA1"]["cabeceras"][0]["comentario"] == "la partida sale mal"
    assert tablas["IA1"]["lineas"][0]["comentario"] == "la partida sale mal"
    assert tablas["IA3"]["lineas_valoradas"][0]["comentario"] == "la partida sale mal"
    assert tablas["FINAL"]["lineas"][0]["comentario"] == "la partida sale mal"
    assert tablas["FINAL"]["datos_generales"][0]["comentario"] == "la partida sale mal"


def test_f045_r2_la_sintetica_y_la_conciliacion_tambien_arrastran_su_comentario():
    caso = _caso_completo(comentarios="no ha creado esta linea", deducida=True, nueva=True)
    tablas = reparto.repartir(caso, VOCAB)
    assert tablas["IA3"]["sinteticas_esperadas"][0]["comentario"] == "no ha creado esta linea"
    assert tablas["FINAL"]["lineas_anadidas"][0]["comentario"] == "no ha creado esta linea"


def test_f045_r2_los_datos_generales_llevan_proveedor_fecha_y_fichero():
    caso = _caso_completo()
    caso.fichero = "HOR-001.pdf"
    generales = reparto.repartir(caso, VOCAB)["FINAL"]["datos_generales"][0]
    assert generales["proveedor"] == "HORPRESOL, S.L."
    assert generales["fecha"] == "2026-03-11"
    assert generales["fichero"] == "HOR-001.pdf"


def test_f045_r2_la_linea_de_entrada_lleva_su_unidad():
    linea = reparto.repartir(_caso_completo(), VOCAB)["INPUTS"]["lineas_albaran"][0]
    assert linea["unidad"] == "M3"
    assert linea["descripcion"] == "HA-25/B/20/IIa"


def test_f045_r2_casa_con_contrato_dice_SI_solo_si_la_linea_esta_en_contrato():
    del_contrato = reparto.repartir(_caso_completo(), VOCAB)["FINAL"]["lineas"][0]
    assert del_contrato["casa_con_contrato"] == "SI"
    assert del_contrato["linea_contrato"] == "?"
    nueva = reparto.repartir(_caso_completo(nueva=True), VOCAB)["FINAL"]["lineas"][0]
    assert nueva["casa_con_contrato"] == "NO"
    assert nueva["linea_contrato"] is None


def test_f045_r2_el_total_se_redondea_a_dos_decimales():
    """Son euros: un total con tres decimales no existe en ninguna factura."""
    caso = _caso_completo(importe=10.126)
    total = reparto.repartir(caso, VOCAB)["FINAL"]["datos_generales"][0]
    assert total["total_valorado_esperado"] == 10.13


# --- Números: el Excel los manda como texto tan a menudo como no ----------


@pytest.mark.parametrize(
    "bruto,esperado",
    [("72,50", 72.5), ("72.5", 72.5), (72.5, 72.5), ("", None), ("no es", "no es")],
)
def test_f045_r2_el_numero_se_reconoce_venga_como_venga(bruto, esperado):
    assert reparto._numero(bruto) == esperado


def test_f045_r2_un_booleano_no_es_un_numero_ni_se_convierte():
    assert reparto._numero(True) is True
    assert reparto._numero(None) is None


def test_f045_r2_dos_comas_no_son_un_decimal():
    """«1,234,56» no es un número español: se deja el texto, no se adivina."""
    assert reparto._numero("1,234,56") == "1,234,56"


# --- El vocabulario: el prefijo más largo gana ----------------------------


def test_f045_r5_entre_dos_prefijos_que_solapan_gana_el_mas_largo(tmp_path):
    datos = json.loads(vocabulario.RUTA_VOCABULARIO.read_text(encoding="utf-8"))
    datos["origen_linea"] = [
        {"canonico": "impresa", "exactos": [], "prefijos": ["EN"]},
        {"canonico": "deducida", "exactos": [], "prefijos": ["EN ALBARAN PERO"]},
    ]
    ruta = tmp_path / "vocabulario.json"
    ruta.write_text(json.dumps(datos), encoding="utf-8")
    vocab = vocabulario.cargar(ruta)
    assert vocab.origen_linea("EN ALBARAN PERO DEDUCE", fila=2) == "deducida"
    assert vocab.origen_linea("EN OTRA COSA", fila=2) == "impresa"


# --- Los modelos son inmutables a propósito -------------------------------


@pytest.mark.parametrize(
    "objeto",
    [
        FilaPlana(numero_fila=2, valores={}),
        vocabulario.OrigenPrecio(precio_source="albaran", impreso=True),
        albaranes.Copia(origen="a.pdf", destino="b.pdf", caso_id="X", formato="pdf"),
        albaranes.Fallo(tipo="x", detalle="y"),
        escritura.DefTabla(titulo="TABLA 1", clave="cabeceras"),
        vocabulario.DestinoEtiqueta(
            etiqueta="HORMIGON", familia_documento="hormigon", pestana="Hormigon",
            prefijo="HOR", familia_linea=None, en_catalogo=True,
        ),
        LineaRevisada(
            fila=FilaPlana(numero_fila=2, valores={}), origen_linea="impresa",
            origen_contrato="contrato", precio_source="contrato_db",
            precio_impreso=False, importe_source="contrato_db",
            importe_impreso=False, num_linea=1,
        ),
    ],
)
def test_f045_r2_los_modelos_del_importador_no_se_mutan_por_accidente(objeto):
    """Congelados a propósito: una fila del Excel no se reescribe a mitad."""
    campo = dataclasses.fields(objeto)[0].name
    with pytest.raises(dataclasses.FrozenInstanceError):
        setattr(objeto, campo, "otra cosa")


# --- Lectura: filas cortas y celdas en blanco -----------------------------


def test_f045_r1_una_fila_mas_corta_que_los_encabezados_no_revienta(tmp_path):
    import openpyxl

    from tests.test_f045_r1_lectura import ENCABEZADOS

    libro = openpyxl.Workbook()
    hoja = libro.active
    hoja.append(list(ENCABEZADOS))
    hoja.append(["0000168", "RESIDUOS", "B82899550"])
    ruta = tmp_path / "corta.xlsx"
    libro.save(ruta)
    libro.close()
    fila = lectura.leer(ruta)[0]
    assert fila.texto("codigo_albaran") == "0000168"
    assert fila.vacia("comentarios")


def test_f045_r1_una_celda_de_solo_espacios_esta_vacia():
    assert lectura._esta_vacia("   ")
    assert lectura._esta_vacia(None)
    assert not lectura._esta_vacia("0")


def test_f045_r1_las_rutas_por_defecto_apuntan_donde_dicen():
    from evals.revision import __main__ as cli

    assert lectura.RUTA_FUENTE.parent.name == "fuente"
    assert lectura.RUTA_FUENTE.parent.parent.name == "inputs"
    assert cli.RUTA_INFORME.parent.name == "progress"
    assert cli.RUTA_ORIGINALES.parent.name == "inputs"
    assert cli.RUTA_ORIGINALES.name == "albaranes"


# --- Emparejado: el mínimo de subcadena es un límite, no un adorno --------


def test_f045_r20_un_codigo_de_exactamente_cinco_se_busca_dentro_del_nombre():
    plan = albaranes.emparejar({"24385": "RES-009"}, ["ALB del 24385 obra.pdf"])
    assert [c.caso_id for c in plan.copias] == ["RES-009"]


# --- Utilidades -----------------------------------------------------------


def _caso(comentario: str | None = None) -> CasoRevisado:
    destino = VOCAB.etiqueta("HORMIGON", fila=2)
    fila = FilaPlana(numero_fila=2, valores={"comentarios": comentario})
    linea = LineaRevisada(
        fila=fila, origen_linea="impresa", origen_contrato="contrato",
        precio_source="contrato_db", precio_impreso=False,
        importe_source="contrato_db", importe_impreso=False, num_linea=1,
    )
    return CasoRevisado(codigo="X", clave="c/X", destino=destino, lineas=[linea])


def _caso_completo(comentarios=None, deducida=False, nueva=False, importe=580) -> CasoRevisado:
    valores = {
        "codigo_albaran": "H132525", "tipo_albaran": "HORMIGON",
        "cif": "B04685541", "nombre_empresa": "HORPRESOL, S.L.",
        "codigo_obra": "693", "fecha": "2026-03-11",
        "codigo_contrato": "CTSU23/0386", "partida": "P5.14.01",
        "origen_linea": "DEDUCIDA INCREMENTO POR ANIO" if deducida else "EN ALBARAN",
        "origen_contrato": "NUEVA" if nueva else "EN CONTRATO",
        "concepto": "HA-25/B/20/IIa", "cantidad": 8, "unidad": "M3",
        "precio_unitario": 72.5, "origen_precio": "DE CONTRATO",
        "importe": importe, "origen_importe": "DE CONTRATO",
        "descuento": None, "ler": None, "comentarios": comentarios,
    }
    filas = [FilaPlana(numero_fila=2, valores=valores)]
    if deducida:
        impresa = dict(valores, origen_linea="EN ALBARAN", origen_contrato="EN CONTRATO")
        filas.insert(0, FilaPlana(numero_fila=1, valores=impresa))
    casos = reparto.agrupar_por_albaran(filas, VOCAB)
    reparto.asignar_casos_id(casos, {})
    return casos[0]


# --- Segunda tanda: lo que la reinyección dejó todavía vivo ---------------


def test_f045_r2_la_fila_de_ia4_tambien_arrastra_su_comentario():
    caso = _caso_completo(comentarios="no encuentro de donde saca el CIF", nueva=True)
    conciliacion = reparto.repartir(caso, VOCAB)["IA4"]["conciliacion"][0]
    assert conciliacion["comentario"] == "no encuentro de donde saca el CIF"


def test_f045_r7_un_caso_sin_gemelo_guarda_null_y_no_una_cadena_vacia():
    """`gemelo_de` es un enlace o no lo es; `""` no es ninguna de las dos."""
    casos = reparto.agrupar_por_albaran([_fila_hormigon()], VOCAB)
    mapa_nuevo, _ = reparto.asignar_casos_id(casos, {})
    assert mapa_nuevo["HOR-001"]["gemelo_de"] is None


def test_f045_r20_el_minimo_de_subcadena_cuenta_tambien_sin_los_ceros():
    """`024385` pela a `24385`, que mide exactamente el mínimo: entra."""
    plan = albaranes.emparejar({"024385": "RES-009"}, ["ALB del 24385 obra.pdf"])
    assert [(c.caso_id, c.estrategia) for c in plan.copias] == [("RES-009", "sin_ceros")]


def test_f045_r1_del_excel_se_lee_el_VALOR_no_la_formula(tmp_path):
    """`data_only=True`: una celda con fórmula vale por su resultado, y un

    libro recién escrito no lo trae; leer el texto `=A2*2` como cantidad
    metería una cadena donde el banco espera un número."""
    import openpyxl

    from tests.test_f045_r1_lectura import ENCABEZADOS, FILA

    libro = openpyxl.Workbook()
    hoja = libro.active
    hoja.append(list(ENCABEZADOS))
    hoja.append(list(FILA))
    hoja.cell(row=2, column=12, value="=1+1")  # la columna `cantidad`
    ruta = tmp_path / "con_formula.xlsx"
    libro.save(ruta)
    libro.close()
    assert lectura.leer(ruta)[0].bruto("cantidad") is None


def test_f045_r1_las_rutas_por_defecto_caen_dentro_del_repositorio():
    """Un `parents[N]` de más las saca del repo y el importador leería y

    escribiría en otro sitio sin decir nada."""
    import evals
    from evals.revision import __main__ as cli

    paquete = Path(evals.__file__).resolve().parent
    raiz = paquete.parent
    # Lo que vive dentro del banco tiene que caer dentro de `evals/`...
    for ruta in (lectura.RUTA_FUENTE, cli.RUTA_ORIGINALES, mapa.RUTA_MAPA,
                 vocabulario.RUTA_VOCABULARIO):
        assert paquete in ruta.parents, ruta
    # ...y el informe, en `progress/` de la raíz, que es de donde lo lee el humano.
    assert cli.RUTA_INFORME.parent == raiz / "progress"
    assert cli.RUTA_ORIGINALES == paquete / "inputs" / "albaranes"
    assert lectura.RUTA_FUENTE.parent == paquete / "inputs" / "fuente"


def _fila_hormigon() -> FilaPlana:
    return FilaPlana(
        numero_fila=2,
        valores={"codigo_albaran": "H132525", "tipo_albaran": "HORMIGON",
                 "cif": "B04685541", "origen_linea": "EN ALBARAN",
                 "origen_contrato": "EN CONTRATO", "origen_precio": "DE CONTRATO",
                 "origen_importe": "DE CONTRATO"},
    )
