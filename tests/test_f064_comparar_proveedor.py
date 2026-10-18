# tests/test_f064_comparar_proveedor.py
"""F-064 · R14–R17: el comparador del PROVEEDOR base/rama, sin LLM.

El banco no mide el CIF del proveedor (``NO_COMPARAR`` en IA1, no observable
en el E2E), así que F-064 trae su propio comparador:
``python -m evals.comparar_proveedor``. Aquí se prueba todo lo que no es
llamar al LLM: clasificación del CIF, las dos fases con un servicio doble,
la mayoría, el veredicto C1–C3, los informes (el versionable SIN CIF ni
nombres) y las paradas con código 2 antes de gastar.

Dobles con centinelas: ``CENTINELA-NOMBRE-F064`` y CIF inventados.
"""

from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

import pytest

from evals import comparar_proveedor as cp
from evals.procesos import sv2_proveedor

RAIZ_REPO = Path(__file__).resolve().parent.parent

#: `dev` de antes de F-064: inmutable, sin `{empresas_cliente}` ni la regla.
BASE_FIJA = "544113b"

CIF_CLIENTE = "A81873903"
CIF_EMISOR = "B99999999"
CIF_OTRO = "Q0000000J"
NOMBRE = "CENTINELA-NOMBRE-F064"
PROPIOS = frozenset({CIF_CLIENTE})


# --- Dobles -------------------------------------------------------------------


def _entorno(**extra) -> dict:
    base = {"GEMINI_API_KEY": "clave-de-mentira", "OPENAI_API_KEY": "clave-de-mentira"}
    base.update(extra)
    return {k: v for k, v in base.items() if v is not None}


def _fixtures(tmp_path: Path, casos: dict[str, tuple[str, str]]) -> Path:
    """`casos[caso_id] = (cif esperado, tipología)` → fixtures final e IA1."""
    raiz = tmp_path / "fixtures"
    for fase in ("final", "IA1"):
        (raiz / fase).mkdir(parents=True, exist_ok=True)
    for caso, (cif, tipologia) in casos.items():
        final = {"caso_id": caso, "tipologia": tipologia,
                 "tablas": {"datos_generales": [{"caso_id": caso, "cif": cif}]}}
        ia1 = {"caso_id": caso, "tipologia": tipologia, "tablas": {"cabeceras": []}}
        (raiz / "final" / f"{caso}.json").write_text(json.dumps(final), encoding="utf-8")
        (raiz / "IA1" / f"{caso}.json").write_text(json.dumps(ia1), encoding="utf-8")
    return raiz


class Dobles:
    """`respuestas[(variante, caso)]`: por repetición, `(cif_ia1, cif_ia2)` o una excepción."""

    def __init__(self, tmp_path: Path, respuestas: dict) -> None:
        self.tmp_path = tmp_path
        self.respuestas = respuestas
        self.llamadas: list[tuple] = []
        self.montajes: list[tuple] = []
        self.bases: list[str] = []
        self._contador: dict[tuple, int] = {}

    def ficheros_de_base(self, directorio: Path, base: str) -> dict:
        self.bases.append(base)
        return {"prompts": Path(directorio) / "p.yaml", "reglas": Path(directorio) / "r.yaml"}

    def ficheros_de_rama(self) -> dict:
        return {"prompts": self.tmp_path / "p_rama.yaml", "reglas": self.tmp_path / "r_rama.yaml"}

    def montar_extractor(self, ficheros, proveedores, entorno):
        self.montajes.append((tuple(sorted(ficheros)), dict(proveedores)))

        def extraer(variante, caso_id, ruta, tipologia):
            clave = (variante, caso_id)
            indice = self._contador.get(clave, 0)
            self._contador[clave] = indice + 1
            self.llamadas.append((variante, caso_id, indice + 1, tipologia))
            valor = self.respuestas[clave][indice]
            if isinstance(valor, BaseException):
                raise valor
            cif1, cif2 = valor
            return {"ia1": {"nombre": NOMBRE, "cif": cif1}, "ia2": {"nombre": NOMBRE, "cif": cif2}}

        return extraer

    def dependencias(self, fixtures: Path) -> cp.Dependencias:
        return cp.Dependencias(
            ficheros_de_base=self.ficheros_de_base,
            ficheros_de_rama=self.ficheros_de_rama,
            montar_extractor=self.montar_extractor,
            fixtures=fixtures,
        )


def _albaranes(tmp_path: Path, casos) -> Path:
    directorio = tmp_path / "albaranes"
    directorio.mkdir(exist_ok=True)
    for caso in casos:
        (directorio / f"{caso}.pdf").write_bytes(b"%PDF-de-mentira")
    return directorio


def _lanzar(tmp_path, dobles, casos, *extra, entorno=None, con_pdf=None, esperados=None):
    esperados = esperados or {c: (CIF_EMISOR, "Hormigon") for c in casos}
    fixtures = _fixtures(tmp_path, esperados)
    albaranes = _albaranes(tmp_path, con_pdf if con_pdf is not None else casos)
    salida = tmp_path / "salida"
    resumen = tmp_path / "progress" / "comparar_proveedor_F-064.md"
    codigo = cp.main(
        ["--casos", ",".join(casos), "--albaranes", str(albaranes), "--salida", str(salida),
         "--resumen", str(resumen), *extra],
        entorno=entorno if entorno is not None else _entorno(),
        dependencias=dobles.dependencias(fixtures),
    )
    return codigo, salida, resumen


