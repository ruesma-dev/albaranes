<!-- progress/impl_F-062.md -->
# F-062 · informe del implementer

sv3 aplica el proveedor propuesto antes de buscar contratos · rigor `critico` · servicios sv3 y comun.
Rama `feature/F-062-proveedor-aplicado` (worktree `../albaranes-F-062`, desde `dev` `e7d7507`). Un commit por
tarea (`F-062 T1`…`T11`), sin push. Spec: `specs/F-062-proveedor-aplicado/`; datos y Q0–Q6: `progress/spec_F-062.md`.

## 1. Qué cambió

| Fichero | Cambio |
|---|---|
| `albaranes-comun/ruesma_comun/proveedores/{__init__,identificador}.py` (nuevo) | `normalizar_cif` (R1) e `identificador_fiscal_valido` (R2): CIF con control por tipo de letra, NIF, NIE, NIF especial K/L/M |
| sv3 `domain/models/header_resolution_models.py` | `proveedor_cif_origen` en la cabecera (R13) y constantes de motivos y del prefijo `[CORREGIDO] Proveedor` |
| sv3 `domain/ports/header_resolver_ports.py` | `aplicar_correccion_proveedor`, `retirar_motivos_proveedor` |
| sv3 `infrastructure/database/sqlalchemy_albaran_repository.py` | las dos escrituras (una transacción cada una), `depurar_motivos_proveedor` (pura) y el origen en `get_merge_header_for_resolution` |
| sv3 `application/services/header_resolver_service.py` | `_candidatos_puntuados` (una consulta por pasada), `_mejor_de`, `_distancia_edicion`, `_candidato_claro`, `_aplicar_candidato_claro`, `_retirar_motivos_safely`; la red aplica, retira caducados y añade la frase del control (R11) |
| sv3 `config/settings.py`, `interface_adapters/composition.py`, `interface_adapters/api/app.py` | `RED_PROVEEDOR_CORRECCION_ENABLED` (true), `…_SCORE_MIN` (1.0), `…_MARGEN_DISTANCIA` (2), cableados en los dos puntos de composición |
| sv3 `.env.example` | los tres nuevos, documentados |
| sv3 `tests/doble_sigrid_api.py` | fixture `fixture_f062` (obras 0720 y 0678), sin tocar el de F-052 |
| sv3 `tests/f062_dobles.py` (nuevo) + 5 `test_f062_*.py`; comun `test_f062_identificador_fiscal.py` | tests de R1–R16 |
| sv3 `tests/test_f002_red_proveedor.py`, `tests/test_f052_nota_proveedor.py` | los que afirman D3 van con `correccion_enabled=False` (R12) |
| `docs/ARCHITECTURE.md` (regla 17), `docs/referencia/dominio_negocio_albaranes.md` §10.1, `specs/F-002-obra-proveedor/design.md` D3 | T10 |
| `progress/mutacion_F-062.md`, fila en `progress/inventario_mutacion_F-039.md` | T11 (la exige `test_f039_r2`) |

Sin DDL, sin SQL nueva contra Sigrid, sin tocar sv4 ni el pipeline (R8 se cumple por orden: el resolver ya corría
antes que los contratos en las tres rutas). `azure-apps/albaranes.md` no describe la red (grep: 0 menciones de
`RED_PROVEEDOR`/`HEADER_RESOLVER`): no se toca.

## 2. Decisiones y desviaciones (justificadas)

1. **Nota de la corrección** (R7, formato del líder): `[CORREGIDO] Proveedor: leído B86056201 → B66056201 (HORMIGONES
   MAT, S.L.U.). Nombre leído: 'Hormigones Mat SL'. El CIF leído no existe en Sigrid y el carácter de control del CIF
   leído no es válido (lectura errónea); se aplica porque es el candidato con el CIF más cercano al leído con contrato
   en la obra 0720 y nombre completo. Si no es el proveedor, cámbialo con «Elegir proveedor».` Motivo:
   `proveedor_cif_corregido:<leído>><aplicado>` (leído tal cual, aplicado normalizado).
