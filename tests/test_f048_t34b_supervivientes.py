# tests/test_f048_t34b_supervivientes.py
"""F-048 · T34 (segunda campaña) — los huecos que dejaban vivos a los mutantes de `evals/`.

La segunda campaña de mutación (`progress/mutacion_F-048.md`, HEAD `14cee8a`)
metió `evals/` en el alcance y dejó 80 supervivientes. Cada test de este
fichero cierra uno o varios; el número entre corchetes es el del superviviente
en ese informe, y el análisis completo está en
`progress/impl_F-048_T34b_supervivientes.md`.

Sin red, sin LLM, sin Azurite: dobles en todo lo que toca fuera. Lo único real
es `git` sobre este repositorio (solo lectura), como ya hacen los tests del
comparador.
"""

from __future__ import annotations

import ast
import dataclasses
import io
import json
import logging
import subprocess
import sys
import types
from pathlib import Path
from typing import ClassVar

import pydantic
import pytest
from ruesma_comun.correo import construir_contexto_correo

from evals import comparar_obra as co
from evals import correos, inyeccion, runner
from evals.modelos import ERROR, NO_EVALUABLE
from evals.procesos import errores, sv2_extraccion, sv2_obra
from evals.procesos import sv5_valoracion as sv5
from evals.procesos import sv6_build as sv6

RAIZ = Path(__file__).resolve().parent.parent


# =============================================================================
# comparar_obra.py — los informes, línea a línea [1-19]
# =============================================================================


def _ok(codigo: str) -> dict:
    return {"obra_codigo": codigo, "obra_nombre": f"Obra {codigo}"}


def _error(fase: str, tipo: str, motivo: str) -> dict:
    return {"error": {"fase": fase, "tipo": tipo, "motivo": motivo}}


def _corrida(variantes, repeticiones, resultados) -> co.Corrida:
    casos = list(resultados[variantes[0]][0])
    return co.Corrida(
        casos=casos,
        variantes=list(variantes),
        repeticiones=repeticiones,
        proveedor="gemini",
        modelo="gemini-2.5-flash",
        obras=7,
        resultados=resultados,
    )


def _corrida_dos_variantes() -> co.Corrida:
    """Un caso por categoría; el roto falla SOLO en dev r2."""
    return _corrida(
        ("dev", "rama"),
        2,
        {
            "dev": [
                {"C-IDENT": _ok("0945"), "C-DIFIERE": _ok("0945"), "C-RUIDO": _ok("0945"), "C-ROTO": _ok("0945")},
                {
                    "C-IDENT": _ok("0945"),
                    "C-DIFIERE": _ok("0945"),
                    "C-RUIDO": _ok("0950"),
                    "C-ROTO": _error("IA1", "ValueError", "ValueError: sin detalle"),
                },
            ],
            "rama": [
                {"C-IDENT": _ok("0945"), "C-DIFIERE": _ok("0950"), "C-RUIDO": _ok("0945"), "C-ROTO": _ok("0945")},
                {"C-IDENT": _ok("0945"), "C-DIFIERE": _ok("0950"), "C-RUIDO": _ok("0945"), "C-ROTO": _ok("0945")},
            ],
        },
    )


def _corrida_una_variante() -> co.Corrida:
    return _corrida(
        ("dev",),
        2,
        {"dev": [{"C-EST": _ok("1"), "C-RUIDO": _ok("1")}, {"C-EST": _ok("1"), "C-RUIDO": _ok("2")}]},
    )


def _corrida_todo_errores() -> co.Corrida:
    return _corrida(
        ("dev",),
        1,
        {"dev": [{"C-1": _error("preproceso", "SinAlbaran", "no existe el fichero del albarán de C-1")}]},
    )


COMMITS = {"rama": "abc1234", "dev": ""}
FECHA = "2026-09-25T00:00:00Z"


def _seccion(texto: str, titulo: str, siguiente: str | None) -> list[str]:
    cuerpo = texto.split(f"## {titulo}\n\n", 1)[1]
    if siguiente:
        cuerpo = cuerpo.split(f"\n\n## {siguiente}", 1)[0]
    return cuerpo.strip("\n").splitlines()


