<!-- informe generado por evals/informe.py -->

# Evals de IA — F-045

- Fecha: 2026-09-16T14:10:52Z
- Commit HEAD: 8a682b3
- Feature: F-045
- Modo: pasada completa (con llamadas LLM reales)

Líneas parseables por la puerta del arnés:

```
MODO: completa
FASES: IA1,IA2,IA3,IA4,E2E
PROVEEDORES: gemini,openai
```

## IA1 · extracción genérica (sv2) — ROJO

- Casos evaluados: 57 · omitidos: 2
- Proveedores invocados: gemini

| Caso | Estado | Fallos críticos | Avisos laxos | Motivo |
|---|---|---|---|---|
| RES-020 | OMITIDO | — | — | no existe el fichero del albarán de RES-020 |
| RES-021 | OMITIDO | — | — | no existe el fichero del albarán de RES-021 |
| ALQ-001/gemini | ROJO | 9 | 5 | — |
| COM-001/gemini | ROJO | 4 | 0 | — |
| FER-001/gemini | ROJO | 8 | 1 | — |
| FER-002/gemini | ROJO | 33 | 5 | — |
| FER-003/gemini | ROJO | 8 | 2 | — |
| GEN-001/gemini | ROJO | 5 | 1 | — |
| GEN-002/gemini | ROJO | 33 | 9 | — |
| GEN-003/gemini | ROJO | 10 | 2 | — |
| GEN-004/gemini | ROJO | 4 | 1 | — |
| GEN-005/gemini | ROJO | 6 | 4 | — |
| GEN-006/gemini | ROJO | 4 | 1 | — |
| GEN-007/gemini | ROJO | 4 | 3 | — |
| GEN-008/gemini | ROJO | 4 | 1 | — |
| GEN-009/gemini | ROJO | 6 | 1 | — |
| GEN-010/gemini | ROJO | 5 | 3 | — |
| GRA-001/gemini | ROJO | 6 | 3 | — |
| GRA-002/gemini | ROJO | 6 | 3 | — |
| HOR-001/gemini | ROJO | 4 | 3 | — |
| HOR-002/gemini | ROJO | 4 | 3 | — |
| HOR-003/gemini | ROJO | 5 | 3 | — |
| HOR-004/gemini | ROJO | 8 | 2 | — |
| HOR-005/gemini | ROJO | 8 | 2 | — |
| HOR-006/gemini | ROJO | 4 | 3 | — |
| HOR-007/gemini | ROJO | 5 | 0 | — |
| HOR-008/gemini | ROJO | 4 | 2 | — |
| HOR-009/gemini | ROJO | 6 | 2 | — |
| HOR-010/gemini | ROJO | 5 | 2 | — |
| HOR-011/gemini | ROJO | 4 | 0 | — |
| HOR-012/gemini | ROJO | 6 | 2 | — |
| HOR-013/gemini | ROJO | 5 | 3 | — |
| HOR-014/gemini | ROJO | 6 | 2 | — |
| HOR-015/gemini | ROJO | 7 | 3 | — |
| HOR-016/gemini | ROJO | 5 | 2 | — |
| HOR-017/gemini | ROJO | 8 | 2 | — |
| MOR-001/gemini | ROJO | 4 | 3 | — |
| MOR-002/gemini | ROJO | 6 | 3 | — |
| MOR-003/gemini | ROJO | 5 | 3 | — |
| MOR-004/gemini | ROJO | 5 | 3 | — |
| RES-001/gemini | ROJO | 5 | 3 | — |
| RES-002/gemini | ROJO | 5 | 3 | — |
| RES-003/gemini | ROJO | 7 | 3 | — |
| RES-004/gemini | ROJO | 6 | 3 | — |
| RES-005/gemini | ROJO | 6 | 3 | — |
| RES-006/gemini | ROJO | 5 | 3 | — |
| RES-007/gemini | ROJO | 6 | 3 | — |
| RES-008/gemini | ROJO | 6 | 3 | — |
| RES-009/gemini | ROJO | 6 | 3 | — |
| RES-010/gemini | ROJO | 7 | 2 | — |
| RES-011/gemini | ROJO | 7 | 2 | — |
| RES-012/gemini | ROJO | 7 | 2 | — |
| RES-013/gemini | ROJO | 7 | 2 | — |
| RES-014/gemini | ROJO | 7 | 2 | — |
| RES-015/gemini | ROJO | 7 | 2 | — |
| RES-016/gemini | ROJO | 6 | 3 | — |
| RES-017/gemini | ROJO | 7 | 2 | — |
| RES-018/gemini | ROJO | 7 | 2 | — |
| RES-019/gemini | ROJO | 8 | 2 | — |

Detalle campo a campo:

