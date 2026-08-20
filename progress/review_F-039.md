<!-- progress/review_F-039.md -->
# F-039 · Review

**Revisión completa (pasada 1).** Rango recalculado con `git merge-base dev
HEAD` = `d3422ee`: se revisa **`d3422ee..29d7fd6`** (14 commits, 19 ficheros,
+1.864/−35); `dev` está en `d3422ee`, así que coincide con `dev..HEAD`. Árbol
limpio al empezar y al terminar.

## Veredicto: CHANGES_REQUESTED

Dos CR pequeños y acotados. **El fondo está bien y verificado de forma
independiente**: los números de las dos campañas son reales —reproducidos
mutante a mutante—, `init.sh` en verde, y las decisiones de juicio (R20, R21, el
equivalente, dejar fuera `_base_rota_al_final`) son las correctas. Falta una
guarda de test y una guarda de entrada. **Nivel de rigor:** `estandar`, exige
fase RED, cobertura ≥ 80 %, campaña analizada y «Evidencias»; RM5 no aplica.

## Verificación independiente

- `bash harness/init.sh` tal cual, **exit 0**: **416 passed in 75.31s**,
  `COBERTURA 96.9%` (31/32), `TAMAÑO requirements 150/150, design 224/250, impl
  210/220`. Los avisos (`ruff` 1108, sv1/infra sin tests, `[ADAPTAR]` de
  F-034/F-035) son deuda previa. **150/150 comprobado**: `wc -l` = 150 exactas;
  clavado en el tope, que es legal.
- **Recálculo puro de T11**: `alcance_de_ficheros` da 1932+541+269 = **2742**
  líneas y `generar_mutantes` **417** mutantes; coinciden al dígito. **Los 20
  muestreados reproducidos** con `Random(20260820).sample`: salen los mismos, y
  **los 7 supervivientes están entre ellos**, con idéntico operador y texto
  original→mutado. `mutacion_F-039.md`: 61+73 = **134** líneas, **13** mutantes.
- **Campañas NO reejecutadas** (838,7 s y 473,1 s, muy por encima del umbral de
  60 s de C4 bis). En su lugar, **tercera vía (RM4)**: copia del árbol en el
  scratchpad y reejecución de los 33 mutantes contra el subconjunto de tests de
  la maquinaria (219 tests): **13/13 muertos** en la campaña de la feature y
  **20/20 veredictos idénticos** a los declarados en la de la maquinaria. Los
  muertos están comprobados, no solo contados. Árbol principal intacto.
- **R5 provocado sobre copia**: inyectada una fila de reloj nueva en
  `escribir_informe` sin declararla, el test de R4 **falla** (`At index 22 diff:
  '| Segundos netos de reloj | 2.70' != '… 888.84'`): la guarda contra el flake
  de F-038 T5 funciona. **R16 en vivo**: ruta inexistente y no-producción
  abortan con exit 2 y mensaje explícito, sin tocar nada.
- **`arnes-base` intacto**: commit `c6d4979` del 20-ago 17:00, limpio, sin rastro
  de lo nuevo (T17 bien aplazado). **`mutacion_F-034.md` fuera del diff** (R25) y
  **`features.json` solo pasa a `in_progress`**: ninguna ficha nueva (R20).

## RM1–RM6

- **RM1 [x]** · SHA completo `b0761e85…`. Desde ese commit hasta HEAD **ningún
  fichero del alcance cambia** (`git diff --name-only b0761e8..HEAD` sobre los
  tres, vacío): solo entran informes, `tasks.md` y un fichero de tests **nuevo**,
  que como mucho mataría supervivientes, nunca al revés.
- **RM2 [x]** · 20 × 41,9 = 838 ≈ **838,7 s**, sin salto de orden de magnitud;
  media (41,9) < base (57,1) es el caso legítimo de `-x` con 13/20 muertos, como
  F-038. Idem `mutacion_F-039.md`: 13 × 36,4 ≈ 473,1. **El relato de las tres
  pasadas se sostiene**: otra sesión cargando la máquina explica 51 s → 149 s, la
  suite seguía en `409 passed` y `--timeout 400` sin tocar `rigor.json` es el
  remedio correcto (D5 en pie).
- **RM3 [x]** · Ningún equivalente sale MUERTO: revisados los 13 uno a uno, todos
  cambian comportamiento observable (`__name__ != "__main__"` ejecuta el cuerpo
  al importar; `[None] // efectivo` y `split(…)[2]` revientan; el resto invierten
  guardas vivas). Confirmado en la copia. **RM4 [x]**: usada, arriba.
- **RM5 · N/A justificado** (solo `critico`). Aun así he leído la justificación
  de `mutacion.py:1348` y **se sostiene**: con `or` la rama se toma también en
  líneas sin backticks, que dejan `mutado` en `None` sin cambiar el estado; el
  único camino divergente es un bloque sin `- Mutado:` válido, y ahí el original
  recoge el análisis y lo tira después en `if analisis and original is not None and
  mutado is not None`. Mismo observable. **RM6 · N/A justificado**: no se quita ni
  una guarda defensiva; el superviviente de `mutacion.py:1807` se deja **vivo**.

## CHECKPOINTS.md

- **C1 [x]** · `init.sh` exit 0; ficheros obligatorios presentes. **C2 [x]** ·
  una sola feature `in_progress`, rama correcta, `current.md` al día.
