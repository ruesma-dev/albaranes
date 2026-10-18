<!-- progress/review_F-064_o1.md -->
Revisión incremental desde `9388383` (pasada O1) · delta `9388383..9bb238d` (fusión de `dev` `d79b3d9` en `b06d251` + O1 en `bea97f4` + papeleo)

# F-064 · review · pasada O1

Va en fichero aparte porque `progress/review_F-064.md` está en su tope (140/140, `harness/rigor.json` · `tamano.review`).

**Veredicto: APPROVED.** Cierre de F-064 condicionado SOLO a T9 y T10 (evals con LLM real, humano), que deben correr
sobre **`9bb238de6e1ede94cc3f3bd7d2c8b7fb29d61609`** (`9bb238d`) o cualquier commit posterior de la rama que no toque
`services/albaranes-api` ni `evals/`. Ver §5.

**Rigor:** `critico` (declarado en `features.json`). Fase RED, cobertura ≥ 80 % de lo cambiado, mutación con 0
supervivientes salvo equivalente aceptado, RM1–RM6 y C4 ter (ruta sensible: `revision_rules.yaml`).

## 1. La fusión de `dev` no rompió F-064

- **Ningún cambio de producción de F-064 movido por la fusión.** `git diff --stat 9388383 b06d251 -- services/albaranes-api evals`
  sale vacío; `git diff d79b3d9 HEAD -- services/albaranes-comun services/albaranes-persistencia services/albaranes-front`
  también. Respecto a `dev`, la rama solo difiere en los 29 ficheros de F-064.
- **`features.json`**: F-064 `in_progress` y **única** (F-053 y F-070 `blocked`, como en `dev`); el diff contra `d79b3d9`
  es solo la entrada de F-064. `BACKLOG.md` lo regenera `init.sh` (ver §4).
- **`ARCHITECTURE.md`**: regla 18 (F-063) con la viñeta «Prompts (F-064)» al final, seguida de 19 (F-053), 20 (F-065)
  y 21 (F-070) de `dev`, intactas (diff contra `d79b3d9`: solo +21 líneas dentro de la 18).
- **Inventario de mutación**: 37 filas (36 de `dev` + F-064), recuento al día; la fila de F-064 no cambia de contenido.
- **`rutas_sensibles.json` y `test_f011_r19_r20`**: solo las dos rutas de F-064 sobre lo de `dev`.

## 2. O1: lo que aprobó el humano, en su sitio

- **Texto aprobado:** «Si no puedes leer con seguridad al emisor, conserva lo de fase 1 salvo que sea una empresa del
  cliente (entonces CIF null)».
- **Texto aplicado** (`revision_rules.yaml:130-132`, viñeta de «Acción:» de `proveedor_emisor`): «Si no puedes leer con
  seguridad al emisor, conserva lo de fase 1, salvo que sea una empresa del cliente: entonces deja proveedor_cif en
  null.» Mismo sentido; solo cambia «CIF» por el nombre del campo, que es el vocabulario del resto de la regla. Correcto.
- **Sitio:** entre «corrígelos… / deja proveedor_cif en null» y «Si son correctos, cópialos tal cual». Es donde debe ir:
  distingue «emisor legible sin CIF» (null, viñeta anterior) de «emisor ilegible» (conservar), y no pisa la de copiar.
- **Llega a los cuatro prompts de fase 2** (es, hormigón, mortero, residuos) por `{revision_rules}`, sin editarlos;
  el test parametrizado lo comprueba con y sin contexto de Sigrid (una sola aparición, dentro de la regla).
- **Al día:** design §5 (literal + nota de origen), R9 de `requirements.md` y ARCHITECTURE regla 18. Sin texto de
  cliente escrito a mano en el YAML (sigue llegando por `{prompt_fase_1}`).
- **RED reproducida** en una copia (`git archive bea97f4` en el scratchpad, con el YAML de `bea97f4~1`, venv del árbol
  principal y `PYTHONPATH` a la comun del worktree): `6 failed, 26 passed`, los 6 de O1, idéntico al informe
  (§8 de `impl_F-064.md`). Con el YAML de `bea97f4`: `32 passed`.
- **Control negativo reproducido** (misma copia): la viñeta movida detrás de «Si son correctos» ⇒ `1 failed, 5 passed`
  con `-k o1`; cae el test de orden del YAML. El test de los cuatro prompts solo fija el orden contra la primera y la
  última frase de la regla, pero el del YAML ya fija el sitio exacto: suficiente.

## 3. Mutación (RM1–RM6 sobre el delta)

- **0 líneas mutables es correcto.** `alcance_de_feature("F-064", base="bea97f4~1", rama="bea97f4")` ⇒ 0 ficheros,
  0 líneas: el delta de O1 es YAML, un test y Markdown; el generador solo muta Python de producción. No es un cero
  sospechoso: no hay `.py` de producción en el delta (prueba de control innecesaria por construcción).
