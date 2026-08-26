<!-- progress/impl_F-043_bloque_A_cr.md -->
# F-043 · BLOQUE A — cambios requeridos de la review (pasada 1)

Encargo: `progress/review_F-043_bloque_A.md` (CHANGES_REQUESTED, 2
bloqueantes + menores). Rama `feature/F-043-clasificacion-por-ia1`, rigor
`critico`. **Ninguna tarea nueva**: T5 en adelante siguen sin tocar. Sin
`git push`. Tres commits, uno por cambio requerido:

`74c80be` CR-1 · `d3d195b` CR-2 · `2c438b4` CR-3.

## CR-1 · Trazabilidad de R8 (bloqueante 1)

Los 13 tests que cubren R8 se llamaban `test_f043_schema_sv2|sv3_*`, así que
`grep test_f043_r8` no encontraba nada: incumplía R31, el §Tests de
`docs/CONVENTIONS.md` y la primera casilla de C4.

Renombrados con prefijo, sin tocar ni una aserción:

- `services/albaranes-api/tests/test_f043_schema_sv2_documento.py` — 7 tests
  → `test_f043_r8_schema_sv2_documento_*`.
- `services/albaranes-persistencia/tests/test_f043_schema_sv3_documento.py` —
  5 → `test_f043_r8_schema_sv3_*`, y
  `..._meta_sigue_sin_admitir_la_tipologia` → **`r9_`**, que es de R9.

Verificación: `grep -rn "test_f043_r8" --include=*.py services/` devuelve
**12** líneas (7 sv2 + 5 sv3) donde antes devolvía 0. Sin fase RED: un
renombrado no cambia comportamiento, y lo que había que demostrar —que el
nombre no era trazable— es ese `grep`.

```
$ (sv2) python -m pytest tests -k f043_schema -q
7 passed, 58 deselected in 1.48s
$ (sv3) python -m pytest tests -k f043_schema -q
6 passed, 125 deselected in 5.16s
```

## CR-2 · Divergencia catálogo / `TipoFamilia` (bloqueante 2)

`contexto_linea.py` declaraba un `Literal` con **seis** familias de línea; el
catálogo devuelve **siete** e incluye `generico`. Dos sitios, y ya
divergentes: con esa lista, dar de alta una familia la enrutaba en fase 2 y
en valoración pero la validación de `ContextoLinea` rechazaba la línea que la
llevase — la trampa de F-023 que R1-R3 vienen a cerrar.

**Decisión aplicada (del humano, 2026-08-26): se AÑADE `generico` a
`TipoFamilia`.** Es lo coherente con el diseño §1.1, que le da alcance
documento + línea, y solo AMPLÍA lo que la validación acepta: ningún envelope
que validase antes deja de validar.

### Fase RED (traza real)

Test escrito primero, con el `Literal` todavía de seis:

```
$ (comun) python -m pytest tests/test_f043_familias.py -k coinciden_con_tipo_familia -q
>       assert set(get_args(TipoFamilia)) == set(cat.familias_linea())
E       AssertionError: assert {'alquiler_ma...', 'residuos'} == {'alquiler_ma..., 'otro', ...}
E
E         Extra items in the right set:
E         'generico'
E         Use -v to get more diff

tests\test_f043_familias.py:112: AssertionError
FAILED tests/test_f043_familias.py::test_f043_r2_las_familias_de_linea_del_catalogo_coinciden_con_tipo_familia
1 failed, 42 deselected in 0.84s
```

Después de añadir `generico` al `Literal`: `1 passed, 42 deselected in 0.49s`.

El test nuevo es
`test_f043_r2_las_familias_de_linea_del_catalogo_coinciden_con_tipo_familia`,
en `services/albaranes-comun/tests/test_f043_familias.py`. Comparación de
conjuntos en las dos direcciones: falla igual si sobra en un lado o en otro.
El `Literal` lleva ahora el comentario de por qué `generico` está ahí (una
línea puede ser genérica dentro de un albarán de otra familia) y de que la
lista debe coincidir con `familias_linea()`, nombrando al test que lo vigila.
De paso se corrigió el docstring del módulo, que listaba los valores a mano y
ya se había quedado sin `mortero`.

### Suites de los tres servicios que leen `contexto_linea`

`ruesma_comun/contratos/contexto_linea.py` lo leen sv3, sv5 y sv6. Ejecutadas
enteras y **una a una** (nada en paralelo), después del cambio:

| Suite | Resultado |
|---|---|
| `comun` | **118 passed, 3 skipped** en 115,22 s |
| sv3 `albaranes-persistencia` | **131 passed** en 2,33 s |
| sv5 `albaran-valoracion-api` | **18 passed** en 0,72 s |
| sv6 `albaran-valoracion-persist` | **185 passed** en 2,47 s |

### Lo que esto implica para T22 (bloque D, que tiene que saberlo)

Con `generico` como familia de línea, **`familia_efectiva` puede devolver
`'generico'` por su rama 4**: un albarán clasificado `generico` y no mixto
propaga esa familia a las líneas sin `tipo_familia` propio. Las puertas de
familia de sv6 comparan contra `'residuos'` y `'hormigon'`, así que
**`'generico'` no abre ninguna: mismo efecto que el `None` de hoy.** No cambia
nada hoy ni en T22, salvo que alguien escriba una puerta que compare contra
`'generico'`. Si T22 necesita distinguir «sin familia» de «familia genérica»,
el valor ya se lo dice; hasta entonces son equivalentes al valorar.

## CR-3 · Menores (hallazgo 3)

**(a) Una sola ruta de import para `ClasificacionAlbaran`: el reexport
`from ruesma_comun.contratos import ClasificacionAlbaran`.** Aplicado a los 5
sitios que lo importaban (`albaran_models.py` de sv2, `extraction_models.py`
de sv3 y los tres ficheros de test).

*Por qué el reexport y no el shim de dominio.* El patrón
`services/*/domain/models/contexto_linea.py` no es un patrón de diseño: es una
cicatriz. Había una copia local divergente de `ContextoLinea` por servicio, y
al unificarla en `ruesma_comun` se dejó un reexport en la ruta vieja para no
tocar decenas de imports. `ClasificacionAlbaran` nace en `ruesma_comun` y no
tiene copia previa que conservar: un shim solo añadiría un fichero vacío y un
segundo nombre por el que importarla, que es lo que el hallazgo pedía cerrar.
Ahora el `__init__.py` hace lo que su docstring promete.

El test `test_f043_r7_contrato_se_exporta_desde_ruesma_comun_contratos` habría
quedado tautológico al cambiar el import del módulo, así que ahora importa
también por la ruta interna y comprueba que **las dos rutas devuelven el mismo
objeto** (`is`): dos clases con el mismo nombre serían la divergencia otra vez.

**(b) Informe del bloque corregido** (`progress/impl_F-043_bloque_A.md`):

- §3 T4: el segundo test de sv2 que ya pasaba en RED **no es de no-regresión**;
  es `..._rechaza_una_clasificacion_mal_formada`, y pasaba por el
  `extra_forbidden` del bloque entero, no por el `le=100` que comprueba de
  verdad. En sv3 sí eran los dos de no-regresión.
- §6: el **98,7 %** de cobertura se mide sobre el diff contra `dev`, que
  arrastra F-036, no solo sobre el bloque A. Dicho ahora en la propia fila.
- Además, dos cifras que mis cambios dejaron obsoletas: los tests del fichero
  de `comun` pasan de 42 a **43** (55 → **56** tests nuevos de F-043) y
  `familias.py` importa dos cosas, no tres.

**(c) Aserciones endurecidas** (`test_f043_familias.py`):

- `_r1_catalogo_es_inmutable`: `pytest.raises(Exception)` →
  **`pytest.raises(FrozenInstanceError)`**. Ahora comprueba que el dataclass
  está congelado y no que la asignación falle por lo que sea.
- `_r13_familia_efectiva_no_mira_el_ler_ni_el_texto`: la lista EXACTA de
  imports pasa a **lista NEGRA** (`ler`, `residuo`, `proveedor`, `cif`,
  `texto`, `producto`, `tipologia`, `regex`, `unicodedata`, `difflib`,
  `rapidfuzz`, `infrastructure`, `domain.`, más `re` comprobado por nombre de
  módulo y no por subcadena). Añadir un import legítimo ya no lo rompe; colar
  uno de los prohibidos sí. El fallo lleva mensaje con la línea culpable.
  *No corregido*, y a propósito: `_r2_catalogo_las_listas_se_derivan_no_se_declaran`
  sigue reimplementando la comprensión del código. La propia review dice que
  lo salva su test hermano —`_r2_catalogo_familias_documento_son_las_cuatro_con_prompt`,
  que fija los valores a mano— y no estaba entre los cambios requeridos.

**(d) `ruff` limpio en los 6 ficheros nuevos del bloque: 16 → 0 avisos.**

