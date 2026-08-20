<!-- specs/F-039-remedir-campanas-invocacion-rota/design.md -->
# F-039 · Diseño técnico

Feature de **arnés**: no toca `services/**` ni SQL. Nivel de rigor
`estandar`. Servicio afectado: ninguno del pipeline; el sujeto es `harness/`.

## Orden de ejecución y por qué es ese

1. **Bloque B** (constante de filas de reloj) — endurece el test del que
   depende todo lo demás.
2. **Bloque C** (verificar el paralelo) — decide **cómo** se lanza la
   remedición y descarta que quede una causa viva distinta del reloj.
3. **Bloque D** (remedir F-012) — la medición cara, ya con la suite estable.
4. **Bloques A y E** (inventario y cabeceras) — se escriben al final, cuando
   ya se sabe el veredicto real de cada informe.

Remedir antes de C sería medir con una maquinaria sin verificar; escribir el
inventario antes de D obligaría a reescribirlo.

## Ficheros a crear

| Ruta | Qué es |
|---|---|
| `tests/test_f039_r3_r7_filas_de_reloj.py` | R3–R7: la constante, `lineas_comparables` y que el test de paridad la usa |
| `tests/test_f039_r1_r2_r20_r22_documentos.py` | R1, R2, R20–R22: inventario completo y cabeceras |
| `progress/inventario_mutacion_F-039.md` | R1: una fila por campaña, con veredicto |
| `progress/mutacion_F-012_remedida.md` | R14: informe generado + cabecera manual |
| `progress/verificacion_paralela_F-039.md` | R9–R12: salida real de la verificación manual |
| `progress/impl_F-039.md`, `progress/review_F-039.md` | papeleo del arnés |

## Ficheros a modificar

| Ruta | Qué cambia |
|---|---|
| `harness/mutacion.py` | Añade `FILAS_DE_RELOJ` y `lineas_comparables()` **junto a** `escribir_informe` (hoy en la línea ~1367). Nada más: ni el mutador, ni `ejecutor_para`, ni el informe cambian de contenido |
| `tests/test_f012_r1_r5_r11_coordinador.py` | El `_comparable` interno del test de paridad (líneas 258-272) pasa a llamar a `lineas_comparables`; se borra la lista de prefijos a mano |
| `progress/mutacion_F-012.md` | Solo la cabecera: el `⚠` se queda y gana el puntero a la remedida (R20) |
| `progress/mutacion_F-011.md` | Solo la cabecera: decisión del 2026-08-20 y su consecuencia (R21) |
| `harness/features.json`, `progress/current.md`, `progress/history.md` | Estado de la feature y ficha nueva propuesta (R17) |

## Ficheros que NO se tocan (los que tientan)

- `harness/mutacion_paralela.py` — el paralelo **se verifica**, no se arregla;
  su causa ya se eliminó en F-038. Si hubiera que tocarlo, es R11 y se para.
- `harness/alcance.py`, `harness/rigor.json`, `harness/servicios.json`,
  `harness/init.sh` — la invocación ya está arreglada; aquí solo se mide.
- `progress/mutacion_F-034.md` (R22) y el resto de informes válidos.
- El cuerpo de `progress/mutacion_F-011.md` y de `mutacion_F-012.md`: sus
  análisis de supervivientes se conservan tal cual, cuelguen de lo que cuelguen.

## Funciones nuevas (capa: herramienta del arnés, sin capa hexagonal)

```python
#: Prefijos de las filas del informe cuyo valor sale del reloj. Vive AQUÍ,
#: pegado a escribir_informe, para que quien añada una fila de reloj la vea.
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

`escribir_informe` no cambia de salida: la constante solo **declara** lo que ya
escribe. Comparar por prefijo es deliberado: `| Línea base (s) — \`etiqueta\``
lleva la etiqueta pegada.

## Cómo se ejecuta cada verificación cara

### C · Verificación del paralelo (R9, MANUAL)

```bash
python -m harness.mutacion --feature F-038 --workers 5 --max-mutantes 1 \
  --salida "$TEMP/verificacion_paralela_F-039.md"
```

- `--max-mutantes 1` es la clave del coste: lo que se verifica es la **línea
  base en los cinco worktrees**, no la campaña. Tras la base, evalúa un solo
  mutante y termina. Coste ≈ una suite, no 20.
- **Sesión dedicada**: nada más corriendo —ni `init.sh`, ni otra suite, ni
  otro repositorio—. Cinco suites simultáneas son el límite conocido de esta
  máquina (`0xC0000142`); por eso R10 permite bajar N y declarar el mayor
  verde.
- Verde = la salida **no** contiene `LÍNEA BASE EN ROJO` y la campaña llega a
  evaluar. `--salida` fuera de `progress/` para no pisar informes.
- Después: `git status --porcelain` vacío y `git worktree list` con una línea
  (R12). Si quedara algo, `python -m harness.mutacion --restaurar`.

### D · Remedición de F-012 (MANUAL)

```bash
git worktree add --detach "$TEMP/f012" feature/F-012-mutacion-paralela
python -m harness.mutacion --feature F-012 --raiz "$TEMP/f012" --workers 1 \
  --salida "<ruta absoluta>/progress/mutacion_F-012_remedida.md"
git worktree remove --force "$TEMP/f012"
```

