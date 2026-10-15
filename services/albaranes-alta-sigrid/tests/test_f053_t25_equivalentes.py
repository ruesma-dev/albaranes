# tests/test_f053_t25_equivalentes.py
"""F-053 · T25 · RM5 (review fase 2): demostración EJECUTABLE de los
equivalentes de sv9 de ``progress/mutacion_F-053.md`` (#1 a #7).

Patrón de F-048 (``7b8adab``), diferencial: se carga el módulo REAL, se fabrica
su variante mutada sustituyendo el texto de la línea y se comparan las salidas
de las dos sobre un dominio amplio. Cada grupo lleva un CONTROL no equivalente
que sí se detecta (la comparación no es ciega).

Las dos versiones salen de la MISMA fuente normalizada: si una campaña ha
inyectado uno de estos equivalentes en el propio fichero, primero se devuelve
la línea a su forma original y después se fabrican original, mutante y control.
Así el test sigue comparando original contra mutante y el equivalente no sale
muerto por leer su propia fuente (RM3 de F-048). Si alguien reescribe la línea
y no queda ninguna de las formas conocidas, el test falla: la justificación hay
que rehacerla.
"""
from __future__ import annotations

import itertools
import random
import sys
import types
from pathlib import Path

import pytest

import application.alta_sigrid_service as servicio_mod
import domain.services.validador_alta as validador_mod
import infrastructure.database.sql_alta_repository as repo_mod
from domain.models.alta_models import (
    AccionAlta,
    AltaActual,
    ErrorAlta,
    EstadoAlta,
    ModoAlta,
    PeticionAlbaran,
    RespuestaAlta,
    ResultadoAdjunto,
    TipoFallo,
)
from domain.services.validador_alta import validar_y_construir
from tests.f053_datos import CONFIG, USU, HOY, datos, sin_vincular, vinculada
from tests.f053_fakes import (
    AHORA,
    DESDE,
    ESPERA,
    PdfFalso,
    RepoFalso,
    SigridFalso,
    previa_ok,
)


def fuente_normalizada(modulo: types.ModuleType,
                       *lineas: tuple[str, tuple[str, ...]]) -> str:
    """La fuente del módulo con cada línea en su forma original (deshace un
    equivalente que una campaña haya inyectado en el fichero)."""
    fuente = Path(modulo.__file__).read_text(encoding="utf-8")
    for original, equivalentes in lineas:
        for mutado in equivalentes:
            fuente = fuente.replace(mutado, original)
        assert fuente.count(original) == 1, "la línea cambió: rehacer la justificación"
    return fuente


def cargar(modulo: types.ModuleType, fuente: str, *cambios: tuple[str, str]) -> types.ModuleType:
    """Ejecuta ``fuente`` (con ``cambios`` aplicados) como un módulo aparte."""
    for de, a in cambios:
        assert fuente.count(de) == 1, f"no está (o se repite): {de!r}"
        fuente = fuente.replace(de, a)
    nombre = f"{modulo.__name__}__variante_{abs(hash(fuente))}"
    nuevo = types.ModuleType(nombre)
    nuevo.__file__ = modulo.__file__
    sys.modules[nombre] = nuevo  # dataclasses mira el módulo de la clase
    try:
        exec(compile(fuente, modulo.__file__, "exec"), nuevo.__dict__)  # noqa: S102
    finally:
        sys.modules.pop(nombre, None)
    return nuevo


# =================================================================== #
# #1 · alta_sigrid_service.py:327 · ``paso.en_vuelo = False`` -> ``True``
# =================================================================== #
D = datos(vinculada(1), sin_vincular(2))


def _peticion() -> PeticionAlbaran:
    return validar_y_construir(D, CONFIG, HOY, USU)


class _RepoQueFallaEnElAdjunto(RepoFalso):
    """Falla al guardar el SEGUNDO ``registrado`` (el del adjunto)."""

    def __init__(self) -> None:
        super().__init__()
        self._registrados = 0

    def guardar(self, document_id, resultado, *, ahora) -> None:
        if resultado.estado is EstadoAlta.REGISTRADO:
            self._registrados += 1
            if self._registrados == 2:
                raise RuntimeError("BBDD caída al guardar el adjunto")
        super().guardar(document_id, resultado, ahora=ahora)


