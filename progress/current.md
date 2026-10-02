<!-- progress/current.md -->
# Trabajo en curso

> Podado el 2026-10-01 al cerrar F-052 (C2 de `progress/review_F-052.md`). El `current.md` anterior, íntegro, está
> en `progress/historico/current_2026-10-01_cierre_F-052.md`; el resumen de F-052, en `progress/history.md`.
> Aquí solo queda lo vivo. Lo que manda sobre el estado de cada feature es `harness/features.json`.

**F-054 · CERRADA (`done`, 2026-10-02)**, review de cierre APROBADA: sv1 ingiere los PDF **e imágenes** de correos
adjuntos (`message/rfc822`). Rama `feature/F-054-correo-adjunto-encadenado`, **pendiente de merge a `dev`**, despliegue
de sv1 y la verificación MANUAL T12 (sección «F-054 · lo que queda» al final). Resumen en `progress/history.md`.

## LO PRIMERO AL ABRIR LA PRÓXIMA SESIÓN

- **F-054 · CERRADA (`done`, 2026-10-02)**. Pendiente del humano: merge de
  `feature/F-054-correo-adjunto-encadenado` a `dev`, `.\deploy.ps1 -Only sv1` + `.\check_deploy.ps1` desde `infra/`
  y la **T12 MANUAL** (procedimiento al final). La T12 no bloquea el `done`.
- **F-052 · CERRADA (`done`, 2026-10-01)**, fusionada en `dev` y desplegada (sección de abajo).
- **F-053** (alta en Sigrid de los aprobados): `spec_ready` en `../albaranes-F-053` (rama
  `feature/F-053-alta-sigrid`), **16 preguntas abiertas** al humano. La escritura en Sigrid NO va en el despliegue
  de F-052.
- **F-051** (almacén por línea): spec v2 en `../albaranes-F-051` (rama `feature/F-051-almacen-por-linea`),
  **esperando las respuestas del humano**.
- **F-055** (IA2 elige el proveedor entre los de la obra): `pending`, prioridad 1. Depende de F-052.
- **Fichas nuevas del cierre de F-052** (`pending`, prioridad 2): **F-056** re-búsqueda doble en sv4 y **F-057**
  truncado sin comprobar en los clientes colindantes de sv4 y sv3.
- **Crédito de OpenAI agotado el 2026-09-30.** Probablemente **3 albaranes en `q-extraccion-poison`**: comprobar y
  reencolar cuando haya crédito (pendiente).

F-051 y F-053 viven en sus ramas: no constan en el `features.json` de esta rama hasta que se fusionen en `dev`.
F-054 consta aquí como `done` (esta es su rama); llega a `dev` con el merge.

## F-052 · cerrada, fusionada y desplegada (2026-10-01)

- Merge a `dev` por el humano (`a7a53ef`, subido a `origin/dev`). Despliegue del humano: sv3 `r20261001-1654`
  (DDL `contratos_busqueda_*` OK en producción, comprobado en Log Analytics) → sv4 `r20261001-1657` (100 % del
  tráfico; la revisión vieja seguía activa: `fix_revisiones.ps1 -Only sv4`).
- **T23 cerrada por el humano (2026-10-01)**: «hemos estado probando, no hace migrar nada de albaranes antiguos.
  da t23 por cerrada». Sin saneamiento de históricos (D5): si aparece alguno, se corrige a mano en sv4 con «Solo
  volver a buscar» o cambiando el CIF y guardando. Comando y SELECT de sospechosos, por si se necesitan: T23 en
  `specs/F-052-proveedores-truncados/tasks.md` y `progress/spec_F-052.md` §Anexo.

### 3. Observaciones de la review de cierre que siguen vivas

- **Re-búsqueda doble en sv4 → ficha F-056** (O-C2 + mejora menor de T22 + O-C8). La mejora de T22, tal como la
  anotó el humano: un «Guardar» pulsado mientras la ficha está en «Buscando…» relanza otra búsqueda, porque el
  rastro aún tiene el CIF/obra de antes. Inocuo (sv3 y sv6 reemplazan), pero es trabajo doble. Arreglo barato:
  mientras busca, sv4 no relanza si CIF y obra son los mismos con los que lanzó la búsqueda en curso. O-C2: el
  autoguardado del combo (obra y luego proveedor) publica dos re-búsquedas. O-C8: «Solo volver a buscar» con CIF y
  obra vacíos publica un mensaje que sv3 descarta sin sellar.
