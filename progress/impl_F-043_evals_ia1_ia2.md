<!-- progress/impl_F-043_evals_ia1_ia2.md -->
# F-043 · IA1 e IA2 del lote SALMEDINA — HECHO

Banco de evals completado con las fases **IA1** e **IA2** de los siete albaranes
de SALMEDINA (`B82899550`). **Opción A**, decidida por el humano el 2026-09-11:
IA1 mide **lo impreso en el papel**.

Índices: **IA1 0 → 7**, **IA2 0 → 7**. `bash harness/init.sh` en verde. Cero
llamadas a LLM. No se ha tocado código de producción.

> Este informe sustituye a la versión que cerró en `blocked` el mismo día. El
> diagnóstico de aquella (§1–§3) sigue vigente y es lo que motivó la decisión;
> aquí queda lo ejecutado.

## 1. Qué son estos albaranes (y por qué mandaba la pregunta)

Los siete PDF no son albaranes comerciales: son el impreso legal **«DOCUMENTO DE
IDENTIFICACIÓN / DOCUMENTO DE CONTROL» (Art. 6 RD 553/2020)**, con una rejilla
de 12 códigos LER preimpresos donde el operario escribe a mano el volumen del
residuo que se lleva.

El papel **no imprime** concepto de línea, ni precio, ni importe, ni código de
obra, ni forma de pago. Lo que el Excel de negocio da en esas columnas
(«CAMBIO CONTENEDOR 6M3», `1,00 UD`, 120 €, obra 687) es la vista **ya
valorada**. De ahí la parada, y de ahí la Opción A.

## 2. Lo sembrado, caso a caso

Transcrito del papel; los LER se cruzaron con el Excel y **coinciden 7 de 7**.

| caso_id | Nº albarán | Fecha | Fila LER marcada | Denominación impresa | VOL m³ |
|---|---|---|---|---|---|
| RES-001 | SS-0000168 | 2024-07-03 | 17 02 01 | Madera | 6 |
| RES-002 | SS-0003935 | 2024-07-16 | 17 01 07 | Horm_Ladr_Cerám. | 6 |
| RES-003 | SS-0000589 | 2024-07-08 | 17 08 02 | Mat. Yeso | 6 |
| RES-004 | SS-0003967 | 2024-07-10 | 17 06 04 | Mat. Aislamiento | 6 |
| RES-005 | **SS-0001977** | 2024-07-18 | 17 06 04 | Mat. Aislamiento | 6 |
| RES-006 | SS-0025146 | 2024-11-05 | 17 09 04 | Mat. Mezclados | 6 |
| RES-007 | SS-0026122 | 2024-11-05 | 17 08 02 | Mat. Yeso | **9** |

### IA1 · TABLA 1 (cabeceras), 7 filas

