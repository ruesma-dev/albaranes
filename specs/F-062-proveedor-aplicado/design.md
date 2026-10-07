# F-062 · sv3 aplica el proveedor propuesto antes de buscar contratos — diseño

Requisitos: `requirements.md`. Diagnóstico, datos y preguntas: `progress/spec_F-062.md`.

## 1. Encaje y límite de servicio

- Todo cae en responsabilidades que **ya** son de sv3 (resolver de cabecera y red de proveedor,
  F-002/F-052). No nace dominio nuevo ni integración nueva: no hay nada que extraer.
- La regla del identificador fiscal es lógica de dominio reutilizable (sv4 la querrá al elegir
  proveedor; F-055 al verificar la elección de IA2) ⇒ `ruesma_comun`, como
  `normalizar_codigo_obra` en F-052. Hoy solo la importa sv3.
- Sin DDL: motivos y notas nuevos son texto en columnas existentes (`review_reasons_json`,
  `review_notes`). Ningún lector con SQL crudo (sv5) cambia. Sin SQL nueva contra Sigrid: se
  reutiliza la consulta agregada de F-052 que la red ya lanza.

## 2. Orden en el pipeline (comprobado en el código)

`application/pipelines/persist_albaran_pipeline.py`: en las **tres** rutas el resolver de cabecera
corre antes que los contratos —albarán nuevo (`:216` resolver → `:221` contratos), duplicado
(`:130` → `:137`) y `reenrich_by_merge_id` (`:424` → `:429`), que es lo que ejecuta el
`MensajePersistencia(force=True)` de «Guardar y volver a buscar» y «Solo volver a buscar»—. La
búsqueda lee el CIF del merge (`get_merge_cif_and_obra`), así que basta con que la red lo
**escriba**: el pipeline no cambia (R8 se verifica con un test, no con código nuevo).

**Una corrección humana posterior no se pisa** (R13), por construcción:

- sv3 solo aplica cuando el CIF del merge **no existe** en `prv`.
- En sv4 el CIF es de solo lectura (`templates/document_detail.html:266`) y solo cambia con el
  desplegable «Elegir proveedor», que escribe un `prv.cif`: siempre existe ⇒ en la re-pasada la
  red lo canoniza y no corrige.
- Guarda explícita: `proveedor_cif_origen = 'manual'` ⇒ no se aplica (convención de
  `update_merge_resolved_header`). Hoy sv4 no escribe `manual` (fuera de alcance).
- «Deshacer» la corrección = elegir otro proveedor en sv4: «Guardar» relanza (D4-A de F-052) y
  sv3 retira el motivo y la nota de la corrección (R15).

## 3. Ficheros a crear

| Ruta | Contenido |
|---|---|
| `services/albaranes-comun/ruesma_comun/proveedores/__init__.py` | Reexporta `normalizar_cif`, `identificador_fiscal_valido` |
| `services/albaranes-comun/ruesma_comun/proveedores/identificador.py` | R1, R2 (puro, sin dependencias) |
| `services/albaranes-comun/tests/test_f062_identificador_fiscal.py` | R1, R2 |
| `services/albaranes-persistencia/tests/test_f062_*.py` | Ver §8 |

## 4. Ficheros a modificar (todos en `services/albaranes-persistencia/`)

- `application/services/header_resolver_service.py`: §5.1–5.3.
- `domain/models/header_resolution_models.py`: `MergeHeaderForResolution.proveedor_cif_origen:
  str | None = None` (con defecto: los dobles actuales siguen valiendo).
- `domain/ports/header_resolver_ports.py`: `HeaderMergeRepository` gana los métodos de §5.4.
- `infrastructure/database/sqlalchemy_albaran_repository.py`: §5.4 y rellenar el origen en
  `get_merge_header_for_resolution`.
- `config/settings.py`: `RED_PROVEEDOR_CORRECCION_ENABLED` (true),
  `RED_PROVEEDOR_CORRECCION_SCORE_MIN` (1.0), `RED_PROVEEDOR_CORRECCION_MARGEN_DISTANCIA` (2), en
  el bloque de redes de F-002, y su comentario («si el CIF no existe, se PROPONE…») corregido.
- `interface_adapters/composition.py` y `interface_adapters/api/app.py`: cablean los tres.
- `tests/test_f002_red_proveedor.py`: los tests que afirman D3 (`r9_no_sobrescribe…`,
  `r9_horpresol…`, `r9_ante_un_empate…`) se ejecutan con `correccion_enabled=False` (R12): siguen
  siendo la prueba de la vuelta atrás.
