<!-- specs/F-038-coste-del-ciclo-sdd/requirements.md -->
# F-038 · Requisitos

Alcance y motivos: ficha `F-038` de `harness/features.json` (fuente única; no
se repite aquí). Las seis reglas de revisión de campañas de la ficha se citan
como **RM1..RM6** para no chocar con los `R` de este fichero.

> Esta spec se somete a sus propios topes: 150 / 250 líneas.

## Bloque A — Infraestructura: hoy no se puede mutar `harness/` (T0)

R1. CUANDO se pide el ejecutor de un fichero que no pertenece a ningún
servicio Python de `harness/servicios.json` y existe el directorio
`<raiz>/tests`, el sistema debe juzgar ese mutante con la suite de la raíz
**acotada a `tests`**.

R2. SI no existe `<raiz>/tests`, ENTONCES el sistema debe invocar la suite de
la raíz sin ruta, exactamente como hoy.

R3. El sistema debe aplicar esa misma ruta acotada a la **línea base**, no
solo a la ejecución de los mutantes.

R4. Dos ejecutores que corren desde la misma raíz con el mismo intérprete pero
distinta ruta acotada deben tener **identidad distinta** (no se deduplican ni
se comparte su línea base).

## Bloque B — Coste de la campaña de mutación

R5. El sistema debe leer de `harness/rigor.json` un `max_mutantes` y una
`semilla` **por nivel de rigor**: `estandar` con tope 20 y semilla fija,
`critico` sin tope, `documental` irrelevante (no exige mutación).

R6. CUANDO se lanza `python -m harness.mutacion --feature F-XXX` sin
`--max-mutantes` ni `--semilla`, el sistema debe aplicar los del nivel de rigor
de esa feature (el declarado, o `nivel_por_defecto` si no declara).

R7. CUANDO se pasan `--max-mutantes` o `--semilla` explícitos, el sistema debe
darles precedencia sobre los del nivel; y `--max-mutantes 0` debe significar
**sin tope**, para poder anular desde la orden el tope de un nivel.

R8. El sistema debe aplicar `estandar` —no `critico`— a las features que no
declaran `rigor`.

R9. SI la campaña se ha muestreado, ENTONCES el informe debe declarar cuántos
mutantes se evaluaron de cuántos generados, la semilla y el nivel que la fijó.

## Bloque C — El informe de mutación trae los datos que hoy cuesta pedir

R10. (RM1) El informe de mutación debe declarar el **SHA completo de HEAD**
contra el que se midió.

R11. (RM2) El informe de mutación debe declarar los **segundos de la línea
base** de cada ejecutor implicado y la **media de segundos por mutante
evaluado**, para que la incoherencia temporal se detecte leyendo, sin
reejecutar nada.

R12. SI el tiempo de la línea base no está disponible (informes agregados de la
campaña paralela sin ese dato), ENTONCES el informe debe imprimir `n/d`, nunca
un cero ni omitir la fila.

## Bloque D — Topes de tamaño del papeleo

R13. `harness/rigor.json` debe declarar los topes de líneas de
`requirements.md` (150), `design.md` (250), `progress/impl_F-XXX.md` (220) y
`progress/review_F-XXX.md` (140). Los topes viven en el fichero de
configuración, nunca cableados en el código.

R14. CUANDO se ejecuta `python -m harness.tamano --feature F-XXX`, el sistema
debe medir esos cuatro ficheros —**solo los que existan**— y salir con código 1
nombrando cada uno que exceda su tope, con su número de líneas real y el tope.

R15. CUANDO se ejecuta `bash harness/init.sh`, el sistema debe aplicar esa
medición **solo a la feature en curso** (la de la rama actual, o la
`in_progress`), y ponerse en rojo si alguno excede. MIENTRAS no haya feature en
curso identificable, la comprobación debe declararse `N/A` con su motivo.

R16. El sistema NO debe medir las specs de otras features: las 12 specs
existentes exceden hoy los topes y no se reescriben (ver «Decisiones», D3 del
design).

## Bloque E — Protocolo de los agentes y checkpoints

R17. `specs/SPECS.md` y los tres agentes (`spec-author`, `implementer`,
`reviewer`) deben declarar los topes de R13 y la regla «lo que no cabe se
resume y se enlaza».

R18. `.claude/agents/reviewer.md` y `CHECKPOINTS.md` deben bajar el umbral de
reejecución obligatoria de la campaña de **5 minutos a 60 segundos**.

R19. `.claude/agents/reviewer.md` debe establecer la **revisión incremental por
defecto**: en la pasada N se revisa `git diff <último commit aprobado>..HEAD`, y
el informe de review declara **desde qué SHA** revisa.

R20. `.claude/agents/reviewer.md` debe recoger RM1..RM6, y `CHECKPOINTS.md`
(C4 bis) debe añadir un checkbox por RM1, RM2, RM5 y RM6. RM5 solo se exige en
rigor `critico` y con **una muestra de un** superviviente elegido por el
reviewer. RM3 y RM4 quedan como criterio de juicio en el agente, sin checkbox.

R21. Ninguna de RM1..RM6 debe convertirse en puerta automática de `init.sh`
(razón en el design, D4): lo que `init.sh` gana es el tope de tamaño, y lo que
la herramienta garantiza son los datos de R10–R12.

## Bloque F — Deuda de los informes medidos con la invocación rota

R22. SI un informe de `progress/mutacion_*.md` midió ficheros fuera de
`services/` con la invocación rota, ENTONCES debe llevar en cabecera un aviso
de que sus números **no valen** y que hay que repetir la campaña. La repetición
NO entra en esta feature (D5).

## Decisiones del humano (2026-08-20) — las tres preguntas, cerradas

1. **Semilla `20260820`**, fija y escrita en `rigor.json` (R5). Dos reviewers
   que remidan la misma feature obtienen los mismos 20 mutantes.
2. **Remedir F-012 NO entra aquí** (se mantiene D5): el aviso de invalidez sí
   (R22), y la remedición se abre como feature propia **F-039**.
3. **`nivel_por_defecto: estandar` se acepta sin revisar fichas**: las 38
   features del backlog **declaran rigor** (30 `estandar`, 8 `critico`), así
   que el cambio no altera el rigor de ninguna feature actual; solo afecta a
   las futuras que omitan declararlo.
