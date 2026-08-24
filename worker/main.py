from __future__ import annotations

import logging
import os
import signal
import time

from .runtime import WorkerRuntime
from .server import WorkerHTTPServer

logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))


def main() -> None:
    runtime = WorkerRuntime.create()
    server = WorkerHTTPServer(runtime)
    server.start()
    logging.info("PC Worker %s ready on %s:%s", runtime.worker_id, server.host, server.port)
    stop = False

    def shutdown(*_args):
        nonlocal stop
        stop = True

    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)
    while not stop:
        time.sleep(1)
    server.stop()


if __name__ == "__main__":
    main()
