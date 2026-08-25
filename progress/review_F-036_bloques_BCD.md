<!-- progress/review_F-036_bloques_BCD.md -->
# F-036 · Review ACOTADA de los bloques B, C y D

Revisión incremental desde `6f8ad4f` (pasada 2). El bloque A queda dado por bueno
(`review_F-036_bloque_A.md`); solo se remiró T0. `7137d4b`, `d6e101f` y `390167f`
son papeleo del líder y no se revisan.

**VEREDICTO: RECHAZADO** (bloques B, C y D). Dos bloqueantes, ambos baratos; el
resto está bien hecho. **No cierra la feature ni la juzga entera**: sigue
`blocked` por F-043 y T23/T24 son del humano, no se exigen aquí.

**Rigor `critico`** (declarado en `features.json`): fase RED, cobertura, mutación
con cero supervivientes y `MANUAL (humano)` con comando. La **mutación no se exige
aquí** (T23, encargo del líder): no es un N/A, es tarea abierta que bloquea el
cierre, no esta review. **Verificado por mí**: `bash harness/init.sh` → exit 0
(raíz `531 passed in 110,10s`; `PUERTA COBERTURA 97.8%`, 267/273); como los
servicios salían por caché los relancé en serie (sv6 `175 passed`, sv5 `18`, sv3
`117`); dos sondas sobre el builder real (scratchpad); `git status` limpio.

## Los ocho puntos
- **1 · La reversión de T11 NO quedó limpia → bloqueante 1.** El código de sv5 sí
  (sin `_hay_ler_en_linea`, sin import de `ruesma_comun.ler`, con el porqué en
  `valuation_extraction_service.py:320-328`) y R13, el design de sv5 y T11 dicen la
  verdad; pero tres documentos —dos de producción— aún describen la regla.
- **2 · El hallazgo de R19 y su arreglo son correctos.** Confirmado que el record
  base guarda los m³ crudos en `cantidad_albaran` (`valuation_builder.py:1297`) y
  los contenedores en `cantidad_convertida` (`:1172-1174`). El arreglo
  (`:1439-1465`) va condicionado a `tipo_familia=='residuos'` **del padre**: no
  regresa hormigón ni las M1/código, con test de no regresión (padre de hormigón
  → hereda 8.0). Sondas propias: 6 m³ → 1 UD → 171,00; 12 m³ → 2 UD → 342,00.
- **3 · T12 fiel a la decisión del 2026-08-19.** `residuos_container_calc.py:166+`
  anida la resta dentro del `if m3 is None or m3 <= 0`: el único camino a
  `residuos_sin_volumen_m3` es «ni volumen ni resta», literalmente R22. **Los seis
  nombres de `reasons` no cambiaron** (hay test que los congela), así que la
  inspección por prefijo de `valuation_builder.py:1274-1277` sigue casando.
- **4 · T9/T10 respetan R12 y no pisan al ganador.** `_completar_campos_objetivos`
  solo recorre los nueve, respeta lo que el ganador trae y lo devuelve intacto si
  no hay hueco; `ContextoLinea` tiene 14 campos = 5 + 9. El criterio de hueco
  acierta con `carga_incompleta` (`False` es dato, con test) y es **discutible en
  las seis medidas numéricas**: `volumen_m3=0.0` puntúa +1 y bloquea el relleno
  desde quien sí trae los 6 m³. Sin test → cambio 3.
- **5 · T14/T16/T17: forma C exacta, dedupe correcto, enganche real.**
  `dto_red_residuos` (`residuos_incrementos.py:138`) es el espejo de
  `_dto_red_codigo` (`valuation_builder.py:872`); R17 añade `RAZON_SIN_TARIFA` y
  revisión forzada (`:1629-1643`). El recorrido (`:814`) no conoce ninguna regla:
  itera `REGLAS_SINTETICAS_RESIDUOS` y deduplica por rol y `claves_dedupe(dto)`, y
  el test de la regla ficticia lo demuestra. **Sí es enganche para F-006** (aunque
  `claves_dedupe` es compartida: se edita en el mismo fichero, R21 a salvo).
