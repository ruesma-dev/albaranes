<!-- progress/spec_F-072.md -->
# Spec de F-072 · la caché de suites tiene en cuenta las dependencias

- **Spec:** `specs/F-072-cache-con-dependencias/` (requirements 136/150 con R1–R34; design 250/250; tasks T1–T17).
  Medido con `python -m harness.tamano --feature F-072`: dentro de los topes.
- **Alta:** `harness/features.json` como `spec_ready`, con rigor `critico`, prioridad 1 y rama
  `feature/F-072-cache-con-dependencias` (worktree `C:\Users\pgris\PycharmProjects\albaranes-F-072`, creada desde
  `dev` en `4f1e802`). `BACKLOG.md` regenerado con `python harness/backlog.py`.
- **Id libre:** F-072 no existe en `dev` ni en ninguna rama local, incluidas las de F-070 y F-071 (búsqueda en el
  `features.json` de todas).
- **No se ha ejecutado ninguna suite** (F-070 está en curso).

## Qué propone, en cinco líneas
1. `servicios.json` gana tres campos opcionales por servicio: `depende_de` (rutas del repositorio), `importa` (módulos
   cuya ruta real se comprueba) y `entradas_no_versionadas`. Por defecto también cuentan `.env` de la raíz y el del
   servicio, solo por metadatos. Sin los campos, todo sale igual que hoy.
2. La clave se calcula en Python (`harness/cache_suites.py`, testeable y con campaña de mutación). Es el `sha256` de:
   hash del servicio, hash de sus dependencias, intérprete, ruta real de los módulos importados (con una sonda que usa
   el intérprete del servicio) y huella de las entradas locales. Con algo sucio no hay caché, como hoy.
3. Un módulo importado desde fuera del repositorio en curso (el caso del worktree) da un `[AVISO]` visible y no se
   cachea.
4. La línea de caché dice la fecha del verde que reutiliza. `ARNES_SIN_CACHE=1` fuerza la ejecución (y refresca la
   caché).
5. Porte pieza a pieza a `arnes-base` como 1.7.16, porque `servicios.py`, el ejemplo y la §7 bis son hoy idénticos en
   los dos repositorios.

## Hallazgo que conviene saber antes de la PARADA 1
`arnes-base` ya tiene este mismo arreglo en su backlog: la **F-028 del taller** («La caché de suites no tapa un rojo»,
`pending`, `critico`, en la rama `dev` de `arnes-base`). Viene del encargo `ENCARGO_1.7.12_…md`, que trae dos
reincidencias más de otros proyectos: un `.env` que cambia y un test que lee `docs/` fuera de su servicio. La spec
cumple sus siete criterios de aceptación, para que haya **un solo** cambio de formato de la clave y no dos.

## Preguntas para el humano (con recomendación)
- **P1 · Módulo importado desde fuera del repositorio: ¿`[AVISO]` o `[KO]`?** Recomiendo `[AVISO]` (design D2). En
  este repositorio, todos los worktrees importan la comun del árbol principal, así que un `[KO]` pondría en rojo
  todos los worktrees sin que la feature tenga culpa. La suite sí se ejecuta y el aviso dice qué copia prueba.
- **P2 · ¿Arreglar también QUÉ comun prueban las suites en un worktree?** F-072 hace visible el problema (ya no hay
  verde de caché), pero en un worktree sv1–sv9 siguen probando la comun del árbol principal. Ese es el fondo del caso
  (b) y hoy obliga al reviewer a ejecutarlas a mano con la comun de la rama. Recomiendo una **feature aparte después
  de F-072**: por ejemplo, anteponer en `PYTHONPATH` la ruta declarada de la dependencia, o un venv por worktree.
  Cambia cómo se ejecutan las suites, no la caché.
- **P3 · `ARNES_SIN_CACHE=1` y la regla «`init.sh` tal cual».** Los agentes solo tienen permitido
  `bash harness/init.sh` sin variables. Si quieres que el reviewer pueda forzar la ejecución sin caché, la entrada
  `Bash(ARNES_SIN_CACHE=1 bash harness/init.sh)` en `.claude/settings.json` la añades tú: la spec no toca permisos.
  Recomiendo añadirla.
- **P4 · Alcance: la huella del `.env`** (R9, R10 y parte de R33). No la pediste tú, la pide la F-028 del taller.
  Recomiendo mantenerla, para cerrar la F-028 entera con un único cambio de formato. Quitarla ahorra unas 30 líneas
  de código y sus tests.
- **P5 · Destino del porte:** commit local en `main` de `arnes-base` como **1.7.16** (como la 1.7.15). La 1.8.0 está
  reservada por el encargo de adelgazar. La F-028 del backlog del taller la cierra la sesión de `arnes-base`, que es
  la dueña de su `features.json`. Desde aquí solo se anota «Implementado en 1.7.16» en el encargo 1.7.12.
  Recomiendo que sea así.

## Rigor `critico` (justificación corta; detalle en design §1)
Decide qué es verde en el portero de todos los repositorios con arnés, y su modo de fallo es un verde falso
silencioso. El taller ya la clasificó `critico`. El módulo es pequeño, así que la campaña completa sale barata.

## Lo que la spec deja fuera
- Cambiar qué copia de la comun importan las suites (P2).
- Permisos (P3).
- El backlog del taller (P5).
- `harness/VERSION` de albaranes, que sigue en 1.7.2 con una nota en `ARNES_VERSION.md`, porque aquí faltan la
  1.7.3–1.7.15.

## Verificación que no puede hacer el implementer
T16 es MANUAL del humano, tras fusionar en `dev`: comprobar en el árbol principal que un commit en la comun invalida la
caché de sv1–sv9.