def _nada_escrito(dobles: Dobles, tmp_path: Path) -> None:
    assert dobles.llamadas == [] and dobles.montajes == []
    assert not (tmp_path / "salida").exists()
    assert not (tmp_path / "progress").exists()


# --- R14 · clasificación del CIF ------------------------------------------------


@pytest.mark.parametrize(
    ("cif", "categoria"),
    [
        (CIF_EMISOR, "emisor"),
        ("b-99.999.999", "emisor"),
        ("ESB99999999", "emisor"),
        (CIF_CLIENTE, "cliente"),
        ("A-81873903", "cliente"),
        (None, "nulo"),
        ("", "nulo"),
        ("  -  ", "nulo"),
        (CIF_OTRO, "otro"),
    ],
)
def test_f064_r14_clasificar_cif(cif, categoria):
    assert cp.clasificar_cif(cif, CIF_EMISOR, PROPIOS) == categoria


def test_f064_r14_el_esperado_tambien_se_normaliza():
    assert cp.clasificar_cif(CIF_EMISOR, "B-99999999", PROPIOS) == "emisor"


def test_f064_r14_sin_esperado_un_cif_ajeno_es_otro():
    assert cp.clasificar_cif(CIF_EMISOR, None, PROPIOS) == "otro"


def test_f064_r14_casos_por_defecto_son_los_19_del_design():
    assert cp.CASOS_POR_DEFECTO == (
        "FER-001", "FER-002", "FER-003",
        "HOR-005", "HOR-006", "HOR-007", "HOR-008", "HOR-009", "HOR-010", "HOR-011",
        "MOR-003",
        "ALQ-001", "COM-001", "GEN-002", "GEN-004", "GEN-010", "HOR-012", "RES-001", "RES-010",
    )


def test_f064_r14_los_casos_por_defecto_tienen_cif_esperado_y_tipologia():
    for caso in cp.CASOS_POR_DEFECTO:
        assert cp.esperado_de(caso, cp.RUTA_FIXTURES), caso
        assert cp.tipologia_de(caso, cp.RUTA_FIXTURES), caso


# --- R14 · las dos fases (servicio doble) --------------------------------------


class _Resultado:
    def __init__(self, datos) -> None:
        self.parsed = _Modelo(datos)


class _Modelo:
    def __init__(self, datos) -> None:
        self._datos = datos

    def model_dump(self):
        return self._datos


class ServicioDoble:
    def __init__(self, fase_2=None, error_1=None, error_2=None) -> None:
        self.fase_1: list[dict] = []
        self.fase_2: list[dict] = []
        self._respuesta_2 = fase_2
        self._error_1 = error_1
        self._error_2 = error_2

    def extract_phase_1(self, **kwargs):
        self.fase_1.append(kwargs)
        if self._error_1:
            raise self._error_1
        return _Resultado({"cabecera": {"proveedor_nombre": NOMBRE, "proveedor_cif": CIF_CLIENTE}, "lineas": []})

    def review_phase_2(self, **kwargs):
        self.fase_2.append(kwargs)
        if self._error_2:
            raise self._error_2
        return _Resultado(self._respuesta_2)


def test_f064_r14_dos_fases_con_el_proveedor_y_el_prompt_de_cada_fase():
    revisado = {"review_status": "ok_with_changes",
                "documento_revisado": {"cabecera": {"proveedor_nombre": "EMISOR", "proveedor_cif": CIF_EMISOR}}}
    servicio = ServicioDoble(fase_2=revisado)

    salida = sv2_proveedor.dos_fases(servicio, ["adjunto"], {"IA1": "gemini", "IA2": "openai"}, "Hormigon")

    assert salida == {"ia1": {"nombre": NOMBRE, "cif": CIF_CLIENTE}, "ia2": {"nombre": "EMISOR", "cif": CIF_EMISOR}}
    assert servicio.fase_1 == [{"attachments": ["adjunto"], "provider": "gemini", "prompt_key": "albaran_factura_es"}]
    llamada = servicio.fase_2[0]
    assert llamada["provider"] == "openai"
    assert llamada["prompt_key"] == "albaran_revision_fase2_hormigon"
    assert llamada["phase_1_json"]["cabecera"]["proveedor_cif"] == CIF_CLIENTE
    assert llamada["attachments"] == ["adjunto"]


def test_f064_r14_tipologia_sin_prompt_propio_va_al_generico():
    servicio = ServicioDoble(fase_2={"documento_revisado": {"cabecera": {}}})

    sv2_proveedor.dos_fases(servicio, [], {"IA1": "gemini", "IA2": "gemini"}, "Ferreteria")

    assert servicio.fase_2[0]["prompt_key"] == "albaran_revision_fase2_es"


