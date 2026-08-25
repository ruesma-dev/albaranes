<!-- progress/impl_F-036_correcciones_BCD.md -->
# F-036 · Correcciones del RECHAZO de los bloques B, C y D

Ciclo de corrección sobre `progress/review_F-036_bloques_BCD.md` (veredicto
RECHAZADO: 2 bloqueantes + 6 cambios requeridos). **No se implementó nada
nuevo** fuera de ese encargo. La feature sigue `blocked` por F-043 y
`harness/features.json` NO se ha tocado. T11 sigue retirada y no se ha
restaurado ni rodeado.

| Commit | Punto del review |
|---|---|
| `2025e08` | **CR-1** · bloqueante 1: la doc deja de decir que sv5 consume el LER |
| `a6d4e47` | **CR-2** · bloqueante 2: R19 tampoco hereda los m³ sin contenedores |
| `c54de49` | **CR-3** · cambio 1: una fecha deja de leerse como código LER |
| `89769aa` | **CR-4** · cambio 2: la congelación de motivos ve las constantes |
| `ae3548a` | **CR-5** · cambio 3: `_tiene_valor` separa el `bool` del cero |
| `5c4807f` | **CR-6** · cambio 6: las nueve medidas se contrastan con el modelo |
| `414ce70` | **CR-7** · cambio 4: R25 declara sus DOS precondiciones |
| `5edd058` | **CR-8** · cambio 5: `pytest`/`coverage` en el README de sv4 |

---

## BLOQUEANTE 1 · documentación viva de una regla retirada — `2025e08`

Los tres sitios reescritos para decir la verdad (consumidores reales hoy: sv2
en `tipologia_resolver`, sv6 en `residuos_incrementos` y
`modifier_contract_matcher`), y en los dos de producción se deja escrito
además que **sv5 NO es consumidor** y por qué, con la fecha y el commit
`7ca2ffc`, para que nadie lo "restituya" creyendo que falta:

- `services/albaranes-comun/ruesma_comun/ler.py` (cabecera).
- `services/albaranes-api/domain/models/tipologia.py` (bloque de R14).
- `specs/.../requirements.md` R14 — **reescrito, no añadido**: el fichero
  sigue en 149/150 líneas.

Verificación: es documentación, sin test. `grep` posterior sobre el árbol: no
queda ninguna afirmación de que sv5 use el catálogo. Suites de comun y sv2 en
verde (abajo).

## BLOQUEANTE 2 · R19 se incumplía por el camino sin contenedores — `a6d4e47`

**Fase RED** (`services/albaran-valoracion-persist/`, 3 tests nuevos):

```
$ python -m pytest tests/test_f036_r16_r19_sinteticas_ler.py -k "sin_contenedores" -q
>       assert syn.cantidad_albaran is None
E       AssertionError: assert 6.0 is None
...
>       assert "residuos_sintetica_sin_cantidad" in syn.review_reasons
E       AssertionError: assert 'residuos_sintetica_sin_cantidad' in ['inherited_from_base_line']
...
>       assert cabecera.total_valorado == pytest.approx(
            base_de(registros).importe_calculado
        )
E       assert 1026.0 == 720.0 ± 7.2e-04
3 failed, 23 deselected in 0.71s
```

**1026,00** reproduce exactamente lo que midió el reviewer (306,00 de
incremento fantasma sobre una base de 720,00).

**Arreglo** (`valuation_builder.py:1440-1478`): en residuos la herencia deja de
tener fallback. Si el padre es de residuos, la cantidad es
`parent_record.cantidad_convertida` **y punto** —aunque sea `None`—; ya no cae
al `elif` de `cantidad_albaran` ni al de `parent_albaran.cantidad`. La razón,
escrita en el propio código: no sabemos cuántos contenedores son, así que no se
inventa ninguno. R19 no admite excepciones.

**Su razón**: constante nueva `RAZON_SIN_CANTIDAD =
"residuos_sintetica_sin_cantidad"` en `residuos_incrementos.py`, que el builder
emite cuando una sintética de `gestion_residuos` se queda sin cantidad, con
`review_required = True`. Sin ella la línea aparecería muda y el revisor no
sabría si es un cero real o un dato que falta.

