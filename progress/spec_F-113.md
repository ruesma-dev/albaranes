<!-- progress/spec_F-113.md -->
# F-113 · Informe de la spec (v1, 2026-10-30)

Autoría: el spec-author redactó `requirements.md` y `design.md` y se cortó por el límite semanal de la API antes de
escribir `tasks.md` y este informe. Los ha terminado el líder sin delegar, con permiso del humano («continua»).
Además, el líder ha cambiado la versión de comun de 0.10.0 a 0.9.1 (D-8), porque F-106 ya usa la 0.10.0 en su rama.

## Diagnóstico (líder, solo lectura, 2026-10-30)

- Correo de la obra 0728, recibido a las 10:01:52 UTC, con 5 fotos de FEYMACO («WhatsApp Image …jpeg»).
- sv1 abrió 5 `workflow_runs` a las 10:02:29, que siguen en `email_received`; no hay ninguna fila en
  `albaran_documents`.
- Logs de `ca-sv2-extraccion`: IA1 escribe el `phase_1` y después IA2 (OpenAI) devuelve 400 «unsupported MIME type
  'application/octet-stream'». Es un error no reintentable, y aun así se reintentó: a las 11:24 iba por el intento
  3/5. Al quinto, el mensaje va a poison.
- Causa: Graph declara `contentType` = `application/octet-stream` y sv1 lo propaga tal cual.

## Decisiones para la PARADA 1 (`design.md` §8)

| Decisión | Recomendación |
|---|---|
| D-1 | Manda la firma de bytes |
| D-2 | Se detectan TIFF y HEIC; HEIC no se convierte |
| D-3 | No se filtran los adjuntos que no son ni imagen ni PDF |
| D-4 | Ir a poison sin agotar los intentos queda fuera: feature aparte |
| D-5 | El humano reenvía el correo |
| D-6 | Medición en solo lectura antes del despliegue y a las 24 h |
| D-7 | La clave del blob sigue siendo `input/{id}.pdf` |
| D-8 | Comun 0.9.1, y F-113 entra en `dev` antes que F-106 |

## Pendiente

- PARADA 1 con el humano.
- Pasar a `spec_ready` en `chore/alta-F-111-F-112`.
- Implementar: los subagentes no tienen cuota hasta el 2026-11-01 a las 23:00; si el humano lo pide, lo hace el líder.
