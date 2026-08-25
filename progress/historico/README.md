<!-- progress/historico/README.md -->
# Histórico de `progress/`

Aquí viven los informes **`impl_*`, `review_*` y `evals_*` de features ya
cerradas** (`done` en `harness/features.json`). Se archivaron el
**2026-08-25**: eran 29 ficheros y **639 KB**, más de la mitad de `progress/`,
y estorbaban la lectura de lo que sigue vivo.

## La regla, y su excepción

- **Al cerrar una feature**, sus informes `impl_`, `review_` y `evals_` se
  mueven aquí. Lo vivo se queda en `progress/`.
- **Las campañas de mutación NO se archivan.** `mutacion_*.md`,
  `inventario_mutacion_F-039.md` y `verificacion_paralela_F-039.md` se quedan
  en `progress/` **a propósito**: F-039 dejó tests que las vigilan por ruta
  fija (`tests/test_f039_r1_r2_r23_r25_documentos.py`) —el inventario tiene
  que llevar una fila por informe en disco, y los avisos de invalidez tienen
  que seguir ahí—. Moverlas pone ocho tests en rojo. Si algún día quieres
  archivarlas, hay que adaptar antes ese test y portarlo a `arnes-base`.
- **No se borra nada.** Archivar es mover, y git conserva el historial completo
  de todas formas.
- **`init.sh` no los lee.** Solo exige `progress/current.md` e `history.md`.
  `harness/tamano.py` sí usa rutas planas (`progress/impl_{feature}.md`), pero
  **solo de la feature en curso**, nunca de una cerrada.
- **Si reabres una feature archivada**, devuelve sus informes a `progress/`
  antes de medirla: `harness/tamano.py` los busca en la raíz.

## Antes de citar nada de aquí

Un informe archivado sigue siendo cierto **para la fecha en que se escribió**.
Si dice que un fichero está en tal línea o que un test se llama de tal forma,
compruébalo contra el código antes de actuar: esto es arqueología, no la
fotografía de hoy. Lo que manda sobre el estado real es `progress/current.md`.
