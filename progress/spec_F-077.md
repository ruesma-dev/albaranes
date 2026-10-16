<!-- progress/spec_F-077.md -->
# F-077 · Ficha: guardar y aprobar de una vez · resumen de la spec (spec-author, 2026-10-16)

Spec: `specs/F-077-guardar-y-aprobar/` (requirements 120/150 líneas, design 214/250, tasks T1–T15). Rama
`feature/F-077-guardar-y-aprobar`, worktree `C:\Users\pgris\PycharmProjects\albaranes-F-077`. Estado `spec_ready`,
prioridad 1, rigor **estandar**, servicio **sv4** únicamente.

## 1. Alcance (PARADA 1 aprobada por el humano el 2026-10-16, ampliada el mismo día con el punto 4)

| Punto | Requisitos | En una frase |
|---|---|---|
| 1 · Guardar y aprobar | R1–R13 | Guarda antes las filas con cambios (mismo PATCH por fila y R27 v5); si una falla, para y no aprueba; «Guardar» igual sin aprobar |
| 2 · Panel del alta | R14–R19 | «Alta en curso…» sin resultado viejo ni botones mientras la aprobación vigente no tenga respuesta de sv9; sondeo de una ruta de solo lectura y recarga |
| 3 · Tooltip del ⚠ | R20–R22 | «No coincide con la partida leída en el albarán (X)» |
| 4 · Motivos de línea | R25–R28 | Los que no caben en la tabla del panel salen en la lista como «Línea N: texto legible» (caso del documento `86c13097-…`) |

## 2. Decisiones tomadas en la spec (el detalle, en design §9)

- **D1** Parar al primer PATCH que falla (no seguir como «Guardar todas»).
- **D2** Tras un fallo no se recarga: las filas guardadas se **consolidan** (valor inicial = enviado, casillas
  desactivadas) para que un reintento no las reenvíe (el servidor daría 409 «Línea guardada…»).
- **D3** El aviso de suma se **relee** del servidor (`GET /api/documents/{id}`, `aviso_suma`) cuando se guardaron
  filas: el pintado al cargar ya no vale. Si la lectura falla, no se aprueba y se recarga.
- **D4** «Pendiente» = sin fila de sv9, o fila repetible de una aprobación anterior, o `en_curso` de la vigente;
  **acotado por la Espera** (15 min). Ver P1.
- **D5** Al llegar el resultado se recarga la página entera (la ficha aprobada es de solo lectura: no se pierde nada).
- **D6** Una sola función de PATCH de fila en `app.js` para los tres guardados (hoy hay dos copias de la petición y
  de la lectura del motivo).
- **D7** «Línea N» usa la posición en la tabla de la ficha (filas con conciliación, como F-065 R20); si no casa,
  «Línea (ref. <id>)». El `referencia_linea` de sv9 es el id de la línea valorada, que el administrativo no ve.

## 3. Tests de F-065 que cambian (design §6)

- `test_f065_f1_js.py`: se borra `test_f065_r19_js_aviso_de_filas_sin_guardar` (la función desaparece) y
  `test_f065_r19_guardar_y_aprobar_miran_las_filas_sucias_antes_del_put` (pasa a `test_f077_r1_…`); los dos R18 pasan a
  `filasConCambios`; R21 se mantiene.
- `test_f065_f3bis_front.py`: `test_f065_r27v5_guardar_y_aprobar_marca_la_partida_mala` espera la alerta de partidas no
  válidas en vez de «Hay 1 línea…» (sigue sin enviar nada); `_GUARDAR` y `_FICHA` cambian de lista de funciones.
- Ningún test de F-053 cambia de expectativas (los campos nuevos valen `False`/vacío por defecto).

## 4. Preguntas abiertas para el humano (con la opción por defecto que sigue la spec)

- **P1 · Cota de «Alta en curso…».** El coordinador pidió: mientras la aprobación sea más reciente que la fila de sv9
  (o no haya fila), sin «Solicitar alta» y con «Alta en curso…». La spec añade dos condiciones: (a) solo con estados
  que sv9 vuelve a procesar (con `ya_en_sigrid` sv9 ignora la nueva aprobación y la fila vieja es la respuesta
  definitiva: sin la condición, «en curso» hasta la cota sin que pase nada); (b) como mucho la Espera (15 min) desde la
  aprobación: si la publicación se perdió, vuelve el panel de hoy con «Solicitar alta». **Por defecto: con las dos.**
  Quitar cualquiera es borrar una condición de `alta_pendiente`.
- **P2 · Filas sin línea del albarán** (sintéticas, manuales, repartos): su ⚠ compara la partida final con la de su
  línea de contrato, no con nada leído. **Por defecto:** «No coincide con la partida de su línea de contrato (X)».
- **P3 · Texto legible de los motivos del documento** (`falta_obra`, `fecha_no_plausible`…): fuera del encargo.
  **Por defecto:** siguen con su código, como hoy; la tabla de textos de R27 se puede ampliar después sin rediseño.
- **P4 · Intervalo del sondeo.** **Por defecto:** 3 s el primer minuto y 15 s después.

## 5. Riesgos

- No atómico (aceptado): si falla la aprobación, las filas guardadas quedan guardadas y bloqueadas.
- «Guardar» con `?buscar_si_cambia=1` puede relanzar la búsqueda y la revaloración descarta lo editado (F-058): es
  lo de hoy.
- «Solicitar alta» sin reaprobar no se ve como «en curso» hasta que sv9 marca `en_curso`; el listado (F-053 R31) sigue
  pintando el estado guardado. Fuera de alcance.
- El JS no lo mide la campaña de mutación (solo Python); lo cubren los tests con node.
- Rigor `estandar` y no `critico`: no cambia lo que se aprueba ni lo que recibe sv9, solo el orden de acciones en el
  cliente que ya existían y lo que se pinta.

## 6. Solapes con otras ramas

- **F-076** (spec en curso, sin commits): su R15 rehace `/api/sigrid/partidas` desde comun con los mismos `items`;
  F-077 solo los consume. Con F-076, una lectura `CI.04.18` normalizada a `CI.4.18` sigue dando ⚠ (y el tooltip de
  R20 lo explica); si F-076 decide que lo equivalente no avisa, cambia `agree_partida`, no F-077. Posible conflicto de
  texto en `review_repository.py` junto a `agree_partida` si F-076 lo toca.
- **F-068** (pendiente): `wireDividir`/F7 en `app.js`, otra zona. **F-058**: sin relación directa.
- `azure-apps/albaranes.md` no cambia: la ruta nueva solo la usa el JS de sv4.