2. **Frase de R11 al FINAL de la nota `[AVISO]`**: las consultas A.1/A.2 del humano buscan el literal «no existe en
   Sigrid. PROPUESTA:»; meterla en medio las habría roto (test `r11_la_frase_no_rompe_la_consulta_de_vigilancia`).
3. **R12 «exactamente como antes»**: con el interruptor apagado no se aplica, no se retira ningún motivo y no se añade
   la frase del control. Los motivos `proveedor_cif_corregido` de cuando estaba encendido se quedan (informan).
4. **R15 también sin candidato claro** (desviación menor del design §5.3, que solo retiraba en «existe» y al aplicar):
   R15 es incondicional, así que en la rama «sin candidato claro» se llama a `retirar_motivos_proveedor(cif_leído)`
   antes de marcar. Caso casi inalcanzable (sv4 solo escribe `prv.cif`), pero el requisito lo pide.
5. **Si aplicar falla** (BBDD), se marca como hoy (`proveedor_cif_no_casa` + propuesta): best-effort, nunca rompe.
6. **Sin candidato claro, la propuesta es la de F-052** (el primero con mejor nombre), aunque el claro fuera otro (p.
   ej. origen `manual`): design §5.3 «con el mismo `mejor`».
7. **Tests de F-052 con el interruptor apagado** (desviación del design §4, que solo nombraba F-002):
   `test_f052_nota_proveedor.py` prueba la nota de D3, y SALMEDINA (B82899550, 0691) es candidato claro; con la
   corrección encendida esos tests pasaban por el camino «aplicar falla» (su doble no tiene `aplicar_…`), lo que era
   probar otra cosa. La aplicación de ese mismo caso la prueba `test_f062_r6_el_caso_salmedina_de_f052_ahora_se_aplica`.
   En F-002, `r9_no_sobrescribe…` pasa a usar un candidato con CIF **válido** (B66056201): con el antiguo (inválido)
   el test no distinguía el interruptor.
8. **`depurar_motivos_proveedor` sin contador ni `rsplit`** (T11): 3 supervivientes equivalentes de la 1.ª campaña
   (`retirados += 1` usado solo como booleano; `rsplit(">", 1)[-1]` ≡ `rsplit(">", 2)[-1]`) → `len(vivos) ==
   len(motivos)` y `rpartition(">")[2]`, misma semántica. No se quitó ninguna guarda (RM6 N/A).
9. **Versión de comun**: no se sube (`0.7.0`); ningún servicio fija versión de comun (se instala del árbol).

## 3. Fase RED (trazas reales, comandos desde la raíz del servicio, `PYTHONPATH` = comun del worktree)

