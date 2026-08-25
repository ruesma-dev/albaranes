<!-- progress/review_F-036_bloques_BCD_pasada2.md -->
# F-036 · Review ACOTADA de los bloques B, C y D — PASADA 2

Revisión incremental desde `7e2c300` (pasada 2): los nueve commits `F-036
CR-1..CR-9` (`2025e08` → `465d295`). Lo aprobado en la pasada 1 y el bloque A no
se vuelven a mirar.

**VEREDICTO: APROBADO (bloques B, C y D).** Los dos bloqueantes resueltos y los
seis cambios hechos. **No cierra la feature**: sigue `blocked` por F-043 y
T23/T24 son del humano. Quedan cuatro pendientes menores, ninguno de euros.

**Rigor `critico`** (declarado; `features.json` no se tocó). La mutación (T23)
queda fuera de este encargo por decisión del líder: no es un N/A, es tarea
abierta que bloquea el cierre, no esta review. **Ejecutado por mí:** `bash
harness/init.sh` → **exit 0** (raíz `532 passed in 103,47s`; `PUERTA COBERTURA
[OK] 98.2%`, 278/283). Los seis servicios salían por caché: relancé sus suites
**en serie** → sv6 `180`, sv3 `125`, comun `75+3s`, sv2 `58`, sv5 `18`, sv4
`131`. Tres sondas con el builder real y un worktree desechable en `7e2c300`;
`git worktree list` y `git status` limpios al acabar.

## Bloqueante 2 (el que vale euros) — RESUELTO, medido por mí

Reproduje el escenario de la pasada 1 con el builder real (SALMEDINA sin
`volumen_m3` ni `contenedores`), **sin usar los tests del implementer**, y lo
mismo en un worktree en `7e2c300`, para tener el antes y el después:

| Escenario | ANTES (`7e2c300`) | AHORA (`465d295`) |
|---|---|---|
| Sin contenedores | syn `cant=6.0`, **importe 306,00**, total **1026,00**, `review=False` | syn `cant=None`, **importe None**, total **720,00**, `review=True` |
| 6 m³ / 12 m³ / `contenedores=3` | 51,00 / 102,00 / 153,00 (totales 171 / 342 / 513) | **idénticos** |

El fallback está fuera entero (`valuation_builder.py:1468-1473`) y la línea sale
explicada: `['inherited_from_base_line', 'residuos_sintetica_sin_cantidad']` con
`review_required=True` (`:1664-1669`). Los 720,00 de la base son el fallback
preexistente de `importe_calculator`, y el tercer test los compara en vez de
congelarlos: correcto. **No ha regresado nada**: hormigón intacto (padre de
hormigón → 8.0) y las M1/código bajo padre de residuos con m³ heredan 1 UD.

## Bloqueante 1 — RESUELTO donde lo señalé; queda un residuo que yo no vi

`ruesma_comun/ler.py:8-25` y `albaranes-api/domain/models/tipologia.py:22-31`
dicen ahora la verdad (consumidores sv2 y **sv6**) y dejan escrito que sv5 **no**
lo es, con fecha y el commit `7ca2ffc`; `requirements.md:71-72` ya dice «sv2 y
sv6 (sv5 no: R13 retirado)». Los tres sitios que nombré, cerrados. **Pero el
grep del implementer («no queda ninguna afirmación») no es exacto**:
`albaranes-api/tests/test_f036_r14_ler_reexportado.py:5` sigue diciendo «porque
sv5 tambien los necesita (R13)». Docstring de test, sin efecto, y tampoco la vi
yo en la pasada 1: no levanta el veredicto → **cambio requerido 1**.

## Los seis cambios requeridos

1. **Fecha ≠ LER — hecho y bien situado.** `ler_creible` (`ler.py:106-144`) ES
   el cuerpo que ya tenía `texto_contiene_ler`, que pasa a ser `ler_creible(t)
   is not None`, con test que impide que diverjan. Sonda mía: `"…DESDE
   01-01-25"` y `"INCREMENTO 192137"` → `None`; `"INCREMENTO LER 170802 …"` y
   `"INCREMENTO 17 08 02"` → `170802`. Vive en comun: R14 a salvo.
2. **Agujero de la congelación — cerrado donde lo señalé, con guardián.**
   `_motivos_de` resuelve `ast.Name` contra una tabla que sigue el `from
   application.services.X import CONST` hasta sv6. Lo probé con nueve formas: ve
   el literal, la constante local, la importada de sv6 y la aliasada; **se le
   escapan aún en silencio** `ri.RAZON_X`, las constantes de fuera de sv6, las
   locales de función y `extend`/`insert`, ninguna usada hoy → **CR 3**.
3. **`_tiene_valor` separa el `bool` del cero — correcto.**
   `contexto_linea_merger.py:84-92`: `bool` ANTES que el número (por
   `False == 0`), `str` en blanco → False, `int/float` → `valor != 0`. Así
   `carga_incompleta=False` sigue puntuando y las siete medidas a 0 abren el
   hueco de R11 — que es lo que el contrato ya pedía: `contexto_linea.py:141`
   dice «null si no consta **o es 0**».
