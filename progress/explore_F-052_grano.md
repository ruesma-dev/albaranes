# Exploración F-052 · grano de la consulta de proveedores por obra

Fecha: 2026-09-29 · Solo lectura (sigrid-api `sql/read`, SELECT; `.env` de sv3; `familias_de_texto` real de sv3).
Obras: 0691 y las 5 con más filas (0696, 0686, 0668, 0655, 0695). Validación final: **las 74 obras de más de 1.000 filas**.

## 1. Filas por grano (emp=1)

| Obra | Hoy (1 fila/línea) | (a) cif+raz | (b) +contrato | (c) cif+cód. prod. | (d) cif+desc. línea | (e) cif+naturaleza | **Agregada (§3)** |
|---|---|---|---|---|---|---|---|
| 0691 | 2.083 | 81 | 84 | 127 | 1.590 | 127 | **81** |
| 0696 | 5.558 | 163 | 193 | 310 | 2.864 | 295 | **163** |
| 0686 | 4.793 | 112 | 114 | 155 | 2.919 | 155 | **112** |
| 0668 | 4.266 | 75 | 81 | 120 | 1.613 | 120 | **75** |
| 0655 | 4.045 | 145 | 152 | 247 | 2.517 | 236 | **145** |
| 0695 | 3.929 | 112 | 119 | 174 | 2.555 | 173 | **112** |

- (e): `pro.famide` → `auxfam` **no sirve**: `auxfam` está vacía y `famide = 0` en todos los productos. La única clasificación con datos es `pro.natide` → `auxpronat` («Naturaleza de productos / Actividades», 258 valores: «OBRA COMPLETA», «SUBCONTRATA…», «HORMIGONES Y MORTEROS…», «ALQUILER DE MAQUINARIA»…). Es la que se ha medido como (e).
- Las filas de hoy son ~2× las descripciones distintas: la mayor parte del volumen es repetición de la misma descripción en líneas distintas. Pero (d) DISTINCT sigue sin caber en 1.000 (hasta 2.919).

## 2. ¿Se pierde señal? Proveedores cuyo conjunto de familias cambia frente al texto de hoy

| Obra | Prov. con familia hoy | (b) | (b)+(c) | (b)+(e) | (b)+(c)+(e) | (b)+(d) | (b)+(c)+(d) DISTINCT |
|---|---|---|---|---|---|---|---|
| 0691 | 25 / 81 | 21 | 21 | 18 | 18 | **0** | **0** |
| 0696 | 75 / 163 | 65 | 65 | 61 | 61 | **0** | **0** |
| 0686 | 45 / 112 | 36 | 36 | 35 | 35 | **0** | **0** |
| 0668 | 21 / 75 | 20 | 20 | 18 | 18 | **0** | **0** |
| 0655 | 60 / 145 | 54 | 54 | 48 | 48 | **0** | **0** |
| 0695 | 53 / 112 | 46 | 46 | 47 | 47 | **0** | **0** |

- **Toda la señal está en `ctrpro.res` (d).** El nombre del contrato casi nunca la trae, y los códigos de producto (c) no añaden nada: (b) y (b)+(c) dan exactamente lo mismo.
- (e) naturaleza **no sustituye** a (d). Pierde familias y además **inventa** otras (0696: PEDRO MOLINA ∅→maquinaria, TRADEX GESTIÓN AMBIENTAL residuos→maquinaria, DOMINGO LAREDO +hormigón; 0691: GALINDO RENT y RIWAL ∅→maquinaria). Se descarta sin rehacer `familia_detector`.
- 0691 con (b), los 21 que cambian: KORPORATE maq→∅; LUMINICA acero+maq→∅; FERMALUX acero→∅; CEMENTVAL horm+mort→∅; MAT. CERÁMICOS TORRES acero+mort→∅; AIRMAX maq→∅; DEYCON mort→∅; GRUFIN maq→∅; TOI TOI maq→∅; ESTRUCALA mort→∅; RENTAIRE comb+horm+maq→maq; MÁQUINAS OPEIN maq+res→maq; SEGURIDAD PREVENTIVA mort→∅; SONDENIRIS maq→∅; IMETAL maq→∅; JUANBAR acero→∅; EQUINSA acero+maq→∅; OBRAS Y PROYECTOS horm→∅; TALLERES PROEJE acero→∅; GASÓLEOS GALAPAGAR comb+maq→comb; LOXAM maq→∅.

## 3. Consulta recomendada: agregar en SQL, una fila por proveedor

