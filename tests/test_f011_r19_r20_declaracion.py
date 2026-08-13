# tests/test_f011_r19_r20_declaracion.py
"""F-011 · R19 y R20 — La declaración de rutas sensibles y su validador.

Una declaración muerta (patrones que ya no casan con nada) es peor que no
tenerla: el arnés imprime que protege algo que dejó de existir. Por eso el
validador exige que cada patrón case con al menos un fichero real.
"""

import json

import pytest

from harness.rutas_sensibles import (
    EXIGENCIAS,
    RUTA_DECLARACION,
    ErrorDeclaracion,
    cargar_declaracion,
    validar,
)

_DECLARACION = {
    "verificaciones": [
        {
            "nombre": "evals",
            "comando": "python -m evals.runner --con-llm --feature {feature}",
            "informe": "progress/evals_{feature}.md",
            "exigencia": "aviso",
            "exige_lineas": ["MODO: completa", "VEREDICTO: VERDE"],
            "rutas": [{"patron": "harness/*.py", "motivo": "el propio arnés"}],
        }
    ]
}


def _escribir(tmp_path, datos):
    ruta = tmp_path / "rutas_sensibles.json"
    ruta.write_text(json.dumps(datos, ensure_ascii=False), encoding="utf-8")
    return ruta


def test_f011_r19_una_declaracion_sana_se_carga(tmp_path):
    verificaciones = cargar_declaracion(_escribir(tmp_path, _DECLARACION))

    assert len(verificaciones) == 1
    verificacion = verificaciones[0]
    assert verificacion.nombre == "evals"
    assert verificacion.exigencia == "aviso"
    assert verificacion.rutas[0].patron == "harness/*.py"
    assert verificacion.rutas[0].motivo == "el propio arnés"


def test_f011_r19_las_exigencias_declarables_son_bloqueo_y_aviso():
    assert set(EXIGENCIAS) == {"bloqueo", "aviso"}


def test_f011_r19_el_comando_y_el_informe_se_resuelven_con_la_feature(tmp_path):
    verificacion = cargar_declaracion(_escribir(tmp_path, _DECLARACION))[0]

    assert verificacion.comando_para("F-011").endswith("--feature F-011")
    assert verificacion.informe_para("F-011") == "progress/evals_F-011.md"


@pytest.mark.parametrize(
    ("campo", "valor"),
    [
        ("nombre", ""),
        ("comando", ""),
        ("informe", ""),
        ("exigencia", "obligatorio"),
    ],
)
def test_f011_r20_un_campo_obligatorio_mal_puesto_falla_diciendo_cual(
    tmp_path, campo, valor
):
    datos = json.loads(json.dumps(_DECLARACION))
    datos["verificaciones"][0][campo] = valor

    with pytest.raises(ErrorDeclaracion) as error:
        cargar_declaracion(_escribir(tmp_path, datos))

    assert campo in str(error.value)


def test_f011_r20_una_verificacion_sin_rutas_no_protege_nada(tmp_path):
    datos = json.loads(json.dumps(_DECLARACION))
    datos["verificaciones"][0]["rutas"] = []

    with pytest.raises(ErrorDeclaracion) as error:
        cargar_declaracion(_escribir(tmp_path, datos))

    assert "rutas" in str(error.value)


def test_f011_r20_una_ruta_sin_motivo_falla(tmp_path):
    datos = json.loads(json.dumps(_DECLARACION))
    datos["verificaciones"][0]["rutas"] = [{"patron": "harness/*.py"}]

    with pytest.raises(ErrorDeclaracion) as error:
        cargar_declaracion(_escribir(tmp_path, datos))

    assert "motivo" in str(error.value)


def test_f011_r20_nombres_de_verificacion_duplicados_fallan(tmp_path):
    datos = json.loads(json.dumps(_DECLARACION))
    datos["verificaciones"].append(json.loads(json.dumps(datos["verificaciones"][0])))

    with pytest.raises(ErrorDeclaracion) as error:
        cargar_declaracion(_escribir(tmp_path, datos))

    assert "evals" in str(error.value)