- ALQ-001/gemini · FALLO · IA1.cabeceras[].caso_id: esperado 'ALQ-001', obtenido None
- ALQ-001/gemini · AVISO · IA1.cabeceras[].comentario: esperado 'ha cogido una obra que no es (vieja), pero es que no hay obra indicada con codigo en el albaran', obtenido None
- ALQ-001/gemini · FALLO · IA1.cabeceras[].fichero_albaran: esperado 'ALQ-001.pdf', obtenido None
- ALQ-001/gemini · FALLO · IA1.cabeceras[].proveedor_nombre: esperado 'TRANSPORTES Y GRUAS ANGEL MARTIN, S.L.', obtenido 'TRANSPORTES Y GRUAS ANGEL MARTIN S.L.'
- ALQ-001/gemini · FALLO · IA1.lineas[1].caso_id: esperado 'ALQ-001', obtenido None
- ALQ-001/gemini · AVISO · IA1.lineas[1].comentario: esperado 'ha cogido una obra que no es (vieja), pero es que no hay obra indicada con codigo en el albaran', obtenido None
- ALQ-001/gemini · AVISO · IA1.lineas[1].descripcion_esperada: esperado 'SALIDA CAMIÓN GRÚA 100 TN', obtenido 'Desplazamiento'
- ALQ-001/gemini · FALLO · IA1.lineas[1].unidad: esperado 'UD', obtenido None
- ALQ-001/gemini · FALLO · IA1.lineas[2].caso_id: esperado 'ALQ-001', obtenido None
- ALQ-001/gemini · AVISO · IA1.lineas[2].descripcion_esperada: esperado 'CAMIÓN GRÚA 100 TN', obtenido 'Horas normales'
- ALQ-001/gemini · FALLO · IA1.lineas[2].unidad: esperado 'UD', obtenido None
- ALQ-001/gemini · FALLO · IA1.lineas[3].caso_id: esperado 'ALQ-001', obtenido None
- ALQ-001/gemini · AVISO · IA1.lineas[3].descripcion_esperada: esperado 'HHEE CAMIÓN GRÚA 100 TN', obtenido 'Horas extras'
- ALQ-001/gemini · FALLO · IA1.lineas[3].unidad: esperado 'UD', obtenido None
- COM-001/gemini · FALLO · IA1.cabeceras[].caso_id: esperado 'COM-001', obtenido None
- COM-001/gemini · FALLO · IA1.cabeceras[].fichero_albaran: esperado 'COM-001.pdf', obtenido None
- COM-001/gemini · FALLO · IA1.lineas[1].caso_id: esperado 'COM-001', obtenido None
- COM-001/gemini · FALLO · IA1.lineas[1].unidad: esperado 'LT', obtenido None
- FER-001/gemini · FALLO · IA1.cabeceras[].caso_id: esperado 'FER-001', obtenido None
- FER-001/gemini · FALLO · IA1.cabeceras[].fecha: esperado '2026-06-05', obtenido '2020-06-05'
- FER-001/gemini · FALLO · IA1.cabeceras[].fichero_albaran: esperado 'FER-001.pdf', obtenido None
- FER-001/gemini · FALLO · IA1.cabeceras[].proveedor_nombre: esperado 'FERRETERIA Y MAQUINARIA PARA LA CONSTRUCCION, S.A. (FEYMACO)', obtenido 'FERRETERÍA Y MAQUINARIA PARA LA CONSTRUCCIÓN, S.A.'
- FER-001/gemini · FALLO · IA1.lineas[1].caso_id: esperado 'FER-001', obtenido None
- FER-001/gemini · AVISO · IA1.lineas[1].descripcion_esperada: esperado 'DISCO ESPECIAL ACERO INOX 115x1x22', obtenido 'DISCO ESPECIAL ACERO INOX. 115X1X22'
- FER-001/gemini · FALLO · IA1.lineas[1].descuentos: esperado 40, obtenido None
- FER-001/gemini · FALLO · IA1.lineas[1].importe: esperado None, obtenido 19.41
- FER-001/gemini · FALLO · IA1.lineas[1].unidad: esperado 'UD', obtenido None
- FER-002/gemini · FALLO · IA1.cabeceras[].caso_id: esperado 'FER-002', obtenido None
- FER-002/gemini · FALLO · IA1.cabeceras[].fichero_albaran: esperado 'FER-002.pdf', obtenido None
- FER-002/gemini · FALLO · IA1.cabeceras[].proveedor_nombre: esperado 'FERRETERIA Y MAQUINARIA PARA LA CONSTRUCCION, S.A. (FEYMACO)', obtenido 'FERRETERÍA Y MAQUINARIA PARA LA CONSTRUCCIÓN, S.A.'
- FER-002/gemini · FALLO · IA1.lineas[1].cantidad: esperado 54, obtenido 108.0
- FER-002/gemini · FALLO · IA1.lineas[1].caso_id: esperado 'FER-002', obtenido None
- FER-002/gemini · AVISO · IA1.lineas[1].descripcion_esperada: esperado 'papel higienico', obtenido 'PAPEL HIGIENICO (SACO 108)'
- FER-002/gemini · FALLO · IA1.lineas[1].descuentos: esperado 40, obtenido None
- FER-002/gemini · FALLO · IA1.lineas[1].importe: esperado None, obtenido 35.19
- FER-002/gemini · FALLO · IA1.lineas[1].unidad: esperado 'UD', obtenido None
- FER-002/gemini · FALLO · IA1.lineas[2].cantidad: esperado 5, obtenido 10.0
- FER-002/gemini · FALLO · IA1.lineas[2].caso_id: esperado 'FER-002', obtenido None
- FER-002/gemini · AVISO · IA1.lineas[2].descripcion_esperada: esperado 'jabon liquido ph neutro', obtenido 'LTS. JABON LIQUIDO PH NEUTRO ****'
- FER-002/gemini · FALLO · IA1.lineas[2].descuentos: esperado 40, obtenido None
- FER-002/gemini · FALLO · IA1.lineas[2].importe: esperado None, obtenido 20.53
- FER-002/gemini · FALLO · IA1.lineas[2].unidad: esperado 'UD', obtenido None
- FER-002/gemini · FALLO · IA1.lineas[3].cantidad: esperado 6, obtenido 12.0
- FER-002/gemini · FALLO · IA1.lineas[3].caso_id: esperado 'FER-002', obtenido None
- FER-002/gemini · AVISO · IA1.lineas[3].descripcion_esperada: esperado 'rollo papel ind.', obtenido 'ROLLO PAPEL IND. (P)****'
- FER-002/gemini · FALLO · IA1.lineas[3].descuentos: esperado 40, obtenido None
- FER-002/gemini · FALLO · IA1.lineas[3].importe: esperado None, obtenido 55.63
- FER-002/gemini · FALLO · IA1.lineas[3].unidad: esperado 'UD', obtenido None
- FER-002/gemini · FALLO · IA1.lineas[4].cantidad: esperado 54, obtenido 4.0
- FER-002/gemini · FALLO · IA1.lineas[4].caso_id: esperado 'FER-002', obtenido None
- FER-002/gemini · AVISO · IA1.lineas[4].descripcion_esperada: esperado 'papel higienico', obtenido 'KGS ANIL ESPECIAL FEYMACO (SYMA-MONTSERRAT)'
- FER-002/gemini · FALLO · IA1.lineas[4].descuentos: esperado 40, obtenido None
- FER-002/gemini · FALLO · IA1.lineas[4].importe: esperado None, obtenido 13.19
- FER-002/gemini · FALLO · IA1.lineas[4].precio_unitario: esperado 0.543, obtenido 5.497
- FER-002/gemini · FALLO · IA1.lineas[4].unidad: esperado 'UD', obtenido None
- FER-002/gemini · FALLO · IA1.lineas[5].cantidad: esperado 5, obtenido 100.0
- FER-002/gemini · FALLO · IA1.lineas[5].caso_id: esperado 'FER-002', obtenido None
- FER-002/gemini · AVISO · IA1.lineas[5].descripcion_esperada: esperado 'jabon liquido ph neutro', obtenido 'BOLSA BASURA 52X58 (25 BOLSAS ROLLO)'
- FER-002/gemini · FALLO · IA1.lineas[5].descuentos: esperado 40, obtenido None
- FER-002/gemini · FALLO · IA1.lineas[5].importe: esperado None, obtenido 15.12
- FER-002/gemini · FALLO · IA1.lineas[5].precio_unitario: esperado 3.422, obtenido 0.252
- FER-002/gemini · FALLO · IA1.lineas[5].unidad: esperado 'UD', obtenido None
- FER-002/gemini · FALLO · IA1.lineas[6]: esperado {'cantidad': 6, 'caso_id': 'FER-002', 'codigo_imputacion': '@@NO_COMPARAR@@', 'comentario': None, 'descripcion_esperada': 'rollo papel ind.', 'descuentos': 40, 'importe': None, 'num_linea': 6, 'precio_unitario': 7.726, 'unidad': 'UD'}, obtenido None (fila del ground truth que el sistema no ha producido)
- FER-002/gemini · FALLO · IA1.lineas[7]: esperado {'cantidad': 4, 'caso_id': 'FER-002', 'codigo_imputacion': '@@NO_COMPARAR@@', 'comentario': None, 'descripcion_esperada': 'AÑIL ESPECIAL FEYMACO', 'descuentos': 40, 'importe': None, 'num_linea': 7, 'precio_unitario': 5.497, 'unidad': 'UD'}, obtenido None (fila del ground truth que el sistema no ha producido)
- FER-002/gemini · FALLO · IA1.lineas[8]: esperado {'cantidad': 100, 'caso_id': 'FER-002', 'codigo_imputacion': '@@NO_COMPARAR@@', 'comentario': None, 'descripcion_esperada': 'BOLSA BASURA 52x58', 'descuentos': 40, 'importe': None, 'num_linea': 8, 'precio_unitario': 0.252, 'unidad': 'UD'}, obtenido None (fila del ground truth que el sistema no ha producido)
- FER-003/gemini · FALLO · IA1.cabeceras[].caso_id: esperado 'FER-003', obtenido None
- FER-003/gemini · AVISO · IA1.cabeceras[].comentario: esperado 'ha cogido 01.04.18 en lugar de CI.04.18 | la deduccion no la ha cogido (no estaba planteado hasta ahora). En el albaran poner RTIRAR 4 disco diamante. Y una referencia a un albaran anterior (su numero de alabaran, no nuestro codigo interno)', obtenido None
- FER-003/gemini · FALLO · IA1.cabeceras[].fichero_albaran: esperado 'FER-003.pdf', obtenido None
- FER-003/gemini · FALLO · IA1.cabeceras[].proveedor_nombre: esperado 'FERRETERIA Y MAQUINARIA PARA LA CONSTRUCCION, S.A. (FEYMACO)', obtenido 'FERRETERÍA Y MAQUINARIA PARA LA CONSTRUCCIÓN, S. A.'
- FER-003/gemini · FALLO · IA1.lineas[1].caso_id: esperado 'FER-003', obtenido None
- FER-003/gemini · AVISO · IA1.lineas[1].comentario: esperado 'ha cogido 01.04.18 en lugar de CI.04.18', obtenido None
- FER-003/gemini · FALLO · IA1.lineas[1].descuentos: esperado 40, obtenido None
- FER-003/gemini · FALLO · IA1.lineas[1].precio_unitario: esperado None, obtenido 95.481
- FER-003/gemini · FALLO · IA1.lineas[1].unidad: esperado 'UD', obtenido None
- FER-003/gemini · FALLO · IA1.lineas[2]: esperado {'cantidad': -4, 'caso_id': 'FER-003', 'codigo_imputacion': '@@NO_COMPARAR@@', 'comentario': 'la deduccion no la ha cogido (no estaba planteado hasta ahora). En el albaran poner RTIRAR 4 disco diamante. Y una referencia a un albaran anterior (su numero de alabaran, no nuestro codigo interno)', 'descripcion_esperada': 'DISCO DIAMANTE 100 MM. PULIDORA (11-380)', 'descuentos': 40, 'importe': None, 'num_linea': 2, 'precio_unitario': None, 'unidad': 'UD'}, obtenido None (fila del ground truth que el sistema no ha producido)
- GEN-001/gemini · FALLO · IA1.cabeceras[].caso_id: esperado 'GEN-001', obtenido None
- GEN-001/gemini · FALLO · IA1.cabeceras[].fichero_albaran: esperado 'GEN-001.pdf', obtenido None
- GEN-001/gemini · FALLO · IA1.cabeceras[].proveedor_nombre: esperado 'VODALAND ESPAÑA, S.L', obtenido 'VODALAND ESPAÑA SL'
- GEN-001/gemini · FALLO · IA1.lineas[1].caso_id: esperado 'GEN-001', obtenido None
- GEN-001/gemini · AVISO · IA1.lineas[1].descripcion_esperada: esperado 'CANAL DE PLÁSTICO BASE DN100 H60', obtenido 'Canal de Plástico Base DN100 H60 modernizado'
- GEN-001/gemini · FALLO · IA1.lineas[1].unidad: esperado 'MT', obtenido None
- GEN-002/gemini · FALLO · IA1.cabeceras[].caso_id: esperado 'GEN-002', obtenido None
- GEN-002/gemini · AVISO · IA1.cabeceras[].comentario: esperado 'habia 2 contratos, y no ha sabido elegir uno. Podriamos hacer uqe si no sabe elegir que coja los 2, lo smerge (distinguiendo que es un mergeo) y que siga con eso. No ha coigo el capitulo inicial P5. el codigo era P5.09.03', obtenido None
- GEN-002/gemini · FALLO · IA1.cabeceras[].fichero_albaran: esperado 'GEN-002.pdf', obtenido None
- GEN-002/gemini · FALLO · IA1.cabeceras[].proveedor_nombre: esperado 'PAVIMARSA, S.A.', obtenido 'PAVIMARSA'
- GEN-002/gemini · FALLO · IA1.lineas[1].caso_id: esperado 'GEN-002', obtenido None
- GEN-002/gemini · AVISO · IA1.lineas[1].comentario: esperado 'habia 2 contratos, y no ha sabido elegir uno. Podriamos hacer uqe si no sabe elegir que coja los 2, lo smerge (distinguiendo que es un mergeo) y que siga con eso. No ha coigo el capitulo inicial P5. el codigo era P5.09.03', obtenido None
- GEN-002/gemini · AVISO · IA1.lineas[1].descripcion_esperada: esperado 'SOLADO BOREAL WHITE 60X60 cm - COCINA (OP1)', obtenido '60X60 BOREAL WHITE'
- GEN-002/gemini · FALLO · IA1.lineas[1].importe: esperado None, obtenido 14.38
- GEN-002/gemini · FALLO · IA1.lineas[1].precio_unitario: esperado None, obtenido 14.38
- GEN-002/gemini · FALLO · IA1.lineas[1].unidad: esperado 'M2', obtenido None
- GEN-002/gemini · FALLO · IA1.lineas[2].caso_id: esperado 'GEN-002', obtenido None
- GEN-002/gemini · AVISO · IA1.lineas[2].descripcion_esperada: esperado 'SOLADO SAN FRANCISCO SAND 60X60 cm - COCINA (OP2)', obtenido '60X60 SAN FRANCISCO SAND'
- GEN-002/gemini · FALLO · IA1.lineas[2].importe: esperado None, obtenido 14.38
- GEN-002/gemini · FALLO · IA1.lineas[2].precio_unitario: esperado None, obtenido 14.38
- GEN-002/gemini · FALLO · IA1.lineas[2].unidad: esperado 'M2', obtenido None
- GEN-002/gemini · FALLO · IA1.lineas[3].caso_id: esperado 'GEN-002', obtenido None
- GEN-002/gemini · AVISO · IA1.lineas[3].descripcion_esperada: esperado 'SOLADO SAN FRANCISCO GREY 60X60 cm - COCINA (OP3)', obtenido '60X60 SAN FRANCISCO GREY'
- GEN-002/gemini · FALLO · IA1.lineas[3].importe: esperado None, obtenido 14.38
- GEN-002/gemini · FALLO · IA1.lineas[3].precio_unitario: esperado None, obtenido 14.38
- GEN-002/gemini · FALLO · IA1.lineas[3].unidad: esperado 'M2', obtenido None
- GEN-002/gemini · FALLO · IA1.lineas[4].caso_id: esperado 'GEN-002', obtenido None
- GEN-002/gemini · AVISO · IA1.lineas[4].descripcion_esperada: esperado 'SOLADO BOREAL GREY 60X60 cm - BAÑOS PRINCIPALES (OP2)', obtenido '60X60 BOREAL GREY'
- GEN-002/gemini · FALLO · IA1.lineas[4].importe: esperado None, obtenido 14.38
- GEN-002/gemini · FALLO · IA1.lineas[4].precio_unitario: esperado None, obtenido 14.38
- GEN-002/gemini · FALLO · IA1.lineas[4].unidad: esperado 'M2', obtenido None
- GEN-002/gemini · FALLO · IA1.lineas[5].caso_id: esperado 'GEN-002', obtenido None
- GEN-002/gemini · AVISO · IA1.lineas[5].descripcion_esperada: esperado 'SOLADO NATURE BONE RECTIFICADO 60x60 cm - BAÑOS SECUNDARIOS (OP2)', obtenido '60X60 NATURE BONE'
- GEN-002/gemini · FALLO · IA1.lineas[5].importe: esperado None, obtenido 14.38
- GEN-002/gemini · FALLO · IA1.lineas[5].precio_unitario: esperado None, obtenido 14.38
- GEN-002/gemini · FALLO · IA1.lineas[5].unidad: esperado 'M2', obtenido None
- GEN-002/gemini · FALLO · IA1.lineas[6].caso_id: esperado 'GEN-002', obtenido None
- GEN-002/gemini · AVISO · IA1.lineas[6].descripcion_esperada: esperado 'SOLADO RC ESSEN GREY 60x60', obtenido '60X60 RC ESSEN GREY'
- GEN-002/gemini · FALLO · IA1.lineas[6].importe: esperado 621.22, obtenido 14.38
- GEN-002/gemini · FALLO · IA1.lineas[6].unidad: esperado 'M2', obtenido None
- GEN-002/gemini · FALLO · IA1.lineas[7].caso_id: esperado 'GEN-002', obtenido None
- GEN-002/gemini · AVISO · IA1.lineas[7].descripcion_esperada: esperado 'ROMANCE ROBLE 24,8x150', obtenido '24,8X150 ROMANCE ROBLE'
- GEN-002/gemini · FALLO · IA1.lineas[7].importe: esperado 11234.36, obtenido 22.44
- GEN-002/gemini · FALLO · IA1.lineas[7].unidad: esperado 'M2', obtenido None
- GEN-002/gemini · FALLO · IA1.lineas[8].cantidad: esperado 22, obtenido 23.0
- GEN-002/gemini · FALLO · IA1.lineas[8].caso_id: esperado 'GEN-002', obtenido None
- GEN-002/gemini · FALLO · IA1.lineas[8].importe: esperado 180, obtenido 9.0
- GEN-002/gemini · FALLO · IA1.lineas[8].unidad: esperado 'UD', obtenido None
- GEN-003/gemini · FALLO · IA1.cabeceras[].caso_id: esperado 'GEN-003', obtenido None
- GEN-003/gemini · FALLO · IA1.cabeceras[].fichero_albaran: esperado 'GEN-003.pdf', obtenido None
- GEN-003/gemini · FALLO · IA1.lineas[1].caso_id: esperado 'GEN-003', obtenido None
- GEN-003/gemini · AVISO · IA1.lineas[1].descripcion_esperada: esperado 'SOLADO BOREAL GREY 60X60 cm - BAÑOS PRINCIPALES (OP2)', obtenido '60X60 BOREAL GREY'
- GEN-003/gemini · FALLO · IA1.lineas[1].importe: esperado None, obtenido 14.38
- GEN-003/gemini · FALLO · IA1.lineas[1].precio_unitario: esperado None, obtenido 14.38
- GEN-003/gemini · FALLO · IA1.lineas[1].unidad: esperado 'M2', obtenido None
- GEN-003/gemini · FALLO · IA1.lineas[2].caso_id: esperado 'GEN-003', obtenido None
- GEN-003/gemini · AVISO · IA1.lineas[2].descripcion_esperada: esperado 'RODAPIÉ BOREAL GREY C/BISELADO 14,8x60 cm - BAÑOS PRINCIPALES (OP2)', obtenido '14,8X60 RODAPIE BOREAL GREY BISELADO'
- GEN-003/gemini · FALLO · IA1.lineas[2].importe: esperado None, obtenido 2.76
- GEN-003/gemini · FALLO · IA1.lineas[2].precio_unitario: esperado None, obtenido 2.76
- GEN-003/gemini · FALLO · IA1.lineas[2].unidad: esperado 'UD', obtenido None
- GEN-004/gemini · FALLO · IA1.cabeceras[].caso_id: esperado 'GEN-004', obtenido None
- GEN-004/gemini · FALLO · IA1.cabeceras[].fichero_albaran: esperado 'GEN-004.pdf', obtenido None
- GEN-004/gemini · FALLO · IA1.lineas[1].caso_id: esperado 'GEN-004', obtenido None
- GEN-004/gemini · AVISO · IA1.lineas[1].descripcion_esperada: esperado 'Inodoro Roca Gap Square Compact asiento', obtenido 'THE GAP COMPACT ASIENTO INODORO SUPRALIT BLANCO'
- GEN-004/gemini · FALLO · IA1.lineas[1].unidad: esperado 'UD', obtenido None
- GEN-005/gemini · FALLO · IA1.cabeceras[].caso_id: esperado 'GEN-005', obtenido None
- GEN-005/gemini · AVISO · IA1.cabeceras[].comentario: esperado 'la partida la ha leido mal. Ha puesto 18.04.11', obtenido None
- GEN-005/gemini · FALLO · IA1.cabeceras[].fichero_albaran: esperado 'GEN-005.pdf', obtenido None
- GEN-005/gemini · FALLO · IA1.lineas[1].caso_id: esperado 'GEN-005', obtenido None
- GEN-005/gemini · AVISO · IA1.lineas[1].comentario: esperado 'la partida la ha leido mal. Ha puesto 18.04.11', obtenido None
- GEN-005/gemini · AVISO · IA1.lineas[1].descripcion_esperada: esperado 'Inodoro Roca Gap Square Compact taza', obtenido 'THE GAP SQUARE COMPACT TAZA TANQUE BAJO 2/4L DUAL RIMLESS BL'
- GEN-005/gemini · FALLO · IA1.lineas[1].unidad: esperado 'UD', obtenido None
- GEN-005/gemini · FALLO · IA1.lineas[2].caso_id: esperado 'GEN-005', obtenido None
- GEN-005/gemini · AVISO · IA1.lineas[2].descripcion_esperada: esperado 'Reja vertedero', obtenido 'REJA ACERO INOXIDABLE VERTEDERO GARDA'
- GEN-005/gemini · FALLO · IA1.lineas[2].unidad: esperado 'UD', obtenido None
- GEN-006/gemini · FALLO · IA1.cabeceras[].caso_id: esperado 'GEN-006', obtenido None
- GEN-006/gemini · FALLO · IA1.cabeceras[].fichero_albaran: esperado 'GEN-006.pdf', obtenido None
- GEN-006/gemini · FALLO · IA1.lineas[1].caso_id: esperado 'GEN-006', obtenido None
- GEN-006/gemini · AVISO · IA1.lineas[1].descripcion_esperada: esperado 'Vertedero Roca Garda', obtenido 'VERTEDERO GARDA BLANCO'
- GEN-006/gemini · FALLO · IA1.lineas[1].unidad: esperado 'UD', obtenido None
- GEN-007/gemini · FALLO · IA1.cabeceras[].caso_id: esperado 'GEN-007', obtenido None
- GEN-007/gemini · AVISO · IA1.cabeceras[].comentario: esperado 'ha puesto unitario 0, porque pone incluido en contrato', obtenido None
- GEN-007/gemini · FALLO · IA1.cabeceras[].fichero_albaran: esperado 'GEN-007.pdf', obtenido None
- GEN-007/gemini · FALLO · IA1.lineas[1].caso_id: esperado 'GEN-007', obtenido None
- GEN-007/gemini · AVISO · IA1.lineas[1].comentario: esperado 'ha puesto unitario 0, porque pone incluido en contrato', obtenido None
- GEN-007/gemini · AVISO · IA1.lineas[1].descripcion_esperada: esperado 'Kit Victoria', obtenido 'KIT G FIJACION VICTORIA TAZA-SUELO Y BIDES'
- GEN-007/gemini · FALLO · IA1.lineas[1].unidad: esperado 'UD', obtenido None
- GEN-008/gemini · FALLO · IA1.cabeceras[].caso_id: esperado 'GEN-008', obtenido None
- GEN-008/gemini · FALLO · IA1.cabeceras[].fichero_albaran: esperado 'GEN-008.pdf', obtenido None
- GEN-008/gemini · FALLO · IA1.lineas[1].caso_id: esperado 'GEN-008', obtenido None
- GEN-008/gemini · AVISO · IA1.lineas[1].descripcion_esperada: esperado 'Reja vertedero', obtenido 'REJA ACERO INOXIDABLE VERTEDERO GARDA'
- GEN-008/gemini · FALLO · IA1.lineas[1].unidad: esperado 'UD', obtenido None
- GEN-009/gemini · FALLO · IA1.cabeceras[].caso_id: esperado 'GEN-009', obtenido None
- GEN-009/gemini · FALLO · IA1.cabeceras[].fichero_albaran: esperado 'GEN-009.pdf', obtenido None
- GEN-009/gemini · FALLO · IA1.cabeceras[].proveedor_nombre: esperado 'DICONA, S.A.', obtenido 'DICONA, S.A'
- GEN-009/gemini · FALLO · IA1.lineas[1].caso_id: esperado 'GEN-009', obtenido None
- GEN-009/gemini · AVISO · IA1.lineas[1].descripcion_esperada: esperado 'Solado Somport Light 60x120', obtenido 'M2 P KS SOMPORT 60X120 LIGHT DUR1100'
- GEN-009/gemini · FALLO · IA1.lineas[1].descuentos: esperado 8, obtenido None
- GEN-009/gemini · FALLO · IA1.lineas[1].unidad: esperado 'M2', obtenido None
- GEN-010/gemini · FALLO · IA1.cabeceras[].caso_id: esperado 'GEN-010', obtenido None
- GEN-010/gemini · AVISO · IA1.cabeceras[].comentario: esperado 'aunque pone almacen en el albaran ha cogio 02.43 que es el unitario (que lo ha usado despues para unitario acertadamente)', obtenido None
- GEN-010/gemini · FALLO · IA1.cabeceras[].fichero_albaran: esperado 'GEN-010.pdf', obtenido None
- GEN-010/gemini · FALLO · IA1.lineas[1].caso_id: esperado 'GEN-010', obtenido None
- GEN-010/gemini · AVISO · IA1.lineas[1].comentario: esperado 'aunque pone almacen en el albaran ha cogio 02.43 que es el unitario (que lo ha usado despues para unitario acertadamente)', obtenido None
- GEN-010/gemini · AVISO · IA1.lineas[1].descripcion_esperada: esperado 'TUBO DRENAJE 240º Ø160', obtenido 'TB DRENAJE D.160 D/P BARRA 6M 240° PE'
- GEN-010/gemini · FALLO · IA1.lineas[1].precio_unitario: esperado None, obtenido 2.43
- GEN-010/gemini · FALLO · IA1.lineas[1].unidad: esperado 'MT', obtenido None
- GRA-001/gemini · FALLO · IA1.cabeceras[].caso_id: esperado 'GRA-001', obtenido None
- GRA-001/gemini · AVISO · IA1.cabeceras[].comentario: esperado 'La unidad esta bien, pero ha cogio un unitario que no es. Es grava 20/40 (se deduce del texto, esta en el contrato), el unitario es 12,86', obtenido None
- GRA-001/gemini · FALLO · IA1.cabeceras[].fichero_albaran: esperado 'GRA-001.pdf', obtenido None
- GRA-001/gemini · FALLO · IA1.cabeceras[].proveedor_nombre: esperado 'MATERIALES Y HORMIGONES, S.L. (MAHORSA)', obtenido 'MATERIALES Y HORMIGONES S.L.'
- GRA-001/gemini · FALLO · IA1.lineas[1].cantidad: esperado 30.38, obtenido 30380.0
- GRA-001/gemini · FALLO · IA1.lineas[1].caso_id: esperado 'GRA-001', obtenido None
- GRA-001/gemini · AVISO · IA1.lineas[1].comentario: esperado 'La unidad esta bien, pero ha cogio un unitario que no es. Es grava 20/40 (se deduce del texto, esta en el contrato), el unitario es 12,86', obtenido None
- GRA-001/gemini · AVISO · IA1.lineas[1].descripcion_esperada: esperado 'GRAVA 20/40', obtenido 'ARIDO M-20/40-S EN 12620:2002'
- GRA-001/gemini · FALLO · IA1.lineas[1].unidad: esperado 'TN', obtenido None
- GRA-002/gemini · FALLO · IA1.cabeceras[].caso_id: esperado 'GRA-002', obtenido None
- GRA-002/gemini · AVISO · IA1.cabeceras[].comentario: esperado 'La partida ha cogido PT.03.04 en lugar de P5.03.04La unidad esta bien, pero ha cogio un unitario que no es. Es grava 20/40 (se deduce del texto, esta en el contrato), el unitario es 12,87', obtenido None
- GRA-002/gemini · FALLO · IA1.cabeceras[].fichero_albaran: esperado 'GRA-002.pdf', obtenido None
- GRA-002/gemini · FALLO · IA1.cabeceras[].proveedor_nombre: esperado 'MATERIALES Y HORMIGONES, S.L. (MAHORSA)', obtenido 'MATERIALES Y HORMIGONES S.L.'
- GRA-002/gemini · FALLO · IA1.lineas[1].cantidad: esperado 29.96, obtenido 29960.0
- GRA-002/gemini · FALLO · IA1.lineas[1].caso_id: esperado 'GRA-002', obtenido None
- GRA-002/gemini · AVISO · IA1.lineas[1].comentario: esperado 'La partida ha cogido PT.03.04 en lugar de P5.03.04La unidad esta bien, pero ha cogio un unitario que no es. Es grava 20/40 (se deduce del texto, esta en el contrato), el unitario es 12,87', obtenido None
- GRA-002/gemini · AVISO · IA1.lineas[1].descripcion_esperada: esperado 'GRAVA 20/40', obtenido 'ARIDO M-20/4D-S EN 12620:2002M'
- GRA-002/gemini · FALLO · IA1.lineas[1].unidad: esperado 'TN', obtenido None
- HOR-001/gemini · FALLO · IA1.cabeceras[].caso_id: esperado 'HOR-001', obtenido None
- HOR-001/gemini · AVISO · IA1.cabeceras[].comentario: esperado 'falta P5 al inicio de la partida.', obtenido None
- HOR-001/gemini · FALLO · IA1.cabeceras[].fichero_albaran: esperado 'HOR-001.pdf', obtenido None
- HOR-001/gemini · FALLO · IA1.lineas[1].caso_id: esperado 'HOR-001', obtenido None
- HOR-001/gemini · AVISO · IA1.lineas[1].comentario: esperado 'falta P5 al inicio de la partida.', obtenido None
- HOR-001/gemini · AVISO · IA1.lineas[1].descripcion_esperada: esperado 'HORMIGÓN HA-25/B/20/XC2', obtenido 'HA-25/B/20/XC2'
- HOR-001/gemini · FALLO · IA1.lineas[1].unidad: esperado 'M3', obtenido None
- HOR-002/gemini · FALLO · IA1.cabeceras[].caso_id: esperado 'HOR-002', obtenido None
- HOR-002/gemini · AVISO · IA1.cabeceras[].comentario: esperado 'Sale PJ.03.04 en la partida. Es P5, es dificil de leer. A la hora de localizar la partida, se puede hacer que busque entre la lista de partidas de la obra (nivel mas bajo, justo superior a los descompuestos)', obtenido None
- HOR-002/gemini · FALLO · IA1.cabeceras[].fichero_albaran: esperado 'HOR-002.pdf', obtenido None
- HOR-002/gemini · FALLO · IA1.lineas[1].caso_id: esperado 'HOR-002', obtenido None
- HOR-002/gemini · AVISO · IA1.lineas[1].comentario: esperado 'Sale PJ.03.04 en la partida. Es P5, es dificil de leer. A la hora de localizar la partida, se puede hacer que busque entre la lista de partidas de la obra (nivel mas bajo, justo superior a los descompuestos)', obtenido None
- HOR-002/gemini · AVISO · IA1.lineas[1].descripcion_esperada: esperado 'HORMIGÓN HA-25/B/20/XC2', obtenido 'HA-25/B/20/XC2'
- HOR-002/gemini · FALLO · IA1.lineas[1].unidad: esperado 'M3', obtenido None
- HOR-003/gemini · FALLO · IA1.cabeceras[].caso_id: esperado 'HOR-003', obtenido None
- HOR-003/gemini · AVISO · IA1.cabeceras[].comentario: esperado 'Partida deberia ser P4.03.05, es verdad que casi parece un 0 el primer digito. Por eso buscar en lista de partidas', obtenido None
- HOR-003/gemini · FALLO · IA1.cabeceras[].fichero_albaran: esperado 'HOR-003.pdf', obtenido None
- HOR-003/gemini · FALLO · IA1.cabeceras[].proveedor_nombre: esperado 'FABRICACION DE HORMIGONES PAZ DEL BARRIO,S.L.', obtenido 'HORMIGONES PAZ DEL BARRIO'
- HOR-003/gemini · FALLO · IA1.lineas[1].caso_id: esperado 'HOR-003', obtenido None
- HOR-003/gemini · AVISO · IA1.lineas[1].comentario: esperado 'Partida deberia ser P4.03.05, es verdad que casi parece un 0 el primer digito. Por eso buscar en lista de partidas', obtenido None
- HOR-003/gemini · AVISO · IA1.lineas[1].descripcion_esperada: esperado 'HORMIGÓN HA-25/B/20/XC2', obtenido 'HA-25/B/20/XC2'
- HOR-003/gemini · FALLO · IA1.lineas[1].unidad: esperado 'M3', obtenido None
- HOR-004/gemini · FALLO · IA1.cabeceras[].caso_id: esperado 'HOR-004', obtenido None
- HOR-004/gemini · AVISO · IA1.cabeceras[].comentario: esperado 'esta linea no la ha generado. Marca sin aditivo (y encima subrayado con rotulador) cuando ponga hay que generar linea', obtenido None
- HOR-004/gemini · FALLO · IA1.cabeceras[].fichero_albaran: esperado 'HOR-004.pdf', obtenido None
- HOR-004/gemini · FALLO · IA1.lineas[1].caso_id: esperado 'HOR-004', obtenido None
- HOR-004/gemini · AVISO · IA1.lineas[1].descripcion_esperada: esperado 'HORMIGON PREPARADOS EN CENTRAL HA-25.', obtenido 'HA-25/F/12/XC1'
- HOR-004/gemini · FALLO · IA1.lineas[1].unidad: esperado 'M3', obtenido None
- HOR-004/gemini · FALLO · IA1.lineas[2]: esperado {'cantidad': 10, 'caso_id': 'HOR-004', 'codigo_imputacion': '@@NO_COMPARAR@@', 'comentario': 'esta linea no la ha generado. Marca sin aditivo (y encima subrayado con rotulador) cuando ponga hay que generar linea', 'descripcion_esperada': 'INCREMENTO POR SIN ADITIVO', 'descuentos': None, 'importe': None, 'num_linea': 2, 'precio_unitario': None, 'unidad': 'M3'}, obtenido None (fila del ground truth que el sistema no ha producido)
- HOR-004/gemini · FALLO · IA1.lineas[3]: esperado {'cantidad': 10, 'caso_id': 'HOR-004', 'codigo_imputacion': '@@NO_COMPARAR@@', 'comentario': None, 'descripcion_esperada': 'INCREMENTO POR ÁRIDO 12 EN HORMIGÓN', 'descuentos': None, 'importe': None, 'num_linea': 3, 'precio_unitario': None, 'unidad': 'M3'}, obtenido None (fila del ground truth que el sistema no ha producido)
- HOR-004/gemini · FALLO · IA1.lineas[4]: esperado {'cantidad': 10, 'caso_id': 'HOR-004', 'codigo_imputacion': '@@NO_COMPARAR@@', 'comentario': None, 'descripcion_esperada': 'INCREMENTO POR CONSISTENCIA FLUIDA EN HORMIGON', 'descuentos': None, 'importe': None, 'num_linea': 4, 'precio_unitario': None, 'unidad': 'M3'}, obtenido None (fila del ground truth que el sistema no ha producido)
- HOR-004/gemini · FALLO · IA1.lineas[5]: esperado {'cantidad': 10, 'caso_id': 'HOR-004', 'codigo_imputacion': '@@NO_COMPARAR@@', 'comentario': None, 'descripcion_esperada': 'INCREMENTO POR FIBRAS', 'descuentos': None, 'importe': None, 'num_linea': 5, 'precio_unitario': None, 'unidad': 'M3'}, obtenido None (fila del ground truth que el sistema no ha producido)
- HOR-005/gemini · FALLO · IA1.cabeceras[].caso_id: esperado 'HOR-005', obtenido None
- HOR-005/gemini · AVISO · IA1.cabeceras[].comentario: esperado 'ha codigo partida 02.05 pero no se de donde lo ha sacado. Si no hay partida es almacen', obtenido None
- HOR-005/gemini · FALLO · IA1.cabeceras[].fichero_albaran: esperado 'HOR-005.pdf', obtenido None
- HOR-005/gemini · FALLO · IA1.lineas[1].caso_id: esperado 'HOR-005', obtenido None
- HOR-005/gemini · AVISO · IA1.lineas[1].comentario: esperado 'ha codigo partida 02.05 pero no se de donde lo ha sacado. Si no hay partida es almacen', obtenido None
- HOR-005/gemini · FALLO · IA1.lineas[1].unidad: esperado 'M3', obtenido None
- HOR-005/gemini · FALLO · IA1.lineas[2]: esperado {'cantidad': 4, 'caso_id': 'HOR-005', 'codigo_imputacion': '@@NO_COMPARAR@@', 'comentario': 'ha codigo partida 02.05 pero no se de donde lo ha sacado. Si no hay partida es almacen', 'descripcion_esperada': 'ADICIÓN FIBRAS POLIPROPILENO (600 GR/M3)', 'descuentos': None, 'importe': None, 'num_linea': 2, 'precio_unitario': None, 'unidad': 'M3'}, obtenido None (fila del ground truth que el sistema no ha producido)
- HOR-005/gemini · FALLO · IA1.lineas[3]: esperado {'cantidad': 4, 'caso_id': 'HOR-005', 'codigo_imputacion': '@@NO_COMPARAR@@', 'comentario': 'ha codigo partida 02.05 pero no se de donde lo ha sacado. Si no hay partida es almacen', 'descripcion_esperada': 'INCREMENTO ARIDO 15', 'descuentos': None, 'importe': None, 'num_linea': 3, 'precio_unitario': None, 'unidad': 'M3'}, obtenido None (fila del ground truth que el sistema no ha producido)
- HOR-005/gemini · FALLO · IA1.lineas[4]: esperado {'cantidad': 4, 'caso_id': 'HOR-005', 'codigo_imputacion': '@@NO_COMPARAR@@', 'comentario': 'ha codigo partida 02.05 pero no se de donde lo ha sacado. Si no hay partida es almacen', 'descripcion_esperada': 'INCREMENTO FRATASADO', 'descuentos': None, 'importe': None, 'num_linea': 4, 'precio_unitario': None, 'unidad': 'M3'}, obtenido None (fila del ground truth que el sistema no ha producido)
- HOR-005/gemini · FALLO · IA1.lineas[5]: esperado {'cantidad': 2, 'caso_id': 'HOR-005', 'codigo_imputacion': '@@NO_COMPARAR@@', 'comentario': 'ha codigo partida 02.05 pero no se de donde lo ha sacado. Si no hay partida es almacen', 'descripcion_esperada': 'HA-25/B/20/XC2. CARGA INCOMPLETA', 'descuentos': None, 'importe': None, 'num_linea': 5, 'precio_unitario': None, 'unidad': 'M3'}, obtenido None (fila del ground truth que el sistema no ha producido)
- HOR-006/gemini · FALLO · IA1.cabeceras[].caso_id: esperado 'HOR-006', obtenido None
- HOR-006/gemini · AVISO · IA1.cabeceras[].comentario: esperado 'ha codigo partida 02.05 pero no se de donde lo ha sacado, ni de donde lo ha sacado negocio', obtenido None
- HOR-006/gemini · FALLO · IA1.cabeceras[].fichero_albaran: esperado 'HOR-006.pdf', obtenido None
- HOR-006/gemini · FALLO · IA1.lineas[1].caso_id: esperado 'HOR-006', obtenido None
- HOR-006/gemini · AVISO · IA1.lineas[1].comentario: esperado 'ha codigo partida 02.05 pero no se de donde lo ha sacado, ni de donde lo ha sacado negocio', obtenido None
- HOR-006/gemini · AVISO · IA1.lineas[1].descripcion_esperada: esperado 'HA-25/B/20/XC2', obtenido 'HA-25/B/20/XC2/$'
- HOR-006/gemini · FALLO · IA1.lineas[1].unidad: esperado 'M3', obtenido None
- HOR-007/gemini · FALLO · IA1.cabeceras[].caso_id: esperado 'HOR-007', obtenido None
- HOR-007/gemini · FALLO · IA1.cabeceras[].fichero_albaran: esperado 'HOR-007.pdf', obtenido None
- HOR-007/gemini · FALLO · IA1.lineas[1].caso_id: esperado 'HOR-007', obtenido None
- HOR-007/gemini · FALLO · IA1.lineas[1].unidad: esperado 'M3', obtenido None
- HOR-007/gemini · FALLO · IA1.lineas[2]: esperado {'cantidad': 1, 'caso_id': 'HOR-007', 'codigo_imputacion': '@@NO_COMPARAR@@', 'comentario': None, 'descripcion_esperada': 'HA-25/B/20/XC2. CARGA INCOMPLETA', 'descuentos': None, 'importe': None, 'num_linea': 2, 'precio_unitario': None, 'unidad': 'M3'}, obtenido None (fila del ground truth que el sistema no ha producido)
- HOR-008/gemini · FALLO · IA1.cabeceras[].caso_id: esperado 'HOR-008', obtenido None
- HOR-008/gemini · AVISO · IA1.cabeceras[].comentario: esperado 'partida ha cogido 02.01, pero no se de donde sale ni de donde la coge neogcio', obtenido None
- HOR-008/gemini · FALLO · IA1.cabeceras[].fichero_albaran: esperado 'HOR-008.pdf', obtenido None
- HOR-008/gemini · FALLO · IA1.lineas[1].caso_id: esperado 'HOR-008', obtenido None
- HOR-008/gemini · AVISO · IA1.lineas[1].comentario: esperado 'partida ha cogido 02.01, pero no se de donde sale ni de donde la coge neogcio', obtenido None
- HOR-008/gemini · FALLO · IA1.lineas[1].unidad: esperado 'M3', obtenido None
- HOR-009/gemini · FALLO · IA1.cabeceras[].caso_id: esperado 'HOR-009', obtenido None
- HOR-009/gemini · AVISO · IA1.cabeceras[].comentario: esperado 'partida ha cogido 10.04.01, pero no se de donde sale ni de donde la coge neogcio. El codigo de hormigon leido es correcto, pero luego lo ha cambiado en la descripcion de la linea de sigrid para casarlo. El codigo de hormigon no se puede cambiar | partida ha cogido 10.04.01, pero no se de donde sale ni de donde la coge neogcio | partida ha cogido 10.04.01, pero no se de donde sale ni de donde la coge neogcio- esta linea no la ha generado, pero pon B en el codigo asi que parece error de negocio', obtenido None
- HOR-009/gemini · FALLO · IA1.cabeceras[].fichero_albaran: esperado 'HOR-009.pdf', obtenido None
- HOR-009/gemini · FALLO · IA1.lineas[1].caso_id: esperado 'HOR-009', obtenido None
- HOR-009/gemini · AVISO · IA1.lineas[1].comentario: esperado 'partida ha cogido 10.04.01, pero no se de donde sale ni de donde la coge neogcio. El codigo de hormigon leido es correcto, pero luego lo ha cambiado en la descripcion de la linea de sigrid para casarlo. El codigo de hormigon no se puede cambiar', obtenido None
- HOR-009/gemini · FALLO · IA1.lineas[1].unidad: esperado 'M3', obtenido None
- HOR-009/gemini · FALLO · IA1.lineas[2]: esperado {'cantidad': 8, 'caso_id': 'HOR-009', 'codigo_imputacion': '@@NO_COMPARAR@@', 'comentario': 'partida ha cogido 10.04.01, pero no se de donde sale ni de donde la coge neogcio', 'descripcion_esperada': 'ADICIÓN FIBRAS POLIPROPILENO (600 GR/M3)', 'descuentos': None, 'importe': None, 'num_linea': 2, 'precio_unitario': None, 'unidad': 'M3'}, obtenido None (fila del ground truth que el sistema no ha producido)
- HOR-009/gemini · FALLO · IA1.lineas[3]: esperado {'cantidad': 8, 'caso_id': 'HOR-009', 'codigo_imputacion': '@@NO_COMPARAR@@', 'comentario': 'partida ha cogido 10.04.01, pero no se de donde sale ni de donde la coge neogcio- esta linea no la ha generado, pero pon B en el codigo asi que parece error de negocio', 'descripcion_esperada': 'INCREM. CONSISTENCIA FLUIDA', 'descuentos': None, 'importe': None, 'num_linea': 3, 'precio_unitario': None, 'unidad': 'M3'}, obtenido None (fila del ground truth que el sistema no ha producido)
- HOR-010/gemini · FALLO · IA1.cabeceras[].caso_id: esperado 'HOR-010', obtenido None
- HOR-010/gemini · AVISO · IA1.cabeceras[].comentario: esperado 'ha cambiado codigo de linea de hormigon en descripcion para casar con sigrid. El codigo del hormigon no se cambia | no la ha generado. Y hay cambio de año entre contrato (ver codigo) y año de albaran. Deberia haberlo hecho', obtenido None
- HOR-010/gemini · FALLO · IA1.cabeceras[].fichero_albaran: esperado 'HOR-010.pdf', obtenido None
- HOR-010/gemini · FALLO · IA1.lineas[1].caso_id: esperado 'HOR-010', obtenido None
- HOR-010/gemini · AVISO · IA1.lineas[1].descripcion_esperada: esperado 'HA-25/F/20/XC2', obtenido 'HA-25/F/20/XC2 EQUIVALENTE A HA-25/B/20/I ó IIa'
- HOR-010/gemini · FALLO · IA1.lineas[1].unidad: esperado 'M3', obtenido None
- HOR-010/gemini · FALLO · IA1.lineas[2]: esperado {'cantidad': 8, 'caso_id': 'HOR-010', 'codigo_imputacion': '@@NO_COMPARAR@@', 'comentario': 'ha cambiado codigo de linea de hormigon en descripcion para casar con sigrid. El codigo del hormigon no se cambia', 'descripcion_esperada': 'INCREM. CONSISTENCIA FLUIDA', 'descuentos': None, 'importe': None, 'num_linea': 2, 'precio_unitario': None, 'unidad': 'M3'}, obtenido None (fila del ground truth que el sistema no ha producido)
- HOR-011/gemini · FALLO · IA1.cabeceras[].caso_id: esperado 'HOR-011', obtenido None
- HOR-011/gemini · FALLO · IA1.cabeceras[].fichero_albaran: esperado 'HOR-011.pdf', obtenido None
- HOR-011/gemini · FALLO · IA1.lineas[1].caso_id: esperado 'HOR-011', obtenido None
- HOR-011/gemini · FALLO · IA1.lineas[1].unidad: esperado 'M3', obtenido None
- HOR-012/gemini · FALLO · IA1.cabeceras[].caso_id: esperado 'HOR-012', obtenido None
- HOR-012/gemini · AVISO · IA1.cabeceras[].comentario: esperado 'no habia elegido contrato. Cuando sean 2 vamos a unirlos. Y que no elija. El incremento de precio se calcula contra año contrato antiguo | no se de donde saca la partida. Ha puesto 02.01.02 | no se de donde saca la partida. Ha puesto 02.01.02. importe de oferta, ahora no sale', obtenido None
- HOR-012/gemini · FALLO · IA1.cabeceras[].fichero_albaran: esperado 'HOR-012.pdf', obtenido None
- HOR-012/gemini · FALLO · IA1.cabeceras[].proveedor_nombre: esperado 'HORMIGONES Y CEMENTOS ANDALUCES, S.L.', obtenido 'HORMIGONES Y CEMENTOS ANDALUCES'
- HOR-012/gemini · FALLO · IA1.lineas[1].caso_id: esperado 'HOR-012', obtenido None
- HOR-012/gemini · AVISO · IA1.lineas[1].comentario: esperado 'no habia elegido contrato. Cuando sean 2 vamos a unirlos. Y que no elija. El incremento de precio se calcula contra año contrato antiguo', obtenido None
- HOR-012/gemini · FALLO · IA1.lineas[1].unidad: esperado 'M3', obtenido None
- HOR-012/gemini · FALLO · IA1.lineas[2]: esperado {'cantidad': 9, 'caso_id': 'HOR-012', 'codigo_imputacion': '@@NO_COMPARAR@@', 'comentario': 'no se de donde saca la partida. Ha puesto 02.01.02', 'descripcion_esperada': 'INCREM. CONSISTENCIA FLUIDA', 'descuentos': None, 'importe': None, 'num_linea': 2, 'precio_unitario': None, 'unidad': 'M3'}, obtenido None (fila del ground truth que el sistema no ha producido)
- HOR-013/gemini · FALLO · IA1.cabeceras[].caso_id: esperado 'HOR-013', obtenido None
- HOR-013/gemini · AVISO · IA1.cabeceras[].comentario: esperado 'el contrato elegido estaba mal. Tiene 2. al quere cambiar de contrato en el desplegable solo me salia el seleccionado y sin contrato, he tenido que poner sin contrato para que me salgan los 2', obtenido None
- HOR-013/gemini · FALLO · IA1.cabeceras[].fichero_albaran: esperado 'HOR-013.pdf', obtenido None
- HOR-013/gemini · FALLO · IA1.cabeceras[].proveedor_nombre: esperado 'HORMIGONES Y CEMENTOS ANDALUCES, S.L.', obtenido 'HORMIGONES Y CEMENTOS ANDALUCES'
- HOR-013/gemini · FALLO · IA1.lineas[1].caso_id: esperado 'HOR-013', obtenido None
- HOR-013/gemini · AVISO · IA1.lineas[1].comentario: esperado 'el contrato elegido estaba mal. Tiene 2. al quere cambiar de contrato en el desplegable solo me salia el seleccionado y sin contrato, he tenido que poner sin contrato para que me salgan los 2', obtenido None
- HOR-013/gemini · AVISO · IA1.lineas[1].descripcion_esperada: esperado 'HA-25/B/22/XC2', obtenido 'HORMIGÓN HA-25/B/22/XC2'
- HOR-013/gemini · FALLO · IA1.lineas[1].unidad: esperado 'M3', obtenido None
- HOR-014/gemini · FALLO · IA1.cabeceras[].caso_id: esperado 'HOR-014', obtenido None
- HOR-014/gemini · AVISO · IA1.cabeceras[].comentario: esperado 'el contrato elegido estaba mal. Tiene 2. al quere cambiar de contrato en el desplegable solo me salia el seleccionado y sin contrato, he tenido que poner sin contrato para que me salgan los 2 | el contrato elegido estaba mal. Tiene 2. al quere cambiar de contrato en el desplegable solo me salia el seleccionado y sin contrato, he tenido que poner sin contrato para que me salgan los 2.como se que es final de bombeo?. Ha leido bien que cantidad es 5, deberia haber pueesto cantidad en carga incompleta 1. analizar porque no lo ha hecho', obtenido None
- HOR-014/gemini · FALLO · IA1.cabeceras[].fichero_albaran: esperado 'HOR-014.pdf', obtenido None
- HOR-014/gemini · FALLO · IA1.cabeceras[].proveedor_nombre: esperado 'HORMIGONES Y CEMENTOS ANDALUCES, S.L.', obtenido 'HORMIGONES Y CEMENTOS ANDALUCES ALGARROBO'
- HOR-014/gemini · FALLO · IA1.lineas[1].caso_id: esperado 'HOR-014', obtenido None
- HOR-014/gemini · AVISO · IA1.lineas[1].comentario: esperado 'el contrato elegido estaba mal. Tiene 2. al quere cambiar de contrato en el desplegable solo me salia el seleccionado y sin contrato, he tenido que poner sin contrato para que me salgan los 2', obtenido None
- HOR-014/gemini · FALLO · IA1.lineas[1].unidad: esperado 'M3', obtenido None
- HOR-014/gemini · FALLO · IA1.lineas[2]: esperado {'cantidad': 1, 'caso_id': 'HOR-014', 'codigo_imputacion': '@@NO_COMPARAR@@', 'comentario': 'el contrato elegido estaba mal. Tiene 2. al quere cambiar de contrato en el desplegable solo me salia el seleccionado y sin contrato, he tenido que poner sin contrato para que me salgan los 2.como se que es final de bombeo?. Ha leido bien que cantidad es 5, deberia haber pueesto cantidad en carga incompleta 1. analizar porque no lo ha hecho', 'descripcion_esperada': 'CARGA INCOMPLETA. NO PROCEDE. FINAL DE BOMBEO', 'descuentos': None, 'importe': None, 'num_linea': 2, 'precio_unitario': None, 'unidad': 'M3'}, obtenido None (fila del ground truth que el sistema no ha producido)
- HOR-015/gemini · FALLO · IA1.cabeceras[].caso_id: esperado 'HOR-015', obtenido None
- HOR-015/gemini · AVISO · IA1.cabeceras[].comentario: esperado 'no habia elegido contrato. Cuando sean 2 vamos a unirlos. Y que no elija. El incremento de precio se calcula contra año contrato antiguo | no se de donde saca la partida. Ha puesto 02.01.02 | no se de donde saca la partida. Ha puesto 02.01.02. importe de oferta, ahora no sale', obtenido None
- HOR-015/gemini · FALLO · IA1.cabeceras[].fichero_albaran: esperado 'HOR-015.pdf', obtenido None
- HOR-015/gemini · FALLO · IA1.cabeceras[].proveedor_nombre: esperado 'HORMIGONES Y CEMENTOS ANDALUCES, S.L.', obtenido 'HORMIGONES Y CEMENTOS ANDALUCES'
- HOR-015/gemini · FALLO · IA1.lineas[1].caso_id: esperado 'HOR-015', obtenido None
- HOR-015/gemini · AVISO · IA1.lineas[1].comentario: esperado 'no habia elegido contrato. Cuando sean 2 vamos a unirlos. Y que no elija. El incremento de precio se calcula contra año contrato antiguo', obtenido None
- HOR-015/gemini · AVISO · IA1.lineas[1].descripcion_esperada: esperado 'HA-25/F/12/XC2/1', obtenido 'HA-25/F/12/XC2/I'
- HOR-015/gemini · FALLO · IA1.lineas[1].unidad: esperado 'M3', obtenido None
- HOR-015/gemini · FALLO · IA1.lineas[2]: esperado {'cantidad': 7, 'caso_id': 'HOR-015', 'codigo_imputacion': '@@NO_COMPARAR@@', 'comentario': 'no se de donde saca la partida. Ha puesto 02.01.02', 'descripcion_esperada': 'INCREM. ARIDO 12', 'descuentos': None, 'importe': None, 'num_linea': 2, 'precio_unitario': None, 'unidad': 'M3'}, obtenido None (fila del ground truth que el sistema no ha producido)
- HOR-015/gemini · FALLO · IA1.lineas[3]: esperado {'cantidad': 7, 'caso_id': 'HOR-015', 'codigo_imputacion': '@@NO_COMPARAR@@', 'comentario': 'no se de donde saca la partida. Ha puesto 02.01.02', 'descripcion_esperada': 'INCREM. CONSISTENCIA FLUIDA', 'descuentos': None, 'importe': None, 'num_linea': 3, 'precio_unitario': None, 'unidad': 'M3'}, obtenido None (fila del ground truth que el sistema no ha producido)
- HOR-016/gemini · FALLO · IA1.cabeceras[].caso_id: esperado 'HOR-016', obtenido None
- HOR-016/gemini · AVISO · IA1.cabeceras[].comentario: esperado 'el contrato elegido estaba mal. Tiene 2. al quere cambiar de contrato en el desplegable solo me salia el seleccionado y sin contrato, he tenido que poner sin contrato para que me salgan los 2 | no ha salido esta linea. Porque no la ha generado? El contrato es 2024 (se ve en codigo) y el alabran 2025', obtenido None
- HOR-016/gemini · FALLO · IA1.cabeceras[].fichero_albaran: esperado 'HOR-016.pdf', obtenido None
- HOR-016/gemini · FALLO · IA1.cabeceras[].proveedor_nombre: esperado 'HORMIGONES Y CEMENTOS ANDALUCES, S.L.', obtenido 'HORMIGONES Y CEMENTOS ANDALUCES'
- HOR-016/gemini · FALLO · IA1.lineas[1].caso_id: esperado 'HOR-016', obtenido None
- HOR-016/gemini · AVISO · IA1.lineas[1].comentario: esperado 'el contrato elegido estaba mal. Tiene 2. al quere cambiar de contrato en el desplegable solo me salia el seleccionado y sin contrato, he tenido que poner sin contrato para que me salgan los 2', obtenido None
- HOR-016/gemini · FALLO · IA1.lineas[1].unidad: esperado 'M3', obtenido None
- HOR-017/gemini · FALLO · IA1.cabeceras[].caso_id: esperado 'HOR-017', obtenido None
- HOR-017/gemini · AVISO · IA1.cabeceras[].comentario: esperado 'cantida mal. En m3 sale 3 en el albaran. Ha puesto 8. de ahi se deduce carga incompleta. no se de donde saca la partida. Ha puesto 02.01.02. no habia elegido contrato', obtenido None
- HOR-017/gemini · FALLO · IA1.cabeceras[].fichero_albaran: esperado 'HOR-017.pdf', obtenido None
- HOR-017/gemini · FALLO · IA1.cabeceras[].proveedor_nombre: esperado 'HORMIGONES Y CEMENTOS ANDALUCES, S.L.', obtenido 'HORMIGONES Y CEMENTOS ANDALUCES'
- HOR-017/gemini · FALLO · IA1.lineas[1].caso_id: esperado 'HOR-017', obtenido None
- HOR-017/gemini · AVISO · IA1.lineas[1].comentario: esperado 'cantida mal. En m3 sale 3 en el albaran. Ha puesto 8. de ahi se deduce carga incompleta. no se de donde saca la partida. Ha puesto 02.01.02. no habia elegido contrato', obtenido None
- HOR-017/gemini · FALLO · IA1.lineas[1].unidad: esperado 'M3', obtenido None
- HOR-017/gemini · FALLO · IA1.lineas[2]: esperado {'cantidad': 3, 'caso_id': 'HOR-017', 'codigo_imputacion': '@@NO_COMPARAR@@', 'comentario': 'cantida mal. En m3 sale 3 en el albaran. Ha puesto 8. de ahi se deduce carga incompleta. no se de donde saca la partida. Ha puesto 02.01.02. no habia elegido contrato', 'descripcion_esperada': 'INCREM. ARIDO 12', 'descuentos': None, 'importe': None, 'num_linea': 2, 'precio_unitario': None, 'unidad': 'M3'}, obtenido None (fila del ground truth que el sistema no ha producido)
- HOR-017/gemini · FALLO · IA1.lineas[3]: esperado {'cantidad': 3, 'caso_id': 'HOR-017', 'codigo_imputacion': '@@NO_COMPARAR@@', 'comentario': 'cantida mal. En m3 sale 3 en el albaran. Ha puesto 8. de ahi se deduce carga incompleta. no se de donde saca la partida. Ha puesto 02.01.02. no habia elegido contrato', 'descripcion_esperada': 'INCREM. CONSISTENCIA FLUIDA', 'descuentos': None, 'importe': None, 'num_linea': 3, 'precio_unitario': None, 'unidad': 'M3'}, obtenido None (fila del ground truth que el sistema no ha producido)
- HOR-017/gemini · FALLO · IA1.lineas[4]: esperado {'cantidad': 3, 'caso_id': 'HOR-017', 'codigo_imputacion': '@@NO_COMPARAR@@', 'comentario': 'cantida mal. En m3 sale 3 en el albaran. Ha puesto 8. de ahi se deduce carga incompleta. no se de donde saca la partida. Ha puesto 02.01.02. no habia elegido contrato', 'descripcion_esperada': 'CARGA INCOMPLETA', 'descuentos': None, 'importe': None, 'num_linea': 4, 'precio_unitario': None, 'unidad': 'M3'}, obtenido None (fila del ground truth que el sistema no ha producido)
- MOR-001/gemini · FALLO · IA1.cabeceras[].caso_id: esperado 'MOR-001', obtenido None
- MOR-001/gemini · AVISO · IA1.cabeceras[].comentario: esperado 'la partida ha puesto RJ.14.01.02.02 en lugar de P5.14.01.02.02 | No ha cogido la linea. El mortero tambien tiene incremento de precio por año como hormigon. Sale en el contrato. Si sale en el contrato hay que analizarlo', obtenido None
- MOR-001/gemini · FALLO · IA1.cabeceras[].fichero_albaran: esperado 'MOR-001.pdf', obtenido None
- MOR-001/gemini · FALLO · IA1.lineas[1].caso_id: esperado 'MOR-001', obtenido None
- MOR-001/gemini · AVISO · IA1.lineas[1].comentario: esperado 'la partida ha puesto RJ.14.01.02.02 en lugar de P5.14.01.02.02', obtenido None
- MOR-001/gemini · AVISO · IA1.lineas[1].descripcion_esperada: esperado 'MORTERO PREP. M-7,5', obtenido 'M-7,5/B/4'
- MOR-001/gemini · FALLO · IA1.lineas[1].unidad: esperado 'M3', obtenido None
- MOR-002/gemini · FALLO · IA1.cabeceras[].caso_id: esperado 'MOR-002', obtenido None
- MOR-002/gemini · AVISO · IA1.cabeceras[].comentario: esperado 'La partida ha puesto 14.01.02.02, cuando es P4.01.02.02. partida debe buscar en lista de partidas de la obra | La partida ha puesto 14.01.02.02, cuando es P4.01.02.02. partida debe buscar en lista de partidas de la obra. No ha creado esta linea. Sin embargo hay una casilla claramente donde dice carga incompleta 3. los morteross tambien tienen carga incompleta como los hormigones, añadir a la tipologia', obtenido None
- MOR-002/gemini · FALLO · IA1.cabeceras[].fichero_albaran: esperado 'MOR-002.pdf', obtenido None
- MOR-002/gemini · FALLO · IA1.cabeceras[].proveedor_nombre: esperado 'FABRICACION DE HORMIGONES PAZ DEL BARRIO,S.L.', obtenido 'HORMIGONES PAZ DEL BARRIO'
- MOR-002/gemini · FALLO · IA1.lineas[1].caso_id: esperado 'MOR-002', obtenido None
- MOR-002/gemini · AVISO · IA1.lineas[1].comentario: esperado 'La partida ha puesto 14.01.02.02, cuando es P4.01.02.02. partida debe buscar en lista de partidas de la obra', obtenido None
- MOR-002/gemini · AVISO · IA1.lineas[1].descripcion_esperada: esperado 'MORTERO 7,5 - 48H', obtenido 'M-7,5/B/04 48H BLANDA'
- MOR-002/gemini · FALLO · IA1.lineas[1].unidad: esperado 'M3', obtenido None
- MOR-002/gemini · FALLO · IA1.lineas[2]: esperado {'cantidad': 3, 'caso_id': 'MOR-002', 'codigo_imputacion': '@@NO_COMPARAR@@', 'comentario': 'La partida ha puesto 14.01.02.02, cuando es P4.01.02.02. partida debe buscar en lista de partidas de la obra. No ha creado esta linea. Sin embargo hay una casilla claramente donde dice carga incompleta 3. los morteross tambien tienen carga incompleta como los hormigones, añadir a la tipologia', 'descripcion_esperada': 'CARGAS INCOMPLETAS', 'descuentos': None, 'importe': None, 'num_linea': 2, 'precio_unitario': None, 'unidad': 'M3'}, obtenido None (fila del ground truth que el sistema no ha producido)
- MOR-003/gemini · FALLO · IA1.cabeceras[].caso_id: esperado 'MOR-003', obtenido None
- MOR-003/gemini · AVISO · IA1.cabeceras[].comentario: esperado 'partida en blanco es almacen | partida en blanco es almacen. En mortero tambien hay carga incompleta.en hormigon lo pilla bien , aquí en mortero lo mismo (copiar regla desde hormigon sin inventar)', obtenido None
- MOR-003/gemini · FALLO · IA1.cabeceras[].fichero_albaran: esperado 'MOR-003.pdf', obtenido None
- MOR-003/gemini · FALLO · IA1.lineas[1].caso_id: esperado 'MOR-003', obtenido None
- MOR-003/gemini · AVISO · IA1.lineas[1].comentario: esperado 'partida en blanco es almacen', obtenido None
- MOR-003/gemini · AVISO · IA1.lineas[1].descripcion_esperada: esperado 'MD-200 (M-5) / 48 H.', obtenido 'MD-200/2/36H'
- MOR-003/gemini · FALLO · IA1.lineas[1].unidad: esperado 'M3', obtenido None
- MOR-003/gemini · FALLO · IA1.lineas[2]: esperado {'cantidad': 2, 'caso_id': 'MOR-003', 'codigo_imputacion': '@@NO_COMPARAR@@', 'comentario': 'partida en blanco es almacen. En mortero tambien hay carga incompleta.en hormigon lo pilla bien , aquí en mortero lo mismo (copiar regla desde hormigon sin inventar)', 'descripcion_esperada': 'MD-200 (M-5) / 48 H. CARGA INCOMPLETA', 'descuentos': None, 'importe': None, 'num_linea': 2, 'precio_unitario': None, 'unidad': 'M3'}, obtenido None (fila del ground truth que el sistema no ha producido)
- MOR-004/gemini · FALLO · IA1.cabeceras[].caso_id: esperado 'MOR-004', obtenido None
- MOR-004/gemini · AVISO · IA1.cabeceras[].comentario: esperado 'partida mal, ha cogido 00.03.01. importe viene de oferta. Añadir | no se porque hay que meter esta linea, revisar negocio | incrementos por año en morteros hay que meterlo', obtenido None
- MOR-004/gemini · FALLO · IA1.cabeceras[].fichero_albaran: esperado 'MOR-004.pdf', obtenido None
- MOR-004/gemini · FALLO · IA1.lineas[1].caso_id: esperado 'MOR-004', obtenido None
- MOR-004/gemini · AVISO · IA1.lineas[1].comentario: esperado 'partida mal, ha cogido 00.03.01. importe viene de oferta. Añadir', obtenido None
- MOR-004/gemini · AVISO · IA1.lineas[1].descripcion_esperada: esperado 'D-300/B/5/I', obtenido 'D-300/B/5/1 AUTONIVELANTE'
- MOR-004/gemini · FALLO · IA1.lineas[1].unidad: esperado 'M3', obtenido None
- MOR-004/gemini · FALLO · IA1.lineas[2]: esperado {'cantidad': 9, 'caso_id': 'MOR-004', 'codigo_imputacion': '@@NO_COMPARAR@@', 'comentario': 'no se porque hay que meter esta linea, revisar negocio', 'descripcion_esperada': 'INCREM. FIBRAS POLIPROPILENO', 'descuentos': None, 'importe': None, 'num_linea': 2, 'precio_unitario': None, 'unidad': 'M3'}, obtenido None (fila del ground truth que el sistema no ha producido)
- RES-001/gemini · FALLO · IA1.cabeceras[].caso_id: esperado 'RES-001', obtenido None
- RES-001/gemini · AVISO · IA1.cabeceras[].comentario: esperado 'No hay codigo de obra en albaran, no ha cogido ninguna', obtenido None
- RES-001/gemini · FALLO · IA1.cabeceras[].fichero_albaran: esperado 'RES-001.pdf', obtenido None
- RES-001/gemini · FALLO · IA1.lineas[1].cantidad: esperado 1, obtenido 6.0
- RES-001/gemini · FALLO · IA1.lineas[1].caso_id: esperado 'RES-001', obtenido None
- RES-001/gemini · AVISO · IA1.lineas[1].comentario: esperado 'No hay codigo de obra en albaran, no ha cogido ninguna', obtenido None
- RES-001/gemini · AVISO · IA1.lineas[1].descripcion_esperada: esperado 'CAMBIO CONTENEDOR 6M3', obtenido 'Madera'
- RES-001/gemini · FALLO · IA1.lineas[1].unidad: esperado 'UD', obtenido None
- RES-002/gemini · FALLO · IA1.cabeceras[].caso_id: esperado 'RES-002', obtenido None
- RES-002/gemini · AVISO · IA1.cabeceras[].comentario: esperado 'No hay codigo de obra en albaran, no ha cogido ninguna', obtenido None
- RES-002/gemini · FALLO · IA1.cabeceras[].fichero_albaran: esperado 'RES-002.pdf', obtenido None
- RES-002/gemini · FALLO · IA1.lineas[1].cantidad: esperado 1, obtenido 6.0
- RES-002/gemini · FALLO · IA1.lineas[1].caso_id: esperado 'RES-002', obtenido None
- RES-002/gemini · AVISO · IA1.lineas[1].comentario: esperado 'No hay codigo de obra en albaran, no ha cogido ninguna', obtenido None
- RES-002/gemini · AVISO · IA1.lineas[1].descripcion_esperada: esperado 'CAMBIO CONTENEDOR 6M3', obtenido 'Horm_Ladr_Cerám. (LER 17 01 07)'
- RES-002/gemini · FALLO · IA1.lineas[1].unidad: esperado 'UD', obtenido None
- RES-003/gemini · FALLO · IA1.cabeceras[].caso_id: esperado 'RES-003', obtenido None
- RES-003/gemini · AVISO · IA1.cabeceras[].comentario: esperado 'No hay codigo de obra en albaran, no ha cogido ninguna', obtenido None
- RES-003/gemini · FALLO · IA1.cabeceras[].fichero_albaran: esperado 'RES-003.pdf', obtenido None
- RES-003/gemini · FALLO · IA1.cabeceras[].numero_albaran: esperado 'SS-0000589', obtenido 'SS-0080589'
- RES-003/gemini · FALLO · IA1.lineas[1].cantidad: esperado 1, obtenido 6.0
- RES-003/gemini · FALLO · IA1.lineas[1].caso_id: esperado 'RES-003', obtenido None
- RES-003/gemini · AVISO · IA1.lineas[1].comentario: esperado 'No hay codigo de obra en albaran, no ha cogido ninguna', obtenido None
- RES-003/gemini · AVISO · IA1.lineas[1].descripcion_esperada: esperado 'CAMBIO CONTENEDOR 6M3', obtenido '17 08 02 Mat. Yeso'
- RES-003/gemini · FALLO · IA1.lineas[1].unidad: esperado 'UD', obtenido None
- RES-003/gemini · FALLO · IA1.lineas[2]: esperado {'cantidad': 1, 'caso_id': 'RES-003', 'codigo_imputacion': '@@NO_COMPARAR@@', 'comentario': 'No hay codigo de obra en albaran, no ha cogido ninguna', 'descripcion_esperada': 'INCREMENTO LER 170802 MAT. DE CONST. A PARTIR DE YESOS-E', 'descuentos': None, 'importe': None, 'num_linea': 2, 'precio_unitario': None, 'unidad': 'UD'}, obtenido None (fila del ground truth que el sistema no ha producido)
- RES-004/gemini · FALLO · IA1.cabeceras[].caso_id: esperado 'RES-004', obtenido None
- RES-004/gemini · AVISO · IA1.cabeceras[].comentario: esperado 'No hay codigo de obra en albaran, no ha cogido ninguna', obtenido None
- RES-004/gemini · FALLO · IA1.cabeceras[].fichero_albaran: esperado 'RES-004.pdf', obtenido None
- RES-004/gemini · FALLO · IA1.lineas[1].cantidad: esperado 1, obtenido 6.0
- RES-004/gemini · FALLO · IA1.lineas[1].caso_id: esperado 'RES-004', obtenido None
- RES-004/gemini · AVISO · IA1.lineas[1].comentario: esperado 'No hay codigo de obra en albaran, no ha cogido ninguna', obtenido None
- RES-004/gemini · AVISO · IA1.lineas[1].descripcion_esperada: esperado 'CAMBIO CONTENEDOR 6M3', obtenido 'Mat. Aislamiento (LER 17 06 04)'
- RES-004/gemini · FALLO · IA1.lineas[1].unidad: esperado 'UD', obtenido None
- RES-004/gemini · FALLO · IA1.lineas[2]: esperado {'cantidad': 1, 'caso_id': 'RES-004', 'codigo_imputacion': '@@NO_COMPARAR@@', 'comentario': None, 'descripcion_esperada': 'INCREMENTO LER 170604 MATERIALES DE AISLAMIENTO-E', 'descuentos': None, 'importe': None, 'num_linea': 2, 'precio_unitario': None, 'unidad': 'UD'}, obtenido None (fila del ground truth que el sistema no ha producido)
- RES-005/gemini · FALLO · IA1.cabeceras[].caso_id: esperado 'RES-005', obtenido None
- RES-005/gemini · AVISO · IA1.cabeceras[].comentario: esperado 'No hay codigo de obra en albaran, no ha cogido ninguna', obtenido None
- RES-005/gemini · FALLO · IA1.cabeceras[].fichero_albaran: esperado 'RES-005.pdf', obtenido None
- RES-005/gemini · FALLO · IA1.lineas[1].cantidad: esperado 1, obtenido 6.0
- RES-005/gemini · FALLO · IA1.lineas[1].caso_id: esperado 'RES-005', obtenido None
- RES-005/gemini · AVISO · IA1.lineas[1].comentario: esperado 'No hay codigo de obra en albaran, no ha cogido ninguna', obtenido None
- RES-005/gemini · AVISO · IA1.lineas[1].descripcion_esperada: esperado 'CAMBIO CONTENEDOR 6M3', obtenido 'Mat. Aislamiento (LER 170604)'
- RES-005/gemini · FALLO · IA1.lineas[1].unidad: esperado 'UD', obtenido None
- RES-005/gemini · FALLO · IA1.lineas[2]: esperado {'cantidad': 1, 'caso_id': 'RES-005', 'codigo_imputacion': '@@NO_COMPARAR@@', 'comentario': 'No hay codigo de obra en albaran, no ha cogido ninguna', 'descripcion_esperada': 'INCREMENTO LER 170604 MATERIALES DE AISLAMIENTO-E', 'descuentos': None, 'importe': None, 'num_linea': 2, 'precio_unitario': None, 'unidad': 'UD'}, obtenido None (fila del ground truth que el sistema no ha producido)
- RES-006/gemini · FALLO · IA1.cabeceras[].caso_id: esperado 'RES-006', obtenido None
- RES-006/gemini · AVISO · IA1.cabeceras[].comentario: esperado 'hay que guardar el codigo ler en bbdd, lo ha hecho? En codigo existente no sale, y no hay columna de LER en la vista detallada.', obtenido None
- RES-006/gemini · FALLO · IA1.cabeceras[].fichero_albaran: esperado 'RES-006.pdf', obtenido None
- RES-006/gemini · FALLO · IA1.lineas[1].cantidad: esperado 1, obtenido 6.0
- RES-006/gemini · FALLO · IA1.lineas[1].caso_id: esperado 'RES-006', obtenido None
- RES-006/gemini · AVISO · IA1.lineas[1].comentario: esperado 'hay que guardar el codigo ler en bbdd, lo ha hecho? En codigo existente no sale, y no hay columna de LER en la vista detallada.', obtenido None
- RES-006/gemini · AVISO · IA1.lineas[1].descripcion_esperada: esperado 'CONTENEDOR DE RESIDUOS 6 M3', obtenido 'Mat. Mezclados'
- RES-006/gemini · FALLO · IA1.lineas[1].unidad: esperado 'UD', obtenido None
- RES-007/gemini · FALLO · IA1.cabeceras[].caso_id: esperado 'RES-007', obtenido None
- RES-007/gemini · AVISO · IA1.cabeceras[].comentario: esperado 'leido mal la obra (no sale en albaran, la habra cogido po rdireccion, ver como lo ha hecho). Coge mal el CIF proveedor (no encuentro de donde lo ha sacado, en la obra si que estra salmedina). Podriamos hacer que proveedores ya identificados claramente, como salmedina, al leer el nombre ya coja todo?. estudiar como ha llegado a la info que ha recogido. no ha encontrado contrato porque no hay en la obra que eligio (que estaba mal)\nNo ha metido el precio unitario del incremento LER | leido mal la obra (no sale en albaran, la habra cogido po rdireccion, ver como lo ha hecho). Coge mal el CIF proveedor (no encuentro de donde lo ha sacado, en la obra si que estra salmedina). Podriamos hacer que proveedores ya identificados claramente, como salmedina, al leer el nombre ya coja todo?. estudiar como ha llegado a la info que ha recogido. no ha encontrado contrato porque no hay en la obra que eligio (que estaba mal)', obtenido None
- RES-007/gemini · FALLO · IA1.cabeceras[].fichero_albaran: esperado 'RES-007.pdf', obtenido None
- RES-007/gemini · FALLO · IA1.lineas[1].cantidad: esperado 1, obtenido 9.0
- RES-007/gemini · FALLO · IA1.lineas[1].caso_id: esperado 'RES-007', obtenido None
- RES-007/gemini · AVISO · IA1.lineas[1].comentario: esperado 'leido mal la obra (no sale en albaran, la habra cogido po rdireccion, ver como lo ha hecho). Coge mal el CIF proveedor (no encuentro de donde lo ha sacado, en la obra si que estra salmedina). Podriamos hacer que proveedores ya identificados claramente, como salmedina, al leer el nombre ya coja todo?. estudiar como ha llegado a la info que ha recogido. no ha encontrado contrato porque no hay en la obra que eligio (que estaba mal)\nNo ha metido el precio unitario del incremento LER', obtenido None
- RES-007/gemini · AVISO · IA1.lineas[1].descripcion_esperada: esperado 'CONTENEDOR DE RESIDUOS 9 M3', obtenido 'Mat. Yeso'
- RES-007/gemini · FALLO · IA1.lineas[1].unidad: esperado 'UD', obtenido None
- RES-007/gemini · FALLO · IA1.lineas[2]: esperado {'cantidad': 1, 'caso_id': 'RES-007', 'codigo_imputacion': '@@NO_COMPARAR@@', 'comentario': 'leido mal la obra (no sale en albaran, la habra cogido po rdireccion, ver como lo ha hecho). Coge mal el CIF proveedor (no encuentro de donde lo ha sacado, en la obra si que estra salmedina). Podriamos hacer que proveedores ya identificados claramente, como salmedina, al leer el nombre ya coja todo?. estudiar como ha llegado a la info que ha recogido. no ha encontrado contrato porque no hay en la obra que eligio (que estaba mal)', 'descripcion_esperada': 'INCREMENTO LEER 17 08 02', 'descuentos': None, 'importe': None, 'num_linea': 2, 'precio_unitario': None, 'unidad': 'UD'}, obtenido None (fila del ground truth que el sistema no ha producido)
- RES-008/gemini · FALLO · IA1.cabeceras[].caso_id: esperado 'RES-008', obtenido None
- RES-008/gemini · AVISO · IA1.cabeceras[].comentario: esperado 'la partida esta mal, era 32.01, en lugar de 04.52.01 (si bien es cierto que esta cortado el numero). El ler no viene en el contrato, asi que aunque haya cogido el generico deberia buscar en la oferta', obtenido None
- RES-008/gemini · FALLO · IA1.cabeceras[].fecha: esperado '2026-03-10', obtenido '2024-03-10'
- RES-008/gemini · FALLO · IA1.cabeceras[].fichero_albaran: esperado 'RES-008.pdf', obtenido None
- RES-008/gemini · FALLO · IA1.lineas[1].cantidad: esperado 1, obtenido 6.0
- RES-008/gemini · FALLO · IA1.lineas[1].caso_id: esperado 'RES-008', obtenido None
- RES-008/gemini · AVISO · IA1.lineas[1].comentario: esperado 'la partida esta mal, era 32.01, en lugar de 04.52.01 (si bien es cierto que esta cortado el numero). El ler no viene en el contrato, asi que aunque haya cogido el generico deberia buscar en la oferta', obtenido None
- RES-008/gemini · AVISO · IA1.lineas[1].descripcion_esperada: esperado 'MOVIMIENTO DE CONTENEDOR DE 6 M CÚBICOS PLASTICO', obtenido 'PLASTICO'
- RES-008/gemini · FALLO · IA1.lineas[1].unidad: esperado 'UD', obtenido None
- RES-009/gemini · FALLO · IA1.cabeceras[].caso_id: esperado 'RES-009', obtenido None
- RES-009/gemini · AVISO · IA1.cabeceras[].comentario: esperado 'numero de albraran incorrecto. Ha cogido 09478. la obra no venaia y ha deducido una incorrecta. Si tiene match de proveedor solo deberia intentar deducir entre las que tienen dicho porveedor en la obra | el precio por incremento por año tambien hay que meterlo en residuos. No lo ha cogido. Si no esta en contrato deducir de la oferta', obtenido None
- RES-009/gemini · FALLO · IA1.cabeceras[].fecha: esperado '2026-03-13', obtenido '2026-01-15'
- RES-009/gemini · FALLO · IA1.cabeceras[].fichero_albaran: esperado 'RES-009.pdf', obtenido None
- RES-009/gemini · FALLO · IA1.lineas[1].cantidad: esperado 1, obtenido 6.0
- RES-009/gemini · FALLO · IA1.lineas[1].caso_id: esperado 'RES-009', obtenido None
- RES-009/gemini · AVISO · IA1.lineas[1].comentario: esperado 'numero de albraran incorrecto. Ha cogido 09478. la obra no venaia y ha deducido una incorrecta. Si tiene match de proveedor solo deberia intentar deducir entre las que tienen dicho porveedor en la obra', obtenido None
- RES-009/gemini · AVISO · IA1.lineas[1].descripcion_esperada: esperado 'MOVIMIENTO DE CONTENEDOR DE 6 M CÚBICOS MEZCLA OTROS RESIDUOS', obtenido 'Residuos mezclados de construcción y demolición que no contienen sustancias peligrosas.'
- RES-009/gemini · FALLO · IA1.lineas[1].unidad: esperado 'UD', obtenido None
- RES-010/gemini · FALLO · IA1.cabeceras[].caso_id: esperado 'RES-010', obtenido None
- RES-010/gemini · AVISO · IA1.cabeceras[].comentario: esperado 'en general, el incremento por leer si no viene leer en el contrato se deduce de canon qe es lo mismo usando el ler. La cantidad es peso en tn, si es menor que 1, pones 1.  hay que añadir incremento por año', obtenido None
- RES-010/gemini · FALLO · IA1.cabeceras[].fichero_albaran: esperado 'RES-010.png', obtenido None
- RES-010/gemini · FALLO · IA1.cabeceras[].proveedor_nombre: esperado 'CARGA Y TRANSPORTE DE CUBAS, S.L.', obtenido 'CARGA Y TRANSPORTE DE CUBAS SL'
- RES-010/gemini · FALLO · IA1.lineas[1].cantidad: esperado 1, obtenido 3000.0
- RES-010/gemini · FALLO · IA1.lineas[1].caso_id: esperado 'RES-010', obtenido None
- RES-010/gemini · AVISO · IA1.lineas[1].descripcion_esperada: esperado 'CONTENEDOR DE 8M3', obtenido 'MEZCLADO (CUBA 1941 - 8 M3)'
- RES-010/gemini · FALLO · IA1.lineas[1].unidad: esperado 'UD', obtenido None
- RES-010/gemini · FALLO · IA1.lineas[2]: esperado {'cantidad': 3, 'caso_id': 'RES-010', 'codigo_imputacion': '@@NO_COMPARAR@@', 'comentario': 'en general, el incremento por leer si no viene leer en el contrato se deduce de canon qe es lo mismo usando el ler. La cantidad es peso en tn, si es menor que 1, pones 1.  hay que añadir incremento por año', 'descripcion_esperada': 'RCDS. SUCIOS', 'descuentos': None, 'importe': None, 'num_linea': 2, 'precio_unitario': None, 'unidad': 'M3'}, obtenido None (fila del ground truth que el sistema no ha producido)
- RES-011/gemini · FALLO · IA1.cabeceras[].caso_id: esperado 'RES-011', obtenido None
- RES-011/gemini · AVISO · IA1.cabeceras[].comentario: esperado 'en general, el incremento por leer si no viene leer en el contrato se deduce de canon qe es lo mismo usando el ler. La cantidad es peso en tn, si es menor que 1, pones 1.  hay que añadir incremento por año', obtenido None
- RES-011/gemini · FALLO · IA1.cabeceras[].fichero_albaran: esperado 'RES-011.png', obtenido None
- RES-011/gemini · FALLO · IA1.cabeceras[].proveedor_nombre: esperado 'CARGA Y TRANSPORTE DE CUBAS, S.L.', obtenido 'CARGA Y TRANSPORTE DE CUBAS SL'
- RES-011/gemini · FALLO · IA1.lineas[1].cantidad: esperado 1, obtenido 8.0
- RES-011/gemini · FALLO · IA1.lineas[1].caso_id: esperado 'RES-011', obtenido None
- RES-011/gemini · AVISO · IA1.lineas[1].descripcion_esperada: esperado 'CONTENEDOR DE 8M3', obtenido 'Mezclado Cuba 1950 Cod LER 170107 (3280 kg)'
- RES-011/gemini · FALLO · IA1.lineas[1].unidad: esperado 'UD', obtenido None
- RES-011/gemini · FALLO · IA1.lineas[2]: esperado {'cantidad': 3.28, 'caso_id': 'RES-011', 'codigo_imputacion': '@@NO_COMPARAR@@', 'comentario': 'en general, el incremento por leer si no viene leer en el contrato se deduce de canon qe es lo mismo usando el ler. La cantidad es peso en tn, si es menor que 1, pones 1.  hay que añadir incremento por año', 'descripcion_esperada': 'RCDS. SUCIOS', 'descuentos': None, 'importe': None, 'num_linea': 2, 'precio_unitario': None, 'unidad': 'M3'}, obtenido None (fila del ground truth que el sistema no ha producido)
- RES-012/gemini · FALLO · IA1.cabeceras[].caso_id: esperado 'RES-012', obtenido None
- RES-012/gemini · AVISO · IA1.cabeceras[].comentario: esperado 'en general, el incremento por leer si no viene leer en el contrato se deduce de canon qe es lo mismo usando el ler. La cantidad es peso en tn, si es menor que 1, pones 1.  hay que añadir incremento por año', obtenido None
- RES-012/gemini · FALLO · IA1.cabeceras[].fichero_albaran: esperado 'RES-012.png', obtenido None
- RES-012/gemini · FALLO · IA1.cabeceras[].proveedor_nombre: esperado 'CARGA Y TRANSPORTE DE CUBAS, S.L.', obtenido 'CARGA Y TRANSPORTE DE CUBAS SL'
- RES-012/gemini · FALLO · IA1.lineas[1].cantidad: esperado 1, obtenido 2380.0
- RES-012/gemini · FALLO · IA1.lineas[1].caso_id: esperado 'RES-012', obtenido None
- RES-012/gemini · AVISO · IA1.lineas[1].descripcion_esperada: esperado 'CONTENEDOR DE 8M3', obtenido 'RESIDUO VOLUMINOSOS - Nº CUBA 1935 - 8 M3 (LER 200307)'
- RES-012/gemini · FALLO · IA1.lineas[1].unidad: esperado 'UD', obtenido None
- RES-012/gemini · FALLO · IA1.lineas[2]: esperado {'cantidad': 2.38, 'caso_id': 'RES-012', 'codigo_imputacion': '@@NO_COMPARAR@@', 'comentario': 'en general, el incremento por leer si no viene leer en el contrato se deduce de canon qe es lo mismo usando el ler. La cantidad es peso en tn, si es menor que 1, pones 1.  hay que añadir incremento por año', 'descripcion_esperada': 'RCDS. VOLUMINOSOS', 'descuentos': None, 'importe': None, 'num_linea': 2, 'precio_unitario': None, 'unidad': 'M3'}, obtenido None (fila del ground truth que el sistema no ha producido)
- RES-013/gemini · FALLO · IA1.cabeceras[].caso_id: esperado 'RES-013', obtenido None
- RES-013/gemini · AVISO · IA1.cabeceras[].comentario: esperado 'en general, el incremento por leer si no viene leer en el contrato se deduce de canon qe es lo mismo usando el ler. La cantidad es peso en tn, si es menor que 1, pones 1.  hay que añadir incremento por año', obtenido None
- RES-013/gemini · FALLO · IA1.cabeceras[].fichero_albaran: esperado 'RES-013.png', obtenido None
- RES-013/gemini · FALLO · IA1.cabeceras[].proveedor_nombre: esperado 'CARGA Y TRANSPORTE DE CUBAS, S.L.', obtenido 'CARGA Y TRANSPORTE DE CUBAS SL'
- RES-013/gemini · FALLO · IA1.lineas[1].cantidad: esperado 1, obtenido 1720.0
- RES-013/gemini · FALLO · IA1.lineas[1].caso_id: esperado 'RES-013', obtenido None
- RES-013/gemini · AVISO · IA1.lineas[1].descripcion_esperada: esperado 'CONTENEDOR DE 8M3', obtenido 'VOLUMEN - CUBA 1441'
- RES-013/gemini · FALLO · IA1.lineas[1].unidad: esperado 'UD', obtenido None
- RES-013/gemini · FALLO · IA1.lineas[2]: esperado {'cantidad': 1.72, 'caso_id': 'RES-013', 'codigo_imputacion': '@@NO_COMPARAR@@', 'comentario': 'en general, el incremento por leer si no viene leer en el contrato se deduce de canon qe es lo mismo usando el ler. La cantidad es peso en tn, si es menor que 1, pones 1.  hay que añadir incremento por año', 'descripcion_esperada': 'RCDS. VOLUMINOSOS', 'descuentos': None, 'importe': None, 'num_linea': 2, 'precio_unitario': None, 'unidad': 'M3'}, obtenido None (fila del ground truth que el sistema no ha producido)
- RES-014/gemini · FALLO · IA1.cabeceras[].caso_id: esperado 'RES-014', obtenido None
- RES-014/gemini · AVISO · IA1.cabeceras[].comentario: esperado 'en general, el incremento por leer si no viene leer en el contrato se deduce de canon qe es lo mismo usando el ler. La cantidad es peso en tn, si es menor que 1, pones 1.  hay que añadir incremento por año', obtenido None
- RES-014/gemini · FALLO · IA1.cabeceras[].fichero_albaran: esperado 'RES-014.png', obtenido None
- RES-014/gemini · FALLO · IA1.cabeceras[].proveedor_nombre: esperado 'CARGA Y TRANSPORTE DE CUBAS, S.L.', obtenido 'CARGA Y TRANSPORTE DE CUBAS SL'
- RES-014/gemini · FALLO · IA1.lineas[1].cantidad: esperado 1, obtenido 6100.0
- RES-014/gemini · FALLO · IA1.lineas[1].caso_id: esperado 'RES-014', obtenido None
- RES-014/gemini · AVISO · IA1.lineas[1].descripcion_esperada: esperado 'CONTENEDOR DE 8M3', obtenido 'MEZCLADO (LER 170904) - Cuba 1962 (8 m3)'
- RES-014/gemini · FALLO · IA1.lineas[1].unidad: esperado 'UD', obtenido None
- RES-014/gemini · FALLO · IA1.lineas[2]: esperado {'cantidad': 6.1, 'caso_id': 'RES-014', 'codigo_imputacion': '@@NO_COMPARAR@@', 'comentario': 'en general, el incremento por leer si no viene leer en el contrato se deduce de canon qe es lo mismo usando el ler. La cantidad es peso en tn, si es menor que 1, pones 1.  hay que añadir incremento por año', 'descripcion_esperada': 'RCDS. SUCIOS', 'descuentos': None, 'importe': None, 'num_linea': 2, 'precio_unitario': None, 'unidad': 'M3'}, obtenido None (fila del ground truth que el sistema no ha producido)
- RES-015/gemini · FALLO · IA1.cabeceras[].caso_id: esperado 'RES-015', obtenido None
- RES-015/gemini · AVISO · IA1.cabeceras[].comentario: esperado 'en general, el incremento por leer si no viene leer en el contrato se deduce de canon qe es lo mismo usando el ler. La cantidad es peso en tn, si es menor que 1, pones 1.  hay que añadir incremento por año', obtenido None
- RES-015/gemini · FALLO · IA1.cabeceras[].fichero_albaran: esperado 'RES-015.png', obtenido None
- RES-015/gemini · FALLO · IA1.cabeceras[].proveedor_nombre: esperado 'CARGA Y TRANSPORTE DE CUBAS, S.L.', obtenido 'CARGA Y TRANSPORTE DE CUBAS SL'
- RES-015/gemini · FALLO · IA1.lineas[1].cantidad: esperado 1, obtenido 4000.0
- RES-015/gemini · FALLO · IA1.lineas[1].caso_id: esperado 'RES-015', obtenido None
- RES-015/gemini · AVISO · IA1.lineas[1].descripcion_esperada: esperado 'CONTENEDOR DE 8M3', obtenido 'MEZCLADO R12/R23'
- RES-015/gemini · FALLO · IA1.lineas[1].unidad: esperado 'UD', obtenido None
- RES-015/gemini · FALLO · IA1.lineas[2]: esperado {'cantidad': 4, 'caso_id': 'RES-015', 'codigo_imputacion': '@@NO_COMPARAR@@', 'comentario': 'en general, el incremento por leer si no viene leer en el contrato se deduce de canon qe es lo mismo usando el ler. La cantidad es peso en tn, si es menor que 1, pones 1.  hay que añadir incremento por año', 'descripcion_esperada': 'RCDS. SUCIOS', 'descuentos': None, 'importe': None, 'num_linea': 2, 'precio_unitario': None, 'unidad': 'M3'}, obtenido None (fila del ground truth que el sistema no ha producido)
- RES-016/gemini · FALLO · IA1.cabeceras[].caso_id: esperado 'RES-016', obtenido None
- RES-016/gemini · AVISO · IA1.cabeceras[].comentario: esperado 'como se que es para llevar? Por que no viene LER?', obtenido None
- RES-016/gemini · FALLO · IA1.cabeceras[].fichero_albaran: esperado 'RES-016.png', obtenido None
- RES-016/gemini · FALLO · IA1.cabeceras[].proveedor_nombre: esperado 'CARGA Y TRANSPORTE DE CUBAS, S.L.', obtenido 'CARGA Y TRANSPORTE DE CUBAS SL'
- RES-016/gemini · FALLO · IA1.lineas[1].cantidad: esperado 1, obtenido 8.0
- RES-016/gemini · FALLO · IA1.lineas[1].caso_id: esperado 'RES-016', obtenido None
- RES-016/gemini · AVISO · IA1.lineas[1].comentario: esperado 'como se que es para llevar? Por que no viene LER?', obtenido None
- RES-016/gemini · AVISO · IA1.lineas[1].descripcion_esperada: esperado 'CONTENEDOR DE 8M3. LLEVAR. NO SE FACTURA', obtenido 'Porte LL - Cuba 1970 - recovan largo'
- RES-016/gemini · FALLO · IA1.lineas[1].unidad: esperado 'UD', obtenido None
- RES-017/gemini · FALLO · IA1.cabeceras[].caso_id: esperado 'RES-017', obtenido None
- RES-017/gemini · AVISO · IA1.cabeceras[].comentario: esperado 'como se que debo aplicarle el canon de voluminosos? La cantidad es el peso en toneladas, solo ocurre en este proveedor?  Como se como se mide eso? Viene en contrato?', obtenido None
- RES-017/gemini · FALLO · IA1.cabeceras[].fichero_albaran: esperado 'RES-017.png', obtenido None
- RES-017/gemini · FALLO · IA1.cabeceras[].proveedor_nombre: esperado 'CARGA Y TRANSPORTE DE CUBAS, S.L.', obtenido 'CARGA Y TRANSPORTE DE CUBAS SL'
- RES-017/gemini · FALLO · IA1.lineas[1].cantidad: esperado 1, obtenido 2160.0
- RES-017/gemini · FALLO · IA1.lineas[1].caso_id: esperado 'RES-017', obtenido None
- RES-017/gemini · AVISO · IA1.lineas[1].descripcion_esperada: esperado 'CONTENEDOR DE 8M3', obtenido 'RESIDUOS LER 170904 CUBA 1940 RES. BIDA PONSIRAD'
- RES-017/gemini · FALLO · IA1.lineas[1].unidad: esperado 'UD', obtenido None
- RES-017/gemini · FALLO · IA1.lineas[2]: esperado {'cantidad': 2.16, 'caso_id': 'RES-017', 'codigo_imputacion': '@@NO_COMPARAR@@', 'comentario': 'como se que debo aplicarle el canon de voluminosos? La cantidad es el peso en toneladas, solo ocurre en este proveedor?  Como se como se mide eso? Viene en contrato?', 'descripcion_esperada': 'RCDS. VOLUMINOSOS', 'descuentos': None, 'importe': None, 'num_linea': 2, 'precio_unitario': None, 'unidad': 'M3'}, obtenido None (fila del ground truth que el sistema no ha producido)
- RES-018/gemini · FALLO · IA1.cabeceras[].caso_id: esperado 'RES-018', obtenido None
- RES-018/gemini · AVISO · IA1.cabeceras[].comentario: esperado 'La cantidad es el peso en toneladas, solo ocurre en este proveedor?  Como se como se mide eso? Viene en contrato? | porque solo este tiene el incremento por año? Y los demas?', obtenido None
- RES-018/gemini · FALLO · IA1.cabeceras[].fichero_albaran: esperado 'RES-018.png', obtenido None
- RES-018/gemini · FALLO · IA1.cabeceras[].proveedor_nombre: esperado 'CARGA Y TRANSPORTE DE CUBAS, S.L.', obtenido 'CARGA Y TRANSPORTE DE CUBAS SL'
- RES-018/gemini · FALLO · IA1.lineas[1].cantidad: esperado 1, obtenido 5400.0
- RES-018/gemini · FALLO · IA1.lineas[1].caso_id: esperado 'RES-018', obtenido None
- RES-018/gemini · AVISO · IA1.lineas[1].descripcion_esperada: esperado 'CONTENEDOR DE 8M3', obtenido 'SUCIO - Cod LER 170904 (Nº Cuba: 1952)'
- RES-018/gemini · FALLO · IA1.lineas[1].unidad: esperado 'UD', obtenido None
- RES-018/gemini · FALLO · IA1.lineas[2]: esperado {'cantidad': 5.4, 'caso_id': 'RES-018', 'codigo_imputacion': '@@NO_COMPARAR@@', 'comentario': 'La cantidad es el peso en toneladas, solo ocurre en este proveedor?  Como se como se mide eso? Viene en contrato?', 'descripcion_esperada': 'RCDS. SUCIOS', 'descuentos': None, 'importe': None, 'num_linea': 2, 'precio_unitario': None, 'unidad': 'M3'}, obtenido None (fila del ground truth que el sistema no ha producido)
- RES-019/gemini · FALLO · IA1.cabeceras[].caso_id: esperado 'RES-019', obtenido None
- RES-019/gemini · AVISO · IA1.cabeceras[].comentario: esperado 'de donde sale que el unitario es 10?', obtenido None
- RES-019/gemini · FALLO · IA1.cabeceras[].fecha: esperado '2025-07-28', obtenido '2023-08-07'
- RES-019/gemini · FALLO · IA1.cabeceras[].fichero_albaran: esperado 'RES-019.png', obtenido None
- RES-019/gemini · FALLO · IA1.cabeceras[].proveedor_nombre: esperado 'CARGA Y TRANSPORTE DE CUBAS, S.L.', obtenido 'CARGA Y TRANSPORTE DE CUBAS SL'
- RES-019/gemini · FALLO · IA1.lineas[1].cantidad: esperado 1, obtenido 8.0
- RES-019/gemini · FALLO · IA1.lineas[1].caso_id: esperado 'RES-019', obtenido None
- RES-019/gemini · AVISO · IA1.lineas[1].descripcion_esperada: esperado 'CONTENEDOR DE 8M3', obtenido 'MADERA'
- RES-019/gemini · FALLO · IA1.lineas[1].unidad: esperado 'UD', obtenido None
- RES-019/gemini · FALLO · IA1.lineas[2]: esperado {'cantidad': 1, 'caso_id': 'RES-019', 'codigo_imputacion': '@@NO_COMPARAR@@', 'comentario': 'de donde sale que el unitario es 10?', 'descripcion_esperada': 'RCDS. MADERA LIMPIA', 'descuentos': None, 'importe': None, 'num_linea': 2, 'precio_unitario': None, 'unidad': 'M3'}, obtenido None (fila del ground truth que el sistema no ha producido)

