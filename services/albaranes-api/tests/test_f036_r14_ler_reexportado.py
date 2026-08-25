# tests/test_f036_r14_ler_reexportado.py
"""F-036 R14 · sv2 consume el catalogo LER de `ruesma_comun`, sin copia.

El catalogo (Decision 2014/955/UE) y su validador se movieron a
`ruesma_comun.ler` porque sv5 tambien los necesita (R13). En sv2 queda
SOLO la reexportacion, para no romper a quien importa desde
`domain.models.tipologia`.

El contrato de comportamiento del catalogo vive en
`services/albaranes-comun/tests/test_f036_r14_ler.py`; aqui se comprueba
lo unico que sv2 puede comprobar: que no hay una segunda implementacion.
"""
from __future__ import annotations

from domain.models import tipologia as tipologia_sv2


def test_f036_r14_sv2_reexporta_la_misma_funcion_no_una_copia():
    """La reexportacion debe ser EL MISMO objeto que el de comun.

    Si sv2 volviera a definir su propia `es_ler_valido`, este test
    seria el que lo cazara: dos implementaciones del catalogo LER es
    justo lo que R14 prohibe.
    """
    from ruesma_comun import ler as ler_comun

    assert tipologia_sv2.es_ler_valido is ler_comun.es_ler_valido
    assert tipologia_sv2.texto_contiene_ler is ler_comun.texto_contiene_ler
    assert tipologia_sv2.normalizar_ler is ler_comun.normalizar_ler


def test_f036_r14_el_resolver_de_tipologia_sigue_funcionando():
    """`tipologia_resolver` no cambia: importa donde importaba."""
    from application.services.tipologia_resolver import resolver_tipologia

    assert resolver_tipologia is not None
