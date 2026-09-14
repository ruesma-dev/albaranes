<!-- informe generado por evals/informe.py -->

# Evals de IA — F-043

- Fecha: 2026-09-14T18:17:54Z
- Commit HEAD: 06d6150
- Feature: F-043
- Modo: pasada completa (con llamadas LLM reales)

Líneas parseables por la puerta del arnés:

```
MODO: completa
FASES: IA1,IA2,IA3,IA4,E2E
PROVEEDORES: gemini,openai
```

## IA1 · extracción genérica (sv2) — ROJO

- Casos evaluados: 7 · omitidos: 0
- Proveedores invocados: gemini

| Caso | Estado | Fallos críticos | Avisos laxos | Motivo |
|---|---|---|---|---|
| RES-001/gemini | ROJO | 3 | 2 | — |
| RES-002/gemini | ROJO | 4 | 3 | — |
| RES-003/gemini | ROJO | 5 | 2 | — |
| RES-004/gemini | ROJO | 3 | 3 | — |
| RES-005/gemini | ROJO | 3 | 2 | — |
| RES-006/gemini | ROJO | 3 | 2 | — |
| RES-007/gemini | ROJO | 4 | 3 | — |

Detalle campo a campo:

- RES-001/gemini · FALLO · IA1.cabeceras[].caso_id: esperado 'RES-001', obtenido None
- RES-001/gemini · AVISO · IA1.cabeceras[].comentario: esperado "Documento de control de residuos (Art. 6 RD 553/2020): rejilla LER preimpresa y volumen escrito a mano. No imprime codigo de obra (687/691 son de Sigrid) ni forma de pago, y la casilla CIF/NIF esta vacia. obra_nombre va '?' porque el papel solo trae la direccion de obra manuscrita, distinta en cada albaran, y es campo critico: exigir una transcripcion exacta de la caligrafia seria una moneda al aire. proveedor_cif va '?': el unico CIF visible esta en el sello del destino, que aqui es CCR LAS MULAS, S.L.U. y NO es el proveedor.", obtenido None
- RES-001/gemini · FALLO · IA1.cabeceras[].fichero_albaran: esperado 'RES-001.pdf', obtenido None
- RES-001/gemini · FALLO · IA1.lineas[1].caso_id: esperado 'RES-001', obtenido None
- RES-001/gemini · AVISO · IA1.lineas[1].comentario: esperado "Fila LER 17 02 01 'Madera', con 6 manuscrito en la columna VOL. m3. Sin precio ni importe: el Excel de negocio declara que vienen del CONTRATO (de la OFERTA en RES-007), nunca del albaran. unidad vacia: el papel no escribe unidad en la linea (el m3 es el rotulo de la columna) y F-024 fijo unidad_medida null en los siete. Sin codigo_imputacion: CI.03A.7 es de Sigrid, no del papel. El incremento por LER NO se extrae aqui: es sintetica de IA3.", obtenido None
- RES-002/gemini · FALLO · IA1.cabeceras[].caso_id: esperado 'RES-002', obtenido None
- RES-002/gemini · AVISO · IA1.cabeceras[].comentario: esperado "Documento de control de residuos (Art. 6 RD 553/2020): rejilla LER preimpresa y volumen escrito a mano. No imprime codigo de obra (687/691 son de Sigrid) ni forma de pago, y la casilla CIF/NIF esta vacia. obra_nombre va '?' porque el papel solo trae la direccion de obra manuscrita, distinta en cada albaran, y es campo critico: exigir una transcripcion exacta de la caligrafia seria una moneda al aire. proveedor_cif va '?': el unico CIF visible esta en el sello del destino, que aqui es CCR LAS MULAS, S.L.U. y NO es el proveedor.", obtenido None
- RES-002/gemini · FALLO · IA1.cabeceras[].fichero_albaran: esperado 'RES-002.pdf', obtenido None
- RES-002/gemini · FALLO · IA1.lineas[1].cantidad: esperado 6, obtenido 8120.0
- RES-002/gemini · FALLO · IA1.lineas[1].caso_id: esperado 'RES-002', obtenido None
- RES-002/gemini · AVISO · IA1.lineas[1].comentario: esperado "Fila LER 17 01 07 'Horm_Ladr_Cerám.', con 6 manuscrito en la columna VOL. m3. Sin precio ni importe: el Excel de negocio declara que vienen del CONTRATO (de la OFERTA en RES-007), nunca del albaran. unidad vacia: el papel no escribe unidad en la linea (el m3 es el rotulo de la columna) y F-024 fijo unidad_medida null en los siete. Sin codigo_imputacion: CI.03A.7 es de Sigrid, no del papel. El incremento por LER NO se extrae aqui: es sintetica de IA3.", obtenido None
- RES-002/gemini · AVISO · IA1.lineas[1].descripcion_esperada: esperado 'Horm_Ladr_Cerám.', obtenido 'Horm_Ladr_Cerám. (LER 17 01 07)'
- RES-003/gemini · FALLO · IA1.cabeceras[].caso_id: esperado 'RES-003', obtenido None
- RES-003/gemini · AVISO · IA1.cabeceras[].comentario: esperado "Documento de control de residuos (Art. 6 RD 553/2020): rejilla LER preimpresa y volumen escrito a mano. No imprime codigo de obra (687/691 son de Sigrid) ni forma de pago, y la casilla CIF/NIF esta vacia. obra_nombre va '?' porque el papel solo trae la direccion de obra manuscrita, distinta en cada albaran, y es campo critico: exigir una transcripcion exacta de la caligrafia seria una moneda al aire. proveedor_cif va '?': el unico CIF visible (B-82899550) esta dentro del sello de SALMEDINA TRI, no en la cabecera del documento.", obtenido None
- RES-003/gemini · FALLO · IA1.cabeceras[].fichero_albaran: esperado 'RES-003.pdf', obtenido None
- RES-003/gemini · FALLO · IA1.cabeceras[].numero_albaran: esperado 'SS-0000589', obtenido 'SS-0080589'
- RES-003/gemini · FALLO · IA1.cabeceras[].proveedor_nombre: esperado 'SALMEDINA TRATAMIENTO DE RESIDUOS INERTES, S.L.', obtenido 'SALMEDINA TRI, S.L.'
- RES-003/gemini · FALLO · IA1.lineas[1].caso_id: esperado 'RES-003', obtenido None
- RES-003/gemini · AVISO · IA1.lineas[1].comentario: esperado "Fila LER 17 08 02 'Mat. Yeso', con 6 manuscrito en la columna VOL. m3. Sin precio ni importe: el Excel de negocio declara que vienen del CONTRATO (de la OFERTA en RES-007), nunca del albaran. unidad vacia: el papel no escribe unidad en la linea (el m3 es el rotulo de la columna) y F-024 fijo unidad_medida null en los siete. Sin codigo_imputacion: CI.03A.7 es de Sigrid, no del papel. El incremento por LER NO se extrae aqui: es sintetica de IA3.", obtenido None
- RES-004/gemini · FALLO · IA1.cabeceras[].caso_id: esperado 'RES-004', obtenido None
- RES-004/gemini · AVISO · IA1.cabeceras[].comentario: esperado "Documento de control de residuos (Art. 6 RD 553/2020): rejilla LER preimpresa y volumen escrito a mano. No imprime codigo de obra (687/691 son de Sigrid) ni forma de pago, y la casilla CIF/NIF esta vacia. obra_nombre va '?' porque el papel solo trae la direccion de obra manuscrita, distinta en cada albaran, y es campo critico: exigir una transcripcion exacta de la caligrafia seria una moneda al aire. proveedor_cif va '?': el unico CIF visible (B-82899550) esta dentro del sello de SALMEDINA TRI, no en la cabecera del documento.", obtenido None
- RES-004/gemini · FALLO · IA1.cabeceras[].fichero_albaran: esperado 'RES-004.pdf', obtenido None
- RES-004/gemini · FALLO · IA1.lineas[1].caso_id: esperado 'RES-004', obtenido None
- RES-004/gemini · AVISO · IA1.lineas[1].comentario: esperado "Fila LER 17 06 04 'Mat. Aislamiento', con 6 manuscrito en la columna VOL. m3. Sin precio ni importe: el Excel de negocio declara que vienen del CONTRATO (de la OFERTA en RES-007), nunca del albaran. unidad vacia: el papel no escribe unidad en la linea (el m3 es el rotulo de la columna) y F-024 fijo unidad_medida null en los siete. Sin codigo_imputacion: CI.03A.7 es de Sigrid, no del papel. El incremento por LER NO se extrae aqui: es sintetica de IA3.", obtenido None
- RES-004/gemini · AVISO · IA1.lineas[1].descripcion_esperada: esperado 'Mat. Aislamiento', obtenido 'Mat. Aislamiento (LER 17 06 04)'
- RES-005/gemini · FALLO · IA1.cabeceras[].caso_id: esperado 'RES-005', obtenido None
- RES-005/gemini · AVISO · IA1.cabeceras[].comentario: esperado "Documento de control de residuos (Art. 6 RD 553/2020): rejilla LER preimpresa y volumen escrito a mano. No imprime codigo de obra (687/691 son de Sigrid) ni forma de pago, y la casilla CIF/NIF esta vacia. obra_nombre va '?' porque el papel solo trae la direccion de obra manuscrita, distinta en cada albaran, y es campo critico: exigir una transcripcion exacta de la caligrafia seria una moneda al aire. proveedor_cif va '?': el unico CIF visible (B-82899550) esta dentro del sello de SALMEDINA TRI, no en la cabecera del documento. Numero corregido el 2026-09-11 contra el PDF: el papel imprime SS-0001977; SS-0801977 era una mala lectura del sistema.", obtenido None
- RES-005/gemini · FALLO · IA1.cabeceras[].fichero_albaran: esperado 'RES-005.pdf', obtenido None
- RES-005/gemini · FALLO · IA1.lineas[1].caso_id: esperado 'RES-005', obtenido None
- RES-005/gemini · AVISO · IA1.lineas[1].comentario: esperado "Fila LER 17 06 04 'Mat. Aislamiento', con 6 manuscrito en la columna VOL. m3. Sin precio ni importe: el Excel de negocio declara que vienen del CONTRATO (de la OFERTA en RES-007), nunca del albaran. unidad vacia: el papel no escribe unidad en la linea (el m3 es el rotulo de la columna) y F-024 fijo unidad_medida null en los siete. Sin codigo_imputacion: CI.03A.7 es de Sigrid, no del papel. El incremento por LER NO se extrae aqui: es sintetica de IA3.", obtenido None
- RES-006/gemini · FALLO · IA1.cabeceras[].caso_id: esperado 'RES-006', obtenido None
- RES-006/gemini · AVISO · IA1.cabeceras[].comentario: esperado "Documento de control de residuos (Art. 6 RD 553/2020): rejilla LER preimpresa y volumen escrito a mano. No imprime codigo de obra (687/691 son de Sigrid) ni forma de pago, y la casilla CIF/NIF esta vacia. obra_nombre va '?' porque el papel solo trae la direccion de obra manuscrita, distinta en cada albaran, y es campo critico: exigir una transcripcion exacta de la caligrafia seria una moneda al aire. proveedor_cif va '?': el unico CIF visible (B-82899550) esta dentro del sello de SALMEDINA TRI, no en la cabecera del documento.", obtenido None
- RES-006/gemini · FALLO · IA1.cabeceras[].fichero_albaran: esperado 'RES-006.pdf', obtenido None
- RES-006/gemini · FALLO · IA1.lineas[1].caso_id: esperado 'RES-006', obtenido None
- RES-006/gemini · AVISO · IA1.lineas[1].comentario: esperado "Fila LER 17 09 04 'Mat. Mezclados', con 6 manuscrito en la columna VOL. m3. Sin precio ni importe: el Excel de negocio declara que vienen del CONTRATO (de la OFERTA en RES-007), nunca del albaran. unidad vacia: el papel no escribe unidad en la linea (el m3 es el rotulo de la columna) y F-024 fijo unidad_medida null en los siete. Sin codigo_imputacion: CI.03A.7 es de Sigrid, no del papel. El incremento por LER NO se extrae aqui: es sintetica de IA3.", obtenido None
- RES-007/gemini · FALLO · IA1.cabeceras[].caso_id: esperado 'RES-007', obtenido None
- RES-007/gemini · AVISO · IA1.cabeceras[].comentario: esperado "Documento de control de residuos (Art. 6 RD 553/2020): rejilla LER preimpresa y volumen escrito a mano. No imprime codigo de obra (687/691 son de Sigrid) ni forma de pago, y la casilla CIF/NIF esta vacia. obra_nombre va '?' porque el papel solo trae la direccion de obra manuscrita, distinta en cada albaran, y es campo critico: exigir una transcripcion exacta de la caligrafia seria una moneda al aire. proveedor_cif va '?': el unico CIF visible (B-82899550) esta dentro del sello de SALMEDINA TRI, no en la cabecera del documento.", obtenido None
- RES-007/gemini · FALLO · IA1.cabeceras[].fichero_albaran: esperado 'RES-007.pdf', obtenido None
- RES-007/gemini · FALLO · IA1.cabeceras[].numero_albaran: esperado 'SS-0026122', obtenido 'SS-0028122'
- RES-007/gemini · FALLO · IA1.lineas[1].caso_id: esperado 'RES-007', obtenido None
- RES-007/gemini · AVISO · IA1.lineas[1].comentario: esperado "Fila LER 17 08 02 'Mat. Yeso', con 9 manuscrito en la columna VOL. m3. Sin precio ni importe: el Excel de negocio declara que vienen del CONTRATO (de la OFERTA en RES-007), nunca del albaran. unidad vacia: el papel no escribe unidad en la linea (el m3 es el rotulo de la columna) y F-024 fijo unidad_medida null en los siete. Sin codigo_imputacion: CI.03A.7 es de Sigrid, no del papel. El incremento por LER NO se extrae aqui: es sintetica de IA3.", obtenido None
- RES-007/gemini · AVISO · IA1.lineas[1].descripcion_esperada: esperado 'Mat. Yeso', obtenido 'Mat. Yeso (LER 17 08 02)'

