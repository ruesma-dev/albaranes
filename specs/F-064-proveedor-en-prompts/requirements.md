# F-064 · IA1 e IA2 ignoran al cliente (Construcciones Ruesma) y la IA2 confirma el proveedor — requisitos

Rigor **critico**. Servicios: **sv2-api** (prompts, montaje del prompt, configuración) y **evals**. Toca
`config/prompts.yaml` y `config/revision_rules.yaml` de sv2: **RUTA SENSIBLE**, exige pasada de evals con LLM
real del humano. sv3 y `ruesma_comun` no cambian.

## Origen (humano, 2026-10-08)

Albarán de FEYMACO (obra 0694): la IA devolvió bien el nombre y como CIF **A81873903, el de CONSTRUCCIONES
RUESMA** (el cliente, impreso en la casilla «C.I.E./D.N.I.» del bloque del cliente); el CIF de FEYMACO solo
está en el pie («Inscrita en el Registro Mercantil … C.I.F. A-28/733558»). F-063 (en `dev`) lo defiende en
sv3 descartando los CIF propios. El humano pide, literal: «añade en el prompt de sv2 que estos CIF y empresas
son los del cliente, y debe ignorarlos y buscar otros» y «F-064 será para IA 1 y 2. Ambas deben confirmar
proveedor». Empresas del cliente: «de momento esa» (Construcciones Ruesma, A81873903).

Causa en el prompt de hoy (`albaran_factura_es`): la frase sobre Ruesma está escrita a mano y solo en la
viñeta del nombre, y la del CIF dice «Busca el código por un campo que ponga CIF o NIF o NIE»: en FEYMACO la
única casilla con esa etiqueta es la del cliente.

## Definiciones

- **Empresas del cliente**: los CIF de `ruesma_comun.proveedores.cifs_propios(extra)` (F-063), con la razón
  social de `CIFS_PROPIOS_POR_DEFECTO` cuando la hay. Hoy, solo A81873903 — Construcciones Ruesma.
- **Emisor**: la empresa que emite el albarán (membrete, bloque fiscal, pie con la inscripción en el
  Registro Mercantil, «emitido por»). Es el proveedor.
- **Bloque de empresas del cliente**: el texto que sustituye al marcador `{empresas_cliente}`.

## sv2 · la lista de empresas del cliente (una sola fuente)

R1. El sistema debe construir la lista de empresas del cliente SOLO a partir de `ruesma_comun.proveedores`
(`CIFS_PROPIOS_POR_DEFECTO` y `cifs_propios`), ampliada con la variable `CIFS_PROPIOS` de sv2 (mismo nombre,
mismo formato y misma regla que en sv3: solo amplía, nunca quita las de serie). sv2 no mantiene lista propia.

R2. sv2 debe leer `CIFS_PROPIOS` (opcional, defecto vacío) y pasar la lista al servicio de extracción en sus
dos composiciones (worker y API). Sin pasarle nada, el servicio usa la lista de serie: también el adaptador
de evals, que lo monta sin ese argumento.

R3. El bloque debe ser determinista: una cabecera fija y una línea por empresa, `CIF — razón social`, con
las de serie en su orden y después las añadidas por configuración, ordenadas; una añadida sin razón social
lleva un texto fijo («empresa del grupo, sin razón social configurada»). El CIF va normalizado.

R4. CUANDO se añade una empresa a `CIFS_PROPIOS_POR_DEFECTO` o a `CIFS_PROPIOS`, debe aparecer en el prompt
de IA1 y en el de IA2 sin tocar ningún YAML (y sv3 la descarta por F-063, con la misma fuente).

## IA1 · el cliente no es el proveedor

R5. El `task` de `albaran_factura_es` debe llevar el marcador `{empresas_cliente}` exactamente una vez, en
la parte del proveedor de «Reglas para la cabecera». Ni `config/prompts.yaml` ni `config/revision_rules.yaml`
deben llevar escrito a mano el CIF ni el nombre de ninguna empresa del cliente (hoy: ni `A81873903` ni
`Ruesma`, sin distinguir mayúsculas).

R6. CUANDO se construye el prompt de fase 1, el sistema debe sustituir `{empresas_cliente}` por el bloque de
R3 en el mismo punto donde se sustituyen los demás marcadores de fase 1 (`_render_task_fase_1`), ANTES de
`{contexto_correo}`, que sigue siendo el último: un correo que escriba `{empresas_cliente}` no recibe la lista.

R7. SI el `task` no trae el marcador, ENTONCES el sistema no debe añadir nada: el texto queda byte a byte
como el de entrada (lo necesita la variante «base» de R15; el YAML real lo lleva por R5).

R8. Las viñetas `proveedor_nombre` y `proveedor_cif` de IA1 deben decir:
- el proveedor es el EMISOR: su razón social del bloque fiscal (como hoy, el logotipo no manda) y su CIF,
  que está en el membrete, junto a la razón social o en el pie (inscripción en el Registro Mercantil);
- `proveedor_cif` se devuelve sin espacios, guiones, puntos ni barras (`A-28/733558` ⇒ `A28733558`);
- las empresas del bloque son el CLIENTE: aparecen en casillas de cliente («Cliente», «Nº cliente»,
  «Empresa», «Destinatario», «Facturar a», su «C.I.F./D.N.I.»), con la razón social completa o abreviada y
  con o sin forma jurídica; NUNCA se devuelven como proveedor, aunque su CIF sea el único del documento o
  esté en una casilla rotulada CIF: se ignoran y se busca el del emisor;