def test_f064_r14_sin_documento_revisado_ia2_es_lo_de_fase_1():
    """Como el merge de sv2 (`phase_merge`): sin documento revisado, vale fase 1."""
    servicio = ServicioDoble(fase_2={"review_status": "ok", "documento_revisado": None})

    salida = sv2_proveedor.dos_fases(servicio, [], {"IA1": "gemini", "IA2": "openai"}, "")

    assert salida["ia2"] == {"nombre": NOMBRE, "cif": CIF_CLIENTE}


def test_f064_r14_fallo_de_ia1_no_llama_a_ia2():
    servicio = ServicioDoble(error_1=ValueError(f"respuesta con {CIF_CLIENTE}"))

    salida = sv2_proveedor.dos_fases(servicio, [], {"IA1": "gemini", "IA2": "openai"}, "")

    assert salida["ia1"]["error"]["fase"] == "IA1"
    assert salida["ia2"]["error"]["fase"] == "IA2"
    assert CIF_CLIENTE not in json.dumps(salida)
    assert servicio.fase_2 == []


def test_f064_r14_fallo_de_ia2_conserva_ia1():
    servicio = ServicioDoble(error_2=RuntimeError("503"))

    salida = sv2_proveedor.dos_fases(servicio, [], {"IA1": "gemini", "IA2": "openai"}, "")

    assert salida["ia1"] == {"nombre": NOMBRE, "cif": CIF_CLIENTE}
    assert salida["ia2"]["error"]["fase"] == "IA2"


def test_f064_r14_proveedor_de_lee_solo_la_cabecera():
    assert sv2_proveedor.proveedor_de({"cabecera": None}) == {"nombre": None, "cif": None}
    assert sv2_proveedor.proveedor_de(_Modelo({"cabecera": {"proveedor_cif": CIF_OTRO}})) == {
        "nombre": None, "cif": CIF_OTRO,
    }


def test_f064_r14_montar_servicio_rechaza_ficheros_incompletos():
    with pytest.raises(ValueError, match="prompts y reglas"):
        sv2_proveedor.montar_servicio({"prompts": Path("p.yaml")}, [], sin_pie=False)


# --- R16 · mayoría y veredicto --------------------------------------------------


@pytest.mark.parametrize(
    ("categorias", "mayoria"),
    [
        (["emisor", "emisor", "cliente"], "emisor"),
        (["cliente", "cliente", "cliente"], "cliente"),
        (["emisor", "cliente", "nulo"], "inestable"),
        (["emisor", "cliente"], "inestable"),
        (["error", "error", "emisor"], "error"),
        (["nulo"], "nulo"),
        ([], "error"),
    ],
)
def test_f064_r16_mayoritaria(categorias, mayoria):
    assert cp.mayoritaria(categorias) == mayoria


def _clasif(base: dict, rama: dict) -> dict:
    """`base[caso] = (ia1 [cats], ia2 [cats])` → la forma que da `clasificar`."""
    resultado = {}
    for caso, datos_base in base.items():
        resultado[caso] = {}
        for variante, datos in (("base", datos_base), ("rama", rama[caso])):
            ia1, ia2 = datos
            resultado[caso][variante] = {
                "ia1": ia1, "ia2": ia2,
                "mayoria": {"ia1": cp.mayoritaria(ia1), "ia2": cp.mayoritaria(ia2)},
            }
    return resultado


E3, C3, N3 = ["emisor"] * 3, ["cliente"] * 3, ["nulo"] * 3


def test_f064_r16_veredicto_verde():
    clasificacion = _clasif(
        {"A": (C3, C3), "B": (E3, E3)},
        {"A": (["cliente", "emisor", "emisor"], E3), "B": (E3, E3)},
    )

    veredicto = cp.veredicto(clasificacion, ["base", "rama"])

    assert veredicto["C1"]["ok"] and veredicto["C2"]["ok"] and veredicto["C3"]["ok"]
    assert veredicto["global"] == "VERDE"
    assert veredicto["reproduce_incidente"] is True


def test_f064_r16_c1_un_cliente_tras_ia2_en_la_rama_es_rojo():
    clasificacion = _clasif({"A": (C3, C3)}, {"A": (E3, ["emisor", "emisor", "cliente"])})

    veredicto = cp.veredicto(clasificacion, ["base", "rama"])

    assert veredicto["C1"]["ok"] is False
    assert veredicto["global"] == "ROJO"


def test_f064_r16_c1_mas_clientes_tras_ia1_en_la_rama_que_en_base_es_rojo():
    clasificacion = _clasif({"A": (E3, E3)}, {"A": (["cliente", "emisor", "emisor"], E3)})

    assert cp.veredicto(clasificacion, ["base", "rama"])["C1"]["ok"] is False


def test_f064_r16_c1_tras_ia1_igual_que_base_vale():
    clasificacion = _clasif({"A": (["cliente", "emisor", "emisor"], E3)},
                            {"A": (["emisor", "cliente", "emisor"], E3)})

    assert cp.veredicto(clasificacion, ["base", "rama"])["C1"]["ok"] is True


