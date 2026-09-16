<!-- progress/mutacion_F-045.md -->
# F-045 · Campaña de mutación

Generado por `python -m harness.mutacion --feature F-045` el 2026-09-16 23:40.

## Alcance

Origen del diff: **rama** (`5132bdc39889c18af588ec3c3d045775f3fbe524` .. `HEAD`).

| Fichero | Líneas en alcance |
|---|---|
| `evals/revision/__main__.py` | 35 |
| `evals/revision/escritura.py` | 131 |
| `evals/revision/huella.py` | 81 |
| `evals/revision/informe.py` | 19 |
| `evals/revision/mapa.py` | 5 |
| `evals/revision/modelos.py` | 2 |
| `evals/revision/reparto.py` | 36 |
| `evals/revision/vocabulario.py` | 16 |
| **Total** | **325** |

## Totales

| Métrica | Valor |
|---|---|
| Mutantes generados | 44 |
| Mutantes evaluados | 44 |
| Muertos | 35 |
| Supervivientes | 9 |
| Timeouts | 0 |
| Sin veredicto (base rota) | 0 |
| Tiempo total | 871.0 s |
| SHA de HEAD medido | `a7de52a80f8db1356151f29539884d4432f1b7be` |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-045_mbo_itfo/wk_0` | 88.4 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-045_mbo_itfo/wk_1` | 86.6 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-045_mbo_itfo/wk_2` | 88.4 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-045_mbo_itfo/wk_3` | 87.8 |
| Media por mutante evaluado (s) | 19.8 |
| Timeout efectivo por mutante (s) | 177 — derivado de la línea base × 2.0 |
| Suelo configurado (s) | 120 |
| Workers | 4 |
| Muestreo | no: campaña completa |

## Supervivientes: resultado del análisis

**8 cerrados con test y 1 equivalente justificado.** Todos caían en el código
que acababa de perder datos —`huella.py` entero y las dos guardas de
`escritura.py` que deciden qué se retira—, así que casi no había sitio para la
prosa: **ante la duda, test**.

> **Corregido tras el review (pasada 3).** La versión anterior de esta sección
> decía «los 9 cerrados con test, ninguno equivalente», y era **falso por los
> dos lados**: el **7** (`sort_keys`) es equivalente de verdad y ningún test lo
> mata, y el **3** seguía **vivo**, porque el test que lo nombraba colapsaba las
> filas en un `dict` y así no veía que el mutante devuelve 3 donde deben ir 2,
> **duplicando la sintética del humano**. Los dos están arreglados y medidos por
> reinyección; el informe dice ahora lo que el código hace.

El **2** destapó además que la guarda de `_solo_del_importador` era casi código
muerto —nunca retiraba, porque la clave siempre tiene valor—, lo que impedía
retirar en la pestaña donde el humano acababa de borrar una línea; se reescribió
para declarar las columnas en duda de TODA la importación.

| Superviviente | Estado |
|---|---|
| 1, 2, 3, 4, 5, 6, 8, 9 | **muertos** con test nuevo, verificado por reinyección |
| 7 (`sort_keys` de la huella) | **equivalente**, con su comprobación ejecutada |

Verificado por reinyección uno a uno contra la suite acotada a F-045; los que
cambiaron de línea al reescribir la guarda se reinyectaron a mano sobre el
código de hoy.

## Supervivientes

Cada superviviente es una línea que ningún test comprueba de verdad, o una mutación equivalente. Distinguirlo es trabajo del implementer: ningún análisis puede quedarse sin completar al cerrar la feature.

### 1. `evals/revision/__main__.py:230` [logico]

- Original: `tabla: huella.claves_de(previa or {}, tabla)`
- Mutado:   `tabla: huella.claves_de(previa and {}, tabla)`

#### Análisis

- **Por qué sobrevivía**: `huella.claves_de(previa or {})` con `and` devuelve `{}` para cualquier huella no vacía: la retirada deja de funcionar sin que nada falle. No lo cazaba nadie porque no había ningún test que recorriera la retirada de extremo a extremo.
- **Decisión**: TEST NUEVO — `test_f045_r17_una_linea_que_el_humano_borra_del_excel_se_retira_del_libro`: quita una línea del Excel y comprueba que la fila desaparece del libro. Reinyectado uno a uno, **muere**.

### 2. `evals/revision/escritura.py:304` [not]

- Original: `return all(not _tiene_valor(valor) for valor in existente.values())`
- Mutado:   `return all(_tiene_valor(valor) for valor in existente.values())`

#### Análisis

- **Por qué sobrevivía**: la guarda de `_solo_del_importador` sin filas nuevas era casi código muerto —la clave siempre tiene valor, así que nunca retiraba—, y eso mismo la hacía inmune a la mutación. Se ha reescrito: las columnas en duda se declaran para TODA la importación, no se deducen de las filas de turno.
- **Decisión**: TEST NUEVO — `test_f045_r17_sin_filas_nuevas_no_se_retira_nada` y `test_f045_r17_una_tabla_que_esta_importacion_no_alimenta_se_queda_intacta`. Reinyectado uno a uno, **muere**.

### 3. `evals/revision/escritura.py:333` [logico]

- Original: `if nueva is None and campo_prefijo:`
- Mutado:   `if nueva is None or campo_prefijo:`

#### Análisis

