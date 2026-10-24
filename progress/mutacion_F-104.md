<!-- progress/mutacion_F-104.md -->
# F-104 · Campaña de mutación

Generado por `python -m harness.mutacion --feature F-104` el 2026-10-24 15:13.

## Alcance

Origen del diff: **rama** (`ba516a77d6f63f9f088b22655518987c55bf7f55` .. `feature/F-104-codigos-contrato-v83`).

| Fichero | Líneas en alcance |
|---|---|
| `services/albaranes-alta-sigrid/domain/services/clasificador.py` | 7 |
| `services/albaranes-front/domain/models/alta_sigrid_models.py` | 24 |
| **Total** | **31** |

## Totales

| Métrica | Valor |
|---|---|
| Mutantes generados | 1 |
| Mutantes evaluados | 1 |
| Muertos | 1 |
| Supervivientes | 0 |
| Timeouts | 0 |
| Sin veredicto (base rota) | 0 |
| Tiempo total | 566.1 s |
| SHA de HEAD medido | `d3c20f16a91a06fe738bd22b0f042f0693ebd8d6` |
| Línea base (s) — `services/albaranes-front` | 282.4 |
| Media por mutante evaluado (s) | 566.1 |
| Timeout efectivo por mutante (s) | 565 — derivado de la línea base × 2.0 |
| Suelo configurado (s) | 120 |
| Workers | 1 |
| Muestreo | no: campaña completa |

## Supervivientes

Ninguno: cada mutación aplicada la cazó al menos un test.


## Análisis del implementer: por qué 1 mutante y qué lo complementa

El mutador del arnés solo genera mutantes sobre operadores (comparaciones, lógicos, aritméticos, constantes
numéricas...). De las 31 líneas en alcance, 30 son **datos**: entradas `"código": _ESTADO` de `CODIGOS_CABECERA`,
entradas `"código": "texto"` de `TEXTOS_MOTIVO_ALTA`, comentarios y el cuerpo de un literal de diccionario en
`avisos_sigrid`. Sobre ellas no hay operador que mutar, así que el número «1 mutante» es correcto pero no mide la
parte que sostiene F-104. Tampoco cubre `templates/_alta_sigrid.html` (no es Python).

Complemento: **17 mutantes a mano** sobre esas líneas y la plantilla, cada uno juzgado con los tests de F-104 y los
vecinos (`test_f104_contrato_v83.py` + `test_f053_clasificador.py` en sv9; `test_f104_textos_avisos.py` +
`test_f077_motivos_alta.py` en sv4), restaurando el fichero tras cada uno. Script (fuera del repositorio, en el
scratchpad de la sesión): `mutantes_manuales.py`. Resultado real: **17 muertos, 0 supervivientes**.

| # | Fichero | Mutación | Veredicto |
|---|---|---|---|
| M01–M03 | `clasificador.py` | cada Error v8.3 a `_ERROR` / `_REVISAR` | muerto |
| M04 | `clasificador.py` | borrar `retencion_no_soportada` | muerto |
| M05 | `clasificador.py` | `proveedor_sin_albaran_previo` a `_ERROR` (R2) | muerto |
| M06–M07 | `alta_sigrid_models.py` | texto de `proveedor_ambiguo` recortado; texto de `cabecera_sin_dato` = código | muerto |
| M08 | `alta_sigrid_models.py` | borrar el texto de `retencion_del_contrato` | muerto |
| M09–M11 | `alta_sigrid_models.py` | `avisos_sigrid`: `mensaje` ← `detalle`; `referencia_linea` = `None`; `codigo` = `None` | muerto |
| M12 | `alta_sigrid_models.py` | `avisos_sigrid` sin el filtro `isinstance(a, dict)` | muerto |
| M13 | `_alta_sigrid.html` | iterar `alta.avisos` en vez de `alta.avisos_sigrid` | muerto |
| M14–M16 | `_alta_sigrid.html` | rama con texto: sin `· mensaje`; sin `title`; sin «(línea N)» | muerto |
| M17 | `_alta_sigrid.html` | `{% if a.texto %}` → `{% if a.codigo %}` | muerto |

Además, las mutaciones inversas de la fase RED (`progress/impl_F-104.md`) cubren lo que F-104 no cambia pero
protege: el defecto de `ALTA_SIGRID_AVISOS_BLOQUEANTES`, `.env.example`, el comparador frente a `totales.tot`,
`desde_cuerpo` frente a `filas` y el `_ERROR` por defecto de H25. Todas muertas.