## IA2 · contexto por tipología (sv2) — ROJO

- Casos evaluados: 7 · omitidos: 0
- Proveedores invocados: openai

| Caso | Estado | Fallos críticos | Avisos laxos | Motivo |
|---|---|---|---|---|
| RES-001/openai | ROJO | 3 | 7 | — |
| RES-002/openai | ROJO | 3 | 5 | — |
| RES-003/openai | ROJO | 3 | 7 | — |
| RES-004/openai | ROJO | 3 | 4 | — |
| RES-005/openai | ROJO | 3 | 5 | — |
| RES-006/openai | ROJO | 3 | 4 | — |
| RES-007/openai | ROJO | 3 | 5 | — |

Detalle campo a campo:

- RES-001/openai · FALLO · IA2.contexto[1/TIPO_FAMILIA].caso_id: esperado 'RES-001', obtenido None
- RES-001/openai · AVISO · IA2.contexto[1/TIPO_FAMILIA].comentario: esperado 'Familia de linea del catalogo unico: el documento es de gestion de residuos (RCD).', obtenido None
- RES-001/openai · FALLO · IA2.contexto[1/CODIGO_LER].caso_id: esperado 'RES-001', obtenido None
- RES-001/openai · AVISO · IA2.contexto[1/CODIGO_LER].comentario: esperado 'Fila marcada en la rejilla del papel: 17 02 01. Normalizado segun el LEEME de IA2 y el contrato de contexto_linea: 6 digitos, sin espacios ni puntos.', obtenido None
- RES-001/openai · FALLO · IA2.contexto[1/VOLUMEN_M3].caso_id: esperado 'RES-001', obtenido None
- RES-001/openai · AVISO · IA2.contexto[1/VOLUMEN_M3].comentario: esperado 'El 6 manuscrito en la columna VOL. m3. Es la CAPACIDAD del contenedor (§8.1), no una cantidad de material.', obtenido None
- RES-001/openai · AVISO · IA2.contexto[+]: esperado None, obtenido {'num_linea': 1, 'campo_contexto': 'contenedores_entregados', 'valor_esperado': 1.0} (fila producida por el sistema que el ground truth no declara)
- RES-001/openai · AVISO · IA2.contexto[+]: esperado None, obtenido {'num_linea': 1, 'campo_contexto': 'contenedores_retirados', 'valor_esperado': 1.0} (fila producida por el sistema que el ground truth no declara)
- RES-001/openai · AVISO · IA2.contexto[+]: esperado None, obtenido {'num_linea': 1, 'campo_contexto': 'peso_toneladas', 'valor_esperado': 1.5} (fila producida por el sistema que el ground truth no declara)
- RES-001/openai · AVISO · IA2.contexto[+]: esperado None, obtenido {'num_linea': 1, 'campo_contexto': 'rol_linea', 'valor_esperado': 'base'} (fila producida por el sistema que el ground truth no declara)
- RES-002/openai · FALLO · IA2.contexto[1/TIPO_FAMILIA].caso_id: esperado 'RES-002', obtenido None
- RES-002/openai · AVISO · IA2.contexto[1/TIPO_FAMILIA].comentario: esperado 'Familia de linea del catalogo unico: el documento es de gestion de residuos (RCD).', obtenido None
- RES-002/openai · FALLO · IA2.contexto[1/CODIGO_LER].caso_id: esperado 'RES-002', obtenido None
- RES-002/openai · AVISO · IA2.contexto[1/CODIGO_LER].comentario: esperado 'Fila marcada en la rejilla del papel: 17 01 07. Normalizado segun el LEEME de IA2 y el contrato de contexto_linea: 6 digitos, sin espacios ni puntos.', obtenido None
- RES-002/openai · FALLO · IA2.contexto[1/VOLUMEN_M3].caso_id: esperado 'RES-002', obtenido None
- RES-002/openai · AVISO · IA2.contexto[1/VOLUMEN_M3].comentario: esperado 'El 6 manuscrito en la columna VOL. m3. Es la CAPACIDAD del contenedor (§8.1), no una cantidad de material.', obtenido None
- RES-002/openai · AVISO · IA2.contexto[+]: esperado None, obtenido {'num_linea': 1, 'campo_contexto': 'peso_toneladas', 'valor_esperado': 8.12} (fila producida por el sistema que el ground truth no declara)
- RES-002/openai · AVISO · IA2.contexto[+]: esperado None, obtenido {'num_linea': 1, 'campo_contexto': 'rol_linea', 'valor_esperado': 'base'} (fila producida por el sistema que el ground truth no declara)
- RES-003/openai · FALLO · IA2.contexto[1/TIPO_FAMILIA].caso_id: esperado 'RES-003', obtenido None
- RES-003/openai · AVISO · IA2.contexto[1/TIPO_FAMILIA].comentario: esperado 'Familia de linea del catalogo unico: el documento es de gestion de residuos (RCD).', obtenido None
- RES-003/openai · FALLO · IA2.contexto[1/CODIGO_LER].caso_id: esperado 'RES-003', obtenido None
- RES-003/openai · AVISO · IA2.contexto[1/CODIGO_LER].comentario: esperado 'Fila marcada en la rejilla del papel: 17 08 02. Normalizado segun el LEEME de IA2 y el contrato de contexto_linea: 6 digitos, sin espacios ni puntos.', obtenido None
- RES-003/openai · FALLO · IA2.contexto[1/VOLUMEN_M3].caso_id: esperado 'RES-003', obtenido None
- RES-003/openai · AVISO · IA2.contexto[1/VOLUMEN_M3].comentario: esperado 'El 6 manuscrito en la columna VOL. m3. Es la CAPACIDAD del contenedor (§8.1), no una cantidad de material.', obtenido None
- RES-003/openai · AVISO · IA2.contexto[+]: esperado None, obtenido {'num_linea': 1, 'campo_contexto': 'contenedores_entregados', 'valor_esperado': 1.0} (fila producida por el sistema que el ground truth no declara)
- RES-003/openai · AVISO · IA2.contexto[+]: esperado None, obtenido {'num_linea': 1, 'campo_contexto': 'contenedores_retirados', 'valor_esperado': 1.0} (fila producida por el sistema que el ground truth no declara)
- RES-003/openai · AVISO · IA2.contexto[+]: esperado None, obtenido {'num_linea': 1, 'campo_contexto': 'peso_toneladas', 'valor_esperado': 2.16} (fila producida por el sistema que el ground truth no declara)
- RES-003/openai · AVISO · IA2.contexto[+]: esperado None, obtenido {'num_linea': 1, 'campo_contexto': 'rol_linea', 'valor_esperado': 'base'} (fila producida por el sistema que el ground truth no declara)
- RES-004/openai · FALLO · IA2.contexto[1/TIPO_FAMILIA].caso_id: esperado 'RES-004', obtenido None
- RES-004/openai · AVISO · IA2.contexto[1/TIPO_FAMILIA].comentario: esperado 'Familia de linea del catalogo unico: el documento es de gestion de residuos (RCD).', obtenido None
- RES-004/openai · FALLO · IA2.contexto[1/CODIGO_LER].caso_id: esperado 'RES-004', obtenido None
- RES-004/openai · AVISO · IA2.contexto[1/CODIGO_LER].comentario: esperado 'Fila marcada en la rejilla del papel: 17 06 04. Normalizado segun el LEEME de IA2 y el contrato de contexto_linea: 6 digitos, sin espacios ni puntos.', obtenido None
- RES-004/openai · FALLO · IA2.contexto[1/VOLUMEN_M3].caso_id: esperado 'RES-004', obtenido None
- RES-004/openai · AVISO · IA2.contexto[1/VOLUMEN_M3].comentario: esperado 'El 6 manuscrito en la columna VOL. m3. Es la CAPACIDAD del contenedor (§8.1), no una cantidad de material.', obtenido None
- RES-004/openai · AVISO · IA2.contexto[+]: esperado None, obtenido {'num_linea': 1, 'campo_contexto': 'rol_linea', 'valor_esperado': 'base'} (fila producida por el sistema que el ground truth no declara)
- RES-005/openai · FALLO · IA2.contexto[1/TIPO_FAMILIA].caso_id: esperado 'RES-005', obtenido None
- RES-005/openai · AVISO · IA2.contexto[1/TIPO_FAMILIA].comentario: esperado 'Familia de linea del catalogo unico: el documento es de gestion de residuos (RCD).', obtenido None
- RES-005/openai · FALLO · IA2.contexto[1/CODIGO_LER].caso_id: esperado 'RES-005', obtenido None
- RES-005/openai · AVISO · IA2.contexto[1/CODIGO_LER].comentario: esperado 'Fila marcada en la rejilla del papel: 17 06 04. Normalizado segun el LEEME de IA2 y el contrato de contexto_linea: 6 digitos, sin espacios ni puntos.', obtenido None
- RES-005/openai · FALLO · IA2.contexto[1/VOLUMEN_M3].caso_id: esperado 'RES-005', obtenido None
- RES-005/openai · AVISO · IA2.contexto[1/VOLUMEN_M3].comentario: esperado 'El 6 manuscrito en la columna VOL. m3. Es la CAPACIDAD del contenedor (§8.1), no una cantidad de material.', obtenido None
- RES-005/openai · AVISO · IA2.contexto[+]: esperado None, obtenido {'num_linea': 1, 'campo_contexto': 'peso_toneladas', 'valor_esperado': 18.0} (fila producida por el sistema que el ground truth no declara)
- RES-005/openai · AVISO · IA2.contexto[+]: esperado None, obtenido {'num_linea': 1, 'campo_contexto': 'rol_linea', 'valor_esperado': 'base'} (fila producida por el sistema que el ground truth no declara)
- RES-006/openai · FALLO · IA2.contexto[1/TIPO_FAMILIA].caso_id: esperado 'RES-006', obtenido None
- RES-006/openai · AVISO · IA2.contexto[1/TIPO_FAMILIA].comentario: esperado 'Familia de linea del catalogo unico: el documento es de gestion de residuos (RCD).', obtenido None
- RES-006/openai · FALLO · IA2.contexto[1/CODIGO_LER].caso_id: esperado 'RES-006', obtenido None
- RES-006/openai · AVISO · IA2.contexto[1/CODIGO_LER].comentario: esperado 'Fila marcada en la rejilla del papel: 17 09 04. Normalizado segun el LEEME de IA2 y el contrato de contexto_linea: 6 digitos, sin espacios ni puntos.', obtenido None
- RES-006/openai · FALLO · IA2.contexto[1/VOLUMEN_M3].caso_id: esperado 'RES-006', obtenido None
- RES-006/openai · AVISO · IA2.contexto[1/VOLUMEN_M3].comentario: esperado 'El 6 manuscrito en la columna VOL. m3. Es la CAPACIDAD del contenedor (§8.1), no una cantidad de material.', obtenido None
- RES-006/openai · AVISO · IA2.contexto[+]: esperado None, obtenido {'num_linea': 1, 'campo_contexto': 'rol_linea', 'valor_esperado': 'base'} (fila producida por el sistema que el ground truth no declara)
- RES-007/openai · FALLO · IA2.contexto[1/TIPO_FAMILIA].caso_id: esperado 'RES-007', obtenido None
- RES-007/openai · AVISO · IA2.contexto[1/TIPO_FAMILIA].comentario: esperado 'Familia de linea del catalogo unico: el documento es de gestion de residuos (RCD).', obtenido None
- RES-007/openai · FALLO · IA2.contexto[1/CODIGO_LER].caso_id: esperado 'RES-007', obtenido None
- RES-007/openai · AVISO · IA2.contexto[1/CODIGO_LER].comentario: esperado 'Fila marcada en la rejilla del papel: 17 08 02. Normalizado segun el LEEME de IA2 y el contrato de contexto_linea: 6 digitos, sin espacios ni puntos.', obtenido None
- RES-007/openai · FALLO · IA2.contexto[1/VOLUMEN_M3].caso_id: esperado 'RES-007', obtenido None
- RES-007/openai · AVISO · IA2.contexto[1/VOLUMEN_M3].comentario: esperado 'El 9 manuscrito en la columna VOL. m3. Es la CAPACIDAD del contenedor (§8.1), no una cantidad de material.', obtenido None
- RES-007/openai · AVISO · IA2.contexto[+]: esperado None, obtenido {'num_linea': 1, 'campo_contexto': 'peso_toneladas', 'valor_esperado': 2.36} (fila producida por el sistema que el ground truth no declara)
- RES-007/openai · AVISO · IA2.contexto[+]: esperado None, obtenido {'num_linea': 1, 'campo_contexto': 'rol_linea', 'valor_esperado': 'base'} (fila producida por el sistema que el ground truth no declara)

