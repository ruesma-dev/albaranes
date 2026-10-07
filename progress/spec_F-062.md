# F-062 · informe del spec-author (spec v1, 2026-10-07)

Feature: **sv3 aplica el proveedor propuesto antes de buscar contratos** · rigor `critico` · servicios sv3 y comun.
Estado: **`pending`** hasta que el humano cierre Q0–Q6 en la PARADA 1.

## 1. Qué hay en la rama

Rama `feature/F-062-proveedor-aplicado` (worktree `../albaranes-F-062`), creada desde `dev` `e7d7507`. Un commit
de spec, sin código:

- `specs/F-062-proveedor-aplicado/requirements.md` (R1–R16, EARS), `design.md`, `tasks.md` (T0–T13).
- `harness/features.json`: ficha F-062 (`pending`, prioridad 1, `critico`, `sv3-persistencia` + `comun`).
  Id comprobado libre en `albaranes`, `albaranes-F-049` y `albaranes-F-053` (F-061 solo existe en la rama de F-053).
- `BACKLOG.md` regenerado; nota en `progress/current.md`.

## 2. Datos (medición del humano, solo lectura, 2026-10-07)

Consultas 6.1–6.3 de la exploración previa (`diag_proveedor.py` del scratchpad del líder):

- **6.1 · 3 casos, todos «CIF mal leído por la IA»**, ninguno de formato; la primera búsqueda dio `ninguno` en los tres:
  - 19407: leído `B86056201` → real `B66056201` (HORMIGONES MAT, obra 0720, contrato CTSU26/0208).
  - 19394: leído `B86056095` → real `B66056201` (mismo proveedor; varios dígitos mal).
  - 1790636816: leído `B18437421` → real `B18487421` (ARIDOS ANFERSA, obra 0678, CTSU24/0176).
- **6.2a y 6.2b: 0 filas.** Las diferencias de formato y el prefijo `ES` no aparecen en datos reales.
- **6.3: 8 `encontrados`, 5 `ninguno`, 0 `error`** entre los no aprobados. El reintento tras `error` no es urgente.

**Dígito de control (hallazgo del líder, comprobado por mí con el algoritmo oficial)**: los tres CIF leídos tienen
el control **inválido** (`B86056201` debería acabar en 7, `B86056095` en 0 y `B18437421` en 6) y los dos reales
son válidos. Distancias de edición leído → real: **1, 4 y 1**. El 19394 obliga a que la cercanía del CIF no sea un
requisito (con «distancia ≤ 2» se perdería): solo desempata.

## 3. Hallazgos en el código y alcance

- **Orden del pipeline correcto** (punto a): en las tres rutas —nuevo, duplicado y `reenrich_by_merge_id`, que es
  lo que ejecuta `MensajePersistencia(force=True)` desde sv4— el resolver de cabecera corre antes que los
  contratos (`persist_albaran_pipeline.py:130/137`, `:216/221`, `:424/429`), y la búsqueda lee el CIF del merge.
  Basta con que la red **escriba** el CIF: el pipeline no cambia.
- **El revisor no puede ser pisado**: el CIF es de solo lectura en sv4 (`document_detail.html:266`) y el
  desplegable solo escribe `prv.cif`, que existe; sv3 solo corrige un CIF que no existe. Además, guarda por
  origen `manual` (sv4 hoy no lo escribe).
- **Trampa de las notas** (D6 del design): `_remove_nota_proveedor_safely` borra todo lo que empiece por
  `[AVISO] Proveedor` al principio de cada pasada; la nota de la corrección necesita prefijo propio
  (`[CORREGIDO] Proveedor`) o desaparece en la primera re-pasada.
- **Score de nombre simétrico y por subcadenas** (`_match_score`): «Hormigones Mat SL» saca 1,0 frente a
  cualquier «HORMIGONES X» y «MAT» casa con «MATERIALES». Por eso para aplicar se exige nombre completo (1,0) e
  identificador válido, y los empates se desempatan por cercanía del CIF con margen.
- **Confianza de sv4**: un origen desconocido puntúa como fiable; reutilizar `deterministic` (factor 0,6) evita
  tocar sv4.