def test_f048_t34b_comparar_obra_casos_por_categoria_con_su_explicacion():
    """[1, 3, 4, 9] Cada categoría lista SUS casos, y solo el inestable y el roto llevan paréntesis."""
    corrida = _corrida_dos_variantes()
    texto = co.render_versionable(corrida, co.clasificar(corrida), COMMITS, FECHA, "salida")

    assert _seccion(texto, "Casos por categoría", None) == [
        "- **difiere**: C-DIFIERE",
        "- **inestable**: C-RUIDO (dev)",
        "- **identico**: C-IDENT",
        "- **con_errores**: C-ROTO (dev r2: IA1 · ValueError)",
    ]


def test_f048_t34b_comparar_obra_con_una_variante_el_inestable_no_lleva_parentesis():
    """[1, 2] Con una sola variante no hay «cuál de las dos»: el caso va solo."""
    corrida = _corrida_una_variante()
    texto = co.render_versionable(corrida, co.clasificar(corrida), COMMITS, FECHA, "salida")

    assert _seccion(texto, "Casos por categoría", None) == [
        "- **estable**: C-EST",
        "- **inestable**: C-RUIDO",
        "- **con_errores**: (ninguno)",
    ]


def test_f048_t34b_comparar_obra_la_cabecera_marca_el_commit_que_falta_con_interrogacion():
    """[5, 6, 7, 8] El commit ausente sale como `?`; el aviso de 1 repetición, solo con 1."""
    corrida = _corrida_dos_variantes()
    lineas = co.render_versionable(corrida, co.clasificar(corrida), COMMITS, FECHA, "s").splitlines()

    assert f"- Fecha: {FECHA} · rama `abc1234` · dev `?`" in lineas
    assert "- Estable = el mismo `obra_codigo` en todas las repeticiones (el nombre no cuenta)." in lineas

    una = _corrida_todo_errores()
    lineas_una = co.render_versionable(una, co.clasificar(una), {"rama": "", "dev": "def5678"}, FECHA, "s")
    assert f"- Fecha: {FECHA} · rama `?` · dev `def5678`" in lineas_una.splitlines()
    assert (
        "- Estable = el mismo `obra_codigo` en todas las repeticiones (el nombre no cuenta)."
        " Con 1 repetición la estabilidad no se mide."
    ) in lineas_una.splitlines()


def test_f048_t34b_comparar_obra_detalle_tabla_por_caso_con_dos_variantes():
    """[10, 11, 12, 13, 15] Una columna por variante y repetición, sí/no/— y la de «coinciden»."""
    corrida = _corrida_dos_variantes()
    detalle = co.render_detalle(corrida, co.clasificar(corrida), COMMITS, FECHA)

    assert _seccion(detalle, "Por caso", "obra_nombre leído") == [
        "| caso | dev r1 | dev r2 | rama r1 | rama r2 | dev estable | rama estable | coinciden | categoría |",
        "|---|---|---|---|---|---|---|---|---|",
        "| C-IDENT | `0945` | `0945` | `0945` | `0945` | sí | sí | sí | identico |",
        "| C-DIFIERE | `0945` | `0945` | `0950` | `0950` | sí | sí | no | difiere |",
        "| C-RUIDO | `0945` | `0950` | `0945` | `0945` | no | sí | — | inestable |",
        "| C-ROTO | `0945` | ERROR (ValueError) | `0945` | `0945` | — | sí | — | con_errores |",
    ]


def test_f048_t34b_comparar_obra_detalle_nombres_y_errores_con_su_repeticion():
    """[16, 17, 18, 19] Cada nombre y cada error con la repetición en que salió."""
    corrida = _corrida_dos_variantes()
    detalle = co.render_detalle(corrida, co.clasificar(corrida), COMMITS, FECHA)

    nombres = _seccion(detalle, "obra_nombre leído", "Errores")
    assert len(nombres) == 15
    assert "- C-RUIDO · dev r2: 'Obra 0950'" in nombres
    assert "- C-ROTO · dev r1: 'Obra 0945'" in nombres
    assert "- C-ROTO · rama r2: 'Obra 0945'" in nombres
    assert _seccion(detalle, "Errores", None) == ["- C-ROTO · dev r2: ValueError: sin detalle"]


def test_f048_t34b_comparar_obra_detalle_con_una_variante_sin_columna_coinciden():
    """[14, 19] Con una variante no hay nada que comparar entre dos: sin columna «coinciden»."""
    corrida = _corrida_una_variante()
    detalle = co.render_detalle(corrida, co.clasificar(corrida), COMMITS, FECHA)

    assert _seccion(detalle, "Por caso", "obra_nombre leído")[0] == (
        "| caso | dev r1 | dev r2 | dev estable | categoría |"
    )
    assert _seccion(detalle, "Errores", None) == ["(ninguno)"]


