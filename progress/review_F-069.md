Revisión incremental desde d84f27a (pasada 2), hasta 84de3b9
<!-- progress/review_F-069.md -->
# Review F-069 · Usuario y empleado de Sigrid de quien aprueba

**Veredicto: APPROVED** (APROBADO). Reviewer, 2026-10-24. Queda una condición que no depende del
código: **el humano tiene que aceptar la justificación del único superviviente equivalente**
(rigor `critico`, máximo 0 sin aceptación). Hasta entonces la feature no puede pasar a `done`.

**Nivel de rigor:** `critico`, declarado en `harness/features.json`: fase RED, cobertura ≥ 80 %,
mutación con 0 supervivientes o justificación aceptada por el humano, RM5 y MANUAL con comando.

Lo aprobado hasta `d84f27a` en la pasada 1 (`git show d84f27a:progress/review_F-069.md`) se da
por bueno: resolución de `usu`/`empide`, que `resolucion` no viaje a sigrid-api, panel de sv4,
infra sin `ALTA_SIGRID_COMMIT`, documentación y trazabilidad R1–R29. El delta no cambia firmas,
no mueve ficheros y solo toca dentro del alcance medido el script de medición.

## init.sh (ejecutado por el reviewer, tal cual, en el worktree)

Antes: ninguna suite de albaranes en marcha (las de datamart-seg-anual y partes no cuentan; un
`bash` de otra sesión, abierto desde las 7:47 sin hijos ni CPU, no ejecuta nada). Sin borradores
en `progress/` mientras corría (este informe se escribió en el scratchpad y se copió después).

**Exit 0, «ENTORNO LISTO»**: raíz 1883, sv1 205, sv2 485, sv3 1576, sv4 1808, sv5 96, sv6 473
+ 1 skipped, **sv9 961** (41 s), comun en caché verde. **PUERTA COBERTURA [OK] 99,6 %** (443/445,
umbral 80 %); rutas sensibles N/A; **PUERTA TAMAÑO [OK]** (impl 218/220, review 140/140).

## Delta revisado (`d84f27a..84de3b9`, commits `33c6d6c` y `84de3b9`)

- **Condición 1 (superviviente `zip`) — cumplida.** `medir_empleados_f069.py:306-311`:
  `strict=True` y el `ValueError` pasa a `RuntimeError("sql/read: fila desparejada…")`, como
  `truncated`. Test nuevo `test_f069_script_fila_desparejada_es_fallo` (fila corta y fila
  larga), con traza RED real en el informe (`2 failed` sin el código, `2 passed` con él).
  RM4 sobre una copia en el scratchpad: con `strict=False` restaurado, el test da `2 failed`;
  con el código, `test_f069_script.py` entero `49 passed`. Copia borrada y árbol intacto.
- **Condición 2 (campaña repetida + RM5) — cumplida.** Tercera campaña de la herramienta.
- **Condición 3 (`servicios`) — cumplida.** `sv9-alta-sigrid`, `sv4-front` e `infra`.
- **T5 hecha por el líder** (`progress/medicion_F-069.md`), `tasks.md` T5 `[x]`.

## Medición `progress/medicion_F-069.md` (T5)

- **Sin correos completos**: 0 `@` en el fichero. **Sin nombres ni DNI**: solo Logins
  (6), `ide` de `dbo.emp`, `con.ide`, códigos `AC26/…` y `usu`. No se versiona el CSV. Barrido
  del delta entero (correos, GUID, IP, `password=`, `AccountKey`, `sig=`, nombres en mayúsculas):
  solo los correos ficticios de los tests y los marcadores del informe.
- Resultado para el humano (E5): 7 aprobadores (5 con empleado único, 1 sin empleado —
  un buzón, no una persona—, 1 sin correo de Ruesma); 68 altas escritas, **65 con un empleado
  distinto del que les correspondería**; la consulta por correo tarda 3,5 s de media (5,4 s
  máximo), por debajo de los timeouts de sv9. La decisión sobre esas 65 es del humano (con F-103).

## Mutación (`progress/mutacion_F-069.md`, tercera campaña)

- **Recálculo independiente** sobre HEAD (`harness.alcance` + `generar_mutantes`, puro):
  11 ficheros, **1007 líneas, 148 mutantes**: coincide con el informe. El superviviente existe
  con el mismo operador y texto (`:46 [entero] insert(0 → 1)`); el `zip` ahora es
  `strict=True → False` (`:309 [booleano]`) y sale muerto.