**T1 · R1, R2** (comun) — `python -m pytest tests/test_f062_identificador_fiscal.py -q`
```
tests\test_f062_identificador_fiscal.py:13: in <module>
    from ruesma_comun.proveedores import (
E   ModuleNotFoundError: No module named 'ruesma_comun.proveedores'
1 error in 0.42s                      → GREEN: 88 passed in 0.27s
```
**T3 · R14–R16 repositorio** — `python -m pytest tests/test_f062_r14_repasadas_y_motivos.py -q -k "puro or repo"`
```
E   ImportError: cannot import name 'depurar_motivos_proveedor' from 'infrastructure.database.sqlalchemy_albaran_repository'
1 error in 2.80s                      → GREEN: 16 passed in 1.98s
```
**T4** — `python -m pytest tests/test_f062_r3_candidato_claro.py -q`
```
E       AttributeError: 'HeaderResolverService' object has no attribute '_candidatos_puntuados'
7 failed in 0.41s                     → GREEN: 7 passed; F-002 + F-052 sin cambios: 93 passed
```
**T5 · R3–R5** — mismo comando, con `_distancia_edicion` ya escrita y sin `_candidato_claro`:
```
E       AttributeError: 'HeaderResolverService' object has no attribute '_candidato_claro'
FAILED ...::test_f062_r4_empate_desempatado_por_el_cif_mas_cercano
FAILED ...::test_f062_r3_un_candidato_con_el_control_invalido_no_es_elegible
FAILED ...::test_f062_r5_el_control_del_leido_no_cambia_la_regla[control-invalido|control-valido]
FAILED ...::test_f062_r4_los_tres_casos_medidos_tienen_candidato_claro[19407|19394|1790636816]
19 failed, 19 passed in 0.90s         → GREEN: 38 passed in 0.44s
```
**T6 · R6, R7, R9, R11** — `python -m pytest tests/test_f062_r6_aplica_candidato.py tests/test_f062_r10_sin_candidato_claro.py -q`
```
E       ValueError: not enough values to unpack (expected 1, got 0)      ← [aplicada] = repo.aplicadas: hoy no se aplica
E       assert False
E        +  where False = <built-in method endswith ...>('El carácter de control del CIF leído B86056201 no es válido: es una lectura errónea.')
E        +    where ... = "[AVISO] Proveedor el CIF leido B86056201 no existe en Sigrid y ninguno de los 0 proveedores con
              contrato en la obra 0720 casa con el nombre leído ('Hormigones Mat SL'). Revisa el proveedor en el portal.".endswith
FAILED ...::test_f062_r6_aplica_cif_y_razon_social_de_sigrid[19407|19394|1790636816]
FAILED ...::test_f062_r7_motivo_y_nota_de_la_correccion[19407|19394|1790636816]
FAILED ...::test_f062_r11_control_invalido_se_anade_a_la_nota[sin-propuesta|con-propuesta|consulta-fallida]
15 failed, 19 passed in 2.40s         → GREEN: 41 passed (con settings y cableado)
```
(2 de los 15 KO, `r13_origen_manual` y `r6_si_aplicar_falla`, eran del propio test: esperaban como propuesta a
HORMIGONES MAT y la de F-052 es la primera con mejor nombre, A28123453; se pasaron al caso 1790636816.)

**T7 · R15, R16** y **T9 · R8**: el código lo trajo T6 (T7) o no cambia (T9, pipeline); su RED se midió rompiendo a
propósito el código vigilado con los tests ya escritos y restaurando con `git checkout --` (git diff vacío, sha256
`8c9bd260f116999d` igual antes y después):
```
T7 (sin retirar en «existe en prv»): E  AssertionError: assert ['proveedor_c...01>B66056201'] == []
  FAILED ...::test_f062_r15_el_revisor_elige_otro_y_se_retira_la_correccion
  FAILED ...::test_f062_r16_cif_existente_retira_no_casa_de_otro_cif          2 failed, 22 passed
T7 (sin retirar en «sin candidato»): FAILED ...::test_f062_r15_tambien_sin_candidato_claro_se_retira_la_correccion_caducada
T9 (resolver con correccion_enabled=False por defecto, es decir, lo de antes de F-062):
  python -m pytest tests/test_f062_r8_pipeline_tres_casos.py -q -k "acaba_en_encontrados"
  E       assert (False, 0) == (False, 1)        ← contratos_count 0: la búsqueda usó el CIF leído
  FAILED ...::test_f062_r8_{albaran_nuevo,duplicado,reenrich_desde_sv4}_acaba_en_encontrados[19407|19394|1790636816]
  9 failed, 7 deselected in 2.38s      → GREEN: 16 passed
```

## 4. Controles negativos a mano (restaurados en bytes: `git diff --quiet` y sha256 iguales)

| Control (cambio aplicado al código) | Resultado |
|---|---|
| Aplicar sin candidato claro (el mejor por nombre siempre vale) | 16 failed (todos los de R10/R11) |
| Empate sin margen (`if segunda - primera >= margen` → `if True`) | 6 failed (R4 margen, R10 empate 0720) |
| Control del CIF del candidato ignorado (sin `identificador_fiscal_valido`) | 6 failed (R3 control inválido, extranjero, R10) |
| Interruptor ignorado (`_correccion_enabled = True`) | 6 failed (R12, F-002 D3, R8 con corrección apagada) |
| Nota con prefijo de aviso (`"[AVISO] Proveedor corregido"`) | 2 failed (R14: la nota no sobrevive a la re-pasada) |
| Origen `manual` ignorado | 2 failed (R13, R15) |
| Orden antes de la búsqueda de contratos | ver T9 arriba: 9 failed |
| comun: `(10 - suma % 10) % 10` → sin `% 10` / `A B E H` aceptan letra / sin sumar cifras del doble | 5 / 4 / 25 failed de 88 |

