<!-- specs/F-104-codigos-contrato-v83/requirements.md -->
# F-104 · sv9 y sv4 entienden los códigos del contrato v8.3 de sigrid-api · Requisitos (v1)

Servicios: **sv9** (`albaranes-alta-sigrid`: la tabla del clasificador) y **sv4** (`albaranes-front`: textos y panel).
Rigor `critico`. Ficha en `harness/features.json`; nace de la D6 de F-103 (rama
`feature/F-103-alta-sin-facturacion-heredada`, `design.md` §8), que aquí se amplía de un código a cinco.

Fuente (se enlaza, no se copia; dueño sigrid-api, solo lectura): contrato v8.3,
`sigrid-api/specs/F-009-alta-albaran-compra/contrato_albaranes.md` en el commit `871cc0c` de su rama
`feature/F-015-albaran-plantilla-y-retencion` (§3.2 avisos, §3.3 errores), y su resumen
`sigrid-api/progress/t0_F-015_albaranes.md` (tabla «Códigos»). El acuse se envió el 2026-10-24 con los mapeos de abajo,
decididos por el humano: no se reabren.

## Glosario
- **Errores v8.3**: los códigos de cabecera `proveedor_no_encontrado`, `proveedor_ambiguo` y `retencion_no_soportada`.
- **Avisos v8.3**: los avisos de cabecera `retencion_del_contrato` y `cabecera_sin_dato`.
- **Código retirado**: `proveedor_sin_albaran_previo` (la v8.3 deja de devolverlo; la v8.2 desplegada aún puede).
- **Despliegue de F-015**: la imagen de sigrid-api que publica la v8.3. Lo anuncia su sesión; lo despliega el humano.

## A. Clasificador de sv9
R1. CUANDO sigrid-api responda 400 con `details.codigo` igual a uno de los Errores v8.3, en la previa o en la
grabación, sv9 debe clasificar el alta como `no_admitido` (hoy, por desconocido, va a `error`: F-053 H25), con ese
código como motivo de cabecera y el `error` de sigrid-api como detalle (`motivos_de_error`, sin cambios).
R2. MIENTRAS no se haya hecho la verificación de R14 y la retirada de R10, `CODIGOS_CABECERA` debe seguir llevando el
Código retirado a `no_admitido`.
R3. El resto de `CODIGOS_CABECERA` y todo `CODIGOS_LINEA` no deben cambiar, y un código que no esté en la tabla debe
seguir yendo a `error` (H25).

## B. Avisos de sv9
R4. El defecto de `ALTA_SIGRID_AVISOS_BLOQUEANTES` debe seguir siendo `producto_sin_historico` y no incluir ningún
Aviso v8.3; ni `infra/*.ps1` ni `services/albaranes-alta-sigrid/.env.example` deben mencionar los Avisos v8.3.
R5. CUANDO la previa traiga Avisos v8.3 en `avisos[]` de cabecera y la configuración sea la de por defecto, la
comparación no debe añadir ningún motivo por ellos (ningún `aviso_bloqueante`), y sv9 debe guardarlos con su `codigo` y
su `mensaje` en `avisos_json` del alta, sea esta `simulado`, `revisar` o `registrado`.
R6. CUANDO un 200 traiga los campos de la v8.3 (`totales.tot`, `totales.retenciones`, `totales.n_retenciones` y
`filas.dcarec`), sv9 debe clasificarlo y compararlo exactamente igual que sin ellos: la comparación de la previa sigue
por línea y `filas` no se guarda (F-053 R16).

## C. Textos y panel de sv4
R7. `TEXTOS_MOTIVO_ALTA` debe tener, para cada Error v8.3 y cada Aviso v8.3, el texto de design §3.2: no vacío y
distinto del código. El test de F-077 R27 (todo código del clasificador tiene texto) debe seguir en verde.
R8. CUANDO el panel del alta pinte un aviso de Sigrid cuyo código tenga texto en `TEXTOS_MOTIVO_ALTA`, debe enseñar el
texto, a continuación el `mensaje` de sigrid-api (si lo hay) y la línea (si la hay), con el código en el `title`
(D2). Un aviso sin texto debe pintarse como hoy (`<code>codigo</code> · mensaje`).
R9. Los Avisos v8.3 no deben cambiar el estado del alta ni el bloqueo del documento en sv4: se enseñan bajo «Avisos de
Sigrid» y nada más.
R10. CUANDO se haya cumplido R14, sv9 debe quitar el Código retirado de `CODIGOS_CABECERA` (desde entonces, si
llegase, iría a `error` por H25), y sv4 debe conservar su texto en `TEXTOS_MOTIVO_ALTA` (las altas antiguas lo llevan
en `motivos_json`). D1.

## D. Lo que F-104 no hace
R11. F-104 no debe cambiar la petición a sigrid-api (§2 del contrato sin cambios de forma), ni
`domain/services/comparador_previa.py`, ni `ruesma_comun`, ni el DDL de `albaran_altas_sigrid`, ni enseñar
`totales.tot` (neto con retención) en el panel: todo eso queda **fuera**.

## E. Documentación
R12. `services/albaranes-alta-sigrid/sv9.md` debe citar el contrato v8.3 (`871cc0c`) en su cabecera y describir el
mapeo de los cinco códigos y el estado del Código retirado; §10 de `azure-apps/albaranes.md` debe llevar una viñeta
con lo mismo (commit local en `azure-apps`, sin push).

## F. Verificación y despliegue (MANUAL, solo lectura; lo despliega el humano)
R13. Antes de desplegar, el líder debe comprobar en solo lectura que `ca-sv9-alta-sigrid` no lleva ningún Aviso v8.3
en `ALTA_SIGRID_AVISOS_BLOQUEANTES` (design §6, M1).
R14. CUANDO sigrid-api haya desplegado F-015 y sv9 y sv4 ya lleven F-104, el líder debe comprobar en solo lectura, con
el SQL de design §6 (M2) sobre las altas intentadas desde el despliegue: 0 con el Código retirado; los Errores v8.3,
solo en `no_admitido`; ningún `aviso_bloqueante` por un Aviso v8.3; y, con al menos un alta que traiga
`retencion_del_contrato`, que el panel la enseña con su texto (M3).
