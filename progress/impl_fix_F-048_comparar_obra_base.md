<!-- progress/impl_fix_F-048_comparar_obra_base.md -->
# F-048 · fix: base del comparador de obra como parámetro (`--base`)

Rama `fix/F-048-comparar-obra-base` (desde `dev` = `2b05ba7`). Problema: los tests del comparador leían la rama `dev`,
que desde el merge de F-048 ya lleva `{contexto_correo}` y `lectura_correo`: `dev` quedaba en rojo.

## Qué cambió
- `evals/procesos/sv2_obra.py`: `RAMA_DEV` pasa a `BASE_POR_DEFECTO = "dev"`; `prompt_de_dev(directorio, raiz, base=...)`
  hace `git show <base>:<ruta>`. Docstring del módulo actualizada.
- `evals/comparar_obra.py`: CLI `--base <ref>` (por defecto `dev`), llega a `prompt_de_dev(..., base=)` y al commit
  de la cabecera. La variante sigue llamándose `dev` en informes y JSON: formato de `progress/comparar_obra_F-048.md` intacto.
- Tests: `test_f048_comparar_obra.py` y `test_f048_comparar_obra_prompt_dev.py` fijan la base a `1807e83` (el `dev`
  de antes de F-048, inmutable), también en el `git archive` del test byte a byte. Dobles con el keyword `base`
  (incluido el doble mínimo de `test_f048_t34b_supervivientes.py`).
- Tests nuevos: `..._base_llega_a_git_show` (doble de `subprocess.run`, sin git real), `..._cli_base_llega_al_prompt_y_al_commit`
  y `..._cli_sin_base_compara_con_dev`.
- `progress/impl_F-048_evals.md`: nota de que repetir la medición pide `--base 1807e83`.

## RED
RED natural en `dev`, antes de tocar nada:
`python -m pytest tests/test_f048_comparar_obra.py tests/test_f048_comparar_obra_prompt_dev.py -q --tb=line`
```
tests\test_f048_comparar_obra.py:446: AssertionError: assert ('{obras_activas}' in ... and '{contexto_correo}' not in ...
tests\test_f048_comparar_obra_prompt_dev.py:173: assert '{"$defs": {"...e": "object"}' == ... (LecturaCorreo de más)
tests\test_f048_comparar_obra_prompt_dev.py:179: AssertionError: assert 'Eres un administrativo ...' != 'Eres un administrativo ...'
3 failed, 33 passed in 3.60s
```
RED con los tests nuevos y el código sin cambiar (mismo comando):
```
E   TypeError: prompt_de_dev() got an unexpected keyword argument 'base'
E   TypeError: Dobles.prompt_de_dev() missing 1 required positional argument: 'base'
E   SystemExit: 2   (--base no existe)
11 failed, 24 passed, 4 errors in 4.54s
```
## GREEN
Comparador + T34b: `85 passed in 9.56s`. `bash harness/init.sh`: `1067 passed in 257.46s`, ENTORNO LISTO.
Cobertura y mutación: N/A (la puerta de cobertura dice que la rama fix no es una feature declarada).

## Fuera de alcance
Sin LLM ni sigrid-api. No se relanza la comparación real.