## IA3 · valoración contra contrato (sv5) — ROJO

- Casos evaluados: 7 · omitidos: 0
- Proveedores invocados: gemini

| Caso | Estado | Fallos críticos | Avisos laxos | Motivo |
|---|---|---|---|---|
| RES-001 | VERDE | 0 | 0 | — |
| RES-002 | VERDE | 0 | 0 | — |
| RES-003 | ROJO | 7 | 0 | — |
| RES-004 | ROJO | 7 | 0 | — |
| RES-005 | ROJO | 7 | 0 | — |
| RES-006 | VERDE | 0 | 0 | — |
| RES-007 | ROJO | 4 | 0 | — |

Detalle campo a campo:

- RES-003 · FALLO · IA3.lineas_valoradas[1].codigo_partida_final: esperado 'CI.03A.7', obtenido None
- RES-003 · FALLO · IA3.lineas_valoradas[1].codigo_producto_contrato: esperado 'C1', obtenido None
- RES-003 · FALLO · IA3.lineas_valoradas[1].importe_calculado: esperado 120, obtenido None
- RES-003 · FALLO · IA3.lineas_valoradas[1].match_method: esperado 'semantic', obtenido 'no_match'
- RES-003 · FALLO · IA3.lineas_valoradas[1].precio_source: esperado 'contrato_db', obtenido None
- RES-003 · FALLO · IA3.lineas_valoradas[1].precio_unitario_final: esperado 120, obtenido None
- RES-003 · FALLO · IA3.sinteticas_esperadas[1/GESTION_RESIDUOS].codigo_partida: esperado 'CI.03A.7', obtenido None
- RES-004 · FALLO · IA3.lineas_valoradas[1].codigo_partida_final: esperado 'CI.03A.7', obtenido None
- RES-004 · FALLO · IA3.lineas_valoradas[1].codigo_producto_contrato: esperado 'C1', obtenido None
- RES-004 · FALLO · IA3.lineas_valoradas[1].importe_calculado: esperado 120, obtenido None
- RES-004 · FALLO · IA3.lineas_valoradas[1].match_method: esperado 'semantic', obtenido 'no_match'
- RES-004 · FALLO · IA3.lineas_valoradas[1].precio_source: esperado 'contrato_db', obtenido None
- RES-004 · FALLO · IA3.lineas_valoradas[1].precio_unitario_final: esperado 120, obtenido None
- RES-004 · FALLO · IA3.sinteticas_esperadas[1/GESTION_RESIDUOS].codigo_partida: esperado 'CI.03A.7', obtenido None
- RES-005 · FALLO · IA3.lineas_valoradas[1].codigo_partida_final: esperado 'CI.03A.7', obtenido None
- RES-005 · FALLO · IA3.lineas_valoradas[1].codigo_producto_contrato: esperado 'C1', obtenido None
- RES-005 · FALLO · IA3.lineas_valoradas[1].importe_calculado: esperado 120, obtenido None
- RES-005 · FALLO · IA3.lineas_valoradas[1].match_method: esperado 'semantic', obtenido 'no_match'
- RES-005 · FALLO · IA3.lineas_valoradas[1].precio_source: esperado 'contrato_db', obtenido None
- RES-005 · FALLO · IA3.lineas_valoradas[1].precio_unitario_final: esperado 120, obtenido None
- RES-005 · FALLO · IA3.sinteticas_esperadas[1/GESTION_RESIDUOS].codigo_partida: esperado 'CI.03A.7', obtenido None
- RES-007 · FALLO · IA3.lineas_valoradas[1].importe_calculado: esperado 183, obtenido 272.0
- RES-007 · FALLO · IA3.lineas_valoradas[1].precio_unitario_final: esperado 183, obtenido 136.0
- RES-007 · FALLO · IA3.sinteticas_esperadas[1/GESTION_RESIDUOS].cantidad: esperado 1, obtenido 2.0
- RES-007 · FALLO · IA3.sinteticas_esperadas[1/GESTION_RESIDUOS].precio_unitario: esperado 77, obtenido None

