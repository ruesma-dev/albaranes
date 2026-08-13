# tests/test_f011_r4_barrido.py
"""F-011 · R4 — Barrido de datos sensibles integrado en el conversor.

El barrido usa los patrones de C3 bis (correos, IPs, GUIDs, credenciales,
tokens). Precios, razones sociales y CIF NO son patrones del barrido: son el
ground truth y se versionan (decisión D1).
"""

from evals.barrido import PATRONES, barrer


def test_f011_r4_detecta_correo_electronico():
    hallazgos = barrer("Contacto: pedidos@proveedor-hormigones.es para dudas")

    assert [h.patron for h in hallazgos] == ["correo"]
    assert "pedidos@proveedor-hormigones.es" in hallazgos[0].fragmento


def test_f011_r4_detecta_ip():
    hallazgos = barrer("Servidor interno 10.140.22.7 del almacén")

    assert [h.patron for h in hallazgos] == ["ip"]
    assert hallazgos[0].fragmento == "10.140.22.7"


def test_f011_r4_detecta_guid_de_suscripcion_o_tenant():
    hallazgos = barrer("tenant 3f2504e0-4f89-11d3-9a0c-0305e82c3301 de Azure")

    assert [h.patron for h in hallazgos] == ["guid"]


def test_f011_r4_detecta_credencial_declarada():
    hallazgos = barrer("password: loQueSea; AccountKey=abc")

    patrones = {h.patron for h in hallazgos}
    assert "credencial" in patrones


def test_f011_r4_detecta_token_largo():
    hallazgos = barrer("Authorization sk-abcdefghijklmnopqrstuvwxyz0123456789ABCDEF")

    patrones = {h.patron for h in hallazgos}
    assert "token" in patrones


def test_f011_r4_precios_razones_sociales_y_cif_no_disparan():
    """Decisión D1: el ground truth se versiona, no lo bloquea el barrido."""
    texto = (
        "HORMIGONES DEL NORTE S.L. | CIF B12345678 | HA-25/B/20/IIa | "
        "precio 72,50 €/m3 | importe 1.234,56 | fecha 2026-08-13 | "
        "partida 01.02.03 | LER 170504"
    )

    assert barrer(texto) == []


def test_f011_r4_el_hallazgo_identifica_donde_esta():
    hallazgos = barrer("correo@dominio.es", ubicacion="IA1_extraccion.xlsx!Hormigon!C4")

    assert hallazgos[0].ubicacion == "IA1_extraccion.xlsx!Hormigon!C4"


def test_f011_r4_valor_no_textual_no_rompe_el_barrido():
    assert barrer(None) == []
    assert barrer(1234.56) == []


def test_f011_r4_los_patrones_declarados_son_los_de_c3_bis():
    assert {nombre for nombre, _ in PATRONES} == {
        "correo",
        "ip",
        "guid",
        "credencial",
        "token",
    }
