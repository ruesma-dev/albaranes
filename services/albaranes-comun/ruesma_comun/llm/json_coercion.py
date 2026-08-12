# ruesma_comun/llm/json_coercion.py
"""Coercion defensiva del JSON que devuelven los LLM.

Problema real (jul 2026): algunos modelos (visto en claude-sonnet-5, pero
puede pasarle a cualquiera) devuelven un campo que DEBE ser lista/objeto
como un STRING que contiene el JSON:

    {"lineas": "[{\\"merge_line_id\\": 50, ...}]"}   <-- string, no lista
    {"lineas": [{"merge_line_id": 50, ...}]}          <-- correcto

Pydantic (schema estricto) rechaza el primero con:
    "lineas: Input should be a valid list [type=list_type ... input_type=str]"

y la peticion muere con 400, aunque el contenido sea perfectamente valido.

SEGUNDO CASO (jul 2026): el modelo se INVENTA un campo que no existe en el
schema y lo deja a null:

    {"lineas": [{..., "line_kind_note": null}]}

Con schema estricto (extra="forbid") Pydantic tumba TODO el documento:
    "lineas.1.line_kind_note: Extra inputs are not permitted"

``sanear_para_modelo`` elimina esos campos extra CUANDO VALEN None (no
aportan nada). Si un campo extra trae valor SI se conserva: preferimos que
falle a perder informacion en silencio.

TERCER CASO (jul 2026): el modelo ENVUELVE la respuesta en una clave basura
(un placeholder de plantilla que no sustituyo):

    {"$PARAMETER_NAME": {"lineas": [...]}}   <-- envuelto
    {"lineas": [...]}                        <-- correcto

``_desenvolver`` detecta que el dict tiene UNA sola clave, que esa clave no
existe en el schema, y que su contenido SI encaja -> lo desenvuelve.

CUARTO CASO (24-jul-2026, visto en claude-opus-4-7 en Azure): el modelo
repite la clave raiz — envuelve el DOCUMENTO entero bajo el nombre de su
propio primer campo:

    {"lineas": {"lineas": [...]}}   <-- doble anidamiento
    {"lineas": [...]}               <-- correcto

La rama original NO actuaba porque la clave envolvente SI es un campo del
schema. Sintoma en produccion: sv5 devolvia 400 "lineas: Input should be
a valid list [input_type=dict]" con la valoracion PERFECTA dentro, y sv6
cerraba el documento como failed con 0 lineas. En local no se veia porque
alli corria claude-sonnet-4-6, que no envuelve.

QUINTO CASO (24-jul-2026, tarde, claude-opus-4-7): el modelo INVENTA
campos CON VALOR — vimos ``"line_index": 1`` en cada linea. La poda
general solo descarta extras a None (para no perder informacion), pero
hay campos-basura CONOCIDOS cuyo valor es redundante por construccion
(line_index = posicion en la lista): esos se descartan siempre, con
aviso. Lista blanca: ``_EXTRAS_BASURA_CONOCIDOS``.

SEXTO CASO (24-jul-2026, tarde, claude-opus-4-7): sinteticas SIN
``descripcion_linea`` (obligatoria). El validador tumbaba el DOCUMENTO
entero por una linea coja. ``_reparar_lineas`` la rescata con el propio
texto del modelo (modifier_reason / razon_corta, recortado) y, si no
hay nada con que rellenarla, ELIMINA esa linea (con warning): mejor
perder una sintetica invalida que perder la valoracion completa. Ambos
casos eran intermitentes: el mismo documento fallaba y pasaba en
reintentos, tipico de la variabilidad del modelo.

Esta funcion recorre el dict de forma recursiva y, cuando un valor es un
string que "parece" JSON (empieza por ``[`` o ``{``), intenta parsearlo. Si
parsea, sustituye el string por el objeto real. Si no, lo deja tal cual (un
concepto que empiece por '{' seguiria intacto).

Es conservadora: NUNCA rompe un payload correcto (si ya es lista/dict, no
lo toca) y ante cualquier error deja el valor original.
"""
from __future__ import annotations

import json
import logging
from typing import Any

logger = logging.getLogger(__name__)

# Profundidad maxima de "desempaquetado" de strings anidados (por si el
# modelo hace doble encoding: "\"[{...}]\"").
_MAX_DESANIDADO = 3

# Campos que los modelos INVENTAN con valor y cuyo contenido es
# redundante por construccion: se descartan aunque traigan valor.
# (line_index: la posicion en la lista YA es el indice; visto en
# claude-opus-4-7 el 24-jul-2026.)
_EXTRAS_BASURA_CONOCIDOS = frozenset({"line_index"})


