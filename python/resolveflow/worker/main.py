from __future__ import annotations

import logging
import signal
import threading

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")


def run() -> None:
    """Stage 01 worker skeleton; durable job claiming arrives in Milestone 4."""
    stopped = threading.Event()

    def stop(_signum: int, _frame: object) -> None:
        stopped.set()

    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)
    logging.info("resolveflow worker ready (fixture mode, no external writes)")
    stopped.wait()


if __name__ == "__main__":
    run()
