<!-- progress/import_F-045.md -->
# F-045 · Importación de la revisión manual al banco de evals

Generado por `python -m evals.revision`. **No se edita a mano**: la
siguiente importación lo reescribe.

## Resumen

- Filas leídas de la tabla plana: **142**
- Casos (albaranes): **59**, de los que **0** son nuevos
- Libros comprobados: 6
- Libros escritos: (ninguno: ningún libro cambiaba; ver R18)
- Copias de seguridad: 0

## Cómo se reparten los casos

El comentario del Excel dice qué falla HOY, no qué se espera. Vacío
significa que el caso salió BIEN y hay que seguir comprobándolo.

- **no regresión** (deben salir VERDES): 11
- **defecto conocido** (rojo esperado hasta su ficha): 48

No regresión: COM-001, FER-001, FER-002, GEN-001, GEN-003, GEN-004, GEN-006, GEN-008, GEN-009, HOR-007, HOR-011

Defecto conocido: ALQ-001, FER-003, GEN-002, GEN-005, GEN-007, GEN-010, GRA-001, GRA-002, HOR-001, HOR-002, HOR-003, HOR-004, HOR-005, HOR-006, HOR-008, HOR-009, HOR-010, HOR-012, HOR-013, HOR-014, HOR-015, HOR-016, HOR-017, MOR-001, MOR-002, MOR-003, MOR-004, RES-001, RES-002, RES-003, RES-004, RES-005, RES-006, RES-007, RES-008, RES-009, RES-010, RES-011, RES-012, RES-013, RES-014, RES-015, RES-016, RES-017, RES-018, RES-019, RES-020, RES-021

## Casos que cambian de grupo

Respecto a la importación anterior, **ningún caso cambia de grupo**.

## Documentos de entrada

Lo que la regla de nombres no cubre sale listado UNO A UNO: una
importación que se traga casos en silencio es peor que no importar.

### Plan de renombrado

Revísalo ANTES de renombrar: deshacer un renombrado sobre una
asignación equivocada es caro, y un caso emparejado con el papel de
otro no lo detecta nadie. `estrategia` dice por qué casó cada uno:
`exacto` (el nombre ES el código), `subcadena` (el código va dentro
del nombre) o `sin_ceros` (además, ignorando los ceros de la
izquierda).

| Fichero | Caso | Estrategia |
|---|---|---|
| `SALMEDINA_0000168.pdf` | RES-001 | exacto |
| `SALMEDINA_0000589.pdf` | RES-003 | exacto |
| `SALMEDINA_0001977.pdf` | RES-005 | exacto |
| `SALMEDINA_0003935.pdf` | RES-002 | exacto |
| `SALMEDINA_0003967.pdf` | RES-004 | exacto |
| `SALMEDINA_0025146.pdf` | RES-006 | exacto |
| `SALMEDINA_0026122.pdf` | RES-007 | exacto |

**No se ha renombrado nada**: hay que pedirlo con `--renombrar`.

### Lo que se quedó fuera

- `codigo_sin_fila` — '0669 BLOSSOM II _117.png': ninguna de las estrategias (exacto, subcadena, sin_ceros) encuentra en el Excel un código de albarán que case con este nombre.
- `codigo_sin_fila` — '0669 BLOSSOM II _37.png': ninguna de las estrategias (exacto, subcadena, sin_ceros) encuentra en el Excel un código de albarán que case con este nombre.
- `codigo_sin_fila` — '0669 BLOSSOM II _51.png': ninguna de las estrategias (exacto, subcadena, sin_ceros) encuentra en el Excel un código de albarán que case con este nombre.
- `fila_sin_fichero` — RES-020 (código 'MC26442903'): el Excel lo trae pero no hay ningún documento suyo en la carpeta de entrada.
- `fila_sin_fichero` — RES-021 (código 'MC26443249'): el Excel lo trae pero no hay ningún documento suyo en la carpeta de entrada.

## Rojos que nacen esperados

No son regresiones ni defectos de clasificación: son huecos conocidos
del sistema que estos casos ponen a la vista.

### La familia aún no existe en el catálogo

- `combustible`: COM-001
- `ferreteria`: FER-001, FER-002, FER-003
- `grava`: GRA-001, GRA-002

### Criterios de residuos sin implementar

- `canon_por_ler`: RES-003, RES-004, RES-005
- `incremento_por_ano`: RES-009, RES-010, RES-011, RES-014, RES-015, RES-018
- `minimo_1_tn`: RES-010, RES-011, RES-012, RES-013, RES-014, RES-015, RES-017, RES-018, RES-019

## Celdas escritas por libro y columna

`valor` = afirmado por el humano · `?` = no lo afirmó, no se compara ·
`vacía` = afirmó que no hay dato (se compara contra `null`).