def _escenarios():
    peticion = _peticion()
    previas = {
        "previsto": previa_ok(peticion),
        "idempotente": previa_ok(peticion, estado="idempotente", con_ide=5, cod="AC26/5"),
        "distinta": previa_ok(peticion, totales={"1": 1.0}),
        "rechazo": ErrorAlta(tipo=TipoFallo.RECHAZO, status=400, codigo="obra_ambigua"),
        "servidor": ErrorAlta(tipo=TipoFallo.SERVIDOR, status=503),
        "lanza": None,
    }
    grabaciones = {
        "creado": previa_ok(peticion, estado="creado", con_ide=9, cod="AC26/9"),
        "idempotente": previa_ok(peticion, estado="idempotente", con_ide=9, cod="AC26/9"),
        "previsto": previa_ok(peticion),
        "raro": RespuestaAlta(estado="raro"),
        "rechazo": ErrorAlta(tipo=TipoFallo.RECHAZO, status=400, codigo="colision_de_clave"),
        "tiempo": ErrorAlta(tipo=TipoFallo.TIEMPO_AGOTADO),
        "lanza": None,
    }
    adjuntos = ("colgado", "no_colgado", "lanza", "sin_pdf")
    repos = ("bien", "falla_adjunto", "falla_registrado", "falla_incierto")
    altas = (None, AltaActual(estado=EstadoAlta.INCIERTO, peticion=peticion.a_dict(),
                              ultimo_intento_at_utc=AHORA.replace(year=2025)))
    return list(itertools.product(
        (ModoAlta.SIMULACION, ModoAlta.REAL), previas.items(), grabaciones.items(), adjuntos,
        repos, altas,
    ))


def _ejecutar(modulo, escenario):
    modo, (n_previa, previa), (n_grab, grabacion), adjunto, n_repo, alta = escenario
    sigrid = SigridFalso(previa=previa, grabacion=grabacion,
                         adjunto=ResultadoAdjunto(adjunto == "colgado", gra_ide=7,
                                                  codigo=None if adjunto == "colgado" else "x"))
    if n_previa == "lanza":
        sigrid.fallar_en.add("previa")
    if n_grab == "lanza":
        sigrid.fallar_en.add("grabacion")
    if adjunto == "lanza":
        sigrid.fallar_en.add("adjuntar_pdf")
    repo = _RepoQueFallaEnElAdjunto() if n_repo == "falla_adjunto" else RepoFalso()
    if n_repo == "falla_registrado":
        repo.fallar_al_guardar = {EstadoAlta.REGISTRADO}
    if n_repo == "falla_incierto":
        repo.fallar_al_guardar = {EstadoAlta.INCIERTO, EstadoAlta.REGISTRADO}
    doc = repo.anadir(D, alta=alta)
    servicio = modulo.AltaSigridService(
        repo=repo, sigrid=sigrid, pdf=PdfFalso(sin_ruta=adjunto == "sin_pdf"), config=CONFIG, usuario_respaldo=USU,
        modo=modo, desde=DESDE, espera=ESPERA, tolerancia_eur=0.05,
        avisos_bloqueantes=frozenset({"producto_sin_historico"}), reloj=lambda: AHORA,
    )
    resultado = servicio.procesar(doc, AccionAlta.ALTA)
    return (
        resultado.decision, resultado.estado, resultado.motivo,
        [(r.estado, r.adjunto_estado, tuple(m.codigo for m in r.motivos)) for _, r in repo.guardados],
        sigrid.operaciones(),
    )


def test_f053_t25_rm5_equivalente_1_en_vuelo_tras_registrar():
    escenarios = _escenarios()
    tras_registrar = "        self._guardar(document_id, paso, resultado)\n        paso.en_vuelo = "
    original, equivalente = tras_registrar + "False\n", tras_registrar + "True\n"
    fuente = fuente_normalizada(servicio_mod, (original, (equivalente,)))
    base = cargar(servicio_mod, fuente)
    mutado = cargar(servicio_mod, fuente, (original, equivalente))
    # Control NO equivalente: la grabación ya no cuenta como «en vuelo» (R9).
    control = cargar(servicio_mod, fuente, ("        paso.en_vuelo = True\n        grabada",
                                            "        paso.en_vuelo = False\n        grabada"))
    discrepancias = sum(_ejecutar(base, e) != _ejecutar(mutado, e) for e in escenarios)
    detectadas = sum(_ejecutar(base, e) != _ejecutar(control, e) for e in escenarios)
    assert len(escenarios) == 2688
    assert discrepancias == 0
    assert detectadas > 0


# =================================================================== #
# #2, #3 · validador_alta.py:140 · clave de orden de las líneas manuales
# =================================================================== #
_ORDEN = "        return (1, linea.id, 0)\n"
_ORDEN_EQUIVALENTES = ("        return (2, linea.id, 0)\n", "        return (1, linea.id, 1)\n")


def _lote(azar: random.Random):
    ids = azar.sample(range(1, 400), azar.randint(1, 8))
    lineas = []
    for id_ in ids:
        tipo = azar.choice(("merge", "manual", "merge_sin_indice"))
        lineas.append(sin_vincular(
            id_,
            merge_line_id=None if tipo == "manual" else id_ + 1000,
            line_index=azar.randint(0, 50) if tipo == "merge" else None,
            importe_calculado=azar.choice((10.0, -3.5, 0.0, None, 1e-12, 0.01)),
        ))
    azar.shuffle(lineas)
    return datos(*lineas)


