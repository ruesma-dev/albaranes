<!-- specs/F-039-remedir-campanas-invocacion-rota/design.md -->
# F-039 · Diseño técnico

Feature de **arnés**: no toca `services/**` ni SQL. Nivel de rigor
`estandar`. Servicio afectado: ninguno del pipeline; el sujeto es `harness/`.

## Orden de ejecución y por qué es ese

1. **Bloque B** (constante de filas de reloj) — endurece el test del que
   depende todo lo demás.
2. **Bloque C** (verificar el paralelo) — decide **cómo** se lanza la campaña
   y descarta que quede una causa viva distinta del reloj.
3. **Bloque D** (campaña sobre la maquinaria de hoy) — la medición cara, ya
   con la suite estable.
4. **Bloques A y E** (inventario y cabeceras) — se escriben al final, cuando
   ya se sabe el veredicto real de cada informe.

Medir antes de C sería medir con una maquinaria sin verificar; escribir el
inventario antes de D obligaría a reescribirlo.

## Ficheros a crear

| Ruta | Qué es |
|---|---|
| `tests/test_f039_r3_r7_filas_de_reloj.py` | R3–R7: la constante, `lineas_comparables` y que el test de paridad la usa |
| `tests/test_f039_r15_r16_alcance_por_ficheros.py` | R15–R16: `--ficheros` y sus errores |
| `tests/test_f039_r1_r2_r23_r25_documentos.py` | R1, R2, R23–R25: inventario completo y cabeceras |
| `progress/inventario_mutacion_F-039.md` | R1: una fila por campaña, con veredicto |
| `progress/mutacion_maquinaria_paralela_F-039.md` | R17: informe generado + cabecera manual |
| `progress/verificacion_paralela_F-039.md` | R9–R12: salida real de la verificación manual |
| `progress/impl_F-039.md`, `progress/review_F-039.md` | papeleo del arnés |

## Ficheros a modificar

| Ruta | Qué cambia |
|---|---|
| `harness/mutacion.py` | (1) `FILAS_DE_RELOJ` y `lineas_comparables()` **junto a** `escribir_informe` (~línea 1367); (2) el flag `--ficheros` en `_analizar_argumentos` y su rama en `main`. El mutador, `ejecutor_para` y el contenido del informe no cambian |
| `harness/alcance.py` | Añade `alcance_de_ficheros()`: construir un `Alcance` a partir de ficheros enteros es «qué cambió» declarado a mano, y esa responsabilidad vive aquí, que es la única fuente de verdad del alcance |
| `tests/test_f012_r1_r5_r11_coordinador.py` | El `_comparable` interno del test de paridad (líneas 258-272) pasa a llamar a `lineas_comparables`; se borra la lista de prefijos a mano |
| `progress/mutacion_F-012.md` | Solo la cabecera: el `⚠` se queda y gana el puntero al informe nuevo, dejando claro que mide **otro código** (R23) |
| `progress/mutacion_F-011.md` | Solo la cabecera: decisión del 2026-08-20 y su consecuencia (R24) |
| `harness/features.json`, `progress/current.md`, `progress/history.md` | Estado de la feature y presentación de la lista de huecos (R20) |

## Ficheros que NO se tocan (los que tientan)

- `harness/mutacion_paralela.py` — el paralelo **se verifica**, no se arregla;
  su causa ya se eliminó en F-038. Si hubiera que tocarlo, es R11 y se para.
- `harness/rigor.json` — ver D5: `mutacion.workers` sigue **sin declarar**.
- `harness/servicios.json`, `harness/init.sh` — la invocación ya está
  arreglada; aquí solo se mide.
- `progress/mutacion_F-034.md` (R25) y el resto de informes válidos.
- El cuerpo de `progress/mutacion_F-011.md` y de `mutacion_F-012.md`: sus
  análisis de supervivientes se conservan tal cual, cuelguen de lo que cuelguen.

## Funciones nuevas (capa: utillaje del arnés, sin capa hexagonal)

```python
# harness/mutacion.py — pegado a escribir_informe

#: Prefijos de las filas del informe cuyo valor sale del reloj. Vive AQUÍ,
#: junto a quien las escribe, para que quien añada una fila de reloj la vea.
FILAS_DE_RELOJ: tuple[str, ...] = (
    "Generado por",
    "| Tiempo total",
    "| Línea base (s)",
    "| Media por mutante evaluado (s)",
)

def lineas_comparables(texto: str) -> list[str]:
    """Las líneas de un informe que dos campañas equivalentes deben compartir.

    Descarta las de `FILAS_DE_RELOJ` y el comentario de ruta de la cabecera.
    """
```