| Libro | Tabla | Columna | valor | `?` | vacía |
|---|---|---|---:|---:|---:|
| IA1 | cabeceras | caso_id | 59 | 0 | 0 |
| IA1 | cabeceras | fichero_albaran | 57 | 0 | 2 |
| IA1 | cabeceras | proveedor_nombre | 59 | 0 | 0 |
| IA1 | cabeceras | proveedor_cif | 0 | 59 | 0 |
| IA1 | cabeceras | fecha | 59 | 0 | 0 |
| IA1 | cabeceras | numero_albaran | 0 | 59 | 0 |
| IA1 | cabeceras | obra_codigo | 0 | 59 | 0 |
| IA1 | cabeceras | obra_nombre | 0 | 59 | 0 |
| IA1 | cabeceras | forma_pago | 0 | 59 | 0 |
| IA1 | cabeceras | comentario | 48 | 0 | 11 |
| IA1 | lineas | caso_id | 110 | 0 | 0 |
| IA1 | lineas | num_linea | 110 | 0 | 0 |
| IA1 | lineas | descripcion_esperada | 110 | 0 | 0 |
| IA1 | lineas | cantidad | 110 | 0 | 0 |
| IA1 | lineas | unidad | 110 | 0 | 0 |
| IA1 | lineas | precio_unitario | 12 | 0 | 98 |
| IA1 | lineas | descuentos | 12 | 0 | 98 |
| IA1 | lineas | importe | 4 | 0 | 106 |
| IA1 | lineas | codigo_imputacion | 0 | 110 | 0 |
| IA1 | lineas | comentario | 65 | 0 | 45 |
| IA3 | lineas_valoradas | caso_id | 110 | 0 | 0 |
| IA3 | lineas_valoradas | num_linea | 110 | 0 | 0 |
| IA3 | lineas_valoradas | match_method | 27 | 83 | 0 |
| IA3 | lineas_valoradas | codigo_producto_contrato | 0 | 83 | 27 |
| IA3 | lineas_valoradas | codigo_partida_final | 110 | 0 | 0 |
| IA3 | lineas_valoradas | precio_unitario_final | 109 | 1 | 0 |
| IA3 | lineas_valoradas | precio_source | 110 | 0 | 0 |
| IA3 | lineas_valoradas | importe_calculado | 109 | 1 | 0 |
| IA3 | lineas_valoradas | review_required | 0 | 110 | 0 |
| IA3 | lineas_valoradas | comentario | 65 | 0 | 45 |
| IA3 | sinteticas_esperadas | caso_id | 32 | 0 | 0 |
| IA3 | sinteticas_esperadas | num_linea_base | 32 | 0 | 0 |
| IA3 | sinteticas_esperadas | modifier_source | 0 | 32 | 0 |
| IA3 | sinteticas_esperadas | rol_linea | 0 | 32 | 0 |
| IA3 | sinteticas_esperadas | descripcion_esperada | 32 | 0 | 0 |
| IA3 | sinteticas_esperadas | cantidad | 32 | 0 | 0 |
| IA3 | sinteticas_esperadas | precio_unitario | 32 | 0 | 0 |
| IA3 | sinteticas_esperadas | codigo_partida | 32 | 0 | 0 |
| IA3 | sinteticas_esperadas | comentario | 26 | 0 | 6 |
| IA4 | conciliacion | caso_id | 27 | 0 | 0 |
| IA4 | conciliacion | num_linea | 27 | 0 | 0 |
| IA4 | conciliacion | concilia | 0 | 27 | 0 |
| IA4 | conciliacion | linea_contrato_esperada | 0 | 27 | 0 |
| IA4 | conciliacion | precio_unitario_esperado | 27 | 0 | 0 |
| IA4 | conciliacion | motivo | 0 | 0 | 27 |
| IA4 | conciliacion | comentario | 13 | 0 | 14 |
| INPUTS | caso | caso_id | 59 | 0 | 0 |
| INPUTS | caso | tipologia | 59 | 0 | 0 |
| INPUTS | caso | ia_destino | 59 | 0 | 0 |
| INPUTS | caso | origen | 59 | 0 | 0 |
| INPUTS | caso | contrato_codigo | 59 | 0 | 0 |
| INPUTS | caso | descripcion_caso | 59 | 0 | 0 |
| INPUTS | lineas_albaran | caso_id | 110 | 0 | 0 |
| INPUTS | lineas_albaran | num_linea | 110 | 0 | 0 |
| INPUTS | lineas_albaran | descripcion | 110 | 0 | 0 |
| INPUTS | lineas_albaran | cantidad | 110 | 0 | 0 |
| INPUTS | lineas_albaran | unidad | 110 | 0 | 0 |
| INPUTS | lineas_albaran | precio_unitario | 12 | 0 | 98 |
| INPUTS | lineas_albaran | descuentos | 12 | 0 | 98 |
| INPUTS | lineas_albaran | importe | 4 | 0 | 106 |
| INPUTS | lineas_albaran | codigo_imputacion | 0 | 0 | 110 |
| INPUTS | lineas_albaran | observaciones_albaran | 0 | 0 | 110 |
| FINAL | datos_generales | caso_id | 59 | 0 | 0 |
| FINAL | datos_generales | fichero | 57 | 0 | 2 |
| FINAL | datos_generales | obra | 59 | 0 | 0 |
| FINAL | datos_generales | proveedor | 59 | 0 | 0 |
| FINAL | datos_generales | cif | 59 | 0 | 0 |
| FINAL | datos_generales | fecha | 59 | 0 | 0 |
| FINAL | datos_generales | numero_albaran | 0 | 59 | 0 |
| FINAL | datos_generales | contrato_elegido | 59 | 0 | 0 |
| FINAL | datos_generales | total_valorado_esperado | 58 | 1 | 0 |
| FINAL | datos_generales | requiere_revision | 0 | 59 | 0 |
| FINAL | datos_generales | motivo_revision | 0 | 0 | 59 |
| FINAL | datos_generales | comentario | 48 | 0 | 11 |
| FINAL | lineas | caso_id | 110 | 0 | 0 |
| FINAL | lineas | num_linea | 110 | 0 | 0 |
| FINAL | lineas | descripcion | 110 | 0 | 0 |
| FINAL | lineas | cantidad_final | 110 | 0 | 0 |
| FINAL | lineas | unidad_final | 110 | 0 | 0 |
| FINAL | lineas | casa_con_contrato | 110 | 0 | 0 |
| FINAL | lineas | linea_contrato | 0 | 81 | 29 |
| FINAL | lineas | partida_final | 110 | 0 | 0 |
| FINAL | lineas | precio_unitario_final | 109 | 1 | 0 |
| FINAL | lineas | precio_source | 110 | 0 | 0 |
| FINAL | lineas | importe_final | 109 | 1 | 0 |
| FINAL | lineas | linea_a_revision | 0 | 110 | 0 |
| FINAL | lineas | comentario | 65 | 0 | 45 |
| FINAL | lineas_anadidas | caso_id | 32 | 0 | 0 |
| FINAL | lineas_anadidas | num_linea_base | 32 | 0 | 0 |
| FINAL | lineas_anadidas | concepto | 32 | 0 | 0 |
| FINAL | lineas_anadidas | cantidad | 32 | 0 | 0 |
| FINAL | lineas_anadidas | precio_unitario | 32 | 0 | 0 |
| FINAL | lineas_anadidas | partida | 32 | 0 | 0 |
| FINAL | lineas_anadidas | importe | 32 | 0 | 0 |
| FINAL | lineas_anadidas | comentario | 26 | 0 | 6 |
| IA2 | contexto | caso_id | 9 | 0 | 0 |
| IA2 | contexto | num_linea | 9 | 0 | 0 |
| IA2 | contexto | campo_contexto | 9 | 0 | 0 |
| IA2 | contexto | valor_esperado | 9 | 0 | 0 |
| IA2 | contexto | comentario | 9 | 0 | 0 |

