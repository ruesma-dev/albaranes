# Importación de contratos del banco de evals — F-084

<!-- seccion:lineas -->
## Líneas de contrato (`python -m evals.contratos lineas`)

- Fecha: 2026-10-23T10:44:00Z
- Resultado: libro escrito; copia previa en `INPUTS.xlsx.20261023-1243.xlsx`
- Contratos leídos: 18 · fallidos: 0
- Filas de CONTRATO_LINEAS: 3159 · fechas añadidas a CONDICIONES: 52

| Contrato | Líneas leídas | Casos | Motivo del fallo |
|---|---|---|---|
| CTSB23/0964 | 20 | RES-010, RES-011, RES-012, RES-013, RES-014, RES-015, RES-016, RES-017, RES-018, RES-019 | — |
| CTSB25/0708 | 2 | ALQ-001 | — |
| CTSB26/0428 | 5 | RES-020, RES-021 | — |
| CTSU23/0386 | 62 | HOR-005, HOR-006, HOR-007, HOR-008, HOR-009, HOR-010, HOR-011, MOR-003 | — |
| CTSU24/0452 | 69 | HOR-012, HOR-013, HOR-014, HOR-015, HOR-016, HOR-017, MOR-004 | — |
| CTSU24/0454 | 65 | FER-001, FER-002 | — |
| CTSU24/0475 | 8 | COM-001 | — |
| CTSU24/0476 | 429 | HOR-004 | — |
| CTSU24/0477 | 12 | RES-008, RES-009 | — |
| CTSU24/0491 | 75 | FER-003 | — |
| CTSU24/0518 | 100 | HOR-001, HOR-002, MOR-001 | — |
| CTSU25/0001 | 62 | HOR-003, MOR-002 | — |
| CTSU25/0085 | 43 | GRA-001, GRA-002 | — |
| CTSU25/0188 | 49 | GEN-009 | — |
| CTSU25/0317 | 96 | GEN-002, GEN-003 | — |
| CTSU26/0005 | 106 | GEN-004, GEN-005, GEN-006, GEN-007, GEN-008 | — |
| CTSU26/0006 | 15 | GEN-010 | — |
| CTSU26/0058 | 6 | GEN-001 | — |

Control del contrato vigente (R10): de las líneas IA3 con precio `contrato_db`,
cuántas tienen su precio esperado entre los de las líneas importadas. No
empareja: Sigrid da el precio de hoy y el albarán puede ser de ayer.

| Caso | Precios de contrato presentes | num_linea sin su precio |
|---|---|---|
| ALQ-001 | 2 de 2 | — |
| COM-001 | 0 de 0 | — |
| FER-001 | 0 de 0 | — |
| FER-002 | 0 de 0 | — |
| FER-003 | 0 de 0 | — |
| GEN-001 | 1 de 1 | — |
| GEN-002 | 5 de 5 | — |
| GEN-003 | 2 de 2 | — |
| GEN-004 | 1 de 1 | — |
| GEN-005 | 2 de 2 | — |
| GEN-006 | 1 de 1 | — |
| GEN-007 | 0 de 0 | — |
| GEN-008 | 1 de 1 | — |
| GEN-009 | 1 de 1 | — |
| GEN-010 | 1 de 1 | — |
| GRA-001 | 1 de 1 | — |
| GRA-002 | 1 de 1 | — |
| HOR-001 | 1 de 1 | — |
| HOR-002 | 1 de 1 | — |
| HOR-003 | 1 de 1 | — |
| HOR-004 | 5 de 5 | — |
| HOR-005 | 2 de 2 | — |
| HOR-006 | 1 de 1 | — |
| HOR-007 | 1 de 1 | — |
| HOR-008 | 1 de 1 | — |
| HOR-009 | 3 de 3 | — |
| HOR-010 | 2 de 2 | — |
| HOR-011 | 1 de 1 | — |
| HOR-012 | 2 de 2 | — |
| HOR-013 | 1 de 1 | — |
| HOR-014 | 1 de 1 | — |
| HOR-015 | 3 de 3 | — |
| HOR-016 | 1 de 1 | — |
| HOR-017 | 3 de 3 | — |
| MOR-001 | 0 de 1 | 1 |
| MOR-002 | 0 de 0 | — |
| MOR-003 | 0 de 0 | — |
| MOR-004 | 1 de 1 | — |
| RES-008 | 0 de 0 | — |
| RES-009 | 0 de 1 | 1 |
| RES-010 | 2 de 2 | — |
| RES-011 | 2 de 2 | — |
| RES-012 | 2 de 2 | — |
| RES-013 | 2 de 2 | — |
| RES-014 | 2 de 2 | — |
| RES-015 | 2 de 2 | — |
| RES-016 | 0 de 0 | — |
| RES-017 | 2 de 2 | — |
| RES-018 | 2 de 2 | — |
| RES-019 | 1 de 2 | 2 |
| RES-020 | 1 de 1 | — |
| RES-021 | 2 de 2 | — |

<!-- /seccion:lineas -->

<!-- seccion:documentos -->
## Documento del contrato (`python -m evals.contratos documentos`)

- Fecha: 2026-10-23T10:48:18Z
- Recuento: md 1 · pdf 6 · ninguno 13

| Contrato | Tipo | Bytes | Motivo |
|---|---|---|---|
| CTSB23/0964 | pdf | 737355 | — |
| CTSB25/0708 | ninguno | 0 | el contrato no está en albaran_contratos_merge |
| CTSB26/0428 | ninguno | 0 | el contrato no está en albaran_contratos_merge |
| CTSU23/0386 | ninguno | 0 | el contrato no está en albaran_contratos_merge |
| CTSU24/0228 | md | 47193 | — |
| CTSU24/0402 | ninguno | 0 | el contrato no está en albaran_contratos_merge |
| CTSU24/0452 | pdf | 755639 | — |
| CTSU24/0454 | pdf | 772563 | — |
| CTSU24/0475 | ninguno | 0 | el contrato no está en albaran_contratos_merge |
| CTSU24/0476 | pdf | 1139587 | — |
| CTSU24/0477 | ninguno | 0 | el contrato no está en albaran_contratos_merge |
| CTSU24/0491 | ninguno | 0 | el contrato no está en albaran_contratos_merge |
| CTSU24/0518 | ninguno | 0 | el contrato no está en albaran_contratos_merge |
| CTSU25/0001 | pdf | 558722 | — |
| CTSU25/0085 | pdf | 676282 | — |
| CTSU25/0188 | ninguno | 0 | el contrato no está en albaran_contratos_merge |
| CTSU25/0317 | ninguno | 0 | el contrato no está en albaran_contratos_merge |
| CTSU26/0005 | ninguno | 0 | el contrato no está en albaran_contratos_merge |
| CTSU26/0006 | ninguno | 0 | el contrato no está en albaran_contratos_merge |
| CTSU26/0058 | ninguno | 0 | el contrato no está en albaran_contratos_merge |

<!-- /seccion:documentos -->