## IA4 · conciliación de líneas sin match (sv5) — NO_EVALUABLE

- Casos evaluados: 0 · omitidos: 7
- Proveedores invocados: gemini

| Caso | Estado | Fallos críticos | Avisos laxos | Motivo |
|---|---|---|---|---|
| RES-001 | OMITIDO | — | — | sin caso en el libro IA4 |
| RES-002 | OMITIDO | — | — | sin caso en el libro IA4 |
| RES-003 | OMITIDO | — | — | sin caso en el libro IA4 |
| RES-004 | OMITIDO | — | — | sin caso en el libro IA4 |
| RES-005 | OMITIDO | — | — | sin caso en el libro IA4 |
| RES-006 | OMITIDO | — | — | sin caso en el libro IA4 |
| RES-007 | OMITIDO | — | — | sin caso en el libro IA4 |

## Extremo a extremo · RESULTADO_FINAL (sv5 → build de sv6) — ROJO

- Casos evaluados: 7 · omitidos: 0
- Proveedores invocados: gemini

| Caso | Estado | Fallos críticos | Avisos laxos | Motivo |
|---|---|---|---|---|
| RES-001 | VERDE | 0 | 0 | — |
| RES-002 | VERDE | 0 | 0 | — |
| RES-003 | ROJO | 8 | 0 | — |
| RES-004 | ROJO | 8 | 0 | — |
| RES-005 | ROJO | 8 | 0 | — |
| RES-006 | VERDE | 0 | 0 | — |
| RES-007 | ROJO | 8 | 0 | — |

