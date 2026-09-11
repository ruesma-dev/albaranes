<!-- progress/impl_F-043_T28_supervivientes.md -->
# F-043 · T28 · Los 163 supervivientes, uno por uno

Cierre de la verificación MANUAL **T28** de F-043: campaña de mutación
completa, sin tope, y **cero supervivientes sin justificar**.

La campaña en sí **no se ha vuelto a lanzar** (cuesta dos horas y muta el
árbol principal). Se ha trabajado sobre la que corrió el 2026-09-10,
`progress/mutacion_F-043.md`, **reinyectando a mano** cada superviviente
contra la suite de su servicio para saber cuál es su estado HOY.

| | |
|---|---|
| Informe de la campaña | `progress/mutacion_F-043.md` (ya versionado, commit `b114377`) |
| HEAD medido por la campaña | `48e3d17` |
| Alcance | 38 ficheros, 3123 líneas (`--feature F-043` arrastra F-036 entera: esta rama sale de la de F-036, no de `dev`) |
| Mutantes | 347 generados, 347 evaluados, sin muestreo |
| Veredicto de la campaña | 181 muertos · 163 supervivientes · 3 timeouts |
| **Veredicto real tras T28** | **184 muertos · 163 supervivientes · 0 timeouts** |
| **Supervivientes sin justificar** | **0** |

---

## 1. Las cuatro suites, verificadas

Nadie había comprobado que los tests de los cuatro commits de T28 pasaran
de verdad. Lanzadas **por separado** (sv2 y sv3 comparten el paquete
`infrastructure/sigrid` y en un solo proceso de pytest la pasada muere al
RECOGER), y **nada en paralelo**:

| Servicio | Comando | Resultado | Tiempo |
|---|---|---|---|
| `comun` | `cd services/albaranes-comun && python -m pytest -q` | **143 passed, 3 skipped** | 124,56 s |
| sv3 | `cd services/albaranes-persistencia && python -m pytest -q` | **170 passed** | 3,84 s |
| sv4 | `cd services/albaranes-front && .venv/Scripts/python -m pytest -q` | **183 passed** | 4,93 s |
| sv6 | `cd services/albaran-valoracion-persist && python -m pytest -q` | **224 passed** | 3,73 s |
| sv5 | `cd services/albaran-valoracion-api && python -m pytest -q` | **43 passed** | 3,21 s |

sv4 y sv6 llevan ya los dos ficheros de guarda que añade este trabajo
(159 → 183 y 217 → 224). Antes de ellos pasaban igual.

---

## 2. Los 3 timeouts: eran ruido de la máquina, y son MUERTOS

Un timeout no es un muerto: la campaña no llegó a juzgarlos. Verdicto:
**los tres son muertos**, y el timeout fue contención, no lentitud del
mutante.

Ninguna de las tres líneas contiene bucle ni espera —un `if`, una
expresión `or` y un predicado `lambda`—, así que **ninguna mutación puede
colgar nada**. Reinyectados uno a uno, cada uno contra la suite de su
servicio, revertidos después:

| # | Mutante | Suite | Veredicto | Tiempo |
|---|---|---|---|---|
| 6/347 | `sqlalchemy_valuation_context_repository.py:335` `if not familia:` → `if familia:` | sv5 | **MUERTO**, 7 tests fallan | 2,66 s |
| 7/347 | `…:345` `…get("tipologia_origen")) or "ia1"` → `and "ia1"` | sv5 | **MUERTO**, 2 tests fallan | 3,44 s |
| 9/347 | `modifier_contract_matcher.py:284` `normalizar_ler(d) == ler` → `!= ler` | sv6 | **MUERTO**, 3 tests fallan | 2,93 s |

**La causa.** Son los mutantes **6, 7 y 9 de 347**: la primerísima oleada,
con los 4 workers creando worktrees y midiendo líneas base a la vez sobre
una máquina compartida. El timeout que se les aplicó fue de 275 s,
derivado de la peor línea base del worker (`comun`, 137 s). Las líneas
base de sv5 y sv6 se midieron entonces en 10,5 s y 9,2 s; hoy esas mismas
suites tardan 3,2 s y 3,4 s. Ese factor 3 es la huella de la contención.

**El tercero no dependía de los tests nuevos.** Repuesto
`test_f036_r15_r20_matcher_ler.py` a su versión del HEAD de la campaña
(`48e3d17`) e inyectado el mutante, caen 2 tests en 3,05 s: **habría
muerto ya entonces**.

---

