# tests/test_f045_r20_r21_albaranes.py
"""F-045 · R20 y R21: del nombre del fichero al caso, y los cuatro fallos.

El puente entre los tres mundos: del **nombre del fichero** sale el **código de
albarán** —el que el humano escribe en cada fila del Excel— y de ahí el
**caso_id**. Sin ese puente, casar 59 albaranes con 142 filas es trabajo
manual, y el humano sigue añadiendo material: por eso el renombrado es un
script reproducible y no un `mv` a mano.

Y los cuatro fallos que la regla de nombres no cubre salen **listados uno a
uno** (R21). Una importación que se traga 57 de 59 albaranes sin decir cuáles
faltan es peor que no importar.
"""

from __future__ import annotations

from evals.revision import albaranes


# --- R20: el código sale del nombre ----------------------------------------


def test_f045_r20_el_codigo_es_lo_que_va_tras_el_ultimo_guion_bajo():
    assert albaranes.codigo_desde_nombre("PROVEEDOR_SS-0003967.pdf") == "SS-0003967"
    assert albaranes.codigo_desde_nombre("A_B_C_2139643.png") == "2139643"


def test_f045_r20_sin_guion_bajo_el_codigo_es_el_nombre_entero():
    assert albaranes.codigo_desde_nombre("SS-0003967.png") == "SS-0003967"
    assert albaranes.codigo_desde_nombre("0334191.jpg") == "0334191"


def test_f045_r20_se_admiten_las_cuatro_extensiones():
    assert set(albaranes.EXTENSIONES) == {".pdf", ".png", ".jpg", ".jpeg"}


def test_f045_r20_el_formato_distingue_el_pdf_de_la_imagen():
    assert albaranes.formato_de("FOO.pdf") == "pdf"
    for nombre in ("FOO.png", "FOO.jpg", "FOO.JPEG"):
        assert albaranes.formato_de(nombre) == "imagen"


def test_f045_r20_manda_el_codigo_del_papel_no_el_persistido():
    """Precedente real: SS-0801977 leído donde el papel decía SS-0001977."""
    plan = albaranes.emparejar({"SS0001977": "RES-005"}, ["SALMEDINA_SS-0001977.pdf"])
    assert [copia.caso_id for copia in plan.copias] == ["RES-005"]
    otro = albaranes.emparejar({"SS0001977": "RES-005"}, ["SALMEDINA_SS-0801977.pdf"])
    assert otro.copias == []
    assert [fallo.tipo for fallo in otro.fallos] == ["codigo_sin_fila", "fila_sin_fichero"]


def test_f045_r20_el_destino_es_el_caso_id_con_su_extension():
    plan = albaranes.emparejar({"2139643": "FER-002"}, ["FEYMACO_2139643.PDF"])
    assert plan.copias[0].origen == "FEYMACO_2139643.PDF"
    assert plan.copias[0].destino == "FER-002.pdf"


def test_f045_r20_un_fichero_ya_renombrado_no_se_vuelve_a_tocar():
    """El renombrado se repite cada vez que el humano trae material nuevo."""
    plan = albaranes.emparejar(
        {"0000168": "RES-001"}, ["RES-001.pdf"], caso_ids={"RES-001"}
    )
    assert plan.copias == []
    assert plan.fallos == []
    assert plan.ya_colocados == ["RES-001.pdf"]


# --- R21: los cuatro fallos, uno a uno -------------------------------------


def test_f045_r21_dos_ficheros_del_mismo_formato_y_codigo_son_un_choque():
    plan = albaranes.emparejar(
        {"2139643": "FER-002"}, ["A_2139643.pdf", "B_2139643.pdf"]
    )
    assert [fallo.tipo for fallo in plan.fallos] == ["codigo_duplicado"]
    assert "A_2139643.pdf" in plan.fallos[0].detalle
    assert "B_2139643.pdf" in plan.fallos[0].detalle
    assert plan.copias == []


def test_f045_r21_un_codigo_que_no_esta_en_el_excel_se_lista():
    plan = albaranes.emparejar({}, ["PROV_999999.pdf"])
    assert plan.fallos[0].tipo == "codigo_sin_fila"
    assert "999999" in plan.fallos[0].detalle


def test_f045_r21_una_fila_sin_fichero_se_lista():
    plan = albaranes.emparejar({"0000168": "RES-001", "0003935": "RES-002"},
                               ["PROV_0000168.pdf"])
    sin_fichero = [f for f in plan.fallos if f.tipo == "fila_sin_fichero"]
    assert len(sin_fichero) == 1
    assert "RES-002" in sin_fichero[0].detalle


def test_f045_r21_un_nombre_que_queda_vacio_tras_la_regla_se_lista():
    plan = albaranes.emparejar({"X": "GEN-001"}, ["PROVEEDOR_.pdf"])
    assert [f.tipo for f in plan.fallos] == ["nombre_vacio", "fila_sin_fichero"]


def test_f045_r21_una_extension_que_no_es_de_albaran_no_es_un_albaran():
    plan = albaranes.emparejar({"0000168": "RES-001"}, ["notas.txt", "PROV_0000168.pdf"])
    assert plan.ignorados == ["notas.txt"]
    assert len(plan.copias) == 1


def test_f045_r21_sin_ningun_fichero_se_listan_todas_las_filas():
    """Si el humano aún no ha copiado los originales, hay que decirlo así."""
    plan = albaranes.emparejar({"a": "RES-001", "b": "RES-002"}, [])
    assert [f.tipo for f in plan.fallos] == ["fila_sin_fichero"] * 2
    assert plan.copias == []


# --- El renombrado es un script, no un `mv` a mano -------------------------


def test_f045_r20_renombrar_es_reproducible(tmp_path):
    (tmp_path / "PROV_0000168.pdf").write_bytes(b"%PDF-falso")
    plan = albaranes.emparejar({"0000168": "RES-001"}, ["PROV_0000168.pdf"])
    hechos = albaranes.renombrar(plan.copias, tmp_path)
    assert hechos == ["PROV_0000168.pdf -> RES-001.pdf"]
    assert (tmp_path / "RES-001.pdf").read_bytes() == b"%PDF-falso"
    assert not (tmp_path / "PROV_0000168.pdf").exists()
    # Segunda pasada: el fichero ya no está y no se inventa nada.
    assert albaranes.renombrar(plan.copias, tmp_path) == []


def test_f045_r20_renombrar_en_seco_no_toca_el_disco(tmp_path):
    (tmp_path / "PROV_0000168.pdf").write_bytes(b"%PDF-falso")
    plan = albaranes.emparejar({"0000168": "RES-001"}, ["PROV_0000168.pdf"])
    assert albaranes.renombrar(plan.copias, tmp_path, ejecutar=False) == [
        "PROV_0000168.pdf -> RES-001.pdf"
    ]
    assert (tmp_path / "PROV_0000168.pdf").exists()
    assert not (tmp_path / "RES-001.pdf").exists()


def test_f045_r20_renombrar_no_pisa_un_destino_que_ya_existe(tmp_path):
    (tmp_path / "PROV_0000168.pdf").write_bytes(b"nuevo")
    (tmp_path / "RES-001.pdf").write_bytes(b"el que ya estaba")
    plan = albaranes.emparejar({"0000168": "RES-001"}, ["PROV_0000168.pdf"])
    assert albaranes.renombrar(plan.copias, tmp_path) == []
    assert (tmp_path / "RES-001.pdf").read_bytes() == b"el que ya estaba"