## Avisos

- `INPUTS.CONTRATO_LINEAS`, `INPUTS.CONDICIONES` e `IA3` TABLA 3 no se alimentan (design §3): sin líneas de contrato, los casos nuevos solo son evaluables con LLM y la corrida determinista sigue viviendo de los 7 casos RES.
- DESVIACIÓN de `design.md` §3, pendiente de que la cierre el humano: `IA1.lineas.codigo_imputacion` sale `?` en TODAS las líneas. §3 dice «fila impresa con partida en el papel → IA1», pero la tabla plana no tiene ninguna columna que diga si la partida venía impresa —en residuos no viene y en hormigón sí—, y suponerlo sería inventar ground truth (R11). El precio es que la mitad de EXTRACCIÓN del patrón 1 (la partida se lee mal) queda sin vigilar; su mitad de DECISIÓN sí se compara, en `IA3.codigo_partida_final` y `FINAL.lineas.partida_final`. Se cierra con una columna nueva en el Excel o aceptando la ceguera.
- DESVIACIÓN de `design.md` §3, pendiente de que la cierre el humano: `INPUTS.CASOS.tipologia` lleva la PESTAÑA y no la familia de documento. `MAPA_TIPO_FAMILIA` de `evals/procesos/sv5_valoracion.py` y `sv6_build.py` está indexado por pestaña, así que escribir la familia dejaría TODOS los casos —incluidos los 7 RES que ya funcionaban— en `tipo_familia='otro'`. La familia de documento queda en `evals/mapa_casos.json` y agrupada más arriba en este informe.
