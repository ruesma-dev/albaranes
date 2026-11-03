<!-- progress/review_F-111.md -->
Revisión completa (pasada 1) · `dev...178a29c` (base de rama `8d5b702`)

# F-111 · review

**Veredicto: APPROVED**

Fuera de esta revisión por encargo del líder: **T13** (MANUAL, después de desplegar y revalorar, solo lectura). Que siga
`[ ]` en `tasks.md` es lo esperado y no bloquea esta review. Sí bloquea el `done`, igual que las condiciones C1 y C2
de abajo.

## Nivel de rigor

`critico`, declarado en `harness/features.json`. Exige fase RED con salida real, puerta de cobertura y campaña de
mutación completa. Además, **cero supervivientes salvo justificación escrita aceptada por el humano**, RM5 (reproducir
un equivalente) y las MANUAL listadas.

## Verificación ejecutada por el reviewer

- `bash harness/init.sh` en el worktree, con `PYTHONPATH=<worktree>\services\albaranes-comun` y `ARNES_SIN_CACHE=1`:
  **EXIT 0, «ENTORNO LISTO»**. Todo passed: raíz 1919, sv1 236, sv2 496, sv3 1608, sv4 2562, sv5 148, sv6 627
  (+1 skipped), sv9 1186 y comun 1424. Puertas:
  - `PUERTA COBERTURA [OK] 99,7 %` (397/398).
  - `PUERTA TAMAÑO [OK]`.
  - `RUTAS SENSIBLES [evals]` en **AVISO** (7 rutas; ver C4 ter).
  - `git status` limpio después.
- **Recálculo independiente de la mutación** (`alcance_de_feature("F-111")` + `generar_mutantes`, cálculo puro, script
  en el scratchpad): **17 ficheros, 1016 líneas, 113 mutantes**, lo mismo que el informe, fichero a fichero. Los 3
  supervivientes existen como mutantes reales, con el mismo operador y el mismo texto:
  - `partida_residuos_service.py:124` y `:126`, `indent=2→3`;
  - `partida_residuos.py:271`, `split(":", 1)[0]→split(":", 2)[0]`.
- **Campaña no reejecutada: 1300,6 s (21,7 min) según el informe**, por encima del umbral de 60 s. Me quedo en el
  recálculo puro y RM1–RM6.
- Repaso de los 113 mutantes en busca de equivalentes que salgan como muertos (RM3): ninguno.
  - Los candidatos dudosos cambian el comportamiento observable y tienen un test que lo fija: `ensure_ascii=True`
    (tildes), el `+` del log (caplog), `deep=False` (el sobre original intacto), `max(2, …)` (`intentos=1`), `[:201]`
    (cuerpo de 200 caracteres) y `_DECIMALES_M3=3` (6,004 m³).
  - `isinstance` negado en `partida_residuos_service.py:75` deja de convertir un modelo ajeno, que entonces falla.
- **RM5, muestra de UNO**: `split(":", 1)[0]` frente a `split(":", 2)[0]`. Ejecutado con los 4 formatos de motivo
  reales (sin `:`, con lista, con `(+N)` y con códigos con puntos): **iguales en todos**. Es equivalente por definición:
  el elemento `[0]` es el prefijo anterior al primer separador para cualquier `maxsplit ≥ 1`.
- Lectura del diff completo de código (sv6, sv5 y comun), de los prompts y de los tests viejos retocados. También el
  commit `ab78985` de `azure-apps` (§15 de `albaranes.md`).

## Checkpoints

**C1** [x] init.sh exit 0 · [x] ficheros del arnés presentes.

**C2** [x] una sola `in_progress` (F-111) · [x] rama `feature/F-111-residuos-contenedores-y-partida` · [x]
`current.md` con la sesión activa · [x] las `done` tienen su resumen (lo valida init.sh).

