# harness/mutacion_paralela.py
"""Campaña de mutación repartida entre varios workers, cada uno en su worktree.

La campaña en serie de `harness.mutacion` ya hace bien lo difícil: aplica un
mutante, lanza la suite del servicio dueño del fichero y restaura con
`try/finally` más una red de seguridad final. Aquí NO se reescribe nada de eso:
el paralelismo se monta por fuera.

1. El coordinador calcula los mutantes UNA vez desde el árbol principal y
   aplica el muestreo UNA vez, antes de repartir.
2. Crea N `git worktree` desechables desde `HEAD`, en el temp del sistema.
3. Lanza N hilos; cada uno llama a `ejecutar_campania` tal cual, con
   `raiz=<su worktree>` y `mutantes=<su partición>`. El trabajo pesado (pytest)
   va en subprocesos, así que el GIL no pinta nada.
4. Fusiona los parciales en un informe idéntico al de la campaña en serie
   salvo la fecha y la fila «Tiempo total».
5. `finally`: retira los worktrees pase lo que pase.

El árbol principal no se muta NUNCA en modo paralelo, y por eso se exige que
esté limpio: los worktrees se crean desde `HEAD` y con cambios sin commitear
evaluarían un código distinto del que se ve en disco.

Limitaciones conocidas del modo paralelo (en serie no aplican, porque la suite
corre sobre el propio árbol):

- **Instalación editable apuntando al árbol principal.** Si el venv de un
  servicio instala su paquete en modo editable contra el árbol principal, la
  suite del worker importaría el código SIN mutar y darían supervivientes
  falsos. Los venvs no se copian al worktree: solo se reutiliza su intérprete.
- **Suites que dependan de ficheros no versionados** (`.env`, datos locales):
  no existen dentro de un worktree. Las convenciones ya prohíben unit tests con
  esas dependencias; un proyecto que las viole verá la suite roja en el worker
  y contará mutantes «muertos» de más.

Todo con biblioteca estándar, como el resto del arnés.
"""

from __future__ import annotations

from harness.alcance import Alcance
from harness.mutacion import InformeMutacion, Mutante

#: Clave con la que la campaña en serie ordena sus mutantes. El informe
#: paralelo tiene que salir en ESTE orden para ser indistinguible del suyo.
Clave = tuple[str, int, int, str]


def clave_estable(mutante: Mutante) -> Clave:
    """Identidad ordenable de un mutante: `(fichero, línea, columna, operador)`."""
    return (mutante.fichero, mutante.linea, mutante.col, mutante.operador)


# --- Reparto y fusión (funciones puras) -------------------------------------


def repartir(mutantes: list[Mutante], n: int) -> list[list[Mutante]]:
    """Reparte los mutantes entre `n` workers en round-robin por índice.

    Determinista: las mismas entradas dan siempre las mismas particiones, y su
    unión es exactamente la lista recibida, sin repetidos ni omitidos. El
    round-robin sobre la lista ya ordenada equilibra el coste: mutantes del
    mismo fichero —cuya suite tarda lo mismo— se reparten entre todos.
    """
    cuantos = max(1, n)
    return [mutantes[indice::cuantos] for indice in range(cuantos)]


def fusionar(
    alcance: Alcance,
    parciales: list[InformeMutacion],
    generados: int,
    segundos: float,
    muestreado: bool = False,
    max_mutantes: int | None = None,
    semilla: int | None = None,
) -> InformeMutacion:
    """Funde los informes de los workers en el informe único de la campaña.

    Los totales se suman y las listas se reordenan por la clave estable, de
    forma que el resultado no delata en qué worker cayó cada mutante. Los
    metadatos de muestreo son los del coordinador, que es quien muestreó.
    """
    informe = InformeMutacion(
        feature=alcance.feature,
        alcance=alcance,
        generados=generados,
        muertos=sum(parcial.muertos for parcial in parciales),
        segundos=segundos,
        muestreado=muestreado,
        max_mutantes=max_mutantes,
        semilla=semilla,
    )
    for atributo in ("supervivientes", "timeouts", "mutantes_evaluados"):
        juntos: list[Mutante] = []
        for parcial in parciales:
            juntos.extend(getattr(parcial, atributo))
        setattr(informe, atributo, sorted(juntos, key=clave_estable))
    return informe