def test_f064_r16_c2_menos_casos_con_mayoria_emisor_es_rojo():
    clasificacion = _clasif({"A": (E3, E3), "B": (N3, E3)}, {"A": (N3, E3), "B": (N3, E3)})

    veredicto = cp.veredicto(clasificacion, ["base", "rama"])

    assert veredicto["C2"]["ok"] is False
    assert veredicto["C3"]["ok"] is False


def test_f064_r16_c3_perder_un_emisor_aunque_se_gane_otro_es_rojo():
    clasificacion = _clasif({"A": (E3, E3), "B": (N3, N3)}, {"A": (E3, N3), "B": (N3, E3)})

    veredicto = cp.veredicto(clasificacion, ["base", "rama"])

    assert veredicto["C2"]["ok"] is True
    assert veredicto["C3"]["ok"] is False
    assert "A" in veredicto["C3"]["detalle"]


def test_f064_r16_sin_ningun_cliente_en_base_no_reproduce_el_incidente():
    clasificacion = _clasif({"A": (E3, E3)}, {"A": (E3, E3)})

    assert cp.veredicto(clasificacion, ["base", "rama"])["reproduce_incidente"] is False


def test_f064_r16_con_una_variante_no_hay_veredicto():
    assert cp.veredicto({"A": {"rama": {"ia1": E3, "ia2": E3, "mayoria": {}}}}, ["rama"])["global"] == "NO APLICA"


# --- R16 · corrida con dobles e informes ----------------------------------------


def _respuestas_tipicas() -> dict:
    return {
        ("base", "FER-001"): [(CIF_CLIENTE, CIF_CLIENTE)] * 3,
        ("rama", "FER-001"): [(CIF_EMISOR, CIF_EMISOR)] * 3,
        ("base", "GEN-002"): [(CIF_EMISOR, CIF_EMISOR)] * 3,
        ("rama", "GEN-002"): [(CIF_EMISOR, CIF_EMISOR), ("b-99999999", CIF_EMISOR), (CIF_EMISOR, CIF_EMISOR)],
    }


def test_f064_r16_corrida_con_dobles_escribe_detalle_y_resumen(tmp_path):
    dobles = Dobles(tmp_path, _respuestas_tipicas())
    esperados = {"FER-001": (CIF_EMISOR, "Ferreteria"), "GEN-002": (CIF_EMISOR, "Generico-Suministros")}

    codigo, salida, resumen = _lanzar(tmp_path, dobles, ["FER-001", "GEN-002"], esperados=esperados)

    assert codigo == 0
    assert sorted(p.name for p in salida.iterdir()) == [
        "base_r1.json", "base_r2.json", "base_r3.json", "rama_r1.json", "rama_r2.json", "rama_r3.json", "resumen.md",
    ]
    rama_r1 = json.loads((salida / "rama_r1.json").read_text(encoding="utf-8"))
    assert rama_r1["casos"]["FER-001"]["ia2"]["cif"] == CIF_EMISOR
    assert rama_r1["proveedores"] == {"IA1": "gemini", "IA2": "openai"}
    # Repeticiones intercaladas: base y rama dentro de cada vuelta; la tipología llega.
    assert dobles.llamadas[:4] == [
        ("base", "FER-001", 1, "Ferreteria"), ("base", "GEN-002", 1, "Generico-Suministros"),
        ("rama", "FER-001", 1, "Ferreteria"), ("rama", "GEN-002", 1, "Generico-Suministros"),
    ]
    texto = resumen.read_text(encoding="utf-8")
    assert "VEREDICTO: VERDE" in texto
    assert "C1 · OK" in texto and "C2 · OK" in texto and "C3 · OK" in texto
    detalle = (salida / "resumen.md").read_text(encoding="utf-8")
    assert CIF_EMISOR in detalle and NOMBRE in detalle
    assert detalle.endswith("## Errores\n\n(ninguno)\n")


def test_f064_r16_resumen_versionable_sin_cif_ni_nombres(tmp_path):
    dobles = Dobles(tmp_path, _respuestas_tipicas())

    _codigo, _salida, resumen = _lanzar(tmp_path, dobles, ["FER-001", "GEN-002"])

    texto = resumen.read_text(encoding="utf-8")
    for valor in (CIF_CLIENTE, CIF_EMISOR, "b-99999999", NOMBRE, "99999999", "81873903"):
        assert valor not in texto
    assert "FER-001" in texto and "GEN-002" in texto
    assert texto.startswith("<!-- progress/comparar_proveedor_F-064.md -->")


def test_f064_r16_un_caso_roto_no_para_la_corrida_y_el_error_va_sin_valores(tmp_path):
    respuestas = _respuestas_tipicas()
    respuestas[("rama", "GEN-002")] = [ValueError(f"respuesta con {CIF_CLIENTE}")] + [(CIF_EMISOR, CIF_EMISOR)] * 2
    dobles = Dobles(tmp_path, respuestas)

    codigo, _salida, resumen = _lanzar(tmp_path, dobles, ["FER-001", "GEN-002"])

    assert codigo == 0
    assert len(dobles.llamadas) == 12
    texto = resumen.read_text(encoding="utf-8")
    assert CIF_CLIENTE not in texto
    assert "rama r1: IA1 · ValueError" in texto