## 3. Los 163 supervivientes, por grupo

Cada grupo se ha **reinyectado mutante a mutante** contra la suite de su
servicio y revertido. El análisis corto de cada uno está además escrito
dentro de `progress/mutacion_F-043.md`, en el formato que
`harness.mutacion` arrastra a la siguiente campaña de la feature.

| Grupo | Fichero | N | Veredicto | Quién lo cierra |
|---|---|---|---|---|
| **A** | `ruesma_comun/ler.py` | **84** | Hueco real, **CERRADO con test** | `9568ac2` |
| **B** | sv6 (4 ficheros) | **8** | Hueco real, **CERRADO con test** | `8f36c77` |
| **C** | sv6 `valuation_builder.py:1532` | **1** | **Equivalente** + guarda | este trabajo |
| **D** | sv4 `review_repository.py` (×4) | **4** | Hueco real, **CERRADO con test** | `cd35efb` |
| **E** | sv4 `review_repository.py` (×2) | **2** | **Equivalente** + guarda | este trabajo |
| **F** | sv4 `review_models.py` | **3** | **Equivalente** + guarda | este trabajo |
| **G** | sv3 `contexto_linea_merger.py:92` | **1** | **Equivalente** + guarda | `805cccb` |
| **H** | `scripts/diagnose_sigrid_contrato_docs*.py` | **60** | **Justificado EN BLOQUE** | autorización del humano |
| | **Total** | **163** | **0 sin justificar** | |

**Reparto:** 96 huecos reales cerrados con tests nuevos · 7 equivalentes
justificados y con guarda · 60 justificados en bloque.

### Grupo A · el catálogo LER (84)

Los 84 son mutaciones de enteros sobre el literal `_CAPITULOS_LER` de
`ruesma_comun/ler.py:51-70` (cambiar un subcapítulo, correr un `range`).
El catálogo se daba por bueno entero: **ningún test lo recorría**, así que
un dígito cambiado no rompía nada y un número de 6 cifras que no es un LER
podía pasar por válido — que es exactamente el bug real que motivó la
validación (el producto `192137` de un albarán de mortero disparando la
regla «LER → residuos»).

`services/albaranes-comun/tests/test_f036_r14_catalogo_ler_exhaustivo.py`
(commit `9568ac2`, **25 tests**) recorre los 20 capítulos y sus
subcapítulos uno a uno.

**Medido:** los 84 reinyectados contra ese solo fichero de test (0,06 s
por pasada) → **84 muertos, 0 vivos**. Si lo mata el fichero, lo mata la
suite entera.

### Grupo B · los ocho huecos de sv6 (8)

`modifier_contract_matcher.py:284`, `residuos_container_calc.py:176` (×2),
`residuos_incrementos.py:126/176/193/201` y `valuation_builder.py:1708`.
Ramas que existían pero que ningún test distinguía de su contraria.
Cerrados por `8f36c77`.

**Medido:** los 9 supervivientes de sv6 reinyectados contra la suite de
sv6 → **8 muertos**, y el noveno es el grupo C.

### Grupo C · la herencia de cantidad de una sintética (1) — EQUIVALENTE

`valuation_builder.py:1532`:

```
elif parent_record is not None and parent_record.cantidad_albaran is not None:
                                                                 ↓ mutado a
elif parent_record is not None and parent_record.cantidad_albaran is None:
```

Es la rama que decide de dónde hereda la cantidad una línea sintética que
**no** cuelga de una base de residuos. Los dos candidatos salen del MISMO
sitio: `_build_synthetic_line` busca
`parent_albaran = albaran_by_id.get(parent_merge_line_id)`, y el
`parent_record` que recibe es el que la pasada 2 guardó en
`records_by_merge_id[parent_merge_line_id]`, construido por `_build_line`
con `cantidad_albaran = albaran_line.cantidad if albaran_line else None`
sobre **ese mismo `albaran_by_id` y esa misma clave**. Caso por caso:

- hay línea con cantidad → `cantidad_albaran == parent_albaran.cantidad`;
  el original toma la primera, el mutante cae a la segunda, valen lo mismo;
- hay línea con `cantidad = None` → los dos dejan `None`;
- no hay línea → `cantidad_albaran` es `None` y `parent_albaran` es `None`;
  el original llega al `else`, el mutante entra en el `elif`, los dos
  dejan `None`.