- **F-030** (pendiente, «IA2 busca el proveedor parecido cuando el CIF no casa») se solapa: su parte sv3 (CIF
  aproximado + razón social) la cubre F-062 y su parte IA2, F-055.

**Entra**: (a) aplicación del candidato claro antes de buscar contratos, con revisión y auditoría; validación del
control del CIF en `ruesma_comun.proveedores` (encargo del líder); (c) retirada de `proveedor_cif_no_casa`
caducado y de la corrección cuando el revisor elige otro.

**Fuera, con los datos**: (b) normalización única y SQL normalizada (6.2: 0 casos; queda `normalizar_cif` en comun);
(d) reintento y «Guardar» en `error` (6.3: 0); caso «CIF existe sin contrato en la obra» (0 casos en 6.1).
(e) **F-055** es la solución de fondo (IA2 elige el proveedor de la lista de la obra); F-062 queda como red de
seguridad determinista y sigue valiendo después: verifica lo que elija la IA.

## 4. Preguntas para la PARADA 1 (cerradas, con recomendación)

**Respuesta del humano (2026-10-07): «si me vale»: Q0–Q6 aceptadas con la recomendación; PARADA 1 aprobada; implementar ya y fusionar en `dev` antes que F-053.** F-062 pasa a `spec_ready`.

- **Q0 · «Que proponga uno» = aplicarlo** (CIF y razón social de Sigrid en el merge antes de buscar contratos;
  lo leído queda en la nota y el motivo). *Recomendación: sí.* Hoy la nota ya propone uno: si el humano solo
  quería eso, F-062 sobra.
- **Q1 · ¿Sigue yendo a revisión cuando se corrige?** *Recomendación: sí, al menos al principio* (no bloquea la
  aprobación). Si dentro de unas semanas T12 no muestra errores, quitar `review_required` es un cambio de una línea.
- **Q2 · CIF leído que SÍ existe en Sigrid pero sin contrato en la obra, con otro proveedor de nombre casi igual que
  sí lo tiene.** Opciones: A) solo proponer en la nota; B) aplicar y repetir la búsqueda; C) fuera de F-062.
  *Recomendación: C* — 0 de los 3 casos medidos; un CIF que existe y casa con el nombre es, casi siempre, el
  proveedor correcto sin contrato en esa obra todavía. Si aparece, ficha aparte con la variante A.
- **Q3 · Qué es «candidato claro».** *Recomendación*: elegibles = candidatos con contrato en la obra, CIF válido y
  nombre completo (score 1,0); uno solo ⇒ claro; varios ⇒ gana el de CIF más cercano al leído si le saca 2 o más
  de distancia al siguiente; si no, no hay claro y se propone como hoy. Los tres umbrales son configurables.
- **Q4 · CIF leído con control VÁLIDO que no existe en Sigrid.** *Recomendación: aplicar igual* (literal del
  humano: «salvo que no haya ningún candidato claro»). Alternativa estricta: solo proponer, por si es un proveedor
  real aún no dado de alta en Sigrid. El control inválido se dice en la nota.
- **Q5 · F-030.** *Recomendación*: no tocarla ahora; al cerrar F-062, proponer cerrarla como absorbida (sv3 por
  F-062, IA2 por F-055).
- **Q6 · Recorte por datos**: normalización única y reintento tras `error`, fuera sin ficha nueva (anotados en
  «fuera» de la spec). *Recomendación: de acuerdo*; si 6.2 o 6.3 cambian, se reabre.

## 5. Plan de implementación (para la PARADA 1)

1. T0 hecha (datos de §2). T0b opcional: Anexo A.1 contrasta la regla de Q3 con las propuestas que ya aceptó el revisor.
2. T1 · comun: `ruesma_comun/proveedores/identificador.py` (`normalizar_cif`, `identificador_fiscal_valido`).
3. T2 · doble de sigrid-api con las obras 0720 y 0678 y una hormigonera que empata por nombre.
4. T3 · repositorio y puerto: `aplicar_correccion_proveedor` (una transacción) y `retirar_motivos_proveedor`.
5. T4 · resolver: una sola consulta de candidatos por pasada, sin cambio de comportamiento.
6. T5 · `_candidato_claro` (Q3, Q4).
7. T6 · la red aplica; settings `RED_PROVEEDOR_CORRECCION_*` (interruptor de vuelta atrás) y cableado.
8. T7 · re-pasadas idempotentes y retirada de motivos caducados.
9. T8 · los tests de D3 de F-002 siguen vivos con el interruptor apagado.
10. T9 · pipeline: 19407, 19394 y 1790636816 acaban en `encontrados` en las tres rutas.
11. T10 · docs (ARCHITECTURE regla 17, dominio §10.1, nota en D3 de F-002); `azure-apps` no cambia.
12. T11 · cobertura y mutación completa; T13 · `init.sh` en verde.
13. Despliegue: **solo sv3**. T12 MANUAL: vigilar los `proveedor_cif_corregido` (Anexo A.3).

