from __future__ import annotations

import logging
import signal
import threading

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")


def run() -> None:
    """Start the worker process with the external-effect kill switch engaged by default."""
    stopped = threading.Event()

    def stop(_signum: int, _frame: object) -> None:
        stopped.set()

    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)
    logging.info(
        "resolveflow durable worker ready (dispatch kill switch off by default; no external writes)"
    )
    stopped.wait()


if __name__ == "__main__":
    run()