- **C3 [x]** · Hexagonal **N/A justificado**: la feature vive entera en
  `harness/`, utillaje sin capas (design §«Encaje»). Primera línea con ruta en los
  cinco nuevos; sin `print()` de debug; sin secretos. **C3 bis · N/A**: no entra
  ningún documento externo.
- **C4 [ ]** · Falla por **R18**: sin ningún test, y `tasks.md` T12 declara como
  verificación «test de documentos de T15», que no existe (CR-1). El resto sí:
  MANUAL de T5/T6/T7 en `current.md` §1 con comando exacto; nada toca red ni BBDD.
- **C4 bis [x]** · Fase RED con **dos trazas reales** (los dos `ImportError`, más
  el rojo intencionado de R7); cobertura en `[OK]`; `mutacion_F-039.md` generado
  por la herramienta y con totales verificados; cero `PENDIENTE` en los dos
  informes; «Evidencias» con los cuatro números; no es campaña de cero mutantes.
  **C4 ter · N/A justificado**: «F-039 no toca ninguna ruta sensible».
- **C5 [x] con salvedad escrita** · Commits `F-039 Tn: …` por tarea; árbol
  limpio; `features.json` refleja el estado real. `tasks.md` deja `[ ]` T5, T6,
  T7 —MANUAL del humano— y T17 —porte a `arnes-base` **tras** el merge, F-038
  D6—; ambas excepciones constan por escrito: no son tareas sin hacer, son
  tareas asignadas a otro momento y a otra persona.

## Trazabilidad requisito → test

| Req | Test |
|---|---|
| R1, R2 | `test_f039_r1_*` (3) y `test_f039_r2_todo_informe…figura_en_el_inventario` |
| R3–R7 | `test_f039_r3_*` (2), `r4_dos_informes…`, `r5_*` (2), `r6_las_diferencias…`, `r7_el_test_de_paridad_de_f012…` |
| R8–R12 | MANUAL (humano) · `verificacion_paralela_F-039.md`, comando y criterio listos |
| R13, R14, R17 | Verificados por recálculo del reviewer sobre el informe |
| R15, R16 | 6 tests `test_f039_r15_*` y 4 `test_f039_r16_*` (+ comprobado en vivo) |
| **R18** | **ninguno — CR-1** |
| R19–R26 | `grep -c PENDIENTE` = 0; `current.md` §2 y §3; `features.json` sin ficha nueva; línea base 57,1 s verde; `test_f039_r23_*`, `r24_*`, `r25_*`; `init.sh` exit 0 |

## Cambios requeridos

**CR-1 · R18 no tiene guarda, y el propio informe dice por qué hace falta.**
`progress/mutacion_maquinaria_paralela_F-039.md` avisa: «`escribir_informe`
conserva los análisis de los supervivientes, pero **no esta cabecera**. Vuélvela
a pegar.» Quien repita la campaña borra en silencio el comando de reproducción y
la advertencia de que mide otro código que `mutacion_F-012.md`, y nada lo
detecta. R23 —mismo tipo de requisito— sí tiene test; R18 se quedó fuera. Añadir
a `tests/test_f039_r1_r2_r23_r25_documentos.py` un `test_f039_r18_*` que exija (a)
el `--ficheros` completo del comando de reproducción y (b) la frase de que mide
**otro código** y no repone los de F-012. Y corregir la verificación de **T12** en
`tasks.md`, que declara un test inexistente.

**CR-2 · La guarda de lista vacía de `alcance_de_ficheros` es inalcanzable desde
el CLI** (`harness/alcance.py:235`). `design.md` promete «Aborta con
`SystemExit` … si la lista viene vacía» y `test_f039_r16_una_lista_vacia_aborta`
solo cubre la llamada directa con `[]`. Desde `main` la lista nunca es `[]`:
`split(",")` devuelve siempre ≥ 1 elemento y las entradas en blanco se saltan
con `continue` (líneas 245-246). Comprobado: `--ficheros ","` termina en **exit
0** y escribe un informe de **0 mutantes**, que es justo la campaña vacía que
`CHECKPOINTS.md` manda mirar con lupa. Mover la comprobación **después** del
filtrado —si `lineas` queda vacío, abortar— y cubrirla con un test vía `main`.

## Observaciones (no bloquean)

1. **T16 se commiteó antes que T11**, invirtiendo el orden D → E del design: sin
   consecuencia, pero ese orden es parte de la spec y si se cambia, se dice. Y
   `requirements.md` en 150/150 por segunda feature seguida sugiere que el tope
   se queda corto para features de arnés: propuesta para el humano.
2. **`_base_rota_al_final`: de acuerdo en dejarlo fuera.** No lo cubre ningún
   requisito, es genérico del arnés, y —argumento que el implementer no hace—
   **arreglarlo tras medir movería el alcance bajo el SHA ya declarado y
   obligaría a repetir 838 s de campaña por RM1**.
3. **R21 no debía dispararse, y el grupo A no cambia eso.** El mutante de
   `mutacion.py:1807` invierte una guarda que **en el código real funciona**: la
   campaña sí restaura el centinela sucio antes de empezar. Falta el test que la
   sujeta, no la defensa: hueco, y de los graves, pero hueco. Bien clasificado
   como Alta y bien enviado al humano.