- **6 · Confirmado: `ModifierContractMatcher` no está cableado.** `grep` propio:
  solo su fichero, su test, un comentario de `residuos_incrementos.py:61` y specs
  de F-003/F-004/F-006; no lo instancian `composition.py` ni `app.py` y nadie lee
  `settings.modifier_table_match_enabled`. **T19/R20 no afecta hoy a ninguna
  valoración**: el precio lo pone `tarifa_incremento_ler` (sonda: 90,00 € desde la
  línea 26481). De las siete tareas del bloque C, T19 no entrega efecto.
- **7 · T25 amplió la lista por la razón correcta, pero dejó un agujero.** El
  comentario de `tests/test_f027_r18_r22_contrato.py:196-204` cita al consumidor y
  lo verifiqué (sv6 solo escribe; sv4 pinta en crudo, sin lista blanca). **Pero**
  `_motivos_de` (`:62-80`) recoge del AST solo literales y
  `reasons.append(RAZON_SIN_TARIFA)` (`valuation_builder.py:1642`) es un `Name`:
  `residuos_ler_sin_tarifa_en_contrato` entró sin pasar la congelación → cambio 2.
- **8 · T21/T22 mide algo real; dos precondiciones y solo una declarada.** Usa el
  builder real (`construir_builder()`) y los totales del Excel del administrativo,
  no de las fixtures, fijando concepto, rol, `modifier_source` y padre. **La RED
  del worktree de `dev` es sólida**: su aritmética cuadra sola (9 rojos = 3 totales
  + 6 sintéticas; 10 verdes = 6 invariantes de 1 UD + 3 totales + precondición).
  **R25 tiene el criterio correcto** (invariante = TOTAL, y la sintética sin precio
  con `review_required` es lo QUERIDO por R16/R17), pero exige además de
  `tipo_familia` que **IA3 haya casado el CONTENEDOR**: con el match real de
  SS-0003967 y el `tipo_familia` puesto medí **90,00 € frente a los 210,00 de
  R25**. El §2 del informe lo mide; el §8, que es lo que lee el humano, no.

## Checkpoints
- **C1** [x] exit 0 y documentos obligatorios presentes. **C2** [x] ninguna
  `in_progress`, rama correcta, `current.md` de la sesión viva.
- **C3** [ ] arquitectura correcta, ruta en la primera línea de los ficheros
  nuevos, sin prints, secretos ni dependencias nuevas — **vacío por el
  bloqueante 1**. **C3 bis** N/A: el diff no toca `docs/referencia/`.
- **C4** [ ] R9-R22 y R25 con test trazable y en verde, ninguno toca red, BBDD ni
  LLM, T24 listada con su SQL en `tasks.md:56` — **vacío por el bloqueante 2**:
  R19 no se cumple en el camino sin contenedores y no hay test de él.
- **C4 bis** [x] parcial y acotado: rigor declarado; fase RED con trazas reales
  en los tres informes (worktree para T21/T22, `sitecustomize` para T25);
  cobertura `[OK]` 97,8 %; «Evidencias» en los tres. Mutación fuera de encargo.
- **C4 ter** [ ] la puerta salió `N/A` solo porque F-036 ya no es la feature en
  curso, pero el diff **sí** toca rutas sensibles (`prompts.yaml`,
  `residuos_container_calc.py`, `tipologia.py`, `valuation_builder.py`,
  `modifier_contract_matcher.py`) y falta `progress/evals_F-036.md`. Exigencia
  `aviso`; **motivo**: `evals.runner --con-llm` gasta LLM real (decisión del
  humano) y con los seis `_indice.json` vacíos daría NO_EVALUABLE.
- **C5** [ ] T23/T24 abiertas a propósito (feature sin cerrar), T11 como `[~]
  RETIRADA` con fecha y razón, un commit `F-036 Tn:` por tarea, árbol limpio y
  `features.json` en `blocked` con los seis servicios reales.
