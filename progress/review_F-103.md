<!-- progress/review_F-103.md -->
Revisión incremental desde a01c0ad (pasada 2): `a01c0ad..cf0a090` (`0006ae7`, `cf0a090`, solo `progress/verif_F-103.md`).
Lo aprobado en la pasada 1 (§1, §3, §4 y la tabla de checkpoints de aquella revisión) queda dado por bueno; el delta no
toca nada que lo invalide (ni código, ni otro fichero, ni el alcance).

# F-103 · Review del cierre sin código

- **Veredicto:** APPROVED
- **Nivel de rigor:** `critico`, declarado en `harness/features.json`. Fase RED, cobertura y mutación son **N/A
  justificadas**: el diff de la feature (`dev...HEAD`) es un único `.md` de `progress/`, sin código, SQL ni tests; no
  hay nada que pueda fallar en RED, ni líneas que cubrir, ni mutantes que generar. Lo que `critico` exige aquí es que la
  evidencia de producción sea completa y que no quede alcance de la ficha sin decidir: ahora se cumple.
- **`bash harness/init.sh`** (entero, también en esta pasada): exit 0, «ENTORNO LISTO» (1919 passed en la raíz, 13 min 42 s;
  servicios en verde por caché). Las puertas de cobertura, rutas sensibles y tamaño las midió sobre F-100, la feature que
  `init.sh` toma como en curso; sobre este diff no habría nada que medir.

## Cambios requeridos en la pasada 1 → estado

| # | Pedido | Hecho en | Estado |
|---|---|---|---|
| 1 | Declarar qué pasa con el detector (alcance 3) y los campos explícitos de sv9 (alcance 4), y por decisión de quién | párrafo «Fuera de F-103»: caen porque F-015 monta la cabecera por lista blanca; confirmado por el humano el 2026-10-28 («todo a») según el líder | [x] |
| 2 | `horfac` y `antestfac` en la tabla | fila `fecfac`/`horfac`/`antestfac`/`estfac`: 0/0/0/0 en las 12; en las 5, `horfac` ≠ 0, `antestfac` 3, `estfac` 1 | [x] |
| 3 | Confirmar 30770, 30820 y 30821 en `dbo.log` o dar el argumento | lectura de `dbo.log` (`tab` = `con`, por `ide`) de las cinco: filas `ope` 5 (y `ope` 30 en 30820/30821) con `ide` posterior a la `ope` 1 del alta; más el argumento de `estfac` = 1 | [x] |
| 4 | Frase «las 12 escritas desde el 26-10 por la tarde» | «las 12 restantes (30819 y las 11 del 28-10)» | [x] |

Comprobaciones sobre el delta:

- Las cuentas cuadran: 5 con `fecfac` (30675, 30676, 30770, 30820, 30821) + 12 restantes = 17 escritas; con la
  `alta_a_mano` son las 18 de `albaran_altas_sigrid`.
- La lectura de `dbo.log` ordena por `ide`, no por `hor`, como manda lo aprendido el 2026-10-27 (la hora de la
  interfaz es la del puesto). Por eso «27-10 de madrugada» en 30820/30821 no es un indicio contra la atribución.
- La confirmación del humano consta en el fichero con fecha y cita; no la puedo ver en el chat del líder y la doy por
  buena según su mensaje. La frase final del párrafo («Si el humano quiere el detector…») ya sobra tras el «todo a»,
  pero no confunde: no se pide quitarla.
- Sin secretos ni datos de terceros en el delta: ni logins, ni nombres, ni emails, ni URL. «Modificaciones de usuario
  desde la interfaz» es la forma pedida.

## Lo recomendado en la pasada 1 (plantilla con `idefac` ≠ 0 y grupo «otras»)

**No bloquea.** Era la prueba de R19 de la spec v1, que no se fusiona, así que no es exigible. La evidencia que hay
basta para la conclusión: con la lista blanca de F-015 ninguna fila de cabecera se clona, y antes del arreglo 12 de 46
altas (26 %) salían con `idefac` ajeno; que las 17 posteriores salgan todas con `idefac` 0 y las 12 sin facturación con
`fecfac`/`horfac`/`antestfac`/`estfac` a 0 sería muy improbable si la herencia siguiera. Probar el caso adverso es
responsabilidad de los tests de F-015 en sigrid-api, no de albaranes. Si algún día reaparece el síntoma, esa prueba es
la primera que hay que hacer: conviene que el resumen de `history.md` lo diga en una línea.

## Checkpoints (pasada 2, solo lo que el delta puede cambiar)

| Checkpoint | Estado | Motivo |
|---|---|---|
| C1 `init.sh` en verde | [x] | ver cabecera |
| C2 una sola `in_progress` | [x] | F-103 sigue `blocked` hasta que el líder la cierre |
| C3 secretos | [x] | delta revisado; sin secretos ni datos personales |
| C3 bis documentos de fuera | N/A | no entra ningún PDF ni ofimática |
| C4 requisito → evidencia | [x] | toda la tabla de alcance de la ficha tiene evidencia o decisión escrita (cambios 1–3) |
| C4 bis RED / cobertura / mutación / RM1–RM6 / Evidencias | N/A | sin código ni SQL versionado (justificado arriba) |
| C4 ter rutas sensibles | N/A | el diff no toca ninguna ruta declarada |
| C5 `tasks.md` | N/A | es de la spec v1, que no se fusiona; ninguna de sus tareas queda pendiente en albaranes (pasada 1, §3, con el detector ya fuera por decisión del humano) |
| C5 sin temporales | [x] | los dos `??` del árbol son de F-083 y F-051 |
| C5 `features.json` real | N/A | lo pasa a `done` el líder tras este APPROVED (abajo) |

## Corrección propia: un login entró en la historia por esta review

La pasada 1 (`a01c0ad`) escribió en este fichero, al comprobar el punto 4, el login literal que el líder pedía que no
apareciera. Ya no está en el fichero, pero sigue en el commit `a01c0ad` de esta rama (local, sin push). Fallo del
reviewer, no del cierre. Para que no llegue a `dev`: **fusionar `chore/F-103-cierre` con `git merge --squash`** (un solo
commit con el árbol final, sin `a01c0ad`) y borrar la rama después con `git branch -D chore/F-103-cierre`; o, si el
humano prefiere conservar los commits, reescribir `a01c0ad` antes de fusionar. Lo decide el humano.

## Qué falta para `done` (lo hace el líder)

- `harness/features.json`: F-103 `blocked` → `done`, sin tocar `rigor`.
- `progress/history.md`: resumen con la decisión del 24-10 (no se limpia), F-015 de sigrid-api (`60db955`, 24-10
  18:21:18 UTC), el resultado de las 17, lo que queda fuera por el «todo a» del 28-10 (detector y campos de sv9), que la
  spec v1 no se fusiona y que su Bloque C lo absorbió F-104; más la línea de la prueba del caso adverso (arriba).
- `progress/current.md`: quitar el bloque F-103 y la viñeta «Para F-103, al retomarla» del bloque F-104.
- Rama `feature/F-103-alta-sin-facturacion-heredada` y worktree `../albaranes-F-103`: conservar como archivo o borrar;
  antes de `git worktree remove`, quitar la *junction* `.venv` de sv4 con `cmd /c rmdir`.
- Fusionar `chore/F-103-cierre` en `dev` según la sección anterior.
