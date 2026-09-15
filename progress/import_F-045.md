<!-- progress/import_F-045.md -->
# F-045 · Importación de la revisión manual al banco de evals

Generado por `python -m evals.revision`. **No se edita a mano**: la
siguiente importación lo reescribe.

## Resumen

- Filas leídas de la tabla plana: **142**
- Casos (albaranes): **59**, de los que **0** son nuevos
- Libros escritos: (ninguno: en seco)
- Copias de seguridad: 0

## Cómo se reparten los casos

El comentario del Excel dice qué falla HOY, no qué se espera. Vacío
significa que el caso salió BIEN y hay que seguir comprobándolo.

- **no regresión** (deben salir VERDES): 11
- **defecto conocido** (rojo esperado hasta su ficha): 48

No regresión: COM-001, FER-001, FER-002, GEN-001, GEN-003, GEN-004, GEN-006, GEN-008, GEN-009, HOR-007, HOR-011

Defecto conocido: ALQ-001, FER-003, GEN-002, GEN-005, GEN-007, GEN-010, GRA-001, GRA-002, HOR-001, HOR-002, HOR-003, HOR-004, HOR-005, HOR-006, HOR-008, HOR-009, HOR-010, HOR-012, HOR-013, HOR-014, HOR-015, HOR-016, HOR-017, MOR-001, MOR-002, MOR-003, MOR-004, RES-001, RES-002, RES-003, RES-004, RES-005, RES-006, RES-007, RES-008, RES-009, RES-010, RES-011, RES-012, RES-013, RES-014, RES-015, RES-016, RES-017, RES-018, RES-019, RES-020, RES-021

## Documentos de entrada

Lo que la regla de nombres no cubre sale listado UNO A UNO: una
importación que se traga casos en silencio es peor que no importar.

### Plan de renombrado

(ningún fichero emparejado)

### Lo que se quedó fuera

