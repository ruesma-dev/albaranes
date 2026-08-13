<!-- specs/F-012-mutacion-paralela/design.md -->
# F-012 · Campaña de mutación en paralelo — Diseño

## Idea central

La campaña actual (`harness/mutacion.py::ejecutar_campania`) ya hace bien lo
difícil: aplica un mutante, lanza la suite del servicio dueño del fichero,
restaura con `try/finally` y una red de seguridad final. **No se reescribe
nada de eso.** El paralelismo se monta POR FUERA:

1. El **coordinador** calcula el alcance, genera los mutantes UNA vez desde
   el árbol principal y aplica el muestreo UNA vez (mismo código de hoy).
2. Crea N `git worktree` desechables desde `HEAD`, en el temp del sistema.
3. Lanza N **hilos**; cada hilo llama a `ejecutar_campania(...)` tal cual,
   con `raiz=<su worktree>` y `mutantes=<su partición>`. El trabajo pesado
   (pytest) va en subprocesos, así que el GIL no pinta nada, y las garantías
   de restauración de `ejecutar_campania` aplican POR WORKER sin duplicar
   código.
4. Fusiona los N `InformeMutacion` parciales en uno, reordena por la clave
   estable `(fichero, linea, col, operador)` y llama al `escribir_informe`
   de siempre. El informe sale idéntico al de la serie salvo fecha y tiempo.
5. `finally`: retira los N worktrees pase lo que pase.

El árbol principal no se muta nunca en modo paralelo: la «restauración
garantizada por worker» del requisito es doble —el `finally` de
`ejecutar_campania` dentro de cada worktree, y el borrado del worktree
entero— y el peor caso imaginable (kill -9) deja basura solo en el temp del
sistema, que el `git worktree prune` del siguiente arranque desregistra.

## Ficheros a crear

- **`harness/mutacion_paralela.py`** — todo lo nuevo vive aquí, solo
  biblioteca estándar (`threading`, `tempfile`, `subprocess`, `os`,
  `shutil`), como el resto del arnés. Contenido:

  - `repartir(mutantes: list[Mutante], n: int) -> list[list[Mutante]]` —
    función pura; round-robin por índice (`mutantes[i::n]`) sobre la lista
    YA ordenada y muestreada. Determinista: mismas entradas, mismas
    particiones (R3).
  - `fusionar(alcance, parciales: list[InformeMutacion], generados, ...)
    -> InformeMutacion` — función pura; suma `muertos`, concatena y reordena
    `supervivientes`, `timeouts` y `mutantes_evaluados` por la clave
    estable; conserva `generados`, `muestreado`, `max_mutantes` y `semilla`
    del coordinador; `segundos` = reloj de pared de la campaña (R4).
  - `arbol_limpio(raiz: str) -> bool` — `git status --porcelain` vacío (R9).
  - `class Worktrees` — gestor con protocolo de contexto:
    - `__enter__`: `git -C raiz worktree prune` y después, por worker,
      `git -C raiz worktree add --detach <tmp>/wk_i HEAD` con
      `tempfile.mkdtemp(prefix="mutacion_<feature>_")` FUERA del repo.
    - `__exit__`: por cada worktree `git worktree remove --force`; si falla
      (fichero bloqueado en Windows), `git worktree prune` +
      `shutil.rmtree(ignore_errors=True)`. Se ejecuta también con excepción
      o `KeyboardInterrupt` en vuelo (R10).
  - `resolver_interpretes(alcance, servicios, raiz) -> dict[str, str]` —
    resuelve POR ADELANTADO el intérprete de cada servicio afectado por el
    alcance llamando a `interprete(servicio, raiz_principal)`; un venv
    declarado e inexistente revienta aquí, antes de crear worktrees (R11).
    Nota: `interprete()` ya devuelve ruta absoluta, así que vale tal cual
    para ejecutar la suite desde el worktree.
  - `ejecutar_campania_paralela(alcance, servicios, timeout_s, raiz,
    workers, max_mutantes, semilla, eco) -> InformeMutacion` — el
    coordinador descrito arriba. Detalles:
    - genera y muestrea con `generar_mutantes` + la misma lógica de
      `random.Random(semilla).sample` que hoy vive en `ejecutar_campania`
      (se reutiliza pasando `mutantes=` ya muestreados y `max_mutantes=None`
      a cada worker; la fila de muestreo del informe la repone `fusionar`);
    - cada hilo construye su factoría `ejecutor_de` con
      `ejecutor_para(fichero, servicios, raiz=<worktree>,
      raiz_venvs=<árbol principal>)` (ver cambio en `mutacion.py`) (R5);
    - `eco` compartido con `threading.Lock` y contador global
      (`[i/total] veredicto descripcion`): el orden de las líneas de
      progreso NO es contractual, el informe sí;
    - cancelación cooperativa: un `threading.Event` que los workers
      consultan entre mutante y mutante vía el parámetro `eco`… no: se
      implementa envolviendo la partición en un iterador que corta cuando el
      evento está puesto, sin tocar `ejecutar_campania`. `KeyboardInterrupt`
      en el hilo principal ⇒ `event.set()`, `join()` a los hilos (el pytest
      en vuelo muere solo con el Ctrl-C de consola o agota su timeout) y el
      `finally` de `Worktrees` limpia igual.

