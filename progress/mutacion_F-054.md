<!-- progress/mutacion_F-054.md -->
# F-054 · Campaña de mutación

Generado por `python -m harness.mutacion --feature F-054` el 2026-10-02 11:06.

## Alcance

Origen del diff: **rama** (`ddc384723ffdde64d45508b4a53c392d21e22bd1` .. `feature/F-054-correo-adjunto-encadenado`).

| Fichero | Líneas en alcance |
|---|---|
| `services/albaranes-email/application/pipelines/polling_pipeline.py` | 307 |
| `services/albaranes-email/domain/models/email_models.py` | 29 |
| `services/albaranes-email/domain/ports/extractor_correo_adjunto.py` | 36 |
| `services/albaranes-email/domain/ports/mailbox_client.py` | 6 |
| `services/albaranes-email/infrastructure/document/mime_documento_extractor.py` | 156 |
| `services/albaranes-email/main.py` | 4 |
| **Total** | **538** |

## Totales

| Métrica | Valor |
|---|---|
| Mutantes generados | 77 |
| Mutantes evaluados | 20 |
| Muertos | 19 |
| Supervivientes | 1 |
| Timeouts | 0 |
| Sin veredicto (base rota) | 0 |
| Tiempo total | 142.8 s |
| SHA de HEAD medido | `3fb2bb8fd6497776960f9c4fe631fbc8ca480201` |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-054_dy0e67pt/wk_0/services/albaranes-email` | 23.5 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-054_dy0e67pt/wk_1/services/albaranes-email` | 23.3 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-054_dy0e67pt/wk_2/services/albaranes-email` | 23.7 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-054_dy0e67pt/wk_3/services/albaranes-email` | 23.8 |
| Media por mutante evaluado (s) | 7.1 |
| Timeout efectivo por mutante (s) | 120 — derivado de la línea base × 2.0 |
| Suelo configurado (s) | 120 |
| Workers | 4 |
| Muestreo | sí — 20 de 77 mutantes, semilla `20260820`, nivel `estandar` |

## Supervivientes

Cada superviviente es una línea que ningún test comprueba de verdad, o una mutación equivalente. Distinguirlo es trabajo del implementer: ningún análisis puede quedarse sin completar al cerrar la feature.

### 1. `services/albaranes-email/infrastructure/document/mime_documento_extractor.py:155` [entero]

- Original: `extension = "pdf" if tipo == _TIPO_PDF else tipo.split("/", 1)[1]`
- Mutado:   `extension = "pdf" if tipo == _TIPO_PDF else tipo.split("/", 2)[1]`

#### Análisis (implementer)

> Por qué ningún test lo caza: es un **mutante equivalente**. `tipo` sale de `get_content_type()`, que siempre
> devuelve `maintype/subtype` con UNA sola barra (RFC 2045: el subtipo es un token, no admite `/`; ante un tipo
> mal formado la biblioteca `email` cae a `text/plain`). Con una sola barra, `split("/", 1)` y `split("/", 2)`
> dan la misma lista y el `[1]` es el mismo subtipo.
> Decisión: mutante equivalente justificado; sin test nuevo (ningún test puede distinguirlos).

## Primera pasada (HEAD `cea0788`, misma semilla): 17 muertos, 3 supervivientes

Los dos supervivientes que no aparecen arriba eran huecos reales y se mataron con tests nuevos (commit
`F-054 T10`), verificado aplicando cada mutante a mano y viendo el test en rojo:

1. `polling_pipeline.py:305` `len(a_procesar) - correos_adjuntos` → `+`: el recuento de directos del log final
   de destino no lo comprobaba nadie. Test nuevo:
   `test_f054_r21_el_log_final_cuenta_directos_correos_adjuntos_y_paginas`.
2. `polling_pipeline.py:657` `max_bytes > 0` → `>= 0` en `_es_correo_adjunto`: con `max_bytes = 0` («sin límite»,
   igual que en `_is_eligible`) el mutante descartaría todo correo adjunto. Test nuevo:
   `test_f054_r2_sin_limite_configurado_no_se_descarta_por_tamano`.

