<!-- progress/mutacion_F-072_arnes.md -->
# F-072 · Campaña de mutación

Generado por `python -m harness.mutacion --feature F-072` el 2026-10-16 19:46.

## Alcance

Origen del diff: **rama** (`d79b3d99938a165339f4bfda7c9a08c4f93ffff8` .. `feature/F-072-cache-con-dependencias`).

| Fichero | Líneas en alcance |
|---|---|
| `harness/cache_suites.py` | 394 |
| `harness/servicios.py` | 94 |
| **Total** | **488** |

## Totales

| Métrica | Valor |
|---|---|
| Mutantes generados | 72 |
| Mutantes evaluados | 72 |
| Muertos | 65 |
| Supervivientes | 7 |
| Timeouts | 0 |
| Sin veredicto (base rota) | 0 |
| Tiempo total | 3674.5 s |
| SHA de HEAD medido | `576f464dbc974ecf50ac83de496301456fd8ff8b` |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-072_9bxx01o9/wk_0` | 225.0 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-072_9bxx01o9/wk_1` | 231.0 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-072_9bxx01o9/wk_2` | 224.8 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-072_9bxx01o9/wk_3` | 225.0 |
| Media por mutante evaluado (s) | 51.0 |
| Timeout efectivo por mutante (s) | 462 — derivado de la línea base × 2.0 |
| Suelo configurado (s) | 120 |
| Workers | 4 |
| Muestreo | no: campaña completa |

## Supervivientes

Cada superviviente es una línea que ningún test comprueba de verdad, o una mutación equivalente. Distinguirlo es trabajo del implementer: ningún análisis puede quedarse sin completar al cerrar la feature.

### 1. `harness/cache_suites.py:78` [booleano]

- Original: `@dataclass(frozen=True)`
- Mutado:   `@dataclass(frozen=False)`

#### Análisis

> Por qué ningún test lo caza: Ningún test comprobaba que `Sondeo` fuera inmutable: todos lo construían y lo leían.
> Decisión: **MUERTO con test nuevo**. `test_f072_r7_el_sondeo_es_inmutable` (asignar `tiene_coverage` lanza `FrozenInstanceError`). Con el mutante aplicado a mano: `1 failed` (salida en `progress/impl_F-072.md`).

### 2. `harness/cache_suites.py:86` [booleano]

- Original: `@dataclass(frozen=True)`
- Mutado:   `@dataclass(frozen=False)`

#### Análisis

> Por qué ningún test lo caza: Igual que el 1, con `Decision`.
> Decisión: **MUERTO con test nuevo**. `test_f072_r22_la_decision_es_inmutable`. Con el mutante aplicado a mano: `1 failed`.

### 3. `harness/cache_suites.py:110` [booleano]

- Original: `text=True,`
- Mutado:   `text=False,`

#### Análisis

> Por qué ningún test lo caza: `_git` pasa `encoding="utf-8"` y `errors="replace"`. En CPython, `Popen` abre las tuberías en modo texto si hay `encoding`, `errors` o `text` (`self.text_mode = encoding or errors or text`), así que `text=False` no cambia nada: `stdout` sigue siendo `str` decodificado en UTF-8.
> Decisión: **EQUIVALENTE (RM5, demostración ejecutable)**. Demostración: `python -c "import subprocess,sys; r=subprocess.run([sys.executable,'-c','print(\"ñ\")'],capture_output=True,text=False,encoding='utf-8',errors='replace'); print(type(r.stdout).__name__, repr(r.stdout))"` imprime `str 'ñ
'`, igual que con `text=True`. Pendiente de la aceptación escrita del humano.

### 4. `harness/cache_suites.py:122` [logico]

- Original: `if proceso.returncode != 0 or not hash_objeto:`
- Mutado:   `if proceso.returncode != 0 and not hash_objeto:`

#### Análisis

> Por qué ningún test lo caza: Los tests reales de git nunca dan un `returncode != 0` con algo en stdout (con `--verify --quiet` git calla), ni un 0 con stdout vacío: las dos ramas del `or` solo se distinguían con un git que se comporta raro.
> Decisión: **MUERTO con test nuevo**. `test_f072_r12_git_que_falla_aunque_imprima_algo_no_da_hash` y `test_f072_r12_git_que_sale_bien_sin_hash_no_da_hash` (con `_git` falso). Con el mutante: `2 failed`.

### 5. `harness/cache_suites.py:167` [booleano]

- Original: `text=True,`
- Mutado:   `text=False,`

#### Análisis

> Por qué ningún test lo caza: Mismo caso que el 3, en `sondear`: también pasa `encoding="utf-8"` y `errors="replace"`.
> Decisión: **EQUIVALENTE (RM5, demostración ejecutable)**. La misma demostración del 3. Pendiente de la aceptación escrita del humano.

### 6. `harness/cache_suites.py:172` [booleano]

- Original: `check=False,`
- Mutado:   `check=True,`

#### Análisis

> Por qué ningún test lo caza: El test de salida con error usaba un `subprocess.run` falso que ignora `check`, y la sonda real nunca salía con código distinto de 0.
> Decisión: **MUERTO con test nuevo**. `test_f072_r15_sonda_real_que_sale_con_error_da_error_de_sonda` (un padre que hace `SystemExit(3)` al importarse: la sonda real sale con 3 y debe dar `ErrorDeSonda`) y la aserción `check is False` en `test_f072_r16_sonda_con_el_interprete_y_la_carpeta_del_servicio`. Con el mutante: `2 failed`.

### 7. `harness/cache_suites.py:361` [booleano]

- Original: `analizador.add_argument("--servicio", required=True)`
- Mutado:   `analizador.add_argument("--servicio", required=False)`

#### Análisis

> Por qué ningún test lo caza: Ningún test llamaba a `main` sin `--servicio`; sin `required`, el nombre `None` acababa en «no está declarado» con código 1 en vez del error de uso.
> Decisión: **MUERTO con test nuevo**. `test_f072_r22_sin_servicio_es_un_error_de_uso` (`SystemExit` con código 2 y `--servicio` en stderr). Con el mutante: `1 failed`.

## Resumen del análisis (implementer)

- 5 de 7 supervivientes eran huecos reales: 6 tests nuevos los matan, comprobado aplicando cada mutante a mano
  (1, 2, 4, 6 y 7). Ningún test se escribió quitando código defensivo (RM6 no aplica).
- 2 de 7 (3 y 5) son equivalentes: `text=False` junto a `encoding=` no cambia el modo de las tuberías. Demostración
  ejecutable arriba; quedan pendientes de la aceptación escrita del humano.
- Reproducción de los dos equivalentes: con `text=False` en las líneas 110 y 167 a la vez, los 154 tests de
  F-072 (`python -m pytest tests/test_f072_*.py -q -p no:cacheprovider`) dan `154 passed`; restaurado después.
- No se relanza la campaña: los tests nuevos no tocan código de producción y cada muerte se ha reproducido a mano.