@pytest.mark.parametrize("mutado", _ORDEN_EQUIVALENTES, ids=["equivalente_2", "equivalente_3"])
def test_f053_t25_rm5_equivalentes_2_y_3_orden_de_las_manuales(mutado):
    fuente = fuente_normalizada(validador_mod, (_ORDEN, _ORDEN_EQUIVALENTES))
    base = cargar(validador_mod, fuente)
    variante_m = cargar(validador_mod, fuente, (_ORDEN, mutado))
    # Control NO equivalente: las manuales primero.
    control = cargar(validador_mod, fuente, (_ORDEN, "        return (-1, linea.id, 0)\n"))
    azar = random.Random(53)
    lotes = [_lote(azar) for _ in range(3000)]

    def orden(modulo, lote):
        return [linea.id for linea in modulo.lineas_a_registrar(lote)]

    assert sum(orden(base, lote) != orden(variante_m, lote) for lote in lotes) == 0
    assert sum(orden(base, lote) != orden(control, lote) for lote in lotes) > 0


# =================================================================== #
# #4, #5, #6 · validador_alta.py:247 y :267 · bordes en importe 0
# =================================================================== #
_SIGNOS = "        if (cantidad > 0 and importe < 0) or (cantidad < 0 and importe > 0):\n"
_CON_SIGNO = "    con_signo = -cantidad if importe < 0 else cantidad\n"
_EQUIVALENTE_4 = _SIGNOS.replace("importe < 0)", "importe <= 0)")
_EQUIVALENTE_5 = _SIGNOS.replace("importe > 0)", "importe >= 0)")
_EQUIVALENTE_6 = _CON_SIGNO.replace("importe < 0", "importe <= 0")


@pytest.mark.parametrize("original, mutado", [
    (_SIGNOS, _EQUIVALENTE_4),
    (_SIGNOS, _EQUIVALENTE_5),
    (_CON_SIGNO, _EQUIVALENTE_6),
], ids=["equivalente_4", "equivalente_5", "equivalente_6"])
def test_f053_t25_rm5_equivalentes_4_5_6_importe_cero(original, mutado):
    fuente = fuente_normalizada(
        validador_mod, (_SIGNOS, (_EQUIVALENTE_4, _EQUIVALENTE_5)), (_CON_SIGNO, (_EQUIVALENTE_6,)),
    )
    base = cargar(validador_mod, fuente)
    variante_m = cargar(validador_mod, fuente, (original, mutado))
    # Control NO equivalente (lo mató la campaña): importe < 1 en vez de < 0.
    control = cargar(validador_mod, fuente,
                     (_SIGNOS, _SIGNOS.replace("importe < 0)", "importe < 1)")))
    valores = (None, 0.0, -0.0, 1e-12, -1e-12, 1e-9, -1e-9, 0.5, -0.5, 1.0, -1.0, 10.0, -10.0)
    casos = []
    for cantidad, importe in itertools.product(valores, valores):
        for linea in (
            sin_vincular(1, cantidad_albaran=cantidad, importe_calculado=importe),
            vinculada(1, cantidad_convertida=cantidad, importe_calculado=importe),
        ):
            casos.append(datos(linea, sin_vincular(2)))

    def salida(modulo, caso):
        resultado = modulo.validar_y_construir(caso, CONFIG, HOY, USU)
        return resultado if isinstance(resultado, list) else resultado.a_dict()

    assert len(casos) == 338
    assert sum(salida(base, c) != salida(variante_m, c) for c in casos) == 0
    assert sum(salida(base, c) != salida(control, c) for c in casos) > 0


# =================================================================== #
# #7 · sql_alta_repository.py:162 · ``or`` -> ``and`` en ``_json``
# =================================================================== #
def test_f053_t25_rm5_equivalente_7_json_vacio():
    original = '    if valor is None or valor == "":\n'
    equivalente = original.replace(" or ", " and ")
    fuente = fuente_normalizada(repo_mod, (original, (equivalente,)))
    base = cargar(repo_mod, fuente)
    mutado = cargar(repo_mod, fuente, (original, equivalente))
    entradas = [None, "", " ", "0", "null", "[]", "{}", '{"a": 1}', "[1, 2]", "{roto", "\x00",
                b"", b"[]", 0, 1.5, [], {}, "\"texto\"", "true"]
    defectos = [None, [], {}, "d"]

    def salida(modulo, valor, defecto):
        try:
            return ("ok", modulo._json(valor, defecto))
        except Exception as exc:  # noqa: BLE001 — también se compara la excepción
            return ("lanza", type(exc).__name__)

    casos = list(itertools.product(entradas, defectos))
    assert sum(salida(base, v, d) != salida(mutado, v, d) for v, d in casos) == 0

    # Control NO equivalente: el mismo ``and`` sin capturar el ValueError de "".
    control_doble = cargar(
        repo_mod, fuente, (original, equivalente),
        ("    except (TypeError, ValueError):\n        return defecto\n",
         "    except TypeError:\n        return defecto\n"),
    )
    assert sum(salida(base, v, d) != salida(control_doble, v, d) for v, d in casos) > 0