def test_f048_t34b_comparar_obra_detalle_sin_ningun_nombre_lo_dice():
    """[18] Si todo falló, la sección de nombres dice «(ninguno)» en vez de quedar vacía."""
    corrida = _corrida_todo_errores()
    detalle = co.render_detalle(corrida, co.clasificar(corrida), COMMITS, FECHA)

    assert _seccion(detalle, "obra_nombre leído", "Errores") == ["(ninguno)"]
    assert _seccion(detalle, "Errores", None) == ["- C-1 · dev r1: no existe el fichero del albarán de C-1"]


# =============================================================================
# comparar_obra.py — escritura de ficheros [20-25]
# =============================================================================


def test_f048_t34b_comparar_obra_escribir_crea_los_directorios_anidados(tmp_path):
    """[20, 24] `--salida` y `--resumen` pueden apuntar a directorios que aún no existen."""
    salida = tmp_path / "a" / "b" / "salida"
    resumen = tmp_path / "c" / "d" / "resumen.md"

    co.escribir(_corrida_una_variante(), salida, resumen, COMMITS, FECHA)

    assert (salida / "dev_r1.json").is_file() and (salida / "resumen.md").is_file()
    assert resumen.is_file()


def test_f048_t34b_comparar_obra_escribir_sobre_directorios_que_ya_existen(tmp_path):
    """[21, 25] Repetir una corrida en el mismo `--salida` o junto a otro resumen no revienta."""
    salida = tmp_path / "salida"
    salida.mkdir()
    resumen = tmp_path / "progress" / "resumen.md"
    resumen.parent.mkdir()

    co.escribir(_corrida_una_variante(), salida, resumen, COMMITS, FECHA)

    assert (salida / "dev_r2.json").is_file() and resumen.is_file()


def test_f048_t34b_comparar_obra_el_json_es_utf8_legible_con_sangria_2(tmp_path):
    """[22, 23] Los JSON de la corrida se abren a mano: acentos tal cual y sangría 2."""
    corrida = _corrida(
        ("rama",), 1, {"rama": [{"C-1": {"obra_codigo": "0945", "obra_nombre": "Urbanización Ñandú"}}]}
    )

    co.escribir(corrida, tmp_path / "salida", tmp_path / "r.md", COMMITS, FECHA)

    texto = (tmp_path / "salida" / "rama_r1.json").read_text(encoding="utf-8")
    assert "Urbanización Ñandú" in texto
    assert texto == json.dumps(json.loads(texto), ensure_ascii=False, indent=2)


# =============================================================================
# comparar_obra.py — commits, modelo, recuento de llamadas y CLI [26-34]
# =============================================================================