def test_f064_r16_todo_fallido_sale_con_1(tmp_path):
    respuestas = {("base", "C-1"): [RuntimeError("x")] * 3, ("rama", "C-1"): [RuntimeError("x")] * 3}

    codigo, _salida, resumen = _lanzar(tmp_path, Dobles(tmp_path, respuestas), ["C-1"])

    assert codigo == 1
    assert resumen.exists()


def test_f064_r16_una_sola_variante_no_juzga(tmp_path):
    respuestas = {("rama", "C-1"): [(CIF_EMISOR, CIF_EMISOR)]}
    dobles = Dobles(tmp_path, respuestas)

    codigo, _salida, resumen = _lanzar(tmp_path, dobles, ["C-1"], "--variante", "rama", "--repeticiones", "1")

    assert codigo == 0
    assert dobles.bases == []
    assert "VEREDICTO: NO APLICA" in resumen.read_text(encoding="utf-8")


def test_f064_r16_la_salida_por_defecto_la_ignora_git_y_el_resumen_no():
    salida = cp.directorio_por_defecto().relative_to(RAIZ_REPO).as_posix() + "/base_r1.json"
    ignorado = subprocess.run(["git", "-C", str(RAIZ_REPO), "check-ignore", "-q", salida], check=False)
    resumen = cp.RUTA_RESUMEN_VERSIONABLE.relative_to(RAIZ_REPO).as_posix()
    versionable = subprocess.run(["git", "-C", str(RAIZ_REPO), "check-ignore", "-q", resumen], check=False)

    assert ignorado.returncode == 0
    assert versionable.returncode == 1


# --- R17 · paradas antes de gastar -----------------------------------------------


@pytest.mark.parametrize("variable", ["GEMINI_API_KEY", "OPENAI_API_KEY"])
def test_f064_r17_para_sin_la_clave_de_una_de_las_fases(tmp_path, capsys, variable):
    dobles = Dobles(tmp_path, {})

    codigo, _s, _r = _lanzar(tmp_path, dobles, ["C-1"], entorno=_entorno(**{variable: None}))

    assert codigo == 2
    assert variable in capsys.readouterr().err
    _nada_escrito(dobles, tmp_path)


def test_f064_r17_las_fases_usan_ia_primera_y_segunda_fase(tmp_path):
    dobles = Dobles(tmp_path, {("rama", "C-1"): [(CIF_EMISOR, CIF_EMISOR)]})
    entorno = _entorno(IA_PRIMERA_FASE="claude", IA_SEGUNDA_FASE="gemini", ANTHROPIC_API_KEY="k", OPENAI_API_KEY=None)

    codigo, _s, _r = _lanzar(tmp_path, dobles, ["C-1"], "--variante", "rama", "--repeticiones", "1", entorno=entorno)

    assert codigo == 0
    assert dobles.montajes[0][1] == {"IA1": "claude", "IA2": "gemini"}


def test_f064_r17_para_si_ningun_caso_tiene_albaran(tmp_path, capsys):
    dobles = Dobles(tmp_path, {})

    codigo, _s, _r = _lanzar(tmp_path, dobles, ["C-1"], con_pdf=[])

    assert codigo == 2
    assert "ningún caso tiene albarán" in capsys.readouterr().err
    assert dobles.llamadas == [] and dobles.montajes == []


def test_f064_r17_para_si_falla_el_git_show_de_la_base(tmp_path, capsys):
    dobles = Dobles(tmp_path, {})

    def sin_base(directorio, base):
        raise sv2_proveedor.BaseNoDisponible("sin la base pedida")

    fixtures = _fixtures(tmp_path, {"C-1": (CIF_EMISOR, "Hormigon")})
    dependencias = dobles.dependencias(fixtures)
    dependencias.ficheros_de_base = sin_base
    codigo = cp.main(
        ["--casos", "C-1", "--albaranes", str(_albaranes(tmp_path, ["C-1"])),
         "--salida", str(tmp_path / "salida"), "--resumen", str(tmp_path / "progress" / "r.md")],
        entorno=_entorno(), dependencias=dependencias,
    )

    assert codigo == 2
    assert "sin la base pedida" in capsys.readouterr().err
    _nada_escrito(dobles, tmp_path)


def test_f064_r17_para_si_un_caso_no_tiene_cif_esperado(tmp_path, capsys):
    dobles = Dobles(tmp_path, {})
    fixtures = _fixtures(tmp_path, {"C-1": ("@@NO_COMPARAR@@", "Hormigon")})
    codigo = cp.main(
        ["--casos", "C-1", "--albaranes", str(_albaranes(tmp_path, ["C-1"])),
         "--salida", str(tmp_path / "salida"), "--resumen", str(tmp_path / "progress" / "r.md")],
        entorno=_entorno(), dependencias=dobles.dependencias(fixtures),
    )

    assert codigo == 2
    assert "C-1" in capsys.readouterr().err
    _nada_escrito(dobles, tmp_path)


