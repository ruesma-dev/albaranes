# main.py
"""Punto de entrada del contenedor de sv9 (``python main.py``).

sv9 es solo worker (no expone HTTP): delega en ``main_worker.main``, que
consume ``q-feedback``. Existe para que sv9 arranque como el resto de
servicios del monorepo (mismo ``CMD`` en el Dockerfile).
"""
from __future__ import annotations


def main() -> int:
    from main_worker import main as main_worker

    return main_worker()


if __name__ == "__main__":
    raise SystemExit(main())