(comun: el fichero se había escrito con LF y `git checkout --` lo dejó en CRLF por `core.autocrlf`; contenido igual,
`git diff` vacío.)

## 5. Tests (resultado real, 2026-10-08)

- comun: **417 passed, 3 skipped** in 121.39 s (88 nuevos).
- sv3: **544 passed, 1 failed** (14.48 s con coverage, tras T11) → el KO es de entorno (§6).
- raíz: **1083 passed** in 163.97 s.

## 6. `bash harness/init.sh`

Ejecutado en el worktree el 2026-10-08 con `PYTHONPATH` al comun del worktree (entorno del líder), sobre `114b124`:
```
[OK] features.json válido · [OK] BACKLOG.md al día · [OK] compileall · [AVISO] ruff: 1190 avisos (dev: 1181)
1083 passed in 175.23s → [OK] pytest en verde (con medición de cobertura)              (raíz)
[OK] sv1, sv2, sv4, sv5, sv6 (caché) · 417 passed, 3 skipped → [OK] servicio comun
FAILED tests/test_f052_t19_supervivientes.py::test_f052_t19_script_arranca_como_script_desde_otra_carpeta
1 failed, 394 passed in 16.24s → [KO] servicio sv3-persistencia: pytest en rojo
[KO] PUERTA COBERTURA: 59.6% de 203 líneas cambiadas cubiertas (121/203, umbral 80%, nivel critico)
[OK] PUERTA RUTAS SENSIBLES: N/A · [OK] PUERTA TAMAÑO (requirements 124/150, design 184/250, impl 178/220)
2 comprobaciones fallidas.
```
**Los dos KO son del entorno del worktree, no del código:**
1. **sv3**: ese test lanza `scripts/verificar_f052_proveedores_obra.py` en un subproceso **quitando `PYTHONPATH`** a
   propósito; el venv del árbol principal trae `ruesma_comun` instalado en editable desde `../albaranes` (en `dev`, sin
   `proveedores`) ⇒ `ModuleNotFoundError: No module named 'ruesma_comun.proveedores'`. En el árbol principal, con
   comun fusionado, el editable ya apunta a un comun con `proveedores` y el test pasa.
2. **Cobertura**: consecuencia de 1. La suite corre con `-x` y ese test va antes alfabéticamente que los
   `test_f062_*`, así que el `coverage.json` de sv3 se queda a medias.

Contraprueba (misma orden, deseleccionando SOLO ese test con `PYTEST_ADDOPTS="--deselect …"`): `544 passed, 1
deselected` → `[OK] servicio sv3-persistencia`, `[OK] PUERTA COBERTURA: 100.0% de 203 líneas cambiadas cubiertas
(203/203, umbral 80%, nivel critico)` y **`ENTORNO LISTO. Puedes trabajar.`** Después se borró
`.arnes_cache/suite_sv3-persistencia.ok` para que un `init.sh` posterior no dé sv3 por verde con esa deselección.
Una ejecución anterior también falló en la raíz (`test_f039_r2_todo_informe_de_mutacion_figura_en_el_inventario`): el
informe de mutación nuevo no tenía fila en `progress/inventario_mutacion_F-039.md`; añadida (`114b124`).
**Para cerrar**: repetir `bash harness/init.sh` tal cual en el árbol principal tras fusionar en `dev` (líder/humano).

## 7. MANUAL pendientes (humano)

- **T0b** (recomendable): Anexo A.1 de `progress/spec_F-062.md` (qué hizo el revisor con las PROPUESTAS de hoy) para
  contrastar R3–R4 con más casos. Script `diag_f062.py` del scratchpad del líder; resultado en `spec_F-062.md` §2.
