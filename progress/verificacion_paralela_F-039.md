<!-- progress/verificacion_paralela_F-039.md -->
# F-039 · Verificación de la campaña paralela (T5, T6, T7 — MANUAL, humano)

Estado: **PENDIENTE DEL HUMANO**. Preparado por el implementer el 2026-08-20;
esperando la salida real.

## Por qué no la ejecuta el agente

`--workers 5` lanza **cinco suites de pytest simultáneas**. En esta máquina ya
se sabe que dos procesos concurrentes tumban el intérprete con `0xC0000142`
(«the application was unable to start correctly»), y una campaña muerta a
medias deja mutantes escritos en worktrees. Es exactamente el caso que R9
manda ejecutar en **sesión dedicada**: nada más corriendo, ni `init.sh`, ni
otra suite, ni otro repositorio, ni otro agente. Por eso T5 y T6 son
verificación MANUAL del humano y no las lanza el implementer.

## Antes de lanzar (comprobaciones de un segundo)

```powershell
git -C C:\Users\pgris\PycharmProjects\albaranes status --porcelain   # vacío
git -C C:\Users\pgris\PycharmProjects\albaranes worktree list        # 1 línea
python -m harness.mutacion --estado                                  # código 0
```

Si `--estado` no devuelve 0, hay una campaña viva o un centinela de una
muerta: `python -m harness.mutacion --restaurar` antes de seguir.

## T5 · El comando exacto (copiar y pegar)

PowerShell, desde `C:\Users\pgris\PycharmProjects\albaranes`:

```powershell
python -m harness.mutacion --feature F-038 --workers 5 --max-mutantes 1 --salida "$env:TEMP\verificacion_paralela_F-039.md"
```

Git Bash, desde la misma raíz:

```bash
python -m harness.mutacion --feature F-038 --workers 5 --max-mutantes 1 --salida "$TEMP/verificacion_paralela_F-039.md"
```

`--max-mutantes 1` es lo que hace barato esto: lo que se verifica es que la
**línea base arranca en los cinco worktrees**, no la campaña entera. Tras la
base evalúa un solo mutante y termina; coste ≈ una suite, no veinte.
`--salida` apunta **fuera de `progress/`** para no pisar ningún informe.

## Criterio de verde (R9)

Las tres cosas, juntas:

1. La salida **NO** contiene `LÍNEA BASE EN ROJO` ni `CAMPAÑA NO VÁLIDA`.
2. La campaña **llega a evaluar** el mutante: aparece la línea de resumen
   `1 mutantes evaluados, ...` y se escribe el informe en `$TEMP`.
3. Al terminar (R12): `git status --porcelain` **vacío** y `git worktree list`
   con **una sola línea**.

Rojo no es «tarda mucho»: es una de esas tres sin cumplirse.

## T6 · Si el proceso muere con `0xC0000142` (R10)

No es un fallo del paralelo: es el límite de esta máquina. Se repite bajando N
y se declara por escrito **el mayor N con línea base verde**:

```powershell
python -m harness.mutacion --feature F-038 --workers 3 --max-mutantes 1 --salida "$env:TEMP\verificacion_paralela_F-039.md"
python -m harness.mutacion --feature F-038 --workers 2 --max-mutantes 1 --salida "$env:TEMP\verificacion_paralela_F-039.md"
```

Se para en el primero que salga verde: ese es el N que se declara. Recuerda
que **no** se declara `mutacion.workers` en `harness/rigor.json` (decisión 3
del humano, D5 del diseño): el N se pasa por `--workers` en la orden.

## Resultados

| N (`--workers`) | Fecha | Línea base | ¿Llegó a evaluar? | Veredicto |
|---|---|---|---|---|
| 5 | — | — | — | PENDIENTE |
| 3 | — | — | — | (solo si 5 falla) |
| 2 | — | — | — | (solo si 3 falla) |

**Mayor N con línea base verde:** PENDIENTE.

### Salida real

```text
PENDIENTE: pegar aquí la salida completa de la ejecución.
```

### Estado del árbol al terminar (R12)

```text
PENDIENTE: pegar aquí `git status --porcelain` y `git worktree list`.
```

## T7 · Diagnóstico si la línea base sale en rojo (R11)

Aplica **solo** si la base sale roja. La causa del reloj ya se eliminó en
F-038, así que cualquier rojo aquí es una causa nueva y **sí** es trabajo de
esta feature: se diagnostica por escrito en esta sección antes de seguir, y si
el arreglo excede el arnés se marca la feature `blocked` en
`harness/features.json`, se anota el motivo en `progress/current.md` y se para.

```text
NO APLICA todavía: la verificación no se ha ejecutado.
```

## Qué depende de esto

R8 dice que no se remide hasta verificar el paralelo. La campaña del bloque D
(T11) se ha lanzado **en serie**, sin `--workers`, precisamente porque no
depende del paralelo: mide con la maquinaria en serie, que es la que este
repositorio lleva usando en todas sus campañas. Lo que queda pendiente de esta
verificación es el uso de `--workers` en campañas futuras, no el número de
T11.