**Guarda nueva:**
`services/albaran-valoracion-persist/tests/test_f043_t28_herencia_sintetica.py`
(7 tests). **No lo mata** —nada puede— y no se escribió para eso: fija el
invariante del que depende la justificación, que `cantidad_albaran` se
**copia** de la línea de albarán de su propio `merge_line_id`. Si mañana
se alimenta de otra fuente, los dos candidatos dejan de coincidir y el
mutante pasa a ser un hueco real.

**Verificado en rojo por dos sitios:** alimentando `cantidad_albaran`
desde `cantidad_override` caen 4 tests; poniéndole un fallback `0.0` en
vez de `None` cae 1.

### Grupo D · lo defensivo de sv4 (4)

`review_repository.py:3375/3393/3450/3478`. Los caminos defensivos de sv4
se tragan la excepción a propósito —sellar trazabilidad no puede tumbar el
guardado del revisor—, y lo único que queda del fallo es el
`logger.warning`. La suite comprobaba que el guardado sobrevive; nadie
comprobaba que quedara **algo con que diagnosticar**. Cerrados por
`cd35efb`.

**Medido:** los 9 supervivientes de sv4 reinyectados contra la suite de
sv4 → **4 muertos**, 5 vivos (grupos E y F).

### Grupo E · `ensure_ascii` (2) — EQUIVALENTE

`review_repository.py:3384` y `:3440`, `json.dumps(..., ensure_ascii=False)`
→ `True`. `ensure_ascii` solo decide si un carácter no ASCII se escribe
tal cual o escapado como `\uXXXX`. Las dos serializaciones son JSON válido
y **parsean al mismo valor**, y todo consumidor de `review_reasons_json`
entra por `json.loads`/`motivos_de_json` (verificado con grep): la columna
se **lee parseada**, nunca se compara como texto. Ya lo declaraba `cd35efb`;
aquí se le pone la guarda que le faltaba.

### Grupo F · el doble cinturón de `review_models.py` (3) — EQUIVALENTE

`numeros_iguales:31` (`or` → `and`) y `conversion_reproducible:78` (dos
mutaciones sobre la cadena de tres `or`). **Este grupo no lo había tocado
nadie**: `cd35efb` sólo se ocupó de los 6 de `review_repository.py`.

Las tres mutaciones abren la guarda de `None` y dejan pasar un `None` al
cuerpo. Da igual: **el cuerpo lo vuelve a atrapar**. `float(None)` lanza
`TypeError` y el `except (TypeError, ValueError)` devuelve `False`, que es
lo mismo que devolvía la guarda; y un `cantidad_convertida` a `None` cae
en la guarda de `None` de `numeros_iguales`, que ya devuelve `False`.

**Probado exhaustivamente**, no argumentado: enumerado todo el espacio que
esas funciones distinguen (`None`, números, numérico-como-texto y basura
no convertible) — **81 pares y 2 × 729 ternas, CERO discrepancias** entre
original y mutante.

**Guarda nueva:**
`services/albaranes-front/tests/test_f043_t28_equivalentes.py` (24 tests,
cubre también E). Fija el segundo cinturón. **Verificado en rojo**
estrechando el `except` a `ValueError`: caen 6 tests.

### Grupo G · la rama inalcanzable de sv3 (1) — EQUIVALENTE

`contexto_linea_merger.py:92`, `return True` → `return False`. Esa rama de
`_tiene_valor` atiende a un valor que no es `None`, ni `bool`, ni `str`,
ni `int`/`float`, y hoy ninguno puede llegar: se invoca sólo con
`getattr(ctx, campo, None)` sobre las nueve medidas de `_CAMPOS_RESIDUOS`
de un `ContextoLinea` ya validado, y pydantic rechaza los 45 intentos de
meter ahí una lista, un dict, una tupla, un set o un objeto suelto
(medido, 45/45). Guardado por `805cccb`.

**Medido:** reinyectado contra la suite de sv3 → **sigue vivo**, como debe
un equivalente.

### Grupo H · los 60 de los scripts de diagnóstico — EN BLOQUE

29 de `scripts/diagnose_sigrid_contrato_docs.py` y 31 de
`..._v2.py`. **Justificación autorizada expresamente por el humano el
2026-09-10**: diagnósticos manuales de un solo uso, ajenos a F-043 y a
F-036, fuera del pipeline y sin tests. Entran en el alcance sólo porque
los commits `ec5b5b0` y `48e3d17` de esta rama los corrigieron.

**Verificado antes de darla por buena** (era condición del encargo; si algo
hubiera salido falso, había que parar):

