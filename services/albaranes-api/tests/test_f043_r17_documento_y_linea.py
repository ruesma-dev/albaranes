# tests/test_f043_r17_documento_y_linea.py
"""F-043 · R17 · la clasificacion es del DOCUMENTO; la linea sigue afinando.

R17 tiene DOS mitades y las dos hay que fijarlas, porque romper cualquiera
de ellas deja el sistema funcionando y equivocado:

1. **La clasificacion es propiedad del DOCUMENTO.** Vive en
   `DocumentoAlbaran.clasificacion` y NO en la linea. Si manana alguien la
   declarara tambien por linea habria dos verdades sobre la misma cosa y
   la pregunta "de que es este albaran" pasaria a tener N respuestas. Lo
   que la linea hereda del documento se resuelve en LECTURA
   (`familia_efectiva`, R20/R21), no se copia dentro de la linea.

2. **`contexto_linea.tipo_familia` sigue vivo y lo rellena la fase 2.** No
   se ha sustituido por la clasificacion de documento: es el afinado por
   LINEA (una linea de transporte dentro de un albaran de residuos, el
   incremento por LER, la linea base de hormigon). Si la fase 2 dejara de
   rellenarlo, la clasificacion de documento seguiria llegando y R18 haria
   heredar a TODAS las lineas la familia del albaran: las reglas de sv6
   que distinguen base/transporte/incremento se quedarian sin su senal.

`config/prompts.yaml` es RUTA SENSIBLE: que la IA acierte con esas
instrucciones es evidencia de las evals con LLM real (T30). Lo que si se
comprueba aqui, y es lo que falla en silencio, es que el contrato y el
texto del prompt sigan pidiendo cada cosa en su sitio.

Sin red, sin BBDD y sin LLM.
"""
from __future__ import annotations

from pathlib import Path

import pytest
import yaml
from pydantic import ValidationError
from ruesma_comun.contratos import familias as cat

from domain.models.albaran_models import DocumentoAlbaran, LineaAlbaran
from domain.models.contexto_linea import ContextoLinea
from domain.models.revision_models import RevisionAlbaranFase2

RAIZ = Path(__file__).resolve().parents[1]
PROMPTS_REALES = RAIZ / "config" / "prompts.yaml"

_CABECERA = {"proveedor_nombre": "SALMEDINA", "numero_albaran": "SS-0003967"}
_CLASIFICACION = {
    "familia": "residuos",
    "confianza_pct": 93.0,
    "motivo": "Gestor autorizado de RCD, codigos LER y contenedores.",
}


def _prompts_reales() -> dict:
    return yaml.safe_load(PROMPTS_REALES.read_text(encoding="utf-8"))


def _claves_fase2_con_familia() -> tuple[str, ...]:
    """Las claves de fase 2 que el catalogo enruta por familia.

    Se derivan del catalogo (R3), no de una lista escrita a mano: son las
    que particularizan una familia y, por tanto, las que tienen algo que
    afinar por linea. El generico (`albaran_revision_fase2_es`) queda
    fuera a proposito: no particulariza ninguna familia.
    """
    claves = set()
    for id_familia in cat.familias_documento():
        clave = cat.prompt_fase2_de(id_familia)
        if clave:
            claves.add(clave)
    return tuple(sorted(claves))


# ------------------------------------------------------------------ #
# Mitad 1 — la clasificacion es del DOCUMENTO.
# ------------------------------------------------------------------ #
def test_f043_r17_la_clasificacion_la_declara_el_documento():
    documento = DocumentoAlbaran.model_validate(
        {
            "cabecera": _CABECERA,
            "lineas": [{"concepto": "Contenedor RCD 6 m3", "cantidad": 1}],
            "clasificacion": _CLASIFICACION,
        }
    )

    assert "clasificacion" in DocumentoAlbaran.model_fields
    assert documento.clasificacion is not None
    assert documento.clasificacion.familia == "residuos"


