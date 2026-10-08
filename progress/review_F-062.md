<!-- progress/review_F-062.md -->
Revisión completa (pasada 1) · `dev` `e7d7507` .. `132df3a`

# F-062 · review (reviewer)

**Veredicto: CHANGES_REQUESTED** (1 hallazgo ALTO y 1 MEDIO; el código es sólido en todo lo demás).

**Rigor:** `critico`, declarado en `harness/features.json`. Exige fase RED, cobertura ≥ 80 % de las líneas
cambiadas, mutación completa con 0 supervivientes y MANUAL listadas con comando exacto.

**Entorno:** worktree con los venvs del árbol principal y `PYTHONPATH` = comun del worktree (verificado:
`ruesma_comun.proveedores` se importa de `albaranes-F-062`). Sin `.env`, sigrid-api, Azure ni BBDD reales.
Controles negativos y diferenciales hechos sobre **copias** (`git archive HEAD`) en el scratchpad, nunca en el árbol;
el worktree termina limpio (`git status` y `git diff` vacíos). Nota: por descuido lancé en el árbol principal dos
órdenes git de solo lectura (`rev-parse`, `status`); no cambiaron nada.

## Hallazgos

**H1 · ALTA · «nombre completo» no se cumple: con score 1,0 se aplican nombres que no son el completo.**
R3 («defecto 1,0: todas las palabras del nombre»), Q3 aprobada por el humano («nombre completo (score 1,0)»), D2 del
design («con 0,5 "MAT" casaría con "MATERIALES"»: da a entender que 1,0 lo evita), ARCHITECTURE regla 17 y la propia
nota que lee el revisor («…con contrato en la obra 0720 y nombre completo») prometen un filtro que no existe.
`_score_razon_social` (simétrico y por subcadenas, `header_resolver_service.py:96-114`, heredado de F-052) da 1,0
cuando un nombre contiene al otro o cuando todas las palabras de ≥3 letras de **cualquiera de los dos** aparecen como
**subcadena** en el otro. Evidencia, resolver real de la rama, CIF leído `B86056201`, obra con un solo candidato
(CIF válido), resultado **APLICADO** («es el único candidato») en los cuatro:

| Nombre leído | Razón social del candidato |
|---|---|
| `Hormigones Mat SL` | `HORMIGONES MATERIALES, S.A.` |
| `Transportes` | `TRANSPORTES PEREZ GARCIA, S.L.` |
| `Grupo Hormigones Mat` | `HORMIGONES, S.A.` |
| `S.L.` | `ARIDOS ANFERSA, S.L.` |

Riesgo: el proveedor real no está entre los que tienen contrato en la obra (no dado de alta, sin contrato aún, o
el CIF leído es de otra empresa) y hay uno solo con nombre «parecido» ⇒ sv3 cambia el proveedor, encuentra **su**
contrato y la valoración sale con precios ajenos. Antes de F-062 se quedaba en `ninguno` con propuesta. El código
cumple la letra de la *Definición* («`score` de `_score_razon_social`»), pero no la de R3 ni lo que aprobó el humano.
Hace falta decisión del humano, una de dos:
- **A (recomendada).** Elegibilidad propia de la corrección más estricta que el score de la propuesta (p. ej. por
  palabras completas, sin formas jurídicas SL/SA/SLU, y en un sentido definido), con tests que dejen NO elegibles
  los cuatro casos de arriba y elegibles los tres medidos, SALMEDINA y el caso HORPRESOL si el humano lo quiere.
- **B.** El humano acepta la semántica actual: corregir R3, D2, ARCHITECTURE regla 17, dominio §10.1 y la frase
  «nombre completo» de la nota (`header_resolver_service.py:622-625`) para que digan lo que hace, y fijarlo con un test.
En ambos casos, conviene hacer **T0b** (Anexo A.1) antes de desplegar: es la única medición de esta regla con más
casos que los tres de la tabla.

**M1 · MEDIA · C4: las MANUAL no constan en `progress/current.md` con su comando exacto.** Solo dice
«Pendientes del humano: T0b (opcional) y T12». Los comandos están en `tasks.md` T12 e `impl_F-062.md` §7: copiarlos
a `current.md` (`.\deploy.ps1 -Only sv3`, `.\check_deploy.ps1` desde `infra/`, consulta A.3 y, para T0b, el script
`diag_f062.py` con la consulta A.1).

