# tests/test_f011_r12_omitidos.py
"""F-011 · R12 — Sin fichero de albarán, el caso se OMITE y se dice.

Los albaranes no se versionan (son documentos de proveedor). En una máquina que
no los tenga, la corrida no puede fallar entera ni —peor— dar VERDE saltándose
casos en silencio: se marcan OMITIDOS con su motivo y salen en el informe.
"""

from evals.modelos import NO_EVALUABLE, OMITIDO, ResultadoCaso, ResultadoFase
from evals.procesos.sv2_extraccion import EXTENSIONES, ruta_de_albaran


def test_f011_r12_sin_fichero_no_hay_ruta(tmp_path):
    assert ruta_de_albaran("HOR-001", tmp_path) is None


def test_f011_r12_se_encuentra_el_pdf_del_caso(tmp_path):
    (tmp_path / "HOR-001.pdf").write_bytes(b"%PDF-1.4")

    assert ruta_de_albaran("HOR-001", tmp_path).name == "HOR-001.pdf"


def test_f011_r12_tambien_valen_las_fotos(tmp_path):
    (tmp_path / "RES-001.jpg").write_bytes(b"\xff\xd8\xff")

    assert ruta_de_albaran("RES-001", tmp_path).name == "RES-001.jpg"
    assert ".jpg" in EXTENSIONES and ".png" in EXTENSIONES


def test_f011_r12_el_caso_omitido_lleva_su_motivo():
    caso = ResultadoCaso.omitido(
        "HOR-002", "IA1", "no existe evals/inputs/albaranes/HOR-002.pdf"
    )

    assert caso.estado == OMITIDO
    assert "HOR-002.pdf" in caso.motivo


def test_f011_r12_los_omitidos_no_cuentan_como_evaluados():
    fase = ResultadoFase(
        nombre="IA1",
        casos=[
            ResultadoCaso.omitido("HOR-002", "IA1", "falta el fichero"),
            ResultadoCaso.omitido("HOR-003", "IA1", "falta el fichero"),
        ],
    )

    assert fase.evaluados == []
    assert len(fase.omitidos) == 2
    assert fase.veredicto() == NO_EVALUABLE


def test_f011_r12_un_omitido_no_impide_evaluar_al_resto():
    fase = ResultadoFase(
        nombre="IA1",
        casos=[
            ResultadoCaso.desde_discrepancias("HOR-001", "IA1", []),
            ResultadoCaso.omitido("HOR-002", "IA1", "falta el fichero"),
        ],
    )

    assert fase.veredicto() == "VERDE"
    assert len(fase.evaluados) == 1
