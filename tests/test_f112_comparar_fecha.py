# tests/test_f112_comparar_fecha.py
"""F-112 · R19–R24, R29: el comparador de la FECHA base/rama, sin LLM.

Se prueba todo lo que no es llamar al LLM: los cuatro juegos y sus
referencias, la clasificación de la fecha, la mayoría, el efecto de IA2, el
veredicto C1–C7, las dos fases con un servicio doble, los informes (el
versionable SIN fechas ni datos del albarán) y las paradas con código 2 antes
de gastar, también con `--solo-validar`.

Dobles con fechas inventadas y el centinela ``CENTINELA-F112``.
"""

from __future__ import annotations

import json
from collections.abc import Callable
from datetime import date, timedelta
from pathlib import Path

import pytest

from evals import comparar_fecha as cf
from evals.procesos import sv2_fecha

CENTINELA = "CENTINELA-F112"
ENTORNO = {"GEMINI_API_KEY": "clave-de-mentira", "OPENAI_API_KEY": "clave-de-mentira"}


# --- Dobles y ficheros ------------------------------------------------------------


def _banco(tmp_path: Path, casos: dict[str, tuple[str | None, str]]) -> Path:
    """`casos[caso_id] = (fecha esperada, tipología)` → `fixtures/IA1/<caso>.json`."""
    raiz = tmp_path / "fixtures"
    (raiz / "IA1").mkdir(parents=True, exist_ok=True)
    for caso, (fecha, tipologia) in casos.items():
        datos = {"caso_id": caso, "tipologia": tipologia,
                 "tablas": {"cabeceras": [{"caso_id": caso, "fecha": fecha}]}}
        (raiz / "IA1" / f"{caso}.json").write_text(json.dumps(datos), encoding="utf-8")
    (raiz / "IA1" / "_indice.json").write_text(json.dumps({"casos": []}), encoding="utf-8")
    return raiz


def _json_casos(ruta: Path, casos: list[dict]) -> Path:
    ruta.write_text(json.dumps({"version": 1, "casos": casos}), encoding="utf-8")
    return ruta


def _a(caso_id: str, esperada: str, recibido: str, clase: str = "anio", tipologia: str = "Residuos") -> dict:
    return {"caso_id": caso_id, "tipologia": tipologia, "clase": clase,
            "fecha_esperada": esperada, "recibido": recibido}


def _d(caso_id: str, esperada: str, recibido_utc: str) -> dict:
    return {"caso_id": caso_id, "tipologia": "generico", "fecha_esperada": esperada,
            "recibido_utc": recibido_utc}