| Campo | Valor | Por qué |
|---|---|---|
| `proveedor_nombre` | `SALMEDINA TRATAMIENTO DE RESIDUOS INERTES, S.L.` | **Preimpreso** en la casilla RAZÓN SOCIAL de los siete. Coincide literalmente con el Excel |
| `fecha`, `numero_albaran` | ver tabla | Impresos / manuscritos y legibles en los siete |
| `fichero_albaran` | `RES-00N.pdf` | El nombre que manda el LEEME |
| `obra_codigo` | **vacío** (= null) | 687/691 son códigos de Sigrid; el papel solo trae una dirección |
| `forma_pago` | **vacío** (= null) | El documento no tiene sección de pago |
| `proveedor_cif` | **`?`** (no se compara) | La casilla CIF/NIF está vacía. El único CIF visible está dentro de un sello, y **en RES-001 y RES-002 ese sello es de «CCR LAS MULAS, S.L.U.», otra empresa**. No es decidible |
| `obra_nombre` | **`?`** | El papel trae la dirección **manuscrita** y distinta en cada uno («M-401 S/N», «Ctra. M-401 km 1'800», «Ctra. 401 Madrid-Toledo p.k. 1800»). Es campo **crítico** (patrón `*obra*`): exigir una transcripción exacta de la caligrafía sería una moneda al aire |

### IA1 · TABLA 2 (líneas), 7 filas — **una por caso**

`num_linea` = 1; `descripcion_esperada` = la denominación impresa; `cantidad` =
6 (9 en RES-007).

Vacíos (= null) y por qué: `precio_unitario` e `importe`, porque **el propio
Excel declara** en sus columnas «viene en albarán o valorado en contrato?» que
son `CONTRATO` (`OFERTA` en RES-007), nunca `ALBARAN`; `descuentos`, que no
existen en el documento; `codigo_imputacion`, porque `CI.03A.7` es de Sigrid;
y `unidad`, porque la línea no escribe unidad (el «m³» es el rótulo de la
columna) y F-024 ya fijó `unidad_medida = null` en los siete.

### IA2 · CONTEXTO ESPERADO, 21 filas (3 campos × 7 casos)

| `campo_contexto` | Valor |
|---|---|
| `tipo_familia` | `residuos` |
| `codigo_ler` | `170201` / `170107` / `170802` / `170604` / `170604` / `170904` / `170802` |
| `volumen_m3` | `6` (`9` en RES-007) |

**Formato del LER: 6 dígitos, sin espacios** (`17 08 02` → `170802`). Lo fijan a
la vez el LEEME de IA2 («6 dígitos sin espacios») y el contrato de código
(`contexto_linea.py`: *«Sin espacios ni puntos»*), y coincide con el
`codigo_ler` ya sembrado en las CONDICIONES de `INPUTS`. No hubo que añadir ni
quitar ceros: los 12 LER del impreso ya son de 6 dígitos.

## 3. Dos desvíos de la instrucción literal, y por qué

**No sembré `tamano_contenedor` ni `movimiento`.** Los dos venían en el encargo
(y en mi propia propuesta), tomados de la lista del LEEME — que se declara
**«orientativo, usa los reales del contexto»**. Al comprobar el contrato
canónico `services/albaranes-comun/ruesma_comun/contratos/contexto_linea.py`,
**ninguno de los dos existe**: los campos reales son `tipo_familia`,
`rol_linea`, `codigo_ler`, `volumen_m3`, `peso_toneladas`, `contenedores`,
`contenedores_entregados`, `contenedores_retirados`.

Sembrarlos habría sido peor que inútil: `campo_contexto` es **crítico** y
`proyectar_ia2` descarta los campos nulos, así que una fila con un campo que el
sistema no emite **nunca** casa y da FALLO fijo («fila del ground truth que el
sistema no ha producido»). El tamaño del contenedor no es un dato de la línea:
vive en el contrato, y ya está sembrado como `tamano_contenedor_contrato` en las
CONDICIONES de `INPUTS`.

**El `movimiento` tampoco es decidible aunque existiera**, que era el motivo por
el que iba a ir en `?`: los siete papeles traen **rellenas a la vez** «Nº cont.
LLEVADA» y «Nº cont. RETIRADA» — son cambios de contenedor. Y lo que hay escrito
ahí son **identificadores** de contenedor («6224», «2008», «6M 6550»), no
recuentos, así que tampoco alimentan `contenedores_entregados` /
`contenedores_retirados`. Por esa misma razón esos dos campos quedan **sin fila**
(no en `?`): una fila `?` de un campo que puede salir nulo falla igual.

**Tampoco sembré `peso_toneladas`.** El papel trae «Cantidad Recibida: ____ kgs»
manuscrito, pero no estaba en la lista decidida, la caligrafía es dudosa y
algunos valores son inverosímiles (20 kg para 6 m³ en RES-006). Queda fuera y
dicho.

## 4. La alineación de `descripcion` no hizo falta

El punto 4 del encargo preveía un choque entre la `descripcion` de IA1 y la de
`INPUTS`. **No se produjo.** Al abrir el libro, `INPUTS.LINEAS_ALBARAN` ya traía
`170201 MADERA`, `170802 MATERIALES DE CONSTRUCCION A BASE DE YESO`… es decir,
**la denominación del residuo con el LER delante**, no el concepto del contrato.
Mi lectura previa del informe de siembra («reconstruida de las columnas LER y
Concepto») me había hecho temer un `170802 CAMBIO CONTENEDOR 6M3` que no existe.

Así que `INPUTS` es ya coherente con la Opción A y **no se tocó**: IA1 guarda el
texto literal del papel («Mat. Yeso») e `INPUTS` su convención declarada
`<LER> <concepto>`. La diferencia es de forma, `descripcion*` es **laxo**, y
cambiarlo habría movido el estímulo de IA3 sin ganar nada.

Corrobora la decisión el test ya aprobado de este mismo albarán,
`services/albaran-valoracion-persist/tests/test_f043_r26_ss0003967.py:57`, que
modela la línea como `CONCEPTO = "RETIRADA MATERIALES DE AISLAMIENTO"` —la
denominación del residuo—, no como el concepto del contrato.

## 5. RES-005: `SS-0801977` → `SS-0001977`

Corregido en el banco, como se decidió. El papel imprime `SS - 0001977` en la
misma tipografía roja que los otros seis; `0801977` era una mala lectura del
sistema consagrada como ground truth.

Cuatro celdas, en dos libros: `INPUTS.xlsx!CASOS!F7`,
`INPUTS.xlsx!CONDICIONES!C24`, `RESULTADO_FINAL.xlsx!Residuos!G7` y
`!L7`. De ahí a los fixtures `inputs/RES-005.json`, `final/RES-005.json` e
`IA1/RES-005.json`.

**La divergencia queda escrita, no borrada.** El comentario del caso dice ahora,
literalmente: *«Numero corregido el 2026-09-11 contra el PDF: el papel imprime
SS-0001977 (el Excel lo numera '1977'). SS-0801977 era una mala lectura del
sistema; la BBDD local sigue guardando el documento como SS-0801977 y por eso
diverge del banco (§8.5).»* **La BBDD local NO se ha tocado.**

Y no se reescribe el pasado: `progress/impl_F-043_evals_banco.md` sigue citando
`SS-0801977` en su tabla y en §2. **Nota para `current.md`:** ese informe está
superado en ese punto por esta corrección.

## 6. El hallazgo que tapaba tener los libros vacíos

**IA1 e IA2 darán fallos falsos hasta que se les pase su lista de
`observables`.** `evals/runner.py:306` compara las dos fases con
`observables=None`, es decir **comparando todas las columnas del libro**,
incluidas las de papeleo. IA3 e IA4 no lo hacen: pasan una lista explícita
(`runner.py:196` y `:398`) que deja fuera `caso_id` y `comentario`.

Consecuencia, con el libro ya relleno: cada caso de IA1 sumará dos FALLOS
críticos (`caso_id` y `fichero_albaran`, que la proyección de sv2 no produce
porque no son datos extraídos) y cada fila de IA2 uno (`caso_id`) — **21 en
IA2**. `comentario` solo dará AVISO (patrón `comentario*` es laxo), pese a que
el LEEME promete que *«no lo lee el eval»*.

No lo he tapado poniendo `?` en esas celdas: eso escondería el defecto y
perdería el nombre del fichero. **El arreglo es una línea**, del mismo tipo que
ya existe para IA4 — pasar `observables=(...)` en `_comparar_tablas_de` para
IA1 e IA2—, pero es un cambio de diseño del banco y lo decide el humano, no una
siembra. Este defecto era invisible mientras los dos libros estaban vacíos.

## 7. Verificación ejecutada

### Conversor (fixtures + barrido de datos sensibles)

```
$ python -m evals.conversor
6 libro(s) convertidos, 41 fichero(s) escritos (FINAL: 7, IA1: 7, IA2: 7, IA3: 7, IA4: 0, INPUTS: 7)
```

**IA1 e IA2 pasan de 0 a 7**, que era el criterio del punto 6 del encargo. El
barrido de C3 bis corre dentro del conversor y **no encontró nada**: si hubiera
saltado, no se habría escrito ni un fichero.

### Runner determinista, antes y después (cero coste)

```
$ python -m evals.runner --feature F-043 --informes <scratchpad>/despues
ROJO  (exit 1)
$ diff <(grep -E "FALLO|AVISO" base/evals_F-043.md) <(grep -E "FALLO|AVISO" despues/evals_F-043.md)
   → SIN CAMBIOS
```

**Ni un fallo ni un aviso de diferencia** con la línea base tomada antes de
tocar nada: los 18 fallos de IA3 y los de E2E son exactamente los mismos, todos
de la causa ya documentada (los importes ×6 por `volumen_m3` sin propagar). La
siembra de IA1/IA2 y la corrección de RES-005 **no han movido nada**. Se lanzó
**sin `--con-llm`** y con el informe fuera de `progress/`, para no ocupar el
nombre que T30 tiene que producir.

### Los `.xlsx` y los PDF, fuera de git

```
$ git ls-files "*.xlsx"          → (vacío)
$ git status --porcelain evals/  → solo ficheros .json
$ git check-ignore -v evals/ground_truth/IA1_extraccion.xlsx
.gitignore:18:*.xlsx    evals/ground_truth/IA1_extraccion.xlsx
```

Los siete PDF siguen ignorados (`.gitignore:16:*.pdf`). Sigue en pie el aviso de
que hay **un PDF preexistente en el índice**,
`services/albaranes-api/worker_input/0695 - Albaranes 2026.03.09-13-16.pdf`,
entrado en `df01ef4` con la importación de `albaranes-api`: **queda como asunto
aparte y no se ha tocado.**

## 8. Dónde acabaron los PDF

Movidos (`mv`, no copiados) de `evals/fixtures/inputs/SALMEDINA_<n>.pdf` a
**`evals/inputs/albaranes/<caso_id>.pdf`**, los siete.

**No es la ruta que decía el encargo** (`evals/fixtures/inputs/albaranes/`). Usé
la que mandan a la vez el código (`evals/procesos/sv2_extraccion.py:36` →
`RUTA_ALBARANES = RAIZ_REPO / "evals" / "inputs" / "albaranes"`), el LEEME de IA1
y el README. En `evals/fixtures/` el runner no los habría encontrado nunca. De
paso, la carpeta **versionada** `evals/fixtures/inputs/` ya no contiene
documentos de proveedor.

## 9. ¿Es T30 ejecutable en modo completa? Todavía no: falta una cosa y media

1. ~~Los PDF en su sitio~~ → **hecho** (§8).
2. ~~`IA1_extraccion.xlsx` e `IA2_contexto.xlsx` rellenos~~ → **hecho**: 7 y 7.
3. **Propagar las CONDICIONES al `contexto_linea`** en `evals/procesos/sv6_build.py`
   (`construir_envelope_estimulado`) y `evals/procesos/sv5_valoracion.py`
   (`construir_contexto`). Es el agujero de `progress/impl_F-043_evals_banco.md`
   §5: sin `volumen_m3` la regla 4.bis de residuos no se ejecuta y los importes
   salen ×6. **Sigue abierto** y es el único bloqueante real del verde.
4. **El `observables` de IA1/IA2** (§6): sin él, las dos fases nuevas darán 14 +
   21 fallos de papeleo que no son ground truth. No impide *ejecutar* T30, pero
   sí leerlo.
5. **Claves LLM en el entorno** y el `--con-llm`, que **autoriza el humano**. No
   se lanzó: **cero euros**.

Con 3 y 4 resueltos, T30 es ejecutable de verdad; RES-007 seguirá en rojo por
diseño hasta F-017, como pidió el humano.

## 10. Ficheros tocados

- `evals/ground_truth/IA1_extraccion.xlsx`, `IA2_contexto.xlsx` — rellenados;
  `INPUTS.xlsx`, `RESULTADO_FINAL.xlsx` — 4 celdas de RES-005. **NO versionados.**
- `evals/fixtures/IA1/RES-00{1..7}.json`, `evals/fixtures/IA2/RES-00{1..7}.json`
  — **14 nuevos, versionados**, tras el barrido.
- `evals/fixtures/{IA1,IA2,inputs,final}/_indice.json` y los 14 fixtures de
  `inputs/` y `final/` — solo cambia `sha256_libro` salvo en RES-005.
- `evals/inputs/albaranes/RES-00{1..7}.pdf` — movidos, **NO versionados**.
- `progress/impl_F-043_evals_ia1_ia2.md`, `progress/current.md`.

Sin cambios en `services/`, `harness/` ni `evals/*.py`.

## 11. Evidencias

| Evidencia | Valor |
|---|---|
| Tests ejecutados (`bash harness/init.sh`) | **556 passed**, 0 fallos |
| Tiempo de la suite raíz | 196,69 s |
| Cobertura de líneas cambiadas | **89,8 %** (633/705, umbral 80 %, nivel crítico) |
| Veredicto de `init.sh` | **ENTORNO LISTO** (verde) |
| Casos en IA1 / IA2 | **7 / 7** (antes 0 / 0) |
| Filas escritas | IA1: 7 cabeceras + 7 líneas · IA2: 21 de contexto |
| Fixtures nuevos versionados | **14** |
| Barrido de datos sensibles (C3 bis) | **0 hallazgos** |
| Regresión en el runner determinista | **0** (diff vacío contra la línea base) |
| PDF leídos y transcritos | 7/7 |
| LER del Excel confirmados contra el papel | **7/7** |
| Filas `DEDUCIDA` en las 11 filas SALMEDINA | **0** |
| `.xlsx` en el índice de git | **0** |
| `.pdf` en el índice de git | **1, preexistente y ajeno** (§7) |
| Llamadas a LLM / coste | **0 / 0 €** |

**Fase RED**: no aplica — esta tarea no escribe código ni tests; su artefacto es
ground truth. La evidencia equivalente es el **diff vacío** del runner: la
siembra no mueve el veredicto del sistema, y las fases nuevas nacen medibles en
vez de nacer verdes. **Mutación y cobertura de líneas cambiadas**: no aplican,
no hay líneas de Python nuevas (la cobertura de la tabla es la del estado de la
rama, no de este trabajo).

## 12. Para que el líder lo arrastre a `current.md`

1. **`SS-0801977` → `SS-0001977`** en RES-005. `progress/impl_F-043_evals_banco.md`
   queda **superado en ese punto**. La BBDD local sigue con `SS-0801977`: no se
   tocó, y la divergencia está escrita en el comentario del caso.
2. **IA1/IA2 necesitan su `observables`** (§6) o darán 35 fallos de papeleo.
3. **Sigue abierto** el agujero de las CONDICIONES sin propagar al
   `contexto_linea` (§9.3): es lo único que impide el verde de T30.