@pytest.mark.parametrize(
    "argumentos",
    [["--casos", ""], ["--repeticiones", "0"], ["--variante", "dev"]],
)
def test_f064_r17_rechaza_peticiones_mal_formadas(tmp_path, argumentos):
    with pytest.raises(SystemExit) as salida:
        cp.main(argumentos, entorno=_entorno(), dependencias=Dobles(tmp_path, {}).dependencias(tmp_path))
    assert salida.value.code == 2


# --- R15 · los YAML de la base ----------------------------------------------------


def test_f064_r15_ficheros_de_base_son_los_de_git_tal_cual(tmp_path):
    ficheros = sv2_proveedor.ficheros_de_base(tmp_path, base=BASE_FIJA)

    for clave, ruta in (("prompts", sv2_proveedor.RUTA_PROMPTS), ("reglas", sv2_proveedor.RUTA_REGLAS)):
        esperado = subprocess.run(
            ["git", "-C", str(RAIZ_REPO), "show", f"{BASE_FIJA}:{ruta}"], capture_output=True, check=True,
        ).stdout
        assert ficheros[clave].parent == tmp_path
        assert ficheros[clave].read_bytes() == esperado
    assert "{empresas_cliente}" not in ficheros["prompts"].read_text(encoding="utf-8")
    assert "proveedor_emisor" not in ficheros["reglas"].read_text(encoding="utf-8")


def test_f064_r15_ficheros_de_rama_son_los_del_arbol_de_trabajo():
    ficheros = sv2_proveedor.ficheros_de_rama()

    assert "{empresas_cliente}" in ficheros["prompts"].read_text(encoding="utf-8")
    assert "proveedor_emisor" in ficheros["reglas"].read_text(encoding="utf-8")


def test_f064_r15_la_base_llega_a_git_show(tmp_path, monkeypatch):
    llamadas: list[list[str]] = []

    class Proceso:
        returncode = 0
        stdout = b"x: 1\n"
        stderr = b""

    def run_de_mentira(argumentos, **_kwargs):
        llamadas.append(argumentos)
        return Proceso()

    monkeypatch.setattr(sv2_proveedor.subprocess, "run", run_de_mentira)
    sv2_proveedor.ficheros_de_base(tmp_path, base="abc1234")

    assert [a[-1] for a in llamadas] == [
        f"abc1234:{sv2_proveedor.RUTA_PROMPTS}", f"abc1234:{sv2_proveedor.RUTA_REGLAS}",
    ]


def test_f064_r15_sin_la_base_para(tmp_path):
    with pytest.raises(sv2_proveedor.BaseNoDisponible):
        sv2_proveedor.ficheros_de_base(tmp_path, base="no-existe-f064", raiz=tmp_path)


def test_f064_r15_la_base_del_cli_llega_a_los_ficheros(tmp_path):
    respuestas = {("base", "C-1"): [(CIF_EMISOR, CIF_EMISOR)], ("rama", "C-1"): [(CIF_EMISOR, CIF_EMISOR)]}
    dobles = Dobles(tmp_path, respuestas)

    _lanzar(tmp_path, dobles, ["C-1"], "--base", "abc1234", "--repeticiones", "1")

    assert dobles.bases == ["abc1234"]
    assert dobles.montajes[0][0] == ("base", "rama")


def test_f064_r16_un_caso_sin_albaran_va_a_error_sin_llamar_al_llm(tmp_path):
    respuestas = {("base", "C-1"): [(CIF_EMISOR, CIF_EMISOR)], ("rama", "C-1"): [(CIF_EMISOR, CIF_EMISOR)]}
    dobles = Dobles(tmp_path, respuestas)

    codigo, salida, resumen = _lanzar(tmp_path, dobles, ["C-1", "C-2"], "--repeticiones", "1", con_pdf=["C-1"])

    assert codigo == 0
    assert {(v, c) for v, c, _i, _t in dobles.llamadas} == {("base", "C-1"), ("rama", "C-1")}
    assert "C-2 (base r1: preproceso · SinAlbaran; rama r1: preproceso · SinAlbaran)" in resumen.read_text(
        encoding="utf-8"
    )
    assert "ERROR (SinAlbaran)" in (salida / "resumen.md").read_text(encoding="utf-8")


def test_f064_r17_un_caso_sin_fixture_para(tmp_path):
    assert cp.esperado_de("NO-EXISTE", tmp_path) is None
    assert cp.tipologia_de("NO-EXISTE", tmp_path) == ""


def test_f064_r14_clasificar_categoriza_cada_ejecucion_y_su_mayoria():
    """Un resultado válido se clasifica por su CIF; uno con error o ausente es `error`."""
    error = {"error": {"fase": "IA2", "tipo": "X", "motivo": "m"}}
    corrida = cp.Corrida(
        casos=["A"], variantes=["rama"], repeticiones=3,
        proveedores={"IA1": "gemini", "IA2": "openai"}, modelos={"IA1": "m", "IA2": "m"},
        resultados={"rama": [
            {"A": {"ia1": {"nombre": NOMBRE, "cif": CIF_CLIENTE}, "ia2": {"nombre": NOMBRE, "cif": CIF_EMISOR}}},
            {"A": {"ia1": {"nombre": NOMBRE, "cif": None}, "ia2": error}},
            {"A": {"ia1": {"nombre": NOMBRE, "cif": CIF_CLIENTE}, "ia2": None}},
        ]},
    )

    clasificacion = cp.clasificar(corrida, {"A": CIF_EMISOR}, PROPIOS)["A"]["rama"]

    assert clasificacion["ia1"] == ["cliente", "nulo", "cliente"]
    assert clasificacion["ia2"] == ["emisor", "error", "error"]
    assert clasificacion["mayoria"] == {"ia1": "cliente", "ia2": "error"}