- **Campaña no reejecutada: 2047,7 s (34 min) según el informe** (> 60 s): recálculo + RM1–RM6.
- **RM1** SHA medido `33c6d6c`; de ahí a HEAD solo cambian ficheros de `progress/`. Válido.
- **RM2** 4 workers; media 13,8 s × 4 = 55 s por mutante frente a líneas base de 51 s (sv9) y
  167 s (sv4), con `-x`: coherente; 148 × 13,8 ≈ 2042 s ≈ total. Coste por mutante
  2047,7 × 4 / 148 = 55,3 s. Sin «NO VÁLIDA», 0 sin veredicto, 0 timeouts.
- **RM3** los muertos nuevos respecto a la 2.ª campaña son el `strict` (no equivalente: lo mata
  el test nuevo). Nada equivalente sale muerto.
- **RM5** el superviviente trae ya demostración ejecutable (script y salida real en el informe),
  la misma que reproduje en la pasada 1 sobre dos copias en el scratchpad: idéntica resolución de
  `domain`, `infrastructure`, `httpx`, `psycopg` y `tenacity`, y `--help` con 0. **Equivalente.**
- **RM6** N/A justificado: no se quitó ninguna guarda; el cambio añade una comprobación.

## Checkpoints

**C1** [x] init.sh exit 0 · [x] ficheros del arnés.
**C2** [x] una sola `in_progress` (F-069) · [x] rama `feature/F-069-usuario-empleado-sigrid` ·
[x] `current.md` al día con la pasada 2 · [x] las `done` con su resumen en `history.md`.
**C3** [x] hexagonal (sin cambios en el delta; el script sigue fuera, design §6) · [x] primera
línea con ruta · [x] sin prints de debug, TODO, secretos ni dependencias nuevas · [x] reglas de
`ARCHITECTURE.md` (tres trampas N/A: ni merge/raw, ni schema, ni importes).
**C3 bis** N/A: no toca `docs/referencia/`.
**C4** [x] todo requisito con test y en verde (tabla de la pasada 1, más el test nuevo de R25) ·
[x] sin red ni BBDD (`httpx.MockTransport`) · [x] MANUAL T16 y T17 listadas en `current.md`,
con su comando exacto en `progress/impl_F-069.md`.
**C4 bis** [x] rigor declarado · [x] fase RED (también la del cambio de la review) · [x] cobertura
[OK] (abajo) · [x] mutación con totales verificados · [x] > 60 s: recálculo, dicho arriba ·
[x] coste por mutante 55,3 s · [x] sin «NO VÁLIDA» · [x] RM1 · [x] RM2 · [x] RM5 · [x] RM6 N/A
justificado · N/A campaña manual (la automática dio 148) · [x] supervivientes: 1, analizado y
demostrado; **su aceptación es del humano** (condición de cierre, no de código) · [x] «Evidencias»
con los cuatro números y los 4 workers.
**C4 ter** N/A: la puerta de rutas sensibles de init.sh dice que F-069 no toca ninguna.
**C5** [x] `tasks.md`: T1–T15 y T18 `[x]` con sus commits (`F-069 Tn:` y los dos de la review);
T16 y T17 son MANUAL del humano tras fusionar · [x] árbol limpio salvo este informe ·
[x] `features.json`: `in_progress`, rama y `servicios` reales.

## Para cerrar (no son cambios de código)

1. **Humano**: aceptar (o no) la justificación del equivalente `sys.path.insert(1, …)` de
   `services/albaranes-alta-sigrid/scripts/medir_empleados_f069.py:46`, con su demostración en
   `progress/mutacion_F-069.md`.
2. **Humano**: decidir E5 con la medición (65 altas con otro empleado), junto con F-103.
3. Tras fusionar en `dev`: T16 (despliegue, escribe en producción) y T17 (comprobación en solo
   lectura), con los comandos de `progress/impl_F-069.md`.

## Observaciones de la pasada 1 que siguen (no bloquean)

- `create_capps_sv9.ps1` y `set_alta_sigrid.ps1` comparan la Lista releída con `-ne` (en
  PowerShell no distingue mayúsculas); `-cne` sería exacto.
- El cliente de sv9 (`sigrid_api_alta_client.py:208`, de F-053 y fuera del diff) sigue con
  `zip(strict=False)`: el mismo hueco que se cerró en el script; candidato a una mejora aparte.
- `ruff` en los ficheros nuevos: `I001` y `RUF100`, autocorregibles.
- **Automejora** (propuesta, no aplicada): RM5 de `CHECKPOINTS.md` podría decir que «equivalente
  bajo el contrato de un tercero» no es equivalente, sino un comportamiento sin test.