## IA2 · contexto por tipología (sv2) — ROJO

- Casos evaluados: 9 · omitidos: 2
- Proveedores invocados: openai

| Caso | Estado | Fallos críticos | Avisos laxos | Motivo |
|---|---|---|---|---|
| RES-020 | OMITIDO | — | — | no existe el fichero del albarán de RES-020 |
| RES-021 | OMITIDO | — | — | no existe el fichero del albarán de RES-021 |
| RES-001/openai | ROJO | 3 | 7 | — |
| RES-002/openai | ROJO | 3 | 5 | — |
| RES-003/openai | ROJO | 4 | 5 | — |
| RES-004/openai | ROJO | 4 | 6 | — |
| RES-005/openai | ROJO | 4 | 5 | — |
| RES-006/openai | ROJO | 3 | 4 | — |
| RES-007/openai | ROJO | 4 | 5 | — |
| RES-008/openai | ROJO | 1 | 2 | — |
| RES-009/openai | ROJO | 1 | 3 | — |

Detalle campo a campo:

- RES-001/openai · FALLO · IA2.contexto[1/TIPO_FAMILIA].caso_id: esperado 'RES-001', obtenido None
- RES-001/openai · AVISO · IA2.contexto[1/TIPO_FAMILIA].comentario: esperado 'Familia de linea del catalogo unico: el documento es de gestion de residuos (RCD).', obtenido None
- RES-001/openai · FALLO · IA2.contexto[1/CODIGO_LER].caso_id: esperado 'RES-001', obtenido None
- RES-001/openai · AVISO · IA2.contexto[1/CODIGO_LER].comentario: esperado 'No hay codigo de obra en albaran, no ha cogido ninguna', obtenido None
- RES-001/openai · FALLO · IA2.contexto[1/VOLUMEN_M3].caso_id: esperado 'RES-001', obtenido None
- RES-001/openai · AVISO · IA2.contexto[1/VOLUMEN_M3].comentario: esperado 'El 6 manuscrito en la columna VOL. m3. Es la CAPACIDAD del contenedor (§8.1), no una cantidad de material.', obtenido None
- RES-001/openai · AVISO · IA2.contexto[+]: esperado None, obtenido {'num_linea': 1, 'campo_contexto': 'contenedores_entregados', 'valor_esperado': 1.0} (fila producida por el sistema que el ground truth no declara)
- RES-001/openai · AVISO · IA2.contexto[+]: esperado None, obtenido {'num_linea': 1, 'campo_contexto': 'contenedores_retirados', 'valor_esperado': 1.0} (fila producida por el sistema que el ground truth no declara)
- RES-001/openai · AVISO · IA2.contexto[+]: esperado None, obtenido {'num_linea': 1, 'campo_contexto': 'peso_toneladas', 'valor_esperado': 1.5} (fila producida por el sistema que el ground truth no declara)
- RES-001/openai · AVISO · IA2.contexto[+]: esperado None, obtenido {'num_linea': 1, 'campo_contexto': 'rol_linea', 'valor_esperado': 'base'} (fila producida por el sistema que el ground truth no declara)
- RES-002/openai · FALLO · IA2.contexto[1/TIPO_FAMILIA].caso_id: esperado 'RES-002', obtenido None
- RES-002/openai · AVISO · IA2.contexto[1/TIPO_FAMILIA].comentario: esperado 'Familia de linea del catalogo unico: el documento es de gestion de residuos (RCD).', obtenido None
- RES-002/openai · FALLO · IA2.contexto[1/CODIGO_LER].caso_id: esperado 'RES-002', obtenido None
- RES-002/openai · AVISO · IA2.contexto[1/CODIGO_LER].comentario: esperado 'No hay codigo de obra en albaran, no ha cogido ninguna', obtenido None
- RES-002/openai · FALLO · IA2.contexto[1/VOLUMEN_M3].caso_id: esperado 'RES-002', obtenido None
- RES-002/openai · AVISO · IA2.contexto[1/VOLUMEN_M3].comentario: esperado 'El 6 manuscrito en la columna VOL. m3. Es la CAPACIDAD del contenedor (§8.1), no una cantidad de material.', obtenido None
- RES-002/openai · AVISO · IA2.contexto[+]: esperado None, obtenido {'num_linea': 1, 'campo_contexto': 'peso_toneladas', 'valor_esperado': 0.81} (fila producida por el sistema que el ground truth no declara)
- RES-002/openai · AVISO · IA2.contexto[+]: esperado None, obtenido {'num_linea': 1, 'campo_contexto': 'rol_linea', 'valor_esperado': 'base'} (fila producida por el sistema que el ground truth no declara)
- RES-003/openai · FALLO · IA2.contexto[1/TIPO_FAMILIA].caso_id: esperado 'RES-003', obtenido None
- RES-003/openai · AVISO · IA2.contexto[1/TIPO_FAMILIA].comentario: esperado 'Familia de linea del catalogo unico: el documento es de gestion de residuos (RCD).', obtenido None
- RES-003/openai · FALLO · IA2.contexto[1/CODIGO_LER].caso_id: esperado 'RES-003', obtenido None
- RES-003/openai · AVISO · IA2.contexto[1/CODIGO_LER].comentario: esperado 'No hay codigo de obra en albaran, no ha cogido ninguna', obtenido None
- RES-003/openai · FALLO · IA2.contexto[1/VOLUMEN_M3].caso_id: esperado 'RES-003', obtenido None
- RES-003/openai · AVISO · IA2.contexto[1/VOLUMEN_M3].comentario: esperado 'El 6 manuscrito en la columna VOL. m3. Es la CAPACIDAD del contenedor (§8.1), no una cantidad de material.', obtenido None
- RES-003/openai · FALLO · IA2.contexto[2/CODIGO_LER]: esperado {'campo_contexto': 'codigo_ler', 'caso_id': 'RES-003', 'comentario': 'No hay codigo de obra en albaran, no ha cogido ninguna', 'num_linea': 2, 'valor_esperado': '170802'}, obtenido None (fila del ground truth que el sistema no ha producido)
- RES-003/openai · AVISO · IA2.contexto[+]: esperado None, obtenido {'num_linea': 1, 'campo_contexto': 'peso_toneladas', 'valor_esperado': 2.16} (fila producida por el sistema que el ground truth no declara)
- RES-003/openai · AVISO · IA2.contexto[+]: esperado None, obtenido {'num_linea': 1, 'campo_contexto': 'rol_linea', 'valor_esperado': 'base'} (fila producida por el sistema que el ground truth no declara)
- RES-004/openai · FALLO · IA2.contexto[1/TIPO_FAMILIA].caso_id: esperado 'RES-004', obtenido None
- RES-004/openai · AVISO · IA2.contexto[1/TIPO_FAMILIA].comentario: esperado 'Familia de linea del catalogo unico: el documento es de gestion de residuos (RCD).', obtenido None
- RES-004/openai · FALLO · IA2.contexto[1/CODIGO_LER].caso_id: esperado 'RES-004', obtenido None
- RES-004/openai · AVISO · IA2.contexto[1/CODIGO_LER].comentario: esperado 'No hay codigo de obra en albaran, no ha cogido ninguna', obtenido None
- RES-004/openai · FALLO · IA2.contexto[1/VOLUMEN_M3].caso_id: esperado 'RES-004', obtenido None
- RES-004/openai · AVISO · IA2.contexto[1/VOLUMEN_M3].comentario: esperado 'El 6 manuscrito en la columna VOL. m3. Es la CAPACIDAD del contenedor (§8.1), no una cantidad de material.', obtenido None
- RES-004/openai · FALLO · IA2.contexto[2/CODIGO_LER]: esperado {'campo_contexto': 'codigo_ler', 'caso_id': 'RES-004', 'comentario': None, 'num_linea': 2, 'valor_esperado': '170604'}, obtenido None (fila del ground truth que el sistema no ha producido)
- RES-004/openai · AVISO · IA2.contexto[+]: esperado None, obtenido {'num_linea': 1, 'campo_contexto': 'contenedores_entregados', 'valor_esperado': 1.0} (fila producida por el sistema que el ground truth no declara)
- RES-004/openai · AVISO · IA2.contexto[+]: esperado None, obtenido {'num_linea': 1, 'campo_contexto': 'contenedores_retirados', 'valor_esperado': 1.0} (fila producida por el sistema que el ground truth no declara)
- RES-004/openai · AVISO · IA2.contexto[+]: esperado None, obtenido {'num_linea': 1, 'campo_contexto': 'rol_linea', 'valor_esperado': 'base'} (fila producida por el sistema que el ground truth no declara)
- RES-005/openai · FALLO · IA2.contexto[1/TIPO_FAMILIA].caso_id: esperado 'RES-005', obtenido None
- RES-005/openai · AVISO · IA2.contexto[1/TIPO_FAMILIA].comentario: esperado 'Familia de linea del catalogo unico: el documento es de gestion de residuos (RCD).', obtenido None
- RES-005/openai · FALLO · IA2.contexto[1/CODIGO_LER].caso_id: esperado 'RES-005', obtenido None
- RES-005/openai · AVISO · IA2.contexto[1/CODIGO_LER].comentario: esperado 'No hay codigo de obra en albaran, no ha cogido ninguna', obtenido None
- RES-005/openai · FALLO · IA2.contexto[1/VOLUMEN_M3].caso_id: esperado 'RES-005', obtenido None
- RES-005/openai · AVISO · IA2.contexto[1/VOLUMEN_M3].comentario: esperado 'El 6 manuscrito en la columna VOL. m3. Es la CAPACIDAD del contenedor (§8.1), no una cantidad de material.', obtenido None
- RES-005/openai · FALLO · IA2.contexto[2/CODIGO_LER]: esperado {'campo_contexto': 'codigo_ler', 'caso_id': 'RES-005', 'comentario': 'No hay codigo de obra en albaran, no ha cogido ninguna', 'num_linea': 2, 'valor_esperado': '170604'}, obtenido None (fila del ground truth que el sistema no ha producido)
- RES-005/openai · AVISO · IA2.contexto[+]: esperado None, obtenido {'num_linea': 1, 'campo_contexto': 'peso_toneladas', 'valor_esperado': 1.8} (fila producida por el sistema que el ground truth no declara)
- RES-005/openai · AVISO · IA2.contexto[+]: esperado None, obtenido {'num_linea': 1, 'campo_contexto': 'rol_linea', 'valor_esperado': 'base'} (fila producida por el sistema que el ground truth no declara)
- RES-006/openai · FALLO · IA2.contexto[1/TIPO_FAMILIA].caso_id: esperado 'RES-006', obtenido None
- RES-006/openai · AVISO · IA2.contexto[1/TIPO_FAMILIA].comentario: esperado 'Familia de linea del catalogo unico: el documento es de gestion de residuos (RCD).', obtenido None
- RES-006/openai · FALLO · IA2.contexto[1/CODIGO_LER].caso_id: esperado 'RES-006', obtenido None
- RES-006/openai · AVISO · IA2.contexto[1/CODIGO_LER].comentario: esperado 'hay que guardar el codigo ler en bbdd, lo ha hecho? En codigo existente no sale, y no hay columna de LER en la vista detallada.', obtenido None
- RES-006/openai · FALLO · IA2.contexto[1/VOLUMEN_M3].caso_id: esperado 'RES-006', obtenido None
- RES-006/openai · AVISO · IA2.contexto[1/VOLUMEN_M3].comentario: esperado 'El 6 manuscrito en la columna VOL. m3. Es la CAPACIDAD del contenedor (§8.1), no una cantidad de material.', obtenido None
- RES-006/openai · AVISO · IA2.contexto[+]: esperado None, obtenido {'num_linea': 1, 'campo_contexto': 'rol_linea', 'valor_esperado': 'base'} (fila producida por el sistema que el ground truth no declara)
- RES-007/openai · FALLO · IA2.contexto[1/TIPO_FAMILIA].caso_id: esperado 'RES-007', obtenido None
- RES-007/openai · AVISO · IA2.contexto[1/TIPO_FAMILIA].comentario: esperado 'Familia de linea del catalogo unico: el documento es de gestion de residuos (RCD).', obtenido None
- RES-007/openai · FALLO · IA2.contexto[1/CODIGO_LER].caso_id: esperado 'RES-007', obtenido None
- RES-007/openai · AVISO · IA2.contexto[1/CODIGO_LER].comentario: esperado 'leido mal la obra (no sale en albaran, la habra cogido po rdireccion, ver como lo ha hecho). Coge mal el CIF proveedor (no encuentro de donde lo ha sacado, en la obra si que estra salmedina). Podriamos hacer que proveedores ya identificados claramente, como salmedina, al leer el nombre ya coja todo?. estudiar como ha llegado a la info que ha recogido. no ha encontrado contrato porque no hay en la obra que eligio (que estaba mal)\nNo ha metido el precio unitario del incremento LER', obtenido None
- RES-007/openai · FALLO · IA2.contexto[1/VOLUMEN_M3].caso_id: esperado 'RES-007', obtenido None
- RES-007/openai · AVISO · IA2.contexto[1/VOLUMEN_M3].comentario: esperado 'El 9 manuscrito en la columna VOL. m3. Es la CAPACIDAD del contenedor (§8.1), no una cantidad de material.', obtenido None
- RES-007/openai · FALLO · IA2.contexto[2/CODIGO_LER]: esperado {'campo_contexto': 'codigo_ler', 'caso_id': 'RES-007', 'comentario': 'leido mal la obra (no sale en albaran, la habra cogido po rdireccion, ver como lo ha hecho). Coge mal el CIF proveedor (no encuentro de donde lo ha sacado, en la obra si que estra salmedina). Podriamos hacer que proveedores ya identificados claramente, como salmedina, al leer el nombre ya coja todo?. estudiar como ha llegado a la info que ha recogido. no ha encontrado contrato porque no hay en la obra que eligio (que estaba mal)', 'num_linea': 2, 'valor_esperado': '170802'}, obtenido None (fila del ground truth que el sistema no ha producido)
- RES-007/openai · AVISO · IA2.contexto[+]: esperado None, obtenido {'num_linea': 1, 'campo_contexto': 'peso_toneladas', 'valor_esperado': 23.6} (fila producida por el sistema que el ground truth no declara)
- RES-007/openai · AVISO · IA2.contexto[+]: esperado None, obtenido {'num_linea': 1, 'campo_contexto': 'rol_linea', 'valor_esperado': 'base'} (fila producida por el sistema que el ground truth no declara)
- RES-008/openai · FALLO · IA2.contexto[1/CODIGO_LER]: esperado {'campo_contexto': 'codigo_ler', 'caso_id': 'RES-008', 'comentario': 'la partida esta mal, era 32.01, en lugar de 04.52.01 (si bien es cierto que esta cortado el numero). El ler no viene en el contrato, asi que aunque haya cogido el generico deberia buscar en la oferta', 'num_linea': 1, 'valor_esperado': '170203'}, obtenido None (fila del ground truth que el sistema no ha producido)
- RES-008/openai · AVISO · IA2.contexto[+]: esperado None, obtenido {'num_linea': 1, 'campo_contexto': 'rol_linea', 'valor_esperado': 'base'} (fila producida por el sistema que el ground truth no declara)
- RES-008/openai · AVISO · IA2.contexto[+]: esperado None, obtenido {'num_linea': 1, 'campo_contexto': 'tipo_familia', 'valor_esperado': 'residuos'} (fila producida por el sistema que el ground truth no declara)
- RES-009/openai · FALLO · IA2.contexto[1/CODIGO_LER].caso_id: esperado 'RES-009', obtenido None
- RES-009/openai · AVISO · IA2.contexto[1/CODIGO_LER].comentario: esperado 'numero de albraran incorrecto. Ha cogido 09478. la obra no venaia y ha deducido una incorrecta. Si tiene match de proveedor solo deberia intentar deducir entre las que tienen dicho porveedor en la obra', obtenido None
- RES-009/openai · AVISO · IA2.contexto[+]: esperado None, obtenido {'num_linea': 1, 'campo_contexto': 'rol_linea', 'valor_esperado': 'base'} (fila producida por el sistema que el ground truth no declara)
- RES-009/openai · AVISO · IA2.contexto[+]: esperado None, obtenido {'num_linea': 1, 'campo_contexto': 'tipo_familia', 'valor_esperado': 'residuos'} (fila producida por el sistema que el ground truth no declara)