**C3**
- [x] Hexagonal: `EligePartidaPort` en dominio (Protocol, sin infraestructura); el cliente httpx en
  `infrastructure/clients`; el asignador y el cálculo en `application`, sin I/O; el cableado en `composition`.
- [x] Primera línea con la ruta en los 12 `.py` nuevos.
- [x] Sin `print`, `TODO` ni secretos. La clave de sigrid-api vive solo en la clave en memoria de `_PUERTOS_COMPARTIDOS`
  y nunca va al log.
- [x] Sin dependencias nuevas: httpx y tenacity ya estaban.
- [x] Reglas de dominio:
  - el valorado sale del sobre (merge), no de las raw;
  - sin DDL ni lectores nuevos;
  - la unidad no cambia: solo cambia la cantidad de contenedores, con el precio de la casada;
  - las sintéticas LER heredan la partida asignada (R24);
  - regla 27 nueva en `ARCHITECTURE.md` y excepción de residuos en la regla 16.

**C3 bis** N/A: no toca `docs/referencia/`.

**C4**
- [x] Cada requisito tiene test (tabla abajo) y todos pasan.
- [x] Unit tests sin red ni BBDD: `httpx.MockTransport`, elector y puertos falsos, stub de FastAPI.
- [x] MANUAL listada: T13 en `tasks.md`, en `current.md` y en el informe §6, con el método en `spec_F-111.md` §2.
  Ver O1.

**C4 bis**
- [x] `rigor` declarado (`critico`).
- [x] Fase RED con salida real de T1 y T3–T10, más el cableado de T10 (§3 del informe).
- [x] Cobertura 99,7 %.
- [x] `mutacion_F-111.md` generado por la herramienta, con los totales recalculados.
- [x] Muertos: campaña de más de 60 s, así que recálculo + RM1–RM6 (dicho arriba).
- [x] Coste por mutante = 1300,6 × 4 ÷ 113 = 46 s, muy por encima de 1 s.
- [x] Sin «⚠ CAMPAÑA NO VÁLIDA»; «Sin veredicto» = 0.
- [x] RM1: SHA medido `cf249a2`. Desde entonces (`cf249a2..178a29c`) solo cambian `progress/` y `tasks.md`, nada del
  alcance.
- [x] RM2: media 11,5 s × 4 workers = 46 s por mutante, frente a líneas base de 27,8 s (sv6), 37 s (sv5) y 114 s
  (comun). Coherente: la mayoría de los mutantes son de sv6 y mueren con `-x`. 113 × 11,5 = 1300 s, igual que el
  total.
- [x] RM5: reproducido 1 de 3 (arriba).
- [x] RM6: las dos guardas quitadas no eran defensa. `tramos and` sobra porque `str.split` nunca devuelve una lista
  vacía (comprobado: `"".split(" › ") == ['']`). `_alm` era un atributo sin lectores: `ALM` no está vacía y
  `normalizar_partida` ya la excluye de la búsqueda (R28, con su test).
- N/A campaña manual: la automática dio 113.
- [x] Los 3 supervivientes tienen su análisis completo, ninguno `PENDIENTE`. En `critico` falta la **aceptación
  escrita del humano** de los 3 equivalentes: es la condición C1 de abajo.
- [x] «Evidencias» con los cuatro números y los workers (4).
- [x] Ningún N/A sin motivo.

**C4 ter** [x] con motivo escrito (exigencia `aviso`). La puerta señala 7 rutas sensibles tocadas (prompts YAML,
schemas e IA de sv5, red de sv6) y no hay `progress/evals_F-111.md`. Motivos:
- (1) **D8 = (a)**, decidida por el humano en la PARADA 1: sin caso nuevo en el banco. El número de contenedores es
  determinista en sv6 y tiene test unitario; el prompt se prueba por texto (R12–R16, R32).
- (2) Los fixtures de `evals/fixtures/` siguen vacíos: la pasada daría NO_EVALUABLE.
- (3) La pasada `--con-llm` cuesta dinero y la decide el humano.