def _parece_json(texto: str) -> bool:
    t = texto.strip()
    return len(t) >= 2 and (
        (t.startswith("[") and t.endswith("]"))
        or (t.startswith("{") and t.endswith("}"))
    )


def _desempaquetar(valor: Any, ruta: str) -> Any:
    """Si el valor es un string con JSON dentro, lo convierte."""
    actual = valor
    for _ in range(_MAX_DESANIDADO):
        if not isinstance(actual, str):
            break
        texto = actual.strip()
        if _parece_json(texto):
            try:
                decodificado = json.loads(texto)
            except (ValueError, TypeError):
                break
        elif len(texto) >= 2 and texto[0] == '"' and texto[-1] == '"':
            # Doble encoding: '"[{...}]"'. Solo lo aceptamos si al
            # decodificar sale OTRO string que SI parece JSON; asi un
            # texto normal entrecomillado ("hola") queda intacto.
            try:
                interno = json.loads(texto)
            except (ValueError, TypeError):
                break
            if not (isinstance(interno, str) and _parece_json(interno)):
                break
            decodificado = interno
        else:
            break
        logger.warning(
            "[json-coercion] campo %r venia como STRING con JSON dentro; "
            "se convierte a %s (bug de serializacion del LLM).",
            ruta,
            type(decodificado).__name__,
        )
        actual = decodificado
    return actual


def coercionar_json_llm(dato: Any, ruta: str = "$") -> Any:
    """Devuelve el dato con los strings-JSON convertidos, recursivamente."""
    dato = _desempaquetar(dato, ruta)

    if isinstance(dato, dict):
        return {
            clave: coercionar_json_llm(valor, f"{ruta}.{clave}")
            for clave, valor in dato.items()
        }
    if isinstance(dato, list):
        return [
            coercionar_json_llm(item, f"{ruta}[{i}]")
            for i, item in enumerate(dato)
        ]
    return dato


def sanear_para_modelo(dato: Any, response_model: Any) -> Any:
    """Coerciona + elimina campos EXTRA a None que el schema no acepta.

    Solo actua si el modelo Pydantic prohibe extras (``extra="forbid"``),
    que es el caso de los schemas estrictos de albaranes. Recorre en
    paralelo el dato y los campos del modelo, y descarta las claves
    desconocidas cuyo valor sea ``None``.
    """
    dato = coercionar_json_llm(dato)
    dato = _desenvolver(dato, response_model)
    # Reparar DESPUES de desenvolver: con doble envoltura, 'lineas' aun
    # no es una lista hasta quitar la capa exterior (test del 24-jul).
    dato = _reparar_lineas(dato, response_model)
    try:
        return _podar(dato, response_model, "$")
    except Exception as exc:  # noqa: BLE001 - best-effort
        logger.warning(
            "[json-coercion] no se pudo podar campos extra (%s); se "
            "valida el dato tal cual.",
            exc,
        )
        return dato


def _reparar_lineas(dato: Any, response_model: Any) -> Any:
    """Rescata sinteticas sin ``descripcion_linea`` (claude-opus-4-7).

    Solo actua si el schema tiene un campo ``lineas`` y el dato lo trae
    como lista de dicts. Para cada linea ``synthetic_modifier`` sin
    descripcion: 1) la rellena con modifier_reason / razon_corta
    (texto del PROPIO modelo, recortado a 120); 2) si no hay nada con
    que rellenar, ELIMINA la linea. En ambos casos, warning con la
    posicion. Cualquier otra forma se devuelve intacta.
    """
    campos = getattr(response_model, "model_fields", None)
    if (
        not isinstance(dato, dict)
        or not campos
        or "lineas" not in campos
        or not isinstance(dato.get("lineas"), list)
    ):
        return dato

    reparadas: list[Any] = []
    for i, linea in enumerate(dato["lineas"]):
        if not isinstance(linea, dict):
            reparadas.append(linea)
            continue
        es_sintetica = linea.get("line_kind") == "synthetic_modifier"
        desc = linea.get("descripcion_linea")
        desc_vacia = desc is None or (
            isinstance(desc, str) and not desc.strip()
        )
        if not (es_sintetica and desc_vacia):
            reparadas.append(linea)
            continue
        sustituto = None
        for origen in ("modifier_reason", "razon_corta"):
            v = linea.get(origen)
            if isinstance(v, str) and v.strip():
                sustituto = v.strip()[:120]
                break
        if sustituto:
            logger.warning(
                "[json-coercion] lineas[%s] sintetica SIN "
                "descripcion_linea; se rellena con el propio texto "
                "del modelo: %r",
                i, sustituto,
            )
            linea = dict(linea)
            linea["descripcion_linea"] = sustituto
            reparadas.append(linea)
        else:
            logger.warning(
                "[json-coercion] lineas[%s] sintetica SIN "
                "descripcion_linea NI texto con que rellenarla; se "
                "ELIMINA para no tumbar el documento entero. "
                "Contenido: %r",
                i, {k: str(v)[:40] for k, v in linea.items()},
            )
    dato = dict(dato)
    dato["lineas"] = reparadas
    return dato