def test_f048_t34b_comparar_obra_commit_es_el_sha_corto_de_git_en_texto():
    """[26, 28, 29] El commit del informe es el `rev-parse --short` de git, como texto."""
    esperado = subprocess.run(
        ["git", "-C", str(RAIZ), "rev-parse", "--short", "HEAD"],
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()

    obtenido = co._commit("HEAD")

    assert esperado and isinstance(obtenido, str)
    assert obtenido == esperado


def test_f048_t34b_comparar_obra_commit_de_una_referencia_que_no_existe_es_vacio():
    """[27] Sin la referencia (p. ej. sin rama `dev` con `--variante rama`) no se revienta: `?`."""
    assert co._commit("referencia-que-no-existe-t34b") == ""


class _DoblesMinimos:
    def __init__(self, tmp_path: Path) -> None:
        self.tmp_path = tmp_path

    def dependencias(self) -> co.Dependencias:
        def prompt_de_dev(directorio):
            ruta = Path(directorio) / "prompts_dev.yaml"
            ruta.write_text("{}\n", encoding="utf-8")
            return ruta

        def montar(prompts, obras, proveedor, entorno):
            return lambda variante, caso_id, ruta: {"obra_codigo": "1", "obra_nombre": "n"}

        return co.Dependencias(
            prompt_de_dev=prompt_de_dev,
            prompt_de_rama=lambda: self.tmp_path / "prompts_rama.yaml",
            consultar_obras=lambda entorno: ["obra-a", "obra-b"],
            montar_extractor=montar,
        )


def _entorno(**extra) -> dict:
    base = {
        "GEMINI_API_KEY": "clave-de-mentira",
        "SIGRID_API_BASE_URL": "http://sigrid.invalid",
        "SIGRID_API_FUNCTION_KEY": "clave-de-mentira",
        "SIGRID_API_DATABASE": "bbdd-de-mentira",
    }
    base.update(extra)
    return base


def _lanzar_con_tres_casos(tmp_path, entorno):
    """C-1 y C-2 con albarán, C-3 sin él; dos variantes y tres repeticiones."""
    albaranes = tmp_path / "albaranes"
    albaranes.mkdir()
    for caso in ("C-1", "C-2"):
        (albaranes / f"{caso}.pdf").write_bytes(b"%PDF-de-mentira")
    resumen = tmp_path / "progress" / "r.md"
    codigo = co.main(
        [
            "--casos", "C-1,C-2,C-3",
            "--repeticiones", "3",
            "--albaranes", str(albaranes),
            "--salida", str(tmp_path / "salida"),
            "--resumen", str(resumen),
        ],
        entorno=entorno,
        dependencias=_DoblesMinimos(tmp_path).dependencias(),
    )
    return codigo, resumen.read_text(encoding="utf-8")


def test_f048_t34b_comparar_obra_avisa_de_cuantas_llamadas_va_a_facturar(tmp_path, capsys):
    """[30, 31, 32, 33] 2 casos con albarán × 2 variantes × 3 repeticiones = 12 llamadas."""
    codigo, resumen = _lanzar_con_tres_casos(tmp_path, _entorno())

    assert codigo == 0
    err = capsys.readouterr().err
    assert (
        "comparar_obra: 12 llamadas a gemini (gemini-2.5-flash) · 2 obras activas · variantes dev, rama"
        in err.splitlines()
    )
    assert "- IA1 (solo fase 1, sin correo): proveedor `gemini`, modelo `gemini-2.5-flash`" in resumen


def test_f048_t34b_comparar_obra_el_modelo_del_entorno_manda_sobre_el_de_por_defecto(tmp_path, capsys):
    """[30] Con `GEMINI_MODEL`, el informe dice el modelo que de verdad se usó."""
    codigo, resumen = _lanzar_con_tres_casos(tmp_path, _entorno(GEMINI_MODEL="modelo-de-prueba"))

    assert codigo == 0
    assert "12 llamadas a gemini (modelo-de-prueba)" in capsys.readouterr().err
    assert "modelo `modelo-de-prueba`" in resumen


def test_f048_t34b_comparar_obra_sin_casos_es_un_error_de_uso(tmp_path):
    """[34] `--casos` es obligatorio: sin él, código 2 de argparse y no una traza."""
    with pytest.raises(SystemExit) as salida:
        co.main([], entorno=_entorno(), dependencias=_DoblesMinimos(tmp_path).dependencias())
    assert salida.value.code == 2


# =============================================================================
# correos.py — R38 [35]
# =============================================================================


def test_f048_t34b_r38_fuera_de_un_repositorio_el_escaner_falla_en_vez_de_dar_cero(tmp_path, monkeypatch):
    """[35] Si `git ls-files` falla, el escáner NO puede responder «ningún correo versionado»."""
    fuera = tmp_path / "no_es_un_repositorio"
    fuera.mkdir()
    monkeypatch.setenv("GIT_CEILING_DIRECTORIES", str(tmp_path))

    with pytest.raises(subprocess.CalledProcessError):
        correos.versionados_con_correo(fuera)


# =============================================================================
# inyeccion.py — R16, R40, R41 y reentradas [36-42]
# =============================================================================


class _Repositorio:
    def __init__(self) -> None:
        self.llamadas: list[dict] = []

    def crear_si_no_existe(self, **kwargs):
        from ruesma_comun.workflows.repositorio import ResultadoCreacion

        self.llamadas.append(dict(kwargs))
        return ResultadoCreacion(workflow_id="wf-1", creado=True, estado_actual="email_received")


class _Almacen:
    def __init__(self) -> None:
        self.jsons: list[tuple] = []

    def put_bytes(self, contenedor, nombre, data, *, content_type=None, metadata=None):
        pass

    def put_json(self, contenedor, nombre, objeto):
        self.jsons.append((contenedor, nombre, objeto))


class _Publicador:
    def __init__(self) -> None:
        self.publicados: list[tuple] = []

    def publicar(self, cola, mensaje):
        self.publicados.append((cola, mensaje))


def _inyector(**extra) -> tuple[inyeccion.Inyector, _Repositorio, _Almacen, _Publicador]:
    repo, almacen, publicador = _Repositorio(), _Almacen(), _Publicador()
    inyector = inyeccion.Inyector(
        repositorio=repo, almacen=almacen, publicador=publicador, pasada_id="2026-09-25-01", **extra
    )
    return inyector, repo, almacen, publicador


def test_f048_t34b_r16_la_inyeccion_es_inmutable():
    """[36] Lo que quedó de meter un caso no se puede reescribir después."""
    resultado = _inyector()[0].inyectar("RES-001", b"%PDF", "RES-001.pdf")
    with pytest.raises(dataclasses.FrozenInstanceError):
        resultado.caso_id = "OTRO"


@pytest.mark.parametrize("clave", ["eval/a/b/c", "eval/a/", "eval//b", "eval/"])
def test_f048_t34b_r16_una_clave_con_partes_de_mas_o_vacias_no_es_del_banco(clave):
    """[37] Solo `eval/{pasada}/{caso}` con las dos partes: ni tres, ni una vacía."""
    assert inyeccion.partes_de_clave(clave) is None


def test_f048_t34b_r41_por_defecto_el_inyector_va_con_correo():
    """[38] Sin `--sin-correo`, el correo del caso SÍ se inyecta."""
    inyector, _, almacen, publicador = _inyector()
    correo = construir_contexto_correo("Obra 0945", "Adjunto albarán")

    resultado = inyector.inyectar("RES-001", b"%PDF", "RES-001.pdf", correo=correo)

    assert inyector.sin_correo is False
    assert resultado.correo_blob is not None
    assert len(almacen.jsons) == 1
    assert publicador.publicados[0][1].correo_blob == resultado.correo_blob


def test_f048_t34b_r40_el_payload_es_json_utf8_sin_escapar_como_el_de_sv1():
    """[39] `payload_json` se serializa con `ensure_ascii=False`, igual que en sv1 (R10)."""
    inyector, repo, _, _ = _inyector()

    inyector.inyectar("RES-001", b"%PDF", "Albarán nº 12 — Hormigón.pdf")

    payload_json = repo.llamadas[0]["payload_json"]
    assert "Albarán nº 12 — Hormigón.pdf" in payload_json
    assert payload_json == json.dumps(json.loads(payload_json), ensure_ascii=False)


def test_f048_t34b_r40_el_log_lleva_la_huella_de_ocho_caracteres(caplog):
    """[40] La huella abreviada es la misma que en sv1: 8 caracteres, ni uno más."""
    inyector, *_ = _inyector()
    correo = construir_contexto_correo("Obra 0945", "Adjunto albarán")

    with caplog.at_level(logging.INFO, logger=inyeccion.logger.name):
        inyector.inyectar("RES-001", b"%PDF", "RES-001.pdf", correo=correo)

    assert f"correo=SI(sha={correo.sha256[:8]})" in caplog.text


def test_f048_t34b_r2_una_inyeccion_nueva_no_es_un_duplicado():
    """[41] Solo el `crear_si_no_existe` que no crea marca duplicado."""
    resultado = _inyector()[0].inyectar("RES-001", b"%PDF", "RES-001.pdf")
    assert resultado.duplicado is False


def test_f048_t34b_r24_revalorar_fuerza_por_defecto():
    """[42] La revaloración del banco es la de sv4: `force=True` si no se dice otra cosa."""
    inyector, _, _, publicador = _inyector()

    inyector.republicar_valoracion("doc-1", "eval/2026-09-25-01/RES-001")

    assert publicador.publicados[0][1].force is True


# =============================================================================
# procesos/errores.py — el motivo del caso roto [50-60]
# =============================================================================

_SIN_DETALLE = "sin detalle (el texto de la excepción no se copia: puede llevar valores)"


def _excepcion_con_nombre_de(longitud: int) -> BaseException:
    """Una excepción cuyo nombre de tipo hace que el motivo mida `longitud` caracteres."""
    largo_nombre = longitud - len(f": {_SIN_DETALLE}")
    return type("E" * largo_nombre, (Exception,), {})()


def test_f048_t34b_errores_un_motivo_de_200_caracteres_no_se_recorta():
    """[58] El tope es 200 INCLUIDO: uno que mide justo eso sale entero."""
    motivo = errores.describir_error(_excepcion_con_nombre_de(200), "IA1")["motivo"]

    assert len(motivo) == 200
    assert motivo.endswith(_SIN_DETALLE)


def test_f048_t34b_errores_un_motivo_de_201_se_recorta_a_199_mas_puntos_suspensivos():
    """[50, 59, 60] Pasado el tope, 199 caracteres del motivo y «…»: 200 en total."""
    error = _excepcion_con_nombre_de(201)
    completo = f"{type(error).__name__}: {_SIN_DETALLE}"

    motivo = errores.describir_error(error, "IA1")["motivo"]

    assert len(completo) == 201
    assert motivo == completo[:199] + "…"


def test_f048_t34b_errores_avisar_vacia_el_buffer_aunque_stderr_no_sea_de_linea(monkeypatch):
    """[51] El aviso sale AL MOMENTO aunque stderr esté redirigido con buffer completo."""
    crudo = io.BytesIO()
    monkeypatch.setattr(
        sys, "stderr", io.TextIOWrapper(crudo, encoding="utf-8", newline="\n", line_buffering=False)
    )

    errores.avisar("sv2", "caso HOR-001: ok")

    assert crudo.getvalue().decode("utf-8") == "sv2: caso HOR-001: ok\n"


@pytest.mark.parametrize("atributos", [{"lineno": 3}, {"colno": 7}])
def test_f048_t34b_errores_sin_linea_y_columna_no_se_describe_como_json_roto(atributos):
    """[52] Solo con línea Y columna enteras es un JSON roto; con una sola, no hay posición."""
    error = type("Raro", (Exception,), {})()
    for nombre, valor in atributos.items():
        setattr(error, nombre, valor)

    assert errores.describir_error(error, "IA1")["motivo"] == f"Raro: {_SIN_DETALLE}"


def test_f048_t34b_errores_de_pydantic_se_piden_sin_entrada_ni_url_ni_contexto():
    """[53, 54, 55] R31 de F-047: la entrada del LLM no sale del `ValidationError`."""

    class _Modelo(pydantic.BaseModel):
        cantidad: int = pydantic.Field(gt=0)

    with pytest.raises(pydantic.ValidationError) as error:
        _Modelo.model_validate({"cantidad": -5})
    assert {"input", "url", "ctx"} <= set(error.value.errors()[0]), "el doble debe traer los tres"

    obtenidos = errores._errores_de_pydantic(error.value)

    assert [set(e) for e in obtenidos] == [{"type", "loc", "msg"}]


class _Tres(pydantic.BaseModel):
    a: int
    b: int
    c: int


class _Cuatro(_Tres):
    d: int


def test_f048_t34b_errores_con_justo_tres_errores_no_hay_resto():
    """[56] Tres errores caben enteros: nada de «(+0 más)»."""
    with pytest.raises(pydantic.ValidationError) as error:
        _Tres.model_validate({})

    assert errores.describir_error(error.value, "IA1")["motivo"] == (
        "ValidationError: missing en a; missing en b; missing en c"
    )


def test_f048_t34b_errores_con_cuatro_errores_se_resume_uno():
    """[57] El cuarto ya no se detalla: «(+1 más)»."""
    with pytest.raises(pydantic.ValidationError) as error:
        _Cuatro.model_validate({})

    assert errores.describir_error(error.value, "IA1")["motivo"] == (
        "ValidationError: missing en a; missing en b; missing en c; (+1 más)"
    )


# =============================================================================
# procesos/sv2_obra.py — sv2 montado como en producción [61-76]
# =============================================================================


def _por_defecto_de_sv2() -> dict[str, object]:
    """`alias → valor por defecto` de los `Field(valor, alias=...)` de `config/settings.py` de sv2.

    Se lee el fuente con `ast`: sv2 no se puede importar en este intérprete.
    """
    arbol = ast.parse((sv2_extraccion.RAIZ_SV2 / "config" / "settings.py").read_text(encoding="utf-8"))
    valores: dict[str, object] = {}
    for nodo in ast.walk(arbol):
        if isinstance(nodo, ast.Call) and getattr(nodo.func, "id", None) == "Field" and nodo.args:
            alias = next((k.value for k in nodo.keywords if k.arg == "alias"), None)
            if isinstance(alias, ast.Constant) and isinstance(nodo.args[0], ast.Constant):
                valores[alias.value] = nodo.args[0].value
    return valores


def test_f048_t34b_sv2_obra_los_valores_por_defecto_son_los_de_sv2():
    """[61, 62] Sin variables, el comparador corta y limita la lista de obras como producción."""
    defecto = _por_defecto_de_sv2()

    for variable, valor in (sv2_obra.TIMEOUT_SIGRID, sv2_obra.COD_MIN_OBRAS, sv2_obra.MAX_OBRAS):
        assert defecto[variable] == valor, variable


def test_f048_t34b_sv2_obra_sv2_va_el_primero_en_el_path(monkeypatch):
    """[63] Todos los servicios tienen `application/`, `domain/`, `config/`: gana el de sv2."""
    monkeypatch.setattr(sys, "path", ["/otro/servicio", "/y/otro"])

    sv2_obra._con_sv2_en_path()

    assert sys.path[0] == str(sv2_extraccion.RAIZ_SV2)


def test_f048_t34b_sv2_obra_un_prompt_de_dev_vacio_no_sirve(tmp_path, monkeypatch):
    """[64] `git show` con código 0 pero sin contenido: se para, no se compara contra un vacío."""
    monkeypatch.setattr(
        sv2_obra.subprocess,
        "run",
        lambda *a, **k: types.SimpleNamespace(returncode=0, stdout=b"", stderr=b""),
    )

    with pytest.raises(sv2_obra.PromptDevNoDisponible):
        sv2_obra.prompt_de_dev(tmp_path)
    assert not (tmp_path / "prompts_dev.yaml").exists()


class _ClienteObras:
    """`SigridApiObrasClient` de mentira: registra con qué se construyó."""

    construcciones: ClassVar[list[dict]] = []
    catalogo: ClassVar[object] = None

    def __init__(self, **kwargs) -> None:
        _ClienteObras.construcciones.append(kwargs)

    def obtener_catalogo(self):
        return _ClienteObras.catalogo


@pytest.fixture
def cliente_obras(monkeypatch):
    """Sustituye el módulo del cliente de sv2 por el doble, sin tocar la red ni el `sys.path` real."""
    monkeypatch.setattr(sys, "path", list(sys.path))
    modulo = types.ModuleType("infrastructure.sigrid.sigrid_api_obras_client")
    modulo.SigridApiObrasClient = _ClienteObras
    monkeypatch.setitem(sys.modules, "infrastructure", types.ModuleType("infrastructure"))
    monkeypatch.setitem(sys.modules, "infrastructure.sigrid", types.ModuleType("infrastructure.sigrid"))
    monkeypatch.setitem(sys.modules, "infrastructure.sigrid.sigrid_api_obras_client", modulo)
    _ClienteObras.construcciones = []
    _ClienteObras.catalogo = types.SimpleNamespace(activas=["0945 Obra", "0950 Obra"])
    return _ClienteObras


def test_f048_t34b_sv2_obra_consultar_obras_sin_variables_usa_los_valores_por_defecto(cliente_obras):
    """[65, 66, 67, 68, 69, 70] Sin `SIGRID_API_TIMEOUT_S` ni `OBRAS_ACTIVAS_COD_MIN`, los de sv2."""
    assert sv2_obra.consultar_obras(_entorno()) == ["0945 Obra", "0950 Obra"]

    construido = cliente_obras.construcciones[0]
    assert construido["timeout_s"] == 30.0 and isinstance(construido["timeout_s"], float)
    assert construido["cod_min"] == 450 and isinstance(construido["cod_min"], int)


def test_f048_t34b_sv2_obra_consultar_obras_con_variables_usa_las_del_entorno(cliente_obras):
    """[65, 66, 68, 69] Con las variables puestas, mandan ellas."""
    sv2_obra.consultar_obras(_entorno(SIGRID_API_TIMEOUT_S="12", OBRAS_ACTIVAS_COD_MIN="700"))

    construido = cliente_obras.construcciones[0]
    assert construido["timeout_s"] == 12.0
    assert construido["cod_min"] == 700


@pytest.mark.parametrize(
    "catalogo", [None, types.SimpleNamespace(activas=[])], ids=["sin_catalogo", "sin_activas"]
)
def test_f048_t34b_sv2_obra_sin_obras_activas_devuelve_none(cliente_obras, catalogo):
    """[71, 72, 73] Sin catálogo o con la lista vacía, `None`: quien llama para la corrida."""
    cliente_obras.catalogo = catalogo

    assert sv2_obra.consultar_obras(_entorno()) is None


@pytest.fixture
def montaje_sin_sv2(monkeypatch):
    """`montar_extractor` sin sv2 ni LLM: registra con qué `obras_max` se monta cada variante."""
    monkeypatch.setattr(sys, "path", list(sys.path))
    monkeypatch.setattr(sv2_extraccion, "_especificacion", lambda proveedor: f"spec-{proveedor}")
    monkeypatch.setattr(sv2_extraccion, "_adjuntos", lambda ruta: ["adjunto"])
    montajes: list[tuple] = []

    def montar_servicio(variante, ruta, especificacion, proveedor_obras, obras_max):
        montajes.append((variante, obras_max))

    monkeypatch.setattr(sv2_obra, "montar_servicio", montar_servicio)
    return montajes


def test_f048_t34b_sv2_obra_montar_extractor_sin_variable_limita_como_sv2(montaje_sin_sv2):
    """[75, 76] Sin `OBRAS_ACTIVAS_MAX`, el tope de producción."""
    sv2_obra.montar_extractor({"rama": Path("p.yaml")}, ["obra"], "gemini", {})

    assert montaje_sin_sv2 == [("rama", 300)]


def test_f048_t34b_sv2_obra_montar_extractor_con_variable_usa_la_del_entorno(montaje_sin_sv2):
    """[74, 75] Con `OBRAS_ACTIVAS_MAX`, esa."""
    sv2_obra.montar_extractor({"dev": Path("p.yaml")}, ["obra"], "gemini", {"OBRAS_ACTIVAS_MAX": "25"})

    assert montaje_sin_sv2 == [("dev", 25)]


# =============================================================================
# runner.py — el caso que sv6 no devuelve [77]
# =============================================================================


def _banco_determinista(tmp_path, *ids) -> Path:
    fixtures = tmp_path / "fixtures"
    for fase in ("inputs", "IA3", "IA4", "final"):
        (fixtures / fase).mkdir(parents=True)
        for caso_id in ids:
            (fixtures / fase / f"{caso_id}.json").write_text(
                json.dumps({"caso_id": caso_id, "tablas": {}}), encoding="utf-8"
            )
    return fixtures


@pytest.fixture
def sv6_sin_servicios(monkeypatch):
    monkeypatch.setattr(sv6, "construir_envelope_estimulado", lambda datos, ia3: {})
    monkeypatch.setattr(sv5, "conciliaciones_desde_ground_truth", lambda ia4, env: [])
    monkeypatch.setattr(sv5, "aplicar_conciliacion", lambda env, conc: 0)
    monkeypatch.setattr(sv5, "proyectar_ia4", lambda conciliaciones, envelope: [])
    monkeypatch.setattr(
        sv6,
        "evaluar_caso_determinista",
        lambda **kwargs: types.SimpleNamespace(discrepancias=[], no_observables=[]),
    )


def _casos_de(fases, nombre) -> dict:
    return {c.caso_id: c for c in next(f for f in fases if f.nombre == nombre).casos}


def test_f048_t34b_runner_un_caso_que_sv6_no_devuelve_sale_error_y_no_verde(
    tmp_path, monkeypatch, sv6_sin_servicios
):
    """[77] sv6 vivo pero sin el resultado de un caso: ERROR con motivo, nunca evaluado."""
    fixtures = _banco_determinista(tmp_path, "HOR-001", "HOR-002")
    monkeypatch.setattr(
        sv6,
        "ejecutar_en_subproceso",
        lambda trabajo, interprete=None: {"resultados": [{"caso_id": "HOR-002", "header": {}, "lineas": []}]},
    )

    fases, _ = runner.corrida_determinista(fixtures)

    for nombre in ("IA3", "E2E"):
        casos = _casos_de(fases, nombre)
        assert casos["HOR-001"].estado == ERROR
        assert casos["HOR-001"].motivo == "sv6 no devolvió resultado"
        assert casos["HOR-002"].estado == "VERDE"


def test_f048_t34b_runner_si_muere_sv6_cada_caso_lleva_el_motivo_de_la_muerte(
    tmp_path, monkeypatch, sv6_sin_servicios
):
    """[77] Si el subproceso murió, el caso dice ESO, no un genérico «no devolvió»."""
    fixtures = _banco_determinista(tmp_path, "HOR-001")

    def muere(trabajo, interprete=None):
        raise RuntimeError("se murió")

    monkeypatch.setattr(sv6, "ejecutar_en_subproceso", muere)

    fases, _ = runner.corrida_determinista(fixtures)

    for nombre in ("IA3", "E2E"):
        fase = next(f for f in fases if f.nombre == nombre)
        caso = _casos_de(fases, nombre)["HOR-001"]
        assert fase.veredicto() == NO_EVALUABLE
        assert caso.estado == ERROR
        assert caso.motivo == fase.motivo
        assert caso.motivo.startswith("el subproceso de sv6 murió")
