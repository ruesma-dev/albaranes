# F-063 · El CIF de Construcciones Ruesma nunca es el proveedor — diseño

## 1. Dónde va la regla

Las tres rutas de sv3 (albarán nuevo, duplicado y `reenrich_by_merge_id` de sv4) pasan por
`HeaderResolverService.resolve_merge_document` antes de enriquecer obra y contratos, y este llama a
`_resolve_proveedor`. La regla va **al principio de `_resolve_proveedor`**, antes de la rama «CIF
presente» (red de F-002/F-062): un solo punto cubre las tres rutas y la búsqueda de contratos, que
lee el CIF del merge después, ya no ve el CIF propio.

```
cif_leido = strip(proveedor_cif)
si cif_leido y _descartar_cif_propio(cif_leido, origen, doc):   # R4, R6, R7
    cif_leido = ""                                               # R5: camino «sin CIF»
si cif_leido: (red por CIF, como antes)                          # R8
paso 1 / paso 2 (como antes, sin candidatos propios)             # R9
```

`_descartar_cif_propio` devuelve `True` si el CIF es propio y el origen no es `manual`, haya ido
bien o no la escritura (R7: con la escritura fallida, si el camino «sin CIF» deduce un CIF,
`update_merge_resolved_header` lo escribe igualmente porque el origen no es `manual`).

## 2. Comun (`ruesma_comun/proveedores/propios.py`)

- `CIFS_PROPIOS_POR_DEFECTO: dict[str, str]` = `{"A81873903": "Construcciones Ruesma"}`.
- `cifs_propios(extra: str | None) -> frozenset[str]`: defecto ∪ `normalizar_cif` de cada trozo de
  `extra` partido por `[,;\s]+`, sin vacíos.
- `es_cif_propio(valor, propios) -> bool`: `normalizar_cif(valor) in propios` (None ⇒ False).
- Se exportan en `ruesma_comun.proveedores`. Puro: sv2 y sv4 podrán usarlo (fuera de alcance).

## 3. sv3

- `config/settings.py`: `cifs_propios: str = Field("", alias="CIFS_PROPIOS")`.
- `HeaderResolverService(..., cifs_propios: frozenset[str] | None = None)`; `None` ⇒
  `cifs_propios(None)`. Cableado en `composition.py` y `api/app.py` con
  `cifs_propios(settings.cifs_propios)`.
- Constantes de dominio (`header_resolution_models.py`): `MOTIVO_PROVEEDOR_CIF_PROPIO =
  "proveedor_cif_propio:"` y `NOTA_CIF_PROPIO_PREFIJO = "[AVISO] CIF del cliente"`.
- Puerto `HeaderMergeRepository.descartar_cif_propio(document_id, motivo, nota)` y su
  implementación SQLAlchemy: en una transacción `proveedor_cif = proveedor_cif_origen = None`,
  `review_required = True`, `anadir_motivo_revision` y `_sustituir_nota` con el prefijo propio.
  `KeyError` si el merge no existe (como `aplicar_correccion_proveedor`). No toca nombre ni raw.
- Nota (R4): `f"{NOTA_CIF_PROPIO_PREFIJO}: la IA leyó el CIF del cliente ({cif}, {nombre}) como CIF
  del proveedor; se descarta y el proveedor se busca por nombre."`, con `nombre` el de
  `CIFS_PROPIOS_POR_DEFECTO` o «CIF propio» para los añadidos por configuración.
- R9: filtro `_sin_propios` en los tres sitios donde entran candidatos: `_resolver_por_obra_y_familia`
  (lista de la obra), paso 2 (lista global) y `_candidatos_puntuados` (red por CIF). Si tras filtrar
  la lista de la obra queda vacía, se trata como «obra sin proveedores con contrato».

### Decisiones

- **D1 · Prefijo propio de nota y motivo** (R10). El texto pedido empezaba por «[AVISO]
  Proveedor:», pero ese prefijo lo borra `_remove_nota_proveedor_safely` en la misma pasada en
  cuanto el camino «sin CIF» resuelve por nombre (y en cada re-pasada con CIF): la nota no llegaría
  nunca al revisor. Mismo motivo y misma solución que `[CORREGIDO] Proveedor` de F-062 (D6).
- **D2 · El revisor manda** (R6). Si el revisor elige a mano un CIF propio (origen `manual`), se
  respeta: es una decisión humana explícita, y el portal no debe pelearse con ella.
- **D3 · La lista solo se amplía** (R1). Quitar el CIF de Ruesma por configuración reabriría el
  incidente; si algún día hiciera falta, es un cambio de código con su spec.
- **D4 · Sin interruptor**. La regla no tiene falsos positivos posibles (Ruesma no es proveedor de
  sí misma en un albarán de proveedor); la vuelta atrás es la revisión anterior de sv3.
- **D5 · Sin backfill** de los merges ya canonizados (requirements, «Fuera de alcance»).

## 4. Doble de sigrid-api (`tests/doble_sigrid_api.py`)

`fixture_f063()` aparte (no toca los de F-052/F-062): obra 0694 con FEYMACO (A28733558, razón social
supuesta «FERRETERIA Y MAQUINARIA PARA LA CONSTRUCCION, S.A.», un contrato con líneas) y un segundo
proveedor que no casa por nombre; en `prv` global además Construcciones Ruesma (A81873903,
«CONSTRUCCIONES RUESMA, S.A.»), para reproducir la canonización del incidente. La razón social real
de FEYMACO en Sigrid no se conoce: el log de producción prueba que casa por nombre con el leído
(score ≥ 0,5) y el fixture usa una que cumple eso.

## 5. Tests

- comun: `tests/test_f063_cifs_propios.py` (R1, R2).
- sv3: `tests/test_f063_cif_propio.py`: repositorio (sesión doble de F-062), resolver con `RepoRed`
  (R4–R10) y pipeline en las tres rutas con el doble (R11, R12), cada uno con su control negativo
  (CIF normal ⇒ sin cambios; sin la regla, el pipeline reproduce el incidente).

## 6. Documentación

`docs/ARCHITECTURE.md` regla 18 y `services/albaranes-persistencia/.env.example` (`CIFS_PROPIOS`).
`azure-apps/` no cambia: sv3 no expone ni consume nada nuevo (una variable opcional sin valor).