```
$ python -m ruff check <los 6 ficheros>
All checks passed!
```

Eran 10 `UP045` (`Optional[X]` → `X | None`), 3 `I001` (orden de imports),
`UP006`+`UP035` (`typing.List` → `list`) y 1 `PIE810` (dos `startswith`
seguidos, introducido por la lista negra de (c), corregido a mano). **Solo
anotaciones de tipo y orden de imports; ni una línea de lógica.** La deuda del
resto del monorepo no se tocó: `init.sh` pasa de 1131 a **1115** avisos, los 16
del bloque y ninguno más.

## Efecto sobre la campaña de mutación: NINGUNO (comprobado, no supuesto)

No se lanzó ninguna campaña (lo prohíbe el encargo y mutan el árbol
principal). En su lugar, `harness.mutacion.generar_mutantes` —generación, sin
ejecutar nada— sobre los ficheros tocados:

- `familias.py` **9 mutantes**, `clasificacion.py` **3** = **12**, los mismos
  doce que describe §6 del informe del bloque, uno a uno (el `frozen=True`,
  los dos `not` de la normalización, el `==` de `obtener`, los dos ternarios
  `is not None` de los `prompt_*_de`, el `is None` de `_campo`, el
  `clasificacion is None` y el `mixto` `False` de `familia_efectiva`, y
  `ge=0` / `le=100` / `default=False` del contrato). **El conjunto no cambia**:
  los cambios de CR-3(d) son anotaciones, que no generan mutantes.
- Sobre las líneas cambiadas por estos tres commits en `contexto_linea.py`
  (14), `albaran_models.py` (1) y `extraction_models.py` (1): **0 mutantes**.

Conclusión: `progress/mutacion_F-043_bloque_A.md` **sigue siendo válido** y no
hay código mutable nuevo sin cubrir. La campaña completa sigue siendo T28.

## Fuera de alcance y MANUAL

`tipologia_resolver`, prompts, workers, DDL, sv4, sv5 y sv6: **intactos** —de
sv5 y sv6 solo se ejecutaron sus suites—. Ni una regla determinista que
infiera la familia por LER, familia de producto, texto o CIF. Ninguna tarea de
T5 en adelante; `tasks.md` sin tocar, los CR no son tareas. **MANUAL nuevas:
ninguna**; las de la feature siguen siendo T30 (evals con LLM real), T31 y
T32, y están en `progress/current.md`.

## Evidencias

| Evidencia | Valor medido |
|---|---|
| Tests ejecutados y resultado | raíz **556 passed** (169,45 s) · comun **118 passed, 3 skipped** (132,62 s) · sv2 **65 passed** (3,75 s) · sv3 **131 passed** (5,44 s) · sv5 **18 passed** (0,72 s) · sv6 **185 passed** (2,47 s). **Cero fallos, cero skips nuevos.** |
| Tests nuevos en esta pasada | **1** (el de coherencia catálogo/`TipoFamilia`); 13 renombrados |
| Cobertura de líneas cambiadas | **98,6 %** (365/370, umbral 80 %, nivel `critico`) — sigue midiéndose sobre el diff contra `dev`, que arrastra F-036 |
| Mutantes generados / supervivientes | **12 / 0**, sin recampaña: conjunto de mutantes idéntico al de la campaña del bloque (arriba, comprobado con `generar_mutantes`) |
| Tiempo de la suite | el de cada suite, en la fila 1 |
| `ruff` en los 6 ficheros del bloque | **0 avisos** (eran 16) |

## `bash harness/init.sh` — resultado real

**Verde a la primera**: `ENTORNO LISTO. Puedes trabajar.`

- raíz **556 passed in 169.45s**, las 6 suites de servicio en verde.
- `PUERTA COBERTURA [OK] 98.6%` (365/370, umbral 80 %, nivel `critico`).
- `PUERTA TAMAÑO [OK]` · rama correcta · árbol limpio tras los tres commits.

Avisos que siguen (**todos previos y ninguno bloqueante**): F-036 en `blocked`;
`ruff` 1115 de deuda previa; sv1-email e `infra` sin tests; marcas `[ADAPTAR]`
en las specs de F-034/F-035; y `PUERTA RUTAS SENSIBLES` en aviso por las 7
rutas, cuya evidencia es **T30**, reservada al humano.

*Nota de tamaño*: `impl_F-043_bloque_A.md` queda en **221** líneas y este en
**~220**, frente al tope de 220. La puerta mide `progress/impl_F-043.md`
(nombre exacto), no los informes por bloque, y sale `[OK]`.
