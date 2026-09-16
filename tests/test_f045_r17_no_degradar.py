# tests/test_f045_r17_no_degradar.py
"""F-045 · R17: un valor afirmado NO puede degradarse a `?` en silencio.

El 2026-09-16 se perdieron **38 valores afirmados** de los 7 casos RES —el
número de albarán, el `match_method` semántico, el `codigo_producto_contrato`,
la línea de contrato, el `requiere_revision`— y **no lo vio nadie**: la
comprobación de entonces miró un campo de tres casos y dio por bueno el resto.
Los encontró el reviewer comparando fixture a fixture.

Con `?` esos campos no salen rojos: **dejan de mirarse**. Y lo que dejaban de
mirar era justo que la valoración elige el producto correcto del contrato, que
es el patrón 5 del humano —la tarifa parecida pero equivocada—. Un banco que
deja de mirar sin decirlo es peor que no tener banco.

Los libros `.xlsx` no se versionan, así que un `git diff` no avisa. De ahí esta
instantánea versionada: lo que el humano afirmó, campo a campo. Si un valor
desaparece o se degrada, este test lo dice **con su nombre**.

Cuando el cambio sea LEGÍTIMO —el humano corrige su ground truth— se regenera
la instantánea y el diff enseña exactamente qué cambió, que es justo lo que
faltaba.
"""

from __future__ import annotations

import json
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
INSTANTANEA = RAIZ / "tests" / "datos" / "afirmado_por_el_humano_RES.json"
FIXTURES = RAIZ / "evals" / "fixtures"

NO_COMPARAR = "@@NO_COMPARAR@@"

#: Cómo se identifica una fila dentro de su tabla (igual que `escritura.py`).
CLAVES: dict[str, tuple[str, ...]] = {
    "cabeceras": ("caso_id",),
    "lineas": ("caso_id", "num_linea"),
    "contexto": ("caso_id", "num_linea", "campo_contexto"),
    "lineas_valoradas": ("caso_id", "num_linea"),
    "sinteticas_esperadas": ("caso_id", "num_linea_base", "descripcion_esperada"),
    "sinteticas_prohibidas": ("caso_id", "concepto_vetado"),
    "conciliacion": ("caso_id", "num_linea"),
    "caso": ("caso_id",),
    "lineas_albaran": ("caso_id", "num_linea"),
    "contrato_lineas": ("caso_id", "codigo_producto"),
    "condiciones": ("caso_id", "campo"),
    "datos_generales": ("caso_id",),
    "lineas_anadidas": ("caso_id", "num_linea_base", "concepto"),
}

#: Campos laxos que el humano reescribe cada semana: vigilarlos daría rojos que
#: no dicen nada del banco.
FUERA = {"comentario", "descripcion_caso", "observaciones_albaran"}


def _afirmado(valor: object) -> bool:
    if valor is None or valor == NO_COMPARAR:
        return False
    return not (isinstance(valor, str) and not valor.strip())


def afirmados_hoy() -> dict[str, object]:
    """Los valores afirmados que hay AHORA en los fixtures de los 7 RES."""
    encontrados: dict[str, object] = {}
    for destino in ("IA1", "IA2", "IA3", "IA4", "inputs", "final"):
        for numero in range(1, 8):
            ruta = FIXTURES / destino / f"RES-{numero:03d}.json"
            if not ruta.is_file():
                continue
            datos = json.loads(ruta.read_text(encoding="utf-8"))
            for tabla, filas in datos.get("tablas", {}).items():
                claves = CLAVES[tabla]
                for fila in filas:
                    identidad = "|".join(str(fila.get(c, "")).strip() for c in claves)
                    for campo, valor in fila.items():
                        if campo in FUERA or campo in claves or not _afirmado(valor):
                            continue
                        encontrados[f"{destino}.{tabla}[{identidad}].{campo}"] = valor
    return encontrados


def instantanea() -> dict[str, object]:
    return json.loads(INSTANTANEA.read_text(encoding="utf-8"))["valores"]


# --- El guardián ------------------------------------------------------------


def test_f045_r17_ningun_valor_afirmado_ha_desaparecido():
    """El que habría cazado los 38 el primer día."""
    esperados, hoy = instantanea(), afirmados_hoy()
    perdidos = sorted(campo for campo in esperados if campo not in hoy)
    assert not perdidos, (
        f"{len(perdidos)} valor(es) afirmados por el humano han desaparecido o se "
        f"han degradado a `?`, y con `?` dejan de mirarse EN SILENCIO:\n"
        + "\n".join(f"  - {campo}: era {esperados[campo]!r}" for campo in perdidos[:25])
        + "\n\nSi el cambio es legítimo, regenera "
        f"{INSTANTANEA.relative_to(RAIZ).as_posix()} y que el diff lo enseñe."
    )


def test_f045_r17_ningun_valor_afirmado_ha_cambiado_de_valor():
    """Degradar no es lo único que se puede hacer mal: también sustituir."""
    esperados, hoy = instantanea(), afirmados_hoy()
    cambiados = sorted(
        campo for campo, valor in esperados.items()
        if campo in hoy and hoy[campo] != valor
    )
    assert not cambiados, (
        f"{len(cambiados)} valor(es) del humano han cambiado de valor:\n"
        + "\n".join(
            f"  - {campo}: {esperados[campo]!r} -> {hoy[campo]!r}" for campo in cambiados[:25]
        )
    )


def test_f045_r17_la_instantanea_cubre_los_campos_que_costaron_el_disgusto():
    """Los seis que se perdieron el 2026-09-16, por su nombre."""
    esperados = instantanea()
    assert esperados["IA1.cabeceras[RES-005].numero_albaran"] == "SS-0001977"
    assert esperados["final.datos_generales[RES-005].numero_albaran"] == "SS-0001977"
    assert esperados["IA3.lineas_valoradas[RES-001|1].match_method"] == "semantic"
    assert esperados["IA3.lineas_valoradas[RES-001|1].codigo_producto_contrato"] == "C1"
    assert esperados["final.lineas[RES-001|1].linea_contrato"] == "C1"
    assert esperados["final.datos_generales[RES-001].requiere_revision"] == "SI"


def test_f045_r17_la_instantanea_no_esta_vacia_ni_a_medias():
    """Una instantánea vacía pasaría todos los tests sin vigilar nada."""
    esperados = instantanea()
    assert len(esperados) > 400, "la instantánea se ha quedado corta: no vigila nada"
    casos = {campo.split("[")[1].split("|")[0].split("]")[0] for campo in esperados}
    assert casos == {f"RES-{n:03d}" for n in range(1, 8)}


def test_f045_r17_el_importador_no_degrada_un_valor_afirmado():
    """La otra mitad: que el código NO pueda hacerlo, no solo que no lo haya hecho."""
    from evals.revision import escritura

    existente = {"caso_id": "RES-001", "numero_albaran": "SS-0000168",
                 "match_method": "semantic", "codigo_producto_contrato": "C1"}
    nuevo = {"caso_id": "RES-001", "numero_albaran": "?", "match_method": "?",
             "codigo_producto_contrato": "?"}
    fundido = escritura.fundir(existente, nuevo)
    assert fundido["numero_albaran"] == "SS-0000168"
    assert fundido["match_method"] == "semantic"
    assert fundido["codigo_producto_contrato"] == "C1"
