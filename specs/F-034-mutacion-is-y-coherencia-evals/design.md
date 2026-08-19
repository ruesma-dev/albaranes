<!-- specs/F-034-mutacion-is-y-coherencia-evals/design.md -->
# F-034 · Diseño técnico

> Feature del **arnés**, no del pipeline. Encaje en `docs/ARCHITECTURE.md`:
> ninguno — `harness/` es la herramienta que mide el monorepo, vive fuera de
> la arquitectura hexagonal de los servicios y no tiene capas `domain/`,
> `application/` ni `infrastructure/`. **Límite de servicio**: no se toca
> `services/` ni `evals/` (código); no aparece ninguna responsabilidad nueva
> que exija otro servicio.

## 1. Ficheros a crear

| Ruta | Qué es |
|---|---|
| `tests/test_mutacion_operadores.py` | Tests del generador de mutantes: `is`/`is not`, delimitador de palabra, límites declarados y la guarda de coherencia de la puerta de evals (R14). |
| `progress/mutacion_F-019_remedida.md` | Salida de la campaña de R10 (`--salida`). Fichero **nuevo**: no pisa el informe histórico. |
| `progress/mutacion_F-027_remedida.md` | Salida de la campaña de R9. Ídem. |
| `progress/impl_F-034.md` | Informe del implementer (fase RED, evidencias, comandos exactos). |

> Los dos `*_remedida.md` son evidencia obligatoria de R9/R10 aunque el humano
> elija la opción **A** de D1; lo que D1 decide es si además se enlazan desde
> los informes históricos como re-medición oficial (T7).

## 2. Ficheros a modificar

### En este repositorio (`albaranes`)

| Ruta | Qué cambia |
|---|---|
| `harness/mutacion.py` | (a) `COMPARACIONES` gana `ast.Is` y `ast.IsNot`; (b) `_localizar` deja de aceptar la primera coincidencia a ciegas y exige delimitación de palabra para los tokens alfabéticos; (c) docstrings de ambos puntos con la limitación de R7. |
| `CHECKPOINTS.md` | C4 bis: punto nuevo de **campaña MANUAL** (R16). C4 ter, último párrafo (línea 185): la condición pasa a los fixtures versionados (R13/R15). |
| `.claude/agents/reviewer.md` | Punto 4 del protocolo: una frase con lo mismo que R16. |
| `harness/rutas_sensibles.json` | Clave `_exigencia` (línea 3): condición reescrita sobre `evals/fixtures/` (R13/R14). **Solo esa clave**: ni un patrón ni un `exige_lineas` se tocan. |
| `progress/current.md` | Líneas 33 y 64: la frase del `ground_truth` «inexistente» (R15). Y, al cerrar, la entrada de sesión que exige el arnés. |
| `harness/VERSION` | `ARNES_VERSION` y `ARNES_FECHA` a la versión de D2. |
| `harness/ARNES_VERSION.md` | Versión, fecha y `Modo: propagacion directa desde arnes-base`, igual que hizo el commit `3a146cd` para la 1.5.2. |
| `harness/features.json` | Estado de F-034 (`in_progress` → `done`) y, **si el humano acepta D3**, la frase corregida de su descripción. |
| `BACKLOG.md` | **No se edita a mano**: lo regenera `bash harness/init.sh` desde `features.json`. Entra en el mismo commit. |

### En el otro repositorio (`C:\Users\pgris\PycharmProjects\arnes-base`)

Repositorio git aparte, **commit propio allí** (y sin `push`: lo decide el
humano, igual que aquí).

| Ruta | Qué cambia |
|---|---|
| `arnes-base/harness/mutacion.py` | Copia del de albaranes (hoy son idénticos: verificado con `diff`, sin una sola diferencia). |
| `arnes-base/tests/test_mutacion_operadores.py` | Copia del test nuevo. |
| `arnes-base/CHECKPOINTS.md` | El punto nuevo de C4 bis, **idéntico**. C4 ter **no**: el párrafo de los evals es específico de albaranes y en `arnes-base` ni existe. |
| `arnes-base/.claude/agents/reviewer.md` | La misma frase. |
| `arnes-base/harness/VERSION` | Versión y fecha nuevas. |
| `arnes-base/GUIA_INSTALACION.md` | Sección nueva `## … (X.Y.Z, 2026-08-19)` al final de la lista de versiones, con el aviso de R20. |

> `CHECKPOINTS.md` ha **derivado** entre los dos repositorios (C3 tiene un
> `[ADAPTAR]` resuelto aquí, y C4 ter está redactado distinto). C4 bis, en
> cambio, es **idéntico** hoy: el punto nuevo se añade tal cual en los dos. No
> se aprovecha esta feature para reconciliar el resto de la deriva.