def test_f043_r17_la_linea_no_declara_clasificacion_propia():
    """Dos verdades sobre la misma cosa es peor que ninguna.

    `StrictSchemaModel` es `extra='forbid'`, asi que una linea con
    `clasificacion` no valida: el dia que alguien intente meterla ahi,
    revienta en la extraccion y no seis meses despues en la valoracion.
    """
    assert "clasificacion" not in LineaAlbaran.model_fields

    with pytest.raises(ValidationError):
        LineaAlbaran.model_validate(
            {"concepto": "Contenedor RCD", "clasificacion": _CLASIFICACION}
        )


def test_f043_r17_el_json_schema_pone_la_clasificacion_solo_en_el_documento():
    """Lo que se le manda al LLM dice lo mismo que el contrato.

    Si el schema la ofreciera tambien por linea, la IA la rellenaria por
    linea: el prompt puede pedir lo que quiera, pero lo que el modelo ve
    como forma valida es esto.
    """
    esquema = DocumentoAlbaran.model_json_schema()
    linea = esquema["$defs"]["LineaAlbaran"]

    assert "clasificacion" in esquema["properties"]
    assert "clasificacion" not in linea["properties"]


# ------------------------------------------------------------------ #
# Mitad 2 — la fase 2 SIGUE rellenando `contexto_linea.tipo_familia`.
# ------------------------------------------------------------------ #
def test_f043_r17_la_linea_conserva_su_tipo_familia():
    """El afinado por linea no lo ha sustituido la clasificacion."""
    assert "contexto_linea" in LineaAlbaran.model_fields
    assert "tipo_familia" in ContextoLinea.model_fields

    linea = LineaAlbaran.model_validate(
        {
            "concepto": "Contenedor 6 m3 RCD mezclados",
            "contexto_linea": {
                "tipo_familia": "residuos",
                "rol_linea": "base",
                "codigo_ler": "170604",
            },
        }
    )

    assert linea.contexto_linea.tipo_familia == "residuos"
    assert linea.contexto_linea.rol_linea == "base"
    assert linea.contexto_linea.codigo_ler == "170604"


def test_f043_r17_fase2_devuelve_las_dos_cosas_a_la_vez():
    """La de documento y la de linea conviven en `documento_revisado`.

    Es el escenario real de F-043: IA2 confirma o corrige la familia del
    ALBARAN (R16) y en la misma respuesta sigue marcando el rol de cada
    LINEA. Ninguna de las dos pisa a la otra.
    """
    revision = RevisionAlbaranFase2.model_validate(
        {
            "review_status": "ok_with_changes",
            "documento_revisado": {
                "cabecera": _CABECERA,
                "lineas": [
                    {
                        "concepto": "Contenedor RCD 6 m3",
                        "cantidad": 1,
                        "contexto_linea": {
                            "tipo_familia": "residuos",
                            "rol_linea": "base",
                        },
                    },
                    {
                        "concepto": "Portes",
                        "cantidad": 1,
                        "contexto_linea": {"rol_linea": "transporte"},
                    },
                ],
                "clasificacion": _CLASIFICACION,
            },
        }
    )
    documento = revision.documento_revisado

    assert documento.clasificacion.familia == "residuos"
    assert documento.lineas[0].contexto_linea.tipo_familia == "residuos"
    # La linea de portes NO trae familia propia: lo que la IA dijo por
    # linea se conserva tal cual y la herencia se resuelve en lectura
    # (R21). Aqui solo se comprueba que el hueco sigue siendo un hueco.
    assert documento.lineas[1].contexto_linea.tipo_familia is None


def test_f043_r17_los_prompts_de_fase2_siguen_pidiendo_el_contexto_de_linea():
    """El texto real: cada prompt de familia sigue mandando rellenarlo.

    Es la mitad de R17 que no vive en el contrato sino en el prompt: el
    schema puede admitir `contexto_linea` para siempre y la fase 2 dejar
    de rellenarlo el dia que alguien reescriba el texto pensando que la
    clasificacion de documento ya lo cubre.
    """
    prompts = _prompts_reales()
    claves = _claves_fase2_con_familia()

    assert claves  # el catalogo enruta al menos un prompt de familia
    for clave in claves:
        task = prompts[clave]["task"]
        assert "contexto_linea" in task, clave
        assert "tipo_familia" in task, clave