def _forbid_extras(modelo: Any) -> bool:
    cfg = getattr(modelo, "model_config", None)
    if isinstance(cfg, dict):
        return cfg.get("extra") == "forbid"
    return False


def _podar(dato: Any, modelo: Any, ruta: str) -> Any:
    campos = getattr(modelo, "model_fields", None)
    if not isinstance(dato, dict) or not campos:
        return dato

    limpio: dict[str, Any] = {}
    for clave, valor in dato.items():
        campo = campos.get(clave)
        if campo is None:
            # Clave desconocida para el schema.
            if clave in _EXTRAS_BASURA_CONOCIDOS and _forbid_extras(modelo):
                logger.warning(
                    "[json-coercion] campo basura conocido %r=%r; se "
                    "DESCARTA aunque traiga valor (redundante por "
                    "construccion).",
                    f"{ruta}.{clave}",
                    valor,
                )
                continue
            if valor is None and _forbid_extras(modelo):
                logger.warning(
                    "[json-coercion] campo %r no existe en %s y vale None; "
                    "se DESCARTA (el LLM se lo invento).",
                    f"{ruta}.{clave}",
                    getattr(modelo, "__name__", "?"),
                )
                continue
            limpio[clave] = valor
            continue

        # Campo conocido: bajar recursivamente si es submodelo o lista.
        sub = _submodelo(campo)
        if sub is not None:
            if isinstance(valor, list):
                limpio[clave] = [
                    _podar(v, sub, f"{ruta}.{clave}[{i}]")
                    for i, v in enumerate(valor)
                ]
            else:
                limpio[clave] = _podar(valor, sub, f"{ruta}.{clave}")
        else:
            limpio[clave] = valor
    return limpio


def _submodelo(campo: Any) -> Any:
    """Modelo Pydantic anidado de un FieldInfo (directo, List[X] u Optional)."""
    from typing import get_args

    candidatos = [getattr(campo, "annotation", None)]
    candidatos += list(get_args(getattr(campo, "annotation", None)) or ())
    for c in candidatos:
        for cc in [c] + list(get_args(c) or ()):
            if hasattr(cc, "model_fields"):
                return cc
    return None


def _desenvolver(dato: Any, response_model: Any) -> Any:
    """Quita capas de envoltorio del documento.

    Rama A — clave basura: ``{"$PARAM": {...}}``. El dict tiene UNA sola
    clave, esa clave NO es un campo del schema, y su valor es un dict que
    SI contiene algun campo del schema.

    Rama B — clave raiz repetida (claude-opus-4-7, 24-jul-2026):
    ``{"lineas": {"lineas": [...]}}``. El dict tiene UNA sola clave, esa
    clave SI es campo del schema, su valor es un dict, y ese dict vuelve
    a contener LA MISMA clave: la capa exterior sobra. Exigir la
    repeticion literal de la clave evita tocar un campo-objeto legitimo.

    Se aplica en bucle (hasta 3 capas) por si el modelo anida doble.
    Conservadora: cualquier otra forma se devuelve intacta.
    """
    campos = getattr(response_model, "model_fields", None)
    if not campos:
        return dato

    for _ in range(3):
        if not isinstance(dato, dict) or len(dato) != 1:
            return dato
        clave, valor = next(iter(dato.items()))
        if not isinstance(valor, dict):
            return dato

        if clave not in campos:
            # Rama A: envoltorio basura.
            if not any(k in campos for k in valor):
                return dato
            logger.warning(
                "[json-coercion] respuesta ENVUELTA en la clave basura "
                "%r (placeholder no sustituido por el LLM); se "
                "desenvuelve.",
                clave,
            )
            dato = valor
            continue

        if clave in valor:
            # Rama B: el documento entero envuelto bajo su propio campo.
            logger.warning(
                "[json-coercion] respuesta con la clave raiz %r "
                "REPETIDA (documento doblemente anidado, visto en "
                "claude-opus-4-7); se quita la capa exterior.",
                clave,
            )
            dato = valor
            continue

        return dato
    return dato