Verde: `180 passed` en sv6 (era 175 antes de este ciclo).

**Lo que NO se tocó, como pidió el líder**: los 720,00 € que la línea base saca
en ese escenario (6 m³ × 120) son el fallback preexistente de
`importe_calculator`, no una regresión de F-036. El tercer test lo dice por
escrito y compara el total contra el importe de la base, no contra un número
fijo, para no congelar ese fallback.

## Cambio 1 · una fecha no es un código LER — `c54de49`

**Fase RED**:

```
$ python -m pytest tests/test_f036_r16_r19_sinteticas_ler.py -k "una_fecha_no_es" -q
>       assert es_linea_incremento_ler("INCREMENTO TARIFA DESDE 01-01-25") is None
E       AssertionError: assert '010125' is None
1 failed, 26 deselected in 0.55s
```

**Arreglo, sin duplicar la defensa**: en `ruesma_comun/ler.py` se extrae
`ler_creible(texto) -> str | None`, que ES el cuerpo que ya tenía
`texto_contiene_ler` devolviendo el código en vez de un booleano;
`texto_contiene_ler` pasa a ser `ler_creible(t) is not None`. `es_linea_incremento_ler`
usa `ler_creible` en lugar de `normalizar_ler`. Un test parametrizado en comun
fija que las dos funciones no puedan divergir nunca.

Por qué en comun y no una guarda local en sv6: R14 exige que el catálogo y su
validador vivan en un solo sitio; la defensa de forma-fecha es parte del
validador, no una regla de sv6. `normalizar_ler` se queda como está —es para
campos que ya se sabe que traen un código, como `contexto_linea.codigo_ler`— y
la docstring nueva dice cuál usar cuándo.

Verde: comun `75 passed, 3 skipped`; sv2 `58 passed`; sv6 `179 passed`.

**Observado y NO cambiado** (fuera del encargo, para el reviewer): `claves_dedupe`
también llama a `normalizar_ler` sobre texto libre (`dto.descripcion_linea`).
Con las sintéticas de esta red no falla —todas se llaman "INCREMENTO LER
NNNNNN", que lleva el token— pero una sintética de IA3 cuyo texto trajera una
fecha produciría una clave de dedupe espuria. No se tocó porque cambiaría el
comportamiento de R18, que el reviewer dio por bueno.

## Cambio 2 · el agujero de la congelación de motivos — `89769aa`

Se eligió la opción que el líder prefería: **tapar el agujero**, no solo añadir
la cadena. `_motivos_de` (`tests/test_f027_r18_r22_contrato.py`) ahora construye
una tabla de símbolos con las constantes de cadena del módulo **y las
importadas** de otro fichero de sv6 (`_constantes_str`, `_tabla_de_simbolos`), y
`_texto_de` resuelve `ast.Name`.

**Fase RED** — el arreglo del helper es lo que destapa lo que se había colado:

```
$ python -m pytest tests/test_f027_r18_r22_contrato.py -q -k "no_introduce_ni_retira"
>       assert _motivos_de(VALUATION_BUILDER) == MOTIVOS_DEL_BUILDER
E       AssertionError: ...
E         Extra items in the left set:
E         'residuos_ler_sin_tarifa_en_contrato'
E         'residuos_sintetica_sin_cantidad'
1 failed, 1 passed, 7 deselected in 0.57s
```

Los dos motivos entran en `MOTIVOS_DEL_BUILDER` **con la comprobación de
consumidores de T25, rehecha**: sv6 solo los escribe; sv4 pinta
`review_reasons_json` en crudo —su
`tests/test_f036_r23_r24_trazabilidad.py:313` afirma la cadena sobre el HTML—,
sin lista blanca que ampliar. Test nuevo
`test_f027_r22_la_congelacion_ve_los_motivos_escritos_como_constante`: el
guardián del guardián, para que la resolución de nombres no se pierda en un
refactor. Verde: `10 passed`.