def test_f011_r20_json_roto_falla_nombrando_el_fichero(tmp_path):
    ruta = tmp_path / "rutas_sensibles.json"
    ruta.write_text("{no soy json", encoding="utf-8")

    with pytest.raises(ErrorDeclaracion) as error:
        cargar_declaracion(ruta)

    assert "rutas_sensibles.json" in str(error.value)


def test_f011_r20_validar_exige_que_cada_patron_case_con_algo(tmp_path):
    datos = json.loads(json.dumps(_DECLARACION))
    datos["verificaciones"][0]["rutas"] = [
        {"patron": "esto/no/existe/**", "motivo": "patrón muerto"}
    ]
    verificaciones = cargar_declaracion(_escribir(tmp_path, datos))

    with pytest.raises(ErrorDeclaracion) as error:
        validar(verificaciones, raiz=".")

    assert "esto/no/existe/**" in str(error.value)


def test_f011_r20_la_declaracion_de_este_repositorio_es_sana():
    """La de verdad: si un servicio se renombra, esto salta."""
    verificaciones = cargar_declaracion(RUTA_DECLARACION)

    assert verificaciones, "harness/rutas_sensibles.json debe declarar algo"
    validar(verificaciones, raiz=".")


def test_f011_r19_la_declaracion_de_este_repositorio_arranca_en_aviso():
    """Decisión D5: se sube a `bloqueo` cuando haya ground truth rellenado."""
    verificacion = cargar_declaracion(RUTA_DECLARACION)[0]

    assert verificacion.exigencia == "aviso"
    assert verificacion.informe == "progress/evals_{feature}.md"


#: Las 14 rutas que la spec aprobada de F-011 manda declarar (R19 de
#: `requirements.md` y el esquema literal de `design.md`). Se fija el CONJUNTO,
#: no solo que la declaración sea sintácticamente sana: la primera versión
#: implementada se dejó fuera las reglas de revisión de sv5 y ningún test lo
#: notó, porque una declaración a la que le falta una ruta sigue siendo válida.
#: Quitar o añadir una ruta es una decisión, y una decisión se escribe aquí.
RUTAS_DE_LA_SPEC: frozenset[str] = frozenset(
    {
        "services/albaranes-api/config/prompts/**",
        "services/albaranes-api/config/prompts.yaml",
        "services/albaranes-api/config/revision_rules.yaml",
        "services/albaranes-api/domain/models/**",
        "services/albaranes-api/infrastructure/llm/**",
        "services/albaran-valoracion-api/config/prompts/**",
        "services/albaran-valoracion-api/config/prompts.yaml",
        "services/albaran-valoracion-api/config/revision_rules.yaml",
        "services/albaran-valoracion-api/domain/models/**",
        "services/albaran-valoracion-api/infrastructure/llm/**",
        "services/albaran-valoracion-persist/application/services/**",
        "services/albaran-valoracion-persist/domain/models/**",
        "services/albaran-valoracion-persist/config/unit_registry.yaml",
        "services/albaranes-comun/ruesma_comun/llm/**",
    }
)


def test_f011_r19_la_declaracion_cubre_las_rutas_de_la_spec():
    """El conjunto declarado es exactamente el de la spec: ni una menos."""
    verificacion = cargar_declaracion(RUTA_DECLARACION)[0]
    declaradas = {ruta.patron for ruta in verificacion.rutas}

    assert declaradas == RUTAS_DE_LA_SPEC, (
        f"faltan: {sorted(RUTAS_DE_LA_SPEC - declaradas)} · "
        f"sobran: {sorted(declaradas - RUTAS_DE_LA_SPEC)}"
    )


def test_f011_r19_cada_ruta_declarada_explica_por_que_es_sensible():
    """Sin motivo, el KO de la puerta no le dice nada a quien lo lee."""
    verificacion = cargar_declaracion(RUTA_DECLARACION)[0]

    assert len(verificacion.rutas) == 14
    assert all(len(ruta.motivo) > 10 for ruta in verificacion.rutas)
