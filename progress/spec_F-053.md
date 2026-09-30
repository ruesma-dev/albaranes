<!-- progress/spec_F-053.md -->
# Spec F-053 · Alta en Sigrid de los albaranes aprobados (spec-author, 2026-09-30)

Rama `feature/F-053-alta-sigrid` (worktree `../albaranes-F-053`, desde `dev` c8a295e).
Estado `spec_ready`, rigor `critico`, prioridad 1. Registrada en `harness/features.json`.

## Qué se ha escrito

- `specs/F-053-alta-sigrid/requirements.md` — R1–R36 en EARS (149 líneas, tope 150).
- `specs/F-053-alta-sigrid/design.md` — servicio sv9, flujo, DDL, configuración,
  orden, cambio de reglas propuesto (240 líneas).
- `specs/F-053-alta-sigrid/tasks.md` — T1–T30; T22 y T26–T29 son MANUAL del humano.
- `python -m harness.tamano --feature F-053`: dentro de los topes.

No se ha llamado a sigrid-api ni a Azure. sigrid-api se leyó en solo lectura.

## Hallazgos que condicionan el diseño

1. **sigrid-api vigente = `sigrid-api`** (git, rama `dev`, último commit del 25 sep).
   `sigrid-api-v2` es una copia de julio sin git: no se usa.
2. **`sigrid/albaran` no deja fijar ni precio ni partida.** Pide `{ctrpro_ide,
   cantidad ≥ 0}` y copia de la línea de contrato precio (`ctrpro.pre`, neto),
   partida (`paride`), almacén y cuenta. Con eso **no se puede expresar**: la
   línea en almacén de F-051 si la línea de contrato tiene partida, una partida
   final distinta de la del contrato, un precio distinto del contrato, las
   líneas sin línea de contrato (derivadas `missing_partida`/`alm_acopio`, sin
   match, sintéticas sin recurso) ni las devoluciones (cantidad negativa).
3. **`sigrid/albaran-directo` exige `proide`** (producto de Sigrid) por línea;
   el pipeline no lo tiene. Además, con `paride` nulo hereda el de la última
   `dcapro` del producto (lo vio también F-051). **Fuera de v1.**
4. **Sin idempotencia en sigrid-api** para albaranes (roadmap 1 de
   `sigrid_api.md` §13). `dca.synckey` («Clave externa de sincronización», 128)
   existe pero no se usa; `dca.entref` («Referencia», 128) tiene índice. La spec
   se defiende con estados, una réplica, grabación sin reintento, Espera antes de
   retomar un `incierto` y búsqueda por CIF + referencia.
5. Errores de sigrid-api: 400 con **texto libre, sin códigos** (salvo
   `concepto-grafico`); 500 para lo inesperado. El docstring de la ruta
   `sigrid/albaran` dice que replica todas las líneas del contrato; el código solo
   incluye las pedidas. R17 (`lineas_distintas`) lo vigila en cada previa.
6. **Ya existe F-013** («Registro del albarán aprobado en Sigrid», `pending`,
   pensada con `sql/write`). F-053 la sustituye: ver pregunta 3.
7. **Nombre**: `sv7` = orquestador retirado (comentarios de sv4 y
   `ruesma_comun.workflows`); `sv8` = `ca-sv8-aprendizaje`, en el docstring de
   `MensajeFeedback`. Se propone **sv9**, `services/albaranes-alta-sigrid`.
8. En sv4, `update_document` pone `approved_at_utc = ahora` en **cada** guardado
   con `approved=true`. Por eso el disparo es solo el paso de no aprobado a
   aprobado (R1–R2), no «cada vez que se aprueba».
9. El **deshacer** de sv4 restaura instantáneas de la fila del merge: si el
   estado del alta viviera en el merge, deshacer lo devolvería a un estado viejo.
   Por eso va en tabla aparte, `albaran_altas_sigrid`, que solo escribe sv9.
10. Las columnas de aprobación (`approved*`) las crea sv4 por ALTER, no sv3. La
    tabla nueva va a sv3 como propuso el líder (pregunta 13).
11. `features.json` de esta rama no tiene F-051 ni F-052 (viven en sus ramas):
    habrá un conflicto trivial al fusionar las tres.

## Orden y dependencias

**F-052 → F-051 → F-053.** F-053 se puede implementar a la vez en su rama, pero
se fusiona después de las dos y el modo real no se enciende hasta que las tres
estén en producción. Detalle en design §8.

## Preguntas abiertas al humano (PARADA 1)

1. **Servicio nuevo sv9 dentro del monorepo** (propuesta) o proyecto aparte.
   Es una responsabilidad nueva: escribir en el ERP.
2. **Cola**: sv9 consume `q-feedback` como dice `docs/ARCHITECTURE.md`. El
   docstring de `MensajeFeedback` la destinaba a un «sv8 aprendizaje»: si algún
   día existe, necesitará su propia cola (las colas de Azure no reparten un
   mensaje a dos consumidores). ¿De acuerdo, y con el nombre sv9?
