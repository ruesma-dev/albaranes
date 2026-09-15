# evals/revision/informe.py
"""El informe de la importación, en Markdown. Es lo que evita el falso verde.

Una importación que se traga 57 de 59 albaranes sin decir cuáles faltan es
peor que no importar: el banco parecería completo. Por eso aquí todo lo que se
quedó fuera sale **con nombre y apellidos**, y los rojos que nacen esperados
—familias que aún no están en el catálogo, criterios de residuos sin
implementar— van agrupados aparte de los defectos reales.
"""

from __future__ import annotations

from evals.revision.modelos import (
    DEFECTO_CONOCIDO,
    NO_REGRESION,
    InformeImportacion,
)

#: Qué significa cada tipo de fallo del emparejado, en una línea (R21).
MOTIVOS: dict[str, str] = {
    "codigo_duplicado": "dos ficheros del mismo formato resuelven al mismo código",
    "codigo_sin_fila": "el fichero existe pero su código no está en el Excel",
    "fila_sin_fichero": "la fila existe pero no hay documento suyo en la carpeta",
    "nombre_vacio": "el nombre queda vacío tras aplicar la regla del código",
}


def render(informe: InformeImportacion) -> str:
    """El informe entero. Sin reloj: dos pasadas iguales dan el mismo texto."""
    partes = [
        "<!-- progress/import_F-045.md -->",
        "# F-045 · Importación de la revisión manual al banco de evals",
        "",
        "Generado por `python -m evals.revision`. **No se edita a mano**: la",
        "siguiente importación lo reescribe.",
        "",
        *_resumen(informe),
        *_clasificacion(informe),
        *_documentos(informe),
        *_rojos_esperados(informe),
        *_celdas(informe),
        *_avisos(informe),
    ]
    return "\n".join(partes).rstrip() + "\n"


def _resumen(informe: InformeImportacion) -> list[str]:
    return [
        "## Resumen",
        "",
        f"- Filas leídas de la tabla plana: **{informe.filas_leidas}**",
        f"- Casos (albaranes): **{len(informe.casos)}**, "
        f"de los que **{len(informe.caso_ids_nuevos)}** son nuevos",
        f"- Libros escritos: {', '.join(informe.libros_escritos) or '(ninguno: en seco)'}",
        f"- Copias de seguridad: {len(informe.copias)}",
        "",
    ]


def _clasificacion(informe: InformeImportacion) -> list[str]:
    reparto = informe.por_clasificacion
    lineas = [
        "## Cómo se reparten los casos",
        "",
        "El comentario del Excel dice qué falla HOY, no qué se espera. Vacío",
        "significa que el caso salió BIEN y hay que seguir comprobándolo.",
        "",
        f"- **no regresión** (deben salir VERDES): {reparto[NO_REGRESION]}",
        f"- **defecto conocido** (rojo esperado hasta su ficha): "
        f"{reparto[DEFECTO_CONOCIDO]}",
        "",
    ]
    for clasificacion, titulo in (
        (NO_REGRESION, "No regresión"),
        (DEFECTO_CONOCIDO, "Defecto conocido"),
    ):
        casos = [c.caso_id for c in informe.casos if c.clasificacion == clasificacion]
        lineas += [f"{titulo}: {', '.join(sorted(casos)) or '(ninguno)'}", ""]
    return lineas


def _documentos(informe: InformeImportacion) -> list[str]:
    lineas = [
        "## Documentos de entrada",
        "",
        "Lo que la regla de nombres no cubre sale listado UNO A UNO: una",
        "importación que se traga casos en silencio es peor que no importar.",
        "",
    ]
    if not informe.fallos_documentos:
        lineas += ["Sin incidencias: cada caso tiene su documento.", ""]
        return lineas
    for fallo in informe.fallos_documentos:
        lineas.append(f"- {fallo}")
    lineas.append("")
    return lineas


def _rojos_esperados(informe: InformeImportacion) -> list[str]:
    lineas = [
        "## Rojos que nacen esperados",
        "",
        "No son regresiones ni defectos de clasificación: son huecos conocidos",
        "del sistema que estos casos ponen a la vista.",
        "",
        "### La familia aún no existe en el catálogo",
        "",
    ]
    if informe.familias_pendientes:
        for familia, casos in sorted(informe.familias_pendientes.items()):
            lineas.append(f"- `{familia}`: {', '.join(sorted(casos))}")
    else:
        lineas.append("- (ninguna)")
    lineas += ["", "### Criterios de residuos sin implementar", ""]
    if informe.criterios_residuos:
        for criterio, casos in sorted(informe.criterios_residuos.items()):
            lineas.append(f"- `{criterio}`: {', '.join(sorted(casos))}")
    else:
        lineas.append("- (ninguno)")
    lineas.append("")
    return lineas


def _celdas(informe: InformeImportacion) -> list[str]:
    lineas = [
        "## Celdas escritas por libro y columna",
        "",
        "`valor` = afirmado por el humano · `?` = no lo afirmó, no se compara ·",
        "`vacía` = afirmó que no hay dato (se compara contra `null`).",
        "",
        "| Libro | Tabla | Columna | valor | `?` | vacía |",
        "|---|---|---|---:|---:|---:|",
    ]
    for libro, tablas in informe.celdas.items():
        for tabla, columnas in tablas.items():
            for columna, cubo in columnas.items():
                lineas.append(
                    f"| {libro} | {tabla} | {columna} | {cubo['valor']} | "
                    f"{cubo['interrogante']} | {cubo['vacia']} |"
                )
    lineas.append("")
    return lineas


def _avisos(informe: InformeImportacion) -> list[str]:
    if not informe.avisos:
        return []
    return ["## Avisos", "", *(f"- {aviso}" for aviso in informe.avisos), ""]