`STRING_AGG` **no existe** en este SQL Server: da el error 195, anterior a 2017. `FOR XML PATH` sí funciona a través de sigrid-api, y también `WITH`: ni el validador ni una lista blanca lo rechazan. Así el texto conserva **todas** las descripciones distintas y llega en ≤ 163 filas.

```sql
WITH base AS (
    SELECT prv.cif AS cif, prv.raz AS raz, con_ctr.cod AS cod_ctr,
           con_ctr.res AS res_ctr, ctrpro.res AS res_lin, con_pro.cod AS cod_pro
    FROM ctr
    JOIN con AS con_ctr       ON ctr.ide     = con_ctr.ide
    JOIN con AS con_obr       ON ctr.obride  = con_obr.ide
    JOIN prv                  ON ctr.entide  = prv.ide
    LEFT JOIN ctrpro          ON ctrpro.docide = ctr.ide
    LEFT JOIN pro             ON ctrpro.proide = pro.ide
    LEFT JOIN con AS con_pro  ON pro.ide       = con_pro.ide
    WHERE con_obr.cod = ? AND con_ctr.emp = 1
),
txt AS (
    SELECT DISTINCT b.cif, CAST(LTRIM(RTRIM(x.v)) AS NVARCHAR(MAX)) AS v
    FROM base b CROSS APPLY (VALUES (b.res_ctr), (b.res_lin), (b.cod_pro)) AS x(v)
    WHERE x.v IS NOT NULL AND LTRIM(RTRIM(x.v)) <> ''
),
ctrs AS (SELECT DISTINCT cif, cod_ctr FROM base)
SELECT p.cif, p.raz AS nombre,
       STUFF((SELECT '|' + c.cod_ctr FROM ctrs c WHERE c.cif = p.cif
              FOR XML PATH(''), TYPE).value('.', 'NVARCHAR(MAX)'), 1, 1, '') AS codigos_contratos,
       STUFF((SELECT ' ' + t.v FROM txt t WHERE t.cif = p.cif
              FOR XML PATH(''), TYPE).value('.', 'NVARCHAR(MAX)'), 1, 1, '') AS texto
FROM (SELECT DISTINCT cif, raz FROM base) AS p
ORDER BY p.cif
```

**Medido en las 74 obras de más de 1.000 filas:** **0 diferencias** de familias frente al texto de hoy y 0 proveedores perdidos (Salmedina está en la 0691); **máximo 163 filas** (0696), `truncated=false` en todas; hasta 133 KB y 5 s.
- La consulta mantiene `cod_pro`, que es inocuo y conserva la semántica de hoy. Se puede quitar: sin él, el resultado también es idéntico.

**Esto rebate el motivo con que D1 descartó `FOR XML PATH`.** Las columnas `text` se resuelven con el `CAST` y la lista blanca no la rechaza. El riesgo que queda: si una descripción trae un carácter de control no válido en XML (0x01–0x1F), SQL Server falla con `FOR XML could not serialize`. No ha pasado en ninguna de las 74 obras, pero el llamante debe tratar ese error como el de hoy: si falla, el resolver cae al nombre global. Si se quiere eliminar el riesgo del todo, la alternativa sin XML son dos consultas:
- **Q1**: proveedores y contratos DISTINCT, grano (b), ≤ 193 filas. La lista de candidatos queda completa siempre.
- **Q2**: `SELECT DISTINCT prv.cif, ctrpro.res`, grano (d), hasta unas 3.000 filas. Pediría paginar o subir `max_rows`, pero si se truncara solo perdería señal de familia, no candidatos.

## 4. `_SQL_HEADER_AND_LINES` (CIF + obra) y conclusión sobre paginar

- **Sí necesita todas las líneas.** Su grano ya es el mínimo, una fila por `ctrpro.ide`. Cada línea se persiste por `sigrid_ide` (UPSERT de `albaran_contrato_lines_merge`) y alimenta el selector de contratos y la valoración. No se puede reducir.
- Las parejas mayores son B81345548 en la 0668 (**989 líneas**), B10893162 en la 0655 (974) y U87082368 en la 0430 (915). Hoy caben, pero a 11 filas del tope y sin mirar `truncated`.
- **Conclusión:** la consulta de proveedores **no necesita paginar** si se reescribe como en §3: el problema era el grano, no el tamaño de la obra. **La única que puede necesitar paginar** o un tope mayor es `_SQL_HEADER_AND_LINES`. Para ella basta:
  detectar `truncated=true` en `_post_sql_read` y paginar con `OFFSET/FETCH` (`ORDER BY con_ctr.cod, ctrpro.pos, ctrpro.ide`, orden estable) o subir su `max_rows` con aviso. El D3 de la spec (páginas de 5.000 y tope de 100.000) sobra para la consulta de proveedores.
