<!-- progress/review_F-040.md -->
# F-040 · Review

**Revisión completa (pasada 1)**, rango `2ccb8acd8e85e9eff1cfc80bcf7cf9c52cfeb11b..0fa61cb9`
(`git merge-base dev HEAD`), 23 commits, 19 ficheros, +2.858/−48.

## Veredicto: APPROVED

**Nivel de rigor: `estandar`**, declarado en `harness/features.json`: exige
C1–C5, C3 bis y C4 bis con **fase RED**, **cobertura** ≥ 80 % de lo cambiado y
**campaña de mutación** con supervivientes analizados; no exige cero
supervivientes ni RM5. `bash harness/init.sh` **exit 0**, tal cual: **530 passed
en 88,46 s**, 6 suites de servicio en verde, `PUERTA COBERTURA 100,0 % (79/79)`,
`PUERTA TAMAÑO` dentro de topes (117/150, 176/250, 219/220), rutas sensibles
N/A. Los avisos son deuda previa idéntica a `dev`.

## LA PREGUNTA DE FONDO: ¿vale esta campaña para cerrar F-040?

**Sí, y con más respaldo del habitual. Pero el defecto es real y degrada la
puerta de mutación del arnés mientras no se arregle.**

**1. La evidencia se sostiene.** Reproduje **las dos** discrepancias sobre copia
en el scratchpad (RM4, tercera vía; copia borrada, árbol limpio). La copia
arrastra 2 fallos propios por no ser repo git (los tests de CLI que llaman a
`main`): están en el control, no en el delta.

| Mutante | Veredicto de la campaña | Lo que hace la suite (medido por mí) |
|---|---|---|
| `mutacion.py:1942` `max(1,`→`max(2,` | superviviente (paralela) | **5 tests en rojo** (`test_f012_r7_..._nunca_bajan_de_uno` + 4 de R8) |
| `mutacion.py:677` `*`→`//` | superviviente (serie) | **2 tests en rojo** (`test_f040_r2_la_linea_base_recibe_el_suelo_por_el_factor` y `..._siempre_recibe_mas_tiempo`) |

**2. La hipótesis del implementer es mecánicamente correcta**, verificada en
código: `ResultadoSuite.verde` (`harness/mutacion.py:490`) cuenta
`PYTEST_SIN_TESTS = 5` como verde y `EjecutorPytest.ejecutar` (:592-600) devuelve
`SUPERVIVIENTE` para el 0 y para el 5 sin distinguirlos; el informe no guarda el
código, así que hoy no se puede saber cuál fue.

**3. El sesgo del fallo es el SEGURO.** Por ese mecanismo un mutante solo puede
salir **falso superviviente** (trabajo de más), nunca falso muerto (agujero que
pasa), y las dos discrepancias van en esa dirección. Un falso *muerto* exigiría
otro mecanismo (test flaky bajo `-x`, el de F-038 T17), y la suite es hoy estable.

**4. Lo que compensa es haber medido dos veces.** 16 de los 20 mutantes salieron
muertos en **ambos** modos, independientemente; los 4 restantes están explicados
uno a uno y dos reproducidos por mí, así que el recuento honesto —19 cazados, 1
equivalente— se sostiene. Una campaña **única** no tendría este respaldo: mientras
el defecto viva, ninguna de una sola pasada vale como evidencia sin contraste.

**5. RM3 sigue en pie: ningún equivalente salió MUERTO.** Recorrí los 17 muertos
buscando equivalencias y no hay ninguna: los cinco de `:1942` cambian el resultado
con `cpu_count` 8 o 22, `ref_diff[2]` es un `IndexError` y los tres de
`rigor.py:133` cambian la aceptación de `0`/`True`. El único equivalente
(`or 1`→`or 2`) sobrevivió en **las dos** campañas.

**6. Excluirlo estuvo bien** y nada de lo que entra queda cojo: D1–D5 se verifican
por test, sin depender del veredicto de ningún mutante, y el `design.md` §5 lo
pedía por escrito. **Matiz que refuerza la ficha nueva**: «no se recogió ningún
test ⇒ verde» es la MISMA familia que F-038 T0 y que D4, un piso más abajo — D4
guarda el embudo («cero mutantes generados») y el caso «un mutante cuya suite
ejecutó cero tests» sigue sin guarda.

## Checkpoints

- **C1** `[x]` init.sh exit 0; los 9 documentos obligatorios existen.
- **C2** `[x]` una sola `in_progress`; rama correcta; `features.json` coherente.
  *Salvedad no imputable:* `progress/current.md` arrastra secciones de sesiones
  anteriores heredadas de `dev` —la rama solo añade las de F-040—, y eso lo
  resuelve el líder al cerrar sesión.
- **C3** `[x]` solo arnés, ni una línea de `services/`; hexagonal N/A por ámbito;
  cabecera de ruta en los 3 tests nuevos; sin secretos; los `print` son salida de
  CLI; `ruff` limpio en los 3 tests y **12 avisos** en
  `harness/{mutacion,mutacion_paralela,rigor}.py`, los mismos que `dev`.
- **C3 bis** `[x] N/A justificado:` no se toca `docs/referencia/`.
  **C4 ter** `[x] N/A:` `init.sh` dice que F-040 no toca ruta sensible.
- **C4** `[x]` los 27 requisitos con test `test_f040_rN_*` (uno a uno, R1..R27);
  ninguno toca red ni BBDD (dobles y ejecutores falsos); MANUAL: **ninguna**.
