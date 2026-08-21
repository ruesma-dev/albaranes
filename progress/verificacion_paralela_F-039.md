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

---

## RESULTADO REAL — 2026-08-21, ejecutado por el humano (T5, T6)

### VERDE con `--workers 3`, y solo con el reloj ampliado

```
python -m harness.mutacion --feature F-039 --ficheros harness/rigor.py \
  --workers 3 --max-mutantes 3 --timeout 600 --salida "$env:TEMP\verificacion_paralela_F-039.md"

[base] .../wk_0: en verde (119.3 s)
[base] .../wk_2: en verde (119.5 s)
[base] .../wk_1: en verde (121.6 s)
3 mutantes evaluados, 1 muertos, 2 supervivientes, 0 timeouts, 0 sin veredicto en 277.2 s
```

Los cuatro criterios de verde, cumplidos: 3 de 3 evaluados, sin `CAMPAÑA NO
VÁLIDA`, cero timeouts, y árbol y worktrees limpios al terminar.

**La campaña paralela FUNCIONA.** Monta un worktree por worker, cada línea base
pasa dentro del suyo, reparte los mutantes y limpia al terminar. El hallazgo (b)
que motivó F-039 —«no se puede ejecutar»— queda **cerrado**.

### Pero el arnés la deja inutilizable por defecto

| Dato | Valor |
|---|---|
| Suite en reposo | ~51 s |
| Suite con **1** worker | 97,5 s |
| Suite con **3** workers | **119,3 – 121,6 s** |
| `timeout_por_mutante_s` de `rigor.json` | **120 s** |
| Workers **por defecto** en esta máquina (22 núcleos) | **16** |

Con tres workers una de las tres líneas base **ya supera el timeout**. Con el
default de 16, ninguna cabría: la campaña expiraría entera. **Nadie puede lanzar
`--feature X` sin `--workers` en esta máquina y obtener algo válido.**

No es un problema de este equipo: la fórmula del default (`núcleos − 2`, tope
16) supone que el cuello de botella es la CPU, cuando cada worker arranca **una
suite completa** —intérprete, importaciones, E/S—. A más hilos, peor.

### Intento previo, con `--workers 5 --max-mutantes 1` (inválido, y por qué)

Un solo mutante ⇒ **un solo worker**: no ejercitó el paralelo. Además expiró el
mutante y la línea base de cierre con el timeout de 120 s, y el mensaje final
dijo «La base se rompió… **Arregla la suite y repite la campaña**» cuando la
suite estaba impecable: solo había **expirado** (código −1). Es el defecto
`_base_rota_al_final`, mintiendo en su primera ejecución real.

### Lo que queda por decidir (paso 4)

1. **Que el timeout escale con los workers.** El arnés ya reconoce el factor de
   workers al *juzgar* el coste por mutante (1.6.3), pero no al *conceder* el
   tiempo. Es la misma idea aplicada a medias.
2. **Revisar la fórmula del default de workers**: un tope de 16 es irreal cuando
   cada worker corre una suite entera.
3. **`_base_rota_al_final`**: distinguir expirada (código −1) de fallida.
4. **N=5 no se probó**: con 3 verde y la base rozando el timeout, subir sin
   arreglar (1) no tiene sentido.
5. **Dos supervivientes nuevos** en `harness/rigor.py`, huecos de test reales:
   línea 258 (`return 1` → `return 2`) y línea 211 (`or` → `and`, la guarda de
   feature sin `rigor` o con `rigor` nulo — no se prueba porque hoy las 39
   fichas declaran rigor).