class Dobles:
    """`respuestas[(variante, caso_id)]`: por llamada, `(fecha_ia1, fecha_ia2)` o una excepción."""

    def __init__(self, tmp_path: Path, respuestas: dict | Callable | None = None) -> None:
        self.tmp_path = tmp_path
        self.respuestas = respuestas or {}
        self.llamadas: list[tuple] = []
        self.montajes: list[tuple] = []
        self.bases: list[str] = []
        self.fallo_base: BaseException | None = None
        self._contador: dict[tuple, int] = {}

    def ficheros_de_base(self, directorio: Path, base: str) -> dict:
        self.bases.append(base)
        if self.fallo_base is not None:
            raise self.fallo_base
        return {"prompts": Path(directorio) / "p.yaml", "reglas": Path(directorio) / "r.yaml"}

    def ficheros_de_rama(self) -> dict:
        return {"prompts": self.tmp_path / "p.yaml", "reglas": self.tmp_path / "r.yaml"}

    def montar_extractor(self, ficheros, proveedores, entorno):
        self.montajes.append((tuple(sorted(ficheros)), dict(proveedores)))

        def extraer(variante, caso_id, ruta, tipologia, referencia):
            self.llamadas.append((variante, caso_id, tipologia, referencia))
            if callable(self.respuestas):
                valor = self.respuestas(variante, caso_id, referencia)
            else:
                clave = (variante, caso_id)
                indice = self._contador.get(clave, 0)
                self._contador[clave] = indice + 1
                valor = self.respuestas[clave][indice]
            if isinstance(valor, BaseException):
                raise valor
            uno, dos = valor
            return {"ia1": {"fecha": uno}, "ia2": {"fecha": dos}}

        return extraer

    def dependencias(self, fixtures: Path) -> cf.Dependencias:
        return cf.Dependencias(
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


def _lanzar(tmp_path, dobles, *extra, banco=None, casos_a=None, casos_d=None, con_pdf=None, entorno=None):
    banco = banco if banco is not None else {}
    casos_a = casos_a if casos_a is not None else []
    casos_d = casos_d if casos_d is not None else []
    fixtures = _banco(tmp_path, banco)
    ruta_a = _json_casos(tmp_path / "casos_fecha.json", casos_a)
    ruta_d = _json_casos(tmp_path / "casos_fecha_sinteticos.json", casos_d)
    todos = [*banco, *(c.get("caso_id") for c in [*casos_a, *casos_d] if isinstance(c, dict) and c.get("caso_id"))]
    albaranes = _albaranes(tmp_path, con_pdf if con_pdf is not None else todos)
    salida, resumen = tmp_path / "salida", tmp_path / "progress" / "comparar_fecha_F-112.md"
    codigo = cf.main(
        ["--albaranes", str(albaranes), "--salida", str(salida), "--resumen", str(resumen),
         "--casos-fecha", str(ruta_a), "--sinteticos", str(ruta_d), *extra],
        entorno=entorno if entorno is not None else dict(ENTORNO),
        dependencias=dobles.dependencias(fixtures),
    )
    return codigo, salida, resumen


def _nada_gastado(dobles: Dobles, tmp_path: Path) -> None:
    assert dobles.llamadas == [] and dobles.montajes == []
    assert not (tmp_path / "salida").exists()
    assert not (tmp_path / "progress").exists()


# --- R19 · los juegos ---------------------------------------------------------------


def test_f112_r19_juego_a_con_la_recepcion_real_en_madrid(tmp_path):
    ruta = _json_casos(tmp_path / "a.json", [
        _a("FEC-001", "2026-10-17", "2026-10-28T07:12:00Z"),
        _a("FEC-002", "2026-12-31", "2026-12-31T23:30:00Z", clase="antigua"),
        _a("FEC-003", "2026-10-01", "2026-10-02", clase="dudoso"),
    ])

    casos = cf.juego_a(ruta)

    assert [(c.juego, c.caso_id, c.clase, c.tipologia) for c in casos] == [
        ("A", "FEC-001", "anio", "Residuos"), ("A", "FEC-002", "antigua", "Residuos"),
        ("A", "FEC-003", "dudoso", "Residuos"),
    ]
    assert [c.referencia for c in casos] == [date(2026, 10, 28), date(2027, 1, 1), date(2026, 10, 2)]
    assert casos[0].esperada == date(2026, 10, 17)


def test_f112_r19_juego_a_vacio_es_valido(tmp_path):
    assert cf.juego_a(_json_casos(tmp_path / "a.json", [])) == []


def test_f112_r19_el_json_versionado_del_juego_a_valida():
    assert isinstance(cf.juego_a(cf.RUTA_CASOS_FECHA), list)


def test_f112_r19_juego_b_muestra_fija_y_referencia_mas_siete(tmp_path):
    banco = {f"GEN-{i:03d}": (f"2026-0{1 + i % 9}-1{i % 10}", "Generico") for i in range(30)}
    banco["SIN-FECHA"] = (None, "Generico")
    banco["NO-COMP"] = ("@@NO_COMPARAR@@", "Generico")
    fixtures = _banco(tmp_path, banco)

    uno, dos = cf.juego_b(fixtures), cf.juego_b(fixtures)

    assert len(uno) == cf.MUESTRA_B == 20
    assert [c.caso_id for c in uno] == [c.caso_id for c in dos]  # semilla fija
    assert [c.caso_id for c in uno] == sorted(c.caso_id for c in uno)
    assert {"SIN-FECHA", "NO-COMP"}.isdisjoint(c.caso_id for c in uno)
    assert all(c.referencia == c.esperada + timedelta(days=7) for c in uno)
    assert cf.juego_b(fixtures, semilla=1) != uno


def test_f112_r19_juego_b_con_pocos_casos_los_toma_todos(tmp_path):
    fixtures = _banco(tmp_path, {"GEN-001": ("2026-03-04", "Generico"), "GEN-002": ("2025-05-06", "Generico")})
    assert [c.caso_id for c in cf.juego_b(fixtures)] == ["GEN-001", "GEN-002"]


def test_f112_r19_juego_c_anteriores_a_2025_con_730_dias(tmp_path):
    fixtures = _banco(tmp_path, {
        "HOR-001": ("2024-12-31", "Hormigon"),
        "HOR-002": ("2025-01-01", "Hormigon"),
        "RES-001": ("2023-05-06", "Residuos"),
    })

    casos = cf.juego_c(fixtures)

    assert [(c.caso_id, c.tipologia) for c in casos] == [("HOR-001", "Hormigon"), ("RES-001", "Residuos")]
    assert casos[0].referencia == date(2024, 12, 31) + timedelta(days=730)


def test_f112_r19_el_banco_real_tiene_b_a_20_y_c_a_13():
    assert len(cf.juego_b(cf.RUTA_FIXTURES)) == 20
    assert len(cf.juego_c(cf.RUTA_FIXTURES)) == 13


def test_f112_r19_juego_d_con_fecha_recepcion_de(tmp_path):
    ruta = _json_casos(tmp_path / "d.json", [
        _d("SIN-001", "2026-12-28", "2027-01-03T09:00:00Z"),
        _d("SIN-006", "2027-01-01", "2026-12-31T23:30:00Z"),
    ])

    casos = cf.juego_d(ruta)

    assert [c.referencia for c in casos] == [date(2027, 1, 3), date(2027, 1, 1)]
    assert all(c.juego == "D" and c.clase == "" for c in casos)


def test_f112_r19_construir_juegos_en_orden_y_solo_los_pedidos(tmp_path):
    fixtures = _banco(tmp_path, {"HOR-001": ("2024-12-31", "Hormigon")})
    ruta_a = _json_casos(tmp_path / "a.json", [_a("FEC-001", "2026-10-17", "2026-10-28")])
    ruta_d = _json_casos(tmp_path / "d.json", [_d("SIN-001", "2026-12-28", "2027-01-03")])

    todos = cf.construir_juegos(list(cf.JUEGOS), fixtures, ruta_a, ruta_d)
    solo = cf.construir_juegos(["D", "A"], fixtures, ruta_a, ruta_d)

    assert [c.clave for c in todos] == ["A/FEC-001", "B/HOR-001", "C/HOR-001", "D/SIN-001"]
    assert [c.clave for c in solo] == ["A/FEC-001", "D/SIN-001"]


# --- R21 · clasificación, mayoría y efecto de IA2 ------------------------------------

ESPERADA, REFERENCIA = date(2026, 10, 17), date(2026, 10, 28)


@pytest.mark.parametrize(
    ("valor", "categoria"),
    [
        ("2026-10-17", "exacta"),
        ("2026-10-17T00:00:00", "exacta"),
        ("2026-10-28", "referencia"),
        ("2020-10-17", "solo_anio"),
        ("2026-10-18", "otra"),
        ("17/10/2026", "otra"),
        (None, "nula"),
        ("  ", "nula"),
    ],
)
def test_f112_r21_clasificar_fecha(valor, categoria):
    assert cf.clasificar_fecha(valor, ESPERADA, REFERENCIA) == categoria


def test_f112_r21_la_referencia_igual_a_la_esperada_es_exacta():
    assert cf.clasificar_fecha("2026-10-17", ESPERADA, ESPERADA) == "exacta"


def test_f112_r21_mayoritaria():
    assert cf.mayoritaria(["exacta", "exacta", "otra"]) == "exacta"
    assert cf.mayoritaria(["exacta", "otra"]) == "inestable"
    assert cf.mayoritaria([]) == "error"


CASO = cf.Caso("A", "FEC-001", "Residuos", ESPERADA, REFERENCIA, "anio")


@pytest.mark.parametrize(
    ("ia1", "ia2", "efecto"),
    [
        ("2020-10-17", "2026-10-17", "corrige"),
        ("2026-10-17", "2020-10-17", "estropea"),
        ("2026-10-17", None, "estropea"),
        ("2020-10-17", "2021-10-17", "cambia"),
        (None, "2021-10-17", "cambia"),
        ("2020-10-17", "2020-10-17", "igual"),
        ("2026-10-17", "2026-10-17", "igual"),
        (None, None, "igual"),
    ],
)
def test_f112_r21_efecto_de_ia2(ia1, ia2, efecto):
    assert cf.efecto_ia2({"ia1": {"fecha": ia1}, "ia2": {"fecha": ia2}}, CASO) == efecto


def test_f112_r21_sin_efecto_si_una_fase_falla():
    error = {"error": {"fase": "IA2", "tipo": "X", "motivo": "x"}}
    assert cf.efecto_ia2({"ia1": {"fecha": "2026-10-17"}, "ia2": error}, CASO) is None
    assert cf.efecto_ia2({"ia1": error, "ia2": {"fecha": "2026-10-17"}}, CASO) is None
    assert cf.efecto_ia2({"ia1": None, "ia2": {"fecha": "2026-10-17"}}, CASO) is None


# --- R20 · las dos fases con un servicio doble ----------------------------------------


class _Respuesta:
    def __init__(self, datos: dict) -> None:
        self.parsed = self
        self._datos = datos

    def model_dump(self) -> dict:
        return self._datos


class ServicioDoble:
    def __init__(self, fase_1=None, fase_2=None) -> None:
        self.fase_1, self.fase_2 = fase_1, fase_2
        self.llamadas: list[dict] = []

    def extract_phase_1(self, **kwargs):
        self.llamadas.append({"fase": 1, **kwargs})
        if isinstance(self.fase_1, BaseException):
            raise self.fase_1
        return _Respuesta(self.fase_1)

    def review_phase_2(self, **kwargs):
        self.llamadas.append({"fase": 2, **kwargs})
        if isinstance(self.fase_2, BaseException):
            raise self.fase_2
        return _Respuesta(self.fase_2)


PROVEEDORES = {"IA1": "gemini", "IA2": "openai"}


def test_f112_r20_dos_fases_con_la_referencia_y_el_prompt_de_la_tipologia():
    servicio = ServicioDoble(
        {"cabecera": {"fecha": "2020-10-17"}, "lineas": []},
        {"documento_revisado": {"cabecera": {"fecha": "2026-10-17"}}},
    )

    salida = sv2_fecha.dos_fases(servicio, ["material"], PROVEEDORES, "Residuos", REFERENCIA)

    assert salida == {"ia1": {"fecha": "2020-10-17"}, "ia2": {"fecha": "2026-10-17"}}
    uno, dos = servicio.llamadas
    assert uno["fecha_recepcion"] == dos["fecha_recepcion"] == REFERENCIA
    assert uno["provider"] == "gemini" and dos["provider"] == "openai"
    assert uno["prompt_key"] == "albaran_factura_es"
    assert dos["prompt_key"] == "albaran_revision_fase2_residuos"
    assert dos["phase_1_json"] == {"cabecera": {"fecha": "2020-10-17"}, "lineas": []}
    assert "contexto_correo" not in uno and "sigrid_context" not in dos


def test_f112_r20_sin_documento_revisado_ia2_vale_lo_de_ia1():
    servicio = ServicioDoble({"cabecera": {"fecha": "2026-10-17"}}, {"review_status": "ok"})
    salida = sv2_fecha.dos_fases(servicio, [], PROVEEDORES, "", None)
    assert salida["ia2"] == {"fecha": "2026-10-17"}
    assert servicio.llamadas[1]["prompt_key"] == "albaran_revision_fase2_es"


def test_f112_r20_si_ia1_falla_ia2_no_se_llama():
    servicio = ServicioDoble(RuntimeError(CENTINELA))
    salida = sv2_fecha.dos_fases(servicio, [], PROVEEDORES, "", REFERENCIA)
    assert salida["ia1"]["error"]["fase"] == "IA1"
    assert salida["ia2"]["error"]["tipo"] == "SinFase1"
    assert len(servicio.llamadas) == 1


def test_f112_r20_si_ia2_falla_ia1_se_conserva():
    servicio = ServicioDoble({"cabecera": {"fecha": "2026-10-17"}}, ValueError("x"))
    salida = sv2_fecha.dos_fases(servicio, [], PROVEEDORES, "", REFERENCIA)
    assert salida["ia1"] == {"fecha": "2026-10-17"}
    assert salida["ia2"]["error"]["fase"] == "IA2"


def test_f112_r20_fecha_de_documentos_sin_cabecera():
    assert sv2_fecha.fecha_de({}) == {"fecha": None}
    assert sv2_fecha.fecha_de(None) == {"fecha": None}
    assert sv2_fecha.fecha_de({"cabecera": {"fecha": date(2026, 1, 2)}}) == {"fecha": "2026-01-02"}


# --- R22 · veredicto -----------------------------------------------------------------


def _corrida(casos: list[cf.Caso], respuestas: dict, variantes=("base", "rama"), juegos=cf.JUEGOS,
             repeticiones=1) -> cf.Corrida:
    """`respuestas[(variante, clave)] = [(ia1, ia2), ...]` por repetición."""
    resultados = {
        v: [
            {c.clave: {"ia1": {"fecha": respuestas[(v, c.clave)][r][0]},
                       "ia2": {"fecha": respuestas[(v, c.clave)][r][1]}} for c in casos}
            for r in range(repeticiones)
        ]
        for v in variantes
    }
    return cf.Corrida(casos=casos, juegos=list(juegos), variantes=list(variantes), repeticiones=repeticiones,
                      proveedores=PROVEEDORES, modelos={"IA1": "m1", "IA2": "m2"}, resultados=resultados)


def _escenario_verde() -> tuple[list[cf.Caso], dict]:
    """Un caso por juego (y uno `antigua`), con la rama acertando todo."""
    casos = [
        cf.Caso("A", "FEC-001", "Residuos", date(2026, 10, 17), date(2026, 10, 28), "anio"),
        cf.Caso("A", "FEC-002", "Residuos", date(2021, 3, 4), date(2026, 10, 22), "antigua"),
        cf.Caso("B", "GEN-001", "Generico", date(2026, 5, 6), date(2026, 5, 13)),
        cf.Caso("C", "HOR-001", "Hormigon", date(2024, 2, 3), date(2026, 2, 2)),
        cf.Caso("D", "SIN-001", "generico", date(2026, 12, 28), date(2027, 1, 3)),
    ]
    respuestas = {}
    for c in casos:
        bien = c.esperada.isoformat()
        respuestas[("rama", c.clave)] = [(bien, bien)]
        respuestas[("base", c.clave)] = [(bien, bien)]
    # La base tenía el fallo del año en el caso `anio`.
    respuestas[("base", "A/FEC-001")] = [("2020-10-17", "2020-10-17")]
    return casos, respuestas


def _juicio(casos, respuestas, **kwargs) -> dict:
    corrida = _corrida(casos, respuestas, **kwargs)
    return cf.veredicto(corrida, cf.clasificar(corrida))


def test_f112_r22_verde_si_se_cumple_todo():
    juicio = _juicio(*_escenario_verde())
    assert juicio["global"] == "VERDE"
    assert all(juicio[f"C{i}"]["ok"] for i in range(1, 8))


def test_f112_r22_sin_las_dos_variantes_no_aplica():
    casos, respuestas = _escenario_verde()
    assert _juicio(casos, respuestas, variantes=("rama",))["global"] == "NO APLICA"


def test_f112_r22_sin_los_cuatro_juegos_no_aplica():
    casos, respuestas = _escenario_verde()
    juicio = _juicio([c for c in casos if c.juego != "D"], respuestas, juegos=("A", "B", "C"))
    assert juicio["global"] == "NO APLICA"
    assert "cuatro juegos" in juicio["motivo"]


def test_f112_r22_c1_umbral_del_80_por_ciento():
    casos = [cf.Caso("A", f"FEC-{i:03d}", "Residuos", date(2026, 10, 1 + i), date(2026, 10, 28), "anio")
             for i in range(5)]
    otros = _escenario_verde()[0][2:]
    respuestas = {}
    for c in casos + otros:
        bien = c.esperada.isoformat()
        respuestas[("base", c.clave)] = respuestas[("rama", c.clave)] = [(bien, bien)]
    # 4 de 5 = 80 %: OK. 3 de 5: KO.
    respuestas[("rama", "A/FEC-000")] = [("2020-10-01", "2020-10-01")]
    respuestas[("base", "A/FEC-000")] = [("2020-10-01", "2020-10-01")]
    assert _juicio(casos + otros, respuestas)["C1"]["ok"]
    respuestas[("rama", "A/FEC-001")] = [("2020-10-02", "2020-10-02")]
    juicio = _juicio(casos + otros, respuestas)
    assert not juicio["C1"]["ok"] and juicio["global"] == "ROJO"
    assert "umbral 4" in juicio["C1"]["detalle"]


def test_f112_r22_c1_rama_no_puede_quedar_por_debajo_de_base():
    casos = [cf.Caso("A", f"FEC-{i:03d}", "Residuos", date(2026, 10, 1 + i), date(2026, 10, 28), "anio")
             for i in range(5)]
    otros = _escenario_verde()[0][2:]
    respuestas = {}
    for c in casos + otros:
        bien = c.esperada.isoformat()
        respuestas[("base", c.clave)] = respuestas[("rama", c.clave)] = [(bien, bien)]
    respuestas[("rama", "A/FEC-000")] = [("2020-10-01", "2020-10-01")]  # rama 4, base 5
    assert not _juicio(casos + otros, respuestas)["C1"]["ok"]


def test_f112_r22_c1_cuenta_solo_los_anio_y_sin_anio_es_ko():
    casos, respuestas = _escenario_verde()
    casos = [c for c in casos if c.caso_id != "FEC-001"]
    juicio = _juicio(casos, respuestas)
    assert not juicio["C1"]["ok"]
    assert "sin casos `anio`" in juicio["C1"]["detalle"]


def test_f112_r22_c1_los_dudoso_no_cuentan():
    casos, respuestas = _escenario_verde()
    dudoso = cf.Caso("A", "FEC-009", "Residuos", date(2026, 9, 9), date(2026, 10, 28), "dudoso")
    respuestas[("rama", dudoso.clave)] = respuestas[("base", dudoso.clave)] = [("2020-09-09", "2020-09-09")]
    juicio = _juicio([*casos, dudoso], respuestas)
    assert juicio["C1"]["ok"]
    assert "rama = 1 de 1" in juicio["C1"]["detalle"]


def test_f112_r22_c2_un_caso_de_b_que_pierde_la_exacta():
    casos, respuestas = _escenario_verde()
    respuestas[("rama", "B/GEN-001")] = [("2026-05-06", "2026-05-07")]
    juicio = _juicio(casos, respuestas)
    assert not juicio["C2"]["ok"] and "GEN-001" in juicio["C2"]["detalle"]


@pytest.mark.parametrize(("leida", "ok"), [("2026-02-03", False), ("2026-02-02", False), ("2024-02-04", True)])
def test_f112_r22_c3_un_antiguo_de_c_que_pasa_a_solo_anio_o_referencia(leida, ok):
    casos, respuestas = _escenario_verde()
    respuestas[("rama", "C/HOR-001")] = [("2024-02-03", leida)]
    juicio = _juicio(casos, respuestas)
    assert juicio["C3"]["ok"] is ok


def test_f112_r22_c4_cualquier_referencia_en_rama_aunque_sea_tras_ia1():
    casos, respuestas = _escenario_verde()
    respuestas[("rama", "B/GEN-001")] = [("2026-05-13", "2026-05-06")]
    juicio = _juicio(casos, respuestas)
    assert not juicio["C4"]["ok"] and "rama: 1" in juicio["C4"]["detalle"]
    respuestas[("base", "B/GEN-001")] = [("2026-05-13", "2026-05-13")]
    respuestas[("rama", "B/GEN-001")] = [("2026-05-06", "2026-05-06")]
    assert _juicio(casos, respuestas)["C4"]["ok"]  # la base no cuenta


def test_f112_r22_c5_ia2_estropea_en_rama():
    casos, respuestas = _escenario_verde()
    respuestas[("rama", "D/SIN-001")] = [("2026-12-28", "2027-12-28")]
    juicio = _juicio(casos, respuestas)
    assert not juicio["C5"]["ok"] and "SIN-001" in juicio["C5"]["detalle"]


def test_f112_r22_c6_todos_los_d_exactos_y_sin_d_es_ko():
    casos, respuestas = _escenario_verde()
    respuestas[("rama", "D/SIN-001")] = [("2027-12-28", "2027-12-28")]
    assert not _juicio(casos, respuestas)["C6"]["ok"]
    sin_d = [c for c in casos if c.juego != "D"]
    juicio = _juicio(sin_d, respuestas)
    assert not juicio["C6"]["ok"] and "sin casos D" in juicio["C6"]["detalle"]


def test_f112_r22_c7_los_antigua_no_se_mueven():
    casos, respuestas = _escenario_verde()
    respuestas[("rama", "A/FEC-002")] = [("2026-03-04", "2026-03-04")]
    juicio = _juicio(casos, respuestas)
    assert not juicio["C7"]["ok"] and "FEC-002" in juicio["C7"]["detalle"]


def test_f112_r22_la_mayoria_de_las_repeticiones_manda():
    casos, respuestas = _escenario_verde()
    respuestas = {k: v * 3 for k, v in respuestas.items()}
    respuestas[("rama", "B/GEN-001")] = [("2026-05-06", "2026-05-06"), ("2026-05-06", "2026-05-06"),
                                         ("2026-05-08", "2026-05-08")]
    assert _juicio(casos, respuestas, repeticiones=3)["C2"]["ok"]


# --- R23 · paradas con código 2 antes de gastar ---------------------------------------

BANCO = {"HOR-001": ("2024-02-03", "Hormigon")}


def test_f112_r23_sin_clave_de_un_proveedor_para(tmp_path, capsys):
    dobles = Dobles(tmp_path)
    codigo, *_ = _lanzar(tmp_path, dobles, banco=BANCO, entorno={"GEMINI_API_KEY": "x"})
    assert codigo == 2
    assert "OPENAI_API_KEY" in capsys.readouterr().err
    _nada_gastado(dobles, tmp_path)


def test_f112_r23_ningun_caso_con_albaran_para(tmp_path, capsys):
    dobles = Dobles(tmp_path)
    codigo, *_ = _lanzar(tmp_path, dobles, banco=BANCO, con_pdf=[])
    assert codigo == 2
    assert "ningún caso tiene albarán" in capsys.readouterr().err
    _nada_gastado(dobles, tmp_path)


@pytest.mark.parametrize(
    ("casos", "motivo"),
    [
        ([{"tipologia": "Residuos", "clase": "anio", "fecha_esperada": "2026-10-17", "recibido": "2026-10-28"}],
         "no tiene `caso_id`"),
        ([_a("FEC-001", "17/10/2026", "2026-10-28")], "`fecha_esperada`"),
        ([_a("FEC-001", "2026-02-30", "2026-10-28")], "`fecha_esperada`"),
        ([_a("FEC-001", "2026-10-17", "ayer")], "`recibido`"),
        ([{**_a("FEC-001", "2026-10-17", "2026-10-28"), "recibido": 7}], "`recibido`"),
        ([_a("FEC-001", "2026-10-17", "2026-10-28", clase="rara")], "`clase`"),
        ([{**_a("FEC-001", "2026-10-17", "2026-10-28"), "tipologia": None}], "`tipologia`"),
        ([_a("FEC-001", "2026-10-17", "2026-10-28"), _a("FEC-001", "2026-10-18", "2026-10-28")],
         "repite el `caso_id` del caso nº 1"),
        (["no-es-un-objeto"], "no es un objeto"),
    ],
    ids=["sin_id", "formato", "fecha_imposible", "recibido_texto", "recibido_numero", "clase",
         "tipologia", "repetido", "no_objeto"],
)
def test_f112_r23_casos_fecha_que_no_valida_para_sin_citar_su_contenido(tmp_path, capsys, casos, motivo):
    dobles = Dobles(tmp_path)
    codigo, *_ = _lanzar(tmp_path, dobles, banco=BANCO, casos_a=casos)
    error = capsys.readouterr().err
    assert codigo == 2
    assert motivo in error and "casos_fecha.json" in error
    assert "FEC-001" not in error and "2026-10" not in error and "17/10" not in error
    _nada_gastado(dobles, tmp_path)


@pytest.mark.parametrize(
    ("contenido", "motivo"),
    [(None, "no existe"), ("{roto", "no es un JSON"), ('{"version": 1}', "falta la lista"),
     ('[1, 2]', "falta la lista")],
)
def test_f112_r23_casos_fecha_ausente_o_roto_para(tmp_path, capsys, contenido, motivo):
    ruta = tmp_path / "a.json"
    if contenido is not None:
        ruta.write_text(contenido, encoding="utf-8")
    with pytest.raises(cf.Parada, match=motivo):
        cf.juego_a(ruta)


def test_f112_r23_sinteticos_que_no_validan_paran(tmp_path, capsys):
    dobles = Dobles(tmp_path)
    codigo, *_ = _lanzar(tmp_path, dobles, banco=BANCO, casos_d=[_d("SIN-001", "2026-12-28", "")])
    error = capsys.readouterr().err
    assert codigo == 2 and "casos_fecha_sinteticos.json" in error and "`recibido_utc`" in error
    _nada_gastado(dobles, tmp_path)


def test_f112_r23_falla_el_git_show_de_la_base(tmp_path, capsys):
    dobles = Dobles(tmp_path)
    dobles.fallo_base = sv2_fecha.BaseNoDisponible("`git show nada:...` falló")
    codigo, *_ = _lanzar(tmp_path, dobles, "--base", "nada", banco=BANCO)
    assert codigo == 2
    assert dobles.bases == ["nada"]
    _nada_gastado(dobles, tmp_path)


def test_f112_r23_solo_validar_comprueba_y_no_llama(tmp_path, capsys):
    dobles = Dobles(tmp_path)
    codigo, *_ = _lanzar(
        tmp_path, dobles, "--solo-validar", banco=BANCO,
        casos_a=[_a("FEC-001", "2026-10-17", "2026-10-28")], casos_d=[_d("SIN-001", "2026-12-28", "2027-01-03")],
    )
    salida = capsys.readouterr().out
    assert codigo == 0
    assert dobles.bases == ["dev"]  # la base también se comprueba
    assert "todo valida" in salida and "4 casos" in salida and "32 llamadas" in salida  # 4 × 2 variantes × 2 repeticiones × 2 fases
    _nada_gastado(dobles, tmp_path)


def test_f112_r23_solo_validar_tambien_para_con_codigo_2(tmp_path):
    dobles = Dobles(tmp_path)
    codigo, *_ = _lanzar(tmp_path, dobles, "--solo-validar", banco=BANCO, casos_a=[_a("X", "mal", "2026-10-28")])
    assert codigo == 2


def test_f112_r23_solo_validar_de_t9_sin_base(tmp_path):
    """El comando de T9: `--variante rama --juegos A --repeticiones 1 --solo-validar`."""
    dobles = Dobles(tmp_path)
    codigo, *_ = _lanzar(
        tmp_path, dobles, "--variante", "rama", "--juegos", "A", "--repeticiones", "1", "--solo-validar",
        casos_a=[_a("FEC-001", "2026-10-17", "2026-10-28")],
    )
    assert codigo == 0 and dobles.bases == []


@pytest.mark.parametrize("argumentos", [["--juegos", "A,X"], ["--juegos", ","], ["--repeticiones", "0"]])
def test_f112_r23_argumentos_invalidos(tmp_path, argumentos):
    with pytest.raises(SystemExit):
        cf.main(argumentos, entorno=dict(ENTORNO), dependencias=Dobles(tmp_path).dependencias(tmp_path))


# --- R20, R24, R29 · corrida completa e informes --------------------------------------


def _todo_bien_salvo_estropea(variante, caso_id, referencia):
    esperadas = {"FEC-001": "2026-10-17", "FEC-002": "2021-03-04", "HOR-001": "2024-02-03",
                 "SIN-001": "2026-12-28"}
    bien = esperadas[caso_id]
    if variante == "base" and caso_id == "FEC-001":
        return ("2020-10-17", "2020-10-17")
    if variante == "rama" and caso_id == "SIN-001":
        return (bien, "2027-12-28")  # IA2 estropea
    return (bien, bien)


def _lanzar_completa(tmp_path, respuestas=_todo_bien_salvo_estropea, *extra):
    dobles = Dobles(tmp_path, respuestas)
    codigo, salida, resumen = _lanzar(
        tmp_path, dobles, "--repeticiones", "2", *extra, banco=BANCO,
        casos_a=[_a("FEC-001", "2026-10-17", "2026-10-28T07:12:00Z"),
                 _a("FEC-002", "2021-03-04", "2026-10-22", clase="antigua")],
        casos_d=[_d("SIN-001", "2026-12-28", "2027-01-03")],
    )
    return dobles, codigo, salida, resumen


def test_f112_r20_corrida_completa_llama_por_caso_variante_y_repeticion(tmp_path):
    dobles, codigo, _salida, _resumen = _lanzar_completa(tmp_path)

    assert codigo == 0
    # A (2) + B (1) + C (1) + D (1) = 5 casos × 2 variantes × 2 repeticiones.
    assert len(dobles.llamadas) == 20
    assert dobles.montajes == [(("base", "rama"), PROVEEDORES)]
    referencias = {(c, r) for _v, c, _t, r in dobles.llamadas}
    assert ("HOR-001", date(2024, 2, 10)) in referencias  # B: +7
    assert ("HOR-001", date(2026, 2, 2)) in referencias  # C: +730
    assert ("FEC-001", date(2026, 10, 28)) in referencias
    tipologias = {c: t for _v, c, t, _r in dobles.llamadas}
    assert tipologias["SIN-001"] == "generico" and tipologias["FEC-001"] == "Residuos"


def test_f112_r24_resumen_versionable_sin_fechas_ni_datos(tmp_path):
    _dobles, _codigo, _salida, resumen = _lanzar_completa(tmp_path)
    texto = resumen.read_text(encoding="utf-8")

    assert texto.startswith("<!-- progress/comparar_fecha_F-112.md -->")
    for juego in cf.JUEGOS:
        assert f"### Juego {juego}" in texto
    assert "VEREDICTO: ROJO" in texto  # C5 por el estropea de SIN-001
    assert "- C5 · KO" in texto and "- C1 · OK" in texto
    # Ni fechas leídas, ni esperadas, ni referencias, ni tipologías del juego A.
    for prohibido in ("2026-10-17", "2020-10-17", "2027-12-28", "2026-10-28", "2024-02-03", "Residuos"):
        assert prohibido not in texto, prohibido


def test_f112_r29_tabla_del_efecto_de_ia2_y_lista_de_estropea(tmp_path):
    _dobles, _codigo, _salida, resumen = _lanzar_completa(tmp_path)
    texto = resumen.read_text(encoding="utf-8")

    assert "## Efecto de IA2" in texto
    assert "| Juego | Variante | corrige | estropea | cambia | igual |" in texto
    assert "| D | rama | 0 | 2 | 0 | 0 |" in texto
    assert "| A | base | 0 | 0 | 0 | 4 |" in texto
    assert "- `estropea` en rama: SIN-001" in texto
    assert "- `estropea` en base: (ninguno)" in texto


def test_f112_r24_detalle_con_valores_en_salida(tmp_path):
    _dobles, _codigo, salida, _resumen = _lanzar_completa(tmp_path)

    assert sorted(p.name for p in salida.iterdir()) == [
        "base_r1.json", "base_r2.json", "rama_r1.json", "rama_r2.json", "resumen.md",
    ]
    detalle = (salida / "resumen.md").read_text(encoding="utf-8")
    assert "`2027-12-28`" in detalle and "A/FEC-001" in detalle
    carga = json.loads((salida / "rama_r1.json").read_text(encoding="utf-8"))
    assert carga["casos"]["D/SIN-001"] == {"ia1": {"fecha": "2026-12-28"}, "ia2": {"fecha": "2027-12-28"}}


def test_f112_r24_una_variante_da_no_aplica(tmp_path):
    dobles, codigo, _salida, resumen = _lanzar_completa(tmp_path, _todo_bien_salvo_estropea, "--variante", "rama")
    texto = resumen.read_text(encoding="utf-8")
    assert codigo == 0
    assert "VEREDICTO: NO APLICA" in texto and "dos variantes" in texto
    assert dobles.montajes == [(("rama",), PROVEEDORES)]


def test_f112_r24_errores_aislados_y_sin_valores(tmp_path):
    def respuestas(variante, caso_id, referencia):
        if caso_id == "HOR-001":
            return RuntimeError(f"{CENTINELA} 2026-10-17")
        return _todo_bien_salvo_estropea(variante, caso_id, referencia)

    _dobles, codigo, salida, resumen = _lanzar_completa(tmp_path, respuestas)
    texto = resumen.read_text(encoding="utf-8")
    assert codigo == 0
    assert "- B/HOR-001 (base r1: IA1 · RuntimeError" in texto
    assert CENTINELA not in texto
    assert "ERROR (RuntimeError)" in (salida / "resumen.md").read_text(encoding="utf-8")


def test_f112_r24_un_caso_sin_albaran_es_error_y_el_resto_sigue(tmp_path):
    dobles = Dobles(tmp_path, _todo_bien_salvo_estropea)
    codigo, _salida, resumen = _lanzar(
        tmp_path, dobles, "--repeticiones", "1", banco=BANCO,
        casos_a=[_a("FEC-001", "2026-10-17", "2026-10-28")], con_pdf=["HOR-001"],
    )
    assert codigo == 0
    assert "- A/FEC-001 (base r1: preproceso · SinAlbaran" in resumen.read_text(encoding="utf-8")
    assert all(c == "HOR-001" for _v, c, _t, _r in dobles.llamadas)


def test_f112_r24_si_todo_falla_codigo_1(tmp_path):
    dobles = Dobles(tmp_path, lambda *a: RuntimeError("x"))
    codigo, *_ = _lanzar(tmp_path, dobles, "--repeticiones", "1", banco=BANCO)
    assert codigo == 1


def test_f112_r24_por_defecto_la_salida_va_a_evals_salidas():
    assert cf.directorio_por_defecto().parent == cf.RAIZ_REPO / "evals" / "salidas" / "comparar_fecha"
    assert cf.RUTA_RESUMEN_VERSIONABLE == cf.RAIZ_REPO / "progress" / "comparar_fecha_F-112.md"
    assert cf._relativa(cf.RAIZ_REPO / "evals" / "x") == "evals/x"
    assert cf._relativa(Path("/fuera/del/repo")).endswith("fuera/del/repo")


def test_f112_r19_la_referencia_de_d_sale_de_sv2():
    """Nochevieja: el día de Madrid, no el UTC (R1 vía el propio fichero de sv2)."""
    assert cf.fecha_recepcion_de("2026-12-31T23:30:00Z") == date(2027, 1, 1)
    assert cf.fecha_recepcion_de("nada") is None