## IA3 · valoración contra contrato (sv5) — ROJO

- Casos evaluados: 59 · omitidos: 0
- Proveedores invocados: gemini

| Caso | Estado | Fallos críticos | Avisos laxos | Motivo |
|---|---|---|---|---|
| ALQ-001 | ROJO | 12 | 0 | — |
| COM-001 | ROJO | 4 | 0 | — |
| FER-001 | ROJO | 2 | 0 | — |
| FER-002 | ROJO | 16 | 0 | — |
| FER-003 | ROJO | 6 | 0 | — |
| GEN-001 | ROJO | 4 | 0 | — |
| GEN-002 | ROJO | 23 | 0 | — |
| GEN-003 | ROJO | 8 | 0 | — |
| GEN-004 | ROJO | 4 | 0 | — |
| GEN-005 | ROJO | 8 | 0 | — |
| GEN-006 | ROJO | 4 | 0 | — |
| GEN-007 | ROJO | 2 | 0 | — |
| GEN-008 | ROJO | 4 | 0 | — |
| GEN-009 | ROJO | 4 | 0 | — |
| GEN-010 | ROJO | 4 | 0 | — |
| GRA-001 | ROJO | 4 | 0 | — |
| GRA-002 | ROJO | 4 | 0 | — |
| HOR-001 | ROJO | 5 | 0 | — |
| HOR-002 | ROJO | 6 | 0 | — |
| HOR-003 | ROJO | 5 | 0 | — |
| HOR-004 | ROJO | 23 | 0 | — |
| HOR-005 | ROJO | 21 | 2 | — |
| HOR-006 | ROJO | 4 | 0 | — |
| HOR-007 | ROJO | 9 | 0 | — |
| HOR-008 | ROJO | 5 | 0 | — |
| HOR-009 | ROJO | 13 | 0 | — |
| HOR-010 | ROJO | 9 | 1 | — |
| HOR-011 | ROJO | 5 | 0 | — |
| HOR-012 | ROJO | 9 | 1 | — |
| HOR-013 | ROJO | 5 | 0 | — |
| HOR-014 | ROJO | 9 | 0 | — |
| HOR-015 | ROJO | 13 | 1 | — |
| HOR-016 | ROJO | 5 | 0 | — |
| HOR-017 | ROJO | 17 | 1 | — |
| MOR-001 | ROJO | 5 | 0 | — |
| MOR-002 | ROJO | 9 | 0 | — |
| MOR-003 | ROJO | 8 | 0 | — |
| MOR-004 | ROJO | 9 | 0 | — |
| RES-001 | ROJO | 1 | 0 | — |
| RES-002 | ROJO | 1 | 0 | — |
| RES-003 | ROJO | 5 | 1 | — |
| RES-004 | ROJO | 5 | 1 | — |
| RES-005 | ROJO | 5 | 1 | — |
| RES-006 | ROJO | 1 | 0 | — |
| RES-007 | ROJO | 9 | 1 | — |
| RES-008 | ROJO | 4 | 0 | — |
| RES-009 | ROJO | 5 | 0 | — |
| RES-010 | ROJO | 9 | 0 | — |
| RES-011 | ROJO | 9 | 0 | — |
| RES-012 | ROJO | 8 | 0 | — |
| RES-013 | ROJO | 8 | 0 | — |
| RES-014 | ROJO | 9 | 0 | — |
| RES-015 | ROJO | 9 | 0 | — |
| RES-016 | ROJO | 4 | 0 | — |
| RES-017 | ROJO | 8 | 0 | — |
| RES-018 | ROJO | 9 | 0 | — |
| RES-019 | ROJO | 8 | 0 | — |
| RES-020 | ROJO | 4 | 0 | — |
| RES-021 | ROJO | 8 | 0 | — |

Detalle campo a campo:

- ALQ-001 · FALLO · IA3.lineas_valoradas[1].codigo_partida_final: esperado 'ALMACEN', obtenido None
- ALQ-001 · FALLO · IA3.lineas_valoradas[1].importe_calculado: esperado 170, obtenido None
- ALQ-001 · FALLO · IA3.lineas_valoradas[1].precio_source: esperado 'contrato_db', obtenido None
- ALQ-001 · FALLO · IA3.lineas_valoradas[1].precio_unitario_final: esperado 170, obtenido None
- ALQ-001 · FALLO · IA3.lineas_valoradas[2].codigo_partida_final: esperado 'ALMACEN', obtenido None
- ALQ-001 · FALLO · IA3.lineas_valoradas[2].importe_calculado: esperado 805, obtenido None
- ALQ-001 · FALLO · IA3.lineas_valoradas[2].precio_source: esperado 'contrato_db', obtenido None
- ALQ-001 · FALLO · IA3.lineas_valoradas[2].precio_unitario_final: esperado 115, obtenido None
- ALQ-001 · FALLO · IA3.lineas_valoradas[3].codigo_partida_final: esperado 'ALMACEN', obtenido None
- ALQ-001 · FALLO · IA3.lineas_valoradas[3].importe_calculado: esperado 154, obtenido None
- ALQ-001 · FALLO · IA3.lineas_valoradas[3].precio_source: esperado 'oferta', obtenido None
- ALQ-001 · FALLO · IA3.lineas_valoradas[3].precio_unitario_final: esperado 157, obtenido None
- COM-001 · FALLO · IA3.lineas_valoradas[1].codigo_partida_final: esperado 'CI.4.1', obtenido None
- COM-001 · FALLO · IA3.lineas_valoradas[1].importe_calculado: esperado 984.46, obtenido None
- COM-001 · FALLO · IA3.lineas_valoradas[1].precio_source: esperado 'deducido', obtenido None
- COM-001 · FALLO · IA3.lineas_valoradas[1].precio_unitario_final: esperado 1.230578, obtenido None
- FER-001 · FALLO · IA3.lineas_valoradas[1].codigo_partida_final: esperado 'CI.4.18', obtenido None
- FER-001 · FALLO · IA3.lineas_valoradas[1].importe_calculado: esperado 19.41, obtenido 32.35
- FER-002 · FALLO · IA3.lineas_valoradas[1].codigo_partida_final: esperado 'P4.36.01', obtenido None
- FER-002 · FALLO · IA3.lineas_valoradas[1].importe_calculado: esperado 17.59, obtenido 29.32
- FER-002 · FALLO · IA3.lineas_valoradas[2].codigo_partida_final: esperado 'P4.36.01', obtenido None
- FER-002 · FALLO · IA3.lineas_valoradas[2].importe_calculado: esperado 10.27, obtenido 17.11
- FER-002 · FALLO · IA3.lineas_valoradas[3].codigo_partida_final: esperado 'P4.36.01', obtenido None
- FER-002 · FALLO · IA3.lineas_valoradas[3].importe_calculado: esperado 27.81, obtenido 46.36
- FER-002 · FALLO · IA3.lineas_valoradas[4].codigo_partida_final: esperado 'P5.36.01', obtenido None
- FER-002 · FALLO · IA3.lineas_valoradas[4].importe_calculado: esperado 17.59, obtenido 29.32
- FER-002 · FALLO · IA3.lineas_valoradas[5].codigo_partida_final: esperado 'P5.36.01', obtenido None
- FER-002 · FALLO · IA3.lineas_valoradas[5].importe_calculado: esperado 10.27, obtenido 17.11
- FER-002 · FALLO · IA3.lineas_valoradas[6].codigo_partida_final: esperado 'P5.36.01', obtenido None
- FER-002 · FALLO · IA3.lineas_valoradas[6].importe_calculado: esperado 27.81, obtenido 46.36
- FER-002 · FALLO · IA3.lineas_valoradas[7].codigo_partida_final: esperado 'CI.4.18', obtenido None
- FER-002 · FALLO · IA3.lineas_valoradas[7].importe_calculado: esperado 13.19, obtenido 21.99
- FER-002 · FALLO · IA3.lineas_valoradas[8].codigo_partida_final: esperado 'CI.4.18', obtenido None
- FER-002 · FALLO · IA3.lineas_valoradas[8].importe_calculado: esperado 15.12, obtenido 25.2
- FER-003 · FALLO · IA3.lineas_valoradas[1].codigo_partida_final: esperado 'CI.4.18', obtenido None
- FER-003 · FALLO · IA3.lineas_valoradas[1].precio_unitario_final: esperado 95.481, obtenido 57.2875
- FER-003 · FALLO · IA3.lineas_valoradas[2].codigo_partida_final: esperado 'CI.4.18', obtenido None
- FER-003 · FALLO · IA3.lineas_valoradas[2].importe_calculado: esperado -163.15, obtenido None
- FER-003 · FALLO · IA3.lineas_valoradas[2].precio_source: esperado 'deducido', obtenido None
- FER-003 · FALLO · IA3.lineas_valoradas[2].precio_unitario_final: esperado 95.481, obtenido None
- GEN-001 · FALLO · IA3.lineas_valoradas[1].codigo_partida_final: esperado 'P4.22.02.03.01.07', obtenido None
- GEN-001 · FALLO · IA3.lineas_valoradas[1].importe_calculado: esperado 3393, obtenido None
- GEN-001 · FALLO · IA3.lineas_valoradas[1].precio_source: esperado 'contrato_db', obtenido None
- GEN-001 · FALLO · IA3.lineas_valoradas[1].precio_unitario_final: esperado 9, obtenido None
- GEN-002 · FALLO · IA3.lineas_valoradas[1].codigo_partida_final: esperado 'P5.09.03', obtenido None
- GEN-002 · FALLO · IA3.lineas_valoradas[1].importe_calculado: esperado 621.22, obtenido None
- GEN-002 · FALLO · IA3.lineas_valoradas[1].precio_source: esperado 'contrato_db', obtenido None
- GEN-002 · FALLO · IA3.lineas_valoradas[1].precio_unitario_final: esperado 14.38, obtenido None
- GEN-002 · FALLO · IA3.lineas_valoradas[2].codigo_partida_final: esperado 'P5.09.03', obtenido None
- GEN-002 · FALLO · IA3.lineas_valoradas[2].importe_calculado: esperado 5590.94, obtenido None
- GEN-002 · FALLO · IA3.lineas_valoradas[2].precio_source: esperado 'contrato_db', obtenido None
- GEN-002 · FALLO · IA3.lineas_valoradas[2].precio_unitario_final: esperado 14.38, obtenido None
- GEN-002 · FALLO · IA3.lineas_valoradas[3].codigo_partida_final: esperado 'P5.09.03', obtenido None
- GEN-002 · FALLO · IA3.lineas_valoradas[3].importe_calculado: esperado 621.22, obtenido None
- GEN-002 · FALLO · IA3.lineas_valoradas[3].precio_source: esperado 'contrato_db', obtenido None
- GEN-002 · FALLO · IA3.lineas_valoradas[3].precio_unitario_final: esperado 14.38, obtenido None
- GEN-002 · FALLO · IA3.lineas_valoradas[4].codigo_partida_final: esperado 'P5.09.04', obtenido None
- GEN-002 · FALLO · IA3.lineas_valoradas[4].importe_calculado: esperado 621.22, obtenido None
- GEN-002 · FALLO · IA3.lineas_valoradas[4].precio_source: esperado 'contrato_db', obtenido None
- GEN-002 · FALLO · IA3.lineas_valoradas[4].precio_unitario_final: esperado 14.38, obtenido None
- GEN-002 · FALLO · IA3.lineas_valoradas[5].codigo_partida_final: esperado 'P5.09.05', obtenido None
- GEN-002 · FALLO · IA3.lineas_valoradas[5].importe_calculado: esperado 621.22, obtenido None
- GEN-002 · FALLO · IA3.lineas_valoradas[5].precio_source: esperado 'contrato_db', obtenido None
- GEN-002 · FALLO · IA3.lineas_valoradas[5].precio_unitario_final: esperado 14.38, obtenido None
- GEN-002 · FALLO · IA3.lineas_valoradas[6].codigo_partida_final: esperado 'P5.09.06', obtenido None
- GEN-002 · FALLO · IA3.lineas_valoradas[7].codigo_partida_final: esperado 'P5.38.07.02', obtenido None
- GEN-002 · FALLO · IA3.lineas_valoradas[8].codigo_partida_final: esperado 'ALMACEN', obtenido None
- GEN-003 · FALLO · IA3.lineas_valoradas[1].codigo_partida_final: esperado 'P4.09.04', obtenido None
- GEN-003 · FALLO · IA3.lineas_valoradas[1].importe_calculado: esperado 341.67, obtenido None
- GEN-003 · FALLO · IA3.lineas_valoradas[1].precio_source: esperado 'contrato_db', obtenido None
- GEN-003 · FALLO · IA3.lineas_valoradas[1].precio_unitario_final: esperado 14.38, obtenido None
- GEN-003 · FALLO · IA3.lineas_valoradas[2].codigo_partida_final: esperado 'P4.08.21', obtenido None
- GEN-003 · FALLO · IA3.lineas_valoradas[2].importe_calculado: esperado 179.4, obtenido None
- GEN-003 · FALLO · IA3.lineas_valoradas[2].precio_source: esperado 'contrato_db', obtenido None
- GEN-003 · FALLO · IA3.lineas_valoradas[2].precio_unitario_final: esperado 2.76, obtenido None
- GEN-004 · FALLO · IA3.lineas_valoradas[1].codigo_partida_final: esperado '11.02.01', obtenido None
- GEN-004 · FALLO · IA3.lineas_valoradas[1].importe_calculado: esperado 3755.7, obtenido None
- GEN-004 · FALLO · IA3.lineas_valoradas[1].precio_source: esperado 'contrato_db', obtenido None
- GEN-004 · FALLO · IA3.lineas_valoradas[1].precio_unitario_final: esperado 41.73, obtenido None
- GEN-005 · FALLO · IA3.lineas_valoradas[1].codigo_partida_final: esperado '11.02.01', obtenido None
- GEN-005 · FALLO · IA3.lineas_valoradas[1].importe_calculado: esperado 219.48, obtenido None
- GEN-005 · FALLO · IA3.lineas_valoradas[1].precio_source: esperado 'contrato_db', obtenido None
- GEN-005 · FALLO · IA3.lineas_valoradas[1].precio_unitario_final: esperado 109.74, obtenido None
- GEN-005 · FALLO · IA3.lineas_valoradas[2].codigo_partida_final: esperado '11.01.11', obtenido None
- GEN-005 · FALLO · IA3.lineas_valoradas[2].importe_calculado: esperado 285.76, obtenido None
- GEN-005 · FALLO · IA3.lineas_valoradas[2].precio_source: esperado 'contrato_db', obtenido None
- GEN-005 · FALLO · IA3.lineas_valoradas[2].precio_unitario_final: esperado 71.44, obtenido None
- GEN-006 · FALLO · IA3.lineas_valoradas[1].codigo_partida_final: esperado '11.01.11', obtenido None
- GEN-006 · FALLO · IA3.lineas_valoradas[1].importe_calculado: esperado 721.68, obtenido None
- GEN-006 · FALLO · IA3.lineas_valoradas[1].precio_source: esperado 'contrato_db', obtenido None
- GEN-006 · FALLO · IA3.lineas_valoradas[1].precio_unitario_final: esperado 120.28, obtenido None
- GEN-007 · FALLO · IA3.lineas_valoradas[1].codigo_partida_final: esperado '11.01.11', obtenido None
- GEN-007 · FALLO · IA3.lineas_valoradas[1].precio_source: esperado 'contrato_db', obtenido None
- GEN-008 · FALLO · IA3.lineas_valoradas[1].codigo_partida_final: esperado '11.01.11', obtenido None
- GEN-008 · FALLO · IA3.lineas_valoradas[1].importe_calculado: esperado 142.88, obtenido None
- GEN-008 · FALLO · IA3.lineas_valoradas[1].precio_source: esperado 'contrato_db', obtenido None
- GEN-008 · FALLO · IA3.lineas_valoradas[1].precio_unitario_final: esperado 71.44, obtenido None
- GEN-009 · FALLO · IA3.lineas_valoradas[1].codigo_partida_final: esperado '05.01.22', obtenido None
- GEN-009 · FALLO · IA3.lineas_valoradas[1].importe_calculado: esperado 17021.03, obtenido None
- GEN-009 · FALLO · IA3.lineas_valoradas[1].precio_source: esperado 'contrato_db', obtenido None
- GEN-009 · FALLO · IA3.lineas_valoradas[1].precio_unitario_final: esperado 16.79, obtenido None
- GEN-010 · FALLO · IA3.lineas_valoradas[1].codigo_partida_final: esperado 'ALMACEN', obtenido None
- GEN-010 · FALLO · IA3.lineas_valoradas[1].importe_calculado: esperado 174.96, obtenido None
- GEN-010 · FALLO · IA3.lineas_valoradas[1].precio_source: esperado 'contrato_db', obtenido None
- GEN-010 · FALLO · IA3.lineas_valoradas[1].precio_unitario_final: esperado 2.43, obtenido None
- GRA-001 · FALLO · IA3.lineas_valoradas[1].codigo_partida_final: esperado 'P5.22.01.03.07', obtenido None
- GRA-001 · FALLO · IA3.lineas_valoradas[1].importe_calculado: esperado 390.99, obtenido None
- GRA-001 · FALLO · IA3.lineas_valoradas[1].precio_source: esperado 'contrato_db', obtenido None
- GRA-001 · FALLO · IA3.lineas_valoradas[1].precio_unitario_final: esperado 12.87, obtenido None
- GRA-002 · FALLO · IA3.lineas_valoradas[1].codigo_partida_final: esperado 'P5.03.04', obtenido None
- GRA-002 · FALLO · IA3.lineas_valoradas[1].importe_calculado: esperado 385.59, obtenido None
- GRA-002 · FALLO · IA3.lineas_valoradas[1].precio_source: esperado 'contrato_db', obtenido None
- GRA-002 · FALLO · IA3.lineas_valoradas[1].precio_unitario_final: esperado 12.87, obtenido None
- HOR-001 · FALLO · IA3.lineas_valoradas[1].codigo_partida_final: esperado 'P5.03.09', obtenido None
- HOR-001 · FALLO · IA3.lineas_valoradas[1].importe_calculado: esperado 899.1, obtenido None
- HOR-001 · FALLO · IA3.lineas_valoradas[1].precio_source: esperado 'contrato_db', obtenido None
- HOR-001 · FALLO · IA3.lineas_valoradas[1].precio_unitario_final: esperado 99.9, obtenido None
- HOR-001 · FALLO · IA3.sinteticas_esperadas[1/@@NO_COMPARAR@@]: esperado {'cantidad': 9, 'codigo_partida': 'P5.03.09', 'modifier_source': '@@NO_COMPARAR@@', 'num_linea_base': 1, 'precio_unitario': 9, 'rol_linea': '@@NO_COMPARAR@@'}, obtenido None (fila del ground truth que el sistema no ha producido)
- HOR-002 · FALLO · IA3.lineas_valoradas[1].codigo_partida_final: esperado 'P5.03.04', obtenido None
- HOR-002 · FALLO · IA3.lineas_valoradas[1].importe_calculado: esperado 399.6, obtenido None
- HOR-002 · FALLO · IA3.lineas_valoradas[1].precio_source: esperado 'contrato_db', obtenido None
- HOR-002 · FALLO · IA3.lineas_valoradas[1].precio_unitario_final: esperado 99.9, obtenido None
- HOR-002 · FALLO · IA3.sinteticas_esperadas[1/@@NO_COMPARAR@@]: esperado {'cantidad': 2, 'codigo_partida': 'P5.03.04', 'modifier_source': '@@NO_COMPARAR@@', 'num_linea_base': 1, 'precio_unitario': 20, 'rol_linea': '@@NO_COMPARAR@@'}, obtenido None (fila del ground truth que el sistema no ha producido)
- HOR-002 · FALLO · IA3.sinteticas_esperadas[1/@@NO_COMPARAR@@]: esperado {'cantidad': 4, 'codigo_partida': 'P5.03.04', 'modifier_source': '@@NO_COMPARAR@@', 'num_linea_base': 1, 'precio_unitario': 9, 'rol_linea': '@@NO_COMPARAR@@'}, obtenido None (fila del ground truth que el sistema no ha producido)
- HOR-003 · FALLO · IA3.lineas_valoradas[1].codigo_partida_final: esperado 'P4.03.05', obtenido None
- HOR-003 · FALLO · IA3.lineas_valoradas[1].importe_calculado: esperado 799.2, obtenido None
- HOR-003 · FALLO · IA3.lineas_valoradas[1].precio_source: esperado 'contrato_db', obtenido None
- HOR-003 · FALLO · IA3.lineas_valoradas[1].precio_unitario_final: esperado 99.9, obtenido None
- HOR-003 · FALLO · IA3.sinteticas_esperadas[1/@@NO_COMPARAR@@]: esperado {'cantidad': 8, 'codigo_partida': 'P4.03.05', 'modifier_source': '@@NO_COMPARAR@@', 'num_linea_base': 1, 'precio_unitario': 9, 'rol_linea': '@@NO_COMPARAR@@'}, obtenido None (fila del ground truth que el sistema no ha producido)
- HOR-004 · FALLO · IA3.lineas_valoradas[1].codigo_partida_final: esperado '03.03.07', obtenido None
- HOR-004 · FALLO · IA3.lineas_valoradas[1].importe_calculado: esperado 965, obtenido None
- HOR-004 · FALLO · IA3.lineas_valoradas[1].precio_source: esperado 'contrato_db', obtenido None
- HOR-004 · FALLO · IA3.lineas_valoradas[1].precio_unitario_final: esperado 96.5, obtenido None
- HOR-004 · FALLO · IA3.lineas_valoradas[2].codigo_partida_final: esperado '03.03.07', obtenido None
- HOR-004 · FALLO · IA3.lineas_valoradas[2].importe_calculado: esperado 50, obtenido None
- HOR-004 · FALLO · IA3.lineas_valoradas[2].precio_source: esperado 'contrato_db', obtenido None
- HOR-004 · FALLO · IA3.lineas_valoradas[2].precio_unitario_final: esperado 5, obtenido None
- HOR-004 · FALLO · IA3.lineas_valoradas[3].codigo_partida_final: esperado '03.03.07', obtenido None
- HOR-004 · FALLO · IA3.lineas_valoradas[3].importe_calculado: esperado 40, obtenido None
- HOR-004 · FALLO · IA3.lineas_valoradas[3].precio_source: esperado 'contrato_db', obtenido None
- HOR-004 · FALLO · IA3.lineas_valoradas[3].precio_unitario_final: esperado 4, obtenido None
- HOR-004 · FALLO · IA3.lineas_valoradas[4].codigo_partida_final: esperado '03.03.07', obtenido None
- HOR-004 · FALLO · IA3.lineas_valoradas[4].importe_calculado: esperado 40, obtenido None
- HOR-004 · FALLO · IA3.lineas_valoradas[4].precio_source: esperado 'contrato_db', obtenido None
- HOR-004 · FALLO · IA3.lineas_valoradas[4].precio_unitario_final: esperado 4, obtenido None
- HOR-004 · FALLO · IA3.lineas_valoradas[5].codigo_partida_final: esperado '03.03.07', obtenido None
- HOR-004 · FALLO · IA3.lineas_valoradas[5].importe_calculado: esperado 60, obtenido None
- HOR-004 · FALLO · IA3.lineas_valoradas[5].precio_source: esperado 'contrato_db', obtenido None
- HOR-004 · FALLO · IA3.lineas_valoradas[5].precio_unitario_final: esperado 6, obtenido None
- HOR-004 · FALLO · IA3.sinteticas_esperadas[1/@@NO_COMPARAR@@]: esperado {'cantidad': 10, 'codigo_partida': '03.03.07', 'modifier_source': '@@NO_COMPARAR@@', 'num_linea_base': 1, 'precio_unitario': 3, 'rol_linea': '@@NO_COMPARAR@@'}, obtenido None (fila del ground truth que el sistema no ha producido)
- HOR-004 · FALLO · IA3.sinteticas_esperadas[1/@@NO_COMPARAR@@]: esperado {'cantidad': 10, 'codigo_partida': '03.03.07', 'modifier_source': '@@NO_COMPARAR@@', 'num_linea_base': 1, 'precio_unitario': 11, 'rol_linea': '@@NO_COMPARAR@@'}, obtenido None (fila del ground truth que el sistema no ha producido)
- HOR-004 · FALLO · IA3.sinteticas_esperadas[5/@@NO_COMPARAR@@]: esperado {'cantidad': 10, 'codigo_partida': '03.03.07', 'modifier_source': '@@NO_COMPARAR@@', 'num_linea_base': 5, 'precio_unitario': 0.75, 'rol_linea': '@@NO_COMPARAR@@'}, obtenido None (fila del ground truth que el sistema no ha producido)
- HOR-005 · FALLO · IA3.lineas_valoradas[1].codigo_partida_final: esperado 'almacen', obtenido None
- HOR-005 · FALLO · IA3.lineas_valoradas[1].importe_calculado: esperado 339, obtenido None
- HOR-005 · FALLO · IA3.lineas_valoradas[1].precio_source: esperado 'contrato_db', obtenido None
- HOR-005 · FALLO · IA3.lineas_valoradas[1].precio_unitario_final: esperado 84.75, obtenido None
- HOR-005 · FALLO · IA3.lineas_valoradas[2].codigo_partida_final: esperado 'almacen', obtenido None
- HOR-005 · FALLO · IA3.lineas_valoradas[2].importe_calculado: esperado 14, obtenido None
- HOR-005 · FALLO · IA3.lineas_valoradas[2].precio_source: esperado 'contrato_db', obtenido None
- HOR-005 · FALLO · IA3.lineas_valoradas[2].precio_unitario_final: esperado 3.5, obtenido None
- HOR-005 · FALLO · IA3.lineas_valoradas[3].codigo_partida_final: esperado 'almacen', obtenido None
- HOR-005 · FALLO · IA3.lineas_valoradas[3].importe_calculado: esperado 12, obtenido None
- HOR-005 · FALLO · IA3.lineas_valoradas[3].precio_source: esperado 'oferta', obtenido None
- HOR-005 · FALLO · IA3.lineas_valoradas[3].precio_unitario_final: esperado 3, obtenido None
- HOR-005 · FALLO · IA3.lineas_valoradas[4].codigo_partida_final: esperado 'almacen', obtenido None
- HOR-005 · FALLO · IA3.lineas_valoradas[4].importe_calculado: esperado 12, obtenido None
- HOR-005 · FALLO · IA3.lineas_valoradas[4].precio_source: esperado 'oferta', obtenido None
- HOR-005 · FALLO · IA3.lineas_valoradas[4].precio_unitario_final: esperado 3, obtenido None
- HOR-005 · FALLO · IA3.lineas_valoradas[5].codigo_partida_final: esperado 'almacen', obtenido None
- HOR-005 · FALLO · IA3.lineas_valoradas[5].importe_calculado: esperado 30, obtenido None
- HOR-005 · FALLO · IA3.lineas_valoradas[5].precio_source: esperado 'oferta', obtenido None
- HOR-005 · FALLO · IA3.lineas_valoradas[5].precio_unitario_final: esperado 15, obtenido None
- HOR-005 · FALLO · IA3.sinteticas_esperadas[4/@@NO_COMPARAR@@]: esperado {'cantidad': 4, 'codigo_partida': 'almacen', 'modifier_source': '@@NO_COMPARAR@@', 'num_linea_base': 4, 'precio_unitario': 5.5, 'rol_linea': '@@NO_COMPARAR@@'}, obtenido None (fila del ground truth que el sistema no ha producido)
- HOR-005 · AVISO · IA3.sinteticas_esperadas[+]: esperado None, obtenido {'num_linea_base': 1, 'modifier_source': 'codigo_producto', 'rol_linea': 'incremento_fratasado', 'cantidad': 4.0, 'precio_unitario': None, 'codigo_partida': None, 'descripcion_linea': 'INCREMENTO POR HORMIGÓN FRATASADO'} (fila producida por el sistema que el ground truth no declara)
- HOR-005 · AVISO · IA3.sinteticas_esperadas[+]: esperado None, obtenido {'num_linea_base': 1, 'modifier_source': 'codigo_producto', 'rol_linea': 'incremento_aditivo', 'cantidad': 4.0, 'precio_unitario': None, 'codigo_partida': None, 'descripcion_linea': 'INCREMENTO POR FIBRA DE POLIPROPILENO'} (fila producida por el sistema que el ground truth no declara)
- HOR-006 · FALLO · IA3.lineas_valoradas[1].codigo_partida_final: esperado 5.01, obtenido None
- HOR-006 · FALLO · IA3.lineas_valoradas[1].importe_calculado: esperado 593.25, obtenido None
- HOR-006 · FALLO · IA3.lineas_valoradas[1].precio_source: esperado 'contrato_db', obtenido None
- HOR-006 · FALLO · IA3.lineas_valoradas[1].precio_unitario_final: esperado 84.75, obtenido None
- HOR-007 · FALLO · IA3.lineas_valoradas[1].codigo_partida_final: esperado 5.04, obtenido None
- HOR-007 · FALLO · IA3.lineas_valoradas[1].importe_calculado: esperado 423.75, obtenido None
- HOR-007 · FALLO · IA3.lineas_valoradas[1].precio_source: esperado 'contrato_db', obtenido None
- HOR-007 · FALLO · IA3.lineas_valoradas[1].precio_unitario_final: esperado 84.75, obtenido None
- HOR-007 · FALLO · IA3.lineas_valoradas[2].codigo_partida_final: esperado 5.04, obtenido None
- HOR-007 · FALLO · IA3.lineas_valoradas[2].importe_calculado: esperado 15, obtenido None
- HOR-007 · FALLO · IA3.lineas_valoradas[2].precio_source: esperado 'oferta', obtenido None
- HOR-007 · FALLO · IA3.lineas_valoradas[2].precio_unitario_final: esperado 15, obtenido None
- HOR-007 · FALLO · IA3.sinteticas_esperadas[1/@@NO_COMPARAR@@]: esperado {'cantidad': 5, 'codigo_partida': 5.04, 'modifier_source': '@@NO_COMPARAR@@', 'num_linea_base': 1, 'precio_unitario': 5.5, 'rol_linea': '@@NO_COMPARAR@@'}, obtenido None (fila del ground truth que el sistema no ha producido)
- HOR-008 · FALLO · IA3.lineas_valoradas[1].codigo_partida_final: esperado '32.02.01.01', obtenido None
- HOR-008 · FALLO · IA3.lineas_valoradas[1].importe_calculado: esperado 608, obtenido None
- HOR-008 · FALLO · IA3.lineas_valoradas[1].precio_source: esperado 'contrato_db', obtenido None
- HOR-008 · FALLO · IA3.lineas_valoradas[1].precio_unitario_final: esperado 76, obtenido None
- HOR-008 · FALLO · IA3.sinteticas_esperadas[1/@@NO_COMPARAR@@]: esperado {'cantidad': 8, 'codigo_partida': '32.02.01.01', 'modifier_source': '@@NO_COMPARAR@@', 'num_linea_base': 1, 'precio_unitario': 3.8, 'rol_linea': '@@NO_COMPARAR@@'}, obtenido None (fila del ground truth que el sistema no ha producido)
- HOR-009 · FALLO · IA3.lineas_valoradas[1].codigo_partida_final: esperado '32.03.02', obtenido None
- HOR-009 · FALLO · IA3.lineas_valoradas[1].importe_calculado: esperado 80, obtenido None
- HOR-009 · FALLO · IA3.lineas_valoradas[1].precio_source: esperado 'contrato_db', obtenido None
- HOR-009 · FALLO · IA3.lineas_valoradas[1].precio_unitario_final: esperado 80, obtenido None
- HOR-009 · FALLO · IA3.lineas_valoradas[2].codigo_partida_final: esperado '32.03.02', obtenido None
- HOR-009 · FALLO · IA3.lineas_valoradas[2].importe_calculado: esperado 3.5, obtenido None
- HOR-009 · FALLO · IA3.lineas_valoradas[2].precio_source: esperado 'contrato_db', obtenido None
- HOR-009 · FALLO · IA3.lineas_valoradas[2].precio_unitario_final: esperado 3.5, obtenido None
- HOR-009 · FALLO · IA3.lineas_valoradas[3].codigo_partida_final: esperado '32.03.02', obtenido None
- HOR-009 · FALLO · IA3.lineas_valoradas[3].importe_calculado: esperado 3, obtenido None
- HOR-009 · FALLO · IA3.lineas_valoradas[3].precio_source: esperado 'contrato_db', obtenido None
- HOR-009 · FALLO · IA3.lineas_valoradas[3].precio_unitario_final: esperado 3, obtenido None
- HOR-009 · FALLO · IA3.sinteticas_esperadas[3/@@NO_COMPARAR@@]: esperado {'cantidad': 8, 'codigo_partida': '32.03.02', 'modifier_source': '@@NO_COMPARAR@@', 'num_linea_base': 3, 'precio_unitario': 5, 'rol_linea': '@@NO_COMPARAR@@'}, obtenido None (fila del ground truth que el sistema no ha producido)
- HOR-010 · FALLO · IA3.lineas_valoradas[1].codigo_partida_final: esperado 5.02, obtenido None
- HOR-010 · FALLO · IA3.lineas_valoradas[1].importe_calculado: esperado 678, obtenido None
- HOR-010 · FALLO · IA3.lineas_valoradas[1].precio_source: esperado 'contrato_db', obtenido None
- HOR-010 · FALLO · IA3.lineas_valoradas[1].precio_unitario_final: esperado 84.75, obtenido None
- HOR-010 · FALLO · IA3.lineas_valoradas[2].codigo_partida_final: esperado 5.02, obtenido None
- HOR-010 · FALLO · IA3.lineas_valoradas[2].importe_calculado: esperado 24, obtenido None
- HOR-010 · FALLO · IA3.lineas_valoradas[2].precio_source: esperado 'contrato_db', obtenido None
- HOR-010 · FALLO · IA3.lineas_valoradas[2].precio_unitario_final: esperado 3, obtenido None
- HOR-010 · FALLO · IA3.sinteticas_esperadas[2/@@NO_COMPARAR@@]: esperado {'cantidad': 8, 'codigo_partida': 5.02, 'modifier_source': '@@NO_COMPARAR@@', 'num_linea_base': 2, 'precio_unitario': 5.5, 'rol_linea': '@@NO_COMPARAR@@'}, obtenido None (fila del ground truth que el sistema no ha producido)
- HOR-010 · AVISO · IA3.sinteticas_esperadas[+]: esperado None, obtenido {'num_linea_base': 1, 'modifier_source': 'codigo_producto', 'rol_linea': 'incremento_consistencia', 'cantidad': 8.0, 'precio_unitario': None, 'codigo_partida': None, 'descripcion_linea': 'INCREMENTO POR CONSISTENCIA FLUIDA'} (fila producida por el sistema que el ground truth no declara)
- HOR-011 · FALLO · IA3.lineas_valoradas[1].codigo_partida_final: esperado '03.01.01', obtenido None
- HOR-011 · FALLO · IA3.lineas_valoradas[1].importe_calculado: esperado 618.8, obtenido None
- HOR-011 · FALLO · IA3.lineas_valoradas[1].precio_source: esperado 'contrato_db', obtenido None
- HOR-011 · FALLO · IA3.lineas_valoradas[1].precio_unitario_final: esperado 88.4, obtenido None
- HOR-011 · FALLO · IA3.sinteticas_esperadas[1/@@NO_COMPARAR@@]: esperado {'cantidad': 7, 'codigo_partida': '03.01.01', 'modifier_source': '@@NO_COMPARAR@@', 'num_linea_base': 1, 'precio_unitario': 5.96, 'rol_linea': '@@NO_COMPARAR@@'}, obtenido None (fila del ground truth que el sistema no ha producido)
- HOR-012 · FALLO · IA3.lineas_valoradas[1].codigo_partida_final: esperado 42.01, obtenido None
- HOR-012 · FALLO · IA3.lineas_valoradas[1].importe_calculado: esperado 803.7, obtenido None
- HOR-012 · FALLO · IA3.lineas_valoradas[1].precio_source: esperado 'contrato_db', obtenido None
- HOR-012 · FALLO · IA3.lineas_valoradas[1].precio_unitario_final: esperado 89.3, obtenido None
- HOR-012 · FALLO · IA3.lineas_valoradas[2].codigo_partida_final: esperado 42.01, obtenido None
- HOR-012 · FALLO · IA3.lineas_valoradas[2].importe_calculado: esperado 27, obtenido None
- HOR-012 · FALLO · IA3.lineas_valoradas[2].precio_source: esperado 'contrato_db', obtenido None
- HOR-012 · FALLO · IA3.lineas_valoradas[2].precio_unitario_final: esperado 3, obtenido None
- HOR-012 · FALLO · IA3.sinteticas_esperadas[2/@@NO_COMPARAR@@]: esperado {'cantidad': 9, 'codigo_partida': 42.01, 'modifier_source': '@@NO_COMPARAR@@', 'num_linea_base': 2, 'precio_unitario': 6.7, 'rol_linea': '@@NO_COMPARAR@@'}, obtenido None (fila del ground truth que el sistema no ha producido)
- HOR-012 · AVISO · IA3.sinteticas_esperadas[+]: esperado None, obtenido {'num_linea_base': 1, 'modifier_source': 'codigo_producto', 'rol_linea': 'incremento_consistencia', 'cantidad': 9.0, 'precio_unitario': None, 'codigo_partida': None, 'descripcion_linea': 'INCREMENTO POR CONSISTENCIA FLUIDA'} (fila producida por el sistema que el ground truth no declara)
- HOR-013 · FALLO · IA3.lineas_valoradas[1].codigo_partida_final: esperado '38.01.03', obtenido None
- HOR-013 · FALLO · IA3.lineas_valoradas[1].importe_calculado: esperado 714.4, obtenido None
- HOR-013 · FALLO · IA3.lineas_valoradas[1].precio_source: esperado 'contrato_db', obtenido None
- HOR-013 · FALLO · IA3.lineas_valoradas[1].precio_unitario_final: esperado 89.3, obtenido None
- HOR-013 · FALLO · IA3.sinteticas_esperadas[1/@@NO_COMPARAR@@]: esperado {'cantidad': 8, 'codigo_partida': '38.01.03', 'modifier_source': '@@NO_COMPARAR@@', 'num_linea_base': 1, 'precio_unitario': 6.7, 'rol_linea': '@@NO_COMPARAR@@'}, obtenido None (fila del ground truth que el sistema no ha producido)
- HOR-014 · FALLO · IA3.lineas_valoradas[1].codigo_partida_final: esperado '38.01.03', obtenido None
- HOR-014 · FALLO · IA3.lineas_valoradas[1].importe_calculado: esperado 714.4, obtenido None
- HOR-014 · FALLO · IA3.lineas_valoradas[1].precio_source: esperado 'contrato_db', obtenido None
- HOR-014 · FALLO · IA3.lineas_valoradas[1].precio_unitario_final: esperado 89.3, obtenido None
- HOR-014 · FALLO · IA3.lineas_valoradas[2].codigo_partida_final: esperado '38.01.03', obtenido None
- HOR-014 · FALLO · IA3.lineas_valoradas[2].importe_calculado: esperado 0, obtenido None
- HOR-014 · FALLO · IA3.lineas_valoradas[2].precio_source: esperado 'oferta', obtenido None
- HOR-014 · FALLO · IA3.lineas_valoradas[2].precio_unitario_final: esperado 6, obtenido None
- HOR-014 · FALLO · IA3.sinteticas_esperadas[1/@@NO_COMPARAR@@]: esperado {'cantidad': 5, 'codigo_partida': '38.01.03', 'modifier_source': '@@NO_COMPARAR@@', 'num_linea_base': 1, 'precio_unitario': 6.7, 'rol_linea': '@@NO_COMPARAR@@'}, obtenido None (fila del ground truth que el sistema no ha producido)
- HOR-015 · FALLO · IA3.lineas_valoradas[1].codigo_partida_final: esperado 42.01, obtenido None
- HOR-015 · FALLO · IA3.lineas_valoradas[1].importe_calculado: esperado 625.1, obtenido None
- HOR-015 · FALLO · IA3.lineas_valoradas[1].precio_source: esperado 'contrato_db', obtenido None
- HOR-015 · FALLO · IA3.lineas_valoradas[1].precio_unitario_final: esperado 89.3, obtenido None
- HOR-015 · FALLO · IA3.lineas_valoradas[2].codigo_partida_final: esperado 42.01, obtenido None
- HOR-015 · FALLO · IA3.lineas_valoradas[2].importe_calculado: esperado 21, obtenido None
- HOR-015 · FALLO · IA3.lineas_valoradas[2].precio_source: esperado 'contrato_db', obtenido None
- HOR-015 · FALLO · IA3.lineas_valoradas[2].precio_unitario_final: esperado 3, obtenido None
- HOR-015 · FALLO · IA3.lineas_valoradas[3].codigo_partida_final: esperado 42.01, obtenido None
- HOR-015 · FALLO · IA3.lineas_valoradas[3].importe_calculado: esperado 21, obtenido None
- HOR-015 · FALLO · IA3.lineas_valoradas[3].precio_source: esperado 'contrato_db', obtenido None
- HOR-015 · FALLO · IA3.lineas_valoradas[3].precio_unitario_final: esperado 3, obtenido None
- HOR-015 · FALLO · IA3.sinteticas_esperadas[3/@@NO_COMPARAR@@]: esperado {'cantidad': 7, 'codigo_partida': 42.01, 'modifier_source': '@@NO_COMPARAR@@', 'num_linea_base': 3, 'precio_unitario': 6.7, 'rol_linea': '@@NO_COMPARAR@@'}, obtenido None (fila del ground truth que el sistema no ha producido)
- HOR-015 · AVISO · IA3.sinteticas_esperadas[+]: esperado None, obtenido {'num_linea_base': 1, 'modifier_source': 'codigo_producto', 'rol_linea': 'incremento_consistencia', 'cantidad': 7.0, 'precio_unitario': None, 'codigo_partida': None, 'descripcion_linea': 'INCREMENTO POR CONSISTENCIA FLUIDA'} (fila producida por el sistema que el ground truth no declara)
- HOR-016 · FALLO · IA3.lineas_valoradas[1].codigo_partida_final: esperado '38.01.01', obtenido None
- HOR-016 · FALLO · IA3.lineas_valoradas[1].importe_calculado: esperado 785.8, obtenido None
- HOR-016 · FALLO · IA3.lineas_valoradas[1].precio_source: esperado 'contrato_db', obtenido None
- HOR-016 · FALLO · IA3.lineas_valoradas[1].precio_unitario_final: esperado 78.58, obtenido None
- HOR-016 · FALLO · IA3.sinteticas_esperadas[1/@@NO_COMPARAR@@]: esperado {'cantidad': 10, 'codigo_partida': '38.01.01', 'modifier_source': '@@NO_COMPARAR@@', 'num_linea_base': 1, 'precio_unitario': 5.9, 'rol_linea': '@@NO_COMPARAR@@'}, obtenido None (fila del ground truth que el sistema no ha producido)
- HOR-017 · FALLO · IA3.lineas_valoradas[1].codigo_partida_final: esperado 42.01, obtenido None
- HOR-017 · FALLO · IA3.lineas_valoradas[1].importe_calculado: esperado 267.9, obtenido None
- HOR-017 · FALLO · IA3.lineas_valoradas[1].precio_source: esperado 'contrato_db', obtenido None
- HOR-017 · FALLO · IA3.lineas_valoradas[1].precio_unitario_final: esperado 89.3, obtenido None
- HOR-017 · FALLO · IA3.lineas_valoradas[2].codigo_partida_final: esperado 42.01, obtenido None
- HOR-017 · FALLO · IA3.lineas_valoradas[2].importe_calculado: esperado 9, obtenido None
- HOR-017 · FALLO · IA3.lineas_valoradas[2].precio_source: esperado 'contrato_db', obtenido None
- HOR-017 · FALLO · IA3.lineas_valoradas[2].precio_unitario_final: esperado 3, obtenido None
- HOR-017 · FALLO · IA3.lineas_valoradas[3].codigo_partida_final: esperado 42.01, obtenido None
- HOR-017 · FALLO · IA3.lineas_valoradas[3].importe_calculado: esperado 9, obtenido None
- HOR-017 · FALLO · IA3.lineas_valoradas[3].precio_source: esperado 'contrato_db', obtenido None
- HOR-017 · FALLO · IA3.lineas_valoradas[3].precio_unitario_final: esperado 3, obtenido None
- HOR-017 · FALLO · IA3.lineas_valoradas[4].codigo_partida_final: esperado 42.01, obtenido None
- HOR-017 · FALLO · IA3.lineas_valoradas[4].importe_calculado: esperado 18, obtenido None
- HOR-017 · FALLO · IA3.lineas_valoradas[4].precio_source: esperado 'oferta', obtenido None
- HOR-017 · FALLO · IA3.lineas_valoradas[4].precio_unitario_final: esperado 6, obtenido None
- HOR-017 · FALLO · IA3.sinteticas_esperadas[3/@@NO_COMPARAR@@]: esperado {'cantidad': 3, 'codigo_partida': 42.01, 'modifier_source': '@@NO_COMPARAR@@', 'num_linea_base': 3, 'precio_unitario': 6.7, 'rol_linea': '@@NO_COMPARAR@@'}, obtenido None (fila del ground truth que el sistema no ha producido)
- HOR-017 · AVISO · IA3.sinteticas_esperadas[+]: esperado None, obtenido {'num_linea_base': 1, 'modifier_source': 'codigo_producto', 'rol_linea': 'incremento_consistencia', 'cantidad': 3.0, 'precio_unitario': None, 'codigo_partida': None, 'descripcion_linea': 'INCREMENTO POR CONSISTENCIA FLUIDA'} (fila producida por el sistema que el ground truth no declara)
- MOR-001 · FALLO · IA3.lineas_valoradas[1].codigo_partida_final: esperado 'P5.14.01.02.02', obtenido None
- MOR-001 · FALLO · IA3.lineas_valoradas[1].importe_calculado: esperado 504, obtenido None
- MOR-001 · FALLO · IA3.lineas_valoradas[1].precio_source: esperado 'contrato_db', obtenido None
- MOR-001 · FALLO · IA3.lineas_valoradas[1].precio_unitario_final: esperado 72, obtenido None
- MOR-001 · FALLO · IA3.sinteticas_esperadas[1/@@NO_COMPARAR@@]: esperado {'cantidad': 7, 'codigo_partida': 'P5.14.01.02.02', 'modifier_source': '@@NO_COMPARAR@@', 'num_linea_base': 1, 'precio_unitario': 9, 'rol_linea': '@@NO_COMPARAR@@'}, obtenido None (fila del ground truth que el sistema no ha producido)
- MOR-002 · FALLO · IA3.lineas_valoradas[1].codigo_partida_final: esperado 'P4.14.01.02.02', obtenido None
- MOR-002 · FALLO · IA3.lineas_valoradas[1].importe_calculado: esperado 220.5, obtenido None
- MOR-002 · FALLO · IA3.lineas_valoradas[1].precio_source: esperado 'oferta', obtenido None
- MOR-002 · FALLO · IA3.lineas_valoradas[1].precio_unitario_final: esperado 73.5, obtenido None
- MOR-002 · FALLO · IA3.lineas_valoradas[2].codigo_partida_final: esperado 'P4.14.01.02.02', obtenido None
- MOR-002 · FALLO · IA3.lineas_valoradas[2].importe_calculado: esperado 60, obtenido None
- MOR-002 · FALLO · IA3.lineas_valoradas[2].precio_source: esperado 'oferta', obtenido None
- MOR-002 · FALLO · IA3.lineas_valoradas[2].precio_unitario_final: esperado 20, obtenido None
- MOR-002 · FALLO · IA3.sinteticas_esperadas[1/@@NO_COMPARAR@@]: esperado {'cantidad': 3, 'codigo_partida': 'P4.14.01.02.02', 'modifier_source': '@@NO_COMPARAR@@', 'num_linea_base': 1, 'precio_unitario': 9, 'rol_linea': '@@NO_COMPARAR@@'}, obtenido None (fila del ground truth que el sistema no ha producido)
- MOR-003 · FALLO · IA3.lineas_valoradas[1].codigo_partida_final: esperado 'almacen', obtenido None
- MOR-003 · FALLO · IA3.lineas_valoradas[1].importe_calculado: esperado 250.5, obtenido None
- MOR-003 · FALLO · IA3.lineas_valoradas[1].precio_source: esperado 'oferta', obtenido None
- MOR-003 · FALLO · IA3.lineas_valoradas[1].precio_unitario_final: esperado 83.5, obtenido None
- MOR-003 · FALLO · IA3.lineas_valoradas[2].codigo_partida_final: esperado 'almacen', obtenido None
- MOR-003 · FALLO · IA3.lineas_valoradas[2].importe_calculado: esperado 30, obtenido None
- MOR-003 · FALLO · IA3.lineas_valoradas[2].precio_source: esperado 'oferta', obtenido None
- MOR-003 · FALLO · IA3.lineas_valoradas[2].precio_unitario_final: esperado 15, obtenido None
- MOR-004 · FALLO · IA3.lineas_valoradas[1].codigo_partida_final: esperado '10.03.04', obtenido None
- MOR-004 · FALLO · IA3.lineas_valoradas[1].importe_calculado: esperado 837, obtenido None
- MOR-004 · FALLO · IA3.lineas_valoradas[1].precio_source: esperado 'oferta', obtenido None
- MOR-004 · FALLO · IA3.lineas_valoradas[1].precio_unitario_final: esperado 93, obtenido None
- MOR-004 · FALLO · IA3.lineas_valoradas[2].codigo_partida_final: esperado '10.03.04', obtenido None
- MOR-004 · FALLO · IA3.lineas_valoradas[2].importe_calculado: esperado 36, obtenido None
- MOR-004 · FALLO · IA3.lineas_valoradas[2].precio_source: esperado 'contrato_db', obtenido None
- MOR-004 · FALLO · IA3.lineas_valoradas[2].precio_unitario_final: esperado 4, obtenido None
- MOR-004 · FALLO · IA3.sinteticas_esperadas[2/@@NO_COMPARAR@@]: esperado {'cantidad': 9, 'codigo_partida': '10.03.04', 'modifier_source': '@@NO_COMPARAR@@', 'num_linea_base': 2, 'precio_unitario': 5.3, 'rol_linea': '@@NO_COMPARAR@@'}, obtenido None (fila del ground truth que el sistema no ha producido)
- RES-001 · FALLO · IA3.lineas_valoradas[1].match_method: esperado 'semantic', obtenido 'exact_concept'
- RES-002 · FALLO · IA3.lineas_valoradas[1].match_method: esperado 'semantic', obtenido 'exact_concept'
- RES-003 · FALLO · IA3.lineas_valoradas[1].match_method: esperado 'semantic', obtenido 'exact_concept'
- RES-003 · FALLO · IA3.lineas_valoradas[2].codigo_partida_final: esperado 'CI.03A.7', obtenido None
- RES-003 · FALLO · IA3.lineas_valoradas[2].importe_calculado: esperado 51, obtenido None
- RES-003 · FALLO · IA3.lineas_valoradas[2].precio_source: esperado 'contrato_db', obtenido None
- RES-003 · FALLO · IA3.lineas_valoradas[2].precio_unitario_final: esperado 51, obtenido None
- RES-003 · AVISO · IA3.sinteticas_esperadas[+]: esperado None, obtenido {'num_linea_base': 2, 'modifier_source': 'gestion_residuos', 'rol_linea': 'incremento_residuos', 'cantidad': 1.0, 'precio_unitario': 51.0, 'codigo_partida': None, 'descripcion_linea': 'INCREMENTO LER 170802'} (fila producida por el sistema que el ground truth no declara)
- RES-004 · FALLO · IA3.lineas_valoradas[1].match_method: esperado 'semantic', obtenido 'exact_concept'
- RES-004 · FALLO · IA3.lineas_valoradas[2].codigo_partida_final: esperado 'CI.03A.7', obtenido None
- RES-004 · FALLO · IA3.lineas_valoradas[2].importe_calculado: esperado 90, obtenido None
- RES-004 · FALLO · IA3.lineas_valoradas[2].precio_source: esperado 'contrato_db', obtenido None
- RES-004 · FALLO · IA3.lineas_valoradas[2].precio_unitario_final: esperado 90, obtenido None
- RES-004 · AVISO · IA3.sinteticas_esperadas[+]: esperado None, obtenido {'num_linea_base': 2, 'modifier_source': 'gestion_residuos', 'rol_linea': 'incremento_residuos', 'cantidad': 1.0, 'precio_unitario': 90.0, 'codigo_partida': None, 'descripcion_linea': 'INCREMENTO LER 170604'} (fila producida por el sistema que el ground truth no declara)
- RES-005 · FALLO · IA3.lineas_valoradas[1].match_method: esperado 'semantic', obtenido 'exact_concept'
- RES-005 · FALLO · IA3.lineas_valoradas[2].codigo_partida_final: esperado 'CI.03A.7', obtenido None
- RES-005 · FALLO · IA3.lineas_valoradas[2].importe_calculado: esperado 90, obtenido None
- RES-005 · FALLO · IA3.lineas_valoradas[2].precio_source: esperado 'contrato_db', obtenido None
- RES-005 · FALLO · IA3.lineas_valoradas[2].precio_unitario_final: esperado 90, obtenido None
- RES-005 · AVISO · IA3.sinteticas_esperadas[+]: esperado None, obtenido {'num_linea_base': 2, 'modifier_source': 'gestion_residuos', 'rol_linea': 'incremento_residuos', 'cantidad': 1.0, 'precio_unitario': 90.0, 'codigo_partida': None, 'descripcion_linea': 'INCREMENTO LER 170604'} (fila producida por el sistema que el ground truth no declara)
- RES-006 · FALLO · IA3.lineas_valoradas[1].match_method: esperado 'semantic', obtenido 'exact_concept'
- RES-007 · FALLO · IA3.lineas_valoradas[1].importe_calculado: esperado 183, obtenido 272.0
- RES-007 · FALLO · IA3.lineas_valoradas[1].precio_source: esperado 'oferta', obtenido 'contrato_db'
- RES-007 · FALLO · IA3.lineas_valoradas[1].precio_unitario_final: esperado 183, obtenido 136.0
- RES-007 · FALLO · IA3.lineas_valoradas[2].codigo_partida_final: esperado 'CI.03A.7', obtenido None
- RES-007 · FALLO · IA3.lineas_valoradas[2].importe_calculado: esperado 77, obtenido None
- RES-007 · FALLO · IA3.lineas_valoradas[2].precio_source: esperado 'oferta', obtenido None
- RES-007 · FALLO · IA3.lineas_valoradas[2].precio_unitario_final: esperado 77, obtenido None
- RES-007 · FALLO · IA3.sinteticas_esperadas[1/GESTION_RESIDUOS].cantidad: esperado 1, obtenido 2.0
- RES-007 · FALLO · IA3.sinteticas_esperadas[1/GESTION_RESIDUOS].precio_unitario: esperado 77, obtenido None
- RES-007 · AVISO · IA3.sinteticas_esperadas[+]: esperado None, obtenido {'num_linea_base': 2, 'modifier_source': 'gestion_residuos', 'rol_linea': 'incremento_residuos', 'cantidad': 2.0, 'precio_unitario': None, 'codigo_partida': None, 'descripcion_linea': 'INCREMENTO LER 170802'} (fila producida por el sistema que el ground truth no declara)
- RES-008 · FALLO · IA3.lineas_valoradas[1].codigo_partida_final: esperado 32.01, obtenido None
- RES-008 · FALLO · IA3.lineas_valoradas[1].importe_calculado: esperado 173, obtenido None
- RES-008 · FALLO · IA3.lineas_valoradas[1].precio_source: esperado 'oferta', obtenido None
- RES-008 · FALLO · IA3.lineas_valoradas[1].precio_unitario_final: esperado 173, obtenido None
- RES-009 · FALLO · IA3.lineas_valoradas[1].codigo_partida_final: esperado 32.01, obtenido None
- RES-009 · FALLO · IA3.lineas_valoradas[1].importe_calculado: esperado 157, obtenido None
- RES-009 · FALLO · IA3.lineas_valoradas[1].precio_source: esperado 'contrato_db', obtenido None
- RES-009 · FALLO · IA3.lineas_valoradas[1].precio_unitario_final: esperado 157, obtenido None
- RES-009 · FALLO · IA3.sinteticas_esperadas[1/@@NO_COMPARAR@@]: esperado {'cantidad': 1, 'codigo_partida': 32.01, 'modifier_source': '@@NO_COMPARAR@@', 'num_linea_base': 1, 'precio_unitario': 6, 'rol_linea': '@@NO_COMPARAR@@'}, obtenido None (fila del ground truth que el sistema no ha producido)
- RES-010 · FALLO · IA3.lineas_valoradas[1].codigo_partida_final: esperado 'CI.03A.7', obtenido None
- RES-010 · FALLO · IA3.lineas_valoradas[1].importe_calculado: esperado 90, obtenido None
- RES-010 · FALLO · IA3.lineas_valoradas[1].precio_source: esperado 'contrato_db', obtenido None
- RES-010 · FALLO · IA3.lineas_valoradas[1].precio_unitario_final: esperado 90, obtenido None
- RES-010 · FALLO · IA3.lineas_valoradas[2].codigo_partida_final: esperado 'CI.03A.7', obtenido None
- RES-010 · FALLO · IA3.lineas_valoradas[2].importe_calculado: esperado 78, obtenido None
- RES-010 · FALLO · IA3.lineas_valoradas[2].precio_source: esperado 'contrato_db', obtenido None
- RES-010 · FALLO · IA3.lineas_valoradas[2].precio_unitario_final: esperado 26, obtenido None
- RES-010 · FALLO · IA3.sinteticas_esperadas[2/@@NO_COMPARAR@@]: esperado {'cantidad': 3, 'codigo_partida': 'CI.03A.7', 'modifier_source': '@@NO_COMPARAR@@', 'num_linea_base': 2, 'precio_unitario': 4, 'rol_linea': '@@NO_COMPARAR@@'}, obtenido None (fila del ground truth que el sistema no ha producido)
- RES-011 · FALLO · IA3.lineas_valoradas[1].codigo_partida_final: esperado 'CI.03A.7', obtenido None
- RES-011 · FALLO · IA3.lineas_valoradas[1].importe_calculado: esperado 90, obtenido None
- RES-011 · FALLO · IA3.lineas_valoradas[1].precio_source: esperado 'contrato_db', obtenido None
- RES-011 · FALLO · IA3.lineas_valoradas[1].precio_unitario_final: esperado 90, obtenido None
- RES-011 · FALLO · IA3.lineas_valoradas[2].codigo_partida_final: esperado 'CI.03A.7', obtenido None
- RES-011 · FALLO · IA3.lineas_valoradas[2].importe_calculado: esperado 85.28, obtenido None
- RES-011 · FALLO · IA3.lineas_valoradas[2].precio_source: esperado 'contrato_db', obtenido None
- RES-011 · FALLO · IA3.lineas_valoradas[2].precio_unitario_final: esperado 26, obtenido None
- RES-011 · FALLO · IA3.sinteticas_esperadas[2/@@NO_COMPARAR@@]: esperado {'cantidad': 3.28, 'codigo_partida': 'CI.03A.7', 'modifier_source': '@@NO_COMPARAR@@', 'num_linea_base': 2, 'precio_unitario': 4, 'rol_linea': '@@NO_COMPARAR@@'}, obtenido None (fila del ground truth que el sistema no ha producido)
- RES-012 · FALLO · IA3.lineas_valoradas[1].codigo_partida_final: esperado 'CI.03A.7', obtenido None
- RES-012 · FALLO · IA3.lineas_valoradas[1].importe_calculado: esperado 90, obtenido None
- RES-012 · FALLO · IA3.lineas_valoradas[1].precio_source: esperado 'contrato_db', obtenido None
- RES-012 · FALLO · IA3.lineas_valoradas[1].precio_unitario_final: esperado 90, obtenido None
- RES-012 · FALLO · IA3.lineas_valoradas[2].codigo_partida_final: esperado 'CI.03A.7', obtenido None
- RES-012 · FALLO · IA3.lineas_valoradas[2].importe_calculado: esperado 166.6, obtenido None
- RES-012 · FALLO · IA3.lineas_valoradas[2].precio_source: esperado 'contrato_db', obtenido None
- RES-012 · FALLO · IA3.lineas_valoradas[2].precio_unitario_final: esperado 70, obtenido None
- RES-013 · FALLO · IA3.lineas_valoradas[1].codigo_partida_final: esperado 'CI.03A.7', obtenido None
- RES-013 · FALLO · IA3.lineas_valoradas[1].importe_calculado: esperado 90, obtenido None
- RES-013 · FALLO · IA3.lineas_valoradas[1].precio_source: esperado 'contrato_db', obtenido None
- RES-013 · FALLO · IA3.lineas_valoradas[1].precio_unitario_final: esperado 90, obtenido None
- RES-013 · FALLO · IA3.lineas_valoradas[2].codigo_partida_final: esperado 'CI.03A.7', obtenido None
- RES-013 · FALLO · IA3.lineas_valoradas[2].importe_calculado: esperado 120.4, obtenido None
- RES-013 · FALLO · IA3.lineas_valoradas[2].precio_source: esperado 'contrato_db', obtenido None
- RES-013 · FALLO · IA3.lineas_valoradas[2].precio_unitario_final: esperado 70, obtenido None
- RES-014 · FALLO · IA3.lineas_valoradas[1].codigo_partida_final: esperado 'CI.03A.7', obtenido None
- RES-014 · FALLO · IA3.lineas_valoradas[1].importe_calculado: esperado 90, obtenido None
- RES-014 · FALLO · IA3.lineas_valoradas[1].precio_source: esperado 'contrato_db', obtenido None
- RES-014 · FALLO · IA3.lineas_valoradas[1].precio_unitario_final: esperado 90, obtenido None
- RES-014 · FALLO · IA3.lineas_valoradas[2].codigo_partida_final: esperado 'CI.03A.7', obtenido None
- RES-014 · FALLO · IA3.lineas_valoradas[2].importe_calculado: esperado 158.6, obtenido None
- RES-014 · FALLO · IA3.lineas_valoradas[2].precio_source: esperado 'contrato_db', obtenido None
- RES-014 · FALLO · IA3.lineas_valoradas[2].precio_unitario_final: esperado 26, obtenido None
- RES-014 · FALLO · IA3.sinteticas_esperadas[2/@@NO_COMPARAR@@]: esperado {'cantidad': 6.1, 'codigo_partida': 'CI.03A.7', 'modifier_source': '@@NO_COMPARAR@@', 'num_linea_base': 2, 'precio_unitario': 4, 'rol_linea': '@@NO_COMPARAR@@'}, obtenido None (fila del ground truth que el sistema no ha producido)
- RES-015 · FALLO · IA3.lineas_valoradas[1].codigo_partida_final: esperado 'CI.03A.7', obtenido None
- RES-015 · FALLO · IA3.lineas_valoradas[1].importe_calculado: esperado 90, obtenido None
- RES-015 · FALLO · IA3.lineas_valoradas[1].precio_source: esperado 'contrato_db', obtenido None
- RES-015 · FALLO · IA3.lineas_valoradas[1].precio_unitario_final: esperado 90, obtenido None
- RES-015 · FALLO · IA3.lineas_valoradas[2].codigo_partida_final: esperado 'CI.03A.7', obtenido None
- RES-015 · FALLO · IA3.lineas_valoradas[2].importe_calculado: esperado 104, obtenido None
- RES-015 · FALLO · IA3.lineas_valoradas[2].precio_source: esperado 'contrato_db', obtenido None
- RES-015 · FALLO · IA3.lineas_valoradas[2].precio_unitario_final: esperado 26, obtenido None
- RES-015 · FALLO · IA3.sinteticas_esperadas[2/@@NO_COMPARAR@@]: esperado {'cantidad': 4, 'codigo_partida': 'CI.03A.7', 'modifier_source': '@@NO_COMPARAR@@', 'num_linea_base': 2, 'precio_unitario': 4, 'rol_linea': '@@NO_COMPARAR@@'}, obtenido None (fila del ground truth que el sistema no ha producido)
- RES-016 · FALLO · IA3.lineas_valoradas[1].codigo_partida_final: esperado 'CI.03A.7', obtenido None
- RES-016 · FALLO · IA3.lineas_valoradas[1].importe_calculado: esperado 0, obtenido None
- RES-016 · FALLO · IA3.lineas_valoradas[1].precio_source: esperado 'oferta', obtenido None
- RES-016 · FALLO · IA3.lineas_valoradas[1].precio_unitario_final: esperado 90, obtenido None
- RES-017 · FALLO · IA3.lineas_valoradas[1].codigo_partida_final: esperado 'CI.03A.7', obtenido None
- RES-017 · FALLO · IA3.lineas_valoradas[1].importe_calculado: esperado 90, obtenido None
- RES-017 · FALLO · IA3.lineas_valoradas[1].precio_source: esperado 'contrato_db', obtenido None
- RES-017 · FALLO · IA3.lineas_valoradas[1].precio_unitario_final: esperado 90, obtenido None
- RES-017 · FALLO · IA3.lineas_valoradas[2].codigo_partida_final: esperado 'CI.03A.7', obtenido None
- RES-017 · FALLO · IA3.lineas_valoradas[2].importe_calculado: esperado 151.2, obtenido None
- RES-017 · FALLO · IA3.lineas_valoradas[2].precio_source: esperado 'contrato_db', obtenido None
- RES-017 · FALLO · IA3.lineas_valoradas[2].precio_unitario_final: esperado 70, obtenido None
- RES-018 · FALLO · IA3.lineas_valoradas[1].codigo_partida_final: esperado 'CI.03A.7', obtenido None
- RES-018 · FALLO · IA3.lineas_valoradas[1].importe_calculado: esperado 90, obtenido None
- RES-018 · FALLO · IA3.lineas_valoradas[1].precio_source: esperado 'contrato_db', obtenido None
- RES-018 · FALLO · IA3.lineas_valoradas[1].precio_unitario_final: esperado 90, obtenido None
- RES-018 · FALLO · IA3.lineas_valoradas[2].codigo_partida_final: esperado 'CI.03A.7', obtenido None
- RES-018 · FALLO · IA3.lineas_valoradas[2].importe_calculado: esperado 140.4, obtenido None
- RES-018 · FALLO · IA3.lineas_valoradas[2].precio_source: esperado 'contrato_db', obtenido None
- RES-018 · FALLO · IA3.lineas_valoradas[2].precio_unitario_final: esperado 26, obtenido None
- RES-018 · FALLO · IA3.sinteticas_esperadas[2/@@NO_COMPARAR@@]: esperado {'cantidad': 5.4, 'codigo_partida': 'CI.03A.7', 'modifier_source': '@@NO_COMPARAR@@', 'num_linea_base': 2, 'precio_unitario': 4, 'rol_linea': '@@NO_COMPARAR@@'}, obtenido None (fila del ground truth que el sistema no ha producido)
- RES-019 · FALLO · IA3.lineas_valoradas[1].codigo_partida_final: esperado 'CI.03A.7', obtenido None
- RES-019 · FALLO · IA3.lineas_valoradas[1].importe_calculado: esperado 90, obtenido None
- RES-019 · FALLO · IA3.lineas_valoradas[1].precio_source: esperado 'contrato_db', obtenido None
- RES-019 · FALLO · IA3.lineas_valoradas[1].precio_unitario_final: esperado 90, obtenido None
- RES-019 · FALLO · IA3.lineas_valoradas[2].codigo_partida_final: esperado 'CI.03A.7', obtenido None
- RES-019 · FALLO · IA3.lineas_valoradas[2].importe_calculado: esperado 10, obtenido None
- RES-019 · FALLO · IA3.lineas_valoradas[2].precio_source: esperado 'contrato_db', obtenido None
- RES-019 · FALLO · IA3.lineas_valoradas[2].precio_unitario_final: esperado 10, obtenido None
- RES-020 · FALLO · IA3.lineas_valoradas[1].codigo_partida_final: esperado '16.01.', obtenido None
- RES-020 · FALLO · IA3.lineas_valoradas[1].importe_calculado: esperado 184, obtenido None
- RES-020 · FALLO · IA3.lineas_valoradas[1].precio_source: esperado 'contrato_db', obtenido None
- RES-020 · FALLO · IA3.lineas_valoradas[1].precio_unitario_final: esperado 184, obtenido None
- RES-021 · FALLO · IA3.lineas_valoradas[1].codigo_partida_final: esperado '16.01.', obtenido None
- RES-021 · FALLO · IA3.lineas_valoradas[1].importe_calculado: esperado 0, obtenido None
- RES-021 · FALLO · IA3.lineas_valoradas[1].precio_source: esperado 'contrato_db', obtenido None
- RES-021 · FALLO · IA3.lineas_valoradas[1].precio_unitario_final: esperado 184, obtenido None
- RES-021 · FALLO · IA3.lineas_valoradas[2].codigo_partida_final: esperado '16.01.', obtenido None
- RES-021 · FALLO · IA3.lineas_valoradas[2].importe_calculado: esperado 184, obtenido None
- RES-021 · FALLO · IA3.lineas_valoradas[2].precio_source: esperado 'contrato_db', obtenido None
- RES-021 · FALLO · IA3.lineas_valoradas[2].precio_unitario_final: esperado 184, obtenido None