Riesgo principal: una corrección equivocada lleva a otro contrato y a otra valoración. Mitigan: va a revisión
(Q1), la nota dice lo leído y cómo deshacerlo, umbral de nombre completo, CIF válido, margen de desempate e
interruptor `RED_PROVEEDOR_CORRECCION_ENABLED=false`.

## Anexo · consultas de solo lectura (PostgreSQL `albaranes`)

Script listo en el scratchpad del líder: `diag_f062.py` (mismo patrón que `diag_proveedor.py`: sesión
`read_only`, sin imprimir credenciales). No se seleccionan precios.

**A.1 · Qué hizo el revisor con las PROPUESTAS de hoy** (instantáneas de `undo_log`, que guardan el merge antes de
cada «Guardar»; sin «Guardar» no hay historia):

```sql
WITH snaps AS (
    SELECT u.document_id, u.id AS undo_id, e -> 'values' AS v
    FROM undo_log u
    CROSS JOIN LATERAL jsonb_array_elements(u.payload::jsonb -> 'restore') AS e
    WHERE u.document_id IS NOT NULL
      AND e ->> 'table' = 'albaran_documents_merge'
      AND (e -> 'values' ->> 'review_notes') LIKE '%no existe en Sigrid. PROPUESTA:%'
), prop AS (
    SELECT DISTINCT ON (document_id) document_id,
           v ->> 'proveedor_cif' AS cif_leido,
           substring(v ->> 'review_notes' from 'PROPUESTA: (\S+) —') AS cif_propuesto
    FROM snaps ORDER BY document_id, undo_id
)
SELECT m.id, m.numero_albaran, m.obra_codigo, m.approved, p.cif_leido, p.cif_propuesto,
       m.proveedor_cif AS cif_final, m.contratos_busqueda_resultado,
       CASE WHEN upper(m.proveedor_cif) = upper(p.cif_propuesto) THEN 'acepto_propuesta'
            WHEN upper(m.proveedor_cif) = upper(p.cif_leido)     THEN 'sin_cambiar'
            ELSE 'otro_proveedor' END AS desenlace
FROM prop p JOIN albaran_documents_merge m ON m.id = p.document_id
WHERE m.is_active
ORDER BY m.created_at_utc DESC;
```

Lectura: `otro_proveedor` en un caso que la regla de Q3 habría dado por claro sería una corrección equivocada.

**A.2 · Propuestas pendientes hoy** (sin «Guardar» todavía):

```sql
SELECT m.id, m.numero_albaran, m.obra_codigo, m.proveedor_cif AS cif_leido,
       substring(m.review_notes from 'PROPUESTA: (\S+) —') AS cif_propuesto
FROM albaran_documents_merge m
WHERE m.is_active AND NOT coalesce(m.approved, false)
  AND m.review_notes LIKE '%no existe en Sigrid. PROPUESTA:%'
ORDER BY m.created_at_utc DESC;
```

**A.3 · Vigilancia tras desplegar (T12)**:

```sql
SELECT m.id, m.numero_albaran, m.created_at_utc, m.obra_codigo, m.proveedor_cif, m.proveedor_nombre,
       m.contratos_busqueda_resultado, m.approved,
       substring(m.review_reasons_json from 'proveedor_cif_corregido:([^"]+)') AS correccion
FROM albaran_documents_merge m
WHERE m.is_active AND m.review_reasons_json LIKE '%proveedor_cif_corregido:%'
ORDER BY m.created_at_utc DESC;
```