# --- Detalle de los informes (fijado tras la campaña de mutación) ---------------


def test_f064_r16_informes_cabecera_modelos_y_llamadas(tmp_path, capsys):
    dobles = Dobles(tmp_path, _respuestas_tipicas())

    _codigo, salida, resumen = _lanzar(tmp_path, dobles, ["FER-001", "GEN-002"])

    assert "comparar_proveedor: 24 llamadas (IA1 gemini · IA2 openai) · variantes base, rama" in capsys.readouterr().err
    carga = json.loads((salida / "base_r2.json").read_text(encoding="utf-8"))
    assert carga["modelos"] == {"IA1": "gemini-2.5-flash", "IA2": "gpt-5"}
    assert carga["repeticion"] == 2 and carga["variante"] == "base"
    texto = resumen.read_text(encoding="utf-8")
    assert re.search(r"rama `[0-9a-f]{7,}`", texto)
    assert "## Ejecuciones con error\n\n(ninguno)\n" in texto
    assert "AVISO" not in texto  # la base sí dio un CIF cliente (FER-001)
    assert "| cliente | 1 | 1 | 0 | 0 |" in texto
    assert "- **base tras IA1** · emisor: GEN-002 · cliente: FER-001" in texto


def test_f064_r16_el_modelo_sale_del_entorno(tmp_path):
    dobles = Dobles(tmp_path, {("rama", "C-1"): [(CIF_EMISOR, CIF_EMISOR)]})

    _codigo, salida, _r = _lanzar(
        tmp_path, dobles, ["C-1"], "--variante", "rama", "--repeticiones", "1",
        entorno=_entorno(GEMINI_MODEL="modelo-de-mentira"),
    )

    carga = json.loads((salida / "rama_r1.json").read_text(encoding="utf-8"))
    assert carga["modelos"] == {"IA1": "modelo-de-mentira", "IA2": "gpt-5"}


def test_f064_r16_sin_cliente_en_la_base_el_resumen_avisa(tmp_path):
    respuestas = {("base", "C-1"): [(CIF_EMISOR, CIF_EMISOR)], ("rama", "C-1"): [(CIF_EMISOR, CIF_EMISOR)]}

    _codigo, _s, resumen = _lanzar(tmp_path, Dobles(tmp_path, respuestas), ["C-1"], "--repeticiones", "1")

    assert "AVISO: la base no dio ningún CIF cliente" in resumen.read_text(encoding="utf-8")


def test_f064_r16_detalle_con_los_valores_de_cada_ejecucion(tmp_path):
    respuestas = {
        ("base", "C-1"): [(CIF_CLIENTE, None)],
        ("rama", "C-1"): [ValueError("x")],
    }

    _codigo, salida, _r = _lanzar(tmp_path, Dobles(tmp_path, respuestas), ["C-1"], "--repeticiones", "1")

    detalle = (salida / "resumen.md").read_text(encoding="utf-8")
    assert (
        "| caso | esperado | base r1 IA1 | base r1 IA2 | rama r1 IA1 | rama r1 IA2 "
        "| base IA1 | base IA2 | rama IA1 | rama IA2 |"
    ) in detalle
    assert (
        f"| C-1 | `{CIF_EMISOR}` | `{CIF_CLIENTE}` | null | ERROR (ValueError) | ERROR (ValueError) "
        "| cliente | nulo | error | error |"
    ) in detalle
    nombres = detalle[detalle.index("## proveedor_nombre leído"): detalle.index("## Errores")]
    assert nombres.count(NOMBRE) == 2 and "rama" not in nombres
    assert f"- C-1 · base r1 IA1: '{NOMBRE}'" in nombres
    errores = detalle[detalle.index("## Errores"):]
    assert "C-1 · rama r1 IA1: ValueError" in errores and "base" not in errores


def test_f064_r15_git_show_vacio_tambien_para(tmp_path, monkeypatch):
    class Vacio:
        returncode = 0
        stdout = b""
        stderr = b""

    monkeypatch.setattr(sv2_proveedor.subprocess, "run", lambda *_a, **_k: Vacio())

    with pytest.raises(sv2_proveedor.BaseNoDisponible):
        sv2_proveedor.ficheros_de_base(tmp_path, base="abc1234")


def test_f064_r16_un_solo_cliente_en_la_base_ya_reproduce_el_incidente():
    clasificacion = _clasif({"A": (["cliente", "emisor", "emisor"], E3)}, {"A": (E3, E3)})

    assert cp.veredicto(clasificacion, ["base", "rama"])["reproduce_incidente"] is True