## 3. Ficheros que NO se tocan (los colindantes que tientan)

- `harness/mutacion_paralela.py` — reparte mutantes y worktrees; no conoce
  `COMPARACIONES`. Grep confirmado: la tabla solo se usa en
  `harness/mutacion.py:53` y `:124`.
- `harness/alcance.py`, `harness/cobertura.py`, `harness/rigor.py`,
  `harness/servicios.py`, `harness/init.sh` — el alcance y las puertas no
  cambian.
- `evals/` entero (`conversor.py` declara `RUTA_GROUND_TRUTH` y es **correcto**:
  los libros existen), `evals/README.md`, `tests/conftest.py`.
- `services/**` — ni una línea, ni siquiera para matar un superviviente
  (R11 manda **test**, no producción).
- `progress/mutacion_F-019.md` y `progress/mutacion_F-027.md` — **peligro
  real**: `escribir_informe` reescribe el fichero entero y solo conserva los
  análisis de supervivientes. Los dos informes llevan secciones escritas a mano
  que se perderían: el «Complemento MANUAL» de F-027 (los 7 mutantes con su
  texto exacto, que es la evidencia que sostiene su APPROVED) y la «Nota sobre
  esta campaña (round trip 3)» de F-019. Por eso las re-mediciones van a
  ficheros nuevos. Lo único que puede añadírseles es un **puntero de una
  línea**, y solo si el humano elige la opción B de D1.
- El resto de `progress/*.md` y `specs/F-0XX-*/` anteriores: registro histórico.

## 4. El cambio en `harness/mutacion.py`, con el código en la mano

Leído tal como está tras el arnés 1.5.2 (commit `3a146cd`).

### 4.1 La tabla (línea 53)

Hoy:

```python
COMPARACIONES: dict[type, tuple[str, str]] = {
    ast.Eq: ("==", "!="),
    ast.NotEq: ("!=", "=="),
    ast.Lt: ("<", "<="),
    ast.LtE: ("<=", "<"),
    ast.Gt: (">", ">="),
    ast.GtE: (">=", ">"),
}
```

Se añaden **dos entradas** (y nada más):

```python
    ast.Is: ("is", "is not"),
    ast.IsNot: ("is not", "is"),
```

`_candidatos` (línea 118) ya recorre `nodo.ops` de cada `ast.Compare` con
`COMPARACIONES.get(type(operador))` y emite un `_Candidato` por operador, con el
hueco `(_final(izquierda), _inicio(derecha))`. **No hay que tocar `_candidatos`**:
las comparaciones encadenadas y las unidas por `and`/`or` (R3) ya salen bien —
comprobado por cálculo puro: `if a is None or b is None:` da **2** mutantes en
columnas distintas, y `a is b is not c` otros 2.

`aplicar_mutante`, `Mutante.longitud`/`sustituto` y `clave_de_mutante` funcionan
sin cambios: la sustitución es un reemplazo de bytes en una línea, y `is not`
(6 bytes) → `is` (2) es un caso más.

### 4.2 El delimitador de palabra en `_localizar` (línea 217)

Hoy `_localizar` hace `bruta.find(objetivo, desde, hasta)` y **devuelve la
primera coincidencia**, sea o no un token. Con `is` (dos letras) eso es un
problema real: el hueco entre los dos operandos puede contener un **comentario**
cuando la condición está entre paréntesis, y una palabra como «análisis»
contiene `is`. Medido hoy:

```
if (
    valor  # el analisis previo
    is None
):
```

produce el mutante `'valor  # el analis notis previo'`: una mutación dentro de
un comentario, equivalente por construcción, superviviente eterno y ruido en el
informe.

Cambio, mínimo y contenido:

```python
#: Bytes que cuentan como «parte de una palabra» para delimitar un token
#: alfabético. Los >= 0x80 entran porque una letra acentuada de un comentario
#: ocupa dos bytes en UTF-8 y sigue siendo parte de la palabra.
_PARTE_DE_PALABRA = re.compile(rb"[A-Za-z0-9_\x80-\xff]")


def _es_palabra(objetivo: bytes) -> bool:
    """¿El token a buscar se escribe con letras (`is`, `is not`, `and`, `not`)?

    Los símbolos (`==`, `+`, `<=`) NO se delimitan: `x==y` es legal y el
    carácter anterior a `==` es una letra.
    """


def _delimitado(bruta: bytes, ini: int, fin: int) -> bool:
    """¿La coincidencia `[ini, fin)` es un token entero y no parte de una palabra?"""
```

y el bucle de búsqueda pasa de «primera coincidencia» a «primera coincidencia
**válida**»: si la encontrada no está delimitada, se sigue buscando desde
`posicion + 1` dentro del mismo hueco. En el ejemplo de arriba, el `is` del
comentario se descarta y el mutante cae en el `is` de la línea 3, que es el
correcto.