No bloquea: es un `aviso`.

**C5** [x] T0–T12 y T14 `[x]`, con su commit `F-111 Tn:`. T13 es MANUAL y queda fuera de esta review. · [x] sin
temporales sin trackear en el worktree. · [x] `features.json` en `in_progress`, que es el estado real.

## Cobertura requisito → test

| Req. | Test(s) |
|---|---|
| R1–R9, R11 | sv6 `test_f111_tamano.py`: bordes de 3/6/9 (0,5…9,01), paquetes de 6 >9, [6,8] y [8], fuentes de R8, R9 en el builder, 4839 B = 1 × 139, hormigón sin cambios |
| R10 | `test_f111_tamano.py` (r10) + `test_f036_r22_contenedores_prioridades.py` (el de 7 m³ reescrito a 1 × 9, declarado) |
| R12–R14, R16 | sv5 `test_f111_prompt_residuos.py`, sobre el YAML real |
| R15 | `test_f036_r22_prompt_residuos_orden.py` y `test_f036_r16_prompt_residuos_sinteticas.py`, sin tocar y en verde |
| R17–R19 | comun `test_f111_candidatas_residuos.py` (0686, 0694, 0711 «RESIDUAL», ajustes y `None`) |
| R20–R30, R35 | sv6 `test_f111_partida_residuos.py` y `test_f111_pipeline.py` |
| R31–R33 | sv5 `test_f111_partida_residuos.py` (fuera de candidatas ⇒ null; sin proveedor ⇒ 503) |
| R33–R34 | sv6 `test_f111_cliente.py` (una llamada, reintentos 5xx, 4xx sin reintento) |
| R36 | lectura: `docs/ARCHITECTURE.md` regla 27 y regla 16 |

## Condiciones para el `done` (no son cambios al código)

1. **C1 · el humano acepta por escrito los 3 equivalentes** de `mutacion_F-111.md` (rigor `critico`). Los dos
   `indent` son cosméticos para la IA, y el `split` está demostrado arriba.
2. **C2 · T13** (MANUAL, después de desplegar en el orden comun 0.13.0 ⇒ sv5 ⇒ sv6, y de revalorar).

## Observaciones (no bloquean)

- **O1 · El comando exacto de T13 no está versionado.** `tasks.md` y `spec_F-111.md` §2 remiten a `run.ps1`,
  `comun_ro.py`, `m1_residuos.py` y `m2_capitulos.py`, que solo existen en el scratchpad de esta sesión (`f111/`).
  Recomendación: antes de desplegar, el líder copia en `current.md` el comando de PowerShell listo para pegar, o deja
  los scripts fuera del repo en una ruta estable. Si no, T13 no se puede repetir en otra sesión.
- **O2 · Riesgo R-1 del design, vigente.** Si IA3 sigue rellenando `contenedor_m3 = 6` con un contrato sin tamaño, sv6
  lo toma como «tamaño del contrato» (R8) y 8 m³ vuelve a salir como 2 × 6. Hay mitigación en el prompt (R13), y T13
  debe buscar en concreto `contenedor=6` con 8 m³.
- **O3 · Importación privada.** `partida_residuos.py` importa `_familia_de` de `valuation_builder`. El design pedía
  «reutilizable»; una función pública (o en `familia`) sería más limpia. Cosmético.
- **O4 · Coste de los fallos.** El cliente reintenta 3 veces también el 500 genérico de sv5, que puede ser un fallo
  determinista del LLM: hasta 3 llamadas de pago por documento. Aceptable al volumen medido (~4 documentos).

## Automejora (propuesta, no aplicada)

- `CHECKPOINTS.md` C4: exigir que las MANUAL apunten a scripts **versionados** o a un comando autocontenido. Una
  referencia a un scratchpad de sesión no se puede repetir (O1).