- `fila_sin_fichero` — ALQ-001 (código '0009256'): el Excel lo trae pero no hay ningún documento suyo en la carpeta de entrada.
- `fila_sin_fichero` — COM-001 (código 'J1000505'): el Excel lo trae pero no hay ningún documento suyo en la carpeta de entrada.
- `fila_sin_fichero` — FER-001 (código '2139643'): el Excel lo trae pero no hay ningún documento suyo en la carpeta de entrada.
- `fila_sin_fichero` — FER-002 (código '2137569'): el Excel lo trae pero no hay ningún documento suyo en la carpeta de entrada.
- `fila_sin_fichero` — FER-003 (código '2115714'): el Excel lo trae pero no hay ningún documento suyo en la carpeta de entrada.
- `fila_sin_fichero` — GEN-001 (código 'A261584'): el Excel lo trae pero no hay ningún documento suyo en la carpeta de entrada.
- `fila_sin_fichero` — GEN-002 (código '202601007378'): el Excel lo trae pero no hay ningún documento suyo en la carpeta de entrada.
- `fila_sin_fichero` — GEN-003 (código '202601007181'): el Excel lo trae pero no hay ningún documento suyo en la carpeta de entrada.
- `fila_sin_fichero` — GEN-004 (código '2674163'): el Excel lo trae pero no hay ningún documento suyo en la carpeta de entrada.
- `fila_sin_fichero` — GEN-005 (código '2674143'): el Excel lo trae pero no hay ningún documento suyo en la carpeta de entrada.
- `fila_sin_fichero` — GEN-006 (código '2674074'): el Excel lo trae pero no hay ningún documento suyo en la carpeta de entrada.
- `fila_sin_fichero` — GEN-007 (código '2672497'): el Excel lo trae pero no hay ningún documento suyo en la carpeta de entrada.
- `fila_sin_fichero` — GEN-008 (código '2672297'): el Excel lo trae pero no hay ningún documento suyo en la carpeta de entrada.
- `fila_sin_fichero` — GEN-009 (código '170161'): el Excel lo trae pero no hay ningún documento suyo en la carpeta de entrada.
- `fila_sin_fichero` — GEN-010 (código '261046'): el Excel lo trae pero no hay ningún documento suyo en la carpeta de entrada.
- `fila_sin_fichero` — GRA-001 (código '58826'): el Excel lo trae pero no hay ningún documento suyo en la carpeta de entrada.
- `fila_sin_fichero` — GRA-002 (código '58878'): el Excel lo trae pero no hay ningún documento suyo en la carpeta de entrada.
- `fila_sin_fichero` — HOR-001 (código '225137'): el Excel lo trae pero no hay ningún documento suyo en la carpeta de entrada.
- `fila_sin_fichero` — HOR-002 (código '224964'): el Excel lo trae pero no hay ningún documento suyo en la carpeta de entrada.
- `fila_sin_fichero` — HOR-003 (código '0001167'): el Excel lo trae pero no hay ningún documento suyo en la carpeta de entrada.
- `fila_sin_fichero` — HOR-004 (código '0334191'): el Excel lo trae pero no hay ningún documento suyo en la carpeta de entrada.
- `fila_sin_fichero` — HOR-005 (código 'H132525'): el Excel lo trae pero no hay ningún documento suyo en la carpeta de entrada.
- `fila_sin_fichero` — HOR-006 (código 'H98634'): el Excel lo trae pero no hay ningún documento suyo en la carpeta de entrada.
- `fila_sin_fichero` — HOR-007 (código 'H122959'): el Excel lo trae pero no hay ningún documento suyo en la carpeta de entrada.
- `fila_sin_fichero` — HOR-008 (código 'W25963'): el Excel lo trae pero no hay ningún documento suyo en la carpeta de entrada.
- `fila_sin_fichero` — HOR-009 (código 'W26580'): el Excel lo trae pero no hay ningún documento suyo en la carpeta de entrada.
- `fila_sin_fichero` — HOR-010 (código 'W25237'): el Excel lo trae pero no hay ningún documento suyo en la carpeta de entrada.
- `fila_sin_fichero` — HOR-011 (código 'H99168'): el Excel lo trae pero no hay ningún documento suyo en la carpeta de entrada.
- `fila_sin_fichero` — HOR-012 (código '249917'): el Excel lo trae pero no hay ningún documento suyo en la carpeta de entrada.
- `fila_sin_fichero` — HOR-013 (código '249924'): el Excel lo trae pero no hay ningún documento suyo en la carpeta de entrada.
- `fila_sin_fichero` — HOR-014 (código '249927'): el Excel lo trae pero no hay ningún documento suyo en la carpeta de entrada.
- `fila_sin_fichero` — HOR-015 (código '37515'): el Excel lo trae pero no hay ningún documento suyo en la carpeta de entrada.
- `fila_sin_fichero` — HOR-016 (código '249997'): el Excel lo trae pero no hay ningún documento suyo en la carpeta de entrada.
- `fila_sin_fichero` — HOR-017 (código '250012'): el Excel lo trae pero no hay ningún documento suyo en la carpeta de entrada.
- `fila_sin_fichero` — MOR-001 (código '225225'): el Excel lo trae pero no hay ningún documento suyo en la carpeta de entrada.
- `fila_sin_fichero` — MOR-002 (código '0001229'): el Excel lo trae pero no hay ningún documento suyo en la carpeta de entrada.
- `fila_sin_fichero` — MOR-003 (código 'H132193'): el Excel lo trae pero no hay ningún documento suyo en la carpeta de entrada.
- `fila_sin_fichero` — MOR-004 (código '37816'): el Excel lo trae pero no hay ningún documento suyo en la carpeta de entrada.
- `fila_sin_fichero` — RES-008 (código '96187'): el Excel lo trae pero no hay ningún documento suyo en la carpeta de entrada.
- `fila_sin_fichero` — RES-009 (código '93478'): el Excel lo trae pero no hay ningún documento suyo en la carpeta de entrada.
- `fila_sin_fichero` — RES-010 (código '24346'): el Excel lo trae pero no hay ningún documento suyo en la carpeta de entrada.
- `fila_sin_fichero` — RES-011 (código '24385'): el Excel lo trae pero no hay ningún documento suyo en la carpeta de entrada.
- `fila_sin_fichero` — RES-012 (código '24566'): el Excel lo trae pero no hay ningún documento suyo en la carpeta de entrada.
- `fila_sin_fichero` — RES-013 (código '24571'): el Excel lo trae pero no hay ningún documento suyo en la carpeta de entrada.
- `fila_sin_fichero` — RES-014 (código '24788'): el Excel lo trae pero no hay ningún documento suyo en la carpeta de entrada.
- `fila_sin_fichero` — RES-015 (código '24790'): el Excel lo trae pero no hay ningún documento suyo en la carpeta de entrada.
- `fila_sin_fichero` — RES-016 (código '30440'): el Excel lo trae pero no hay ningún documento suyo en la carpeta de entrada.
- `fila_sin_fichero` — RES-017 (código '30490'): el Excel lo trae pero no hay ningún documento suyo en la carpeta de entrada.
- `fila_sin_fichero` — RES-018 (código '29990'): el Excel lo trae pero no hay ningún documento suyo en la carpeta de entrada.
- `fila_sin_fichero` — RES-019 (código '30366'): el Excel lo trae pero no hay ningún documento suyo en la carpeta de entrada.
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