- **Truncado sin comprobar en los clientes colindantes → ficha F-057** (O-C4 + D6, que decía «ficha aparte» y no
  existía): `header_and_lines` de sv4 (`max_rows=1000`, sin `comprobar_truncado`) y `SigridApiObraClient` de sv3.
- **O-B2 · enseñar al humano** (nunca la aceptó por escrito): extensiones de R21, `replace_contratos` fallido →
  rastro `error`; `enabled=False` → sin sello. Consta en `history.md` como decisión.
- **El «1.000» ajeno, para el humano (otros dueños)**: `PycharmProjects/CLAUDE.md` dice que sigrid-api sirve «como
  máximo 1.000 filas por petición» y otros documentos de `azure-apps` lo repiten. El 1.000 era el `max_rows` del
  cliente; sigrid-api admite 500.000 (`docs/ARCHITECTURE.md` «Acceso a datos»).

### 4. PENDIENTE · portar a `arnes-base` (regla de propagación)

`harness/mutacion.py` cuenta a veces como VIVO un mutante muerto. 3 casos en F-052, sin causa encontrada: en
paralelo (4 workers, `07f89cf`) `sigrid_api_contrato_client.py:1081` y `verificar_f052_proveedores_obra.py:331`;
en serie (`dcca978`) `ruesma_comun/obras/codigo.py:39`. Los tres mueren reevaluados aislados con
`ejecutar_campania` en un worktree limpio (mismo intérprete y comando, `.pyc` purgado). Siempre en la dirección
conservadora. Abrir feature de arnés para reproducir y corregir, y portarla a `arnes-base`. Relacionada: F-041.

Propuesta de automejora de la review de cierre (no aplicada): que `init.sh` avise si `current.md` cita como vivo
(`in_progress`/`blocked`) un ID que `features.json` tiene `done`. Genérica: si se aplica, va también a `arnes-base`.

## Arrastre heredado (anterior a F-052; sin verificar desde su fecha)

Resumido del `current.md` anterior; el detalle, en el archivo de `historico/`. Antes de actuar, comprobar que sigue
vigente.

- **F-047** (`spec_ready`, aparcada el 2026-09-24): al retomarla, cablear `anadir_opcion_sin_correo` en el CLI del
  ciclo, pasar `correo=correos.cargar_correo(caso_id)` desde `ciclo.py` y traer
  `tests/test_f047_r5_seleccion_contrato.py`; nota al final de `specs/F-047-evals-ciclo-completo/tasks.md`. Faltan
  además los 130 supervivientes de `progress/mutacion_F-047.md`, T24–T26 y limpiar 28 worktrees huérfanos.
- **F-048**: confirmar que su despliegue (sv3 → sv2 → sv1 → sv4) está hecho; si no, va junto con el de F-052.
- **Pendientes del humano** (2026-09-24 y anteriores): meter un albarán por producción; decidir si se versionan los
  libros de `evals/ground_truth/`; MANUAL arrastradas de F-002 (liberan el merge de F-003), F-019 y F-027;
  reconciliar F-003 y F-004 antes de arrancarlas; histórico mal valorado en BBDD (sin backfill, se sanea
  revalorando desde sv4); actualizar los otros proyectos al arnés vigente; `mutacion_F-011.md` invalidada y
  `mutacion_F-002.md` en cuarentena (en `historico/`); un PDF versionado que incumple la norma
  (`services/albaranes-api/worker_input/0695 - Albaranes 2026.03.09-13-16.pdf`).
- **Mejoras del arnés propuestas y no aplicadas** (genéricas, irían a `arnes-base`): la caché de `init.sh` no se
  invalida cuando cambia `comun`; `PUERTA RUTAS SENSIBLES` sale `N/A` con la ficha en `blocked`; `CHECKPOINTS.md`
  no contempla la review por bloques; falso verde de `harness.cobertura --feature`; `harness.mutacion` no muta
  `in`/`not in`; avisar cuando el alcance de una feature arrastra el de otra.
