# tests/test_f086_textos.py
"""F-086 · R7 y R16: lo que dicen el código de sv2 y los documentos.

Se leen los ficheros como texto: ni se importa sv2 ni se ejecuta PowerShell.
"""

from __future__ import annotations

from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
SV2 = RAIZ / "services" / "albaranes-api"


def _codigo_de_sv2() -> dict[str, str]:
    """El código Python de producción de sv2 (sin tests ni entornos virtuales)."""
    return {
        ruta.relative_to(RAIZ).as_posix(): ruta.read_text(encoding="utf-8-sig")
        for ruta in SV2.rglob("*.py")
        if not {".venv", "tests", "__pycache__"} & set(ruta.relative_to(SV2).parts)
    }


# --- R7 · sv2 sigue forzando la herramienta --------------------------------------


def test_f086_r7_hay_codigo_de_sv2_que_revisar():
    codigo = _codigo_de_sv2()
    assert "services/albaranes-api/interface_adapters/composition.py" in codigo
    assert sum("ClaudeMessagesVisionClient(" in texto for texto in codigo.values()) >= 1


@pytest.mark.parametrize("palabra", ["forzar_herramienta", "ANTHROPIC_FORZAR_HERRAMIENTA"])
def test_f086_r7_sv2_no_pasa_forzar_herramienta(palabra):
    con_la_palabra = [ruta for ruta, texto in _codigo_de_sv2().items() if palabra in texto]
    assert con_la_palabra == [], (
        f"sv2 debe seguir con el defecto de comun (herramienta forzada): {con_la_palabra}"
    )