- `tests/doble_sigrid_api.py`: fixture «0720/0678» de §8 (sin tocar el de F-052).

**Docs**: `docs/ARCHITECTURE.md` (regla 17 nueva: «Proveedor: el candidato claro se aplica»),
`docs/referencia/dominio_negocio_albaranes.md` §10.1 (viñeta de proveedor: de «propuesta a
revisión» a «se aplica y va a revisión»), `specs/F-002-obra-proveedor/design.md` D3 (una línea:
«sustituida por F-062 con el interruptor encendido»). `azure-apps/albaranes.md` no describe la
red (comprobado con grep): no se toca; lo que sv3 consume y expone no cambia.

## 5. Clases y funciones

### 5.1 comun — `ruesma_comun/proveedores/identificador.py`

```python
def normalizar_cif(valor: str | None) -> str | None                  # R1
def identificador_fiscal_valido(valor: str | None) -> bool           # R2 (normaliza dentro)
```

CIF: suma de los dígitos en posición par + suma de cifras de los dígitos impares por 2; control
= `(10 - suma % 10) % 10`; letra = `"JABCDEFGHI"[control]`. Comprobado a mano con los cinco CIF
de la tabla de requisitos (los tres leídos fallan; los dos reales pasan).

### 5.2 sv3 — candidato claro (application, `header_resolver_service.py`)

```python
def _distancia_edicion(a: str, b: str) -> int                         # Levenshtein, pura
def _candidatos_puntuados(self, *, proveedor_nombre, obra
        ) -> tuple[list[tuple[ProveedorObraResumen, float]], str]     # (puntuados, motivo F-052)
def _candidato_claro(self, *, cif_leido: str, puntuados
        ) -> tuple[ProveedorObraResumen | None, str | None]           # (candidato, via)
```

- `_candidatos_puntuados` hace la **única** llamada a `fetch_contratos_resumen_por_obra` de la
  pasada y devuelve el motivo de F-052 (`propuesta`, `nadie_casa`, `sin_obra`, `sin_nombre`,
  `consulta_fallida`). `_mejor_candidato_por_nombre` se reescribe encima con la misma firma y el
  mismo resultado (sus tests de F-052 siguen valiendo sin cambios).
- `_candidato_claro` aplica R3–R4 sobre CIF normalizados: `via ∈ {"unico", "cif_cercano"}`.
  Dos filas con el mismo CIF normalizado cuentan como un candidato (no empatan).

### 5.3 sv3 — red con aplicación

`_red_proveedor_por_cif(cif_leido, proveedor_nombre, obra, merge_document_id, origen)`:

1. `fetch_proveedor_by_cif` falla ⇒ como hoy (no marca nada; F-002 R16).
2. Existe ⇒ canoniza el nombre (hoy) y `retirar_motivos_proveedor` (R15, R16).
3. No existe ⇒ `_candidatos_puntuados` + `_candidato_claro`. Con candidato,
   `correccion_enabled` y `origen != "manual"` ⇒ `repository.aplicar_correccion_proveedor(...)`
   (R6, R7, R16) y fin. Si no ⇒ nota y motivo de hoy con el mismo `mejor` (R10), más la frase de
   control inválido (R11).

`_resolve_proveedor` pasa `hdr.proveedor_cif_origen`; sigue devolviendo `(None,
"deterministic")` con CIF presente, así que `update_merge_resolved_header` no reescribe nada.
`HeaderResolverService.__init__` gana `correccion_enabled: bool = True`,
`correccion_score_min: float = 1.0` y `correccion_margen_distancia: int = 2`.

### 5.4 sv3 — repositorio (infrastructure) y puerto (domain)

```python
def aplicar_correccion_proveedor(*, document_id, cif, nombre, motivo, nota) -> None  # 1 transacción
def retirar_motivos_proveedor(*, document_id, cif_actual: str | None) -> None
```

- `aplicar_correccion_proveedor`: `proveedor_cif`, `proveedor_nombre`, `proveedor_cif_origen =
  'deterministic'`, `review_required = true`, motivo con `anadir_motivo_revision`, nota con
  `_sustituir_nota(prefijo="[CORREGIDO] Proveedor")` y la misma depuración que
  `retirar_motivos_proveedor` con el CIF nuevo.
- `retirar_motivos_proveedor`: quita `proveedor_cif_no_casa:<x>` y
  `proveedor_cif_corregido:<l>><a>` cuyo CIF (`x`, `a`) normalizado no es `cif_actual`; si quitó
  un `proveedor_cif_corregido`, quita también la nota `[CORREGIDO] Proveedor`. No toca
  `review_required`.