- **RM1:** recalculado `alcance_de_feature("F-064", base="dev", rama="HEAD")` tras la fusión ⇒ **7 ficheros, 961
  líneas**, idéntico a `544113b..0ffa0d4` (la campaña). `git diff --stat 0ffa0d4 HEAD` sobre `application/`,
  `settings.py`, `interface_adapters/` de sv2 y `evals/` sale vacío: la campaña de `0ffa0d4` sigue midiendo lo que se
  revisa. No hay que repetirla.
- **RM2/RM3:** sin campaña nueva, nada que recalcular. **RM5:** sin equivalentes nuevos; el #28 consta aceptado por el
  humano (2026-10-15) en `review_F-064.md` §«Aceptación del humano» y en `mutacion_F-064.md`. **RM6:** N/A justificado:
  el delta no quita ninguna guarda (no toca Python de producción).
- El YAML no es mutable por la herramienta: lo que mide si la IA obedece la cláusula son T9 y T10 (C4 ter).

## 4. `bash harness/init.sh` en el worktree

Ejecutado **tal cual y sin caché**: borré antes las `.arnes_cache/suite_*.ok` del worktree. F-064 no cambia la comun
(`git diff d79b3d9 HEAD -- services/albaranes-comun` vacío) y el árbol principal está limpio en `d79b3d9`, así que
la comun que importan los intérpretes es byte a byte la de la rama: no hizo falta un venv aparte. **rc 0, `ENTORNO
LISTO`**, sin ningún `[KO]`.

| Suite | Resultado |
|---|---|
| raíz | 1163 passed (309 s) |
| sv1 / sv2 / sv3 | 205 / **468** / 703 passed |
| sv4 / sv5 / sv6 | 1427 passed, 1 warning / 43 / 295 passed |
| sv9 / comun | 654 passed / 578 passed, 3 skipped |
| PUERTA COBERTURA | `[OK]` 98,9 % (350/354, umbral 80 %, `critico`) |
| PUERTA TAMAÑO | `[OK]` impl 217/220, review 140/140 |
| PUERTA RUTAS SENSIBLES | `[AVISO]` falta la evidencia de 4 rutas: el esperado, T9/T10 |

Avisos previos que no son de F-064: features `blocked` (F-053, F-070), deuda de ruff, `infra` sin tests, marcas
`[ADAPTAR]` de F-034/F-035. `BACKLOG.md` sin cambios tras regenerarlo; `git status` limpio salvo este informe.

## 5. Checkpoints del delta y condiciones de cierre

- [x] C1 trazabilidad: O1 → R9 → `test_f064_o1_*` (3 funciones, 6 casos), en verde.
- [x] C2 diseño: solo `revision_rules.yaml`, el test de IA2 y docs; los prompts de fase 2 sin editar (D de design §5).
- [x] C3 convenciones: primera línea con ruta en los ficheros tocados; sin secretos; sin prints.
- [x] C3 bis / C4: RED con salida real (reproducida); suite y `init.sh` en verde (§4).
- [x] C4 bis: alcance recalculado, 0 líneas en el delta; campaña previa vigente (RM1).
- N/A C4 ter (ruta sensible), justificado: su evidencia son las evals con LLM real (T9/T10), que son MANUAL del humano
  y no las lanza ningún agente; queda como condición de cierre (abajo): no bloquea el veredicto, sí el `done`.
- [x] C5: T0–T8 y T11 `[x]`; T9, T10 y T12 abiertas por ser MANUAL del humano (como en la pasada 1); commits
  `F-064 …`; `current.md` al día con O1 y la fusión.

**Condiciones de cierre que quedan** (sustituyen a las de §5 de `review_F-064.md`):

1. **T9 y T10 sobre `9bb238d`** (o posterior sin cambios en sv2 ni `evals/`). El sv2 y `evals/` de `9bb238d` son
   byte a byte los de `bea97f4` (`git diff --stat bea97f4 9bb238d` solo lista `progress/`). Como O1 toca
   `revision_rules.yaml` (ruta sensible), **`progress/evals_F-064.md` debe ser posterior a `bea97f4`**: la referencia
   «posterior a `8814e4f`» de §5.2 de `review_F-064.md` queda sustituida por esta.
2. Lo demás de §5 de `review_F-064.md` sigue en pie (T9 con el AVISO de la base, `init.sh` en verde en el árbol
   principal tras fusionar, quitar la junction antes de `git worktree remove`). El #28 ya está cerrado.

## 6. Observaciones (no bloquean)

- **OB1 (cosmética, del implementer en mi informe):** al unir líneas para hacer sitio, el punto 6 de §1 de
  `review_F-064.md` quedó pegado al final del punto 5 (línea 41: «…(nivel `critico`). 6. **Puerta…»); en Markdown deja
  de ser un elemento de lista. Sin pérdida de texto. Que el líder lo deje como está o lo parta al cerrar.
- **OB2 (semántica, para T9):** en la duda con una empresa del cliente, la cláusula solo anula el CIF; el
  `proveedor_nombre` de fase 1 puede quedar como «Construcciones Ruesma». Es lo que aprobó el humano y aguas abajo no
  hace daño: sv3 excluye los CIF propios también de la búsqueda por nombre (F-063, ARCHITECTURE regla 18). Si en T9
  aparece así, no es un fallo de O1.