## IA4 · conciliación de líneas sin match (sv5) — ROJO

- Casos evaluados: 13 · omitidos: 46
- Proveedores invocados: gemini

| Caso | Estado | Fallos críticos | Avisos laxos | Motivo |
|---|---|---|---|---|
| ALQ-001 | OMITIDO | — | — | sin caso en el libro IA4 |
| COM-001 | ROJO | 1 | 0 | — |
| FER-001 | ROJO | 1 | 0 | — |
| FER-002 | ROJO | 8 | 0 | — |
| FER-003 | ROJO | 2 | 0 | — |
| GEN-001 | OMITIDO | — | — | sin caso en el libro IA4 |
| GEN-002 | ROJO | 3 | 5 | — |
| GEN-003 | OMITIDO | — | — | sin caso en el libro IA4 |
| GEN-004 | OMITIDO | — | — | sin caso en el libro IA4 |
| GEN-005 | OMITIDO | — | — | sin caso en el libro IA4 |
| GEN-006 | OMITIDO | — | — | sin caso en el libro IA4 |
| GEN-007 | OMITIDO | — | — | sin caso en el libro IA4 |
| GEN-008 | OMITIDO | — | — | sin caso en el libro IA4 |
| GEN-009 | OMITIDO | — | — | sin caso en el libro IA4 |
| GEN-010 | OMITIDO | — | — | sin caso en el libro IA4 |
| GRA-001 | OMITIDO | — | — | sin caso en el libro IA4 |
| GRA-002 | OMITIDO | — | — | sin caso en el libro IA4 |
| HOR-001 | OMITIDO | — | — | sin caso en el libro IA4 |
| HOR-002 | OMITIDO | — | — | sin caso en el libro IA4 |
| HOR-003 | OMITIDO | — | — | sin caso en el libro IA4 |
| HOR-004 | OMITIDO | — | — | sin caso en el libro IA4 |
| HOR-005 | ROJO | 3 | 2 | — |
| HOR-006 | OMITIDO | — | — | sin caso en el libro IA4 |
| HOR-007 | ROJO | 1 | 1 | — |
| HOR-008 | OMITIDO | — | — | sin caso en el libro IA4 |
| HOR-009 | OMITIDO | — | — | sin caso en el libro IA4 |
| HOR-010 | OMITIDO | — | — | sin caso en el libro IA4 |
| HOR-011 | OMITIDO | — | — | sin caso en el libro IA4 |
| HOR-012 | OMITIDO | — | — | sin caso en el libro IA4 |
| HOR-013 | OMITIDO | — | — | sin caso en el libro IA4 |
| HOR-014 | ROJO | 1 | 1 | — |
| HOR-015 | OMITIDO | — | — | sin caso en el libro IA4 |
| HOR-016 | OMITIDO | — | — | sin caso en el libro IA4 |
| HOR-017 | ROJO | 1 | 3 | — |
| MOR-001 | OMITIDO | — | — | sin caso en el libro IA4 |
| MOR-002 | ROJO | 2 | 0 | — |
| MOR-003 | ROJO | 2 | 0 | — |
| MOR-004 | ROJO | 1 | 1 | — |
| RES-001 | OMITIDO | — | — | sin caso en el libro IA4 |
| RES-002 | OMITIDO | — | — | sin caso en el libro IA4 |
| RES-003 | OMITIDO | — | — | sin caso en el libro IA4 |
| RES-004 | OMITIDO | — | — | sin caso en el libro IA4 |
| RES-005 | OMITIDO | — | — | sin caso en el libro IA4 |
| RES-006 | OMITIDO | — | — | sin caso en el libro IA4 |
| RES-007 | OMITIDO | — | — | sin caso en el libro IA4 |
| RES-008 | ROJO | 1 | 0 | — |
| RES-009 | OMITIDO | — | — | sin caso en el libro IA4 |
| RES-010 | OMITIDO | — | — | sin caso en el libro IA4 |
| RES-011 | OMITIDO | — | — | sin caso en el libro IA4 |
| RES-012 | OMITIDO | — | — | sin caso en el libro IA4 |
| RES-013 | OMITIDO | — | — | sin caso en el libro IA4 |
| RES-014 | OMITIDO | — | — | sin caso en el libro IA4 |
| RES-015 | OMITIDO | — | — | sin caso en el libro IA4 |
| RES-016 | OMITIDO | — | — | sin caso en el libro IA4 |
| RES-017 | OMITIDO | — | — | sin caso en el libro IA4 |
| RES-018 | OMITIDO | — | — | sin caso en el libro IA4 |
| RES-019 | OMITIDO | — | — | sin caso en el libro IA4 |
| RES-020 | OMITIDO | — | — | sin caso en el libro IA4 |
| RES-021 | OMITIDO | — | — | sin caso en el libro IA4 |

Detalle campo a campo:

- COM-001 · FALLO · IA4.conciliacion[1].precio_unitario_esperado: esperado 1.230578, obtenido None
- FER-001 · FALLO · IA4.conciliacion[1].precio_unitario_esperado: esperado 0.647, obtenido None
- FER-002 · FALLO · IA4.conciliacion[1].precio_unitario_esperado: esperado 0.543, obtenido None
- FER-002 · FALLO · IA4.conciliacion[2].precio_unitario_esperado: esperado 3.422, obtenido None
- FER-002 · FALLO · IA4.conciliacion[3].precio_unitario_esperado: esperado 7.726, obtenido None
- FER-002 · FALLO · IA4.conciliacion[4].precio_unitario_esperado: esperado 0.543, obtenido None
- FER-002 · FALLO · IA4.conciliacion[5].precio_unitario_esperado: esperado 3.422, obtenido None
- FER-002 · FALLO · IA4.conciliacion[6].precio_unitario_esperado: esperado 7.726, obtenido None
- FER-002 · FALLO · IA4.conciliacion[7].precio_unitario_esperado: esperado 5.497, obtenido None
- FER-002 · FALLO · IA4.conciliacion[8].precio_unitario_esperado: esperado 0.252, obtenido None
- FER-003 · FALLO · IA4.conciliacion[1].precio_unitario_esperado: esperado 95.481, obtenido None
- FER-003 · FALLO · IA4.conciliacion[2].precio_unitario_esperado: esperado 95.481, obtenido None
- GEN-002 · FALLO · IA4.conciliacion[6].precio_unitario_esperado: esperado 14.38, obtenido None
- GEN-002 · FALLO · IA4.conciliacion[7].precio_unitario_esperado: esperado 22.44, obtenido None
- GEN-002 · FALLO · IA4.conciliacion[8].precio_unitario_esperado: esperado 9, obtenido None
- GEN-002 · AVISO · IA4.conciliacion[+]: esperado None, obtenido {'num_linea': 1, 'concilia': False, 'linea_contrato_esperada': None, 'precio_unitario_esperado': None} (fila producida por el sistema que el ground truth no declara)
- GEN-002 · AVISO · IA4.conciliacion[+]: esperado None, obtenido {'num_linea': 2, 'concilia': False, 'linea_contrato_esperada': None, 'precio_unitario_esperado': None} (fila producida por el sistema que el ground truth no declara)
- GEN-002 · AVISO · IA4.conciliacion[+]: esperado None, obtenido {'num_linea': 3, 'concilia': False, 'linea_contrato_esperada': None, 'precio_unitario_esperado': None} (fila producida por el sistema que el ground truth no declara)
- GEN-002 · AVISO · IA4.conciliacion[+]: esperado None, obtenido {'num_linea': 4, 'concilia': False, 'linea_contrato_esperada': None, 'precio_unitario_esperado': None} (fila producida por el sistema que el ground truth no declara)
- GEN-002 · AVISO · IA4.conciliacion[+]: esperado None, obtenido {'num_linea': 5, 'concilia': False, 'linea_contrato_esperada': None, 'precio_unitario_esperado': None} (fila producida por el sistema que el ground truth no declara)
- HOR-005 · FALLO · IA4.conciliacion[3].precio_unitario_esperado: esperado 3, obtenido None
- HOR-005 · FALLO · IA4.conciliacion[4].precio_unitario_esperado: esperado 3, obtenido None
- HOR-005 · FALLO · IA4.conciliacion[5].precio_unitario_esperado: esperado 15, obtenido None
- HOR-005 · AVISO · IA4.conciliacion[+]: esperado None, obtenido {'num_linea': 1, 'concilia': False, 'linea_contrato_esperada': None, 'precio_unitario_esperado': None} (fila producida por el sistema que el ground truth no declara)
- HOR-005 · AVISO · IA4.conciliacion[+]: esperado None, obtenido {'num_linea': 2, 'concilia': False, 'linea_contrato_esperada': None, 'precio_unitario_esperado': None} (fila producida por el sistema que el ground truth no declara)
- HOR-007 · FALLO · IA4.conciliacion[2].precio_unitario_esperado: esperado 15, obtenido None
- HOR-007 · AVISO · IA4.conciliacion[+]: esperado None, obtenido {'num_linea': 1, 'concilia': False, 'linea_contrato_esperada': None, 'precio_unitario_esperado': None} (fila producida por el sistema que el ground truth no declara)
- HOR-014 · FALLO · IA4.conciliacion[2].precio_unitario_esperado: esperado 6, obtenido None
- HOR-014 · AVISO · IA4.conciliacion[+]: esperado None, obtenido {'num_linea': 1, 'concilia': False, 'linea_contrato_esperada': None, 'precio_unitario_esperado': None} (fila producida por el sistema que el ground truth no declara)
- HOR-017 · FALLO · IA4.conciliacion[4].precio_unitario_esperado: esperado 6, obtenido None
- HOR-017 · AVISO · IA4.conciliacion[+]: esperado None, obtenido {'num_linea': 1, 'concilia': False, 'linea_contrato_esperada': None, 'precio_unitario_esperado': None} (fila producida por el sistema que el ground truth no declara)
- HOR-017 · AVISO · IA4.conciliacion[+]: esperado None, obtenido {'num_linea': 2, 'concilia': False, 'linea_contrato_esperada': None, 'precio_unitario_esperado': None} (fila producida por el sistema que el ground truth no declara)
- HOR-017 · AVISO · IA4.conciliacion[+]: esperado None, obtenido {'num_linea': 3, 'concilia': False, 'linea_contrato_esperada': None, 'precio_unitario_esperado': None} (fila producida por el sistema que el ground truth no declara)
- MOR-002 · FALLO · IA4.conciliacion[1].precio_unitario_esperado: esperado 73.5, obtenido None
- MOR-002 · FALLO · IA4.conciliacion[2].precio_unitario_esperado: esperado 20, obtenido None
- MOR-003 · FALLO · IA4.conciliacion[1].precio_unitario_esperado: esperado 83.5, obtenido None
- MOR-003 · FALLO · IA4.conciliacion[2].precio_unitario_esperado: esperado 15, obtenido None
- MOR-004 · FALLO · IA4.conciliacion[1].precio_unitario_esperado: esperado 93, obtenido None
- MOR-004 · AVISO · IA4.conciliacion[+]: esperado None, obtenido {'num_linea': 2, 'concilia': False, 'linea_contrato_esperada': None, 'precio_unitario_esperado': None} (fila producida por el sistema que el ground truth no declara)
- RES-008 · FALLO · IA4.conciliacion[1].precio_unitario_esperado: esperado 173, obtenido None

## Extremo a extremo · RESULTADO_FINAL (sv5 → build de sv6) — ROJO

- Casos evaluados: 59 · omitidos: 0
- Proveedores invocados: gemini

| Caso | Estado | Fallos críticos | Avisos laxos | Motivo |
|---|---|---|---|---|
| ALQ-001 | ROJO | 15 | 0 | — |
| COM-001 | ROJO | 5 | 0 | — |
| FER-001 | ROJO | 3 | 0 | — |
| FER-002 | ROJO | 17 | 0 | — |
| FER-003 | ROJO | 7 | 0 | — |
| GEN-001 | ROJO | 6 | 0 | — |
| GEN-002 | ROJO | 29 | 0 | — |
| GEN-003 | ROJO | 11 | 0 | — |
| GEN-004 | ROJO | 6 | 0 | — |
| GEN-005 | ROJO | 11 | 0 | — |
| GEN-006 | ROJO | 6 | 0 | — |
| GEN-007 | ROJO | 3 | 0 | — |
| GEN-008 | ROJO | 6 | 0 | — |
| GEN-009 | ROJO | 6 | 0 | — |
| GEN-010 | ROJO | 6 | 0 | — |
| GRA-001 | ROJO | 6 | 0 | — |
| GRA-002 | ROJO | 6 | 0 | — |
| HOR-001 | ROJO | 7 | 0 | — |
| HOR-002 | ROJO | 8 | 0 | — |
| HOR-003 | ROJO | 7 | 0 | — |
| HOR-004 | ROJO | 29 | 0 | — |
| HOR-005 | ROJO | 26 | 0 | — |
| HOR-006 | ROJO | 6 | 0 | — |
| HOR-007 | ROJO | 11 | 0 | — |
| HOR-008 | ROJO | 7 | 0 | — |
| HOR-009 | ROJO | 17 | 0 | — |
| HOR-010 | ROJO | 13 | 0 | — |
| HOR-011 | ROJO | 7 | 0 | — |
| HOR-012 | ROJO | 13 | 0 | — |
| HOR-013 | ROJO | 7 | 0 | — |
| HOR-014 | ROJO | 11 | 0 | — |
| HOR-015 | ROJO | 18 | 0 | — |
| HOR-016 | ROJO | 7 | 0 | — |
| HOR-017 | ROJO | 22 | 0 | — |
| MOR-001 | ROJO | 7 | 0 | — |
| MOR-002 | ROJO | 10 | 0 | — |
| MOR-003 | ROJO | 9 | 0 | — |
| MOR-004 | ROJO | 11 | 0 | — |
| RES-001 | VERDE | 0 | 0 | — |
| RES-002 | VERDE | 0 | 0 | — |
| RES-003 | ROJO | 7 | 0 | — |
| RES-004 | ROJO | 7 | 0 | — |
| RES-005 | ROJO | 7 | 0 | — |
| RES-006 | VERDE | 0 | 0 | — |
| RES-007 | ROJO | 14 | 0 | — |
| RES-008 | ROJO | 5 | 0 | — |
| RES-009 | ROJO | 7 | 0 | — |
| RES-010 | ROJO | 12 | 0 | — |
| RES-011 | ROJO | 12 | 0 | — |
| RES-012 | ROJO | 11 | 0 | — |
| RES-013 | ROJO | 11 | 0 | — |
| RES-014 | ROJO | 12 | 0 | — |
| RES-015 | ROJO | 12 | 0 | — |
| RES-016 | ROJO | 5 | 0 | — |
| RES-017 | ROJO | 11 | 0 | — |
| RES-018 | ROJO | 12 | 0 | — |
| RES-019 | ROJO | 11 | 0 | — |
| RES-020 | ROJO | 6 | 0 | — |
| RES-021 | ROJO | 11 | 0 | — |

Detalle campo a campo:

- ALQ-001 · FALLO · FINAL.datos_generales[].total_valorado_esperado: esperado 1129, obtenido 0.0
- ALQ-001 · FALLO · FINAL.lineas[1].casa_con_contrato: esperado 'SI', obtenido False
- ALQ-001 · FALLO · FINAL.lineas[1].importe_final: esperado 170, obtenido None
- ALQ-001 · FALLO · FINAL.lineas[1].partida_final: esperado 'ALMACEN', obtenido None
- ALQ-001 · FALLO · FINAL.lineas[1].precio_source: esperado 'contrato_db', obtenido None
- ALQ-001 · FALLO · FINAL.lineas[1].precio_unitario_final: esperado 170, obtenido None
- ALQ-001 · FALLO · FINAL.lineas[2].casa_con_contrato: esperado 'SI', obtenido False
- ALQ-001 · FALLO · FINAL.lineas[2].importe_final: esperado 805, obtenido None
- ALQ-001 · FALLO · FINAL.lineas[2].partida_final: esperado 'ALMACEN', obtenido None
- ALQ-001 · FALLO · FINAL.lineas[2].precio_source: esperado 'contrato_db', obtenido None
- ALQ-001 · FALLO · FINAL.lineas[2].precio_unitario_final: esperado 115, obtenido None
- ALQ-001 · FALLO · FINAL.lineas[3].importe_final: esperado 154, obtenido None
- ALQ-001 · FALLO · FINAL.lineas[3].partida_final: esperado 'ALMACEN', obtenido None
- ALQ-001 · FALLO · FINAL.lineas[3].precio_source: esperado 'oferta', obtenido None
- ALQ-001 · FALLO · FINAL.lineas[3].precio_unitario_final: esperado 157, obtenido None
- COM-001 · FALLO · FINAL.datos_generales[].total_valorado_esperado: esperado 984.46, obtenido 0.0
- COM-001 · FALLO · FINAL.lineas[1].importe_final: esperado 984.46, obtenido None
- COM-001 · FALLO · FINAL.lineas[1].partida_final: esperado 'CI.4.1', obtenido None
- COM-001 · FALLO · FINAL.lineas[1].precio_source: esperado 'deducido', obtenido None
- COM-001 · FALLO · FINAL.lineas[1].precio_unitario_final: esperado 1.230578, obtenido None
- FER-001 · FALLO · FINAL.datos_generales[].total_valorado_esperado: esperado 19.41, obtenido 32.35
- FER-001 · FALLO · FINAL.lineas[1].importe_final: esperado 19.41, obtenido 32.35
- FER-001 · FALLO · FINAL.lineas[1].partida_final: esperado 'CI.4.18', obtenido None
- FER-002 · FALLO · FINAL.datos_generales[].total_valorado_esperado: esperado 139.65, obtenido 232.77
- FER-002 · FALLO · FINAL.lineas[1].importe_final: esperado 17.59, obtenido 29.32
- FER-002 · FALLO · FINAL.lineas[1].partida_final: esperado 'P4.36.01', obtenido None
- FER-002 · FALLO · FINAL.lineas[2].importe_final: esperado 10.27, obtenido 17.11
- FER-002 · FALLO · FINAL.lineas[2].partida_final: esperado 'P4.36.01', obtenido None
- FER-002 · FALLO · FINAL.lineas[3].importe_final: esperado 27.81, obtenido 46.36
- FER-002 · FALLO · FINAL.lineas[3].partida_final: esperado 'P4.36.01', obtenido None
- FER-002 · FALLO · FINAL.lineas[4].importe_final: esperado 17.59, obtenido 29.32
- FER-002 · FALLO · FINAL.lineas[4].partida_final: esperado 'P5.36.01', obtenido None
- FER-002 · FALLO · FINAL.lineas[5].importe_final: esperado 10.27, obtenido 17.11
- FER-002 · FALLO · FINAL.lineas[5].partida_final: esperado 'P5.36.01', obtenido None
- FER-002 · FALLO · FINAL.lineas[6].importe_final: esperado 27.81, obtenido 46.36
- FER-002 · FALLO · FINAL.lineas[6].partida_final: esperado 'P5.36.01', obtenido None
- FER-002 · FALLO · FINAL.lineas[7].importe_final: esperado 13.19, obtenido 21.99
- FER-002 · FALLO · FINAL.lineas[7].partida_final: esperado 'CI.4.18', obtenido None
- FER-002 · FALLO · FINAL.lineas[8].importe_final: esperado 15.12, obtenido 25.2
- FER-002 · FALLO · FINAL.lineas[8].partida_final: esperado 'CI.4.18', obtenido None
- FER-003 · FALLO · FINAL.datos_generales[].total_valorado_esperado: esperado 66, obtenido 229.15
- FER-003 · FALLO · FINAL.lineas[1].partida_final: esperado 'CI.4.18', obtenido None
- FER-003 · FALLO · FINAL.lineas[1].precio_unitario_final: esperado 95.481, obtenido 57.2875
- FER-003 · FALLO · FINAL.lineas[2].importe_final: esperado -163.15, obtenido None
- FER-003 · FALLO · FINAL.lineas[2].partida_final: esperado 'CI.4.18', obtenido None
- FER-003 · FALLO · FINAL.lineas[2].precio_source: esperado 'deducido', obtenido None
- FER-003 · FALLO · FINAL.lineas[2].precio_unitario_final: esperado 95.481, obtenido None
- GEN-001 · FALLO · FINAL.datos_generales[].total_valorado_esperado: esperado 3393, obtenido 0.0
- GEN-001 · FALLO · FINAL.lineas[1].casa_con_contrato: esperado 'SI', obtenido False
- GEN-001 · FALLO · FINAL.lineas[1].importe_final: esperado 3393, obtenido None
- GEN-001 · FALLO · FINAL.lineas[1].partida_final: esperado 'P4.22.02.03.01.07', obtenido None
- GEN-001 · FALLO · FINAL.lineas[1].precio_source: esperado 'contrato_db', obtenido None
- GEN-001 · FALLO · FINAL.lineas[1].precio_unitario_final: esperado 9, obtenido None
- GEN-002 · FALLO · FINAL.datos_generales[].total_valorado_esperado: esperado 20111.4, obtenido 12035.58
- GEN-002 · FALLO · FINAL.lineas[1].casa_con_contrato: esperado 'SI', obtenido False
- GEN-002 · FALLO · FINAL.lineas[1].importe_final: esperado 621.22, obtenido None
- GEN-002 · FALLO · FINAL.lineas[1].partida_final: esperado 'P5.09.03', obtenido None
- GEN-002 · FALLO · FINAL.lineas[1].precio_source: esperado 'contrato_db', obtenido None
- GEN-002 · FALLO · FINAL.lineas[1].precio_unitario_final: esperado 14.38, obtenido None
- GEN-002 · FALLO · FINAL.lineas[2].casa_con_contrato: esperado 'SI', obtenido False
- GEN-002 · FALLO · FINAL.lineas[2].importe_final: esperado 5590.94, obtenido None
- GEN-002 · FALLO · FINAL.lineas[2].partida_final: esperado 'P5.09.03', obtenido None
- GEN-002 · FALLO · FINAL.lineas[2].precio_source: esperado 'contrato_db', obtenido None
- GEN-002 · FALLO · FINAL.lineas[2].precio_unitario_final: esperado 14.38, obtenido None
- GEN-002 · FALLO · FINAL.lineas[3].casa_con_contrato: esperado 'SI', obtenido False
- GEN-002 · FALLO · FINAL.lineas[3].importe_final: esperado 621.22, obtenido None
- GEN-002 · FALLO · FINAL.lineas[3].partida_final: esperado 'P5.09.03', obtenido None
- GEN-002 · FALLO · FINAL.lineas[3].precio_source: esperado 'contrato_db', obtenido None
- GEN-002 · FALLO · FINAL.lineas[3].precio_unitario_final: esperado 14.38, obtenido None
- GEN-002 · FALLO · FINAL.lineas[4].casa_con_contrato: esperado 'SI', obtenido False
- GEN-002 · FALLO · FINAL.lineas[4].importe_final: esperado 621.22, obtenido None
- GEN-002 · FALLO · FINAL.lineas[4].partida_final: esperado 'P5.09.04', obtenido None
- GEN-002 · FALLO · FINAL.lineas[4].precio_source: esperado 'contrato_db', obtenido None
- GEN-002 · FALLO · FINAL.lineas[4].precio_unitario_final: esperado 14.38, obtenido None
- GEN-002 · FALLO · FINAL.lineas[5].casa_con_contrato: esperado 'SI', obtenido False
- GEN-002 · FALLO · FINAL.lineas[5].importe_final: esperado 621.22, obtenido None
- GEN-002 · FALLO · FINAL.lineas[5].partida_final: esperado 'P5.09.05', obtenido None
- GEN-002 · FALLO · FINAL.lineas[5].precio_source: esperado 'contrato_db', obtenido None
- GEN-002 · FALLO · FINAL.lineas[5].precio_unitario_final: esperado 14.38, obtenido None
- GEN-002 · FALLO · FINAL.lineas[6].partida_final: esperado 'P5.09.06', obtenido None
- GEN-002 · FALLO · FINAL.lineas[7].partida_final: esperado 'P5.38.07.02', obtenido None
- GEN-002 · FALLO · FINAL.lineas[8].partida_final: esperado 'ALMACEN', obtenido None
- GEN-003 · FALLO · FINAL.datos_generales[].total_valorado_esperado: esperado 521.07, obtenido 0.0
- GEN-003 · FALLO · FINAL.lineas[1].casa_con_contrato: esperado 'SI', obtenido False
- GEN-003 · FALLO · FINAL.lineas[1].importe_final: esperado 341.67, obtenido None
- GEN-003 · FALLO · FINAL.lineas[1].partida_final: esperado 'P4.09.04', obtenido None
- GEN-003 · FALLO · FINAL.lineas[1].precio_source: esperado 'contrato_db', obtenido None
- GEN-003 · FALLO · FINAL.lineas[1].precio_unitario_final: esperado 14.38, obtenido None
- GEN-003 · FALLO · FINAL.lineas[2].casa_con_contrato: esperado 'SI', obtenido False
- GEN-003 · FALLO · FINAL.lineas[2].importe_final: esperado 179.4, obtenido None
- GEN-003 · FALLO · FINAL.lineas[2].partida_final: esperado 'P4.08.21', obtenido None
- GEN-003 · FALLO · FINAL.lineas[2].precio_source: esperado 'contrato_db', obtenido None
- GEN-003 · FALLO · FINAL.lineas[2].precio_unitario_final: esperado 2.76, obtenido None
- GEN-004 · FALLO · FINAL.datos_generales[].total_valorado_esperado: esperado 3755.7, obtenido 0.0
- GEN-004 · FALLO · FINAL.lineas[1].casa_con_contrato: esperado 'SI', obtenido False
- GEN-004 · FALLO · FINAL.lineas[1].importe_final: esperado 3755.7, obtenido None
- GEN-004 · FALLO · FINAL.lineas[1].partida_final: esperado '11.02.01', obtenido None
- GEN-004 · FALLO · FINAL.lineas[1].precio_source: esperado 'contrato_db', obtenido None
- GEN-004 · FALLO · FINAL.lineas[1].precio_unitario_final: esperado 41.73, obtenido None
- GEN-005 · FALLO · FINAL.datos_generales[].total_valorado_esperado: esperado 505.24, obtenido 0.0
- GEN-005 · FALLO · FINAL.lineas[1].casa_con_contrato: esperado 'SI', obtenido False
- GEN-005 · FALLO · FINAL.lineas[1].importe_final: esperado 219.48, obtenido None
- GEN-005 · FALLO · FINAL.lineas[1].partida_final: esperado '11.02.01', obtenido None
- GEN-005 · FALLO · FINAL.lineas[1].precio_source: esperado 'contrato_db', obtenido None
- GEN-005 · FALLO · FINAL.lineas[1].precio_unitario_final: esperado 109.74, obtenido None
- GEN-005 · FALLO · FINAL.lineas[2].casa_con_contrato: esperado 'SI', obtenido False
- GEN-005 · FALLO · FINAL.lineas[2].importe_final: esperado 285.76, obtenido None
- GEN-005 · FALLO · FINAL.lineas[2].partida_final: esperado '11.01.11', obtenido None
- GEN-005 · FALLO · FINAL.lineas[2].precio_source: esperado 'contrato_db', obtenido None
- GEN-005 · FALLO · FINAL.lineas[2].precio_unitario_final: esperado 71.44, obtenido None
- GEN-006 · FALLO · FINAL.datos_generales[].total_valorado_esperado: esperado 721.68, obtenido 0.0
- GEN-006 · FALLO · FINAL.lineas[1].casa_con_contrato: esperado 'SI', obtenido False
- GEN-006 · FALLO · FINAL.lineas[1].importe_final: esperado 721.68, obtenido None
- GEN-006 · FALLO · FINAL.lineas[1].partida_final: esperado '11.01.11', obtenido None
- GEN-006 · FALLO · FINAL.lineas[1].precio_source: esperado 'contrato_db', obtenido None
- GEN-006 · FALLO · FINAL.lineas[1].precio_unitario_final: esperado 120.28, obtenido None
- GEN-007 · FALLO · FINAL.lineas[1].casa_con_contrato: esperado 'SI', obtenido False
- GEN-007 · FALLO · FINAL.lineas[1].partida_final: esperado '11.01.11', obtenido None
- GEN-007 · FALLO · FINAL.lineas[1].precio_source: esperado 'contrato_db', obtenido None
- GEN-008 · FALLO · FINAL.datos_generales[].total_valorado_esperado: esperado 142.88, obtenido 0.0
- GEN-008 · FALLO · FINAL.lineas[1].casa_con_contrato: esperado 'SI', obtenido False
- GEN-008 · FALLO · FINAL.lineas[1].importe_final: esperado 142.88, obtenido None
- GEN-008 · FALLO · FINAL.lineas[1].partida_final: esperado '11.01.11', obtenido None
- GEN-008 · FALLO · FINAL.lineas[1].precio_source: esperado 'contrato_db', obtenido None
- GEN-008 · FALLO · FINAL.lineas[1].precio_unitario_final: esperado 71.44, obtenido None
- GEN-009 · FALLO · FINAL.datos_generales[].total_valorado_esperado: esperado 17021.03, obtenido 0.0
- GEN-009 · FALLO · FINAL.lineas[1].casa_con_contrato: esperado 'SI', obtenido False
- GEN-009 · FALLO · FINAL.lineas[1].importe_final: esperado 17021.03, obtenido None
- GEN-009 · FALLO · FINAL.lineas[1].partida_final: esperado '05.01.22', obtenido None
- GEN-009 · FALLO · FINAL.lineas[1].precio_source: esperado 'contrato_db', obtenido None
- GEN-009 · FALLO · FINAL.lineas[1].precio_unitario_final: esperado 16.79, obtenido None
- GEN-010 · FALLO · FINAL.datos_generales[].total_valorado_esperado: esperado 174.96, obtenido 0.0
- GEN-010 · FALLO · FINAL.lineas[1].casa_con_contrato: esperado 'SI', obtenido False
- GEN-010 · FALLO · FINAL.lineas[1].importe_final: esperado 174.96, obtenido None
- GEN-010 · FALLO · FINAL.lineas[1].partida_final: esperado 'ALMACEN', obtenido None
- GEN-010 · FALLO · FINAL.lineas[1].precio_source: esperado 'contrato_db', obtenido None
- GEN-010 · FALLO · FINAL.lineas[1].precio_unitario_final: esperado 2.43, obtenido None
- GRA-001 · FALLO · FINAL.datos_generales[].total_valorado_esperado: esperado 390.99, obtenido 0.0
- GRA-001 · FALLO · FINAL.lineas[1].casa_con_contrato: esperado 'SI', obtenido False
- GRA-001 · FALLO · FINAL.lineas[1].importe_final: esperado 390.99, obtenido None
- GRA-001 · FALLO · FINAL.lineas[1].partida_final: esperado 'P5.22.01.03.07', obtenido None
- GRA-001 · FALLO · FINAL.lineas[1].precio_source: esperado 'contrato_db', obtenido None
- GRA-001 · FALLO · FINAL.lineas[1].precio_unitario_final: esperado 12.87, obtenido None
- GRA-002 · FALLO · FINAL.datos_generales[].total_valorado_esperado: esperado 385.59, obtenido 0.0
- GRA-002 · FALLO · FINAL.lineas[1].casa_con_contrato: esperado 'SI', obtenido False
- GRA-002 · FALLO · FINAL.lineas[1].importe_final: esperado 385.59, obtenido None
- GRA-002 · FALLO · FINAL.lineas[1].partida_final: esperado 'P5.03.04', obtenido None
- GRA-002 · FALLO · FINAL.lineas[1].precio_source: esperado 'contrato_db', obtenido None
- GRA-002 · FALLO · FINAL.lineas[1].precio_unitario_final: esperado 12.87, obtenido None
- HOR-001 · FALLO · FINAL.datos_generales[].total_valorado_esperado: esperado 980.1, obtenido 0.0
- HOR-001 · FALLO · FINAL.lineas[1].casa_con_contrato: esperado 'SI', obtenido False
- HOR-001 · FALLO · FINAL.lineas[1].importe_final: esperado 899.1, obtenido None
- HOR-001 · FALLO · FINAL.lineas[1].partida_final: esperado 'P5.03.09', obtenido None
- HOR-001 · FALLO · FINAL.lineas[1].precio_source: esperado 'contrato_db', obtenido None
- HOR-001 · FALLO · FINAL.lineas[1].precio_unitario_final: esperado 99.9, obtenido None
- HOR-001 · FALLO · FINAL.lineas_anadidas[1]: esperado {'cantidad': 9, 'importe': 81, 'num_linea_base': 1, 'partida': 'P5.03.09', 'precio_unitario': 9}, obtenido None (fila del ground truth que el sistema no ha producido)
- HOR-002 · FALLO · FINAL.datos_generales[].total_valorado_esperado: esperado 475.6, obtenido 0.0
- HOR-002 · FALLO · FINAL.lineas[1].casa_con_contrato: esperado 'SI', obtenido False
- HOR-002 · FALLO · FINAL.lineas[1].importe_final: esperado 399.6, obtenido None
- HOR-002 · FALLO · FINAL.lineas[1].partida_final: esperado 'P5.03.04', obtenido None
- HOR-002 · FALLO · FINAL.lineas[1].precio_source: esperado 'contrato_db', obtenido None
- HOR-002 · FALLO · FINAL.lineas[1].precio_unitario_final: esperado 99.9, obtenido None
- HOR-002 · FALLO · FINAL.lineas_anadidas[1]: esperado {'cantidad': 2, 'importe': 40, 'num_linea_base': 1, 'partida': 'P5.03.04', 'precio_unitario': 20}, obtenido None (fila del ground truth que el sistema no ha producido)
- HOR-002 · FALLO · FINAL.lineas_anadidas[1]: esperado {'cantidad': 4, 'importe': 36, 'num_linea_base': 1, 'partida': 'P5.03.04', 'precio_unitario': 9}, obtenido None (fila del ground truth que el sistema no ha producido)
- HOR-003 · FALLO · FINAL.datos_generales[].total_valorado_esperado: esperado 871.2, obtenido 0.0
- HOR-003 · FALLO · FINAL.lineas[1].casa_con_contrato: esperado 'SI', obtenido False
- HOR-003 · FALLO · FINAL.lineas[1].importe_final: esperado 799.2, obtenido None
- HOR-003 · FALLO · FINAL.lineas[1].partida_final: esperado 'P4.03.05', obtenido None
- HOR-003 · FALLO · FINAL.lineas[1].precio_source: esperado 'contrato_db', obtenido None
- HOR-003 · FALLO · FINAL.lineas[1].precio_unitario_final: esperado 99.9, obtenido None
- HOR-003 · FALLO · FINAL.lineas_anadidas[1]: esperado {'cantidad': 8, 'importe': 72, 'num_linea_base': 1, 'partida': 'P4.03.05', 'precio_unitario': 9}, obtenido None (fila del ground truth que el sistema no ha producido)
- HOR-004 · FALLO · FINAL.datos_generales[].total_valorado_esperado: esperado 1302.5, obtenido 0.0
- HOR-004 · FALLO · FINAL.lineas[1].casa_con_contrato: esperado 'SI', obtenido False
- HOR-004 · FALLO · FINAL.lineas[1].importe_final: esperado 965, obtenido None
- HOR-004 · FALLO · FINAL.lineas[1].partida_final: esperado '03.03.07', obtenido None
- HOR-004 · FALLO · FINAL.lineas[1].precio_source: esperado 'contrato_db', obtenido None
- HOR-004 · FALLO · FINAL.lineas[1].precio_unitario_final: esperado 96.5, obtenido None
- HOR-004 · FALLO · FINAL.lineas[2].casa_con_contrato: esperado 'SI', obtenido False
- HOR-004 · FALLO · FINAL.lineas[2].importe_final: esperado 50, obtenido None
- HOR-004 · FALLO · FINAL.lineas[2].partida_final: esperado '03.03.07', obtenido None
- HOR-004 · FALLO · FINAL.lineas[2].precio_source: esperado 'contrato_db', obtenido None
- HOR-004 · FALLO · FINAL.lineas[2].precio_unitario_final: esperado 5, obtenido None
- HOR-004 · FALLO · FINAL.lineas[3].casa_con_contrato: esperado 'SI', obtenido False
- HOR-004 · FALLO · FINAL.lineas[3].importe_final: esperado 40, obtenido None
- HOR-004 · FALLO · FINAL.lineas[3].partida_final: esperado '03.03.07', obtenido None
- HOR-004 · FALLO · FINAL.lineas[3].precio_source: esperado 'contrato_db', obtenido None
- HOR-004 · FALLO · FINAL.lineas[3].precio_unitario_final: esperado 4, obtenido None
- HOR-004 · FALLO · FINAL.lineas[4].casa_con_contrato: esperado 'SI', obtenido False
- HOR-004 · FALLO · FINAL.lineas[4].importe_final: esperado 40, obtenido None
- HOR-004 · FALLO · FINAL.lineas[4].partida_final: esperado '03.03.07', obtenido None
- HOR-004 · FALLO · FINAL.lineas[4].precio_source: esperado 'contrato_db', obtenido None
- HOR-004 · FALLO · FINAL.lineas[4].precio_unitario_final: esperado 4, obtenido None
- HOR-004 · FALLO · FINAL.lineas[5].casa_con_contrato: esperado 'SI', obtenido False
- HOR-004 · FALLO · FINAL.lineas[5].importe_final: esperado 60, obtenido None
- HOR-004 · FALLO · FINAL.lineas[5].partida_final: esperado '03.03.07', obtenido None
- HOR-004 · FALLO · FINAL.lineas[5].precio_source: esperado 'contrato_db', obtenido None
- HOR-004 · FALLO · FINAL.lineas[5].precio_unitario_final: esperado 6, obtenido None
- HOR-004 · FALLO · FINAL.lineas_anadidas[1]: esperado {'cantidad': 10, 'importe': 30, 'num_linea_base': 1, 'partida': '03.03.07', 'precio_unitario': 3}, obtenido None (fila del ground truth que el sistema no ha producido)
- HOR-004 · FALLO · FINAL.lineas_anadidas[1]: esperado {'cantidad': 10, 'importe': 110, 'num_linea_base': 1, 'partida': '03.03.07', 'precio_unitario': 11}, obtenido None (fila del ground truth que el sistema no ha producido)
- HOR-004 · FALLO · FINAL.lineas_anadidas[5]: esperado {'cantidad': 10, 'importe': 7.5, 'num_linea_base': 5, 'partida': '03.03.07', 'precio_unitario': 0.75}, obtenido None (fila del ground truth que el sistema no ha producido)
- HOR-005 · FALLO · FINAL.datos_generales[].total_valorado_esperado: esperado 429, obtenido 0.0
- HOR-005 · FALLO · FINAL.lineas[1].casa_con_contrato: esperado 'SI', obtenido False
- HOR-005 · FALLO · FINAL.lineas[1].importe_final: esperado 339, obtenido None
- HOR-005 · FALLO · FINAL.lineas[1].partida_final: esperado 'almacen', obtenido None
- HOR-005 · FALLO · FINAL.lineas[1].precio_source: esperado 'contrato_db', obtenido None
- HOR-005 · FALLO · FINAL.lineas[1].precio_unitario_final: esperado 84.75, obtenido None
- HOR-005 · FALLO · FINAL.lineas[2].casa_con_contrato: esperado 'SI', obtenido False
- HOR-005 · FALLO · FINAL.lineas[2].importe_final: esperado 14, obtenido None
- HOR-005 · FALLO · FINAL.lineas[2].partida_final: esperado 'almacen', obtenido None
- HOR-005 · FALLO · FINAL.lineas[2].precio_source: esperado 'contrato_db', obtenido None
- HOR-005 · FALLO · FINAL.lineas[2].precio_unitario_final: esperado 3.5, obtenido None
- HOR-005 · FALLO · FINAL.lineas[3].importe_final: esperado 12, obtenido None
- HOR-005 · FALLO · FINAL.lineas[3].partida_final: esperado 'almacen', obtenido None
- HOR-005 · FALLO · FINAL.lineas[3].precio_source: esperado 'oferta', obtenido None
- HOR-005 · FALLO · FINAL.lineas[3].precio_unitario_final: esperado 3, obtenido None
- HOR-005 · FALLO · FINAL.lineas[4].importe_final: esperado 12, obtenido None
- HOR-005 · FALLO · FINAL.lineas[4].partida_final: esperado 'almacen', obtenido None
- HOR-005 · FALLO · FINAL.lineas[4].precio_source: esperado 'oferta', obtenido None
- HOR-005 · FALLO · FINAL.lineas[4].precio_unitario_final: esperado 3, obtenido None
- HOR-005 · FALLO · FINAL.lineas[5].importe_final: esperado 30, obtenido None
- HOR-005 · FALLO · FINAL.lineas[5].partida_final: esperado 'almacen', obtenido None
- HOR-005 · FALLO · FINAL.lineas[5].precio_source: esperado 'oferta', obtenido None
- HOR-005 · FALLO · FINAL.lineas[5].precio_unitario_final: esperado 15, obtenido None
- HOR-005 · FALLO · FINAL.lineas_anadidas[4]: esperado {'cantidad': 4, 'importe': 22, 'num_linea_base': 4, 'partida': 'almacen', 'precio_unitario': 5.5}, obtenido None (fila del ground truth que el sistema no ha producido)
- HOR-005 · FALLO · FINAL.lineas_anadidas[+]: esperado None, obtenido {'num_linea_base': 1, 'cantidad': 4.0, 'precio_unitario': None, 'partida': None, 'importe': None, 'descripcion_linea': 'INCREMENTO POR HORMIGÓN FRATASADO'} (fila producida por el sistema que el ground truth no declara)
- HOR-005 · FALLO · FINAL.lineas_anadidas[+]: esperado None, obtenido {'num_linea_base': 1, 'cantidad': 4.0, 'precio_unitario': None, 'partida': None, 'importe': None, 'descripcion_linea': 'INCREMENTO POR FIBRA DE POLIPROPILENO'} (fila producida por el sistema que el ground truth no declara)
- HOR-006 · FALLO · FINAL.datos_generales[].total_valorado_esperado: esperado 593.25, obtenido 0.0
- HOR-006 · FALLO · FINAL.lineas[1].casa_con_contrato: esperado 'SI', obtenido False
- HOR-006 · FALLO · FINAL.lineas[1].importe_final: esperado 593.25, obtenido None
- HOR-006 · FALLO · FINAL.lineas[1].partida_final: esperado 5.01, obtenido None
- HOR-006 · FALLO · FINAL.lineas[1].precio_source: esperado 'contrato_db', obtenido None
- HOR-006 · FALLO · FINAL.lineas[1].precio_unitario_final: esperado 84.75, obtenido None
- HOR-007 · FALLO · FINAL.datos_generales[].total_valorado_esperado: esperado 466.25, obtenido 0.0
- HOR-007 · FALLO · FINAL.lineas[1].casa_con_contrato: esperado 'SI', obtenido False
- HOR-007 · FALLO · FINAL.lineas[1].importe_final: esperado 423.75, obtenido None
- HOR-007 · FALLO · FINAL.lineas[1].partida_final: esperado 5.04, obtenido None
- HOR-007 · FALLO · FINAL.lineas[1].precio_source: esperado 'contrato_db', obtenido None
- HOR-007 · FALLO · FINAL.lineas[1].precio_unitario_final: esperado 84.75, obtenido None
- HOR-007 · FALLO · FINAL.lineas[2].importe_final: esperado 15, obtenido None
- HOR-007 · FALLO · FINAL.lineas[2].partida_final: esperado 5.04, obtenido None
- HOR-007 · FALLO · FINAL.lineas[2].precio_source: esperado 'oferta', obtenido None
- HOR-007 · FALLO · FINAL.lineas[2].precio_unitario_final: esperado 15, obtenido None
- HOR-007 · FALLO · FINAL.lineas_anadidas[1]: esperado {'cantidad': 5, 'importe': 27.5, 'num_linea_base': 1, 'partida': 5.04, 'precio_unitario': 5.5}, obtenido None (fila del ground truth que el sistema no ha producido)
- HOR-008 · FALLO · FINAL.datos_generales[].total_valorado_esperado: esperado 638.4, obtenido 0.0
- HOR-008 · FALLO · FINAL.lineas[1].casa_con_contrato: esperado 'SI', obtenido False
- HOR-008 · FALLO · FINAL.lineas[1].importe_final: esperado 608, obtenido None
- HOR-008 · FALLO · FINAL.lineas[1].partida_final: esperado '32.02.01.01', obtenido None
- HOR-008 · FALLO · FINAL.lineas[1].precio_source: esperado 'contrato_db', obtenido None
- HOR-008 · FALLO · FINAL.lineas[1].precio_unitario_final: esperado 76, obtenido None
- HOR-008 · FALLO · FINAL.lineas_anadidas[1]: esperado {'cantidad': 8, 'importe': 30.4, 'num_linea_base': 1, 'partida': '32.02.01.01', 'precio_unitario': 3.8}, obtenido None (fila del ground truth que el sistema no ha producido)
- HOR-009 · FALLO · FINAL.datos_generales[].total_valorado_esperado: esperado 91.5, obtenido 0.0
- HOR-009 · FALLO · FINAL.lineas[1].casa_con_contrato: esperado 'SI', obtenido False
- HOR-009 · FALLO · FINAL.lineas[1].importe_final: esperado 80, obtenido None
- HOR-009 · FALLO · FINAL.lineas[1].partida_final: esperado '32.03.02', obtenido None
- HOR-009 · FALLO · FINAL.lineas[1].precio_source: esperado 'contrato_db', obtenido None
- HOR-009 · FALLO · FINAL.lineas[1].precio_unitario_final: esperado 80, obtenido None
- HOR-009 · FALLO · FINAL.lineas[2].casa_con_contrato: esperado 'SI', obtenido False
- HOR-009 · FALLO · FINAL.lineas[2].importe_final: esperado 3.5, obtenido None
- HOR-009 · FALLO · FINAL.lineas[2].partida_final: esperado '32.03.02', obtenido None
- HOR-009 · FALLO · FINAL.lineas[2].precio_source: esperado 'contrato_db', obtenido None
- HOR-009 · FALLO · FINAL.lineas[2].precio_unitario_final: esperado 3.5, obtenido None
- HOR-009 · FALLO · FINAL.lineas[3].casa_con_contrato: esperado 'SI', obtenido False
- HOR-009 · FALLO · FINAL.lineas[3].importe_final: esperado 3, obtenido None
- HOR-009 · FALLO · FINAL.lineas[3].partida_final: esperado '32.03.02', obtenido None
- HOR-009 · FALLO · FINAL.lineas[3].precio_source: esperado 'contrato_db', obtenido None
- HOR-009 · FALLO · FINAL.lineas[3].precio_unitario_final: esperado 3, obtenido None
- HOR-009 · FALLO · FINAL.lineas_anadidas[3]: esperado {'cantidad': 8, 'importe': 5, 'num_linea_base': 3, 'partida': '32.03.02', 'precio_unitario': 5}, obtenido None (fila del ground truth que el sistema no ha producido)
- HOR-010 · FALLO · FINAL.datos_generales[].total_valorado_esperado: esperado 746, obtenido 0.0
- HOR-010 · FALLO · FINAL.lineas[1].casa_con_contrato: esperado 'SI', obtenido False
- HOR-010 · FALLO · FINAL.lineas[1].importe_final: esperado 678, obtenido None
- HOR-010 · FALLO · FINAL.lineas[1].partida_final: esperado 5.02, obtenido None
- HOR-010 · FALLO · FINAL.lineas[1].precio_source: esperado 'contrato_db', obtenido None
- HOR-010 · FALLO · FINAL.lineas[1].precio_unitario_final: esperado 84.75, obtenido None
- HOR-010 · FALLO · FINAL.lineas[2].casa_con_contrato: esperado 'SI', obtenido False
- HOR-010 · FALLO · FINAL.lineas[2].importe_final: esperado 24, obtenido None
- HOR-010 · FALLO · FINAL.lineas[2].partida_final: esperado 5.02, obtenido None
- HOR-010 · FALLO · FINAL.lineas[2].precio_source: esperado 'contrato_db', obtenido None
- HOR-010 · FALLO · FINAL.lineas[2].precio_unitario_final: esperado 3, obtenido None
- HOR-010 · FALLO · FINAL.lineas_anadidas[2]: esperado {'cantidad': 8, 'importe': 44, 'num_linea_base': 2, 'partida': 5.02, 'precio_unitario': 5.5}, obtenido None (fila del ground truth que el sistema no ha producido)
- HOR-010 · FALLO · FINAL.lineas_anadidas[+]: esperado None, obtenido {'num_linea_base': 1, 'cantidad': 8.0, 'precio_unitario': None, 'partida': None, 'importe': None, 'descripcion_linea': 'INCREMENTO POR CONSISTENCIA FLUIDA'} (fila producida por el sistema que el ground truth no declara)
- HOR-011 · FALLO · FINAL.datos_generales[].total_valorado_esperado: esperado 660.52, obtenido 0.0
- HOR-011 · FALLO · FINAL.lineas[1].casa_con_contrato: esperado 'SI', obtenido False
- HOR-011 · FALLO · FINAL.lineas[1].importe_final: esperado 618.8, obtenido None
- HOR-011 · FALLO · FINAL.lineas[1].partida_final: esperado '03.01.01', obtenido None
- HOR-011 · FALLO · FINAL.lineas[1].precio_source: esperado 'contrato_db', obtenido None
- HOR-011 · FALLO · FINAL.lineas[1].precio_unitario_final: esperado 88.4, obtenido None
- HOR-011 · FALLO · FINAL.lineas_anadidas[1]: esperado {'cantidad': 7, 'importe': 41.72, 'num_linea_base': 1, 'partida': '03.01.01', 'precio_unitario': 5.96}, obtenido None (fila del ground truth que el sistema no ha producido)
- HOR-012 · FALLO · FINAL.datos_generales[].total_valorado_esperado: esperado 891, obtenido 0.0
- HOR-012 · FALLO · FINAL.lineas[1].casa_con_contrato: esperado 'SI', obtenido False
- HOR-012 · FALLO · FINAL.lineas[1].importe_final: esperado 803.7, obtenido None
- HOR-012 · FALLO · FINAL.lineas[1].partida_final: esperado 42.01, obtenido None
- HOR-012 · FALLO · FINAL.lineas[1].precio_source: esperado 'contrato_db', obtenido None
- HOR-012 · FALLO · FINAL.lineas[1].precio_unitario_final: esperado 89.3, obtenido None
- HOR-012 · FALLO · FINAL.lineas[2].casa_con_contrato: esperado 'SI', obtenido False
- HOR-012 · FALLO · FINAL.lineas[2].importe_final: esperado 27, obtenido None
- HOR-012 · FALLO · FINAL.lineas[2].partida_final: esperado 42.01, obtenido None
- HOR-012 · FALLO · FINAL.lineas[2].precio_source: esperado 'contrato_db', obtenido None
- HOR-012 · FALLO · FINAL.lineas[2].precio_unitario_final: esperado 3, obtenido None
- HOR-012 · FALLO · FINAL.lineas_anadidas[2]: esperado {'cantidad': 9, 'importe': 60.3, 'num_linea_base': 2, 'partida': 42.01, 'precio_unitario': 6.7}, obtenido None (fila del ground truth que el sistema no ha producido)
- HOR-012 · FALLO · FINAL.lineas_anadidas[+]: esperado None, obtenido {'num_linea_base': 1, 'cantidad': 9.0, 'precio_unitario': None, 'partida': None, 'importe': None, 'descripcion_linea': 'INCREMENTO POR CONSISTENCIA FLUIDA'} (fila producida por el sistema que el ground truth no declara)
- HOR-013 · FALLO · FINAL.datos_generales[].total_valorado_esperado: esperado 768, obtenido 0.0
- HOR-013 · FALLO · FINAL.lineas[1].casa_con_contrato: esperado 'SI', obtenido False
- HOR-013 · FALLO · FINAL.lineas[1].importe_final: esperado 714.4, obtenido None
- HOR-013 · FALLO · FINAL.lineas[1].partida_final: esperado '38.01.03', obtenido None
- HOR-013 · FALLO · FINAL.lineas[1].precio_source: esperado 'contrato_db', obtenido None
- HOR-013 · FALLO · FINAL.lineas[1].precio_unitario_final: esperado 89.3, obtenido None
- HOR-013 · FALLO · FINAL.lineas_anadidas[1]: esperado {'cantidad': 8, 'importe': 53.6, 'num_linea_base': 1, 'partida': '38.01.03', 'precio_unitario': 6.7}, obtenido None (fila del ground truth que el sistema no ha producido)
- HOR-014 · FALLO · FINAL.datos_generales[].total_valorado_esperado: esperado 768, obtenido 0.0
- HOR-014 · FALLO · FINAL.lineas[1].casa_con_contrato: esperado 'SI', obtenido False
- HOR-014 · FALLO · FINAL.lineas[1].importe_final: esperado 714.4, obtenido None
- HOR-014 · FALLO · FINAL.lineas[1].partida_final: esperado '38.01.03', obtenido None
- HOR-014 · FALLO · FINAL.lineas[1].precio_source: esperado 'contrato_db', obtenido None
- HOR-014 · FALLO · FINAL.lineas[1].precio_unitario_final: esperado 89.3, obtenido None
- HOR-014 · FALLO · FINAL.lineas[2].importe_final: esperado 0, obtenido None
- HOR-014 · FALLO · FINAL.lineas[2].partida_final: esperado '38.01.03', obtenido None
- HOR-014 · FALLO · FINAL.lineas[2].precio_source: esperado 'oferta', obtenido None
- HOR-014 · FALLO · FINAL.lineas[2].precio_unitario_final: esperado 6, obtenido None
- HOR-014 · FALLO · FINAL.lineas_anadidas[1]: esperado {'cantidad': 5, 'importe': 53.6, 'num_linea_base': 1, 'partida': '38.01.03', 'precio_unitario': 6.7}, obtenido None (fila del ground truth que el sistema no ha producido)
- HOR-015 · FALLO · FINAL.datos_generales[].total_valorado_esperado: esperado 714, obtenido 0.0
- HOR-015 · FALLO · FINAL.lineas[1].casa_con_contrato: esperado 'SI', obtenido False
- HOR-015 · FALLO · FINAL.lineas[1].importe_final: esperado 625.1, obtenido None
- HOR-015 · FALLO · FINAL.lineas[1].partida_final: esperado 42.01, obtenido None
- HOR-015 · FALLO · FINAL.lineas[1].precio_source: esperado 'contrato_db', obtenido None
- HOR-015 · FALLO · FINAL.lineas[1].precio_unitario_final: esperado 89.3, obtenido None
- HOR-015 · FALLO · FINAL.lineas[2].casa_con_contrato: esperado 'SI', obtenido False
- HOR-015 · FALLO · FINAL.lineas[2].importe_final: esperado 21, obtenido None
- HOR-015 · FALLO · FINAL.lineas[2].partida_final: esperado 42.01, obtenido None
- HOR-015 · FALLO · FINAL.lineas[2].precio_source: esperado 'contrato_db', obtenido None
- HOR-015 · FALLO · FINAL.lineas[2].precio_unitario_final: esperado 3, obtenido None
- HOR-015 · FALLO · FINAL.lineas[3].casa_con_contrato: esperado 'SI', obtenido False
- HOR-015 · FALLO · FINAL.lineas[3].importe_final: esperado 21, obtenido None
- HOR-015 · FALLO · FINAL.lineas[3].partida_final: esperado 42.01, obtenido None
- HOR-015 · FALLO · FINAL.lineas[3].precio_source: esperado 'contrato_db', obtenido None
- HOR-015 · FALLO · FINAL.lineas[3].precio_unitario_final: esperado 3, obtenido None
- HOR-015 · FALLO · FINAL.lineas_anadidas[3]: esperado {'cantidad': 7, 'importe': 46.9, 'num_linea_base': 3, 'partida': 42.01, 'precio_unitario': 6.7}, obtenido None (fila del ground truth que el sistema no ha producido)
- HOR-015 · FALLO · FINAL.lineas_anadidas[+]: esperado None, obtenido {'num_linea_base': 1, 'cantidad': 7.0, 'precio_unitario': None, 'partida': None, 'importe': None, 'descripcion_linea': 'INCREMENTO POR CONSISTENCIA FLUIDA'} (fila producida por el sistema que el ground truth no declara)
- HOR-016 · FALLO · FINAL.datos_generales[].total_valorado_esperado: esperado 844.8, obtenido 0.0
- HOR-016 · FALLO · FINAL.lineas[1].casa_con_contrato: esperado 'SI', obtenido False
- HOR-016 · FALLO · FINAL.lineas[1].importe_final: esperado 785.8, obtenido None
- HOR-016 · FALLO · FINAL.lineas[1].partida_final: esperado '38.01.01', obtenido None
- HOR-016 · FALLO · FINAL.lineas[1].precio_source: esperado 'contrato_db', obtenido None
- HOR-016 · FALLO · FINAL.lineas[1].precio_unitario_final: esperado 78.58, obtenido None
- HOR-016 · FALLO · FINAL.lineas_anadidas[1]: esperado {'cantidad': 10, 'importe': 59, 'num_linea_base': 1, 'partida': '38.01.01', 'precio_unitario': 5.9}, obtenido None (fila del ground truth que el sistema no ha producido)
- HOR-017 · FALLO · FINAL.datos_generales[].total_valorado_esperado: esperado 324, obtenido 0.0
- HOR-017 · FALLO · FINAL.lineas[1].casa_con_contrato: esperado 'SI', obtenido False
- HOR-017 · FALLO · FINAL.lineas[1].importe_final: esperado 267.9, obtenido None
- HOR-017 · FALLO · FINAL.lineas[1].partida_final: esperado 42.01, obtenido None
- HOR-017 · FALLO · FINAL.lineas[1].precio_source: esperado 'contrato_db', obtenido None
- HOR-017 · FALLO · FINAL.lineas[1].precio_unitario_final: esperado 89.3, obtenido None
- HOR-017 · FALLO · FINAL.lineas[2].casa_con_contrato: esperado 'SI', obtenido False
- HOR-017 · FALLO · FINAL.lineas[2].importe_final: esperado 9, obtenido None
- HOR-017 · FALLO · FINAL.lineas[2].partida_final: esperado 42.01, obtenido None
- HOR-017 · FALLO · FINAL.lineas[2].precio_source: esperado 'contrato_db', obtenido None
- HOR-017 · FALLO · FINAL.lineas[2].precio_unitario_final: esperado 3, obtenido None
- HOR-017 · FALLO · FINAL.lineas[3].casa_con_contrato: esperado 'SI', obtenido False
- HOR-017 · FALLO · FINAL.lineas[3].importe_final: esperado 9, obtenido None
- HOR-017 · FALLO · FINAL.lineas[3].partida_final: esperado 42.01, obtenido None
- HOR-017 · FALLO · FINAL.lineas[3].precio_source: esperado 'contrato_db', obtenido None
- HOR-017 · FALLO · FINAL.lineas[3].precio_unitario_final: esperado 3, obtenido None
- HOR-017 · FALLO · FINAL.lineas[4].importe_final: esperado 18, obtenido None
- HOR-017 · FALLO · FINAL.lineas[4].partida_final: esperado 42.01, obtenido None
- HOR-017 · FALLO · FINAL.lineas[4].precio_source: esperado 'oferta', obtenido None
- HOR-017 · FALLO · FINAL.lineas[4].precio_unitario_final: esperado 6, obtenido None
- HOR-017 · FALLO · FINAL.lineas_anadidas[3]: esperado {'cantidad': 3, 'importe': 20.1, 'num_linea_base': 3, 'partida': 42.01, 'precio_unitario': 6.7}, obtenido None (fila del ground truth que el sistema no ha producido)
- HOR-017 · FALLO · FINAL.lineas_anadidas[+]: esperado None, obtenido {'num_linea_base': 1, 'cantidad': 3.0, 'precio_unitario': None, 'partida': None, 'importe': None, 'descripcion_linea': 'INCREMENTO POR CONSISTENCIA FLUIDA'} (fila producida por el sistema que el ground truth no declara)
- MOR-001 · FALLO · FINAL.datos_generales[].total_valorado_esperado: esperado 567, obtenido 0.0
- MOR-001 · FALLO · FINAL.lineas[1].casa_con_contrato: esperado 'SI', obtenido False
- MOR-001 · FALLO · FINAL.lineas[1].importe_final: esperado 504, obtenido None
- MOR-001 · FALLO · FINAL.lineas[1].partida_final: esperado 'P5.14.01.02.02', obtenido None
- MOR-001 · FALLO · FINAL.lineas[1].precio_source: esperado 'contrato_db', obtenido None
- MOR-001 · FALLO · FINAL.lineas[1].precio_unitario_final: esperado 72, obtenido None
- MOR-001 · FALLO · FINAL.lineas_anadidas[1]: esperado {'cantidad': 7, 'importe': 63, 'num_linea_base': 1, 'partida': 'P5.14.01.02.02', 'precio_unitario': 9}, obtenido None (fila del ground truth que el sistema no ha producido)
- MOR-002 · FALLO · FINAL.datos_generales[].total_valorado_esperado: esperado 307.5, obtenido 0.0
- MOR-002 · FALLO · FINAL.lineas[1].importe_final: esperado 220.5, obtenido None
- MOR-002 · FALLO · FINAL.lineas[1].partida_final: esperado 'P4.14.01.02.02', obtenido None
- MOR-002 · FALLO · FINAL.lineas[1].precio_source: esperado 'oferta', obtenido None
- MOR-002 · FALLO · FINAL.lineas[1].precio_unitario_final: esperado 73.5, obtenido None
- MOR-002 · FALLO · FINAL.lineas[2].importe_final: esperado 60, obtenido None
- MOR-002 · FALLO · FINAL.lineas[2].partida_final: esperado 'P4.14.01.02.02', obtenido None
- MOR-002 · FALLO · FINAL.lineas[2].precio_source: esperado 'oferta', obtenido None
- MOR-002 · FALLO · FINAL.lineas[2].precio_unitario_final: esperado 20, obtenido None
- MOR-002 · FALLO · FINAL.lineas_anadidas[1]: esperado {'cantidad': 3, 'importe': 27, 'num_linea_base': 1, 'partida': 'P4.14.01.02.02', 'precio_unitario': 9}, obtenido None (fila del ground truth que el sistema no ha producido)
- MOR-003 · FALLO · FINAL.datos_generales[].total_valorado_esperado: esperado 280.5, obtenido 0.0
- MOR-003 · FALLO · FINAL.lineas[1].importe_final: esperado 250.5, obtenido None
- MOR-003 · FALLO · FINAL.lineas[1].partida_final: esperado 'almacen', obtenido None
- MOR-003 · FALLO · FINAL.lineas[1].precio_source: esperado 'oferta', obtenido None
- MOR-003 · FALLO · FINAL.lineas[1].precio_unitario_final: esperado 83.5, obtenido None
- MOR-003 · FALLO · FINAL.lineas[2].importe_final: esperado 30, obtenido None
- MOR-003 · FALLO · FINAL.lineas[2].partida_final: esperado 'almacen', obtenido None
- MOR-003 · FALLO · FINAL.lineas[2].precio_source: esperado 'oferta', obtenido None
- MOR-003 · FALLO · FINAL.lineas[2].precio_unitario_final: esperado 15, obtenido None
- MOR-004 · FALLO · FINAL.datos_generales[].total_valorado_esperado: esperado 920.7, obtenido 0.0
- MOR-004 · FALLO · FINAL.lineas[1].importe_final: esperado 837, obtenido None
- MOR-004 · FALLO · FINAL.lineas[1].partida_final: esperado '10.03.04', obtenido None
- MOR-004 · FALLO · FINAL.lineas[1].precio_source: esperado 'oferta', obtenido None
- MOR-004 · FALLO · FINAL.lineas[1].precio_unitario_final: esperado 93, obtenido None
- MOR-004 · FALLO · FINAL.lineas[2].casa_con_contrato: esperado 'SI', obtenido False
- MOR-004 · FALLO · FINAL.lineas[2].importe_final: esperado 36, obtenido None
- MOR-004 · FALLO · FINAL.lineas[2].partida_final: esperado '10.03.04', obtenido None
- MOR-004 · FALLO · FINAL.lineas[2].precio_source: esperado 'contrato_db', obtenido None
- MOR-004 · FALLO · FINAL.lineas[2].precio_unitario_final: esperado 4, obtenido None
- MOR-004 · FALLO · FINAL.lineas_anadidas[2]: esperado {'cantidad': 9, 'importe': 47.7, 'num_linea_base': 2, 'partida': '10.03.04', 'precio_unitario': 5.3}, obtenido None (fila del ground truth que el sistema no ha producido)
- RES-003 · FALLO · FINAL.datos_generales[].total_valorado_esperado: esperado 171, obtenido 222.0
- RES-003 · FALLO · FINAL.lineas[2].casa_con_contrato: esperado 'SI', obtenido False
- RES-003 · FALLO · FINAL.lineas[2].importe_final: esperado 51, obtenido None
- RES-003 · FALLO · FINAL.lineas[2].partida_final: esperado 'CI.03A.7', obtenido None
- RES-003 · FALLO · FINAL.lineas[2].precio_source: esperado 'contrato_db', obtenido None
- RES-003 · FALLO · FINAL.lineas[2].precio_unitario_final: esperado 51, obtenido None
- RES-003 · FALLO · FINAL.lineas_anadidas[+]: esperado None, obtenido {'num_linea_base': 2, 'cantidad': 1.0, 'precio_unitario': 51.0, 'partida': None, 'importe': 51.0, 'descripcion_linea': 'INCREMENTO LER 170802'} (fila producida por el sistema que el ground truth no declara)
- RES-004 · FALLO · FINAL.datos_generales[].total_valorado_esperado: esperado 210, obtenido 300.0
- RES-004 · FALLO · FINAL.lineas[2].casa_con_contrato: esperado 'SI', obtenido False
- RES-004 · FALLO · FINAL.lineas[2].importe_final: esperado 90, obtenido None
- RES-004 · FALLO · FINAL.lineas[2].partida_final: esperado 'CI.03A.7', obtenido None
- RES-004 · FALLO · FINAL.lineas[2].precio_source: esperado 'contrato_db', obtenido None
- RES-004 · FALLO · FINAL.lineas[2].precio_unitario_final: esperado 90, obtenido None
- RES-004 · FALLO · FINAL.lineas_anadidas[+]: esperado None, obtenido {'num_linea_base': 2, 'cantidad': 1.0, 'precio_unitario': 90.0, 'partida': None, 'importe': 90.0, 'descripcion_linea': 'INCREMENTO LER 170604'} (fila producida por el sistema que el ground truth no declara)
- RES-005 · FALLO · FINAL.datos_generales[].total_valorado_esperado: esperado 210, obtenido 300.0
- RES-005 · FALLO · FINAL.lineas[2].casa_con_contrato: esperado 'SI', obtenido False
- RES-005 · FALLO · FINAL.lineas[2].importe_final: esperado 90, obtenido None
- RES-005 · FALLO · FINAL.lineas[2].partida_final: esperado 'CI.03A.7', obtenido None
- RES-005 · FALLO · FINAL.lineas[2].precio_source: esperado 'contrato_db', obtenido None
- RES-005 · FALLO · FINAL.lineas[2].precio_unitario_final: esperado 90, obtenido None
- RES-005 · FALLO · FINAL.lineas_anadidas[+]: esperado None, obtenido {'num_linea_base': 2, 'cantidad': 1.0, 'precio_unitario': 90.0, 'partida': None, 'importe': 90.0, 'descripcion_linea': 'INCREMENTO LER 170604'} (fila producida por el sistema que el ground truth no declara)
- RES-007 · FALLO · FINAL.datos_generales[].total_valorado_esperado: esperado 260, obtenido 272.0
- RES-007 · FALLO · FINAL.lineas[1].casa_con_contrato: esperado 'NO', obtenido True
- RES-007 · FALLO · FINAL.lineas[1].importe_final: esperado 183, obtenido 272.0
- RES-007 · FALLO · FINAL.lineas[1].linea_contrato: esperado None, obtenido 'C1'
- RES-007 · FALLO · FINAL.lineas[1].precio_source: esperado 'oferta', obtenido 'contrato_db'
- RES-007 · FALLO · FINAL.lineas[1].precio_unitario_final: esperado 183, obtenido 136.0
- RES-007 · FALLO · FINAL.lineas[2].importe_final: esperado 77, obtenido None
- RES-007 · FALLO · FINAL.lineas[2].partida_final: esperado 'CI.03A.7', obtenido None
- RES-007 · FALLO · FINAL.lineas[2].precio_source: esperado 'oferta', obtenido None
- RES-007 · FALLO · FINAL.lineas[2].precio_unitario_final: esperado 77, obtenido None
- RES-007 · FALLO · FINAL.lineas_anadidas[1].cantidad: esperado 1, obtenido 2.0
- RES-007 · FALLO · FINAL.lineas_anadidas[1].importe: esperado 77, obtenido None
- RES-007 · FALLO · FINAL.lineas_anadidas[1].precio_unitario: esperado 77, obtenido None
- RES-007 · FALLO · FINAL.lineas_anadidas[+]: esperado None, obtenido {'num_linea_base': 2, 'cantidad': 2.0, 'precio_unitario': None, 'partida': None, 'importe': None, 'descripcion_linea': 'INCREMENTO LER 170802'} (fila producida por el sistema que el ground truth no declara)
- RES-008 · FALLO · FINAL.datos_generales[].total_valorado_esperado: esperado 173, obtenido 0.0
- RES-008 · FALLO · FINAL.lineas[1].importe_final: esperado 173, obtenido None
- RES-008 · FALLO · FINAL.lineas[1].partida_final: esperado 32.01, obtenido None
- RES-008 · FALLO · FINAL.lineas[1].precio_source: esperado 'oferta', obtenido None
- RES-008 · FALLO · FINAL.lineas[1].precio_unitario_final: esperado 173, obtenido None
- RES-009 · FALLO · FINAL.datos_generales[].total_valorado_esperado: esperado 163, obtenido 0.0
- RES-009 · FALLO · FINAL.lineas[1].casa_con_contrato: esperado 'SI', obtenido False
- RES-009 · FALLO · FINAL.lineas[1].importe_final: esperado 157, obtenido None
- RES-009 · FALLO · FINAL.lineas[1].partida_final: esperado 32.01, obtenido None
- RES-009 · FALLO · FINAL.lineas[1].precio_source: esperado 'contrato_db', obtenido None
- RES-009 · FALLO · FINAL.lineas[1].precio_unitario_final: esperado 157, obtenido None
- RES-009 · FALLO · FINAL.lineas_anadidas[1]: esperado {'cantidad': 1, 'importe': 6, 'num_linea_base': 1, 'partida': 32.01, 'precio_unitario': 6}, obtenido None (fila del ground truth que el sistema no ha producido)
- RES-010 · FALLO · FINAL.datos_generales[].total_valorado_esperado: esperado 180, obtenido 0.0
- RES-010 · FALLO · FINAL.lineas[1].casa_con_contrato: esperado 'SI', obtenido False
- RES-010 · FALLO · FINAL.lineas[1].importe_final: esperado 90, obtenido None
- RES-010 · FALLO · FINAL.lineas[1].partida_final: esperado 'CI.03A.7', obtenido None
- RES-010 · FALLO · FINAL.lineas[1].precio_source: esperado 'contrato_db', obtenido None
- RES-010 · FALLO · FINAL.lineas[1].precio_unitario_final: esperado 90, obtenido None
- RES-010 · FALLO · FINAL.lineas[2].casa_con_contrato: esperado 'SI', obtenido False
- RES-010 · FALLO · FINAL.lineas[2].importe_final: esperado 78, obtenido None
- RES-010 · FALLO · FINAL.lineas[2].partida_final: esperado 'CI.03A.7', obtenido None
- RES-010 · FALLO · FINAL.lineas[2].precio_source: esperado 'contrato_db', obtenido None
- RES-010 · FALLO · FINAL.lineas[2].precio_unitario_final: esperado 26, obtenido None
- RES-010 · FALLO · FINAL.lineas_anadidas[2]: esperado {'cantidad': 3, 'importe': 12, 'num_linea_base': 2, 'partida': 'CI.03A.7', 'precio_unitario': 4}, obtenido None (fila del ground truth que el sistema no ha producido)
- RES-011 · FALLO · FINAL.datos_generales[].total_valorado_esperado: esperado 188.4, obtenido 0.0
- RES-011 · FALLO · FINAL.lineas[1].casa_con_contrato: esperado 'SI', obtenido False
- RES-011 · FALLO · FINAL.lineas[1].importe_final: esperado 90, obtenido None
- RES-011 · FALLO · FINAL.lineas[1].partida_final: esperado 'CI.03A.7', obtenido None
- RES-011 · FALLO · FINAL.lineas[1].precio_source: esperado 'contrato_db', obtenido None
- RES-011 · FALLO · FINAL.lineas[1].precio_unitario_final: esperado 90, obtenido None
- RES-011 · FALLO · FINAL.lineas[2].casa_con_contrato: esperado 'SI', obtenido False
- RES-011 · FALLO · FINAL.lineas[2].importe_final: esperado 85.28, obtenido None
- RES-011 · FALLO · FINAL.lineas[2].partida_final: esperado 'CI.03A.7', obtenido None
- RES-011 · FALLO · FINAL.lineas[2].precio_source: esperado 'contrato_db', obtenido None
- RES-011 · FALLO · FINAL.lineas[2].precio_unitario_final: esperado 26, obtenido None
- RES-011 · FALLO · FINAL.lineas_anadidas[2]: esperado {'cantidad': 3.28, 'importe': 13.12, 'num_linea_base': 2, 'partida': 'CI.03A.7', 'precio_unitario': 4}, obtenido None (fila del ground truth que el sistema no ha producido)
- RES-012 · FALLO · FINAL.datos_generales[].total_valorado_esperado: esperado 256.6, obtenido 0.0
- RES-012 · FALLO · FINAL.lineas[1].casa_con_contrato: esperado 'SI', obtenido False
- RES-012 · FALLO · FINAL.lineas[1].importe_final: esperado 90, obtenido None
- RES-012 · FALLO · FINAL.lineas[1].partida_final: esperado 'CI.03A.7', obtenido None
- RES-012 · FALLO · FINAL.lineas[1].precio_source: esperado 'contrato_db', obtenido None
- RES-012 · FALLO · FINAL.lineas[1].precio_unitario_final: esperado 90, obtenido None
- RES-012 · FALLO · FINAL.lineas[2].casa_con_contrato: esperado 'SI', obtenido False
- RES-012 · FALLO · FINAL.lineas[2].importe_final: esperado 166.6, obtenido None
- RES-012 · FALLO · FINAL.lineas[2].partida_final: esperado 'CI.03A.7', obtenido None
- RES-012 · FALLO · FINAL.lineas[2].precio_source: esperado 'contrato_db', obtenido None
- RES-012 · FALLO · FINAL.lineas[2].precio_unitario_final: esperado 70, obtenido None
- RES-013 · FALLO · FINAL.datos_generales[].total_valorado_esperado: esperado 210.4, obtenido 0.0
- RES-013 · FALLO · FINAL.lineas[1].casa_con_contrato: esperado 'SI', obtenido False
- RES-013 · FALLO · FINAL.lineas[1].importe_final: esperado 90, obtenido None
- RES-013 · FALLO · FINAL.lineas[1].partida_final: esperado 'CI.03A.7', obtenido None
- RES-013 · FALLO · FINAL.lineas[1].precio_source: esperado 'contrato_db', obtenido None
- RES-013 · FALLO · FINAL.lineas[1].precio_unitario_final: esperado 90, obtenido None
- RES-013 · FALLO · FINAL.lineas[2].casa_con_contrato: esperado 'SI', obtenido False
- RES-013 · FALLO · FINAL.lineas[2].importe_final: esperado 120.4, obtenido None
- RES-013 · FALLO · FINAL.lineas[2].partida_final: esperado 'CI.03A.7', obtenido None
- RES-013 · FALLO · FINAL.lineas[2].precio_source: esperado 'contrato_db', obtenido None
- RES-013 · FALLO · FINAL.lineas[2].precio_unitario_final: esperado 70, obtenido None
- RES-014 · FALLO · FINAL.datos_generales[].total_valorado_esperado: esperado 273, obtenido 0.0
- RES-014 · FALLO · FINAL.lineas[1].casa_con_contrato: esperado 'SI', obtenido False
- RES-014 · FALLO · FINAL.lineas[1].importe_final: esperado 90, obtenido None
- RES-014 · FALLO · FINAL.lineas[1].partida_final: esperado 'CI.03A.7', obtenido None
- RES-014 · FALLO · FINAL.lineas[1].precio_source: esperado 'contrato_db', obtenido None
- RES-014 · FALLO · FINAL.lineas[1].precio_unitario_final: esperado 90, obtenido None
- RES-014 · FALLO · FINAL.lineas[2].casa_con_contrato: esperado 'SI', obtenido False
- RES-014 · FALLO · FINAL.lineas[2].importe_final: esperado 158.6, obtenido None
- RES-014 · FALLO · FINAL.lineas[2].partida_final: esperado 'CI.03A.7', obtenido None
- RES-014 · FALLO · FINAL.lineas[2].precio_source: esperado 'contrato_db', obtenido None
- RES-014 · FALLO · FINAL.lineas[2].precio_unitario_final: esperado 26, obtenido None
- RES-014 · FALLO · FINAL.lineas_anadidas[2]: esperado {'cantidad': 6.1, 'importe': 24.4, 'num_linea_base': 2, 'partida': 'CI.03A.7', 'precio_unitario': 4}, obtenido None (fila del ground truth que el sistema no ha producido)
- RES-015 · FALLO · FINAL.datos_generales[].total_valorado_esperado: esperado 210, obtenido 0.0
- RES-015 · FALLO · FINAL.lineas[1].casa_con_contrato: esperado 'SI', obtenido False
- RES-015 · FALLO · FINAL.lineas[1].importe_final: esperado 90, obtenido None
- RES-015 · FALLO · FINAL.lineas[1].partida_final: esperado 'CI.03A.7', obtenido None
- RES-015 · FALLO · FINAL.lineas[1].precio_source: esperado 'contrato_db', obtenido None
- RES-015 · FALLO · FINAL.lineas[1].precio_unitario_final: esperado 90, obtenido None
- RES-015 · FALLO · FINAL.lineas[2].casa_con_contrato: esperado 'SI', obtenido False
- RES-015 · FALLO · FINAL.lineas[2].importe_final: esperado 104, obtenido None
- RES-015 · FALLO · FINAL.lineas[2].partida_final: esperado 'CI.03A.7', obtenido None
- RES-015 · FALLO · FINAL.lineas[2].precio_source: esperado 'contrato_db', obtenido None
- RES-015 · FALLO · FINAL.lineas[2].precio_unitario_final: esperado 26, obtenido None
- RES-015 · FALLO · FINAL.lineas_anadidas[2]: esperado {'cantidad': 4, 'importe': 16, 'num_linea_base': 2, 'partida': 'CI.03A.7', 'precio_unitario': 4}, obtenido None (fila del ground truth que el sistema no ha producido)
- RES-016 · FALLO · FINAL.lineas[1].casa_con_contrato: esperado 'SI', obtenido False
- RES-016 · FALLO · FINAL.lineas[1].importe_final: esperado 0, obtenido None
- RES-016 · FALLO · FINAL.lineas[1].partida_final: esperado 'CI.03A.7', obtenido None
- RES-016 · FALLO · FINAL.lineas[1].precio_source: esperado 'oferta', obtenido None
- RES-016 · FALLO · FINAL.lineas[1].precio_unitario_final: esperado 90, obtenido None
- RES-017 · FALLO · FINAL.datos_generales[].total_valorado_esperado: esperado 241.2, obtenido 0.0
- RES-017 · FALLO · FINAL.lineas[1].casa_con_contrato: esperado 'SI', obtenido False
- RES-017 · FALLO · FINAL.lineas[1].importe_final: esperado 90, obtenido None
- RES-017 · FALLO · FINAL.lineas[1].partida_final: esperado 'CI.03A.7', obtenido None
- RES-017 · FALLO · FINAL.lineas[1].precio_source: esperado 'contrato_db', obtenido None
- RES-017 · FALLO · FINAL.lineas[1].precio_unitario_final: esperado 90, obtenido None
- RES-017 · FALLO · FINAL.lineas[2].casa_con_contrato: esperado 'SI', obtenido False
- RES-017 · FALLO · FINAL.lineas[2].importe_final: esperado 151.2, obtenido None
- RES-017 · FALLO · FINAL.lineas[2].partida_final: esperado 'CI.03A.7', obtenido None
- RES-017 · FALLO · FINAL.lineas[2].precio_source: esperado 'contrato_db', obtenido None
- RES-017 · FALLO · FINAL.lineas[2].precio_unitario_final: esperado 70, obtenido None
- RES-018 · FALLO · FINAL.datos_generales[].total_valorado_esperado: esperado 252, obtenido 0.0
- RES-018 · FALLO · FINAL.lineas[1].casa_con_contrato: esperado 'SI', obtenido False
- RES-018 · FALLO · FINAL.lineas[1].importe_final: esperado 90, obtenido None
- RES-018 · FALLO · FINAL.lineas[1].partida_final: esperado 'CI.03A.7', obtenido None
- RES-018 · FALLO · FINAL.lineas[1].precio_source: esperado 'contrato_db', obtenido None
- RES-018 · FALLO · FINAL.lineas[1].precio_unitario_final: esperado 90, obtenido None
- RES-018 · FALLO · FINAL.lineas[2].casa_con_contrato: esperado 'SI', obtenido False
- RES-018 · FALLO · FINAL.lineas[2].importe_final: esperado 140.4, obtenido None
- RES-018 · FALLO · FINAL.lineas[2].partida_final: esperado 'CI.03A.7', obtenido None
- RES-018 · FALLO · FINAL.lineas[2].precio_source: esperado 'contrato_db', obtenido None
- RES-018 · FALLO · FINAL.lineas[2].precio_unitario_final: esperado 26, obtenido None
- RES-018 · FALLO · FINAL.lineas_anadidas[2]: esperado {'cantidad': 5.4, 'importe': 21.6, 'num_linea_base': 2, 'partida': 'CI.03A.7', 'precio_unitario': 4}, obtenido None (fila del ground truth que el sistema no ha producido)
- RES-019 · FALLO · FINAL.datos_generales[].total_valorado_esperado: esperado 100, obtenido 0.0
- RES-019 · FALLO · FINAL.lineas[1].casa_con_contrato: esperado 'SI', obtenido False
- RES-019 · FALLO · FINAL.lineas[1].importe_final: esperado 90, obtenido None
- RES-019 · FALLO · FINAL.lineas[1].partida_final: esperado 'CI.03A.7', obtenido None
- RES-019 · FALLO · FINAL.lineas[1].precio_source: esperado 'contrato_db', obtenido None
- RES-019 · FALLO · FINAL.lineas[1].precio_unitario_final: esperado 90, obtenido None
- RES-019 · FALLO · FINAL.lineas[2].casa_con_contrato: esperado 'SI', obtenido False
- RES-019 · FALLO · FINAL.lineas[2].importe_final: esperado 10, obtenido None
- RES-019 · FALLO · FINAL.lineas[2].partida_final: esperado 'CI.03A.7', obtenido None
- RES-019 · FALLO · FINAL.lineas[2].precio_source: esperado 'contrato_db', obtenido None
- RES-019 · FALLO · FINAL.lineas[2].precio_unitario_final: esperado 10, obtenido None
- RES-020 · FALLO · FINAL.datos_generales[].total_valorado_esperado: esperado 184, obtenido 0.0
- RES-020 · FALLO · FINAL.lineas[1].casa_con_contrato: esperado 'SI', obtenido False
- RES-020 · FALLO · FINAL.lineas[1].importe_final: esperado 184, obtenido None
- RES-020 · FALLO · FINAL.lineas[1].partida_final: esperado '16.01.', obtenido None
- RES-020 · FALLO · FINAL.lineas[1].precio_source: esperado 'contrato_db', obtenido None
- RES-020 · FALLO · FINAL.lineas[1].precio_unitario_final: esperado 184, obtenido None
- RES-021 · FALLO · FINAL.datos_generales[].total_valorado_esperado: esperado 184, obtenido 0.0
- RES-021 · FALLO · FINAL.lineas[1].casa_con_contrato: esperado 'SI', obtenido False
- RES-021 · FALLO · FINAL.lineas[1].importe_final: esperado 0, obtenido None
- RES-021 · FALLO · FINAL.lineas[1].partida_final: esperado '16.01.', obtenido None
- RES-021 · FALLO · FINAL.lineas[1].precio_source: esperado 'contrato_db', obtenido None
- RES-021 · FALLO · FINAL.lineas[1].precio_unitario_final: esperado 184, obtenido None
- RES-021 · FALLO · FINAL.lineas[2].casa_con_contrato: esperado 'SI', obtenido False
- RES-021 · FALLO · FINAL.lineas[2].importe_final: esperado 184, obtenido None
- RES-021 · FALLO · FINAL.lineas[2].partida_final: esperado '16.01.', obtenido None
- RES-021 · FALLO · FINAL.lineas[2].precio_source: esperado 'contrato_db', obtenido None
- RES-021 · FALLO · FINAL.lineas[2].precio_unitario_final: esperado 184, obtenido None

## Campos sin clasificar en evals/criticidad.json

Se han tratado como críticos (R8). Clasifícalos en evals/criticidad.json para que el informe deje de avisar:

- `cantidad_final`
- `caso_id`
- `cif`
- `comentario`
- `concepto`
- `descripcion`
- `descripcion_esperada`
- `fecha`
- `fichero`
- `motivo_revision`
- `numero_albaran`
- `obra`
- `proveedor`
- `unidad_final`

## Veredicto

Hay fallos críticos en: IA1, IA2, IA3, IA4, E2E.

VEREDICTO: ROJO