1. **Son ejecutables sueltos** — y más de lo esperado: no tienen `main()`
   **ni guarda `if __name__ == "__main__"`**. Son sentencias de nivel
   superior que leen `sys.argv` y empiezan a consultar Sigrid e imprimir
   nada más importarse. Importar uno **ejecutaría el diagnóstico**.
2. **Ningún servicio los importa.** `grep` en los seis servicios + `tests`,
   `infra`, `evals` y `harness`: **0 aciertos** en sv1, sv2, sv4, sv5, sv6,
   `comun`, `tests`, `infra`, `evals` y `harness`. Los 63 de sv3 están
   **todos dentro de `scripts/` mismo** (9 ficheros de esa carpeta
   citándose entre sí en docstrings y líneas de uso): ninguno en `domain/`,
   `application/`, `infrastructure/`, `interface_adapters/` ni `tests/`.
3. **Ninguna ruta de producción depende de ellos**: no aparecen en el
   `Dockerfile` de sv3, ni en su `pyproject`/`setup.cfg`, ni en ningún
   entrypoint.
4. **No hay tests suyos y no los puede haber** sin ejecutar un diagnóstico
   contra Sigrid.

**Medido:** los 60 reinyectados uno a uno contra la suite de sv3 → **los 60
siguen vivos**, que es justo lo que predice la justificación: la suite ni
siquiera importa esos módulos, así que ningún test podía matarlos.

Nada de lo que sostiene la justificación resultó falso.

---

## 4. Lo que cambia en el repositorio

| Fichero | Qué |
|---|---|
| `progress/mutacion_F-043.md` | **Versionado** (estaba sin versionar y tenía `init.sh` en rojo por el guardián de F-039 R2). Los 163 análisis escritos, **ninguno `PENDIENTE`**. Añadido el veredicto de los 3 timeouts |
| `progress/inventario_mutacion_F-039.md` | Fila nueva con veredicto `VÁLIDA`; recuento 15 → 16 |
| `services/albaran-valoracion-persist/tests/test_f043_t28_herencia_sintetica.py` | **Nuevo.** 7 tests, guarda del grupo C |
| `services/albaranes-front/tests/test_f043_t28_equivalentes.py` | **Nuevo.** 24 tests, guarda de los grupos E y F |
| `progress/impl_F-043_T28_supervivientes.md` | Este informe |
| `progress/current.md` | T28 cerrada |

Commits: `78d1c6e` (las guardas), `b114377` (informe + inventario), y el de
este informe.

**Ningún test se ha relajado ni retirado**, ninguna regla determinista
infiere familia por LER, producto, texto o CIF, y el árbol queda **limpio**:
todas las mutaciones inyectadas a mano se revirtieron y se comprobó con
`git status` y `git diff` tras cada bloque.

---

## 5. Lo que T28 NO cubre

- **T30** (evals con LLM real), **T31** (SS-0003967 de extremo a extremo) y
  **T32** (la ficha del revisor en sv4) siguen pendientes: son las otras
  tres verificaciones MANUAL del humano.
- La mutación mide si los tests distinguen una rama de su contraria. **No
  dice si IA1 clasifica bien**: eso sólo lo ve T30, que sigue sin autorizar.
  Es el riesgo declarado y aceptado de la feature.
- Los 60 del grupo H **no tienen red de ningún tipo** y no la van a tener.
  Es una decisión escrita, no un descuido.

---

## Evidencias

| Evidencia | Valor |
|---|---|
| **Tests ejecutados** | `comun` 143 passed + 3 skipped · sv3 170 · sv4 183 · sv5 43 · sv6 224. **Todas en verde** |
| **Tests nuevos de este trabajo** | **31** (7 en sv6, 24 en sv4) |
| **Tiempo de las suites** | 124,56 s · 3,84 s · 4,93 s · 3,21 s · 3,73 s |
| **Mutantes generados / supervivientes** | 347 / 163 (campaña del 2026-09-10, no relanzada) |
| **Supervivientes analizados** | **163 de 163. Sin justificar: 0** |
| **Mutantes reinyectados a mano en T28** | **166** (163 supervivientes + los 3 timeouts), cada uno con su suite y revertido |
| **Cobertura de las líneas cambiadas** | la que mida `PUERTA COBERTURA` de `bash harness/init.sh` en la corrida de cierre |
| **Fase RED** | No aplica como tal: T28 no implementa comportamiento. Su equivalente es la reinyección de los 166 mutantes, con la salida real de cada suite, y las dos verificaciones en rojo de las guardas nuevas (4+1 tests en sv6, 6 en sv4) |