3. **F-013**: ¿se cierra como sustituida por F-053? No se ha tocado su estado.
4. **Alcance de v1 limitado por sigrid-api** (hallazgos 2–4). v1 solo registra
   albaranes cuyas líneas con cantidad casan **todas** con líneas del contrato de
   la valoración y con su misma partida; el resto queda `no_admitido` y se da de
   alta a mano. Para cubrir más hace falta una feature en **sigrid-api** (otro
   repositorio): (a) `paride` por línea; (b) líneas fuera de contrato dentro del
   mismo albarán; (c) resolución de producto para `albaran-directo`; (d)
   devoluciones; (e) `referencia_externa` → `dca.synckey` con idempotencia, como
   ya hace `partes-reclamacion`. ¿Se acepta v1 así? ¿Medimos antes, con una
   consulta de solo lectura a nuestra BBDD, qué parte de los aprobados sería
   admisible? Si sale muy baja, conviene hacer antes la de sigrid-api.
5. **¿Aprobar un albarán no admisible?** Propuesta: se deja aprobar, y el alta
   queda `no_admitido` con sus motivos en la ficha. Alternativa: bloquear la
   aprobación (exigiría validar en sv4 al aprobar).
6. **Duplicados por CIF + «Referencia» (`entref`)**: ¿los administrativos ponen
   el número de albarán del proveedor en «Referencia» al darlo de alta a mano?
   Se puede medir con `sql/read` si lo autorizas. Un proveedor que repita número
   bloquearía el alta (`ya_en_sigrid`, visible): se prefiere a duplicar.
7. **Tolerancia e importes**: Sigrid valora al precio del contrato. Si el total
   de una línea difiere del importe aprobado en más de 0,05 €, el alta va a
   `revisar` y no se graba. ¿Vale 0,05 € por línea? Avisos de la previa que
   bloquean: «plantilla de cabecera no es del mismo proveedor» y «sin histórico
   de dcapro». ¿También «cantidad recibida supera lo pendiente de servir»?
8. **Empleado (`empide`)**: ¿fijo (el defecto de sigrid-api, o uno en
   `ALTA_SIGRID_EMPIDE`) o el empleado de Sigrid de quien aprueba (habría que
   mantener una correspondencia)?
9. **Adjunto del PDF**: ¿qué usuario de Sigrid va en `usu` (tiene que existir en
   `dbo.usu`)? Y conviene confirmar, en solo lectura, que
   `SIGRID_DOCUMENT_ALLOWED_GRATIPIDE` incluye `0` y que la firma de PDF está
   en `SIGRID_DOCUMENT_ALLOWED_MAGIC`: el líder comprobó `CONTIP`, no esas dos.
10. **Paso de simulación a real**: ¿los documentos que quedaron `simulado` se
    graban solos al activar el modo real? Propuesta: no; se hace uno a uno
    desde la ficha con «Solicitar alta en Sigrid».
11. **Aprobados antes de DESDE**: no se registran (R6). Pero desaprobar y volver a
    aprobar reinicia `approved_at_utc` y cuenta como aprobación nueva. ¿Se
    acepta? La búsqueda de duplicados lo cubre si ya se dio de alta a mano con la
    referencia.
12. **F-006** (`no_registrar_sigrid`, residuos «solo llevar») y **F-015**
    (tachadas) no están hechas. Hoy solo se excluyen las líneas con cantidad 0.
    ¿Se espera a que lleguen o se integran en R13 cuando lleguen?
13. **DDL**: la tabla la crea sv3 (dueño del schema, como propusiste) y la
    escribe solo sv9. Alternativa: sv9 dueño de su tabla, como sv6.
14. **Albarán registrado**: se propone bloquearlo en sv4 (R25). Para corregirlo:
    anularlo a mano en la UI de Sigrid, pulsar «Ya lo he anulado en Sigrid»
    (sv9 comprueba que el `con.ide` ya no existe) y volver a solicitar el alta.
    ¿Vale?
15. **Documentación que no es de este repositorio**: la fila de consumidores de
    `azure-apps/sigrid_api.md` §10 es de sigrid-api (propuesta: «albaranes (sv9):
    `sql/read`, `sigrid/albaran`, `sigrid/concepto-grafico`, alta del albarán
    aprobado»). La regla del `CLAUDE.md` sobre Sigrid tiene redacción propuesta
    en design §9; no se aplica sin tu visto bueno.
16. **Clave de sigrid-api**: con la escritura de dominio abierta, cualquiera
    que tenga la clave por defecto puede grabar (sv2, sv3, sv4 y otros proyectos
    ya la tienen). ¿Se crea una clave de función solo para las rutas de escritura
    y solo la tiene sv9? Es un cambio en Azure: lo haces tú.

## Riesgo residual (sin pregunta)

Si una llamada de grabación tarda más que la Espera (15 min) en terminar dentro
de la Function después del corte del balanceador, un reintento humano podría
no verla todavía. Lo cierra de verdad la idempotencia en sigrid-api (pregunta 4e).