- **`tests/test_f012_r3_r4_reparto_agregacion.py`** — funciones puras.
- **`tests/test_f012_r2_r9_r10_worktrees.py`** — repos git temporales en
  `tmp_path` (git local, sin red): creación, limpieza en éxito, limpieza con
  excepción simulada, prune de huérfanos, guarda de árbol sucio.
- **`tests/test_f012_r1_r5_r11_coordinador.py`** — coordinador con ejecutor
  falso inyectado (registra desde qué `raiz` y con qué ejecutable se le
  llamó); venv inexistente ⇒ fallo antes de crear worktrees.
- **`tests/test_f012_r6_timeout.py`** — el timeout llega a cada worker y los
  timeouts se agregan.
- **`tests/test_f012_r7_r8_cli.py`** — resolución del default
  (CLI > rigor.json > núcleos−2), camino en serie intacto con efectivo ≤ 1.

## Ficheros a modificar

- **`harness/mutacion.py`** — tres cambios acotados:
  1. `ejecutor_para(fichero, servicios, raiz=".", raiz_venvs=None)`: nuevo
     parámetro opcional; `interprete(servicio, raiz_venvs or raiz)`. Con
     `None` el comportamiento actual es idéntico (compatible con todos los
     llamantes de hoy).
  2. `_analizar_argumentos`: nuevo `--workers` (int, default `None`).
  3. `main()`: si el nº efectivo de workers es ≥ 2 delega en
     `harness.mutacion_paralela.ejecutar_campania_paralela`; si no, el
     camino actual línea a línea (R8). La línea «Generado por `python -m
     harness.mutacion --feature F-XXX`» del informe NO cambia: la identidad
     del informe manda sobre la publicidad del flag.
- **`harness/rigor.py`** — helper `workers_mutacion(rigor) -> int | None`
  que lee la clave opcional `mutacion.workers` (simétrico a
  `timeout_mutacion`, pero SIN reventar si falta: `None` ⇒ el default de
  núcleos−2 lo pone `mutacion.py`).
- **`harness/rigor.json`** — solo el texto `$doc` del bloque `mutacion`,
  documentando la clave opcional `workers`. NO se añade la clave con valor:
  el default por núcleos es mejor que un número cableado que viaja de
  máquina en máquina.

## Ficheros que NO se tocan

- `harness/alcance.py`, `harness/servicios.py`, `harness/cobertura.py`,
  `harness/rutas_sensibles.py`, `harness/init.sh` (la campaña sigue sin
  correr en el portero).
- Dentro de `mutacion.py`: `generar_mutantes`, `aplicar_mutante`,
  `ejecutar_campania`, `escribir_informe`, `EjecutorPytest` — ni una línea.
  Son exactamente lo que el reviewer recalcula en C4 bis; si no cambian, el
  recálculo independiente (alcance + nº de mutantes, cálculo puro) sigue
  valiendo sin retocar CHECKPOINTS.
- `CHECKPOINTS.md` y el resto de docs del arnés: el comando documentado
  `python -m harness.mutacion --feature F-XXX` sigue funcionando tal cual;
  `--workers` es opcional.
- `services/**`, `evals/**`, `harness/features.json` (lo actualiza el
  líder).

## Encaje en la arquitectura y límite de microservicio

Esto es herramienta del arnés (transversal, biblioteca estándar), no lógica
de negocio del pipeline de albaranes: no toca colas, ni schema, ni servicios.
No hay frontera de microservicio que evaluar; su «casa» natural es
`arnes-base`, y por eso el portado es un requisito (R12), no una cortesía.

## Decisiones y alternativas descartadas

1. **Hilos + subprocesos, no `multiprocessing`.** El coste real es el pytest
   subproceso; los hilos solo esperan E/S. `multiprocessing` obligaría a
   picklear `Mutante`/`Alcance`, duplicaría la gestión de Ctrl-C en Windows
   y no aportaría CPU.
2. **Worktrees `--detach`, sin rama efímera.** Una rama por worker
   ensuciaría `git branch`, podría colisionar entre campañas y habría que
   borrarla aparte. Detached sobre `HEAD` no deja rastro en refs.
3. **Worktrees en el temp del sistema, no bajo el repo.** Dentro del repo
   aparecerían en `git status`, en la recolección de pytest de la raíz y en
   el radar del portero. En temp, el peor caso (proceso matado) deja basura
   fuera del árbol y `git worktree prune` desregistra al siguiente arranque.
4. **Exigir árbol limpio en vez de copiar los ficheros sucios al worktree.**
   Copiar lo sucio es un vector de discrepancias silenciosas (¿qué se copia:
   el alcance, todo lo modificado, lo no trackeado?). La campaña de cierre
   se lanza siempre con la feature commiteada; para el caso raro queda
   `--workers 1`, que conserva el comportamiento in situ de hoy.