Detalle campo a campo:

- RES-003 · FALLO · FINAL.datos_generales[].total_valorado_esperado: esperado 171, obtenido 51.0
- RES-003 · FALLO · FINAL.lineas[1].casa_con_contrato: esperado 'SI', obtenido False
- RES-003 · FALLO · FINAL.lineas[1].importe_final: esperado 120, obtenido None
- RES-003 · FALLO · FINAL.lineas[1].linea_contrato: esperado 'C1', obtenido None
- RES-003 · FALLO · FINAL.lineas[1].partida_final: esperado 'CI.03A.7', obtenido None
- RES-003 · FALLO · FINAL.lineas[1].precio_source: esperado 'contrato_db', obtenido None
- RES-003 · FALLO · FINAL.lineas[1].precio_unitario_final: esperado 120, obtenido None
- RES-003 · FALLO · FINAL.lineas_anadidas[1].partida: esperado 'CI.03A.7', obtenido None
- RES-004 · FALLO · FINAL.datos_generales[].total_valorado_esperado: esperado 210, obtenido 90.0
- RES-004 · FALLO · FINAL.lineas[1].casa_con_contrato: esperado 'SI', obtenido False
- RES-004 · FALLO · FINAL.lineas[1].importe_final: esperado 120, obtenido None
- RES-004 · FALLO · FINAL.lineas[1].linea_contrato: esperado 'C1', obtenido None
- RES-004 · FALLO · FINAL.lineas[1].partida_final: esperado 'CI.03A.7', obtenido None
- RES-004 · FALLO · FINAL.lineas[1].precio_source: esperado 'contrato_db', obtenido None
- RES-004 · FALLO · FINAL.lineas[1].precio_unitario_final: esperado 120, obtenido None
- RES-004 · FALLO · FINAL.lineas_anadidas[1].partida: esperado 'CI.03A.7', obtenido None
- RES-005 · FALLO · FINAL.datos_generales[].total_valorado_esperado: esperado 210, obtenido 90.0
- RES-005 · FALLO · FINAL.lineas[1].casa_con_contrato: esperado 'SI', obtenido False
- RES-005 · FALLO · FINAL.lineas[1].importe_final: esperado 120, obtenido None
- RES-005 · FALLO · FINAL.lineas[1].linea_contrato: esperado 'C1', obtenido None
- RES-005 · FALLO · FINAL.lineas[1].partida_final: esperado 'CI.03A.7', obtenido None
- RES-005 · FALLO · FINAL.lineas[1].precio_source: esperado 'contrato_db', obtenido None
- RES-005 · FALLO · FINAL.lineas[1].precio_unitario_final: esperado 120, obtenido None
- RES-005 · FALLO · FINAL.lineas_anadidas[1].partida: esperado 'CI.03A.7', obtenido None
- RES-007 · FALLO · FINAL.datos_generales[].total_valorado_esperado: esperado 260, obtenido 272.0
- RES-007 · FALLO · FINAL.lineas[1].casa_con_contrato: esperado 'NO', obtenido True
- RES-007 · FALLO · FINAL.lineas[1].importe_final: esperado 183, obtenido 272.0
- RES-007 · FALLO · FINAL.lineas[1].linea_contrato: esperado None, obtenido 'C1'
- RES-007 · FALLO · FINAL.lineas[1].precio_unitario_final: esperado 183, obtenido 136.0
- RES-007 · FALLO · FINAL.lineas_anadidas[1].cantidad: esperado 1, obtenido 2.0
- RES-007 · FALLO · FINAL.lineas_anadidas[1].importe: esperado 77, obtenido None
- RES-007 · FALLO · FINAL.lineas_anadidas[1].precio_unitario: esperado 77, obtenido None

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

Hay fallos críticos en: IA1, IA2, IA3, E2E.

VEREDICTO: ROJO
