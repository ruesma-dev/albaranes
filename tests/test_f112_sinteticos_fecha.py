# tests/test_f112_sinteticos_fecha.py
"""F-112 · R27: los sintéticos de cambio de año del juego D.

Seis casos con su papel, su `recibido_utc` y su fecha esperada; dos
generaciones dan los mismos bytes; el JSON versionado es el que genera el
script; y el comparador saca la referencia con `fecha_recepcion_de` (SIN-006,
Nochevieja: el 01-01 de Madrid). Sin red ni IA.
"""

from __future__ import annotations

import io
import json
from datetime import date

from PIL import Image

from evals import comparar_fecha as cf
from evals import sinteticos_fecha as sf

ESPERADOS = {
    # caso: (papel, recibido_utc día UTC, fecha esperada, referencia en Madrid)
    "SIN-001": ("28/12", "2027-01-03", "2026-12-28", date(2027, 1, 3)),
    "SIN-002": ("02/01", "2027-01-05", "2027-01-02", date(2027, 1, 5)),
    "SIN-003": ("15/12", "2026-12-18", "2026-12-15", date(2026, 12, 18)),
    "SIN-004": ("28/12/2026", "2027-01-03", "2026-12-28", date(2027, 1, 3)),
    "SIN-005": ("30/12/25", "2026-01-02", "2025-12-30", date(2026, 1, 2)),
    "SIN-006": ("01/01", "2026-12-31", "2027-01-01", date(2027, 1, 1)),
}


def test_f112_r27_los_seis_casos():
    assert [c.caso_id for c in sf.CASOS] == list(ESPERADOS)
    for caso in sf.CASOS:
        papel, recibido, esperada, _ref = ESPERADOS[caso.caso_id]
        assert caso.papel == papel
        assert caso.recibido_utc.startswith(recibido)
        assert caso.fecha_esperada == esperada
        assert caso.tipologia == "generico"
    assert {c.caso_id: c.recibido_utc for c in sf.CASOS}["SIN-006"] == "2026-12-31T23:30:00Z"


def test_f112_r27_dos_generaciones_dan_los_mismos_bytes(tmp_path):
    uno = sf.generar(tmp_path / "uno", tmp_path / "uno.json")
    dos = sf.generar(tmp_path / "dos", tmp_path / "dos.json")

    assert [p.name for p in uno[:-1]] == [f"{c}.jpg" for c in ESPERADOS]
    for a, b in zip(uno, dos, strict=True):
        assert a.read_bytes() == b.read_bytes(), a.name


def test_f112_r27_las_imagenes_son_jpg_y_solo_cambia_la_fecha(tmp_path):
    rutas = sf.generar(tmp_path / "img", tmp_path / "c.json")[:-1]
    imagenes = [Image.open(io.BytesIO(r.read_bytes())) for r in rutas]

    assert {im.format for im in imagenes} == {"JPEG"}
    assert {im.size for im in imagenes} == {(1240, 700)}
    assert len({r.read_bytes() for r in rutas}) == 6  # cada papel es distinto
    assert sum("{papel}" in linea for linea in sf.LINEAS) == 1
    assert sf.LINEAS[0] == "PROVEEDOR SINTETICO, S.L."
    # La fuente por defecto de Pillow no trae tildes: el papel va en ASCII.
    assert all(linea.isascii() for linea in sf.LINEAS)


def test_f112_r27_el_json_versionado_es_el_que_genera_el_script():
    # Sin depender del fin de línea con que git deje el fichero (core.autocrlf).
    assert sf.RUTA_JSON.read_text(encoding="utf-8").splitlines() == sf.render_json().splitlines()
    datos = json.loads(sf.RUTA_JSON.read_text(encoding="utf-8"))
    assert datos["version"] == 1 and len(datos["casos"]) == 6


def test_f112_r27_el_comparador_saca_la_referencia_de_madrid():
    casos = {c.caso_id: c for c in cf.juego_d(sf.RUTA_JSON)}

    assert list(casos) == list(ESPERADOS)
    for caso_id, (_papel, _recibido, esperada, referencia) in ESPERADOS.items():
        assert casos[caso_id].esperada == date.fromisoformat(esperada)
        assert casos[caso_id].referencia == referencia, caso_id


def test_f112_r27_por_defecto_las_imagenes_van_al_directorio_ignorado():
    assert sf.RUTA_IMAGENES == sf.RAIZ_REPO / "evals" / "inputs" / "albaranes"
    assert cf.RUTA_SINTETICOS == sf.RUTA_JSON


def test_f112_r27_cli(tmp_path, capsys):
    assert sf.main(["--destino", str(tmp_path / "d"), "--json", str(tmp_path / "c.json")]) == 0
    assert (tmp_path / "d" / "SIN-006.jpg").is_file()
    assert capsys.readouterr().out.count("sinteticos_fecha:") == 7
