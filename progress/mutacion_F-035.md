<!-- progress/mutacion_F-035.md -->
# F-035 · Campaña de mutación (MANUAL, sobre PowerShell)

`python -m harness.mutacion --feature F-035` **no tiene sujeto en este
repositorio**: F-035 no cambia una sola línea de Python en `albaranes` (todo el
código vive en `arnes-base`), y el mutador solo muta Python del diff local.
Daría 0 mutantes por falta de sujeto, no por calidad. La evidencia equivalente
es esta campaña manual sobre `instalar_arnes.ps1` y `politica_ficheros.json`,
prevista en `design.md` §7.3.

**Método**: cada mutante se aplica a mano al fichero real, se ejecuta la suite
completa (`powershell -NoProfile -File tests_instalador\prueba_instalador.ps1`)
y se revierte con `git checkout --`. «Muerto» = la suite sale con código ≠ 0 y
nombra el caso. El árbol de `arnes-base` quedó limpio tras la campaña
(`git status --porcelain` vacío).

**Resultado: 7 mutantes, 7 muertos, 0 supervivientes.**

| # | Fichero | Texto exacto original → mutado | Estado | Casos que lo matan |
|---|---|---|---|---|
| M1 | `politica_ficheros.json` | `    "harness/features.json",` → *(línea eliminada de `estado_del_proyecto`)* | MUERTO | P1, P6, P13 |
| M2 | `politica_ficheros.json` | `    "progress/**",` → *(línea eliminada de `estado_del_proyecto`)* | MUERTO | ninguno de P1-P13: lo mata la comprobación de integridad (ver abajo) |
| M2 bis | `politica_ficheros.json` | `"progress/**"` **movido** de `estado_del_proyecto` a `arnes_puro` | MUERTO | **P2**, P6, P13 |
| M3 | `instalar_arnes.ps1` | `    if (-not $patron.Contains('*')) { return 10000 + $patron.Length }` → `    if (-not $patron.Contains('*')) { return 0 }` | MUERTO | P1, P6, P13 |
| M4 | `instalar_arnes.ps1` | en el `default` del diálogo, `                    $respuesta = 'n'` → `                    $respuesta = 's'` | MUERTO | P4 |
| M5 | `instalar_arnes.ps1` | `        if (Backup-Fichero $dest $rel) {` → `        if ($true) {` (rama del arnés puro) | MUERTO | P5 |
| M6 | `instalar_arnes.ps1` | `$sucio = @(& git -C $DestinoAbs status --porcelain -uall -- @RutasAlcance 2>$null` → `$sucio = @(& git -C $DestinoAbs status --porcelain -uall 2>$null` | MUERTO | P8 |

## Análisis de los que no murieron por donde debían

**M2 (el propuesto en el diseño) murió por la vía equivocada, y por eso se
repitió.** Borrar `"progress/**"` de la política no deja `progress/*.md`
desprotegido: lo deja **sin clasificar**, y entonces salta antes
`Test-PayloadClasificado` (R4), que aborta el instalador con código 3 en la
instalación inicial de cada escenario. La suite sale ≠ 0 —el mutante está
muerto— pero por la comprobación de integridad, no por P2. Contarlo como
«muerto en P2» habría sido exactamente el tipo de muerto falso que F-034 acaba
de corregir en `harness/mutacion.py`.

Por eso se añadió **M2 bis**, que mantiene la ruta clasificada pero le quita la
protección (la mueve a `arnes_puro`). Ese sí lo mata P2, con el detalle
esperado:

```
 - P2 - ARCHITECTURE.md y progress/*.md intactos (R9, R40-i) :: progress/current.md conserva su marcador -- no aparece <MARCADOR-CURRENT-NO-PISAR> en la salida
 - P2 - ARCHITECTURE.md y progress/*.md intactos (R9, R40-i) :: progress/history.md conserva su marcador -- no aparece <MARCADOR-HISTORY-NO-PISAR> en la salida
 - P6 - el resumen lista los protegidos (R29, R30) :: el resumen nombra progress/current.md como protegido -- no aparece <[PROTEGIDO] progress/current.md> en la salida
 - P13 - -SoloDiff no escribe nada y aun asi dice que protegeria (R31) :: dice igualmente cuales protegeria -- no aparece <Protegidos: 4> en la salida
```

**M3 no muere en P9, como preveía el diseño, sino en P1, P6 y P13.** P9 (modo
`instalar`) no puede matarlo: ese modo no sobrescribe nada aunque la categoría
esté mal resuelta, así que invertir la precedencia no cambia su resultado. El
mutante muere igualmente, y por el caso que importa (P1, la prueba de fuego).
No es un hueco de la suite: es que la predicción del diseño sobre *qué* caso lo
mataría era optimista.

## Límite declarado

La campaña es manual y no se re-ejecuta sola: no hay CI en `arnes-base` y el
mutador del arnés no muta PowerShell. Si en el futuro se toca
`instalar_arnes.ps1`, hay que repetirla a mano con este mismo guion (queda
escrito arriba, mutante a mutante, para que sea reproducible).
