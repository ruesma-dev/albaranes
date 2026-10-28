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

## Campaña MANUAL: 17 mutantes, 17 muertos, 0 supervivientes

Medida el 2026-10-24 (review 1) sobre `5e2b4ff` (código idéntico a `d3c20f1`), en serie, una suite cada vez:

- **Tests de cada mutante** (los mismos para todos los de su servicio), **sin `-x`**:
  sv9, desde `services/albaranes-alta-sigrid`: `python -m pytest -q --tb=no -p no:cacheprovider
  tests/test_f104_contrato_v83.py tests/test_f053_clasificador.py` (135 tests);
  sv4, desde `services/albaranes-front`: `.venv/Scripts/python.exe -m pytest -q --tb=no -p no:cacheprovider
  tests/test_f104_textos_avisos.py tests/test_f077_motivos_alta.py` (50 tests).
- Antes de cada mutante, esos tests en verde sobre el original; el mutante sustituye **una sola aparición** del texto
  original (si aparece 0 o 2+ veces, la campaña aborta); tras cada uno se restaura el fichero byte a byte y se
  comprueba. `PYTHONDONTWRITEBYTECODE=1`.
- **Línea**: la del primer carácter del texto original en el fichero sin mutar. **Texto exacto**: tal cual se
  sustituyó; `\n` es un salto de línea y `\|` una barra (escapadas solo para la tabla).
- **Fallos**: tests caídos / tests ejecutados, del resumen de pytest. Muerto = al menos un test caído.

| # | Fichero:línea | Texto original | Texto mutado | Fallos | Veredicto |
|---|---|---|---|---|---|
| M01 | `albaranes-alta-sigrid/domain/services/clasificador.py:47` | `"proveedor_no_encontrado": _NO_ADMITIDO` | `"proveedor_no_encontrado": _ERROR` | 10/135 | muerto |
| M02 | `albaranes-alta-sigrid/domain/services/clasificador.py:48` | `"proveedor_ambiguo": _NO_ADMITIDO` | `"proveedor_ambiguo": _REVISAR` | 10/135 | muerto |
| M03 | `albaranes-alta-sigrid/domain/services/clasificador.py:49` | `"retencion_no_soportada": _NO_ADMITIDO` | `"retencion_no_soportada": _ERROR` | 10/135 | muerto |
| M04 | `albaranes-alta-sigrid/domain/services/clasificador.py:49` | `    "retencion_no_soportada": _NO_ADMITIDO,\n` | (línea borrada) | 10/135 | muerto |
| M05 | `albaranes-alta-sigrid/domain/services/clasificador.py:45` | `"proveedor_sin_albaran_previo": _NO_ADMITIDO` | `"proveedor_sin_albaran_previo": _ERROR` | 6/135 | muerto |
| M06 | `albaranes-front/domain/models/alta_sigrid_models.py:109` | `"proveedor_ambiguo": "Hay varios proveedores en Sigrid con ese CIF"` | `"proveedor_ambiguo": "Hay varios proveedores en Sigrid"` | 1/50 | muerto |
| M07 | `albaranes-front/domain/models/alta_sigrid_models.py:138` | `"cabecera_sin_dato": "Sigrid dejó vacío algún dato de pago de la cabecera"` | `"cabecera_sin_dato": "cabecera_sin_dato"` | 5/50 | muerto |
| M08 | `albaranes-front/domain/models/alta_sigrid_models.py:137` | `    "retencion_del_contrato": "Sigrid aplicó la retención del contrato",\n` | (línea borrada) | 6/50 | muerto |
| M09 | `albaranes-front/domain/models/alta_sigrid_models.py:374` | `"mensaje": a.get("mensaje"),` | `"mensaje": a.get("detalle"),` | 4/50 | muerto |
| M10 | `albaranes-front/domain/models/alta_sigrid_models.py:375` | `"referencia_linea": a.get("referencia_linea")}` | `"referencia_linea": None}` | 3/50 | muerto |
| M11 | `albaranes-front/domain/models/alta_sigrid_models.py:372` | `"codigo": a.get("codigo"),\n             "texto"` | `"codigo": None,\n             "texto"` | 4/50 | muerto |
| M12 | `albaranes-front/domain/models/alta_sigrid_models.py:376` | `for a in self.avisos if isinstance(a, dict)\n        ]\n\n    @computed_field  # type: ignore[prop-decorator]\n    @property\n    def usu_respaldo` | `for a in self.avisos\n        ]\n\n    @computed_field  # type: ignore[prop-decorator]\n    @property\n    def usu_respaldo` | 1/50 | muerto |
| M13 | `albaranes-front/templates/_alta_sigrid.html:126` | `{% for a in alta.avisos_sigrid %}` | `{% for a in alta.avisos %}` | 3/50 | muerto |
| M14 | `albaranes-front/templates/_alta_sigrid.html:128` | `<li title="{{ a.codigo }}">{{ a.texto }}{% if a.mensaje %} · {{ a.mensaje }}{% endif %}` | `<li title="{{ a.codigo }}">{{ a.texto }}` | 2/50 | muerto |
| M15 | `albaranes-front/templates/_alta_sigrid.html:128` | `<li title="{{ a.codigo }}">{{ a.texto }}{% if a.mensaje %}` | `<li>{{ a.texto }}{% if a.mensaje %}` | 1/50 | muerto |
| M16 | `albaranes-front/templates/_alta_sigrid.html:128` | `{{ a.texto }}{% if a.mensaje %} · {{ a.mensaje }}{% endif %}{% if a.referencia_linea %} (línea {{ a.referencia_linea }}){% endif %}</li>\n                    {% else %}` | `{{ a.texto }}{% if a.mensaje %} · {{ a.mensaje }}{% endif %}</li>\n                    {% else %}` | 1/50 | muerto |
| M17 | `albaranes-front/templates/_alta_sigrid.html:127` | `{% if a.texto %}` | `{% if a.codigo %}` | 2/50 | muerto |