- Lógica pura nueva junto a `quitar_motivos_con_prefijo`, probada sin BBDD:
  `depurar_motivos_proveedor(reasons_json, cif_actual) -> tuple[str | None, bool]` (JSON nuevo y
  si se retiró alguna corrección).

## 6. SQL

- **PostgreSQL**: nada nuevo, sin DDL; `UPDATE` de columnas existentes del merge en §5.4.
- **Sigrid**: ninguna consulta nueva ni modificada.
- Medición previa (solo lectura, hecha por el humano): `progress/spec_F-062.md` §2 y Anexo.

## 7. Decisiones y alternativas descartadas

- **D1 · Aplicar, no solo proponer** (humano; Q0). Descartado mantener D3 de F-002: los tres
  albaranes medidos se quedan sin contrato por una lectura que sv3 ya sabe corregir.
- **D2 · Elegible = identificador válido + nombre completo** (R3; Q3). Con el umbral de hoy (0,5)
  «MAT» casaría con «MATERIALES …» (`_match_score` busca subcadenas) y bastaría una palabra.
  El identificador válido descarta fichas de Sigrid mal tecleadas y extranjeras: se proponen, no
  se aplican.
- **D3 · La distancia de CIF solo desempata, con margen** (R4; Q3). Solo con distancia ≤ 2 se
  perdería el 19394 (distancia 4 al bueno); sin margen, 4 frente a 5 decidiría a cara o cruz.
  Que la distancia sola baste (sin nombre) se descarta: dos empresas reales pueden distar un
  dígito y el nombre es la red de seguridad.
- **D4 · El control del leído no cambia la regla** (R5; Q4). Literal del humano: «salvo que no
  haya ningún candidato claro». La alternativa estricta (con control válido, solo proponer, por
  si es un proveedor real aún no dado de alta) queda para la PARADA 1.
- **D5 · Origen `deterministic`**: sv4 ya lo pesa 0,6 en la confianza sin tocar sv4. Un origen
  nuevo puntuaría como fiable (sv4 trata lo desconocido como `ia`).
- **D6 · Prefijo de nota propio** `[CORREGIDO] Proveedor`: la red borra por prefijo
  `[AVISO] Proveedor` (`startswith`) al empezar cada pasada; con ese prefijo la nota de la
  corrección desaparecería en la primera re-pasada.
- **D7 · El motivo sella leído y aplicado**: se retira sin estado extra (patrón de F-036 R24).
- **D8 · Sin tocar sv4**: el desplegable solo ofrece CIF de `prv`, así que la guarda estructural
  basta; marcar `manual` cambiaría su confianza (feature aparte).
- **D9 · Alcance recortado por los datos**: normalización única, reintento tras `error` y el
  caso «CIF existente sin contrato en la obra» salen (0 casos medidos; Q2, Q6).

## 8. Tests (sin red ni BBDD)

Doble de sigrid-api, fixture nuevo: obra «0720» con `B66056201 HORMIGONES MAT, S.L.U.` (contrato
`CTSU26/0208` con líneas) y otra hormigonera cuyo nombre empata a 1,0 con «Hormigones Mat SL»
(CIF lejano de los dos leídos); obra «0678» con `B18487421 ARIDOS ANFERSA` (`CTSU24/0176`).
Repositorio: el falso de `test_f002_red_proveedor.py`, ampliado.

| Requisitos | Fichero |
|---|---|
| R1, R2 | `albaranes-comun/tests/test_f062_identificador_fiscal.py` (los cinco CIF reales, NIF, NIE, `K`) |
| R3–R5 | `test_f062_r3_candidato_claro.py` (tabla: único, empate desempatado por distancia, margen insuficiente, nombre por debajo de 1,0, candidato con control inválido) |
| R6, R7, R9, R12, R13 | `test_f062_r6_aplica_candidato.py` |
| R8 | `test_f062_r8_pipeline_tres_casos.py` (pipeline + cliente real + doble; 19407, 19394 y 1790636816 en las tres rutas ⇒ `encontrados`) |
| R10, R11 | `test_f062_r10_sin_candidato_claro.py` |
| R14–R16 | `test_f062_r14_repasadas_y_motivos.py` (+ `depurar_motivos_proveedor` puro) |

MANUAL (humano): T12, tras desplegar **solo sv3** (comun va en su imagen y nadie más importa el
módulo nuevo). Los tres albaranes medidos ya los corrigió el revisor (su CIF actual existe), así
que no sirven para probar: se vigilan los nuevos con la consulta de solo lectura del Anexo A.3 de
`progress/spec_F-062.md` (motivo `proveedor_cif_corregido`) y se revisa cada uno en sv4.