**Por qué el delimitador solo se aplica a tokens alfabéticos (R6)**: aplicarlo a
todos rompería `x==y` (letra antes de `==`, letra después). El requisito R6
existe precisamente para fijar esa no-regresión con un test.

**Alcance del cambio**: `_localizar` la usan también `not`, `and`, `or`, `True`
y `False`. Para todos ellos el delimitador es estrictamente correcto (hoy
tienen el mismo agujero, solo que menos probable) y no cambia ningún resultado
existente — la suite de la raíz lo confirma en T3.

### 4.3 La limitación declarada (R7)

`is  not` (dos espacios) y el operador partido entre dos líneas **no generan
mutante**: `_localizar` busca la cadena literal `"is not"` y busca línea a
línea. Medido: `if x is  not None:` → 0 mutantes, sin excepción. Se declara en
un comentario junto a las dos entradas nuevas de `COMPARACIONES` y se fija con
test, para que nadie lo tome por un fallo silencioso. En un repositorio
formateado (ruff/black) el espaciado canónico está garantizado; sostener una
expresión regular por un caso que el formateador no deja pasar sería pagar
complejidad por nada.

## 5. Los tests (`tests/test_mutacion_operadores.py`)

Puros: llaman a `generar_mutantes` sobre **fuentes en cadena**, sin tocar disco,
red ni BBDD. Uno por requisito de G1, más el de R14.

| Test | Qué fija |
|---|---|
| `test_f034_r1_muta_is_a_is_not` | `if x is None:` → 1 mutante `is not None` |
| `test_f034_r2_muta_is_not_a_is` | La guarda real de F-027 (`if partida_result.derived_line is not None:`) → `is None` |
| `test_f034_r3_una_mutacion_por_operador_en_la_misma_linea` | `if a is None or b is None:` → 2 mutantes, columnas distintas; `if a is b is not c:` → 2 |
| `test_f034_r4_el_operador_declarado_es_comparacion` | `mutante.operador == "comparacion"` y `clave_de_mutante` distingue los dos de la misma línea |
| `test_f034_r5_no_muta_dentro_de_una_palabra_del_comentario` | El caso del comentario con «analisis»: 1 mutante y cae en la línea del `is`, no en el comentario |
| `test_f034_r6_los_simbolos_sin_espacios_siguen_mutando` | `if x==y:` sigue dando su mutante; `z=a+b` el suyo |
| `test_f034_r7_espaciado_no_canonico_no_genera_mutante_ni_falla` | `if x is  not None:` → 0 mutantes, sin excepción |
| `test_f034_r8_el_mutante_compila_y_el_ast_lleva_el_operador_contrario` | `aplicar_mutante` → `compile()` OK y el `ast.Compare` lleva `ast.IsNot` donde había `ast.Is` |
| `test_f034_r14_la_puerta_de_evals_no_se_declara_sobre_lo_no_versionado` | Lee `harness/rutas_sensibles.json` y exige que `_exigencia` mencione `evals/fixtures/` y no condicione la subida a `evals/ground_truth/` |

**Nombre del fichero**: `test_mutacion_operadores.py`, sin prefijo `f034`, igual
que `tests/test_mutacion_informe.py` (la 1.5.1) y `tests/test_backlog_md.py`.
Motivo: el fichero viaja **byte a byte** a `arnes-base`, donde «F-034» no
significa nada; la trazabilidad que exige `docs/CONVENTIONS.md` la dan los
**nombres de las funciones** (`test_f034_rN_…`), que es donde el reviewer la
busca. Es la misma decisión que ya se tomó con los dos ficheros anteriores.

## 6. Cómo se demuestra que sirve (G2), de forma reproducible

Las campañas se lanzan **sobre el árbol principal** —no hace falta worktree— y
con las referencias fijadas, porque `merge-base(dev, rama)` es hoy el propio tip
de cada rama ya integrada y sin `--base` el alcance saldría vacío:

```bash
# F-027 — 1 mutante esperado, MUERTO
python -m harness.mutacion --feature F-027 \
  --base e95549d8880ebdabee45c1ec4fbe20651240428f \
  --rama feature/F-027-conversion-kg-tn-muerta \
  --workers 1 --salida progress/mutacion_F-027_remedida.md

# F-019 — 49 mutantes esperados (31 + 18), 0 supervivientes nuevos
python -m harness.mutacion --feature F-019 \
  --base cd904cdcecee56311280ee54d81a7158d0529eb5 \
  --rama feature/F-019-importe-unitario-manda \
  --workers 1 --salida progress/mutacion_F-019_remedida.md
```

Condiciones que hacen esto válido, **verificadas**:

