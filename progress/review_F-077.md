<!-- progress/review_F-077.md -->
Revisión incremental desde 84e5f78 (pasada 2) · delta `84e5f78..7255a69`; pasada 1 completa sobre `df9c862`

# F-077 · Ficha: guardar y aprobar de una vez · Review (2026-10-17)

**Veredicto: APPROVED.** Los cambios 1–3 de la pasada 1 están aplicados en `861aa70`. El delta no toca código y
`init.sh` sigue en verde.

**Rigor:** `estandar` (declarado): RED en los centrales, cobertura ≥ 80 % y mutación con supervivientes analizados.
Todo eso quedó verificado en la pasada 1; el delta no lo invalida.

## Pasada 2 (incremental)

**Delta.** `596a0a5` (fusión de `dev` con `6bd49ef`/`24c8bd9`), `861aa70` (cambios 1–3) y `7255a69` (resultado de
`init.sh` en el impl). Toca `current.md`, `impl_F-077.md`, `spec_F-077.md`, `design.md`, `requirements.md` y
`sv4.md`. **Cero código:** el único fichero bajo `services/` es `sv4.md` (2 líneas), así que el alcance de la campaña
de mutación no cambia.

- **P2.1 · Cambio 1a (redirección).** El punto 5 dice «la **misma ficha se recarga aprobada** (solo lectura, con el
  mensaje de guardado)». Coincide con `app.py:1235`. «Alta en curso…» y el sondeo se miran en esa misma ficha, «en
  segundos».
- **P2.2 · Cambio 1b (quién y qué escribe).**
  - El título dice «la hace el LÍDER en el navegador, con el humano», y el impl §6 lo repite.
  - Las acciones que escriben llevan **[ESCRIBE EN PRODUCCIÓN]**, con «el sí expreso del humano en el chat, para
    esa acción, antes de pulsar». Solo el punto 5 escribe, y enumera lo que escribe: PATCH de fila con `?bloquear=1`,
    PUT de aprobación y `q-feedback`.
  - El punto 4 «no escribe nada si sale verde» y manda parar si sale alguna PATCH o PUT en F12.
  - Los puntos 1–3 son solo lectura. La consulta SQL de reserva del punto 1 lleva
    `SET default_transaction_read_only = on`.
- **P2.3 · Cambio 1c (no se inventan datos).** El punto 5 se hace solo si el humano tiene un albarán pendiente que
  «necesite de verdad» correcciones; la ficha y los valores los elige él. Explica por qué: un «Solicitar alta»
  posterior con `COMMIT=true` mandaría esos valores a Sigrid. Si no hay ninguno, el punto no se hace, se anota, y queda
  cubierto por `test_f077_guardar_y_aprobar_js.py`. Los puntos 3 y 4 usan fichas que indica el humano y no guardan
  nada.
- **P2.4 · Cambios 1d/1e (encaje).**
  - El bloque de F-077 dice que se despliega en el **paso 4** de la secuencia combinada, que T14 va justo después y
    que el punto 1 va **antes del paso 6**.
  - El paso 4 de la secuencia lleva su nota simétrica («si F-077 ya está en dev, este sv4 la lleva…»).
  - El paso 6 dice «después de su punto 1 de T14».
  - El `no_admitido` en rojo queda ligado a `86c13097`. Punto 1: «Error en el alta en Sigrid: No admitido» y «Línea
    N: La línea no tiene descripción». Punto 2, tras el paso 6: «Estado: Simulado (no grabado)». Los textos coinciden
    con `ETIQUETAS_ESTADO_ALTA` y `TEXTOS_MOTIVO_ALTA`.
  - Lo comprobé contra `fase_alta`. Antes del paso 6, la fila es de la aprobación vigente, en `no_admitido` ⇒
    `resultado` en rojo. Tras «Solicitar alta» (sin reaprobar) ⇒ `simulado` ⇒ `resultado`. La reserva del punto 1
    (instantes distintos ⇒ `en_curso`/`sin_respuesta`) también es coherente con R14.