def test_f064_r16_cabecera_con_y_sin_commits():
    corrida = cp.Corrida(
        casos=[], variantes=["base", "rama"], repeticiones=1,
        proveedores={"IA1": "gemini", "IA2": "openai"}, modelos={"IA1": "m1", "IA2": "m2"},
    )

    con = cp._cabecera(corrida, {"rama": "aaaaaaa", "base": "bbbbbbb"}, "dev", "F")[0]
    sin = cp._cabecera(corrida, {}, "dev", "F")[0]

    assert con == "- Fecha: F · rama `aaaaaaa` · base `dev` (`bbbbbbb`)"
    assert sin == "- Fecha: F · rama `?` · base `dev` (`?`)"


def test_f064_r16_escribir_crea_directorios_anidados_y_reescribe(tmp_path):
    corrida = cp.Corrida(
        casos=["A"], variantes=["rama"], repeticiones=1,
        proveedores={"IA1": "gemini", "IA2": "openai"}, modelos={"IA1": "m", "IA2": "m"},
        resultados={"rama": [{"A": {"ia1": {"nombre": "Ñ", "cif": CIF_EMISOR}, "ia2": {"nombre": "Ñ", "cif": None}}}]},
    )
    salida = tmp_path / "a" / "b" / "salida"
    resumen = tmp_path / "c" / "d" / "resumen.md"

    for _vez in range(2):
        cp.escribir(corrida, {"A": CIF_EMISOR}, salida, resumen, {}, "dev", "F")

    texto = (salida / "rama_r1.json").read_text(encoding="utf-8")
    assert texto.startswith('{\n  "variante": "rama",\n  "repeticion": 1,')
    assert '"nombre": "Ñ"' in texto
    assert resumen.is_file()


def test_f064_r14_sv2_va_el_primero_en_el_path(monkeypatch):
    """Los paquetes de primer nivel de sv2 (`application`, `domain`) tienen que
    ganar a cualquier otro `application` del path: sv2 va en la posición 0."""
    monkeypatch.setattr(sv2_proveedor.sys, "path", ["otro", "y-otro"])

    sv2_proveedor._con_sv2_en_path()
    sv2_proveedor._con_sv2_en_path()

    assert sv2_proveedor.sys.path == [str(sv2_proveedor.RAIZ_SV2), "otro", "y-otro"]


def test_f064_demostracion_el_mutante_28_es_equivalente():
    """Demostración EJECUTABLE de la equivalencia del superviviente #28 (RM5), diferencial.

    `ejecutar` decide si alguna ejecución salió con
    `"error" not in (resultado.get("ia1") or {"error": True})`. El mutante
    cambia el centinela a `{"error": False}`. Se toma la expresión del
    `comparar_proveedor.py` real, se fabrica «la otra forma» sustituyendo el
    texto (el mutante si el fichero trae el original y al revés, para que una
    campaña que lo inyecte en el propio fichero lo siga viendo equivalente) y
    se comparan las dos sobre un dominio amplio de `resultado`: cero
    discrepancias. El control (centinela sin la clave `error`) NO es
    equivalente y tiene que discrepar: la comparación no es ciega. Si la línea
    cambia y no queda ninguna de las dos formas, el test avisa.
    """
    import itertools
    from pathlib import Path

    fuente = Path(cp.__file__).read_text(encoding="utf-8")
    original = '"error" not in (resultado.get("ia1") or {"error": True})'
    mutado = '"error" not in (resultado.get("ia1") or {"error": False})'
    control = '"error" not in (resultado.get("ia1") or {"ok": True})'
    forma = {fuente.count(original), fuente.count(mutado)}
    assert forma == {0, 1}, "la línea del #28 cambió: rehacer la justificación"
    presente, otra = (original, mutado) if original in fuente else (mutado, original)

    def _cargar(expresion: str):
        funcion = eval(f"lambda resultado: {expresion}")  # noqa: S307 — fuente propia

        def salida(resultado):
            # El resultado O la excepción: un valor no iterable rompe igual a las dos.
            try:
                return funcion(resultado)
            except Exception as error:  # noqa: BLE001 - se compara también el fallo
                return type(error).__name__

        return salida

    real, variante, ciego = _cargar(presente), _cargar(otra), _cargar(control)

    valores_ia1 = [
        None, {}, "", 0, [], False,
        {"error": True}, {"error": False}, {"error": None}, {"error": {"fase": "IA1", "tipo": "X", "motivo": "m"}},
        {"nombre": None, "cif": None}, {"nombre": "N", "cif": CIF_EMISOR}, {"cif": CIF_CLIENTE, "error": 0},
        {"Error": True}, {"errores": True}, "error", "sin fallo", ["error"], 1, True,
    ]
    resultados = [{}]
    resultados += [{"ia1": valor} for valor in valores_ia1]
    resultados += [{"ia1": valor, "ia2": otro} for valor, otro in itertools.product(valores_ia1, [None, {"error": True}])]
    resultados += [{"ia2": {"cif": CIF_EMISOR}}, {"error": True}]

    discrepancias = [r for r in resultados if real(r) != variante(r)]
    assert len(resultados) == 63
    assert discrepancias == []
    assert any(real(r) != ciego(r) for r in resultados), "el control tenía que discrepar"