**B1 · BAJA · se aplica el CIF *normalizado*, no el literal de Sigrid** (`header_resolver_service.py:610`, R6). La
búsqueda de contratos compara `prv.cif = ?` (`sigrid_api_contrato_client.py:104`) y `fetch_proveedor_by_cif` solo
quita espacios (`:811`). Si un `prv.cif` lleva guion, punto o `ES`, el CIF aplicado no encuentra contratos y en la
siguiente pasada «no existe». Lo manda R6 y 6.2 no lo midió en `prv`; propuesta: escribir `candidato.cif.strip()`
(lo que escribe el desplegable de sv4) o medirlo en solo lectura. No bloquea.

**B2 · BAJA · desviación no declarada.** En la rama «sin candidato claro» con la corrección encendida,
`retirar_motivos_proveedor(cif_leído)` retira también `proveedor_cif_no_casa:<otro CIF>`, no solo correcciones
(impl §2.4 solo habla de R15). Inocuo (sv4 ya lo hace al guardar, F-036 R24), pero R10 dice «como hoy»: declararlo.

## Verificación propia (resultados reales)

- `bash harness/init.sh` en el worktree (con `PYTHONPATH`): exit 1, **2 KO, ambos de entorno**: sv3
  `test_f052_t19_script_arranca_como_script_desde_otra_carpeta` (quita `PYTHONPATH` y carga el comun de `dev`) y,
  por el `-x`, cobertura 59,6 %. Comprobado que es solo de entorno: el mismo script con el comun del worktree, desde
  otra carpeta, sale con rc=2 y «'12' no es un código de obra válido» (lo que pide el test). Raíz 1083 passed.
- sv3 con coverage deseleccionando solo ese test: **544 passed**; `python -m harness.cobertura --base dev --config
  harness/rigor.json`: **100,0 % de 203 líneas (203/203)**. comun completo: **417 passed, 3 skipped** (117,8 s).
- **CIF/NIF/NIE** contra una implementación de referencia propia (algoritmo oficial): los 5 reales correctos
  (B86056201, B86056095, B18437421 inválidos; B66056201, B18487421 válidos; controles esperados 7, 0 y 6), NIF,
  NIE X/Y/Z, letra en P/Q, dígito en A, K/L/M, prefijo ES, extranjero; **0 diferencias en 300.000 aleatorios**.
- **R12 diferencial**: resolver de `dev` frente al de la rama con `correccion_enabled=False`, 2.268 escenarios (CIF
  existe/no/falla, obra, nombre, 7 listas, consulta caída, origen ia/manual): **0 diferencias** en las llamadas al
  repositorio (notas y motivos incluidos) y a sigrid-api. Además, los tests de `dev` de F-002/F-052 sin tocar, con
  el defecto a `False`: 420 passed (con `True` también pasan, porque sus dobles no tienen `aplicar_…`: no prueban R12).
- **Controles negativos (13, copia, restaurados en bytes)**, fallos que provocan: aplicar sin candidato claro 25 ·
  empate sin margen 7 · CIF del candidato sin validar 7 · interruptor ignorado 7 · origen `manual` ignorado 2 · CIF
  existente tratado como inexistente (R13) 8 · nota con prefijo `[AVISO] Proveedor` (D6, re-pasada) 5 · R15 sin
  retirar la nota 1 · aplicar sin `review_required` 1 · ruta duplicado sin resolver antes de contratos (R8) 3 ·
  comun: N/P/Q/R/S/W con dígito 2 · NIE X/Y cambiados 3 · CIF doblando las posiciones pares 26.
- **Orden (R8)** leído en el código: resolver antes de contratos en nuevo (`:216→221`), duplicado (`:130→137`) y
  `reenrich_by_merge_id` (`:424→429`); `update_merge_resolved_header` no pisa lo aplicado (`proveedor_cif_det=None`).
- **Revisor (R13)**: el desplegable de sv4 escribe `prv.cif` de proveedores con contrato en la obra
  (`sigrid_lookup_client.py:27-37`) y `fetch_proveedor_by_cif` lo encuentra ⇒ nunca entra a corregir; guarda `manual`.
- **Nota `[CORREGIDO] Proveedor`**: `_remove_nota_proveedor_safely` filtra por `startswith("[AVISO] Proveedor")`
  (líneas), no la toca; sustitución por prefijo propio en la misma transacción.