## Cambio 3 · `_tiene_valor` separa el `bool` del cero — `ae3548a`

**Fase RED** (sv3, 8 tests nuevos):

```
$ python -m pytest tests/test_f036_r9_r12_contexto_merger.py -q -k "cero"
>       assert elegido.volumen_m3 == 6.0
E       AssertionError: assert 0.0 == 6.0
...
8 failed, 29 deselected in 0.60s
```

**Arreglo**: `bool` primero (por `False == 0` en Python) y devuelve `True`;
`int`/`float` después, con `valor != 0`. Las siete medidas numéricas no tienen
sentido a cero —no hay retiradas de 0 m³— así que un 0 ahí es «no lo sé» y debe
dejar el hueco abierto para R11. `carga_incompleta=False` sigue contando como
dato (su test previo sigue en verde). `ref_linea_base` no pasa por
`_tiene_valor`, así que el `0` narrativo tampoco cambia.

Verde: sv3 `125 passed` (eran 117).

## Cambio 4 · la SEGUNDA precondición de R25 — `414ce70`

Escrita **en la docstring del escenario** (`test_f036_r25_salmedina_importes.py`,
sección ALCANCE reescrita: ahora enumera las dos precondiciones y dice que el
importe de SS-0003967 está demostrado **bajo hipótesis**) y en el resumen para
el humano (abajo).

Además se fija como test, igual que ya lo estaba la primera:
`test_f036_r25_con_el_match_real_de_ss_0003967_no_se_llega_a_210`. Sonda propia
con el builder real, `tipo_familia='residuos'` y el match real a la línea 26481:

```
[builder][guard-residuos] la linea base merge=700 venia casada con
contrato_line_id=26481 ('INCREMENTO LER 170604 ...'): match ANULADO.
total_valorado = 90.0
base: precio= None importe= None reasons= [... 'residuos_base_casada_con_incremento' ...]
syn: INCREMENTO LER 170604  1.0  90.0  90.0
```

**90,00 € frente a los 210,00 de R25**, confirmando la medición del reviewer.

**Sin fase RED, y es deliberado**: es un test de caracterización de un
comportamiento que NO cambia (la guarda de R15 hace lo correcto). No hay código
nuevo que pudiera fallar antes; exhibir un rojo artificial sería teatro.

## Cambio 5 · `pytest` y `coverage` en el venv de sv4 — `5edd058`

Resuelto como indicó el líder: sección nueva al principio de
`services/albaranes-front/README.md`, con el comando exacto que ejecuta
`init.sh`, qué pasa sin cada paquete, el `pip install` para PowerShell y el
motivo de que NO vaya en `requirements.txt` (es lo que se hornea en producción)
ni en un `requirements-dev.txt` (la dependencia la impone el arnés, no el
servicio). Sin test: es documentación.

## Cambio 6 · las nueve medidas, contrastadas con `ContextoLinea` — `5c4807f`

**Fase RED**, inyectando una décima medida (`kilometros_transporte`) en
`ruesma_comun/contratos/contexto_linea.py` y revirtiéndola después:

```
$ python -m pytest tests/test_f036_r9_r12_contexto_merger.py -q -k "son_exactamente_los_nueve"
>       assert list(_CAMPOS_RESIDUOS) == [
            c for c in campos_del_modelo if c not in _NARRATIVOS
        ]
E       AssertionError: At index 8 diff: 'exceso_declarado_min' != 'kilometros_transporte'
E         Right contains one more item: 'exceso_declarado_min'
1 failed, 36 deselected in 0.52s
```

Y con la misma décima medida presente, la aserción ANTIGUA seguía pasando:

```
el modelo tiene 15 campos (5 narrativos + 10 medidas)
la asercion ANTIGUA pasa igual: no ve la decima medida
```

La tupla se deriva ahora de `ContextoLinea.model_fields` menos los cinco
narrativos, que también quedan fijados. Inyección revertida (`git checkout`),
`git status` limpio antes del commit.

---

## Verificaciones MANUAL pendientes (del humano, sin cambios)

- **T23** campaña de mutación y **T24** comprobación contra la BBDD real: no se
  lanzaron, siguen abiertas.