- **C5** `[x]` 26/26 tareas `[x]` (P1 es posterior al merge y queda `[ ]` con razón);
  todas nombradas en commits `F-040 Tn:`, agrupados por pares RED/GREEN como F-039,
  que se aprobó así; `git status --porcelain` vacío antes y después de mis pruebas.

### C4 bis — **Rigor** `[x]` `estandar`. **Cobertura** `[x]` `100,0 % (79/79)`

- **Fase RED** `[x]` trazas reales para T1, T7, T10, T12, T14, T16, T18, T21 y
  T23. Para T3–T6 (huecos de **test**, sin código previo que romper) se usa la vía
  que `CHECKPOINTS.md` admite —aplicar el mutante que sobrevivió y verlo morir—:
  los cuatro, con su recuento de rojos.
- **Mutación verificada de forma independiente** `[x]`: recalculé sin ejecutar suite
  el alcance (**362+30+20 = 412 líneas**) y los **49 mutantes generados**, idénticos
  al informe, y reproduje el muestreo con la semilla `20260820`: los **20** salen con
  el mismo `fichero:línea`, operador y texto `original -> mutado`.
- **Muertos comprobados** `[x]` **Campaña NO reejecutada: 336,3 s declarados,
  muy por encima del umbral de 60 s.** En su lugar, recálculo puro + RM1–RM6 +
  dos reproducciones sobre copia.
- **RM1** `[x]` SHA `e73a20791b106ca47bb929ca8051068ebf2a462b`. No es HEAD, y lo
  comprobé: entre ese commit y HEAD **no cambia ni un fichero del alcance** (solo
  `progress/`, `specs/`, `CHECKPOINTS.md` y tests). El único cambio con efecto es el
  test de `6d582b9`, que **mata** al superviviente 3: el informe lo dice y la
  desviación va en la dirección conservadora.
- **RM2** `[x]` `20 × 16,8 = 336 ≈ 336,3 s`; corregido por W, `16,8 × 4 = 67 s`
  contra línea base 64,9 s: sin salto de orden de magnitud. Las 4 líneas base
  (64,7–68,3 s) y el efectivo 137 s encajan con `max(120, ceil(68,3 × 2))`.
- **RM3** `[x]` (punto 5 de arriba). **RM4** `[x]` usada, dos mutantes. **RM5**
  `[x]` **N/A justificado por nivel `estandar`**; la justificación escrita del
  equivalente es aritmética. **RM6** `[x] N/A:` no se retiró ninguna guarda; el diff
  **añade** guardas (`bool`, `--timeout>0`, `--workers>=1`, D4, R18). **Campaña
  manual** `[x] N/A:` la automática dio 49 mutantes.
- **Supervivientes analizados** `[x]` 3/3, ninguno `PENDIENTE`. **Evidencias** `[x]`.

## Trazabilidad y verificación en vivo

| Requisitos | Fichero | Comprobado además a mano, hoy |
|---|---|---|
| R1–R10 | `test_f040_r1_r10_dimensionado.py` | `TOPE_WORKERS=4` y `workers_por_defecto()=4` en 22 núcleos; `--workers 12 → 12` y `rigor.workers=9 → 9` (R10); `rigor.json` sin clave `workers` (R9) |
| R11–R17, R27 | `test_f040_r11_r17_honestidad.py` | `--feature F-038` (alcance vacío) → **exit 3**, «No se ha juzgado NADA», **sin escribir informe**; `--ficheros ","` → **exit 2** con la guarda de entrada de F-039 CR-2 **intacta**, nombrando `['','']` (R17) |
| R18–R26 | `test_f040_r18_r26_huecos.py` | R22: `True`, `0`, `-1` → «no vale»; clave ausente → «Falta»; R23: `--timeout 0`, `--timeout -5`, `--workers 0` → **exit 2** |

D3: `_base_rota_al_final` ramifica por `expirado` antes que por `not verde`, y su
mensaje dice «la suite **NO** falló… No toques la suite»: el texto que mandó al
humano a arreglar una suite impecable ya no puede salir. R24 prueba el orden
`rmtree` → `prune` con un `_git` que devuelve 128.

## Observaciones (no bloquean; corregir antes del porte a `arnes-base` 1.7.2)

1. **`test_f040_r11_r17_honestidad.py:435`** — el test que guarda R27 asserta la
   redacción correcta, pero su **nombre** (`..._el_tiempo_total_se_divide_entre_workers`)
   y su **docstring** («un Tiempo total tres veces menor que `mutantes × media`»)
   repiten la fórmula que `94a7c08` refutó: `Tiempo total == mutantes × media` por
   construcción. Se corrigió el documento, no el test que lo vigila. Dos líneas.
2. **`media × W` es cota alta, no igualdad**: el «Tiempo total» incluye la línea
   base de arranque y la de cierre de cada worker; aquí
   `(336,3 − 65 − 65)/5 ≈ 41 s` por mutante, no 67. Como RM2 existe para cazar
   fraude, sobreestimar le baja sensibilidad: que diga «cota superior» y que el
   informe declare aparte el tiempo de las líneas base.
3. **Dos etiquetas del informe pueden decir de más** por caminos que hoy `main`
   no toma: con `comprobar_base=False` la fila sale «derivado de la línea base ×
   2.0» sin medición, y con `--timeout N` «Suelo configurado» muestra N.

**Lo que NO se tocó, comprobado:** `arnes-base` limpio y en 1.7.1, sin commits
nuevos; `features.json` solo cambia `"pending"` → `"in_progress"`; `alcance.py`
sin tocar, como manda el design.
