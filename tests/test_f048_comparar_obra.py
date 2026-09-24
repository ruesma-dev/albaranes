# tests/test_f048_comparar_obra.py
"""F-048 · comparador de la obra que lee IA1 con el prompt de `dev` y el de la rama.

La pasada con LLM de F-048 no pudo decir si el prompt nuevo empeora
`obra_codigo`: el banco no la compara y el modo `completa` corre IA1 sin la
lista de obras activas (`progress/analisis_evals_F-048.md`). El comparador
mide eso directamente, y estos tests fijan que lo mida bien SIN red ni LLM:
el extractor y el proveedor de obras son dobles.

Lo que se fija: la clasificación estable / inestable / difiere / idéntico,
el aislamiento por caso, las dos paradas antes de gastar (sin claves y sin
sigrid-api) y que el resumen que se versiona no lleva valores.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from evals import comparar_obra as co
from evals.procesos import sv2_obra

CENTINELA = "CENTINELA-OBRA-7731"
CENTINELA_NOMBRE = "CENTINELA-NOMBRE-OBRA-7731"


# --- Dobles ------------------------------------------------------------------


def _entorno(**extra) -> dict:
    """Entorno mínimo para que la corrida arranque. Valores de mentira."""
    base = {
        "GEMINI_API_KEY": "clave-de-mentira",
        "SIGRID_API_BASE_URL": "http://sigrid.invalid",
        "SIGRID_API_FUNCTION_KEY": "clave-de-mentira",
        "SIGRID_API_DATABASE": "bbdd-de-mentira",
    }
    base.update(extra)
    return {k: v for k, v in base.items() if v is not None}


class ErrorConValores(ValueError):
    """Una excepción cuyo texto lleva un valor del albarán (como la de pydantic)."""


class Dobles:
    """Extractor, proveedor de obras y prompt de dev de mentira, con registro de llamadas.

    `respuestas[(variante, caso_id)]` es la lista de lo que devuelve IA1 en
    cada repetición: un código (o `None`), o una excepción que se lanza.
    """

    def __init__(self, tmp_path: Path, respuestas: dict, obras=("obra",)) -> None:
        self.tmp_path = tmp_path
        self.respuestas = respuestas
        self.obras = list(obras) if obras is not None else None
        self.llamadas: list[tuple] = []
        self.montajes: list[tuple] = []
        self.consultas = 0
        self._contador: dict[tuple, int] = {}

    def prompt_de_dev(self, directorio: Path) -> Path:
        ruta = Path(directorio) / "prompts_dev.yaml"
        ruta.write_text("albaran_factura_es: {}\n", encoding="utf-8")
        return ruta

    def prompt_de_rama(self) -> Path:
        return self.tmp_path / "prompts_rama.yaml"

    def consultar_obras(self, entorno: dict):
        self.consultas += 1
        return self.obras

    def montar_extractor(self, prompts, obras, proveedor, entorno):
        self.montajes.append((tuple(sorted(prompts)), len(obras), proveedor))

        def extraer(variante: str, caso_id: str, ruta: Path) -> dict:
            clave = (variante, caso_id)
            indice = self._contador.get(clave, 0)
            self._contador[clave] = indice + 1
            self.llamadas.append((variante, caso_id, indice + 1))
            valor = self.respuestas[clave][indice]
            if isinstance(valor, BaseException):
                raise valor
            nombre = CENTINELA_NOMBRE if valor == CENTINELA else f"nombre de {valor}"
            return {"obra_codigo": valor, "obra_nombre": nombre}

        return extraer

    def dependencias(self) -> co.Dependencias:
        return co.Dependencias(
            prompt_de_dev=self.prompt_de_dev,
            prompt_de_rama=self.prompt_de_rama,
            consultar_obras=self.consultar_obras,
            montar_extractor=self.montar_extractor,
        )


def _albaranes(tmp_path: Path, casos) -> Path:
    directorio = tmp_path / "albaranes"
    directorio.mkdir()
    for caso in casos:
        (directorio / f"{caso}.pdf").write_bytes(b"%PDF-de-mentira")
    return directorio


def _lanzar(tmp_path, dobles, casos, *extra, entorno=None, con_pdf=None):
    albaranes = _albaranes(tmp_path, con_pdf if con_pdf is not None else casos)
    salida = tmp_path / "salida"
    resumen = tmp_path / "progress" / "comparar_obra_F-048.md"
    codigo = co.main(
        [
            "--casos", ",".join(casos),
            "--albaranes", str(albaranes),
            "--salida", str(salida),
            "--resumen", str(resumen),
            *extra,
        ],
        entorno=entorno if entorno is not None else _entorno(),
        dependencias=dobles.dependencias(),
    )
    return codigo, salida, resumen


# --- Clasificación -----------------------------------------------------------


@pytest.mark.parametrize(
    ("dev", "rama", "categoria", "estable_dev", "estable_rama", "coinciden"),
    [
        (["0945", "0945", "0945"], ["0945", "0945", "0945"], "identico", True, True, True),
        (["0945", "0945", "0945"], ["0950", "0950", "0950"], "difiere", True, True, False),
        ([None, None, None], ["0950", "0950", "0950"], "difiere", True, True, False),
        (["0945", "0950", "0945"], ["0945", "0945", "0945"], "inestable", False, True, None),
        (["0945", "0945", "0945"], ["0945", None, "0945"], "inestable", True, False, None),
        (["0945", "0950", "0945"], ["0950", "0945", "0945"], "inestable", False, False, None),
    ],
)
def test_f048_comparar_obra_clasifica_cada_caso(
    dev, rama, categoria, estable_dev, estable_rama, coinciden
):
    """Estable = la misma obra en todas las repeticiones; difiere solo si las dos lo son."""
    resultado = co.clasificar_caso(
        {
            "dev": [{"obra_codigo": v, "obra_nombre": None} for v in dev],
            "rama": [{"obra_codigo": v, "obra_nombre": None} for v in rama],
        }
    )
    assert resultado["categoria"] == categoria
    assert resultado["estable"] == {"dev": estable_dev, "rama": estable_rama}
    assert resultado["coinciden"] is coinciden


def test_f048_comparar_obra_la_estabilidad_mira_el_codigo_no_el_nombre():
    """El nombre de la obra puede venir escrito de otra manera; lo que cuenta es el código."""
    resultado = co.clasificar_caso(
        {
            "dev": [{"obra_codigo": "0945", "obra_nombre": "A"}, {"obra_codigo": "0945", "obra_nombre": "B"}],
            "rama": [{"obra_codigo": "0945", "obra_nombre": "C"}, {"obra_codigo": " 0945 ", "obra_nombre": None}],
        }
    )
    assert resultado["categoria"] == "identico"


def test_f048_comparar_obra_un_error_saca_el_caso_de_la_comparacion():
    """Con una repetición fallida no se puede afirmar estabilidad: el caso va aparte."""
    resultado = co.clasificar_caso(
        {
            "dev": [{"obra_codigo": "0945"}, {"error": {"fase": "IA1", "tipo": "X", "motivo": "X"}}],
            "rama": [{"obra_codigo": "0945"}, {"obra_codigo": "0945"}],
        }
    )
    assert resultado["categoria"] == "con_errores"
    assert resultado["estable"]["dev"] is None
    assert resultado["coinciden"] is None


def test_f048_comparar_obra_con_una_sola_variante_no_hay_difiere():
    """`--variante dev` mide solo el ruido de dev: estable o inestable, nunca «difiere»."""
    assert co.clasificar_caso({"dev": [{"obra_codigo": "1"}, {"obra_codigo": "1"}]})["categoria"] == "estable"
    assert co.clasificar_caso({"dev": [{"obra_codigo": "1"}, {"obra_codigo": "2"}]})["categoria"] == "inestable"


# --- Corrida completa con dobles ---------------------------------------------


def test_f048_comparar_obra_corrida_con_dobles_escribe_json_y_recuentos(tmp_path):
    """Una corrida de 4 casos, uno por categoría: JSON por variante y repetición y los dos resúmenes."""
    respuestas = {
        ("dev", "C-IDENT"): ["0945", "0945"],
        ("rama", "C-IDENT"): ["0945", "0945"],
        ("dev", "C-DIFIERE"): ["0945", "0945"],
        ("rama", "C-DIFIERE"): ["0950", "0950"],
        ("dev", "C-RUIDO"): ["0945", "0950"],
        ("rama", "C-RUIDO"): ["0945", "0945"],
        ("dev", "C-NULO"): [None, None],
        ("rama", "C-NULO"): [None, None],
    }
    dobles = Dobles(tmp_path, respuestas)
    casos = ["C-IDENT", "C-DIFIERE", "C-RUIDO", "C-NULO"]

    codigo, salida, resumen = _lanzar(tmp_path, dobles, casos, "--repeticiones", "2")

    assert codigo == 0
    assert dobles.consultas == 1, "una sola consulta de obras para toda la corrida"
    assert dobles.montajes == [(("dev", "rama"), 1, "gemini")]
    assert len(dobles.llamadas) == 2 * 2 * 4
    for variante in ("dev", "rama"):
        for repeticion in (1, 2):
            datos = json.loads((salida / f"{variante}_r{repeticion}.json").read_text(encoding="utf-8"))
            assert datos["variante"] == variante and datos["repeticion"] == repeticion
            assert set(datos["casos"]) == set(casos)
    dev_r2 = json.loads((salida / "dev_r2.json").read_text(encoding="utf-8"))
    assert dev_r2["casos"]["C-RUIDO"]["obra_codigo"] == "0950"
    assert dev_r2["casos"]["C-NULO"]["obra_codigo"] is None

    texto = resumen.read_text(encoding="utf-8")
    assert "| difiere | 1 |" in texto
    assert "| inestable | 1 |" in texto
    assert "| identico | 2 |" in texto
    assert "| con_errores | 0 |" in texto
    assert "C-DIFIERE" in texto and "C-RUIDO (dev)" in texto

    detalle = (salida / "resumen.md").read_text(encoding="utf-8")
    assert "0950" in detalle, "el resumen del directorio ignorado SÍ lleva los valores"


def test_f048_comparar_obra_un_caso_roto_no_para_la_corrida(tmp_path):
    """Aislamiento por caso: la excepción se anota con su forma, sin su texto, y se sigue."""
    respuestas = {
        ("dev", "C-ROTO"): ["0945", ErrorConValores(CENTINELA)],
        ("rama", "C-ROTO"): ["0945", "0945"],
        ("dev", "C-BIEN"): ["0945", "0945"],
        ("rama", "C-BIEN"): ["0945", "0945"],
    }
    dobles = Dobles(tmp_path, respuestas)
    casos = ["C-ROTO", "C-SIN-PDF", "C-BIEN"]

    codigo, salida, resumen = _lanzar(
        tmp_path, dobles, casos, "--repeticiones", "2", con_pdf=["C-ROTO", "C-BIEN"]
    )

    assert codigo == 0
    # El caso roto sigue en las repeticiones y variantes que no fallaron, y C-BIEN entero.
    assert ("rama", "C-ROTO", 2) in dobles.llamadas
    assert [l for l in dobles.llamadas if l[1] == "C-BIEN"] == [
        ("dev", "C-BIEN", 1), ("rama", "C-BIEN", 1), ("dev", "C-BIEN", 2), ("rama", "C-BIEN", 2)
    ]
    assert not [l for l in dobles.llamadas if l[1] == "C-SIN-PDF"]

    dev_r2 = json.loads((salida / "dev_r2.json").read_text(encoding="utf-8"))
    error = dev_r2["casos"]["C-ROTO"]["error"]
    assert error["fase"] == "IA1" and error["tipo"] == "ErrorConValores"
    assert "no existe el fichero" in dev_r2["casos"]["C-SIN-PDF"]["error"]["motivo"]

    texto = resumen.read_text(encoding="utf-8")
    assert "| con_errores | 2 |" in texto
    assert "| identico | 1 |" in texto
    for fichero in [resumen, *salida.iterdir()]:
        assert CENTINELA not in fichero.read_text(encoding="utf-8"), fichero.name


def test_f048_comparar_obra_resumen_versionable_sin_valores(tmp_path):
    """El resumen de `progress/` lleva recuentos y caso_id, nunca un código ni un nombre de obra."""
    respuestas = {
        ("dev", "C-1"): [CENTINELA, CENTINELA],
        ("rama", "C-1"): [CENTINELA, "0950"],
        ("dev", "C-2"): [CENTINELA, CENTINELA],
        ("rama", "C-2"): ["0950", "0950"],
    }
    dobles = Dobles(tmp_path, respuestas)

    codigo, salida, resumen = _lanzar(tmp_path, dobles, ["C-1", "C-2"], "--repeticiones", "2")

    assert codigo == 0
    texto = resumen.read_text(encoding="utf-8")
    assert CENTINELA not in texto and CENTINELA_NOMBRE not in texto and "0950" not in texto
    assert "C-1" in texto and "C-2" in texto
    # El centinela SÍ ha pasado por la corrida: está en lo que no se versiona.
    assert CENTINELA in (salida / "resumen.md").read_text(encoding="utf-8")
    assert CENTINELA_NOMBRE in (salida / "dev_r1.json").read_text(encoding="utf-8")


def test_f048_comparar_obra_una_sola_variante(tmp_path):
    """`--variante rama` monta y llama solo a la rama."""
    dobles = Dobles(tmp_path, {("rama", "C-1"): ["1", "1", "1"]})

    codigo, salida, resumen = _lanzar(tmp_path, dobles, ["C-1"], "--variante", "rama")

    assert codigo == 0
    assert dobles.montajes == [(("rama",), 1, "gemini")]
    assert sorted(p.name for p in salida.glob("*.json")) == ["rama_r1.json", "rama_r2.json", "rama_r3.json"]
    assert "| estable | 1 |" in resumen.read_text(encoding="utf-8")


def test_f048_comparar_obra_todo_fallido_sale_con_1(tmp_path):
    """Si ninguna extracción devuelve nada, la corrida no puede pasar por buena."""
    dobles = Dobles(tmp_path, {("dev", "C-1"): [RuntimeError("x")], ("rama", "C-1"): [RuntimeError("x")]})

    codigo, _, resumen = _lanzar(tmp_path, dobles, ["C-1"], "--repeticiones", "1")

    assert codigo == 1
    assert "| con_errores | 1 |" in resumen.read_text(encoding="utf-8")


# --- Paradas antes de gastar -------------------------------------------------


def _nada_escrito(dobles: Dobles, tmp_path: Path) -> None:
    assert dobles.llamadas == [] and dobles.montajes == []
    assert not (tmp_path / "salida").exists()
    assert not (tmp_path / "progress").exists()


@pytest.mark.parametrize(
    ("entorno", "variable"),
    [
        (_entorno(GEMINI_API_KEY=None), "GEMINI_API_KEY"),
        (_entorno(GEMINI_API_KEY="  "), "GEMINI_API_KEY"),
        (_entorno(IA_PRIMERA_FASE="openai"), "OPENAI_API_KEY"),
    ],
)
def test_f048_comparar_obra_para_sin_claves(tmp_path, capsys, entorno, variable):
    """Sin la clave del proveedor de fase 1 no se consulta nada ni se llama a nadie."""
    dobles = Dobles(tmp_path, {})

    codigo, _, _ = _lanzar(tmp_path, dobles, ["C-1"], entorno=entorno)

    assert codigo == 2
    assert variable in capsys.readouterr().err
    assert dobles.consultas == 0
    _nada_escrito(dobles, tmp_path)


@pytest.mark.parametrize("variable", sv2_obra.VARIABLES_SIGRID_OBLIGATORIAS)
def test_f048_comparar_obra_para_sin_configuracion_de_sigrid(tmp_path, capsys, variable):
    """Sin las variables de sigrid-api no se corre con «NO DISPONIBLE»: se para."""
    dobles = Dobles(tmp_path, {})

    codigo, _, _ = _lanzar(tmp_path, dobles, ["C-1"], entorno=_entorno(**{variable: None}))

    assert codigo == 2
    error = capsys.readouterr().err
    assert "sigrid-api" in error and variable in error
    assert dobles.consultas == 0
    _nada_escrito(dobles, tmp_path)


@pytest.mark.parametrize("obras", [None, []])
def test_f048_comparar_obra_para_si_sigrid_api_no_responde(tmp_path, capsys, obras):
    """sigrid-api configurado pero sin lista (caído, error o vacía): se para antes del LLM."""
    dobles = Dobles(tmp_path, {}, obras=obras)

    codigo, _, _ = _lanzar(tmp_path, dobles, ["C-1"])

    assert codigo == 2
    assert "sigrid-api no está disponible" in capsys.readouterr().err
    assert dobles.consultas == 1
    _nada_escrito(dobles, tmp_path)


def test_f048_comparar_obra_para_si_no_hay_ningun_albaran(tmp_path, capsys):
    """Si ningún caso tiene fichero, no se consulta sigrid-api ni se monta nada."""
    dobles = Dobles(tmp_path, {})

    codigo, _, _ = _lanzar(tmp_path, dobles, ["C-1", "C-2"], con_pdf=[])

    assert codigo == 2
    assert "ningún" in capsys.readouterr().err
    assert dobles.consultas == 0
    _nada_escrito(dobles, tmp_path)


@pytest.mark.parametrize(
    "argumentos",
    [["--casos", ""], ["--casos", "C-1", "--repeticiones", "0"], ["--casos", "C-1", "--variante", "otra"]],
)
def test_f048_comparar_obra_rechaza_peticiones_mal_formadas(tmp_path, argumentos):
    dobles = Dobles(tmp_path, {})
    with pytest.raises(SystemExit) as salida:
        co.main(argumentos, entorno=_entorno(), dependencias=dobles.dependencias())
    assert salida.value.code == 2
    assert dobles.consultas == 0


# --- Salida ignorada por git y piezas puras de sv2_obra -----------------------


def test_f048_comparar_obra_la_salida_por_defecto_la_ignora_git():
    """Los JSON y el resumen con valores caen en un directorio que git no versiona."""
    raiz = Path(__file__).resolve().parent.parent
    salida = co.directorio_por_defecto()
    assert salida.parent == co.RUTA_SALIDAS
    ignorado = subprocess.run(
        ["git", "-C", str(raiz), "check-ignore", "-q", str(salida / "dev_r1.json")], check=False
    )
    assert ignorado.returncode == 0
    versionable = subprocess.run(
        ["git", "-C", str(raiz), "check-ignore", "-q", str(co.RUTA_RESUMEN_VERSIONABLE)], check=False
    )
    assert versionable.returncode == 1, "el resumen sin valores sí se versiona"


def test_f048_comparar_obra_obras_fijas_devuelve_siempre_la_misma_lista():
    proveedor = sv2_obra.ObrasFijas(["a", "b"])
    primera = proveedor.obtener()
    primera.append("c")
    assert proveedor.obtener() == ["a", "b"]
    assert proveedor.obtener_todas() is None
    assert sv2_obra.ObrasFijas(["a"], ["a", "z"]).obtener_todas() == ["a", "z"]


def test_f048_comparar_obra_modelo_sin_campo_conserva_lo_demas():
    """El schema de `dev` es el de la rama sin `lectura_correo`: mismo nombre y mismos campos."""
    from pydantic import BaseModel, ConfigDict, Field

    class Base(BaseModel):
        model_config = ConfigDict(extra="forbid")

    class Documento(Base):
        a: int
        b: str | None = Field(default=None, max_length=3)
        lectura_correo: str | None = None

    reducido = sv2_obra.modelo_sin_campo(Documento)
    assert reducido.__name__ == "Documento"
    assert list(reducido.model_fields) == ["a", "b"]
    esperado = Documento.model_json_schema()
    del esperado["properties"]["lectura_correo"]
    assert reducido.model_json_schema() == esperado
    assert sv2_obra.modelo_sin_campo(reducido) is reducido


def test_f048_comparar_obra_prompt_de_dev_es_el_yaml_de_dev_tal_cual(tmp_path):
    """El YAML de `dev` sale de git, sin tocar: sin el marcador del correo que trae la rama."""
    raiz = Path(__file__).resolve().parent.parent
    ruta = sv2_obra.prompt_de_dev(tmp_path)
    esperado = subprocess.run(
        ["git", "-C", str(raiz), "show", f"dev:{sv2_obra.RUTA_PROMPTS}"], capture_output=True, check=True
    ).stdout
    assert ruta.parent == tmp_path and ruta.read_bytes() == esperado
    texto = ruta.read_text(encoding="utf-8")
    assert "{obras_activas}" in texto and "{contexto_correo}" not in texto
    assert "{contexto_correo}" in sv2_obra.prompt_de_rama().read_text(encoding="utf-8")


def test_f048_comparar_obra_sin_prompt_de_dev_para(tmp_path, capsys):
    """Si `git show dev:...` falla, se para con su motivo antes de gastar."""
    with pytest.raises(sv2_obra.PromptDevNoDisponible):
        sv2_obra.prompt_de_dev(tmp_path, raiz=tmp_path)

    dobles = Dobles(tmp_path, {})

    def sin_dev(directorio):
        raise sv2_obra.PromptDevNoDisponible("sin rama dev")

    dependencias = dobles.dependencias()
    dependencias.prompt_de_dev = sin_dev
    albaranes = _albaranes(tmp_path, ["C-1"])
    codigo = co.main(
        ["--casos", "C-1", "--albaranes", str(albaranes), "--salida", str(tmp_path / "salida"),
         "--resumen", str(tmp_path / "progress" / "r.md")],
        entorno=_entorno(),
        dependencias=dependencias,
    )
    assert codigo == 2
    assert "sin rama dev" in capsys.readouterr().err
    _nada_escrito(dobles, tmp_path)


def test_f048_comparar_obra_registro_sin_campo_y_obra_de():
    """El registro de la variante `dev` recorta y cachea; `obra_de` lee solo la cabecera."""
    from pydantic import BaseModel

    class Cabecera(BaseModel):
        obra_codigo: str | None = None
        obra_nombre: str | None = None

    class Documento(BaseModel):
        cabecera: Cabecera
        lectura_correo: str | None = None

    class Registro:
        def get(self, nombre):
            return Documento

    registro = sv2_obra.RegistroSinCampo(Registro())
    modelo = registro.get("documento_albaran")
    assert "lectura_correo" not in modelo.model_fields
    assert registro.get("documento_albaran") is modelo

    documento = modelo.model_validate({"cabecera": {"obra_codigo": "1", "obra_nombre": "N"}})
    assert sv2_obra.obra_de(documento) == {"obra_codigo": "1", "obra_nombre": "N"}
    assert sv2_obra.obra_de({"cabecera": None}) == {"obra_codigo": None, "obra_nombre": None}
    with pytest.raises(ValueError, match="variante desconocida"):
        sv2_obra.montar_servicio("otra", "x.yaml", None, None)