1. Los ficheros del alcance de F-019 y F-027 son **idénticos** entre `dev` y el
   tip de su rama (`git diff --stat dev <rama> -- <ficheros>` vacío), así que
   los números de línea del diff apuntan al código que hay en el árbol.
2. `harness/servicios.json` no declara `venv` en ningún servicio, así que
   `interprete()` devuelve `sys.executable`: la campaña corre con el intérprete
   actual, sin entornos que preparar.
3. `--workers 1` obligatorio: la campaña paralela se niega a correr con
   ficheros sin versionar, y en Windows lanzar suites en paralelo tumba el
   portero (`0xC0000142`, incidente del 2026-08-18/19 anotado en
   `progress/current.md`).

**Truco para no perder los análisis ya escritos** en la campaña de F-019: antes
de lanzarla, copiar el informe histórico al nombre de salida
(`cp progress/mutacion_F-019.md progress/mutacion_F-019_remedida.md`). El
mecanismo de la 1.5.1 (`analisis_escritos` + `AVISO_REPUESTO`) repone bajo cada
superviviente su análisis anterior, y de paso queda ejercitado sobre un caso
real. El original **no se toca**.

**Prueba de control (obligatoria, la misma que exige `reviewer.md`)**: antes de
tocar nada, lanzar el cálculo puro de mutantes sobre esos dos alcances con el
mutador **actual** y pegar en `progress/impl_F-034.md` los totales (31 y 0). Es
lo que convierte «ahora salen más» en una medición con un antes y un después.

## 7. SQL

Ninguno. Esta feature no toca schema, ni DDL embebido, ni BBDD.

## 8. Riesgos y decisiones

| # | Riesgo / decisión | Resolución |
|---|---|---|
| 1 | **Sobrescribir el informe histórico** al remedir borra evidencia escrita a mano (el complemento manual de F-027 sostiene su APPROVED). | Salida a ficheros `*_remedida.md` nuevos; los originales solo pueden recibir un puntero de una línea. |
| 2 | **El delimitador de palabra rompe los símbolos** (`x==y` dejaría de mutar). | Se aplica solo a tokens alfabéticos; R6 lo fija con test. |
| 3 | **La campaña de F-034 muta `harness/mutacion.py`**, es decir, la propia herramienta. | Precedente: F-012 ya lo hizo (61 mutantes sobre `harness/`). El coordinador tiene el módulo en memoria y los mutantes se juzgan en un pytest aparte. Se lanza con `--workers 1` y con el árbol limpio. |
| 4 | **Explosión de supervivientes en features futuras**: a partir de ahora habrá mutantes `is` que nadie mata. | Es el efecto buscado, no un daño colateral: cada superviviente nuevo es un hueco real. R11 obliga a cerrarlo con test o justificarlo. |
| 5 | **Mutación equivalente típica de `is`**: `x is None` → `x is not None` en una guarda cuyo `else` hace lo mismo. | Se trata como cualquier equivalente: análisis escrito en el informe. No se filtra nada en la herramienta. |
| 6 | **Deriva entre los dos repositorios**: `CHECKPOINTS.md` ya ha divergido. | Se porta solo el bloque C4 bis (hoy idéntico) y `mutacion.py` (hoy idéntico). La deriva de C3/C4 ter se deja como está y se anota. |
| 7 | **Finales de línea**: `albaranes` guarda estos ficheros con CRLF y `arnes-base` con LF (`diff` del test de la 1.5.1 sale entero por eso). | Al portar se copia el **contenido**, respetando el final de línea de cada repositorio, y `diff` se compara normalizando (`diff <(tr -d '\r' < a) <(tr -d '\r' < b)`). |
| 8 | **Otro agente trabajando en el mismo árbol**. | Las campañas de G2 mutan ficheros del árbol de trabajo: T5 y T6 exigen árbol limpio y ninguna otra suite corriendo. |

### Alternativas descartadas

- **Expresión regular `is\s+not` para tolerar el espaciado raro.** Obligaría a
  que `_localizar` devolviera también la longitud del token y a tocar el
  contrato de `_Candidato`, para cubrir un caso que el formateador del
  repositorio no produce. Descartado: R7 lo declara como límite con test.
- **Mutar `is not` sustituyendo solo el `not`** (que sí toleraría el espaciado
  raro, reutilizando el mecanismo del `not` unario). Descartado: deja
  `x is  None` con doble espacio en el informe y hace ilegible la columna
  «Mutado», que es lo que el reviewer lee.
- **Añadir también `ast.In` / `ast.NotIn`.** Fuera del alcance declarado en la
  ficha de la feature; se propone aparte si el humano lo quiere.
- **Filtrar automáticamente los mutantes «probablemente equivalentes»**.
  Descartado: la herramienta no debe decidir por el implementer qué línea
  merece análisis; ahí es donde se pierden los defectos.