- **Deudas menores**: RM2 solo dispara a 10×; marcas `[ADAPTAR]` en las specs de F-034 y F-035; ~1166 avisos de
  `ruff`; sv1-email e `infra` sin tests.

## Notas operativas (valen para cualquier sesión)

- **Los `impl_`, `review_` y `evals_` de features cerradas viven en `progress/historico/`**. Las **campañas de
  mutación NO se archivan**: F-039 las vigila por ruta fija y moverlas pone 8 tests en rojo. El porqué, en
  `progress/historico/README.md`.
- **Nada en paralelo**: dos suites a la vez tumban el proceso en Windows (`0xC0000142`). Y **una campaña de
  mutación muta el árbol principal**: mientras corra, no lanzar `init.sh` ni tests.
- **Un agente con demasiado contexto se cuelga en bucle.** Lanzar uno **nuevo y acotado** —diciéndole exactamente
  qué leer— lo resuelve y sale más barato. Un agente que se cuelga no pierde el trabajo commiteado: commit por tarea.
- **No ensuciar el árbol mientras un agente trabaja**: C5 exige árbol limpio, y tus cambios pueden colarse en el
  commit de otro.
- **Los agentes no deben usar scripts que reescriban ficheros versionados**; copias en el scratchpad.
- **Cuidado con las rutas de Windows en heredocs de Python**: `\U` de `C:\Users` se interpreta como escape unicode.
- **La máquina es compartida y se nota**: otra sesión corriendo triplica los tiempos y puede invalidar una campaña.
- **Un comando de verificación guardado en `progress/` puede caducar**: guarda también de qué depende.
- **El humano ejecuta él mismo** los `push`, los merges y las verificaciones MANUAL. Dale el comando listo para
  **PowerShell**, con `git -C <ruta>`, sin `&&` (su PowerShell 5.1 da error de parser) y con el criterio de verde.

## F-054 · lo que queda (cerrada el 2026-10-02)

- Informes archivados: `progress/historico/impl_F-054.md` y `progress/historico/review_F-054.md`; la campaña
  sigue en `progress/mutacion_F-054.md` (19/20 muertos, 1 equivalente). Resumen y decisiones en `history.md`.
- Al humano: merge de `feature/F-054-correo-adjunto-encadenado` a `dev`; luego, desde `infra/`,
  `.\deploy.ps1 -Only sv1` y `.\check_deploy.ps1`; después la T12 de abajo.
- Log de R23 nuevo en sv1: `sin adjuntos elegibles: ni directos ni correos adjuntos (total=N) → Errores` (sigue
  conteniendo «sin adjuntos elegibles», el texto que busca la T12 en los logs viejos).
- Al leer los logs de la T12 (O1 de la review): unos bytes basura no vacíos en un correo adjunto se leen como
  `text/plain` y salen como WARNING «sin ningun documento interior valido», no como ERROR «ilegible»; el
  destino es el mismo.

### PENDIENTE DEL HUMANO · verificación MANUAL de F-054 (T12, tras merge a `dev` y despliegue de sv1)

No bloquea el `done`. Procedimiento (design §10 y `tasks.md` T12):

1. Desde `infra/`: `.\deploy.ps1 -Only sv1` y `.\check_deploy.ps1`.
2. En Outlook, carpeta `Errores` del buzón de albaranes: localizar los correos cuyo único adjunto es un correo
   (icono de sobre; en los logs viejos de sv1: «sin adjuntos elegibles»).
3. Mover **uno** a la carpeta origen y **marcarlo como no leído** (el filtro de sv1 es `isRead eq false`).
4. Esperar un ciclo de polling y comprobar en los logs de la Container App de sv1: la línea INFO
   `att=<id> documentos interiores: N PDF y M imagen(es)`, el `intake encolado` de cada página y
   `movido a Procesados`; y el albarán en el front (sv4).
5. Si cuadra, repetir con el resto por tandas pequeñas.
6. Los mixtos que están en `Procesados` con el interior perdido **no** se mueven en bloque (re-ingerirían los
   PDF directos con otra `correlation_key`): uno a uno, si el humano lo decide.
7. Anotar aquí el resultado.