- `incremento_por_ano`: RES-009, RES-010, RES-011, RES-014, RES-015, RES-018
- `minimo_1_tn`: RES-010, RES-011, RES-012, RES-013, RES-014, RES-015, RES-017, RES-018, RES-019

## Celdas escritas por libro y columna

`valor` = afirmado por el humano · `?` = no lo afirmó, no se compara ·
`vacía` = afirmó que no hay dato (se compara contra `null`).

| Libro | Tabla | Columna | valor | `?` | vacía |
|---|---|---|---:|---:|---:|
| IA1 | cabeceras | caso_id | 59 | 0 | 0 |
| IA1 | cabeceras | fichero_albaran | 7 | 0 | 52 |
| IA1 | cabeceras | proveedor_nombre | 59 | 0 | 0 |
| IA1 | cabeceras | proveedor_cif | 0 | 59 | 0 |
| IA1 | cabeceras | fecha | 59 | 0 | 0 |
| IA1 | cabeceras | numero_albaran | 0 | 59 | 0 |
| IA1 | cabeceras | obra_codigo | 0 | 59 | 0 |
| IA1 | cabeceras | obra_nombre | 0 | 59 | 0 |
| IA1 | cabeceras | forma_pago | 0 | 59 | 0 |
| IA1 | cabeceras | comentario | 48 | 0 | 11 |
| IA1 | lineas | caso_id | 114 | 0 | 0 |
| IA1 | lineas | num_linea | 114 | 0 | 0 |
| IA1 | lineas | descripcion_esperada | 114 | 0 | 0 |
| IA1 | lineas | cantidad | 114 | 0 | 0 |
| IA1 | lineas | unidad | 114 | 0 | 0 |
| IA1 | lineas | precio_unitario | 12 | 0 | 102 |
| IA1 | lineas | descuentos | 12 | 0 | 102 |
| IA1 | lineas | importe | 4 | 0 | 110 |
| IA1 | lineas | codigo_imputacion | 0 | 114 | 0 |
| IA1 | lineas | comentario | 68 | 0 | 46 |
| IA3 | lineas_valoradas | caso_id | 114 | 0 | 0 |
| IA3 | lineas_valoradas | num_linea | 114 | 0 | 0 |
| IA3 | lineas_valoradas | match_method | 27 | 87 | 0 |
| IA3 | lineas_valoradas | codigo_producto_contrato | 0 | 87 | 27 |
| IA3 | lineas_valoradas | codigo_partida_final | 114 | 0 | 0 |
| IA3 | lineas_valoradas | precio_unitario_final | 113 | 1 | 0 |
| IA3 | lineas_valoradas | precio_source | 114 | 0 | 0 |
| IA3 | lineas_valoradas | importe_calculado | 113 | 1 | 0 |
| IA3 | lineas_valoradas | review_required | 0 | 114 | 0 |
| IA3 | lineas_valoradas | comentario | 68 | 0 | 46 |
| IA3 | sinteticas_esperadas | caso_id | 28 | 0 | 0 |
| IA3 | sinteticas_esperadas | num_linea_base | 28 | 0 | 0 |
| IA3 | sinteticas_esperadas | modifier_source | 0 | 28 | 0 |
| IA3 | sinteticas_esperadas | rol_linea | 0 | 28 | 0 |
| IA3 | sinteticas_esperadas | descripcion_esperada | 28 | 0 | 0 |
| IA3 | sinteticas_esperadas | cantidad | 28 | 0 | 0 |
| IA3 | sinteticas_esperadas | precio_unitario | 28 | 0 | 0 |
| IA3 | sinteticas_esperadas | codigo_partida | 28 | 0 | 0 |
| IA3 | sinteticas_esperadas | comentario | 23 | 0 | 5 |
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
| INPUTS | lineas_albaran | caso_id | 114 | 0 | 0 |
| INPUTS | lineas_albaran | num_linea | 114 | 0 | 0 |
| INPUTS | lineas_albaran | descripcion | 114 | 0 | 0 |
| INPUTS | lineas_albaran | cantidad | 114 | 0 | 0 |
| INPUTS | lineas_albaran | unidad | 114 | 0 | 0 |
| INPUTS | lineas_albaran | precio_unitario | 12 | 0 | 102 |
| INPUTS | lineas_albaran | descuentos | 12 | 0 | 102 |
| INPUTS | lineas_albaran | importe | 4 | 0 | 110 |
| INPUTS | lineas_albaran | codigo_imputacion | 0 | 0 | 114 |
| INPUTS | lineas_albaran | observaciones_albaran | 0 | 0 | 114 |
| FINAL | datos_generales | caso_id | 59 | 0 | 0 |
| FINAL | datos_generales | fichero | 7 | 0 | 52 |
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
| FINAL | lineas | caso_id | 114 | 0 | 0 |
| FINAL | lineas | num_linea | 114 | 0 | 0 |
| FINAL | lineas | descripcion | 114 | 0 | 0 |
| FINAL | lineas | cantidad_final | 114 | 0 | 0 |
| FINAL | lineas | unidad_final | 114 | 0 | 0 |
| FINAL | lineas | casa_con_contrato | 114 | 0 | 0 |
| FINAL | lineas | linea_contrato | 0 | 84 | 30 |
| FINAL | lineas | partida_final | 114 | 0 | 0 |
| FINAL | lineas | precio_unitario_final | 113 | 1 | 0 |
| FINAL | lineas | precio_source | 114 | 0 | 0 |
| FINAL | lineas | importe_final | 113 | 1 | 0 |
| FINAL | lineas | linea_a_revision | 0 | 114 | 0 |
| FINAL | lineas | comentario | 68 | 0 | 46 |
| FINAL | lineas_anadidas | caso_id | 28 | 0 | 0 |
| FINAL | lineas_anadidas | num_linea_base | 28 | 0 | 0 |
| FINAL | lineas_anadidas | concepto | 28 | 0 | 0 |
| FINAL | lineas_anadidas | cantidad | 28 | 0 | 0 |
| FINAL | lineas_anadidas | precio_unitario | 28 | 0 | 0 |
| FINAL | lineas_anadidas | partida | 28 | 0 | 0 |
| FINAL | lineas_anadidas | importe | 28 | 0 | 0 |
| FINAL | lineas_anadidas | comentario | 23 | 0 | 5 |
| IA2 | contexto | caso_id | 13 | 0 | 0 |
| IA2 | contexto | num_linea | 13 | 0 | 0 |
| IA2 | contexto | campo_contexto | 13 | 0 | 0 |
| IA2 | contexto | valor_esperado | 13 | 0 | 0 |
| IA2 | contexto | comentario | 12 | 0 | 1 |

## Avisos

- `INPUTS.CONTRATO_LINEAS`, `INPUTS.CONDICIONES` e `IA3` TABLA 3 no se alimentan (design §3): sin líneas de contrato, los casos nuevos solo son evaluables con LLM y la corrida determinista sigue viviendo de los 7 casos RES.
- DESVIACIÓN de `design.md` §3, pendiente de que la cierre el humano: `INPUTS.CASOS.tipologia` lleva la PESTAÑA y no la familia de documento. `MAPA_TIPO_FAMILIA` de `evals/procesos/sv5_valoracion.py` y `sv6_build.py` está indexado por pestaña, así que escribir la familia dejaría TODOS los casos —incluidos los 7 RES que ya funcionaban— en `tipo_familia='otro'`. La familia de documento queda en `evals/mapa_casos.json` y agrupada más arriba en este informe.