- **P2.5 · La fusión de `dev` no estropea la secuencia combinada.** Los pasos 1–7 conservan su orden: sv6 ⇒ relleno ⇒
  sv4 ⇒ relectura ⇒ F-078 T14 ⇒ F-076 T19. `Usar-PgAzure`/`Quitar-PgAzure` envuelven solo los tres scripts que leen
  o escriben la BBDD: pasos 1, 3 (con `--aplicar`) y 5. Los pasos 2 y 4 (`infra\`) no los necesitan. Las funciones
  van en su propio bloque, que se pega al abrir la consola. No queda conflicto de fusión ni línea duplicada.
  Observación para el líder, que no es de F-077 (viene de `dev`, `6bd49ef`): ese bloque deja versionados el host del
  PostgreSQL, el usuario administrador y el nombre del Key Vault. No son contraseñas; el host ya consta en
  `azure-apps/`. Aun así, el usuario admin roza la regla «nada de cadenas de conexión»: valora si debe salir de
  `00_vars.ps1` (no versionado).
- **P2.6 · Cambio 2 (notas de spec).** Las notas «Nota 2026-10-17 (implementación, aceptado en review)» están en:
  - R22 de `requirements.md`: « · », `title` con la nota de F-076 y el aviso, excluyentes;
  - `spec_F-077.md` §5;
  - design §3: `avisoFilasSinGuardar`/`contarFilasConCambios` se quedan para «Dividir» y se borra
    `partidasInvalidas`, como en el código;
  - design §5 y §9.
  
  Todas coinciden con el código aprobado. `requirements.md` va por 127 de 150 líneas.
- **P2.7 · Cambio 3.** La cita «> F-077: …» de `sv4.md` §11 está fuera de la valla, y la valla abre justo después.
- **P2.8 · `bash harness/init.sh`** (Git Bash, worktree, sobre `7255a69` con esta review): **exit 0, «ENTORNO LISTO»**. Raíz 1237; sv1 205,
  sv2 397, sv3 703, sv4 1715, sv5 43, sv6 444 (+1 skip), sv9 670, todas ejecutadas; comun por caché. `COBERTURA` [OK]
  100 % (92/92); `TAMAÑO` [OK] (review 129/140).

Checkpoint que estaba en `[ ]` y ahora pasa a `[x]`: **C4 · MANUAL listadas con sus pasos exactos y criterio de
verde**. Los demás, como en la pasada 1.

# Pasada 1 (completa, sobre `df9c862`), resumida

Texto completo de la pasada 1: `git show 84e5f78:progress/review_F-077.md`.

**Verificación.**
- `init.sh`: verde, con sv4 1715 passed sin caché y `COBERTURA` [OK] 100 % (92/92).
- Mutación, recálculo puro: 301 líneas y 39 mutantes, que coinciden con el informe. El único superviviente
  (`app.py:1761`, `include_in_schema`) es real y quedó cerrado con un test.
- Campaña no reejecutada: 980,8 s (más de 60 s).
- RM1: el alcance medido sobre `e1d9937` es el revisado. RM2: 49 s × 4 workers = 196 s por mutante, frente a una base
  de 169 s.
- RM3/RM5 N/A, con motivo; RM6, conforme.

**Juicio.**
- **Desviaciones de `impl` §3:** todas caben en la spec, y deben ir en el resumen de la PARADA 2.
  - #1: el « · » lo delegaba la nota de F-076;
  - #2: R27 manda cubrir todo código que escribe sv9 (los cuatro nuevos existen en `alta_sigrid_service.py`);
  - #3: R13 se ciñe a F-065 R19, y «Dividir» queda fuera por design §8.
- **Panel del alta, según las palabras del humano:** cumple.
  - «En curso» solo si sv9 procesa la aprobación vigente.
  - Un resultado malo sale como error, nunca «en curso».
  - Sondeo de 3 s con `setTimeout`; a los 5 min, `sin_respuesta`.
  - No sondea si sv9 va a ignorar la aprobación.
  - La ruta GET es de solo lectura y no publica.
- **«Guardar y aprobar»:** cumple.
  - Guarda antes las filas y para al primer fallo, sin PUT.
  - D2: no reenvía las filas guardadas.
  - El doble clic no repite nada: `enMarcha` y los botones desactivados.
- **⚠ de partida:** solo en Contrato con lectura del albarán; `title` « · ».
- **Integración con F-078 R17 y F-076 R23–R25:** probada.

Observaciones que no bloquean:
- Un `incierto`/`en_curso` anterior pasada la Espera lo reprocesa sv9 sin que el panel sondee (decisión de design §4).
- R6 relee el aviso de la suma solo «en este intento».

**Checkpoints** (sin cambios en la pasada 2, salvo C4):
- **C1** [x] `init.sh` en verde · [x] ficheros del arnés.
- **C2** [x] una sola `in_progress` · [x] rama de la feature · [x] `current.md`, solo trabajo vivo · [x] las `done`,
  en `history.md`.
- **C3** [x] hexagonal · [x] primera línea con ruta · [x] sin `print`, TODO, secretos ni dependencias nuevas ·
  [x] reglas 19 y 20.
- **C3 bis** N/A: no toca `docs/referencia/`. **C4 ter** N/A: la puerta de rutas sensibles da N/A con motivo.
- **C4** [x] R1–R28 con su `test_f077_rN_*` en verde, y R29/R30 revisados · [x] sin red ni BBDD · [x] MANUAL
  (pasada 2).
- **C4 bis** [x] `rigor` · [x] RED con traza real · [x] cobertura · [x] mutación verificada de forma independiente ·
  [x] más de 60 s: recálculo puro · [x] coste por mutante · [x] sin cabecera de no válida · [x] RM1 · [x] RM2 · N/A RM5
  (`estandar`) · [x] RM6 · N/A campaña manual (no la hubo) · [x] superviviente analizado · [x] «Evidencias» con los
  workers.
- **C5** [x] T1–T13 y T15, cada una con su commit `F-077 Tn:`; T14 es MANUAL pendiente · [x] árbol limpio ·
  [x] `features.json` en `in_progress` (pasará a `blocked` o `done` con T14).

**Cobertura requisito → test** (`services/albaranes-front/tests/test_f077_*.py`): R1–R28 tienen cada uno al menos un
`test_f077_rN_*`. La tabla, en el texto completo de la pasada 1.

## Cambios requeridos

Ninguno.

## Automejora (propuesta, no aplicada)

`CHECKPOINTS.md` C4, punto MANUAL: añadir «cada acción que escriba en producción va marcada, con quién la ejecuta y
su autorización». Es lo que pedía el cambio 1b, y hoy ningún checkbox lo exige.