- El módulo que corre es el de **HOY** (con `ejecutor_para` arreglado); lo que
  se muta y la suite que juzga son los de la rama F-012. Es exactamente la
  campaña original con la invocación arreglada.
- `--workers 1` a propósito: el paralelo crea worktrees desde el `HEAD` de
  `--raiz`, que aquí es un detached de otro worktree. No se anida.
- **El árbol principal queda libre** mientras corre: los mutantes se escriben
  en `$TEMP/f012`, así que el humano puede seguir trabajando (a diferencia de
  la remedición de F-034, que mutaba el árbol real ~18 min).
- Coste estimado: 61 mutantes × la suite de la raíz de entonces. Se lanza en
  sesión dedicada y se declara el tiempo real en el informe.

## Decisiones y alternativas descartadas

**D1 · Se remide el alcance ORIGINAL sobre el árbol de F-012, no el alcance
actual de esos ficheros.** Lo que se declaró inválido es un enunciado
concreto: «los tests de F-012 matan 55 de 61 mutantes de las líneas que F-012
introdujo». Rehacerlo exige el código y la suite de entonces.
*Descartada A:* aplicar el alcance original al árbol de hoy —
`alcance_de_feature("F-012")` numera sobre la rama F-012, y `harness/mutacion.py`
ha crecido +1.346 líneas desde su merge-base: mutaría líneas ajenas. Sería peor
que no medir.
*Descartada B:* mutar los tres ficheros enteros en su versión de hoy. Responde
a otra pregunta —«¿mata la suite de hoy al harness de hoy?»— y esa ya la
contesta la campaña **válida** de F-038 sobre esos mismos cuatro ficheros.
*Descartada C:* medir dentro del worktree con el arnés de la rama. Ahí
`ejecutor_para` es el roto: repetiría el falso verde.

**D2 · Informe nuevo (`_remedida.md`), no regeneración en sitio.** Sigue el
precedente de `mutacion_F-019_remedida.md` y `_F-027_remedida.md`, y conserva
el aviso de invalidez donde tiene que estar. Regenerar
`mutacion_F-012.md` borraría el `⚠` (lo advierte su propia cabecera) y con él
la única señal de que sus números circularon como buenos.

**D3 · Cuándo se retira una cabecera `CAMPAÑA NO VÁLIDA`.** Regla: **nunca se
retira de un fichero cuyos números siguen siendo los inválidos**. Se retira
solo si el fichero se regenera en sitio con la medición buena, porque entonces
los números malos ya no están. Aquí: F-012 conserva su aviso + puntero (R20),
F-011 lo conserva para siempre (R21), F-034 no se toca (R22).

**D4 · La deuda heredada del filtro ENTRA.** Es pequeña, vive en el mismo
fichero y sin ella la próxima fila de reloj vuelve a romper el test del que
depende esta feature. El test que la protege no es «revisar la constante»: es
escribir el mismo informe con dos relojes distintos y exigir que
`lineas_comparables` coincida (R4/R5). Eso caza una fila **añadida**, que fue
el caso real de F-038 T5.

**D5 · Los supervivientes se documentan, no se cierran.** Rigor `estandar`
exige análisis escrito, no cero supervivientes. Cerrarlos aquí haría de F-039
una feature sin fondo: son huecos desconocidos hasta que la campaña termine. Se
agrupan por causa, cada uno con su ficha completada, y se propone **una** ficha
nueva con la lista (R17). Excepción: un defecto real de comportamiento para la
feature (R18).

**D6 · La campaña de F-011 no entra.** Decisión del humano del 2026-08-20: 305
mutantes y 133 supervivientes, invalidada para siempre. Lo que sí entra es su
**consecuencia escrita**: la puerta de evals de F-011 no tiene detrás ninguna
medición de mutación válida (R21).

## Riesgos

| Riesgo | Mitigación |
|---|---|
| La suite de la rama F-012 no arranca hoy (deriva de dependencias) | La línea base aborta limpiamente antes de gastar nada; entonces R19: `blocked`, sin inventar alcance |
| `--workers 5` tumba el proceso (`0xC0000142`) | R10: bajar N y declarar el mayor verde; sesión dedicada |
| Muchos supervivientes | D5: análisis agrupado por causa y una ficha nueva |
| Una campaña muere a medias y deja mutantes | `--restaurar` + `git worktree remove --force`; el árbol principal nunca se muta (D1) |
| El informe remedido se escribe encima del inválido | `--salida` explícita a `_remedida.md` (D2); R20 lo verifica por test |

## Encaje con la arquitectura

`docs/ARCHITECTURE.md` describe el pipeline de servicios; esta feature vive
íntegra en `harness/`, que es utillaje del repositorio y no tiene capas
hexagonales. No cruza fronteras de proyecto: no toca `azure-apps/`. La mejora
del bloque B (constante `FILAS_DE_RELOJ`) **es genérica del arnés** y se porta
a `arnes-base` en el mismo trabajo, según la regla de propagación de
`CLAUDE.md`; el inventario y las remediciones son de este repositorio y se
quedan aquí.

## Límite de microservicio

No se cruza: ninguna responsabilidad nueva, ningún servicio nuevo, ningún
dominio ajeno. La feature mide y documenta trabajo ya hecho.
