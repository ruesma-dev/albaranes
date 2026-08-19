<!-- specs/F-035-instalador-no-pisa-estado/tasks.md -->
# F-035 · Tareas

**Dos repositorios.** Cada tarea dice en cuál se hace y cada una es un commit
en **ese** repositorio. Convención de mensaje en `arnes-base`, que no usa el
arnés y no tiene features: `F-035 Tn: <qué>` igual que aquí, para poder
cruzarlos. Sin `push` en ninguno de los dos salvo petición del humano.

Leyenda: **[AB]** = `C:\Users\pgris\PycharmProjects\arnes-base` ·
**[ALB]** = `C:\Users\pgris\PycharmProjects\albaranes`.

---

## Fase 0 · Preparación

- [ ] **T1 [AB]**: Confirmar el punto de partida: `git status` limpio,
      `git log -1` = `9224a5a` (1.5.2) o posterior si F-034 ya cerró, y
      `arnes-base/harness/VERSION` leído (fija el MINOR de T14, §8 del diseño).
      **Verificación**: `git -C ...\arnes-base status --porcelain` vacío y
      `cat arnes-base/harness/VERSION` pegado en `progress/impl_F-035.md`.
      Sin commit.

## Fase 1 · RED — reproducir el incidente en un banco de pruebas

- [ ] **T2 [AB]**: Crear `tests_instalador/prueba_instalador.ps1` con el andamio
      (montaje/limpieza del repo de mentira, `Assert-Igual`, contador,
      `exit 1`) y **solo el caso P1**: sembrar `harness/features.json` con 7
      features, ejecutar `-Modo actualizar -Forzar`, comprobar que siguen
      siendo 7. Crear `tests_instalador/README.md`.
      **Verificación**: `powershell -NoProfile -File tests_instalador\prueba_instalador.ps1`
      **FALLA** contra el instalador actual, con el mensaje de P1 y salida ≠ 0.
      Pegar la salida en `progress/impl_F-035.md`: es la fase RED.

- [ ] **T3 [AB]**: Añadir los casos P2, P6, P9, P11 y P12.
      **Verificación**: la prueba falla en P1, P2, P6, P11 y P12, y **pasa**
      P9 (el modo `instalar` ya es seguro hoy: si P9 falla, el diagnóstico de
      la spec es incorrecto y hay que parar y avisar).

## Fase 2 · La política

- [ ] **T4 [AB]**: Crear `politica_ficheros.json` en la raíz con las cuatro
      listas del diseño §3 (UTF-8 sin BOM, LF).
      **Verificación**:
      `powershell -NoProfile -Command "Get-Content politica_ficheros.json -Raw | ConvertFrom-Json | Out-Null; 'ok'"`.

- [ ] **T5 [AB]**: En `instalar_arnes.ps1`, añadir `Get-Politica` y
      `Get-CategoriaFichero` (resolución por especificidad, R3) y
      `Test-PayloadClasificado` (R4), ejecutado antes de cualquier escritura.
      Sustituir `$Excluidos` (línea 32) por la lista `excluidos` de la política
      (R24). Todavía sin cambiar el comportamiento del recorrido.
      **Verificación**: añadir el caso **P10** a la prueba (payload con una
      ruta sin clasificar ⇒ aborta ≠ 0 y no escribe) y verlo **pasar**; P12
      (`__pycache__` fuera) pasa también.

- [ ] **T6 [AB]**: Añadir el caso **P3** (fichero de categoría (a) sí se
      actualiza) a la prueba.
      **Verificación**: P3 pasa contra el comportamiento actual (hoy `-Forzar`
      ya lo pisa). Queda como red de no-regresión de T7.

## Fase 3 · El comportamiento por categoría

- [ ] **T7 [AB]**: Reescribir el recorrido del payload (líneas 113-186) según
      el diseño §5: `estado` ⇒ `protegido`, ni diff ni pregunta ni escritura
      (R9, R10); `puro` ⇒ se aplica sin preguntar salvo `-PreguntarTodo`
      (R11, R12); `adaptado` ⇒ diff y pregunta; ausente ⇒ se copia sea cual sea
      su categoría (R16). Añadir `-PreguntarTodo` al `param`.
      **Verificación**: P1, P2 y P3 pasan. **P1 es la prueba de fuego: 7
      features siguen siendo 7 tras `-Forzar`.**

- [ ] **T8 [AB]**: Diálogo con default en CONSERVAR: prompt nuevo, Intro ⇒
      conservar a la primera (R13, R14), guardarraíl no interactivo intacto
      (R15). Añadir el caso **P4**.
      **Verificación**: P4 pasa (entrada redirigida a vacío ⇒ `CLAUDE.md`
      conserva su marcador).

- [ ] **T9 [AB]**: `Test-MismoContenido` con normalización CRLF/BOM para
      extensiones de texto y tercer estado `solo-eol` (R23).
      **Verificación**: P11 pasa. Comprobar además que un `.png` o `.pdf`
      sembrado en el destino sigue comparándose por SHA-256 (no se normaliza
      binario).