- si el único CIF del documento es de una empresa del cliente, `proveedor_cif` es null; si no se identifica
  al emisor, `proveedor_nombre` es null.
La frase «Busca el código por un campo que ponga CIF o NIF o NIE» desaparece.

## IA2 · confirma el proveedor

R9. `config/revision_rules.yaml` debe llevar la regla `proveedor_emisor`, que pida a IA2, en cualquier
familia: revisar SIEMPRE `cabecera.proveedor_nombre` y `cabecera.proveedor_cif` de fase 1 contra el
documento; si son de una empresa del cliente (las del bloque de las reglas de fase 1) o no corresponden al
emisor, corregirlos con el nombre y el CIF del emisor leídos en el documento, o dejar `proveedor_cif` null
si el del emisor no aparece; si no puede leer con seguridad al emisor, conservar lo de fase 1 salvo
que sea una empresa del cliente (entonces `proveedor_cif` null; O1, aprobada el 2026-10-15); si son
correctos, copiarlos tal cual sin razonamiento; cada cambio, con un
razonamiento de `campo` `cabecera.proveedor_cif` o `cabecera.proveedor_nombre` y `patron_aplicado`
`proveedor_emisor`. La regla prevalece sobre el contexto de Sigrid: un CIF del cliente nunca es el
proveedor, aunque ese contexto lo dé por validado.

R10. CUANDO se construye el prompt de cualquiera de los cuatro `albaran_revision_fase2_*`, las instructions
deben contener el bloque de empresas del cliente (dentro de `{prompt_fase_1}`) y la regla `proveedor_emisor`
(dentro de `{revision_rules}`), y ningún marcador sin sustituir. Los cuatro prompts de fase 2 no se editan.

R11. IA2 debe devolver el proveedor confirmado o corregido en `documento_revisado.cabecera`
(`proveedor_nombre`, `proveedor_cif`), sin campos nuevos: `DocumentoAlbaran`, `CabeceraAlbaran`,
`RevisionAlbaranFase2` y `origen_datos` quedan con los mismos campos que en `dev`.

R12. sv2 no debe filtrar el CIF del cliente con una regla determinista: lo que devuelva IA2 llega a sv3 tal
cual en el envelope final, para que la red de F-063 lo descarte y deje su motivo `proveedor_cif_propio:`,
que es la señal de que la IA falló.

## sv3 · consumo (sin cambios)

R13. sv3 debe consumir la cabecera del envelope final exactamente como en `dev`: CIF del emisor ⇒ red por
CIF (F-002/F-062); CIF null ⇒ camino «sin CIF» por nombre dentro de la obra (F-063 R5, F-062); CIF propio
que se cuele ⇒ descarte de F-063. Ningún fichero de sv3 cambia y sus suites siguen en verde.

## Evals · medir el proveedor

El banco no mide hoy el CIF: `proveedor_cif` está a `NO_COMPARAR` en los 60 casos de IA1, IA2 solo compara
`contexto_linea` y el E2E no observa `cif` (sale de los fixtures de `inputs`, no de sv2).

R14. `python -m evals.comparar_proveedor` debe ejecutar, por caso, variante (`base`, `rama` o `ambas`) y
repetición, la fase 1 con el proveedor LLM de `IA_PRIMERA_FASE` y la fase 2 con el de `IA_SEGUNDA_FASE`
(prompt de fase 2 según la tipología del caso, como el runner), y clasificar el CIF tras IA1 y tras IA2 en
`emisor` (normalizado igual al `cif` de `evals/fixtures/final/<caso>.json`), `cliente` (`es_cif_propio`),
`nulo` u `otro`.

R15. La variante `base` debe usar `prompts.yaml` y `revision_rules.yaml` de la referencia `--base` (por
defecto `dev`, sacados con `git show`) con el código de la rama; la `rama`, los del árbol de trabajo.

R16. El comparador debe calcular por caso la categoría mayoritaria de cada variante y fase, y el veredicto
de los criterios C1–C3 de `design.md` §7; escribir el detalle CON valores en `evals/salidas/` (ignorado por
git) y un resumen SIN CIF ni nombres (recuentos y `caso_id` por categoría) en `progress/` (versionable).

R17. SI falta la clave de algún proveedor LLM, no hay ningún albarán de los casos pedidos o el `git show`
de la base falla, ENTONCES el comparador debe parar con código 2 ANTES de llamar a ningún LLM.

## Puerta de rutas sensibles

R18. `harness/rutas_sensibles.json` debe declarar `services/albaranes-comun/ruesma_comun/proveedores/
propios.py` y el módulo nuevo de sv2 que renderiza el bloque: su contenido entra en el prompt.

## Fuera de alcance

- Dar a IA2 la lista de proveedores con contrato en la obra para que elija (F-055, con el mecanismo
  `ContextoSigridFase2` de F-049). Encaje en `design.md` §8.
- El endpoint `header-grounding` de sv3, que aún valida el CIF propio (nadie lo consume; lo resuelve F-055).
- Cambiar la razón social de serie («Construcciones Ruesma») en `ruesma_comun` o la nota de F-063.
- Backfill de merges ya procesados; añadir más empresas del grupo (se hace con R1/R4 cuando el humano diga).