- **Trazabilidad**: R9-R12 → sv3 `test_f036_r9..r12_*`; R13 RETIRADO (sin test,
  correcto); R14 → `comun` (7) + sv2 (2); y en sv6 R15 (5), R16 (+prompt sv5), R17
  (4), R18 (3), R19 (4, **incompleto**), R20 (3, no cableado), R21 (8), R22 (11 +
  prompt sv5) y R25 (19).

## Bloqueantes
1. **Documentación viva de la regla retirada.** `ruesma_comun/ler.py:7-9` («sv5
   la usa en `_derivar_tipologia_valoracion` […] F-036 R13») y
   `services/albaranes-api/domain/models/tipologia.py:24-26` («sv5 también los
   necesita, regla dura de tipología de valoración») son falsos desde `7ca2ffc`:
   hoy los consumidores son sv2 y **sv6** (`modifier_contract_matcher.py:71`,
   `residuos_incrementos.py:54`), que es lo que sostiene R14 — y
   `requirements.md:71-72` sigue diciendo «consumido por sv2 y sv5».
2. **R19 se incumple cuando la base de residuos no tiene contenedores
   calculables.** En `valuation_builder.py:1455-1465` la herencia nueva solo
   actúa si `parent_record.cantidad_convertida is not None`; con
   `residuos_sin_volumen_m3` ese campo es `None` y cae al `elif` de
   `cantidad_albaran`. Medido con el builder real (fixture de SALMEDINA sin
   `volumen_m3` ni `contenedores`): la sintética `INCREMENTO LER 170802` sale con
   `cant_conv=6.0` e **importe 306,00** (total 1026,00), seis veces el recargo
   real: el defecto que corrigió el hallazgo de R19, por el otro camino y en la
   línea que estrena F-036. R19 no admite excepciones («nunca de los m³»).
   Arreglo: no inventar cantidad cuando el padre de residuos no la tiene (`None`
   o 1 UD), con su razón y su test. (Los 720 € que saca ahí la base son fallback
   preexistente de `importe_calculator`: no es regresión, pero que lo vea.)

## Cambios requeridos (antes de cerrar F-036; no levantan el rechazo)
1. **`es_linea_incremento_ler` confunde una fecha con un LER**: usa
   `normalizar_ler`, sin la defensa de forma-fecha que sí tiene y testea
   `texto_contiene_ler` (ejecutado: `"INCREMENTO TARIFA DESDE 01-01-25"` →
   `010125`). La guarda de R15 anularía el match de una base casada con una línea
   así, dejándola sin precio. Exigir espacios o el token `LER`.
2. **Tapar el agujero de la congelación de motivos** (punto 7): que `_motivos_de`
   resuelva constantes de módulo, o meter `residuos_ler_sin_tarifa_en_contrato`
   en `MOTIVOS_DEL_BUILDER` con la misma comprobación de consumidores.
3. **Separar el `bool` del cero numérico en `_tiene_valor`** (punto 4), con test.
4. **Declarar la SEGUNDA precondición de R25** (punto 8) en el resumen para el
   humano y en la docstring del escenario, no solo en el §2 del informe.
5. **`pytest` y `coverage` en el venv de sv4** son ya requisito de `init.sh`:
   documentarlo en el README de sv4 o añadir `requirements-dev.txt` (§8.5).
6. `test_f036_r9_son_exactamente_los_nueve_campos_del_requisito` repite la tupla
   en vez de contrastarla con `ContextoLinea`: no vería una décima medida.

## Automejora (propuesta, no aplicada)
C4 ter solo actúa «si la puerta de `init.sh` señaló rutas tocadas», y aquí salió
`N/A` porque la ficha pasó a `blocked`: el estado apagó una puerta de contenido.
Propongo que `harness.rutas_sensibles` acepte `--feature F-XXX` explícito y que
el checkpoint mande cotejar el diff a mano cuando salga ese `N/A`.