- `python -m evals.runner --con-llm --feature F-036`: no se lanzó (gasta LLM
  real, decisión del humano).

## Evidencias

| Evidencia | Valor |
|---|---|
| Tests ejecutados, sv6 | `180 passed in 1.37s` (eran 175) |
| Tests ejecutados, sv3 | `125 passed in 1.36s` (eran 117) |
| Tests ejecutados, comun | `75 passed, 3 skipped in 114.71s` (eran 72) |
| Tests ejecutados, sv2 | `58 passed in 0.91s` (sin cambio: solo un comentario) |
| Tests ejecutados, raíz | `532 passed in 105.39s` (eran 531) |
| Tests ejecutados, sv4 | `131 passed in 4.04s` (sin cambio de código: solo el README) |
| Cobertura de líneas cambiadas | **98,2 %** — 278/283, umbral 80, nivel `critico` |
| Mutantes / supervivientes | **NO medido a propósito**: la campaña es T23, encargo del humano, y el líder la excluyó de este ciclo |
| Tiempo de suite | el de cada línea de arriba; el total, en `init.sh` |
| Tamaño | `PUERTA TAMAÑO: F-036 dentro de los topes` |

**`bash harness/init.sh`**: ejecutado tal cual, el último y solo. Resultado y
cifras, en la sección siguiente.

### Salida de `bash harness/init.sh` — **exit 0**

Ejecutado tal cual, el último y solo (`bash harness/init.sh`; exit code
comprobado aparte: `exit=0`). Lo relevante, literal:

```
    43 features, 32 abiertas, en curso: ninguna, bloqueadas: ['F-036']
[OK] features.json válido
532 passed in 105.39s (0:01:45)
[OK] pytest en verde (con medición de cobertura)
[OK] servicio sv2-api ...: pytest en verde            (58 passed)
[OK] servicio sv3-persistencia ...: pytest en verde   (125 passed)
[OK] servicio sv4-front ...: pytest en verde          (131 passed)
[OK] servicio sv5-valoracion-api ...: pytest en verde (caché: árbol sin cambios)
[OK] servicio sv6-valoracion-persist ...: pytest en verde (180 passed)
[OK] servicio comun ...: pytest en verde              (75 passed, 3 skipped)
[OK] PUERTA COBERTURA: 98.2% de 283 líneas cambiadas cubiertas (278/283,
     umbral 80%, nivel critico)
[OK] PUERTA RUTAS SENSIBLES: N/A (sin feature en curso con rama: no hay diff
     que cotejar)
[OK] PUERTA TAMAÑO: F-036 dentro de los topes (requirements 149/150,
     design 228/250, impl 220/220)
[OK] Rama actual: feature/F-036-residuos-contenedores-e-incrementos
ENTORNO LISTO. Puedes trabajar.
```

Avisos (ninguno nuevo de este ciclo, todos preexistentes): features `blocked`
—es F-036, a la espera de F-043—; `ruff` con 1112 avisos de deuda previa; sv1 e
`infra` sin tests; marcas `[ADAPTAR]` en specs de F-034/F-035.

**`PUERTA RUTAS SENSIBLES` sigue saliendo `N/A`** por el mismo motivo que
levantó el reviewer en C4 ter (F-036 ya no es la feature en curso): el diff de
este ciclo **sí** toca rutas sensibles (`valuation_builder.py`,
`residuos_incrementos.py`, `ler.py`, `tipologia.py`). No se ha tocado
`features.json` para forzarla, porque el líder lo prohibió expresamente. El
reviewer tendrá que cotejar el diff a mano, como él mismo propuso en su
apartado de automejora.

## Nota sobre `progress/impl_F-036.md`

Estaba clavado en 220/220. Se le metió el índice al informe nuevo **sin
crecerlo**: se compactó la línea 4 y se reescribió la 7 (`Los demás informes:
impl_F-036_bloque_{B,C,D}.md y impl_F-036_correcciones_BCD.md`). Sigue en 220
líneas, así que la puerta de tamaño no se toca.