5. **Reutilizar `ejecutar_campania` por worker en vez de un bucle nuevo.**
   Ya acepta `mutantes=` y `raiz=`; su `try/finally` + red de seguridad son
   exactamente la «garantía actual, multiplicada» que pide la feature. Un
   bucle paralelo propio duplicaría la parte más delicada del módulo.
6. **Informe sin fila «Workers».** Identidad estricta con el de serie
   (criterio del humano). El nº de workers queda en stdout y en
   `progress/impl_F-012.md`.
7. **Venvs resueltos contra el árbol principal.** Los worktrees no traen
   venvs (gitignorados). En albaranes ningún servicio declara `venv`, pero
   el arnés es genérico: se resuelve el intérprete absoluto en el árbol
   principal y se ejecuta con `cwd` en el worktree.

## Coste y beneficio (números)

- Beneficio: F-011 = 305 mutantes × ~12,1 s = 3.694 s en serie. Con la
  máquina actual (22 núcleos ⇒ default 20 workers), techo teórico ~185 s de
  evaluación; realista < 10 min contando setup y desbalanceo. Una fracción
  clara del tiempo, que es el criterio de éxito.
- Coste: `git worktree add` de este monorepo son segundos por worker
  (checkout de ficheros versionados, sin venvs ni node_modules); con 20
  workers, en el orden del minuto, que se paga una vez por campaña. Con
  pocos mutantes no compensa: por eso el efectivo es
  `min(workers, nº mutantes)` y con efectivo ≤ 1 ni se crean worktrees.
- Disco: N checkouts del árbol en temp mientras dura la campaña; se borran
  al salir.

## Compatibilidad con la caché de suites del portero

`.arnes_cache/` es por árbol de trabajo, está gitignorado y NO se materializa
en los worktrees; los workers no lo escriben (lanzan pytest directo con
`-p no:cacheprovider`, no `init.sh`). Como el modo paralelo no ensucia el
árbol principal en ningún momento, el hash de árbol commiteado con el que la
caché valida su verde sigue siendo el mismo antes, durante y después de la
campaña: la caché ni se invalida ni —peor— conserva un verde de un árbol que
la campaña hubiera dejado a medias. En serie la garantía equivalente ya
existía (restauración); en paralelo es aún más fuerte (ni se toca).

## Riesgos

- **Timeouts por carga.** N suites simultáneas cargan la máquina y una suite
  lenta puede rozar el `timeout_por_mutante_s` (120 s) que en serie no
  rozaba. Mitigación: default núcleos−2, mismo timeout que en serie, y la
  fila «Timeouts» del informe delata cualquier discrepancia en la
  comparación serie-vs-paralelo de T5. Si apareciera, se ajusta
  `timeout_por_mutante_s` en `rigor.json` (vive en configuración, no en
  código).
- **Venv con instalación editable apuntando al árbol principal.** Si un
  proyecto genérico instalara su paquete editable en el venv, la suite del
  worktree podría importar el código SIN mutar del árbol principal y dar
  supervivientes falsos. En albaranes no aplica (sin venvs declarados; los
  servicios se importan desde su cwd). Se documenta en el docstring del
  módulo como limitación conocida del modo paralelo.
- **Suites que dependan de ficheros no versionados (`.env`, datos
  locales).** No existen en el worktree. Las convenciones ya prohíben unit
  tests con esas dependencias; un proyecto que las viole verá la suite roja
  en el worker (mutantes «muertos» de más). Documentado como limitación.
- **Windows y borrado de worktrees.** Un proceso rezagado puede bloquear un
  fichero durante `worktree remove`. Por eso el fallback
  `prune + rmtree(ignore_errors=True)` y el `prune` de arranque de la
  campaña siguiente.

## Portado a arnes-base (R12)

En el mismo trabajo, copiar a
`C:\Users\pgris\PycharmProjects\arnes-base\arnes-base\harness\`:
`mutacion.py`, `mutacion_paralela.py`, `rigor.py` y `rigor.json` (el `$doc`),
con commit local en arnes-base describiendo la mejora (el push lo hace el
humano, como siempre). Los tests `test_f012_*` se quedan en albaranes:
arnes-base no versiona suites de tests hoy, y cambiar eso no es de esta
feature.

## Preguntas abiertas (para el humano, antes de implementar)

1. **Comparación serie-vs-paralelo de T5.** Propuesta: comparar con muestreo
   fijo (`--max-mutantes 60 --semilla 20260813`, ~12 min la pasada en serie)
   y, aparte, campaña completa de F-011 SOLO en paralelo, contrastando
   totales con el `progress/mutacion_F-011.md` histórico a título
   informativo (la suite ha cambiado desde entonces: no tiene por qué
   clavar los 133 supervivientes). ¿Vale, o quieres también la serie
   completa (~1 h) para una comparación total-contra-total en el mismo
   árbol?
2. **`nucleos - 2`** se lee de `os.cpu_count()` (lógicos; aquí 22 ⇒ 20
   workers). ¿De acuerdo con usar núcleos lógicos, o prefieres un tope
   adicional (p. ej. máximo 16)?