Cruce con la review 1: el reviewer reprodujo M02 (10 failed/135), M09 (4 failed/50) y M14 (2 failed/50); cuadran.

Además, las mutaciones inversas de la fase RED (`progress/impl_F-104.md`) cubren lo que F-104 no cambia pero
protege: el defecto de `ALTA_SIGRID_AVISOS_BLOQUEANTES`, `.env.example`, el comparador frente a `totales.tot`,
`desde_cuerpo` frente a `filas` y el `_ERROR` por defecto de H25. Todas muertas.

## T8 · mutación repetida de `clasificador.py` (R10, 2026-10-28)

Tras quitar `proveedor_sin_albaran_previo` de `CODIGOS_CABECERA` (`4a81091`). El diff de la T8 en ese fichero es
**solo un borrado** (no deja líneas añadidas que mutar), así que la campaña muta el **fichero entero**, en serie:

`python -m harness.mutacion --feature F-104 --ficheros services/albaranes-alta-sigrid/domain/services/clasificador.py
--max-mutantes 0 --workers 1 --salida <scratchpad>/mutacion_F-104_T8.md` (PYTHONPATH = `ruesma_comun` del worktree;
la salida fuera de `progress/` para no pisar este informe ni necesitar fila nueva en el inventario de F-039).

| Métrica | Valor |
|---|---|
| Alcance | 141 líneas, 1 fichero (origen `ficheros`) |
| SHA medido | `4a81091b737506710ca473919017c6e5514670e7` |
| Línea base sv9 | 70,9 s, en verde; timeout por mutante 142 s |
| Mutantes generados / evaluados | 13 / 13 |
| Muertos / supervivientes / timeouts / sin veredicto | **13 / 0 / 0 / 0** |
| Tiempo total | 218,7 s (media 16,8 s por mutante) |
| Muestreo | no: campaña completa |

Mutantes (todos muertos): `:92` `or`→`and`; `:93` `not` quitado; `:102` ×3 (`is not`→`is`, `or`→`and`, `not`
quitado); `:104` `==`→`!=`; `:116` `==`→`!=`; `:129` ×3 (`is not None`→`is None`, `and`→`or`, `is not`→`is`);
`:137` y `:138` `or`→`and`; `:139` `is None`→`is not None`.

**Supervivientes: ninguno; nada que justificar.** Como en T6, el mutador no muta entradas de diccionario: el cambio
de la T8 (una entrada menos) lo cubre el mutante a mano **M18** «volver a poner
`"proveedor_sin_albaran_previo": _NO_ADMITIDO` en `CODIGOS_CABECERA`», que es exactamente la fase RED de la T8
(`progress/impl_F-104.md`): `-k "f104 or f053_clasificador or f053_r18"` → **7 failed**, 145 passed ⇒ **muerto**.