- **Por qué sobrevivía**: con `or`, el casado por prefijo se intenta incluso cuando la clave ya casa EXACTA, y entonces la fila nueva se empareja también con la existente más corta y **se escriben las dos**: 3 filas donde deben ir 2, duplicando la línea deducida que el humano anotó. El banco esperaría dos sintéticas donde el sistema emite una. El test que lo nombraba **pasaba con el mutante puesto** porque colapsaba las filas en un `dict` por descripción, y ahí la duplicada pisaba a su gemela: el fallo quedaba invisible.
- **Decisión**: TEST NUEVO — `test_f045_r17_el_casado_por_prefijo_no_duplica_la_sintetica_del_humano`, que compara las filas **en lista, sin colapsar**. Reinyectado sobre el código de hoy, **muere**.

### 4. `evals/revision/huella.py:29` [entero]

- Original: `RUTA_HUELLA = Path(__file__).resolve().parents[1] / "huella_importacion.json"`
- Mutado:   `RUTA_HUELLA = Path(__file__).resolve().parents[2] / "huella_importacion.json"`

#### Análisis

- **Por qué sobrevivía**: un `parents[N]` de más saca la huella del paquete y el importador leería y escribiría su memoria en otro sitio, en silencio.
- **Decisión**: TEST NUEVO — `test_f045_r17_la_ruta_por_defecto_cae_junto_al_mapa_de_casos`. Reinyectado uno a uno, **muere**.

### 5. `evals/revision/huella.py:57` [booleano]

- Original: `{"_doc": _DOC, "tablas": ordenadas}, ensure_ascii=False, indent=2, sort_keys=True`
- Mutado:   `{"_doc": _DOC, "tablas": ordenadas}, ensure_ascii=True, indent=2, sort_keys=True`

#### Análisis

- **Por qué sobrevivía**: `ensure_ascii=True` llenaría de `\u00f1` un fichero versionado y lo dejaría irrevisable en un diff.
- **Decisión**: TEST NUEVO — `test_f045_r17_la_huella_no_escapa_los_acentos`. Reinyectado uno a uno, **muere**.

### 6. `evals/revision/huella.py:57` [entero]

- Original: `{"_doc": _DOC, "tablas": ordenadas}, ensure_ascii=False, indent=2, sort_keys=True`
- Mutado:   `{"_doc": _DOC, "tablas": ordenadas}, ensure_ascii=False, indent=3, sort_keys=True`

#### Análisis

- **Por qué sobrevivía**: cambiar la sangría cambia el fichero entero en cada importación: un diff de 2.700 líneas donde no cambió ni un dato.
- **Decisión**: TEST NUEVO — `test_f045_r17_la_huella_se_escribe_byte_a_byte_como_dice_su_docstring`, que fija el contenido escrito. Es la lección del bloqueante del `mapa.py`: la serialización no se justifica, se fija. Reinyectado uno a uno, **muere**.

### 7. `evals/revision/huella.py:57` [booleano]

- Original: `{"_doc": _DOC, "tablas": ordenadas}, ensure_ascii=False, indent=2, sort_keys=True`
- Mutado:   `{"_doc": _DOC, "tablas": ordenadas}, ensure_ascii=False, indent=2, sort_keys=False`

#### Análisis

- **Por qué ningún test lo caza**: porque no hay nada que cazar. El envoltorio que escribe `guardar` solo tiene `_doc` y `tablas`, ya en orden alfabético, y dentro hay **listas, no dicts**, así que `sort_keys` no tiene nada que ordenar. Comprobado ejecutando `json.dumps` con `True` y con `False` sobre la huella real del repositorio (35.668 bytes) y sobre unas tablas deliberadamente desordenadas: **idéntico en los dos casos**. El orden que sí importa —el de las tablas y el de sus claves— lo fija el `sorted()` de `guardar`, y de eso sí hay test.
- **Decisión**: MUTANTE EQUIVALENTE, justificado. **No es el caso de `mapa.py`**, donde la misma justificación resultó falsa: allí cada registro es un `dict` montado en el orden de `CAMPOS`, que NO es alfabético, y por eso `sort_keys` sí cambiaba el fichero. La diferencia es que aquí se ha comprobado ejecutando en vez de razonado.

### 8. `evals/revision/huella.py:76` [not]

- Original: `if not campos:`
- Mutado:   `if campos:`

#### Análisis

- **Por qué sobrevivía**: con `if campos`, `anotar` se saltaría justo las tablas cuya identidad está declarada y anotaría las que no: la huella quedaría vacía y no se retiraría nada nunca.
- **Decisión**: TEST NUEVO — `test_f045_r17_anotar_recoge_las_tablas_con_clave_declarada` y `test_f045_r17_anotar_sin_ninguna_clave_declarada_no_anota_nada`. Reinyectado uno a uno, **muere**.

### 9. `evals/revision/informe.py:101` [comparacion]

- Original: `destino = "y a partir de ahora tiene que salir **VERDE**" if ahora == NO_REGRESION else (`
- Mutado:   `destino = "y a partir de ahora tiene que salir **VERDE**" if ahora != NO_REGRESION else (`

#### Análisis

- **Por qué sobrevivía**: el informe diría «tiene que salir VERDE» del caso que acaba de convertirse en defecto conocido, y al revés: manda a mirar el caso equivocado.
- **Decisión**: TEST NUEVO — `test_f045_r14_el_informe_no_confunde_la_direccion_del_cambio`. Reinyectado uno a uno, **muere**.