## Fase 4 · Backup y precondiciones

- [ ] **T10 [AB]**: `New-DirectorioBackup`, `Backup-Fichero`,
      `Write-Manifiesto` y el parámetro `-DirBackup` (R17-R22). Ninguna
      escritura destructiva sin backup previo; abortar si no se puede crear el
      directorio; fichero suelto que falla ⇒ se conserva y salida ≠ 0. Añadir
      el caso **P5**.
      **Verificación**: P5 pasa (existe el backup con sello, contiene la
      versión **previa** de `.claude/agents/leader.md`, el `MANIFIESTO.md` lo
      lista con rama y commit).

- [ ] **T11 [AB]**: `Test-Precondiciones` (R25, R26, R27, R28) y el parámetro
      `-IgnorarPrecondiciones`. Añadir los casos **P7** y **P8**.
      **Verificación**: P7 y P8 pasan (sucio en ruta tocada bloquea; sucio en
      `services/algo.txt` no bloquea; `-IgnorarPrecondiciones` desbloquea).

- [ ] **T12 [AB]**: Resumen final con `protegidos`, `solo finales de línea` y
      `no aplicados (fallo de backup)`, listado de rutas protegidas, ruta del
      backup (R29, R30, R22), y `-SoloDiff` sin escribir nada pero mostrando
      los protegidos (R31). Texto de `harness/ARNES_VERSION.md` corregido
      (R38).
      **Verificación**: P6 pasa (`Protegidos: 4` y las cuatro rutas listadas).
      La prueba completa (P1-P12) en verde:
      `powershell -NoProfile -File tests_instalador\prueba_instalador.ps1`
      ⇒ salida 0. Pegar la salida en `progress/impl_F-035.md`.

## Fase 5 · Mutación manual y cierre en `arnes-base`

- [ ] **T13 [AB]**: Campaña de mutación **manual**, 6 mutantes M1-M6 del
      diseño §7.3, cada uno aplicado a mano, prueba ejecutada y revertido.
      **Verificación**: tabla en `progress/mutacion_F-035.md` (en `albaranes`)
      con el **texto exacto original → mutado** de cada sustitución, el caso
      que lo mata y la salida. Un superviviente = caso de prueba nuevo antes
      de seguir. Sin commit en `[AB]`; el commit es en `[ALB]`.

- [ ] **T14 [AB]**: Subir `arnes-base/harness/VERSION` al MINOR siguiente al
      leído en T1 (1.7.0 si F-034 cerró como 1.6.0; ver diseño §8) con su
      `ARNES_FECHA`, y escribir en `GUIA_INSTALACION.md` la sección de la
      versión nueva (tres categorías, política, backup, precondiciones,
      parámetros nuevos) más la corrección del párrafo «Qué conservar casi
      siempre» de la sección C (R35, R36, R37).
      **Verificación**: `grep -n "protegid\|politica_ficheros\|IgnorarPrecondiciones\|DirBackup\|PreguntarTodo" GUIA_INSTALACION.md`
      devuelve resultados en la sección nueva, y `cat arnes-base/harness/VERSION`
      muestra el número acordado.

## Fase 6 · Rastro y cierre en `albaranes`

- [ ] **T15 [ALB]**: Escribir `progress/impl_F-035.md`: fase RED (salida de
      T2 en rojo), salida final en verde de T12, tabla de mutación de T13, y
      **los hashes de los commits de `arnes-base`** (T2-T14) para que el
      reviewer pueda comprobarlos con
      `git -C C:\Users\pgris\PycharmProjects\arnes-base log --oneline`.
      Actualizar `progress/current.md`.
      **Verificación**: el fichero existe y sus hashes casan con
      `git -C ...\arnes-base log`.

- [ ] **T16 [ALB]**: Ejecutar la verificación MANUAL del diseño §7.4.
      **Verificación**: **MANUAL (humano)**. Desde
      `C:\Users\pgris\PycharmProjects\arnes-base`, en `albaranes` con una rama
      limpia creada desde `dev`:
      `.\instalar_arnes.ps1 -Destino "C:\Users\pgris\PycharmProjects\albaranes" -Modo actualizar -SoloDiff`
      y comprobar que aparecen como **protegidos** `harness/features.json`,
      `docs/ARCHITECTURE.md`, `progress/current.md` y `progress/history.md`, y
      que los «distintos» bajan de 13 a 5. `-SoloDiff` no escribe nada.
      *(Aplicar de verdad la versión nueva a `albaranes` **no** es parte de
      F-035: lo decide el humano después.)*

- [ ] **T17 [ALB]**: Ejecutar `bash harness/init.sh` en verde.
      **Verificación**: `bash harness/init.sh` termina en ENTORNO LISTO.
      *(Recordatorio del diseño §0: aquí no hay líneas Python cambiadas, así
      que las puertas de cobertura y mutación no tienen sujeto en este
      repositorio; la evidencia real son T12 y T13.)*