- **`.env.example`**: solo los tres `RED_PROVEEDOR_CORRECCION_*` con sus defectos; sin valores reales. Barrido del
  diff (correos, IPs, GUID, password/secret/token/key, cadenas de conexión, originales ofimáticos): **0 coincidencias**.
- `azure-apps/albaranes.md` no documenta las variables de la red (grep vacío): no se toca, conforme.

## Mutación (C4 bis)

- Totales **recalculados** con `harness.alcance` + `generar_mutantes`: 9 ficheros, **612 líneas, 104 mutantes**
  en HEAD y en `f3d4174`: coinciden con el informe. Sin «CAMPAÑA NO VÁLIDA», 0 sin veredicto, línea base corrida.
- **RM1**: SHA medido `f3d4174…`; después solo cambian tests y `progress/`: alcance idéntico.
- **RM2**: 1227,7 s, 1 worker, media 11,8 s; bases comun 133,7 / sv3 11,0. **RM4**: un mutante de comun
  (`suma = 0`→`1`) aplicado en copia muere con `-x` en 11 s (25 passed, 1 failed): la media cuadra.
- **Campaña no reejecutada: 20,5 min según el informe** (> 60 s): recálculo puro + RM1–RM6.
- **RM3**: repasados los 104 mutantes uno a uno; ninguno equivalente sale muerto (los de logs los caza `caplog`).
- RM5: N/A (0 supervivientes; los 3 equivalentes de la 1.ª campaña se eliminaron reescribiendo
  `depurar_motivos_proveedor`, misma semántica, comprobado). RM6: N/A (no se quitó ninguna guarda).

## Checkpoints

- C1 init.sh exit 0: **[ ] en el worktree, KO solo de entorno (verificado arriba)**; la definitiva es la del árbol
  principal tras fusionar (líder). Ficheros del arnés: [x].
- C2: [x] una `in_progress` · [x] rama `feature/F-062-proveedor-aplicado` · [x] current.md al día · [x] history.
- C3: [x] hexagonal (constantes en dominio; aplicación importa `ruesma_comun`) · [x] primera línea con ruta ·
  [x] sin prints/secretos/dependencias nuevas · [x] trampas: solo merge, sin DDL, sin importes.
- C3 bis: N/A — solo se edita un documento existente (`dominio_negocio_albaranes.md` §10.1); barrido hecho igual.
- C4: [x] cada R1–R16 con tests `test_f062_rN_*` en verde · [x] sin red ni BBDD · **[ ] MANUAL sin comando en
  current.md (M1)**.
- C4 bis: [x] rigor · [x] fase RED con trazas (T1, T3–T6; T7/T9 rompiendo y restaurando) · [x] cobertura 100 % ·
  [x] mutación verificada · [x] RM1 · [x] RM2 · RM5/RM6 N/A justificados · [x] 0 supervivientes · [x] Evidencias
  con los cuatro números y workers.
- C4 ter: N/A (init: «F-062 no toca ninguna ruta sensible declarada»).
- C5: [x] commits por tarea T1–T11 · T0b/T12 MANUAL del humano y T13 (init en el árbol principal) pendientes,
  justificados · [x] sin temporales · [x] `features.json` coherente.

## Cobertura (requisito → tests)

R1–R2 `test_f062_identificador_fiscal.py` (88) · R3–R5 `test_f062_r3_*` · R6, R7, R9, R12, R13 `test_f062_r6_*`
(+ `r14 … repo_aplica …`) · R8 `test_f062_r8_*` (tres rutas × tres casos y la vuelta atrás) · R10–R11
`test_f062_r10_*` · R14–R16 `test_f062_r14_*` (puros, repositorio y re-pasadas).

## Cambios requeridos

1. **H1**: que el humano elija A o B; implementar la elegida (A: elegibilidad estricta + tests con los cuatro
   contraejemplos; B: corregir R3, D2, ARCHITECTURE 17, dominio §10.1 y la frase de la nota, con test que lo fije).
2. **M1**: comandos exactos de T0b y T12 en `progress/current.md`.
3. (Recomendado) B1 y B2 según lo dicho arriba.

## Automejora (propuesta, no aplicada)

`reviewer.md`: cuando una feature reutiliza una función de puntuación para una decisión más arriesgada que la
original (proponer → aplicar), exigir en la spec una tabla de contraejemplos ejecutada contra esa función.
