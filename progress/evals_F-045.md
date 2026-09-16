<!-- informe generado por evals/informe.py -->

# Evals de IA — F-045

- Fecha: 2026-09-16T20:45:45Z
- Commit HEAD: 6d1114f
- Feature: F-045
- Modo: pasada completa (con llamadas LLM reales)

Líneas parseables por la puerta del arnés:

```
MODO: completa
FASES: IA1
PROVEEDORES: gemini
```

## IA1 · extracción genérica (sv2) — ROJO

- Casos evaluados: 57 · omitidos: 2
- Proveedores invocados: gemini

| Caso | Estado | Fallos críticos | Avisos laxos | Motivo |
|---|---|---|---|---|
| RES-020 | OMITIDO | — | — | no existe el fichero del albarán de RES-020 |
| RES-021 | OMITIDO | — | — | no existe el fichero del albarán de RES-021 |
| ALQ-001/gemini | ROJO | 1 | 3 | — |
| COM-001/gemini | VERDE | 0 | 0 | — |
| FER-001/gemini | ROJO | 3 | 1 | — |
| FER-002/gemini | ROJO | 16 | 5 | — |
| FER-003/gemini | ROJO | 3 | 0 | — |
| GEN-001/gemini | ROJO | 1 | 1 | — |
| GEN-002/gemini | ROJO | 13 | 7 | — |
| GEN-003/gemini | ROJO | 5 | 2 | — |
| GEN-004/gemini | VERDE | 0 | 1 | — |
| GEN-005/gemini | VERDE | 0 | 2 | — |
| GEN-006/gemini | VERDE | 0 | 1 | — |
| GEN-007/gemini | VERDE | 0 | 1 | — |
| GEN-008/gemini | VERDE | 0 | 1 | — |
| GEN-009/gemini | ROJO | 1 | 1 | — |
| GEN-010/gemini | ROJO | 2 | 1 | — |
| GRA-001/gemini | ROJO | 3 | 1 | — |
| GRA-002/gemini | ROJO | 2 | 1 | — |
| HOR-001/gemini | VERDE | 0 | 1 | — |
| HOR-002/gemini | VERDE | 0 | 1 | — |
| HOR-003/gemini | ROJO | 1 | 1 | — |
| HOR-004/gemini | ROJO | 5 | 1 | — |
| HOR-005/gemini | ROJO | 4 | 0 | — |
| HOR-006/gemini | VERDE | 0 | 1 | — |
| HOR-007/gemini | ROJO | 1 | 0 | — |
| HOR-008/gemini | VERDE | 0 | 0 | — |
| HOR-009/gemini | ROJO | 2 | 0 | — |
| HOR-010/gemini | ROJO | 1 | 1 | — |
| HOR-011/gemini | VERDE | 0 | 0 | — |
| HOR-012/gemini | ROJO | 2 | 0 | — |
| HOR-013/gemini | ROJO | 1 | 1 | — |
| HOR-014/gemini | ROJO | 2 | 1 | — |
| HOR-015/gemini | ROJO | 3 | 0 | — |
| HOR-016/gemini | ROJO | 1 | 0 | — |
| HOR-017/gemini | ROJO | 4 | 0 | — |
| MOR-001/gemini | VERDE | 0 | 1 | — |
| MOR-002/gemini | ROJO | 2 | 1 | — |
| MOR-003/gemini | ROJO | 1 | 1 | — |
| MOR-004/gemini | ROJO | 2 | 1 | — |
| RES-001/gemini | ROJO | 1 | 1 | — |
| RES-002/gemini | ROJO | 1 | 1 | — |
| RES-003/gemini | ROJO | 4 | 1 | — |
| RES-004/gemini | ROJO | 2 | 1 | — |
| RES-005/gemini | ROJO | 2 | 1 | — |
| RES-006/gemini | ROJO | 1 | 1 | — |
| RES-007/gemini | ROJO | 2 | 1 | — |
| RES-008/gemini | ROJO | 1 | 1 | — |
| RES-009/gemini | ROJO | 1 | 1 | — |
| RES-010/gemini | ROJO | 3 | 1 | — |
| RES-011/gemini | ROJO | 3 | 1 | — |
| RES-012/gemini | ROJO | 3 | 1 | — |
| RES-013/gemini | ROJO | 4 | 1 | — |
| RES-014/gemini | ROJO | 3 | 1 | — |
| RES-015/gemini | ROJO | 3 | 1 | — |
| RES-016/gemini | ROJO | 2 | 1 | — |
| RES-017/gemini | ROJO | 3 | 1 | — |
| RES-018/gemini | ROJO | 3 | 1 | — |
| RES-019/gemini | ROJO | 4 | 1 | — |

Detalle campo a campo:

- ALQ-001/gemini · FALLO · IA1.cabeceras[].proveedor_nombre: esperado 'TRANSPORTES Y GRUAS ANGEL MARTIN, S.L.', obtenido 'TRANSPORTES Y GRUAS ANGEL MARTIN S.L.'
- ALQ-001/gemini · AVISO · IA1.lineas[1].descripcion_esperada: esperado 'SALIDA CAMIÓN GRÚA 100 TN', obtenido 'Desplazamiento'
- ALQ-001/gemini · AVISO · IA1.lineas[2].descripcion_esperada: esperado 'CAMIÓN GRÚA 100 TN', obtenido 'Horas normales'
- ALQ-001/gemini · AVISO · IA1.lineas[3].descripcion_esperada: esperado 'HHEE CAMIÓN GRÚA 100 TN', obtenido 'Horas extras'
- FER-001/gemini · FALLO · IA1.cabeceras[].fecha: esperado '2026-06-05', obtenido '2020-06-05'
- FER-001/gemini · FALLO · IA1.cabeceras[].proveedor_nombre: esperado 'FERRETERIA Y MAQUINARIA PARA LA CONSTRUCCION, S.A. (FEYMACO)', obtenido 'FEYMACO, S.A.'
- FER-001/gemini · AVISO · IA1.lineas[1].descripcion_esperada: esperado 'DISCO ESPECIAL ACERO INOX 115x1x22', obtenido 'DISCO ESPECIAL ACERO INOX. 115X1X22'
- FER-001/gemini · FALLO · IA1.lineas[1].importe: esperado None, obtenido 19.41
- FER-002/gemini · FALLO · IA1.cabeceras[].proveedor_nombre: esperado 'FERRETERIA Y MAQUINARIA PARA LA CONSTRUCCION, S.A. (FEYMACO)', obtenido 'FERRETERÍA Y MAQUINARIA PARA LA CONSTRUCCIÓN, S. A.'
- FER-002/gemini · FALLO · IA1.lineas[1].cantidad: esperado 54, obtenido 108.0
- FER-002/gemini · AVISO · IA1.lineas[1].descripcion_esperada: esperado 'papel higienico', obtenido 'PAPEL HIGIENICO (SACO 108)'
- FER-002/gemini · FALLO · IA1.lineas[1].importe: esperado None, obtenido 35.19
- FER-002/gemini · FALLO · IA1.lineas[2].cantidad: esperado 5, obtenido 10.0
- FER-002/gemini · AVISO · IA1.lineas[2].descripcion_esperada: esperado 'jabon liquido ph neutro', obtenido 'LTS. JABON LIQUIDO PH NEUTRO ****'
- FER-002/gemini · FALLO · IA1.lineas[2].importe: esperado None, obtenido 20.53
- FER-002/gemini · FALLO · IA1.lineas[3].cantidad: esperado 6, obtenido 12.0
- FER-002/gemini · AVISO · IA1.lineas[3].descripcion_esperada: esperado 'rollo papel ind.', obtenido 'ROLLO PAPEL IND. (P)****'
- FER-002/gemini · FALLO · IA1.lineas[3].importe: esperado None, obtenido 55.63
- FER-002/gemini · FALLO · IA1.lineas[4].cantidad: esperado 54, obtenido 4.0
- FER-002/gemini · AVISO · IA1.lineas[4].descripcion_esperada: esperado 'papel higienico', obtenido 'KGS ANIL ESPECIAL FEYMACO (OSYMA-MONTSERRAT)'
- FER-002/gemini · FALLO · IA1.lineas[4].importe: esperado None, obtenido 13.19
- FER-002/gemini · FALLO · IA1.lineas[4].precio_unitario: esperado 0.543, obtenido 5.497
- FER-002/gemini · FALLO · IA1.lineas[5].cantidad: esperado 5, obtenido 100.0
- FER-002/gemini · AVISO · IA1.lineas[5].descripcion_esperada: esperado 'jabon liquido ph neutro', obtenido 'BOLSA BASURA 52X58 (25 BOLSAS ROLLO)'
- FER-002/gemini · FALLO · IA1.lineas[5].importe: esperado None, obtenido 15.12
- FER-002/gemini · FALLO · IA1.lineas[5].precio_unitario: esperado 3.422, obtenido 0.252
- FER-002/gemini · FALLO · IA1.lineas[6]: esperado {'cantidad': 6, 'codigo_imputacion': '@@NO_COMPARAR@@', 'descripcion_esperada': 'rollo papel ind.', 'importe': None, 'num_linea': 6, 'precio_unitario': 7.726}, obtenido None (fila del ground truth que el sistema no ha producido)
- FER-002/gemini · FALLO · IA1.lineas[7]: esperado {'cantidad': 4, 'codigo_imputacion': '@@NO_COMPARAR@@', 'descripcion_esperada': 'AÑIL ESPECIAL FEYMACO', 'importe': None, 'num_linea': 7, 'precio_unitario': 5.497}, obtenido None (fila del ground truth que el sistema no ha producido)
- FER-002/gemini · FALLO · IA1.lineas[8]: esperado {'cantidad': 100, 'codigo_imputacion': '@@NO_COMPARAR@@', 'descripcion_esperada': 'BOLSA BASURA 52x58', 'importe': None, 'num_linea': 8, 'precio_unitario': 0.252}, obtenido None (fila del ground truth que el sistema no ha producido)
- FER-003/gemini · FALLO · IA1.cabeceras[].proveedor_nombre: esperado 'FERRETERIA Y MAQUINARIA PARA LA CONSTRUCCION, S.A. (FEYMACO)', obtenido 'FERRETERÍA Y MAQUINARIA PARA LA CONSTRUCCIÓN, S. A.'
- FER-003/gemini · FALLO · IA1.lineas[1].precio_unitario: esperado None, obtenido 95.481
- FER-003/gemini · FALLO · IA1.lineas[2]: esperado {'cantidad': -4, 'codigo_imputacion': '@@NO_COMPARAR@@', 'descripcion_esperada': 'DISCO DIAMANTE 100 MM. PULIDORA (11-380)', 'importe': None, 'num_linea': 2, 'precio_unitario': None}, obtenido None (fila del ground truth que el sistema no ha producido)
- GEN-001/gemini · FALLO · IA1.cabeceras[].proveedor_nombre: esperado 'VODALAND ESPAÑA, S.L', obtenido 'VODALAND ESPAÑA SL'
- GEN-001/gemini · AVISO · IA1.lineas[1].descripcion_esperada: esperado 'CANAL DE PLÁSTICO BASE DN100 H60', obtenido 'Canal de Plástico Base DN100 H60 modernizado'
- GEN-002/gemini · AVISO · IA1.lineas[1].descripcion_esperada: esperado 'SOLADO BOREAL WHITE 60X60 cm - COCINA (OP1)', obtenido '60X60 BOREAL WHITE'
- GEN-002/gemini · FALLO · IA1.lineas[1].importe: esperado None, obtenido 14.38
- GEN-002/gemini · FALLO · IA1.lineas[1].precio_unitario: esperado None, obtenido 14.38
- GEN-002/gemini · AVISO · IA1.lineas[2].descripcion_esperada: esperado 'SOLADO SAN FRANCISCO SAND 60X60 cm - COCINA (OP2)', obtenido '60X60 SAN FRANCISCO SAND'
- GEN-002/gemini · FALLO · IA1.lineas[2].importe: esperado None, obtenido 14.38
- GEN-002/gemini · FALLO · IA1.lineas[2].precio_unitario: esperado None, obtenido 14.38
- GEN-002/gemini · AVISO · IA1.lineas[3].descripcion_esperada: esperado 'SOLADO SAN FRANCISCO GREY 60X60 cm - COCINA (OP3)', obtenido '60X60 SAN FRANCISCO GREY'
- GEN-002/gemini · FALLO · IA1.lineas[3].importe: esperado None, obtenido 14.38
- GEN-002/gemini · FALLO · IA1.lineas[3].precio_unitario: esperado None, obtenido 14.38
- GEN-002/gemini · AVISO · IA1.lineas[4].descripcion_esperada: esperado 'SOLADO BOREAL GREY 60X60 cm - BAÑOS PRINCIPALES (OP2)', obtenido '60X60 BOREAL GREY'
- GEN-002/gemini · FALLO · IA1.lineas[4].importe: esperado None, obtenido 14.38
- GEN-002/gemini · FALLO · IA1.lineas[4].precio_unitario: esperado None, obtenido 14.38
- GEN-002/gemini · AVISO · IA1.lineas[5].descripcion_esperada: esperado 'SOLADO NATURE BONE RECTIFICADO 60x60 cm - BAÑOS SECUNDARIOS (OP2)', obtenido '60X60 NATURE BONE'
- GEN-002/gemini · FALLO · IA1.lineas[5].importe: esperado None, obtenido 14.38
- GEN-002/gemini · FALLO · IA1.lineas[5].precio_unitario: esperado None, obtenido 14.38
- GEN-002/gemini · AVISO · IA1.lineas[6].descripcion_esperada: esperado 'SOLADO RC ESSEN GREY 60x60', obtenido '60X60 RC ESSEN GREY'
- GEN-002/gemini · FALLO · IA1.lineas[6].importe: esperado 621.22, obtenido 14.38
- GEN-002/gemini · AVISO · IA1.lineas[7].descripcion_esperada: esperado 'ROMANCE ROBLE 24,8x150', obtenido '24,8X150 ROMANCE ROBLE'
- GEN-002/gemini · FALLO · IA1.lineas[7].importe: esperado 11234.36, obtenido 22.44
- GEN-002/gemini · FALLO · IA1.lineas[8].importe: esperado 180, obtenido 9.0
- GEN-003/gemini · FALLO · IA1.cabeceras[].proveedor_nombre: esperado 'PAVIMARSA, S.A.', obtenido 'PAVIMARSA'
- GEN-003/gemini · AVISO · IA1.lineas[1].descripcion_esperada: esperado 'SOLADO BOREAL GREY 60X60 cm - BAÑOS PRINCIPALES (OP2)', obtenido '60X60 BOREAL GREY'
- GEN-003/gemini · FALLO · IA1.lineas[1].importe: esperado None, obtenido 341.67
- GEN-003/gemini · FALLO · IA1.lineas[1].precio_unitario: esperado None, obtenido 14.38
- GEN-003/gemini · AVISO · IA1.lineas[2].descripcion_esperada: esperado 'RODAPIÉ BOREAL GREY C/BISELADO 14,8x60 cm - BAÑOS PRINCIPALES (OP2)', obtenido '14,8X60 RODAPIE BOREAL GREY BISELADO'
- GEN-003/gemini · FALLO · IA1.lineas[2].importe: esperado None, obtenido 179.4
- GEN-003/gemini · FALLO · IA1.lineas[2].precio_unitario: esperado None, obtenido 2.76
- GEN-004/gemini · AVISO · IA1.lineas[1].descripcion_esperada: esperado 'Inodoro Roca Gap Square Compact asiento', obtenido 'THE GAP COMPACT ASIENTO INODORO SUPRALIT BLANCO'
- GEN-005/gemini · AVISO · IA1.lineas[1].descripcion_esperada: esperado 'Inodoro Roca Gap Square Compact taza', obtenido 'THE GAP SQUARE COMPACT TAZA TANQUE BAJO 2/4L DUAL RIMLESS BL'
- GEN-005/gemini · AVISO · IA1.lineas[2].descripcion_esperada: esperado 'Reja vertedero', obtenido 'REJA ACERO INOXIDABLE VERTEDERO GARDA'
- GEN-006/gemini · AVISO · IA1.lineas[1].descripcion_esperada: esperado 'Vertedero Roca Garda', obtenido 'VERTEDERO GARDA BLANCO'
- GEN-007/gemini · AVISO · IA1.lineas[1].descripcion_esperada: esperado 'Kit Victoria', obtenido 'KIT G FIJACION VICTORIA TAZA-SUELO Y BIDES'
- GEN-008/gemini · AVISO · IA1.lineas[1].descripcion_esperada: esperado 'Reja vertedero', obtenido 'REJA ACERO INOXIDABLE VERTEDERO GARDA'
- GEN-009/gemini · FALLO · IA1.cabeceras[].proveedor_nombre: esperado 'DICONA, S.A.', obtenido 'DICONA, S.A'
- GEN-009/gemini · AVISO · IA1.lineas[1].descripcion_esperada: esperado 'Solado Somport Light 60x120', obtenido 'M2 P KS SOMPORT 60X120 LIGHT DUR1100'
- GEN-010/gemini · AVISO · IA1.lineas[1].descripcion_esperada: esperado 'TUBO DRENAJE 240º Ø160', obtenido 'TB DRENAJE D.160 D/P BARRA 6M 240º PE'
- GEN-010/gemini · FALLO · IA1.lineas[1].importe: esperado None, obtenido 174.96
- GEN-010/gemini · FALLO · IA1.lineas[1].precio_unitario: esperado None, obtenido 2.43
- GRA-001/gemini · FALLO · IA1.cabeceras[].fecha: esperado '2026-05-25', obtenido '2020-05-25'
- GRA-001/gemini · FALLO · IA1.cabeceras[].proveedor_nombre: esperado 'MATERIALES Y HORMIGONES, S.L. (MAHORSA)', obtenido 'MATERIALES Y HORMIGONES S.L.'
- GRA-001/gemini · FALLO · IA1.lineas[1].cantidad: esperado 30.38, obtenido 30380.0
- GRA-001/gemini · AVISO · IA1.lineas[1].descripcion_esperada: esperado 'GRAVA 20/40', obtenido 'ARIDO M-20/40-S EN 12620:2002H'
- GRA-002/gemini · FALLO · IA1.cabeceras[].proveedor_nombre: esperado 'MATERIALES Y HORMIGONES, S.L. (MAHORSA)', obtenido 'MATERIALES Y HORMIGONES S.L.'
- GRA-002/gemini · FALLO · IA1.lineas[1].cantidad: esperado 29.96, obtenido 29960.0
- GRA-002/gemini · AVISO · IA1.lineas[1].descripcion_esperada: esperado 'GRAVA 20/40', obtenido 'ARIDO M-20/40-S EN 12620:2002H'
- HOR-001/gemini · AVISO · IA1.lineas[1].descripcion_esperada: esperado 'HORMIGÓN HA-25/B/20/XC2', obtenido 'HA-25/B/20/XC2'
- HOR-002/gemini · AVISO · IA1.lineas[1].descripcion_esperada: esperado 'HORMIGÓN HA-25/B/20/XC2', obtenido 'HA-25/B/20/XC2'
- HOR-003/gemini · FALLO · IA1.cabeceras[].proveedor_nombre: esperado 'FABRICACION DE HORMIGONES PAZ DEL BARRIO,S.L.', obtenido 'HORMIGONES PAZ DEL BARRIO'
- HOR-003/gemini · AVISO · IA1.lineas[1].descripcion_esperada: esperado 'HORMIGÓN HA-25/B/20/XC2', obtenido 'HA-25/B/20/XC2'
- HOR-004/gemini · FALLO · IA1.cabeceras[].proveedor_nombre: esperado 'SUMINISTROS DE OBRAS MOSTOLES, S.L.', obtenido 'Suministros de Obras Móstoles, S.L.'
- HOR-004/gemini · AVISO · IA1.lineas[1].descripcion_esperada: esperado 'HORMIGON PREPARADOS EN CENTRAL HA-25.', obtenido 'HA-25/F/12/XC1'
- HOR-004/gemini · FALLO · IA1.lineas[2]: esperado {'cantidad': 10, 'codigo_imputacion': '@@NO_COMPARAR@@', 'descripcion_esperada': 'INCREMENTO POR SIN ADITIVO', 'importe': None, 'num_linea': 2, 'precio_unitario': None}, obtenido None (fila del ground truth que el sistema no ha producido)
- HOR-004/gemini · FALLO · IA1.lineas[3]: esperado {'cantidad': 10, 'codigo_imputacion': '@@NO_COMPARAR@@', 'descripcion_esperada': 'INCREMENTO POR ÁRIDO 12 EN HORMIGÓN', 'importe': None, 'num_linea': 3, 'precio_unitario': None}, obtenido None (fila del ground truth que el sistema no ha producido)
- HOR-004/gemini · FALLO · IA1.lineas[4]: esperado {'cantidad': 10, 'codigo_imputacion': '@@NO_COMPARAR@@', 'descripcion_esperada': 'INCREMENTO POR CONSISTENCIA FLUIDA EN HORMIGON', 'importe': None, 'num_linea': 4, 'precio_unitario': None}, obtenido None (fila del ground truth que el sistema no ha producido)
- HOR-004/gemini · FALLO · IA1.lineas[5]: esperado {'cantidad': 10, 'codigo_imputacion': '@@NO_COMPARAR@@', 'descripcion_esperada': 'INCREMENTO POR FIBRAS', 'importe': None, 'num_linea': 5, 'precio_unitario': None}, obtenido None (fila del ground truth que el sistema no ha producido)
- HOR-005/gemini · FALLO · IA1.lineas[2]: esperado {'cantidad': 4, 'codigo_imputacion': '@@NO_COMPARAR@@', 'descripcion_esperada': 'ADICIÓN FIBRAS POLIPROPILENO (600 GR/M3)', 'importe': None, 'num_linea': 2, 'precio_unitario': None}, obtenido None (fila del ground truth que el sistema no ha producido)
- HOR-005/gemini · FALLO · IA1.lineas[3]: esperado {'cantidad': 4, 'codigo_imputacion': '@@NO_COMPARAR@@', 'descripcion_esperada': 'INCREMENTO ARIDO 15', 'importe': None, 'num_linea': 3, 'precio_unitario': None}, obtenido None (fila del ground truth que el sistema no ha producido)
- HOR-005/gemini · FALLO · IA1.lineas[4]: esperado {'cantidad': 4, 'codigo_imputacion': '@@NO_COMPARAR@@', 'descripcion_esperada': 'INCREMENTO FRATASADO', 'importe': None, 'num_linea': 4, 'precio_unitario': None}, obtenido None (fila del ground truth que el sistema no ha producido)
- HOR-005/gemini · FALLO · IA1.lineas[5]: esperado {'cantidad': 2, 'codigo_imputacion': '@@NO_COMPARAR@@', 'descripcion_esperada': 'HA-25/B/20/XC2. CARGA INCOMPLETA', 'importe': None, 'num_linea': 5, 'precio_unitario': None}, obtenido None (fila del ground truth que el sistema no ha producido)
- HOR-006/gemini · AVISO · IA1.lineas[1].descripcion_esperada: esperado 'HA-25/B/20/XC2', obtenido 'HA-25/B/20/XC2/$'
- HOR-007/gemini · FALLO · IA1.lineas[2]: esperado {'cantidad': 1, 'codigo_imputacion': '@@NO_COMPARAR@@', 'descripcion_esperada': 'HA-25/B/20/XC2. CARGA INCOMPLETA', 'importe': None, 'num_linea': 2, 'precio_unitario': None}, obtenido None (fila del ground truth que el sistema no ha producido)
- HOR-009/gemini · FALLO · IA1.lineas[2]: esperado {'cantidad': 8, 'codigo_imputacion': '@@NO_COMPARAR@@', 'descripcion_esperada': 'ADICIÓN FIBRAS POLIPROPILENO (600 GR/M3)', 'importe': None, 'num_linea': 2, 'precio_unitario': None}, obtenido None (fila del ground truth que el sistema no ha producido)
- HOR-009/gemini · FALLO · IA1.lineas[3]: esperado {'cantidad': 8, 'codigo_imputacion': '@@NO_COMPARAR@@', 'descripcion_esperada': 'INCREM. CONSISTENCIA FLUIDA', 'importe': None, 'num_linea': 3, 'precio_unitario': None}, obtenido None (fila del ground truth que el sistema no ha producido)
- HOR-010/gemini · AVISO · IA1.lineas[1].descripcion_esperada: esperado 'HA-25/F/20/XC2', obtenido 'HA-25/F/20/XC2 EQUIVALENTE A HA-25/B/20/I ó IIa'
- HOR-010/gemini · FALLO · IA1.lineas[2]: esperado {'cantidad': 8, 'codigo_imputacion': '@@NO_COMPARAR@@', 'descripcion_esperada': 'INCREM. CONSISTENCIA FLUIDA', 'importe': None, 'num_linea': 2, 'precio_unitario': None}, obtenido None (fila del ground truth que el sistema no ha producido)
- HOR-012/gemini · FALLO · IA1.cabeceras[].proveedor_nombre: esperado 'HORMIGONES Y CEMENTOS ANDALUCES, S.L.', obtenido 'HORMIGONES Y CEMENTOS ANDALUCES'
- HOR-012/gemini · FALLO · IA1.lineas[2]: esperado {'cantidad': 9, 'codigo_imputacion': '@@NO_COMPARAR@@', 'descripcion_esperada': 'INCREM. CONSISTENCIA FLUIDA', 'importe': None, 'num_linea': 2, 'precio_unitario': None}, obtenido None (fila del ground truth que el sistema no ha producido)
- HOR-013/gemini · FALLO · IA1.cabeceras[].proveedor_nombre: esperado 'HORMIGONES Y CEMENTOS ANDALUCES, S.L.', obtenido 'HORMIGONES Y CEMENTOS ANDALUCES ALGARROBO'
- HOR-013/gemini · AVISO · IA1.lineas[1].descripcion_esperada: esperado 'HA-25/B/22/XC2', obtenido 'HORMIGÓN HA-25/B/22/XC2'
- HOR-014/gemini · FALLO · IA1.cabeceras[].proveedor_nombre: esperado 'HORMIGONES Y CEMENTOS ANDALUCES, S.L.', obtenido 'HORMIGONES Y CEMENTOS ANDALUCES ALGARROBO'
- HOR-014/gemini · AVISO · IA1.lineas[1].descripcion_esperada: esperado 'HA-25/B/22/XC2', obtenido 'HORMIGÓN HA-25/B/22/XC2'
- HOR-014/gemini · FALLO · IA1.lineas[2]: esperado {'cantidad': 1, 'codigo_imputacion': '@@NO_COMPARAR@@', 'descripcion_esperada': 'CARGA INCOMPLETA. NO PROCEDE. FINAL DE BOMBEO', 'importe': None, 'num_linea': 2, 'precio_unitario': None}, obtenido None (fila del ground truth que el sistema no ha producido)
- HOR-015/gemini · FALLO · IA1.cabeceras[].proveedor_nombre: esperado 'HORMIGONES Y CEMENTOS ANDALUCES, S.L.', obtenido 'HORMIGONES Y CEMENTOS ANDALUCES'
- HOR-015/gemini · FALLO · IA1.lineas[2]: esperado {'cantidad': 7, 'codigo_imputacion': '@@NO_COMPARAR@@', 'descripcion_esperada': 'INCREM. ARIDO 12', 'importe': None, 'num_linea': 2, 'precio_unitario': None}, obtenido None (fila del ground truth que el sistema no ha producido)
- HOR-015/gemini · FALLO · IA1.lineas[3]: esperado {'cantidad': 7, 'codigo_imputacion': '@@NO_COMPARAR@@', 'descripcion_esperada': 'INCREM. CONSISTENCIA FLUIDA', 'importe': None, 'num_linea': 3, 'precio_unitario': None}, obtenido None (fila del ground truth que el sistema no ha producido)
- HOR-016/gemini · FALLO · IA1.cabeceras[].proveedor_nombre: esperado 'HORMIGONES Y CEMENTOS ANDALUCES, S.L.', obtenido 'HORMIGONES Y CEMENTOS ANDALUCES'
- HOR-017/gemini · FALLO · IA1.cabeceras[].proveedor_nombre: esperado 'HORMIGONES Y CEMENTOS ANDALUCES, S.L.', obtenido 'HORMIGONES Y CEMENTOS ANDALUCES'
- HOR-017/gemini · FALLO · IA1.lineas[2]: esperado {'cantidad': 3, 'codigo_imputacion': '@@NO_COMPARAR@@', 'descripcion_esperada': 'INCREM. ARIDO 12', 'importe': None, 'num_linea': 2, 'precio_unitario': None}, obtenido None (fila del ground truth que el sistema no ha producido)
- HOR-017/gemini · FALLO · IA1.lineas[3]: esperado {'cantidad': 3, 'codigo_imputacion': '@@NO_COMPARAR@@', 'descripcion_esperada': 'INCREM. CONSISTENCIA FLUIDA', 'importe': None, 'num_linea': 3, 'precio_unitario': None}, obtenido None (fila del ground truth que el sistema no ha producido)
- HOR-017/gemini · FALLO · IA1.lineas[4]: esperado {'cantidad': 3, 'codigo_imputacion': '@@NO_COMPARAR@@', 'descripcion_esperada': 'CARGA INCOMPLETA', 'importe': None, 'num_linea': 4, 'precio_unitario': None}, obtenido None (fila del ground truth que el sistema no ha producido)
- MOR-001/gemini · AVISO · IA1.lineas[1].descripcion_esperada: esperado 'MORTERO PREP. M-7,5', obtenido 'M-7,5/B/4'
- MOR-002/gemini · FALLO · IA1.cabeceras[].proveedor_nombre: esperado 'FABRICACION DE HORMIGONES PAZ DEL BARRIO,S.L.', obtenido 'HORMIGONES PAZ DEL BARRIO'
- MOR-002/gemini · AVISO · IA1.lineas[1].descripcion_esperada: esperado 'MORTERO 7,5 - 48H', obtenido 'M-7,5/B/04 48H BLANDA'
- MOR-002/gemini · FALLO · IA1.lineas[2]: esperado {'cantidad': 3, 'codigo_imputacion': '@@NO_COMPARAR@@', 'descripcion_esperada': 'CARGAS INCOMPLETAS', 'importe': None, 'num_linea': 2, 'precio_unitario': None}, obtenido None (fila del ground truth que el sistema no ha producido)
- MOR-003/gemini · AVISO · IA1.lineas[1].descripcion_esperada: esperado 'MD-200 (M-5) / 48 H.', obtenido 'MD-200/2/36H'
- MOR-003/gemini · FALLO · IA1.lineas[2]: esperado {'cantidad': 2, 'codigo_imputacion': '@@NO_COMPARAR@@', 'descripcion_esperada': 'MD-200 (M-5) / 48 H. CARGA INCOMPLETA', 'importe': None, 'num_linea': 2, 'precio_unitario': None}, obtenido None (fila del ground truth que el sistema no ha producido)
- MOR-004/gemini · FALLO · IA1.cabeceras[].proveedor_nombre: esperado 'HORMIGONES Y CEMENTOS ANDALUCES, S.L.', obtenido 'HORMIGONES Y CEMENTOS ANDALUCES'
- MOR-004/gemini · AVISO · IA1.lineas[1].descripcion_esperada: esperado 'D-300/B/5/I', obtenido 'D-300/B/5/1 AUTONIVELANTE'
- MOR-004/gemini · FALLO · IA1.lineas[2]: esperado {'cantidad': 9, 'codigo_imputacion': '@@NO_COMPARAR@@', 'descripcion_esperada': 'INCREM. FIBRAS POLIPROPILENO', 'importe': None, 'num_linea': 2, 'precio_unitario': None}, obtenido None (fila del ground truth que el sistema no ha producido)
- RES-001/gemini · FALLO · IA1.lineas[1].cantidad: esperado 1, obtenido 6.0
- RES-001/gemini · AVISO · IA1.lineas[1].descripcion_esperada: esperado 'CAMBIO CONTENEDOR 6M3', obtenido 'Madera'
- RES-002/gemini · FALLO · IA1.lineas[1].cantidad: esperado 1, obtenido 8120.0
- RES-002/gemini · AVISO · IA1.lineas[1].descripcion_esperada: esperado 'CAMBIO CONTENEDOR 6M3', obtenido 'Horm_Ladr_Cerám.'
- RES-003/gemini · FALLO · IA1.cabeceras[].numero_albaran: esperado 'SS-0000589', obtenido 'SS-0080589'
- RES-003/gemini · FALLO · IA1.cabeceras[].proveedor_nombre: esperado 'SALMEDINA TRATAMIENTO DE RESIDUOS INERTES, S.L.', obtenido 'SALMEDINA TRI, S.L.'
- RES-003/gemini · FALLO · IA1.lineas[1].cantidad: esperado 1, obtenido 6.0
- RES-003/gemini · AVISO · IA1.lineas[1].descripcion_esperada: esperado 'CAMBIO CONTENEDOR 6M3', obtenido 'Mat. Yeso (LER 170802)'
- RES-003/gemini · FALLO · IA1.lineas[2]: esperado {'cantidad': 1, 'codigo_imputacion': '@@NO_COMPARAR@@', 'descripcion_esperada': 'INCREMENTO LER 170802 MAT. DE CONST. A PARTIR DE YESOS-E', 'importe': None, 'num_linea': 2, 'precio_unitario': None}, obtenido None (fila del ground truth que el sistema no ha producido)
- RES-004/gemini · FALLO · IA1.lineas[1].cantidad: esperado 1, obtenido 6.0
- RES-004/gemini · AVISO · IA1.lineas[1].descripcion_esperada: esperado 'CAMBIO CONTENEDOR 6M3', obtenido 'Mat. Aislamiento'
- RES-004/gemini · FALLO · IA1.lineas[2]: esperado {'cantidad': 1, 'codigo_imputacion': '@@NO_COMPARAR@@', 'descripcion_esperada': 'INCREMENTO LER 170604 MATERIALES DE AISLAMIENTO-E', 'importe': None, 'num_linea': 2, 'precio_unitario': None}, obtenido None (fila del ground truth que el sistema no ha producido)
- RES-005/gemini · FALLO · IA1.lineas[1].cantidad: esperado 1, obtenido 6.0
- RES-005/gemini · AVISO · IA1.lineas[1].descripcion_esperada: esperado 'CAMBIO CONTENEDOR 6M3', obtenido 'Mat. Aislamiento'
- RES-005/gemini · FALLO · IA1.lineas[2]: esperado {'cantidad': 1, 'codigo_imputacion': '@@NO_COMPARAR@@', 'descripcion_esperada': 'INCREMENTO LER 170604 MATERIALES DE AISLAMIENTO-E', 'importe': None, 'num_linea': 2, 'precio_unitario': None}, obtenido None (fila del ground truth que el sistema no ha producido)
- RES-006/gemini · FALLO · IA1.lineas[1].cantidad: esperado 1, obtenido 6.0
- RES-006/gemini · AVISO · IA1.lineas[1].descripcion_esperada: esperado 'CONTENEDOR DE RESIDUOS 6 M3', obtenido 'Mat. Mezclados'
- RES-007/gemini · FALLO · IA1.lineas[1].cantidad: esperado 1, obtenido 9.0
- RES-007/gemini · AVISO · IA1.lineas[1].descripcion_esperada: esperado 'CONTENEDOR DE RESIDUOS 9 M3', obtenido 'Mat. Yeso'
- RES-007/gemini · FALLO · IA1.lineas[2]: esperado {'cantidad': 1, 'codigo_imputacion': '@@NO_COMPARAR@@', 'descripcion_esperada': 'INCREMENTO LEER 17 08 02', 'importe': None, 'num_linea': 2, 'precio_unitario': None}, obtenido None (fila del ground truth que el sistema no ha producido)
- RES-008/gemini · FALLO · IA1.lineas[1].cantidad: esperado 1, obtenido 6.0
- RES-008/gemini · AVISO · IA1.lineas[1].descripcion_esperada: esperado 'MOVIMIENTO DE CONTENEDOR DE 6 M CÚBICOS PLASTICO', obtenido 'PLASTICO'
- RES-009/gemini · FALLO · IA1.lineas[1].cantidad: esperado 1, obtenido 6.0
- RES-009/gemini · AVISO · IA1.lineas[1].descripcion_esperada: esperado 'MOVIMIENTO DE CONTENEDOR DE 6 M CÚBICOS MEZCLA OTROS RESIDUOS', obtenido 'Residuos mezclados de construcción y demolición que no contienen sustancias peligrosas.'
- RES-010/gemini · FALLO · IA1.cabeceras[].proveedor_nombre: esperado 'CARGA Y TRANSPORTE DE CUBAS, S.L.', obtenido 'CARGA Y TRANSPORTE DE CUBAS SL'
- RES-010/gemini · FALLO · IA1.lineas[1].cantidad: esperado 1, obtenido 8.0
- RES-010/gemini · AVISO · IA1.lineas[1].descripcion_esperada: esperado 'CONTENEDOR DE 8M3', obtenido 'MEZCLADO (LER 170904) - Cuba 1941'
- RES-010/gemini · FALLO · IA1.lineas[2]: esperado {'cantidad': 3, 'codigo_imputacion': '@@NO_COMPARAR@@', 'descripcion_esperada': 'RCDS. SUCIOS', 'importe': None, 'num_linea': 2, 'precio_unitario': None}, obtenido None (fila del ground truth que el sistema no ha producido)
- RES-011/gemini · FALLO · IA1.cabeceras[].proveedor_nombre: esperado 'CARGA Y TRANSPORTE DE CUBAS, S.L.', obtenido 'CARGA Y TRANSPORTE DE CUBAS SL'
- RES-011/gemini · FALLO · IA1.lineas[1].cantidad: esperado 1, obtenido 3280.0
- RES-011/gemini · AVISO · IA1.lineas[1].descripcion_esperada: esperado 'CONTENEDOR DE 8M3', obtenido 'Traslado de residuos Mezcla RCD / Hormigón (Cuba 1950 - 8 m3)'
- RES-011/gemini · FALLO · IA1.lineas[2]: esperado {'cantidad': 3.28, 'codigo_imputacion': '@@NO_COMPARAR@@', 'descripcion_esperada': 'RCDS. SUCIOS', 'importe': None, 'num_linea': 2, 'precio_unitario': None}, obtenido None (fila del ground truth que el sistema no ha producido)
- RES-012/gemini · FALLO · IA1.cabeceras[].proveedor_nombre: esperado 'CARGA Y TRANSPORTE DE CUBAS, S.L.', obtenido 'CARGA Y TRANSPORTE DE CUBAS SL'
- RES-012/gemini · FALLO · IA1.lineas[1].cantidad: esperado 1, obtenido 2380.0
- RES-012/gemini · AVISO · IA1.lineas[1].descripcion_esperada: esperado 'CONTENEDOR DE 8M3', obtenido 'RESIDUOS VOLUMINOSOS LER 200107 - CUBA 1935 (8 M3)'
- RES-012/gemini · FALLO · IA1.lineas[2]: esperado {'cantidad': 2.38, 'codigo_imputacion': '@@NO_COMPARAR@@', 'descripcion_esperada': 'RCDS. VOLUMINOSOS', 'importe': None, 'num_linea': 2, 'precio_unitario': None}, obtenido None (fila del ground truth que el sistema no ha producido)
- RES-013/gemini · FALLO · IA1.cabeceras[].fecha: esperado '2025-01-29', obtenido '2023-06-29'
- RES-013/gemini · FALLO · IA1.cabeceras[].proveedor_nombre: esperado 'CARGA Y TRANSPORTE DE CUBAS, S.L.', obtenido 'CARGA Y TRANSPORTE DE CUBAS SL'
- RES-013/gemini · FALLO · IA1.lineas[1].cantidad: esperado 1, obtenido 1720.0
- RES-013/gemini · AVISO · IA1.lineas[1].descripcion_esperada: esperado 'CONTENEDOR DE 8M3', obtenido 'VOLUMINOSOS - CUBA 1441'
- RES-013/gemini · FALLO · IA1.lineas[2]: esperado {'cantidad': 1.72, 'codigo_imputacion': '@@NO_COMPARAR@@', 'descripcion_esperada': 'RCDS. VOLUMINOSOS', 'importe': None, 'num_linea': 2, 'precio_unitario': None}, obtenido None (fila del ground truth que el sistema no ha producido)
- RES-014/gemini · FALLO · IA1.cabeceras[].proveedor_nombre: esperado 'CARGA Y TRANSPORTE DE CUBAS, S.L.', obtenido 'CARGA Y TRANSPORTE DE CUBAS SL'
- RES-014/gemini · FALLO · IA1.lineas[1].cantidad: esperado 1, obtenido 6100.0
- RES-014/gemini · AVISO · IA1.lineas[1].descripcion_esperada: esperado 'CONTENEDOR DE 8M3', obtenido 'MEZCLADO'
- RES-014/gemini · FALLO · IA1.lineas[2]: esperado {'cantidad': 6.1, 'codigo_imputacion': '@@NO_COMPARAR@@', 'descripcion_esperada': 'RCDS. SUCIOS', 'importe': None, 'num_linea': 2, 'precio_unitario': None}, obtenido None (fila del ground truth que el sistema no ha producido)
- RES-015/gemini · FALLO · IA1.cabeceras[].proveedor_nombre: esperado 'CARGA Y TRANSPORTE DE CUBAS, S.L.', obtenido 'CARGA Y TRANSPORTE DE CUBAS SL'
- RES-015/gemini · FALLO · IA1.lineas[1].cantidad: esperado 1, obtenido 8.0
- RES-015/gemini · AVISO · IA1.lineas[1].descripcion_esperada: esperado 'CONTENEDOR DE 8M3', obtenido 'MEZCLADO - CUBA 1954'
- RES-015/gemini · FALLO · IA1.lineas[2]: esperado {'cantidad': 4, 'codigo_imputacion': '@@NO_COMPARAR@@', 'descripcion_esperada': 'RCDS. SUCIOS', 'importe': None, 'num_linea': 2, 'precio_unitario': None}, obtenido None (fila del ground truth que el sistema no ha producido)
- RES-016/gemini · FALLO · IA1.cabeceras[].proveedor_nombre: esperado 'CARGA Y TRANSPORTE DE CUBAS, S.L.', obtenido 'CARGA Y TRANSPORTE DE CUBAS SL'
- RES-016/gemini · FALLO · IA1.lineas[1].cantidad: esperado 1, obtenido 8.0
- RES-016/gemini · AVISO · IA1.lineas[1].descripcion_esperada: esperado 'CONTENEDOR DE 8M3. LLEVAR. NO SE FACTURA', obtenido 'Escombro limpio (Cuba 1970)'
- RES-017/gemini · FALLO · IA1.cabeceras[].proveedor_nombre: esperado 'CARGA Y TRANSPORTE DE CUBAS, S.L.', obtenido 'CARGA Y TRANSPORTE DE CUBAS SL'
- RES-017/gemini · FALLO · IA1.lineas[1].cantidad: esperado 1, obtenido 7160.0
- RES-017/gemini · AVISO · IA1.lineas[1].descripcion_esperada: esperado 'CONTENEDOR DE 8M3', obtenido 'RES. BIDA PONSIRAD - COD LER 170904 - CUBA 1940'
- RES-017/gemini · FALLO · IA1.lineas[2]: esperado {'cantidad': 2.16, 'codigo_imputacion': '@@NO_COMPARAR@@', 'descripcion_esperada': 'RCDS. VOLUMINOSOS', 'importe': None, 'num_linea': 2, 'precio_unitario': None}, obtenido None (fila del ground truth que el sistema no ha producido)
- RES-018/gemini · FALLO · IA1.cabeceras[].proveedor_nombre: esperado 'CARGA Y TRANSPORTE DE CUBAS, S.L.', obtenido 'CARGA Y TRANSPORTE DE CUBAS SL'
- RES-018/gemini · FALLO · IA1.lineas[1].cantidad: esperado 1, obtenido 5400.0
- RES-018/gemini · AVISO · IA1.lineas[1].descripcion_esperada: esperado 'CONTENEDOR DE 8M3', obtenido 'SUCIO (Cod LER 170904 - Cuba 1952 - 6 m3)'
- RES-018/gemini · FALLO · IA1.lineas[2]: esperado {'cantidad': 5.4, 'codigo_imputacion': '@@NO_COMPARAR@@', 'descripcion_esperada': 'RCDS. SUCIOS', 'importe': None, 'num_linea': 2, 'precio_unitario': None}, obtenido None (fila del ground truth que el sistema no ha producido)
- RES-019/gemini · FALLO · IA1.cabeceras[].fecha: esperado '2025-07-28', obtenido '2023-08-07'
- RES-019/gemini · FALLO · IA1.cabeceras[].proveedor_nombre: esperado 'CARGA Y TRANSPORTE DE CUBAS, S.L.', obtenido 'CARGA Y TRANSPORTE DE CUBAS SL'
- RES-019/gemini · FALLO · IA1.lineas[1].cantidad: esperado 1, obtenido 8.0
- RES-019/gemini · AVISO · IA1.lineas[1].descripcion_esperada: esperado 'CONTENEDOR DE 8M3', obtenido 'MADERA'
- RES-019/gemini · FALLO · IA1.lineas[2]: esperado {'cantidad': 1, 'codigo_imputacion': '@@NO_COMPARAR@@', 'descripcion_esperada': 'RCDS. MADERA LIMPIA', 'importe': None, 'num_linea': 2, 'precio_unitario': None}, obtenido None (fila del ground truth que el sistema no ha producido)

## Campos no observables en esta corrida

El ground truth los declara, pero esta corrida NO puede verlos: el proceso evaluado no los devuelve. NO se comparan y NO cuentan como fallo (R26). Son deuda declarada, no un rojo: se cierran el día que el proceso empiece a producirlos, y entonces entran solos en OBSERVABLES.

- `cantidad_final`
- `caso_id`
- `cif`
- `comentario`
- `concepto`
- `descripcion`
- `descripcion_esperada`
- `descuentos`
- `fecha`
- `fichero`
- `fichero_albaran`
- `motivo_revision`
- `numero_albaran`
- `obra`
- `proveedor`
- `unidad`
- `unidad_final`

## Veredicto

Hay fallos críticos en: IA1.

VEREDICTO: ROJO