- **T12** (tras fusionar en `dev` y desplegar SOLO sv3), desde `infra/`: `.\deploy.ps1 -Only sv3` y
  `.\check_deploy.ps1`; después, unos días, la consulta A.3 de `progress/spec_F-062.md` y revisar en sv4 cada
  documento con `proveedor_cif_corregido`: CIF aplicado = proveedor real y contrato encontrado. Un caso mal aplicado ⇒
  `RED_PROVEEDOR_CORRECCION_ENABLED=false` (secret/env de la Container App de sv3) y volver a la spec. No bloquea el
  `done`.
- Cierre de F-030 como absorbida (Q5): proponerlo al humano al cerrar F-062.

## 8. Fuera de alcance (spec) y lo que falta

Fuera: normalización única del CIF y SQL normalizada, reintento tras `error`, CIF existente sin contrato en la obra con
homónimo (Q2), que IA2 elija proveedor (F-055), etiquetas de motivos (F-059), que sv4 marque `manual`, backfill.
Falta: review contra `CHECKPOINTS.md` y T12 (MANUAL). No quedan supervivientes que aceptar (§9).

## 9. Evidencias

| Evidencia | Valor real |
|---|---|
| Tests ejecutados | comun 417 passed + 3 skipped (121 s); sv3 544 passed + 1 KO de entorno (§6) (14 s con coverage); raíz 1083 passed (164 s). F-062 añade 88 (comun) + 124 (sv3) tests |
| Cobertura de las líneas cambiadas | `PUERTA COBERTURA: 100.0% de 203 líneas cambiadas cubiertas (203/203, umbral 80%, nivel critico)` |
| Mutación | `progress/mutacion_F-062.md`: **104 generados, 104 muertos, 0 supervivientes**, 0 timeouts, 0 sin veredicto; campaña completa, **workers 1** (en serie), 1227.7 s, media 11.8 s/mutante, base comun 133.7 s / sv3 11.0 s, SHA `f3d4174` (después solo se commitearon el informe y `tasks.md`: el código medido es el de HEAD) |
| Tiempo de la suite | sv3 8–15 s; comun 113–124 s (92 s son el `setup` de `test_humo_colas`); raíz 164 s |

**Campaña 1** (SHA `54e09a5`, 108 mutantes, 101 muertos, **7 supervivientes**, 1111.8 s; informe archivado fuera de git):
4 los matan tests nuevos de T11 (`t4_con_umbral_cero…` ← `mejor_score > 0.0`→`>= 0.0`; `t4_el_log_de_nadie_casa…` ←
`== MOTIVO_NADIE_CASA`→`!=`; `r16_puro_escribe_el_json_con_el_formato…` ← `ensure_ascii` y `indent`), comprobado
aplicando cada mutante a mano (1 KO nuevo cada uno). 3 eran **equivalentes** (`retirados += 1`→`-= 1`/`+= 2`, contador
usado solo como booleano; `rsplit(">", 1)[-1]`→`rsplit(">", 2)[-1]`, idénticos: `'a>b>c'.rsplit('>', n)[-1] == 'c'`
para n = 1, 2, 3) y se reescribió el código para que no existan (§2.8). La campaña 2 es la válida.

**Entorno de la campaña** (para el reviewer): en serie (`--workers 1`) porque el venv del árbol principal tiene comun
instalado en editable desde `../albaranes`: en worktrees de mutación, `PYTHONPATH` haría importar el comun del
worktree de F-062, no el mutado. Con `PYTEST_ADDOPTS="--deselect tests/test_f052_t19_supervivientes.py::test_f052_t19_script_arranca_como_script_desde_otra_carpeta"`
para que la línea base de sv3 no salga roja por el KO de entorno de §6 (ese test no ejerce código de F-062: lanza el
script de F-052 sin `PYTHONPATH`). Comando:
`PYTHONPATH=<worktree>/services/albaranes-comun PYTEST_ADDOPTS=… python -m harness.mutacion --feature F-062 --workers 1`.