```python
# harness/alcance.py

def alcance_de_ficheros(
    rutas: list[str], feature_id: str, raiz: str = "."
) -> Alcance:
    """Alcance declarado a mano: los ficheros indicados, ENTEROS.

    `origen="ficheros"` y `ref_diff=("(sin diff)", <sha de HEAD>)`. Aborta con
    `SystemExit` si una ruta no existe o `es_produccion` la rechaza.
    """
```

`escribir_informe` no cambia de salida: `FILAS_DE_RELOJ` solo **declara** lo
que ya escribe. Comparar por prefijo es deliberado: `| Línea base (s) —
\`etiqueta\`` lleva la etiqueta pegada.

## Cómo se ejecuta cada verificación cara

### C · Verificación del paralelo (R9–R12, MANUAL)

```bash
python -m harness.mutacion --feature F-038 --workers 5 --max-mutantes 1 \
  --salida "$TEMP/verificacion_paralela_F-039.md"
```

- `--max-mutantes 1` es la clave del coste: lo que se verifica es la **línea
  base en los cinco worktrees**, no la campaña. Tras la base evalúa un solo
  mutante y termina. Coste ≈ una suite, no 20.
- **Sesión dedicada**: nada más corriendo —ni `init.sh`, ni otra suite, ni
  otro repositorio—. Cinco suites simultáneas son el límite conocido de esta
  máquina (`0xC0000142`); por eso R10 acepta bajar N y declarar el mayor verde.
- Verde = la salida **no** contiene `LÍNEA BASE EN ROJO` y la campaña llega a
  evaluar. `--salida` fuera de `progress/` para no pisar informes.
- Después: `git status --porcelain` vacío y `git worktree list` con una línea
  (R12). Si quedara algo, `python -m harness.mutacion --restaurar`.

### D · Campaña sobre la maquinaria de hoy (R13–R19, MANUAL)

```bash
python -m harness.mutacion --feature F-039 \
  --ficheros harness/mutacion.py,harness/mutacion_paralela.py,harness/rigor.py \
  --salida progress/mutacion_maquinaria_paralela_F-039.md
```

- Se muta **el árbol de trabajo en HEAD** de esta rama, como cualquier campaña
  normal. Nada de worktrees de ramas viejas.
- `--feature F-039` solo resuelve el **nivel de rigor**: `estandar` ⇒ 20
  mutantes muestreados con semilla `20260820`. Sin el muestreo, mutar tres
  ficheros enteros (~2.500 líneas, `mutacion.py` ya son ~1.900) daría cientos
  de mutantes; con él la campaña cabe en una sesión y es reproducible: dos
  personas obtienen los mismos 20.
- Coste estimado: 20 mutantes × la suite de la raíz (línea base ~50 s, menos
  en los que mueren por `-x`) ≈ 15 min. **Mientras corre, el árbol principal
  está mutado**: nadie lanza `init.sh` ni otra suite hasta que termine.
- `--workers` se decide con el resultado del bloque C: si allí quedó un N
  verde, se usa; si no, `--workers 1`.

## Decisiones y alternativas descartadas

**D1 · Es una campaña NUEVA sobre la maquinaria de mutación tal como es hoy,
no la campaña de F-012 repetida.** Decisión del humano (2026-08-20). Medir el
árbol de agosto contaría qué habría salido entonces: `harness/mutacion.py` ha
crecido +1.346 líneas desde el merge-base de F-012, así que los huecos de
aquel código pueden ya no existir y los de hoy no aparecerían. Lo que interesa
es si está protegido **el código que corre hoy**. Hay que decirlo con esas
palabras en la cabecera del informe (R18) para que dentro de seis meses nadie
lo lea como la campaña de agosto rehecha.
*Descartada A:* medir en un worktree de `feature/F-012-mutacion-paralela` con
el arnés de hoy. Reproduce fielmente la campaña de agosto y responde a la
pregunta que ya no interesa.
*Descartada B:* aplicar el alcance de F-012 al árbol de hoy —
`alcance_de_feature("F-012")` numera sobre la rama F-012: mutaría líneas
ajenas. Peor que no medir.

**D2 · Los números de `mutacion_F-012.md` no se reponen.** Aquella medición
queda invalidada y sin sustituto equivalente; el informe nuevo cubre el mismo
*sujeto* (la maquinaria de mutación) pero **otro código**. De ahí el nombre
`mutacion_maquinaria_paralela_F-039.md`: ni `_remedida` ni `F-012`, porque no
lo es.

