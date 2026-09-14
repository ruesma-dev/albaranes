<!-- informe generado por evals/informe.py -->

# Evals de IA — F-043

- Fecha: 2026-09-12T11:00:08Z
- Commit HEAD: 6da1e7b
- Feature: F-043
- Modo: determinista (sin ninguna llamada LLM ni de red)

Líneas parseables por la puerta del arnés:

```
MODO: determinista
FASES: IA3,IA4,E2E
PROVEEDORES: (ninguno)
```

## IA3 · valoración contra contrato (sv5) — ROJO

- Casos evaluados: 7 · omitidos: 0
- Proveedores invocados: (ninguno)

| Caso | Estado | Fallos críticos | Avisos laxos | Motivo |
|---|---|---|---|---|
| RES-001 | VERDE | 0 | 0 | — |
| RES-002 | VERDE | 0 | 0 | — |
| RES-003 | VERDE | 0 | 0 | — |
| RES-004 | VERDE | 0 | 0 | — |
| RES-005 | VERDE | 0 | 0 | — |
| RES-006 | VERDE | 0 | 0 | — |
| RES-007 | ROJO | 5 | 0 | — |

Detalle campo a campo:

- RES-007 · FALLO · IA3.lineas_valoradas[1].codigo_partida_final: esperado 'CI.03A.7', obtenido None
- RES-007 · FALLO · IA3.lineas_valoradas[1].importe_calculado: esperado 183, obtenido None
- RES-007 · FALLO · IA3.lineas_valoradas[1].precio_unitario_final: esperado 183, obtenido None
- RES-007 · FALLO · IA3.sinteticas_esperadas[1/GESTION_RESIDUOS].cantidad: esperado 1, obtenido 2.0
- RES-007 · FALLO · IA3.sinteticas_esperadas[1/GESTION_RESIDUOS].codigo_partida: esperado 'CI.03A.7', obtenido None

## IA4 · conciliación de líneas sin match (sv5) — NO_EVALUABLE

- Casos evaluados: 0 · omitidos: 7
- Proveedores invocados: (ninguno)

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
- Proveedores invocados: (ninguno)

| Caso | Estado | Fallos críticos | Avisos laxos | Motivo |
|---|---|---|---|---|
| RES-001 | VERDE | 0 | 0 | — |
| RES-002 | VERDE | 0 | 0 | — |
| RES-003 | VERDE | 0 | 0 | — |
| RES-004 | VERDE | 0 | 0 | — |
| RES-005 | VERDE | 0 | 0 | — |
| RES-006 | VERDE | 0 | 0 | — |
| RES-007 | ROJO | 7 | 0 | — |

Detalle campo a campo:

- RES-007 · FALLO · FINAL.datos_generales[].total_valorado_esperado: esperado 260, obtenido 154.0
- RES-007 · FALLO · FINAL.lineas[1].importe_final: esperado 183, obtenido None
- RES-007 · FALLO · FINAL.lineas[1].partida_final: esperado 'CI.03A.7', obtenido None
- RES-007 · FALLO · FINAL.lineas[1].precio_unitario_final: esperado 183, obtenido None
- RES-007 · FALLO · FINAL.lineas_anadidas[1].cantidad: esperado 1, obtenido 2.0
- RES-007 · FALLO · FINAL.lineas_anadidas[1].importe: esperado 77, obtenido 154.0
- RES-007 · FALLO · FINAL.lineas_anadidas[1].partida: esperado 'CI.03A.7', obtenido None

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

Hay fallos críticos en: IA3, E2E.

VEREDICTO: ROJO
