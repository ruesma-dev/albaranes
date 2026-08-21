<!-- harness/ARNES_VERSION.md -->
# Version del arnes instalada en este repositorio

Normalmente lo escribe `instalar_arnes.ps1`. **No lo edites a mano** salvo en
el caso que documenta la nota de abajo.

| Dato | Valor |
|---|---|
| Version del arnes | `1.7.2` |
| Fecha de la version | 2026-08-21 |
| Instalado/actualizado el | 2026-08-21 |
| Modo | actualizar (parche manual, sin instalador) |
| Origen | `arnes-base` |

> **Por que a mano, y no con el instalador (2026-08-21).**
> Las versiones 1.7.0, 1.7.1 y 1.7.2 se desarrollaron **aqui** (F-038, F-039 y
> F-040) y desde aqui se portaron a `arnes-base`. Su codigo ya estaba dentro
> cuando este repositorio seguia sellado en la 1.6.1. De la 1.6.2 (arreglo del
> propio instalador, que este repositorio no lleva) y de la 1.6.3 solo faltaba
> el parche del bytecode envenenado.
> El instalador habria copiado ademas **diez tests genericos que aqui ya
> existen con nombre `test_f038_*`, `test_f039_*` y `test_f040_*`** —los mismos
> tests, el mismo numero de casos— y habria duplicado unos 190. Decision del
> humano: aplicar a mano lo que faltaba de verdad y conservar los nombres con
> trazabilidad al requisito.
> Lo aplicado consta en `progress/history.md`.

> **AVISO de la 1.6.3: hay informes de mutacion que pueden no valer.**
> Hasta este parche la campania lanzaba la suite dejando escribir `__pycache__`,
> asi que un `.pyc` compilado desde el codigo MUTADO sobrevivia a la
> restauracion del `.py`. El sintoma es una campania absurdamente rapida: si el
> **coste por mutante** —«Tiempo total» x workers / mutantes— de un informe baja
> de un segundo, relanza esa campania con la cache limpia antes de fiarte de sus
> numeros.

> **AVISO de la 1.7.2: los tiempos no son comparables entre campanias.**
> El timeout por mutante se deriva de la linea base medida en vez de ser un fijo
> de `rigor.json`. No compares tiempos de campanias con «Timeout efectivo»
> distinto.

> **AVISO de la 1.6.0: cambia QUE se mide, no solo como se informa.**
> El mutador aprende a mutar `is` / `is not`, la guarda de ausencia de Python.
> Los informes de mutacion generados con 1.5.2 o anterior **no son comparables**
> con los posteriores: se midieron sin tocar ese operador. En este repositorio
> se remidieron F-019 (de 31 a 49 mutantes) y F-027 (de 0 a 1), y el resto de
> informes de `progress/mutacion_*.md` llevan anotado con que vara se midieron.

Para actualizar a una version posterior, desde el repositorio `arnes-base`:

```powershell
.\instalar_arnes.ps1 -Destino "C:\Users\pgris\PycharmProjects\albaranes" -Modo actualizar
```

Antes de aceptar cambios, lee `GUIA_INSTALACION.md` en `arnes-base`: los
ficheros con marcas de adaptacion llevan contenido propio de este proyecto y
casi siempre hay que conservarlos, no sobrescribirlos. Y revisa la lista de
ficheros «nuevos»: mientras este repositorio conserve los nombres
`test_f0XX_*`, el instalador seguira ofreciendo sus equivalentes genericos como
altas.