4. **Segunda precondición de R25 — declarada** en la docstring (las DOS, y
   SS-0003967 «bajo hipótesis») y fijada como test
   `..._con_el_match_real_de_ss_0003967_no_se_llega_a_210`: **90,00 €** frente a
   los 210,00 de R25, igual que medí en la pasada 1. Sin RED, con motivo válido.
5 y 6. **`pytest`/`coverage` de sv4 documentados** al principio de su README
   (comando del portero y por qué no van en `requirements.txt`), y **las nueve
   medidas derivadas de `ContextoLinea`**, con RED de la décima medida.

## C4 ter — cotejo MANUAL del diff (encargo mío de la pasada 1)

`PUERTA RUTAS SENSIBLES` volvió a salir `N/A` («sin feature en curso con rama»),
así que coteje el diff a mano contra `harness/rutas_sensibles.json`:
`valuation_builder.py` y `residuos_incrementos.py` **caen** en
`…/application/services/**` (redes deterministas de sv6) y
`albaranes-api/domain/models/tipologia.py` en `…/domain/models/**` (aunque solo
cambie un comentario); `ruesma_comun/ler.py` **NO** es ruta declarada (solo lo es
`ruesma_comun/llm/**`), ni `albaranes-persistencia/**`, ni los tests. La puerta
habría dado **AVISO** por faltar `progress/evals_F-036.md`. **Motivo**: gasta LLM
real (decisión del humano) y los seis `_indice.json` siguen con `casos = 0`.

## Checkpoints

- **C1** [x] exit 0 y documentos obligatorios. **C2** [x] ninguna
  `in_progress`, rama correcta, `current.md` con la sesión viva.
- **C3** [x] sin ficheros nuevos; la defensa de LER vive en comun, sin duplicar
  en sv6; sin prints, secretos, TODOs ni dependencias nuevas (grep sobre el
  diff). **C3 bis** N/A: no toca `docs/referencia/`. **C4** [x] los ocho puntos
  con test trazable y en verde, ninguno toca red, BBDD ni LLM; T23/T24 en
  `tasks.md:55-56` con su comando.
- **C4 bis** [x] parcial y acotado: rigor declarado; RED con traza real en
  CR-2/3/4/5/6 —**la de CR-2 la verifiqué yo** en el worktree de `7e2c300`—,
  CR-7 sin RED con motivo válido, CR-1 y CR-8 documentación; cobertura `[OK]`
  98,2 %; «Evidencias» presente. **Mutación fuera de encargo (T23)**, no N/A.
  **C4 ter** [x] cotejo manual del diff, arriba, con su motivo escrito.
- **C5** [ ] **a propósito**: T23/T24 abiertas, T11 en `[~] RETIRADA` y la
  feature `blocked`. Un commit por punto (`F-036 CR-n:`, no `Tn:`: son
  correcciones), árbol limpio y `features.json` sin tocar. Lo cierra el líder.

## Pendientes para que F-036 pueda cerrarse (del humano / del líder)

1. **F-043**: la feature está `blocked` a su espera.
2. **T23** · `python -m harness.mutacion --feature F-036`, cero supervivientes o
   justificación aceptada (rigor `critico`), y su revisión RM1–RM6.
3. **T24** · BBDD real en SOLO LECTURA, los 7 albaranes de SALMEDINA. **Añadir
   ahí**: que ninguna línea real escriba el incremento como `INCREMENTO 170802`
   —pegado y sin `LER`—, grafía que casaba antes y ahora da `None` (medido).
4. **Evals** (`progress/evals_F-036.md`, cuando los fixtures tengan casos) y
   **C5** completo, con `features.json` a `done` tras el veredicto de cierre.

## Cambios requeridos (no levantan la aprobación; antes de cerrar)

1. `albaranes-api/tests/test_f036_r14_ler_reexportado.py:5` aún dice que el
   catálogo se movió «porque sv5 tambien los necesita (R13)». Una línea.
2. **La sintética muda**: con `modifier_source` distinto de `gestion_residuos` y
   padre de residuos SIN contenedores, la línea sale con `cantidad=None`,
   `importe=None`, **`review_required=False` y sin ninguna razón** (sonda mía).
   No hay euros de más —es más seguro que antes, que heredaba los 6 m³—, pero es
   la «línea muda» que `RAZON_SIN_CANTIDAD` evita: la guarda de `:1664` está
   atada a `modifier_source`, no a `padre_residuos`.
3. Que `_motivos_de` **falle a gritos** ante un `reasons.append(<expresión que no
   sabe resolver>)` en vez de saltárselo en silencio (formas del punto 2).
4. **`claves_dedupe`** (`residuos_incrementos.py:146`) sigue llamando a
   `normalizar_ler` sobre texto libre: mismo defecto que se acaba de corregir en
   `es_linea_incremento_ler`, y `ler_creible` lo cierra. Lo observó el propio
   implementer; se aprueba, pero que no se quede.

## Automejora (propuesta, no aplicada)

Repito la de la pasada 1: `harness.rutas_sensibles` debería aceptar `--feature
F-XXX` explícito, porque una ficha en `blocked` apaga una puerta de contenido.
Y añado: un helper de análisis estático que alimenta una congelación debería
**fallar ante lo que no sabe leer**; en silencio, es decorado.
