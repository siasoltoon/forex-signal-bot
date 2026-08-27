from __future__ import annotations

import logging
import os
import signal
import time

from .executors import register_real_executors
from .handlers import register_agent_handler, register_default_handlers
from .models.bootstrap import build_coding_agent
from .runtime import WorkerRuntime
from .server import WorkerHTTPServer

logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))


def main() -> None:
    runtime = WorkerRuntime.create()
    register_default_handlers(runtime)
    register_real_executors(runtime)

    repo_root = os.getenv("AGENT_REPO_ROOT")
    if repo_root:
        agent = build_coding_agent(repo_root)
        if agent.runtime.health():
            register_agent_handler(runtime, agent)
            logging.info("Local coding agent enabled using Ollama")
        else:
            logging.warning("Ollama unavailable; coding agent handler not enabled")

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
