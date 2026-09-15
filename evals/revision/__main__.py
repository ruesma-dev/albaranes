# evals/revision/__main__.py
"""`python -m evals.revision --origen <fichero.xlsx>`: el volcado completo.

Orquesta y nada más: leer, repartir, emparejar los documentos, escribir los
libros y dejar el informe. Cada paso vive en su módulo.

Dos cosas que decide este punto de entrada:

- **Todo o nada.** Si el vocabulario no reconoce algo, se aborta ANTES de
  tocar un solo libro (R5). Media importación es peor que ninguna: nadie
  sabría qué mitad mirar.
- **`--dry-run` no toca el disco** salvo para dejar el informe. Es la forma
  de ver qué haría la importación sin arriesgar los libros del humano, que no
  se versionan.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from evals import conversor
from evals.revision import albaranes, escritura, informe as informe_mod, lectura, mapa
from evals.revision import reparto, vocabulario
from evals.revision.modelos import InformeImportacion

#: Dónde queda el informe de la última importación.
RUTA_INFORME = Path(__file__).resolve().parents[2] / "progress" / "import_F-045.md"

#: Carpeta de los documentos de entrada (fuera de git: llevan precios).
RUTA_ORIGINALES = Path(__file__).resolve().parents[1] / "inputs" / "albaranes"


def ejecutar(
    origen: Path | str,
    dir_ground_truth: Path | str = conversor.RUTA_GROUND_TRUTH,
    dir_originales: Path | str = RUTA_ORIGINALES,
    ruta_mapa: Path | str = mapa.RUTA_MAPA,
    dry_run: bool = False,
) -> InformeImportacion:
    """La importación entera. Levanta antes de escribir si algo no cuadra."""
    vocab = vocabulario.cargar()
    filas = lectura.leer(origen)
    casos = reparto.agrupar_por_albaran(filas, vocab)
    mapa_actual = mapa.cargar(ruta_mapa)
    mapa_nuevo, nuevos = reparto.asignar_casos_id(casos, mapa_actual)

    plan = _emparejar(casos, dir_originales, mapa_nuevo)
    gemelos = reparto.crear_gemelos(
        casos, {copia.gemelo_de: "imagen" for copia in plan.copias if copia.gemelo_de}
    )
    _anotar_documentos(casos + gemelos, plan, mapa_nuevo)

    resultado = InformeImportacion(
        filas_leidas=len(filas),
        casos=casos + gemelos,
        caso_ids_nuevos=nuevos,
        fallos_documentos=[
            f"`{fallo.tipo}` — {fallo.detalle}" for fallo in plan.fallos
        ],
        familias_pendientes=reparto.familias_pendientes(casos + gemelos),
    )
    tablas = _repartir_todo(resultado, vocab)

    if not dry_run:
        resultado.libros_escritos = _escribir(tablas, resultado, dir_ground_truth)
        mapa.guardar(mapa_nuevo, ruta_mapa)
        albaranes.renombrar(plan.copias, dir_originales)
    else:
        resultado.avisos.append(
            "Pasada EN SECO (`--dry-run`): no se ha escrito ningún libro, ni el "
            "mapa, ni se ha renombrado ningún documento."
        )
    if plan.ignorados:
        resultado.avisos.append(
            f"{len(plan.ignorados)} fichero(s) de la carpeta de entrada no tienen "
            f"extensión de albarán y se ignoran: {', '.join(plan.ignorados)}"
        )
    resultado.avisos.append(
        "`INPUTS.CONTRATO_LINEAS`, `INPUTS.CONDICIONES` e `IA3` TABLA 3 no se "
        "alimentan (design §3): sin líneas de contrato, los casos nuevos solo "
        "son evaluables con LLM y la corrida determinista sigue viviendo de los "
        "7 casos RES."
    )
    resultado.avisos.append(
        "DESVIACIÓN de `design.md` §3, pendiente de que la cierre el humano: "
        "`INPUTS.CASOS.tipologia` lleva la PESTAÑA y no la familia de "
        "documento. `MAPA_TIPO_FAMILIA` de `evals/procesos/sv5_valoracion.py` "
        "y `sv6_build.py` está indexado por pestaña, así que escribir la "
        "familia dejaría TODOS los casos —incluidos los 7 RES que ya "
        "funcionaban— en `tipo_familia='otro'`. La familia de documento queda "
        "en `evals/mapa_casos.json` y agrupada más arriba en este informe."
    )
    return resultado


def _emparejar(casos, dir_originales, mapa_nuevo) -> albaranes.Emparejado:
    """Casa los documentos de la carpeta de entrada con los casos del Excel."""
    carpeta = Path(dir_originales)
    ficheros = sorted(p.name for p in carpeta.iterdir() if p.is_file()) if carpeta.is_dir() else []
    return albaranes.emparejar(
        {reparto.normalizar_codigo(caso.codigo): caso.caso_id for caso in casos},
        ficheros,
        caso_ids=set(mapa_nuevo),
    )


def _anotar_documentos(casos, plan: albaranes.Emparejado, mapa_nuevo: dict) -> None:
    """Lleva al caso y al mapa el documento con el que se quedó cada uno."""
    por_caso = {copia.caso_id: copia for copia in plan.copias}
    for nombre in plan.ya_colocados:
        tronco = Path(nombre).stem
        registro = mapa_nuevo.setdefault(tronco, {})
        registro.setdefault("formato", albaranes.formato_de(nombre))
        registro.setdefault("nombre_original", nombre)
    for caso in casos:
        copia = por_caso.get(caso.caso_id)
        registro = mapa_nuevo.setdefault(caso.caso_id, {})
        if copia is not None:
            caso.fichero = copia.destino
            registro.update(
                {
                    "clave": caso.clave,
                    "codigo": caso.codigo,
                    "pestana": caso.destino.pestana,
                    "nombre_original": copia.origen,
                    "formato": copia.formato,
                    "gemelo_de": copia.gemelo_de or None,
                }
            )
        elif registro.get("nombre_original"):
            caso.fichero = f"{caso.caso_id}{Path(registro['nombre_original']).suffix.lower()}"
        registro.setdefault("clave", caso.clave)
        registro.setdefault("codigo", caso.codigo)
        registro.setdefault("pestana", caso.destino.pestana)
        registro.setdefault("gemelo_de", caso.gemelo_de or None)


def _repartir_todo(resultado: InformeImportacion, vocab) -> dict:
    """`{fase: {pestaña: {tabla: [filas]}}}`, contando cada celda por el camino."""
    tablas: dict[str, dict[str, dict[str, list[dict]]]] = {}
    for caso in resultado.casos:
        criterios = reparto.criterios_residuos(caso, vocab)
        for criterio in criterios:
            resultado.criterios_residuos.setdefault(criterio, []).append(caso.caso_id)
        for fase, por_tabla in reparto.repartir(caso, vocab).items():
            destino = tablas.setdefault(fase, {}).setdefault(caso.destino.pestana, {})
            for tabla, filas in por_tabla.items():
                destino.setdefault(tabla, []).extend(filas)
                for registro in filas:
                    for columna, valor in registro.items():
                        resultado.contar(fase, tabla, columna, valor)
    return tablas


def _escribir(tablas: dict, resultado: InformeImportacion, dir_ground_truth) -> list[str]:
    """Copia, crea las pestañas que falten y funde las filas de cada caso."""
    import openpyxl

    carpeta = Path(dir_ground_truth)
    caso_ids = {caso.caso_id for caso in resultado.casos}
    pestanas_nuevas = tuple(
        sorted({caso.destino.pestana for caso in resultado.casos})
    )
    escritos: list[str] = []

    for definicion in conversor.LIBROS:
        ruta = carpeta / definicion.fichero
        creadas = False
        if definicion.por_tipologia:
            libro = openpyxl.load_workbook(ruta)
            try:
                creadas = bool(escritura.asegurar_pestanas(libro, pestanas_nuevas))
                if creadas:
                    libro.save(ruta)
            finally:
                libro.close()

        trabajo = [
            (pestana, definiciones, _filas_de(definicion, pestana, por_pestana))
            for pestana, definiciones in definicion.tablas_por_pestana.items()
            for por_pestana in [tablas.get(definicion.fase, {})]
        ]
        trabajo = [(p, d, f) for p, d, f in trabajo if any(f.values())]

        # Primero se mira si el libro cambia; solo entonces se copia y se
        # escribe. Guardar un libro idéntico le cambiaría el sha256 y dejaría
        # 264 fixtures «modificados» sin que hubiera cambiado ni un dato (R18).
        cambia = creadas or any(
            escritura.escribir_pestana(
                ruta, pestana, _definiciones(defs), filas, caso_ids, ejecutar=False
            )
            for pestana, defs, filas in trabajo
        )
        if not cambia:
            continue
        resultado.copias.append(str(escritura.copia_de_seguridad(ruta)))
        for pestana, defs, filas in trabajo:
            escritura.escribir_pestana(ruta, pestana, _definiciones(defs), filas, caso_ids)
        escritos.append(definicion.fichero)
    return escritos


def _definiciones(tablas) -> tuple[escritura.DefTabla, ...]:
    """Del contrato que declara el conversor al que consume la escritura."""
    return tuple(escritura.DefTabla(tabla.titulo, tabla.clave) for tabla in tablas)


def _filas_de(definicion, pestana: str, por_pestana: dict) -> dict[str, list[dict]]:
    """En los libros por tipología cada pestaña es una familia; en INPUTS, no.

    `INPUTS` reparte el mismo caso entre pestañas distintas (CASOS,
    LINEAS_ALBARAN…), así que ahí se juntan las filas de todas las familias.
    """
    if definicion.por_tipologia:
        return dict(por_pestana.get(pestana, {}))
    juntas: dict[str, list[dict]] = {}
    for tablas in por_pestana.values():
        for tabla, filas in tablas.items():
            juntas.setdefault(tabla, []).extend(filas)
    return juntas


def main(argv: list[str] | None = None) -> int:
    """Punto de entrada. 0 si todo fue bien, 1 si no se escribió nada."""
    analizador = argparse.ArgumentParser(
        prog="python -m evals.revision",
        description="Vuelca la revisión manual del humano al banco de evals.",
    )
    analizador.add_argument("--origen", default=str(lectura.RUTA_FUENTE))
    analizador.add_argument("--ground-truth", default=str(conversor.RUTA_GROUND_TRUTH))
    analizador.add_argument("--originales", default=str(RUTA_ORIGINALES))
    analizador.add_argument("--mapa", default=str(mapa.RUTA_MAPA))
    analizador.add_argument("--informe", default=str(RUTA_INFORME))
    analizador.add_argument(
        "--dry-run",
        action="store_true",
        help="no escribe libros, mapa ni renombra: solo deja el informe",
    )
    opciones = analizador.parse_args(argv)

    try:
        resultado = ejecutar(
            opciones.origen,
            opciones.ground_truth,
            opciones.originales,
            opciones.mapa,
            dry_run=opciones.dry_run,
        )
    except (
        lectura.ErrorLectura,
        vocabulario.ErrorVocabulario,
        reparto.ErrorReparto,
        escritura.ErrorEscritura,
    ) as error:
        print(str(error), file=sys.stderr)
        return 1

    destino = Path(opciones.informe)
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(informe_mod.render(resultado), encoding="utf-8")
    print(
        f"{len(resultado.casos)} caso(s), {len(resultado.caso_ids_nuevos)} nuevo(s); "
        f"informe en {destino}"
    )
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