**D3 · Cuándo se retira una cabecera `CAMPAÑA NO VÁLIDA`.** Regla: **nunca se
retira de un fichero cuyos números siguen siendo los inválidos**. Solo
desaparecería si el fichero se regenerase en sitio con una medición buena del
mismo código, que aquí no va a ocurrir. F-012 conserva su aviso + puntero
(R23), F-011 lo conserva para siempre (R24), F-034 no se toca (R25).

**D4 · `--ficheros` en vez de un alcance escrito en la spec.** Hoy el alcance
solo se sabe calcular desde un diff, y esta campaña no tiene diff que la
describa. La alternativa —parchear a mano el `Alcance` en un script suelto— no
deja rastro reproducible en el informe. `--ficheros` es genérico, cabe en
cuatro líneas de `alcance.py` y se porta a `arnes-base`.
*Nota de alcance:* entran los **tres ficheros enteros**, no «la parte de
`mutacion.py` que sostiene el paralelo». Recortar por funciones sería un
alcance escrito a mano, imposible de reproducir y de mantener; el muestreo ya
resuelve el coste, que era el único motivo para recortar.

**D5 · NO se declara `mutacion.workers` en `harness/rigor.json`.** Decisión
del humano (2026-08-20), escrita aquí para que nadie lo «arregle» más
adelante: sin declarar, el default se calcula por máquina (`núcleos − 2`, tope
16) y por eso el arnés viaja bien a los cinco proyectos. Declararlo cablearía
el límite de **esta** máquina en el arnés genérico. Para bajarlo puntualmente
está `--workers` en la orden.

**D6 · La deuda heredada del filtro ENTRA.** Es pequeña, vive en el mismo
fichero y sin ella la próxima fila de reloj vuelve a romper el test del que
depende esta feature. El test que la protege no es «revisar la constante»: es
escribir el mismo informe con dos relojes distintos y exigir que
`lineas_comparables` coincida (R4/R5). Eso caza una fila **añadida**, que fue
el caso real de F-038 T5.

**D7 · Los supervivientes se documentan; la ficha no se abre sola.** Rigor
`estandar` exige análisis escrito, no cero supervivientes. Cerrarlos aquí
haría de F-039 una feature sin fondo: son huecos desconocidos hasta que la
campaña termine. Se agrupan por causa, cada uno con su ficha completada, y la
lista se **presenta al humano**, que decide si se abre trabajo, con qué
prioridad y qué entra (R20). Excepción: un defecto real de comportamiento para
la feature (R21).

**D8 · La campaña de F-011 no entra.** Decisión del humano del 2026-08-20: 305
mutantes y 133 supervivientes, invalidada para siempre. Lo que sí entra es su
**consecuencia escrita**: la puerta de evals de F-011 no tiene detrás ninguna
medición de mutación válida (R24).

## Riesgos

| Riesgo | Mitigación |
|---|---|
| `--workers 5` tumba el proceso (`0xC0000142`) | R10: bajar N y declarar el mayor verde; sesión dedicada |
| La campaña muta el árbol principal ~15 min y alguien lanza `init.sh` | Sesión dedicada y aviso en `progress/current.md`; el centinela de `--estado` ya lo detecta |
| Muchos supervivientes | D7: análisis agrupado por causa y lista presentada al humano |
| Una campaña muere a medias y deja mutantes aplicados | `python -m harness.mutacion --restaurar` + `git status` limpio |
| El muestreo elige 20 mutantes casi todos de `mutacion.py` y deja el paralelo sin tocar | Se comprueba el reparto por fichero en el informe; si el paralelo queda sin muestra, se anota y se propone una segunda campaña acotada a ese fichero (no se cambia la semilla a posteriori) |
| El informe nuevo se lee como la campaña de F-012 rehecha | Nombre distinto (D2) + cabecera manual explícita (R18) + puntero en R23 |

## Encaje con la arquitectura

`docs/ARCHITECTURE.md` describe el pipeline de servicios; esta feature vive
íntegra en `harness/`, que es utillaje del repositorio y no tiene capas
hexagonales. No cruza fronteras de proyecto: no toca `azure-apps/`. Las dos
mejoras del bloque B y de `--ficheros` **son genéricas del arnés** y se portan
a `arnes-base` en el mismo trabajo, según la regla de propagación de
`CLAUDE.md`; el inventario y las campañas son de este repositorio y se quedan
aquí.

## Límite de microservicio

No se cruza: ninguna responsabilidad nueva, ningún servicio nuevo, ningún
dominio ajeno. La feature mide y documenta trabajo ya hecho.
